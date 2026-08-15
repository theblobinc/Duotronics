#!/var/www/xavi/.venv/bin/python
from __future__ import annotations

try:
    from .xavi_crypto import shake256_file
except ImportError:
    from xavi_crypto import shake256_file
import argparse, bz2, email, gzip, hashlib, html, json, lzma, mailbox, mimetypes, os, re, sqlite3, subprocess, tarfile, tempfile, time, urllib.request, zipfile
from collections import Counter
from pathlib import Path
from typing import Any
from email import policy as email_policy

ROOT=Path(os.getenv('XAVI_DATALAKE_HOST_ROOT','/datastore2/xavi/data')).resolve()
RUNTIME_ROOT=os.getenv('XAVI_DATALAKE_RUNTIME_ROOT','/data-lake').rstrip('/')
STATE=Path(os.getenv('XAVI_DATALAKE_STATE','/datastore2/xavi/wgrnn-datalake/ingest.sqlite3'))
MCP_URL=os.getenv('XAVI_DATALAKE_MCP_URL','http://127.0.0.1:8080/mcp')
REST_BASE=os.getenv('XAVI_DATALAKE_RUNTIME_REST','http://127.0.0.1:8080').rstrip('/')
EXPERIMENT_ACTIVE_PATH=Path(os.getenv('XAVI_NODE_WORK_EXPERIMENT_ACTIVE','/home/tbi/.local/state/xavi-wgrnn-node-workloads/experiment.active.json'))
EXPERIMENT_ACTIVE_TTL=max(120,min(int(os.getenv('XAVI_DATALAKE_EXPERIMENT_ACTIVE_TTL','480')),1800))
RUNTIME_ENV_FILE=Path(os.getenv('XAVI_DATALAKE_RUNTIME_ENV','/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/.env'))

def research_active():
    try:
        return (time.time()-EXPERIMENT_ACTIVE_PATH.stat().st_mtime) < EXPERIMENT_ACTIVE_TTL
    except OSError:
        return False
SESSION='service:wgrnn-datalake-ingest'; AGENT='wgrnn-datalake-ingest'
TEXT={'.txt','.md','.rst','.log','.json','.jsonl','.ndjson','.csv','.tsv','.xml','.html','.htm','.yaml','.yml','.toml','.ini','.cfg','.conf','.py','.js','.ts','.tsx','.jsx','.php','.sql','.sh','.css','.scss','.srt','.vtt','.lrc'}
IMAGE={'.jpg','.jpeg','.png','.gif','.webp','.bmp','.tif','.tiff'}
AUDIO={'.mp3','.wav','.flac','.aac','.m4a','.ogg','.opus','.wma'}
VIDEO={'.mp4','.mkv','.webm','.avi','.mov','.m4v','.wmv','.mpeg','.mpg'}
DBEXT={'.sqlite','.sqlite3','.db'}
ARCHIVE={'.zip','.tar','.tgz','.tbz','.tbz2','.txz','.gz','.bz2','.xz','.7z','.rar'}
PDF={'.pdf'}
OFFICE={'.docx','.docm','.xlsx','.xlsm','.pptx','.pptm','.odt','.ods','.odp','.epub'}
EMAIL_EXT={'.eml','.mbox','.mailbox'}
ADAPTER_REGISTRY=STATE.with_name('adapter_registry.json')
SECRET=re.compile(r'(^|[._-])(secret|token|password|passwd|credential|private|jwt|enrollment|cookie|cookies|session|auth|key)([._-]|$)',re.I)
LOW_VALUE_DIRS={'node_modules','.git','.svn','.hg','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.cache','venv','.venv','dist','build'}
LOW_VALUE_PREFIXES=(
    'social/facebook/fbscrape/',
    'social/facebook/scrape-logs/',
    'social/facebook/debug_',
    'social/bluesky/',
)
SEALED_SOCIAL_SEGMENTS={
    'security_and_login_information','password_and_security','login_and_password',
    'two_factor_authentication','two-factor_authentication','account_recovery',
    'login_protection_data','ip_address_activity','where_you_are_logged_in',
}
SEALED_SOCIAL_NAMES={
    'two_factor_authentication.html','two-factor_authentication.html','ip_address_activity.html',
    'login_protection_data.html','your_recent_profile_recovery_successes.html',
    'passwords.html','saved_login_information.html','login_activity.html',
}
URL=re.compile(r'https?://[^\s<>"\']+',re.I)
YT=re.compile(r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/|shorts/))([A-Za-z0-9_-]{6,})',re.I)
TRACK=re.compile(r'^\s*(\d{1,6})\s*[-_. ]')
SKIP_PREFIX=('duotronic-runtime/runtime-data/','duotronic-runtime/runtime-data','mediacms/library/datalake_catalog/','mediacms/library/.xavi-datalake-sync/')
_key=None

