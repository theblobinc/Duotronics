from __future__ import annotations

from .crypto_primitives import shake256_file, shake256_ref
import mimetypes
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from psycopg.types.json import Jsonb


CORPUS_INDEX_SCHEMA_SQL = r"""
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS corpus_release_images (
  corpus_id TEXT PRIMARY KEY,
  release_name TEXT UNIQUE NOT NULL,
  version TEXT NOT NULL,
  source_root TEXT NOT NULL,
  release_digest TEXT NOT NULL,
  manifest_ref TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT 'staged'
    CHECK (state IN ('staged','indexed','validated','active','retired','rejected')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  file_count BIGINT NOT NULL DEFAULT 0,
  chunk_count BIGINT NOT NULL DEFAULT 0,
  byte_count BIGINT NOT NULL DEFAULT 0,
  unique_content_count BIGINT NOT NULL DEFAULT 0,
  imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  validated_at TIMESTAMPTZ,
  activated_at TIMESTAMPTZ
);

-- Immutable content-addressed objects shared by every historical corpus release.
CREATE TABLE IF NOT EXISTS corpus_content_files (
  file_digest TEXT PRIMARY KEY,
  byte_count BIGINT NOT NULL,
  media_type TEXT NOT NULL DEFAULT 'application/octet-stream',
  title TEXT NOT NULL DEFAULT '',
  indexable BOOLEAN NOT NULL DEFAULT FALSE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corpus_content_chunks (
  file_digest TEXT NOT NULL REFERENCES corpus_content_files(file_digest) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  content_digest TEXT NOT NULL,
  byte_start BIGINT NOT NULL DEFAULT 0,
  byte_end BIGINT NOT NULL DEFAULT 0,
  content TEXT NOT NULL,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(content,'')), 'A')
  ) STORED,
  PRIMARY KEY (file_digest, chunk_index)
);
CREATE INDEX IF NOT EXISTS corpus_content_chunks_search_gin
  ON corpus_content_chunks USING GIN(search_vector);

-- Release image = immutable mapping of release-relative paths to content objects.
CREATE TABLE IF NOT EXISTS corpus_release_files (
  corpus_id TEXT NOT NULL REFERENCES corpus_release_images(corpus_id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  file_digest TEXT NOT NULL REFERENCES corpus_content_files(file_digest) ON DELETE RESTRICT,
  byte_count BIGINT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (corpus_id, path)
);
CREATE INDEX IF NOT EXISTS corpus_release_files_digest_idx
  ON corpus_release_files(file_digest, corpus_id);
CREATE INDEX IF NOT EXISTS corpus_release_files_path_idx
  ON corpus_release_files(corpus_id, path);
CREATE INDEX IF NOT EXISTS corpus_release_files_path_trgm
  ON corpus_release_files USING GIN((lower(path)) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS corpus_release_state_idx
  ON corpus_release_images(state, activated_at DESC, imported_at DESC);

CREATE TABLE IF NOT EXISTS corpus_runtime_state (
  singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
  active_corpus_id TEXT REFERENCES corpus_release_images(corpus_id) ON DELETE RESTRICT,
  previous_corpus_id TEXT REFERENCES corpus_release_images(corpus_id) ON DELETE SET NULL,
  backend TEXT NOT NULL DEFAULT 'postgres',
  overlays JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO corpus_runtime_state(singleton, backend)
VALUES(TRUE, 'postgres') ON CONFLICT(singleton) DO NOTHING;

-- Mutable knowledge is deliberately separated from the immutable kernel corpus.
CREATE TABLE IF NOT EXISTS corpus_overlay_namespaces (
  overlay_id TEXT PRIMARY KEY,
  namespace TEXT UNIQUE NOT NULL,
  state TEXT NOT NULL DEFAULT 'active' CHECK (state IN ('staged','active','retired')),
  priority INTEGER NOT NULL DEFAULT 100,
  mutable BOOLEAN NOT NULL DEFAULT TRUE,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS corpus_overlay_chunks (
  overlay_id TEXT NOT NULL REFERENCES corpus_overlay_namespaces(overlay_id) ON DELETE CASCADE,
  document_id TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  title TEXT NOT NULL DEFAULT '',
  source_ref TEXT NOT NULL DEFAULT '',
  content_digest TEXT NOT NULL,
  content TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(title,'')), 'A') ||
    setweight(to_tsvector('english', coalesce(content,'')), 'B')
  ) STORED,
  PRIMARY KEY (overlay_id, document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS corpus_overlay_search_gin
  ON corpus_overlay_chunks USING GIN(search_vector);
"""


