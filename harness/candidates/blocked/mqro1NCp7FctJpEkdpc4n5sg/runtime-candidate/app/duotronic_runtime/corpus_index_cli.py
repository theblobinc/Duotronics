from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from .config import get_settings
from .corpus_index import PostgresCorpusBackend
from .db import Store


def backend() -> PostgresCorpusBackend:
    store=Store(get_settings())
    store.migrate()
    result=PostgresCorpusBackend(store)
    result.migrate()
    return result


def release_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        raise FileNotFoundError(root)
    return sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p:p.name.lower())


def cmd_list(args) -> int:
    rows=backend().list_releases()
    active=backend().active_release()
    print(json.dumps({
        'active_corpus_id':active.get('corpus_id') if active else None,
        'active_release':active.get('release_name') if active else None,
        'count':len(rows),'releases':rows,
    },default=str,indent=2))
    return 0


def cmd_import(args) -> int:
    b=backend()
    root=Path(args.path)
    t=time.perf_counter()
    stats=b.import_release(root,release_name=args.name or root.name,activate=args.activate)
    out={**stats.__dict__,'elapsed_seconds':round(time.perf_counter()-t,3),'active':bool(args.activate)}
    print(json.dumps(out,indent=2))
    return 0


def cmd_import_all(args) -> int:
    b=backend()
    history=Path(args.history)
    existing={r['release_name']:r for r in b.list_releases()}
    dirs=release_dirs(history)
    # Active release is imported first so the runtime can switch to indexed search immediately.
    if args.active:
        dirs.sort(key=lambda p:(0 if p.name==args.active else 1,p.name.lower()))
    imported=[]; skipped=[]; failed=[]
    limit=max(0,int(args.max_releases or 0))
    for root in dirs:
        if limit and len(imported)>=limit:
            break
        if args.only_missing and root.name in existing:
            skipped.append(root.name)
            continue
        try:
            t=time.perf_counter()
            stats=b.import_release(root,release_name=root.name,activate=(root.name==args.active))
            row={**stats.__dict__,'elapsed_seconds':round(time.perf_counter()-t,3)}
            imported.append(row)
            print(json.dumps({'event':'imported',**row}),flush=True)
        except Exception as exc:
            failed.append({'release':root.name,'error':f'{type(exc).__name__}: {exc}'})
            print(json.dumps({'event':'failed','release':root.name,'error':str(exc)}),flush=True)
            if args.fail_fast:
                raise
    active=b.active_release()
    print(json.dumps({
        'event':'summary','imported_count':len(imported),'skipped_count':len(skipped),
        'failed_count':len(failed),'active_release':active.get('release_name') if active else None,
        'failed':failed,
    },indent=2),flush=True)
    return 1 if failed and args.fail_fast else 0


def cmd_activate(args) -> int:
    b=backend()
    row=b.release_by_name(args.release)
    if not row:
        raise SystemExit(f'unknown release: {args.release}')
    print(json.dumps(b.activate(row['corpus_id']),default=str,indent=2))
    return 0


def cmd_rollback(args) -> int:
    print(json.dumps(backend().rollback(),default=str,indent=2))
    return 0


def cmd_search(args) -> int:
    b=backend()
    corpus_id=None
    if args.release:
        row=b.release_by_name(args.release)
        if not row:
            raise SystemExit(f'unknown release: {args.release}')
        corpus_id=row['corpus_id']
    t=time.perf_counter()
    result=b.search(args.query,top_k=args.top_k,corpus_id=corpus_id,historical=args.historical)
    result['elapsed_ms']=round((time.perf_counter()-t)*1000,3)
    print(json.dumps(result,default=str,indent=2))
    return 0


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description='Versioned WG-RNN/SRNN corpus index manager')
    sub=parser.add_subparsers(dest='command',required=True)

    p=sub.add_parser('list'); p.set_defaults(func=cmd_list)
    p=sub.add_parser('import')
    p.add_argument('path'); p.add_argument('--name'); p.add_argument('--activate',action='store_true')
    p.set_defaults(func=cmd_import)

    p=sub.add_parser('import-all')
    p.add_argument('--history',default=os.getenv('CORPUS_HISTORY_DIR','/runtime/corpus-history'))
    p.add_argument('--active',default=None)
    p.add_argument('--only-missing',action='store_true',default=False)
    p.add_argument('--max-releases',type=int,default=0)
    p.add_argument('--fail-fast',action='store_true')
    p.set_defaults(func=cmd_import_all)

    p=sub.add_parser('activate'); p.add_argument('release'); p.set_defaults(func=cmd_activate)
    p=sub.add_parser('rollback'); p.set_defaults(func=cmd_rollback)
    p=sub.add_parser('search')
    p.add_argument('query'); p.add_argument('--release'); p.add_argument('--historical',action='store_true'); p.add_argument('--top-k',type=int,default=5)
    p.set_defaults(func=cmd_search)

    args=parser.parse_args(argv)
    return int(args.func(args))


if __name__=='__main__':
    raise SystemExit(main())