def conn():
    STATE.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(STATE,timeout=30); c.row_factory=sqlite3.Row
    c.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;
    CREATE TABLE IF NOT EXISTS files(relpath TEXT PRIMARY KEY,size INTEGER,mtime_ns INTEGER,category TEXT,priority INTEGER,stage TEXT DEFAULT 'new',shake256_512 TEXT,artifact_id TEXT,last_error TEXT,attempts INTEGER DEFAULT 0,discovered_ms INTEGER,processed_ms INTEGER);
    CREATE INDEX IF NOT EXISTS idx_files_stage ON files(stage,priority,discovered_ms);
    CREATE TABLE IF NOT EXISTS refs(ref_type TEXT,ref_value TEXT,relpath TEXT,PRIMARY KEY(ref_type,ref_value,relpath));
    CREATE TABLE IF NOT EXISTS emitted(pattern_key TEXT PRIMARY KEY,emitted_ms INTEGER);
    CREATE TABLE IF NOT EXISTS features(relpath TEXT,feature_key TEXT,feature_value TEXT,confidence REAL,PRIMARY KEY(relpath,feature_key,feature_value));''')
    cols={r['name'] for r in c.execute('PRAGMA table_info(files)')}
    migrations={
        'shake256_512': 'TEXT',
        'training_stage': "TEXT NOT NULL DEFAULT 'pending'",
        'training_next_chunk': 'INTEGER NOT NULL DEFAULT 0',
        'training_chunk_count': 'INTEGER',
        'training_attempts': 'INTEGER NOT NULL DEFAULT 0',
        'training_error': 'TEXT',
        'trained_ms': 'INTEGER',
    }
    for name,decl in migrations.items():
        if name not in cols:
            c.execute(f'ALTER TABLE files ADD COLUMN {name} {decl}')
    legacy_digest_col = 'sha' + '256'
    if legacy_digest_col in cols:
        c.execute('DROP INDEX IF EXISTS idx_files_sha')
        c.execute(f'ALTER TABLE files DROP COLUMN \"{legacy_digest_col}\"')
    c.execute('CREATE INDEX IF NOT EXISTS idx_files_shake256_512 ON files(shake256_512)')
    c.execute("CREATE INDEX IF NOT EXISTS idx_files_training ON files(stage,training_stage,priority,discovered_ms)")
    c.commit()
    return c

def runtime_key():
    global _key
    if _key: return _key
    out=subprocess.check_output(['podman','inspect','duotronic-runtime','--format','{{range .Config.Env}}{{println .}}{{end}}'],text=True,timeout=15)
    for line in out.splitlines():
        k,sep,v=line.partition('=')
        if sep and k=='XAVI_MCP_API_KEY' and v: _key=v; return v
    raise RuntimeError('runtime MCP key unavailable')

_rest_key=None
_REST_ROUTES={
    'runtime.autonomy_ingest_artifact':'/v1/autonomy/artifact/ingest',
    'runtime.datalake_observe':'/v1/autonomy/datalake/observe',
    'runtime.datalake_pattern':'/v1/autonomy/datalake/pattern',
    'runtime.training_observe':'/v1/autonomy/training/observe',
}

def runtime_rest_key():
    global _rest_key
    if _rest_key: return _rest_key
    explicit=str(os.getenv('XAVI_DATALAKE_RUNTIME_API_KEY') or '').strip()
    if explicit: _rest_key=explicit; return explicit
    try:
        for line in RUNTIME_ENV_FILE.read_text(errors='ignore').splitlines():
            k,sep,v=line.partition('=')
            if sep and k.strip()=='RUNTIME_API_KEY' and v.strip(): _rest_key=v.strip(); return _rest_key
    except OSError: pass
    raise RuntimeError('runtime REST API key unavailable')

def call(tool,args,timeout=60):
    route=_REST_ROUTES.get(tool)
    if not route:
        raise RuntimeError(f'unsupported data-lake runtime operation: {tool}')
    body=json.dumps(args,separators=(',',':')).encode()
    req=urllib.request.Request(
        REST_BASE+route,
        data=body,
        headers={
            'content-type':'application/json',
            'accept':'application/json',
            'authorization':'Bearer '+runtime_rest_key(),
            'user-agent':'xavi-wgrnn-datalake-ingest/2',
        },
        method='POST',
    )
    with urllib.request.urlopen(req,timeout=timeout) as response:
        value=json.loads(response.read().decode())
    return value if isinstance(value,dict) else {'value':value}

def digest_file(path):
    return shake256_file(path)

def cat(rel):
    path=Path(rel); s=path.suffix.lower(); low=rel.lower(); name=path.name.lower()
    # Operator explicitly permits full local learning from the canonical archive,
    # including account/security/recovery exports and credential-bearing files.
    # They remain provenance-tagged evidence; they are no longer plaintext-suppressed.
    if s in DBEXT or re.search(r'\.(?:sqlite|sqlite3|db)(?:\.|$)',name): return 'database'
    if s in PDF: return 'pdf'
    if s in OFFICE: return 'office'
    if s in EMAIL_EXT: return 'email'
    if s in TEXT or name.startswith('.env') or SECRET.search(name) or name == '.enrollment_secret': return 'text'
    if s in IMAGE: return 'image'
    if s in AUDIO: return 'audio'
    if s in VIDEO: return 'video'
    if s in ARCHIVE: return 'archive'
    if 'facebook' in low or '/social/' in '/'+low: return 'social-data'
    return 'binary'

def priority(category,rel):
    path=Path(rel); parts={part.lower() for part in path.parts}; ordered=[part.lower() for part in path.parts]; name=path.name.lower()
    # Keep generated/dependency/scraper implementation material eligible, but
    # far behind authored/exported evidence. It can still be inspected later.
    if parts & LOW_VALUE_DIRS: return 98
    lowrel=rel.lower()
    if any(lowrel.startswith(prefix) for prefix in LOW_VALUE_PREFIXES): return 96
    if name in {'.gitignore','.gitattributes','package.json','package-lock.json','yarn.lock','pnpm-lock.yaml'}: return 97
    is_facebook=('facebook' in ordered or 'facebook_data' in ordered or (ordered and ordered[0]=='social' and 'facebook' in rel.lower()))
    if is_facebook:
        return {'text':5,'database':5,'pdf':6,'office':7,'email':7,'social-data':9,'image':20,'audio':25,'video':30,'binary':45,'archive':55}.get(category,60)
    if ordered and ordered[0]=='music':
        return {'text':8,'database':10,'pdf':10,'office':10,'email':12,'audio':18,'video':20,'image':24,'social-data':25,'binary':45,'archive':55}.get(category,55)
    if ordered and ordered[0]=='social':
        return {'text':12,'database':12,'pdf':13,'office':13,'email':13,'social-data':16,'image':25,'audio':30,'video':35,'binary':45,'archive':55}.get(category,60)
    return {'text':15,'database':16,'pdf':17,'office':17,'email':18,'social-data':18,'image':30,'audio':40,'video':55,'archive':65,'binary':70}.get(category,80)

def scan(c):
    n=0; now=int(time.time()*1000)
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.is_symlink(): continue
        rel=p.relative_to(ROOT).as_posix()
        if any(rel==x or rel.startswith(x) for x in SKIP_PREFIX): continue
        st=p.stat(); k=cat(rel); pr=priority(k,rel)
        old=c.execute('SELECT size,mtime_ns,category,stage FROM files WHERE relpath=?',(rel,)).fetchone()
        stage='new' if not old or old['size']!=st.st_size or old['mtime_ns']!=st.st_mtime_ns or old['category']!=k else old['stage']
        c.execute('INSERT INTO files(relpath,size,mtime_ns,category,priority,stage,discovered_ms) VALUES(?,?,?,?,?,?,?) ON CONFLICT(relpath) DO UPDATE SET size=excluded.size,mtime_ns=excluded.mtime_ns,category=excluded.category,priority=excluded.priority,stage=CASE WHEN files.size!=excluded.size OR files.mtime_ns!=excluded.mtime_ns OR files.category!=excluded.category THEN \'new\' ELSE files.stage END',(rel,st.st_size,st.st_mtime_ns,k,pr,stage,now)); n+=1
    c.commit(); return n

def read_text(p,limit=200000):
    b=p.read_bytes()[:limit]; return b.decode('utf-8','replace')

def ffprobe(p):
    try:
        x=subprocess.check_output(['ffprobe','-v','quiet','-print_format','json','-show_format','-show_streams',str(p)],text=True,timeout=30)
        d=json.loads(x); return {'format':d.get('format',{}),'streams':d.get('streams',[])}
    except Exception as e: return {'error':type(e).__name__}

def image_features(p):
    try:
        from PIL import Image
        im=Image.open(p).convert('RGB'); im.thumbnail((320,320)); px=list(im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()); n=max(1,len(px))
        red=sum(1 for r,g,b in px if r>120 and r>g*1.25 and r>b*1.25)/n
        q=[(r//32*32,g//32*32,b//32*32) for r,g,b in px]; top=Counter(q).most_common(5)
        return {'width':Image.open(p).size[0],'height':Image.open(p).size[1],'red_fraction':round(red,5),'dominant_colors':[{'hex':'#%02x%02x%02x'%rgb,'fraction':round(cnt/n,5)} for rgb,cnt in top]}
    except Exception as e: return {'error':type(e).__name__}

def video_visual(p):
    meta=ffprobe(p); duration=0.0
    try: duration=float((meta.get('format') or {}).get('duration') or 0)
    except Exception: pass
    frames=[]
    if duration>0:
        with tempfile.TemporaryDirectory(prefix='wgrnn-frames-') as td:
            for i,fraction in enumerate((.08,.22,.38,.55,.72,.9)):
                out=Path(td)/f'{i}.jpg'
                try:
                    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(duration*fraction),'-i',str(p),'-frames:v','1','-vf','scale=480:-2',str(out)],timeout=35,check=True)
                    frames.append({'time_s':round(duration*fraction,3),**image_features(out)})
                except Exception: pass
    return meta,frames

def sqlite_extract(p):
    records=[]
    try:
        c=sqlite3.connect(f'file:{p}?mode=ro',uri=True,timeout=5); c.row_factory=sqlite3.Row
        tabs=[r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name LIMIT 40")]
        records.append({'kind':'sqlite-schema','content':'SQLite tables: '+', '.join(tabs),'metadata':{'tables':tabs}})
        for t in tabs[:16]:
            try:
                count=c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                cols=[r[1] for r in c.execute(f'PRAGMA table_info("{t}")')]
                records.append({'kind':'sqlite-table','content':f'{t}: {count} rows; columns: '+', '.join(cols),'metadata':{'table':t,'rows':count,'columns':cols}})
                for row in c.execute(f'SELECT * FROM "{t}" LIMIT 8'):
                    vals=[]
                    for k in row.keys():
                        v=row[k]
                        if isinstance(v,str) and v.strip(): vals.append(f'{k}={v[:1200]}')
                    if vals: records.append({'kind':'sqlite-sample','content':f'{t}: '+' | '.join(vals),'metadata':{'table':t}})
            except Exception: pass
        c.close()
    except Exception as e: records.append({'kind':'sqlite-error','content':f'SQLite inspection failed: {type(e).__name__}'})
    return records[:120]

def _adapter_registry_load():
    try:
        v=json.loads(ADAPTER_REGISTRY.read_text())
        return v if isinstance(v,dict) else {}
    except Exception:
        return {}

def _adapter_registry_record(key,mime,strategy,rel):
    if not key: return
    reg=_adapter_registry_load()
    old=reg.get(key)
    entry={'strategy':strategy,'mime':mime,'first_example':rel,'updated_ms':int(time.time()*1000),'auto_created':True}
    if isinstance(old,dict) and old.get('first_example'): entry['first_example']=old['first_example']
    if old != entry:
        ADAPTER_REGISTRY.parent.mkdir(parents=True,exist_ok=True)
        reg[key]=entry
        tmp=ADAPTER_REGISTRY.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(reg,indent=2,sort_keys=True))
        tmp.replace(ADAPTER_REGISTRY)

def _mime(p):
    guessed=mimetypes.guess_type(str(p))[0]
    try:
        out=subprocess.check_output(['file','--brief','--mime-type',str(p)],text=True,timeout=6).strip()
        if out and out!='application/octet-stream': return out
    except Exception: pass
    return guessed or 'application/octet-stream'

def _printable_strings(p,byte_limit=2_000_000,max_strings=4000):
    data=p.read_bytes()[:byte_limit]
    vals=[]
    for m in re.finditer(rb'[\\x09\\x20-\\x7e]{5,}',data):
        try: t=m.group(0).decode('utf-8','replace').strip()
        except Exception: continue
        if t and t not in vals: vals.append(t)
        if len(vals)>=max_strings: break
    return '\\n'.join(vals)[:240000]

def _xml_text(raw):
    t=re.sub(r'<[^>]+>',' ',raw)
    return re.sub(r'\\s+',' ',html.unescape(t)).strip()

def office_extract(p):
    records=[]; chunks=[]
    try:
        with zipfile.ZipFile(p) as z:
            names=z.namelist()
            wanted=[]
            suffix=p.suffix.lower()
            if suffix in {'.docx','.docm'}: wanted=[n for n in names if n.startswith('word/') and n.endswith('.xml')]
            elif suffix in {'.pptx','.pptm'}: wanted=[n for n in names if n.startswith('ppt/slides/') and n.endswith('.xml')]
            elif suffix in {'.xlsx','.xlsm'}: wanted=[n for n in names if (n.startswith('xl/worksheets/') or n=='xl/sharedStrings.xml') and n.endswith('.xml')]
            elif suffix in {'.odt','.ods','.odp','.epub'}: wanted=[n for n in names if n.endswith(('.xml','.xhtml','.html','.htm'))]
            else: wanted=[n for n in names if n.endswith('.xml')]
            for n in wanted[:400]:
                try:
                    raw=z.read(n)[:2_000_000].decode('utf-8','replace')
                    text=_xml_text(raw)
                    if text: chunks.append(text[:120000])
                except Exception: pass
            records.append({'kind':'office-members','content':'\\n'.join(names[:3000]),'metadata':{'member_count':len(names),'parsed_xml_members':len(wanted)}})
    except Exception as e:
        records.append({'kind':'office-error','content':f'Office/ZIP parse failed: {type(e).__name__}: {e}'[:3000]})
    return '\\n'.join(chunks)[:240000] or None,records

def pdf_extract(p):
    text=None; records=[]
    try:
        out=subprocess.check_output(['pdftotext','-layout',str(p),'-'],stderr=subprocess.DEVNULL,timeout=45)
        text=out.decode('utf-8','replace')[:240000]
    except Exception as e:
        try:
            from pypdf import PdfReader
            r=PdfReader(str(p)); text='\\n'.join((pg.extract_text() or '') for pg in r.pages[:300])[:240000]
            records.append({'kind':'pdf-pages','content':f'PDF pages: {len(r.pages)}','metadata':{'pages':len(r.pages)}})
        except Exception:
            records.append({'kind':'pdf-error','content':f'PDF text extraction failed: {type(e).__name__}'})
    return text,records

def email_extract(p):
    records=[]; chunks=[]
    try:
        if p.suffix.lower() in {'.mbox','.mailbox'}:
            box=mailbox.mbox(str(p),create=False)
            msgs=[]
            for i,msg in enumerate(box):
                if i>=250: break
                msgs.append(msg)
        else:
            msgs=[email.message_from_bytes(p.read_bytes(),policy=email_policy.default)]
        for i,msg in enumerate(msgs):
            hdr=' | '.join(f'{k}: {msg.get(k,"")}' for k in ('Date','From','To','Cc','Subject','Message-ID') if msg.get(k))
            body=[]
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() in {'text/plain','text/html'}:
                        try: body.append(part.get_content())
                        except Exception: pass
            else:
                try: body.append(msg.get_content())
                except Exception: pass
            b='\\n'.join(str(x) for x in body)
            if 'html' in str(msg.get_content_type()).lower(): b=_xml_text(b)
            chunks.append((hdr+'\\n'+b)[:120000])
            records.append({'kind':'email-message','content':(hdr+'\\n'+b)[:50000],'metadata':{'message_index':i}})
    except Exception as e:
        records.append({'kind':'email-error','content':f'Email parse failed: {type(e).__name__}: {e}'[:3000]})
    return '\\n\\n'.join(chunks)[:240000] or None,records[:250]

def archive_extract(p):
    records=[]; text=None; suffix=p.suffix.lower()
    try:
        if zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z: names=z.namelist()[:6000]
            records.append({'kind':'archive-members','content':'\\n'.join(names),'metadata':{'member_count_sampled':len(names),'format':'zip'}})
        elif tarfile.is_tarfile(p):
            with tarfile.open(p,'r:*') as t: names=[m.name for m in t.getmembers()[:6000]]
            records.append({'kind':'archive-members','content':'\\n'.join(names),'metadata':{'member_count_sampled':len(names),'format':'tar'}})
        elif suffix in {'.gz','.bz2','.xz'}:
            opener={'.gz':gzip.open,'.bz2':bz2.open,'.xz':lzma.open}[suffix]
            with opener(p,'rb') as f: data=f.read(2_000_000)
            text=data.decode('utf-8','replace')[:240000]
            records.append({'kind':'compressed-stream','content':text[:50000],'metadata':{'format':suffix.lstrip('.')}})
        else:
            try:
                out=subprocess.check_output(['7z','l','-ba',str(p)],stderr=subprocess.STDOUT,timeout=30,text=True)
                records.append({'kind':'archive-members','content':out[:200000],'metadata':{'format':'7z-compatible'}})
            except Exception as e: records.append({'kind':'archive-error','content':f'Archive inspection failed: {type(e).__name__}'})
    except Exception as e:
        records.append({'kind':'archive-error','content':f'Archive inspection failed: {type(e).__name__}: {e}'[:3000]})
    return text,records

def resolve_adapter(p,rel,category):
    mime=_mime(p); ext=p.suffix.lower() or '<no-extension>'
    strategy=category
    if category=='binary':
        lowmime=mime.lower()
        if lowmime.startswith('text/') or lowmime in {'application/json','application/xml','application/x-yaml','application/javascript'}: strategy='text'
        elif lowmime=='application/pdf': strategy='pdf'
        elif 'sqlite' in lowmime: strategy='database'
        elif lowmime.startswith('image/'): strategy='image'
        elif lowmime.startswith('audio/'): strategy='audio'
        elif lowmime.startswith('video/'): strategy='video'
        elif 'zip' in lowmime or 'tar' in lowmime or 'compressed' in lowmime: strategy='archive'
        else: strategy='binary-strings'
    key=f'ext:{ext}'
    _adapter_registry_record(key,mime,strategy,rel)
    return strategy,mime

def derive(p,rel,category):
    text=None; records=[]; obs=[]; refs=[]
    adapter,mime=resolve_adapter(p,rel,category)
    meta={'relative_path':rel,'mtime_ns':p.stat().st_mtime_ns,'category':category,'adapter':adapter,'mime':mime,'full_content_training':True}
    if adapter in {'text','social-data'}:
        text=read_text(p,240000)
    elif adapter=='database':
        records=sqlite_extract(p)
    elif adapter=='pdf':
        text,records=pdf_extract(p)
    elif adapter=='office':
        text,records=office_extract(p)
    elif adapter=='email':
        text,records=email_extract(p)
    elif adapter=='image':
        f=image_features(p); meta['image']=f; records.append({'kind':'image-features','content':json.dumps(f,ensure_ascii=False),'metadata':f})
        if isinstance(f.get('red_fraction'),float): obs.append(('visual_red_fraction',f"Observed red-pixel fraction {f['red_fraction']:.3f} in {rel}",0.85,{'red_fraction':f['red_fraction']}))
    elif adapter in {'audio','video'}:
        if adapter=='video':
            av,frames=video_visual(p); meta['av']=av; meta['frames']=frames
            records.append({'kind':'video-probe','content':json.dumps(av,ensure_ascii=False)[:50000],'metadata':{'frame_samples':len(frames)}})
            records += [{'kind':'video-frame-features','content':json.dumps(x,ensure_ascii=False),'metadata':x} for x in frames]
        else:
            av=ffprobe(p); meta['av']=av; records.append({'kind':'audio-probe','content':json.dumps(av,ensure_ascii=False)[:50000]})
    elif adapter=='archive':
        text,records=archive_extract(p)
    else:
        text=_printable_strings(p)
        records.append({'kind':'binary-strings','content':text[:120000] if text else 'No printable strings found.','metadata':{'adapter':'binary-strings','mime':mime}})
    if text:
        urls=URL.findall(text)
        for u in urls[:500]: refs.append(('url',u))
        for u in urls:
            m=YT.search(u)
            if m: refs.append(('youtube_id',m.group(1)))
        if urls: records.append({'kind':'external-urls','content':'\\n'.join(dict.fromkeys(urls))[:180000],'metadata':{'url_count':len(set(urls))}})
    m=TRACK.match(Path(rel).name)
    if m: obs.append(('playlist_position',f'{rel} has chronological/playlist ordinal {int(m.group(1))}',1.0,{'ordinal':int(m.group(1))}))
    return text,records[:260],meta,obs,refs

def emit_pattern(c,kind,key,statement,members,confidence=.95):
    pk=f'{kind}:{key}'
    if c.execute('SELECT 1 FROM emitted WHERE pattern_key=?',(pk,)).fetchone(): return
    call('runtime.datalake_pattern',{'pattern_kind':kind,'statement':statement,'members':members,'confidence':confidence,'metadata':{'pattern_key':pk}})
    c.execute('INSERT OR IGNORE INTO emitted(pattern_key,emitted_ms) VALUES(?,?)',(pk,int(time.time()*1000))); c.commit()

def process(c,row):
    rel=row['relpath']; p=ROOT/rel; category=row['category']; runtime_path=f'{RUNTIME_ROOT}/{rel}'
    if not p.is_file(): return
    text,records,meta,obs,refs=derive(p,rel,category)
    result=call('runtime.autonomy_ingest_artifact',{
        'path':runtime_path,
        'source_kind':source_kind(rel,category),
        'derived_text':text,
        'derived_records':records or [],
        'metadata':{**meta,'epistemic_policy':'full-local-archive-training','sensitive_personal_data_allowed':True,'adapter_autocreation_allowed':True},
        'training_eligible':True,
        'session_id':'datalake-ingest'
    },timeout=120)
    art=(result.get('artifact') or {}); aid=art.get('artifact_id'); sd=art.get('source_digest') or digest_file(p)
    call('runtime.datalake_observe',{'artifact_id':aid or 'unknown','source_path':runtime_path,'source_digest':sd,'observation_kind':'archive_presence','statement':f'Artifact {rel} exists in the operator data lake with witnessed digest {sd}.','confidence':1.0,'observer_id':'operator-datalake-filesystem','observer_kind':'filesystem_witness','independence_group':'operator-archive','epistemic_class':'archive_fact','metadata':{'relative_path':rel,'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,'training_eligible':True,'adapter':meta.get('adapter'),'mime':meta.get('mime')}})
    for kind,statement,conf,om in obs:
        call('runtime.datalake_observe',{'artifact_id':aid or 'unknown','source_path':runtime_path,'source_digest':sd,'observation_kind':kind,'statement':statement,'confidence':conf,'observer_id':'wgrnn-local-media-analysis','observer_kind':'machine_perception','independence_group':'local-media-analysis','epistemic_class':'machine_derived','metadata':om})
    c.execute("UPDATE files SET shake256_512=?,artifact_id=?,stage='done',processed_ms=?,last_error=NULL,training_stage='pending',training_next_chunk=0,training_chunk_count=NULL,training_attempts=0,training_error=NULL,trained_ms=NULL WHERE relpath=?",(sd,aid,int(time.time()*1000),rel))
    for typ,val in refs: c.execute('INSERT OR IGNORE INTO refs(ref_type,ref_value,relpath) VALUES(?,?,?)',(typ,val,rel))
    c.commit()
    dups=c.execute("SELECT relpath FROM files WHERE shake256_512=? AND stage='done' ORDER BY relpath",(sd,)).fetchall()
    if len(dups)>1: emit_pattern(c,'content_identity',sd,f'{len(dups)} data-lake paths contain byte-identical content.',[{'path':x['relpath'],'digest':sd} for x in dups],1.0)
    for typ,val in refs:
        paths=c.execute('SELECT relpath FROM refs WHERE ref_type=? AND ref_value=? ORDER BY relpath',(typ,val)).fetchall()
        if len(paths)>1 and typ=='youtube_id': emit_pattern(c,'recursive_external_reference',val,f'YouTube object {val} is referenced by {len(paths)} archived artifacts.',[{'path':x['relpath'],'youtube_id':val} for x in paths],.95)

def source_kind(rel,category):
    low=rel.lower()
    if low.startswith('mediacms/'): return 'mediacms-library'
    if low.startswith('social/') or 'facebook' in low: return 'operator-social-archive'
    if low.startswith('music/'): return 'operator-chronological-music'
    return 'xavi-datalake-'+category

def work(c,limit):
    rows=c.execute("SELECT * FROM files WHERE stage IN ('new','error') AND attempts<6 ORDER BY priority,discovered_ms LIMIT ?",(limit,)).fetchall(); ok=err=0
    for r in rows:
        try: process(c,r); ok+=1; print('ok',r['category'],r['relpath'],flush=True)
        except Exception as e:
            msg=f'{type(e).__name__}: {e}'
            lowmsg=msg.lower(); transient=('connection refused' in lowmsg or 'connection reset' in lowmsg or 'broken pipe' in lowmsg or 'connection aborted' in lowmsg or 'timed out' in lowmsg or 'temporary failure' in lowmsg or 'remote end closed' in lowmsg or 'xavi_mcp_api_key' in lowmsg)
            if transient:
                # Runtime/MCP availability is infrastructure state, not evidence quality.
                c.execute('UPDATE files SET stage=\'new\',last_error=? WHERE relpath=?',(msg[:1000],r['relpath'])); c.commit(); print('paused-runtime-unavailable',r['relpath'],msg[:180],flush=True); break
            err+=1; c.execute('UPDATE files SET stage=\'error\',attempts=attempts+1,last_error=? WHERE relpath=?',(msg[:1000],r['relpath'])); c.commit(); print('error',r['relpath'],type(e).__name__,str(e)[:180],flush=True)
    return ok,err,len(rows)

def status(c):
    return {r['stage']:r['n'] for r in c.execute('SELECT stage,COUNT(*) n FROM files GROUP BY stage')}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--once',action='store_true'); ap.add_argument('--scan-only',action='store_true'); ap.add_argument('--limit',type=int,default=int(os.getenv('XAVI_DATALAKE_BATCH','12'))); ap.add_argument('--interval',type=int,default=int(os.getenv('XAVI_DATALAKE_INTERVAL','10'))); ap.add_argument('--scan-interval',type=int,default=int(os.getenv('XAVI_DATALAKE_SCAN_INTERVAL','900'))); a=ap.parse_args()
    c=conn(); last_scan=0.0
    while True:
        now=time.monotonic()
        if last_scan == 0.0 or now-last_scan >= max(60,a.scan_interval):
            n=scan(c); last_scan=time.monotonic(); print('scan_files',n,'state',status(c),flush=True)
        active_research=research_active()
        if not a.scan_only and not active_research:
            ok,er,total=work(c,max(1,min(a.limit,100))); print('batch',{'ok':ok,'error':er,'selected':total,'state':status(c)},flush=True)
        elif not a.scan_only and active_research:
            print('ingest yielding-research',{'mode':'pause-runtime-writes','state':status(c)},flush=True)
        if a.once: break
        time.sleep(max(24,a.interval) if active_research else max(2,a.interval))
if __name__=='__main__': main()