TEXT_SUFFIXES = {
    '.md','.txt','.json','.jsonl','.yaml','.yml','.lean','.tla','.py','.toml','.ini','.cfg',
    '.sh','.bash','.zsh','.php','.js','.mjs','.cjs','.ts','.tsx','.jsx','.sql','.csv','.xml',
    '.html','.htm','.css','.scss','.rst','.tex','.go','.rs','.java','.c','.h','.cpp','.hpp',
}


def _shake256_bytes(data: bytes) -> str:
    return shake256_ref(data)


def _shake256_file(path: Path) -> str:
    return shake256_file(path)


def _slug(value: str) -> str:
    value=re.sub(r'[^A-Za-z0-9._-]+','-',value.strip()).strip('-').lower()
    return value or 'corpus'


def _title_for(path: Path, text: str) -> str:
    for line in text.splitlines()[:40]:
        stripped=line.strip()
        if stripped.startswith('#'):
            return stripped.lstrip('#').strip()[:300]
    return path.stem.replace('_',' ').replace('-',' ')[:300]


def _chunk_text(text: str, target: int=5500, overlap: int=550) -> list[tuple[int,int,str]]:
    if len(text) <= target:
        return [(0,len(text),text)] if text.strip() else []
    chunks=[]
    start=0
    length=len(text)
    while start < length:
        end=min(length,start+target)
        if end < length:
            floor=start+int(target*.65)
            candidates=[text.rfind('\n\n',floor,end),text.rfind('\n',floor,end),text.rfind('. ',floor,end)]
            boundary=max(candidates)
            if boundary > floor:
                end=boundary+1
        piece=text[start:end].strip()
        if piece:
            chunks.append((start,end,piece))
        if end >= length:
            break
        start=max(start+1,end-overlap)
    return chunks


class CorpusBackend(Protocol):
    def active_release(self) -> dict[str,Any] | None: ...
    def search(self, query: str, *, top_k: int=5, corpus_id: str | None=None, historical: bool=False) -> dict[str,Any]: ...


@dataclass
class ImportStats:
    corpus_id: str
    release_name: str
    release_digest: str
    file_count: int
    chunk_count: int
    byte_count: int
    unique_content_count: int
    reused_content_count: int
    skipped_binary_files: int


class PostgresCorpusBackend:
    """Indexed immutable corpus releases in the runtime PostgreSQL database.

    Content is SHAKE256-512-addressed and shared across releases. Corpus releases are
    immutable path->content mappings, which makes 40+ historical kernel versions
    practical without storing duplicate copies of unchanged files.
    """

    def __init__(self, store: Any) -> None:
        self.store=store

    def migrate(self) -> None:
        with self.store.connect() as conn:
            conn.execute(CORPUS_INDEX_SCHEMA_SQL)
            conn.commit()

    def active_release(self) -> dict[str,Any] | None:
        with self.store.connect() as conn:
            row=conn.execute("""
                SELECT r.* FROM corpus_runtime_state s
                JOIN corpus_release_images r ON r.corpus_id=s.active_corpus_id
                WHERE s.singleton=TRUE
            """).fetchone()
            return dict(row) if row else None

    def inspect_active(self, *, document_limit: int=500) -> dict[str,Any] | None:
        release=self.active_release()
        if not release:
            return None
        with self.store.connect() as conn:
            rows=conn.execute("""
                SELECT path,file_digest,byte_count AS bytes
                FROM corpus_release_files
                WHERE corpus_id=%s ORDER BY path LIMIT %s
            """,(release['corpus_id'],max(1,min(int(document_limit),1000)))).fetchall()
        metadata=release.get('metadata') or {}
        return {
            'status':'ok','backend':'postgres','corpus_dir':release.get('source_root'),
            'manifest_path':None,'manifest':metadata,
            'corpus_ref':{
                'version':release.get('version') or release.get('release_name') or 'unversioned',
                'digest':release.get('release_digest') or '',
                'manifest_ref':release.get('manifest_ref') or 'indexed:no-manifest',
            },
            'corpus_id':release.get('corpus_id'),'release_name':release.get('release_name'),
            'file_count':int(release.get('file_count') or 0),
            'chunk_count':int(release.get('chunk_count') or 0),
            'documents':[dict(row) for row in rows],
            'truncated':int(release.get('file_count') or 0)>len(rows),
        }

    def list_releases(self) -> list[dict[str,Any]]:
        with self.store.connect() as conn:
            rows=conn.execute("""
                SELECT corpus_id,release_name,version,release_digest,state,file_count,chunk_count,
                       byte_count,unique_content_count,imported_at,validated_at,activated_at,source_root
                FROM corpus_release_images ORDER BY release_name
            """).fetchall()
            return [dict(row) for row in rows]

    def release_by_name(self, release_name: str) -> dict[str,Any] | None:
        with self.store.connect() as conn:
            row=conn.execute("SELECT * FROM corpus_release_images WHERE release_name=%s",(release_name,)).fetchone()
            return dict(row) if row else None

    def activate(self, corpus_id: str) -> dict[str,Any]:
        with self.store.connect() as conn:
            row=conn.execute("SELECT * FROM corpus_release_images WHERE corpus_id=%s",(corpus_id,)).fetchone()
            if not row:
                raise ValueError(f'unknown corpus_id: {corpus_id}')
            if row['state'] not in {'indexed','validated','active','retired'}:
                raise ValueError(f"corpus {corpus_id} is not activation-ready: {row['state']}")
            current=conn.execute("SELECT active_corpus_id,previous_corpus_id FROM corpus_runtime_state WHERE singleton=TRUE").fetchone()
            active_id=current['active_corpus_id'] if current else None
            if active_id == corpus_id:
                # Idempotent re-activation must preserve rollback history rather
                # than recording the active release as its own predecessor.
                conn.execute("UPDATE corpus_release_images SET state='active' WHERE corpus_id=%s",(corpus_id,))
                conn.commit()
                return dict(row)
            previous=active_id
            if previous:
                conn.execute("UPDATE corpus_release_images SET state='retired' WHERE corpus_id=%s AND state='active'",(previous,))
            conn.execute("UPDATE corpus_release_images SET state='active',activated_at=now() WHERE corpus_id=%s",(corpus_id,))
            conn.execute("""
                UPDATE corpus_runtime_state
                SET previous_corpus_id=%s,active_corpus_id=%s,backend='postgres',updated_at=now()
                WHERE singleton=TRUE
            """,(previous,corpus_id))
            conn.commit()
        return self.active_release() or {}

    def rollback(self) -> dict[str,Any]:
        with self.store.connect() as conn:
            state=conn.execute("SELECT previous_corpus_id FROM corpus_runtime_state WHERE singleton=TRUE").fetchone()
            if not state or not state['previous_corpus_id']:
                raise ValueError('no previous corpus release is recorded')
            target=state['previous_corpus_id']
        return self.activate(target)

    def _known_content(self) -> set[str]:
        with self.store.connect() as conn:
            return {row['file_digest'] for row in conn.execute('SELECT file_digest FROM corpus_content_files').fetchall()}

    def import_release(self, root: Path, *, release_name: str | None=None, activate: bool=False) -> ImportStats:
        root=root.resolve()
        if not root.is_dir():
            raise FileNotFoundError(root)
        release_name=release_name or root.name
        corpus_id='corpus-'+_slug(release_name)
        known=self._known_content()

        release_files=[]
        new_files=[]
        new_chunks=[]
        release_parts=[]
        file_count=chunk_count=byte_count=skipped=unique_content=reused=0
        manifest_ref=''
        canonical_manifest_ref=''
        release_token=re.sub(r'[^a-z0-9]+','_',release_name.lower()).strip('_')
        canonical_descriptor_name=f'canonical_corpus_{release_token}.json'

        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.name.startswith('.'):
                continue
            rel=path.relative_to(root).as_posix()
            size=path.stat().st_size
            digest=_shake256_file(path)
            file_count += 1
            byte_count += size
            release_parts.append(rel.encode('utf-8',errors='ignore')+b'\0'+str(size).encode()+b'\0'+digest.encode()+b'\n')
            lower_name=path.name.lower()
            if lower_name == canonical_descriptor_name:
                canonical_manifest_ref=digest
            elif lower_name in {'manifest.json','corpus.manifest.json','duotronic.manifest.json'} and not manifest_ref:
                manifest_ref=digest
            release_files.append((corpus_id,rel,digest,size,Jsonb({'source_release':release_name})))
            if digest in known:
                reused += 1
                continue

            suffix=path.suffix.lower()
            media_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            indexable=True
            text=''
            if size > 8_000_000:
                indexable=False
            else:
                try:
                    raw=path.read_bytes()
                    if b'\x00' in raw[:8192]:
                        indexable=False
                    else:
                        text=raw.decode('utf-8',errors='ignore')
                        if suffix not in TEXT_SUFFIXES and not text.strip():
                            indexable=False
                except Exception:
                    indexable=False
            if not indexable:
                skipped += 1
            title=_title_for(path,text) if text else path.stem.replace('_',' ').replace('-',' ')[:300]
            new_files.append((digest,size,media_type,title,indexable,Jsonb({'suffix':suffix})))
            known.add(digest)
            unique_content += 1
            if indexable and text.strip():
                for idx,(start,end,content) in enumerate(_chunk_text(text)):
                    new_chunks.append((digest,idx,_shake256_bytes(content.encode('utf-8')),start,end,content))
                    chunk_count += 1

        manifest_ref=canonical_manifest_ref or manifest_ref
        release_digest=shake256_ref(release_parts)
        metadata={
            'source_kind':'witness_contract_release','canonical_root':str(root),
            'skipped_binary_files':skipped,'importer':'postgres-content-addressed-corpus-v2',
        }

        with self.store.connect() as conn:
            existing=conn.execute("SELECT release_digest,state,chunk_count,manifest_ref FROM corpus_release_images WHERE corpus_id=%s",(corpus_id,)).fetchone()
            if existing and existing['release_digest']==release_digest and existing['state'] in {'indexed','validated','active','retired'}:
                if manifest_ref and existing['manifest_ref'] != manifest_ref:
                    conn.execute("UPDATE corpus_release_images SET manifest_ref=%s WHERE corpus_id=%s",(manifest_ref,corpus_id))
                conn.commit()
                if activate:
                    self.activate(corpus_id)
                return ImportStats(corpus_id,release_name,release_digest,file_count,int(existing['chunk_count'] or 0),byte_count,unique_content,reused,skipped)

            conn.execute("""
                INSERT INTO corpus_release_images
                  (corpus_id,release_name,version,source_root,release_digest,manifest_ref,state,metadata,
                   file_count,chunk_count,byte_count,unique_content_count)
                VALUES (%s,%s,%s,%s,%s,%s,'staged',%s,%s,0,%s,%s)
                ON CONFLICT(corpus_id) DO UPDATE SET
                  release_name=EXCLUDED.release_name,version=EXCLUDED.version,source_root=EXCLUDED.source_root,
                  release_digest=EXCLUDED.release_digest,manifest_ref=EXCLUDED.manifest_ref,state='staged',
                  metadata=EXCLUDED.metadata,file_count=EXCLUDED.file_count,byte_count=EXCLUDED.byte_count,
                  unique_content_count=EXCLUDED.unique_content_count,imported_at=now(),validated_at=NULL
            """,(corpus_id,release_name,release_name,str(root),release_digest,manifest_ref,Jsonb(metadata),file_count,byte_count,unique_content))
            if new_files:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO corpus_content_files(file_digest,byte_count,media_type,title,indexable,metadata)
                        VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(file_digest) DO NOTHING
                    """,new_files)
            if new_chunks:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO corpus_content_chunks(file_digest,chunk_index,content_digest,byte_start,byte_end,content)
                        VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(file_digest,chunk_index) DO NOTHING
                    """,new_chunks)
            conn.execute('DELETE FROM corpus_release_files WHERE corpus_id=%s',(corpus_id,))
            if release_files:
                with conn.cursor() as cur:
                    cur.executemany("""
                        INSERT INTO corpus_release_files(corpus_id,path,file_digest,byte_count,metadata)
                        VALUES (%s,%s,%s,%s,%s)
                    """,release_files)
            row=conn.execute("""
                SELECT count(*) AS chunks FROM corpus_release_files rf
                JOIN corpus_content_chunks cc ON cc.file_digest=rf.file_digest
                WHERE rf.corpus_id=%s
            """,(corpus_id,)).fetchone()
            total_chunks=int(row['chunks'] or 0)
            conn.execute("""
                UPDATE corpus_release_images SET state='indexed',validated_at=now(),chunk_count=%s
                WHERE corpus_id=%s
            """,(total_chunks,corpus_id))
            conn.commit()

        if activate:
            self.activate(corpus_id)
        return ImportStats(corpus_id,release_name,release_digest,file_count,total_chunks,byte_count,unique_content,reused,skipped)

    def search(self, query: str, *, top_k: int=5, corpus_id: str | None=None, historical: bool=False) -> dict[str,Any]:
        query=(query or '').strip()
        if not query:
            return {'status':'ok','backend':'postgres','results':[]}
        limit=max(1,min(int(top_k),25))
        with self.store.connect() as conn:
            release=None
            if corpus_id is None and not historical:
                state=conn.execute('SELECT active_corpus_id FROM corpus_runtime_state WHERE singleton=TRUE').fetchone()
                corpus_id=state['active_corpus_id'] if state else None
            if corpus_id:
                release=conn.execute('SELECT * FROM corpus_release_images WHERE corpus_id=%s',(corpus_id,)).fetchone()
                rows=conn.execute("""
                    WITH q AS (SELECT websearch_to_tsquery('english', %s) AS query)
                    SELECT rf.corpus_id,rf.path,cc.chunk_index,cf.title,rf.file_digest,cc.content_digest,cc.content,
                           rf.metadata,
                           ts_rank_cd(cc.search_vector,q.query,32) +
                           (similarity(lower(rf.path),lower(%s))*0.15) AS rank
                    FROM corpus_release_files rf
                    JOIN corpus_content_files cf ON cf.file_digest=rf.file_digest
                    JOIN corpus_content_chunks cc ON cc.file_digest=rf.file_digest,q
                    WHERE rf.corpus_id=%s AND cc.search_vector @@ q.query
                    ORDER BY rank DESC,rf.path,cc.chunk_index LIMIT %s
                """,(query,query,corpus_id,limit)).fetchall()
            else:
                rows=conn.execute("""
                    WITH q AS (SELECT websearch_to_tsquery('english', %s) AS query)
                    SELECT rf.corpus_id,rf.path,cc.chunk_index,cf.title,rf.file_digest,cc.content_digest,cc.content,
                           rf.metadata,ts_rank_cd(cc.search_vector,q.query,32) AS rank
                    FROM corpus_release_files rf
                    JOIN corpus_release_images r ON r.corpus_id=rf.corpus_id
                    JOIN corpus_content_files cf ON cf.file_digest=rf.file_digest
                    JOIN corpus_content_chunks cc ON cc.file_digest=rf.file_digest,q
                    WHERE r.state <> 'rejected' AND cc.search_vector @@ q.query
                    ORDER BY rank DESC,r.imported_at DESC,rf.path LIMIT %s
                """,(query,limit)).fetchall()
            if not rows and corpus_id:
                rows=conn.execute("""
                    SELECT rf.corpus_id,rf.path,0 AS chunk_index,cf.title,rf.file_digest,'' AS content_digest,
                           '' AS content,rf.metadata,similarity(lower(rf.path),lower(%s)) AS rank
                    FROM corpus_release_files rf JOIN corpus_content_files cf ON cf.file_digest=rf.file_digest
                    WHERE rf.corpus_id=%s AND similarity(lower(rf.path),lower(%s)) > 0.12
                    ORDER BY rank DESC LIMIT %s
                """,(query,corpus_id,query,limit)).fetchall()
            results=[]
            for row in rows:
                item=dict(row)
                content=str(item.pop('content') or '')
                item['snippet']=' '.join(content.split())[:1800]
                item['score']=float(item.pop('rank') or 0.0)
                results.append(item)
            ref={}
            if release:
                ref={'version':release['version'],'digest':release['release_digest'],'manifest_ref':release['manifest_ref']}
            return {'status':'ok','backend':'postgres','corpus_id':corpus_id,'corpus_ref':ref,'results':results}


def build_backend(store: Any | None, backend_name: str | None=None) -> PostgresCorpusBackend | None:
    name=(backend_name or os.getenv('CORPUS_BACKEND','postgres')).strip().lower()
    if name == 'postgres' and store is not None:
        return PostgresCorpusBackend(store)
    return None
