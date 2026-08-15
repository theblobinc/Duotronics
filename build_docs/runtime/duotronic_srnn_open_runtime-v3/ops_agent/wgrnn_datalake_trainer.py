#!/var/www/xavi/.venv/bin/python
from __future__ import annotations
import argparse, importlib.util, json, os, sqlite3, time
from pathlib import Path

INGEST_PATH=Path('/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/ops_agent/wgrnn_datalake_ingest.py')
spec=importlib.util.spec_from_file_location('wgrnn_datalake_ingest_shared',INGEST_PATH)
ingest=importlib.util.module_from_spec(spec); spec.loader.exec_module(ingest)
ROOT=ingest.ROOT; RUNTIME_ROOT=ingest.RUNTIME_ROOT
SESSION='service:wgrnn-datalake-trainer'
CHUNK_CHARS=max(1000,min(int(os.getenv('XAVI_DATALAKE_TRAIN_CHARS','9000')),11000))
EXPERIMENT_ACTIVE_PATH=Path(os.getenv('XAVI_NODE_WORK_EXPERIMENT_ACTIVE','/home/tbi/.local/state/xavi-wgrnn-node-workloads/experiment.active.json'))
EXPERIMENT_ACTIVE_TTL=max(120,min(int(os.getenv('XAVI_DATALAKE_EXPERIMENT_ACTIVE_TTL','480')),1800))

def experiment_active():
    try:
        return (time.time()-EXPERIMENT_ACTIVE_PATH.stat().st_mtime) < EXPERIMENT_ACTIVE_TTL
    except OSError:
        return False

def chunks_for(path:Path,rel:str,category:str):
    text,records,meta,_obs,_refs=ingest.derive(path,rel,category)
    out=[]
    def add(value,derivation,metadata=None):
        value=str(value or '')
        for off in range(0,len(value),CHUNK_CHARS):
            chunk=value[off:off+CHUNK_CHARS]
            if chunk.strip(): out.append((chunk,derivation,{**(metadata or {}),'offset':off}))
    if text: add(text,'derived-text',{'adapter':meta.get('adapter')})
    for rec in records or []:
        if not isinstance(rec,dict): continue
        value=rec.get('content') or rec.get('text') or ''
        add(value,str(rec.get('kind') or 'derived-record'),rec.get('metadata') if isinstance(rec.get('metadata'),dict) else {})
    return out,meta

def process_one(c,row,chunk_limit:int):
    rel=row['relpath']; path=ROOT/rel
    if not path.is_file():
        c.execute("UPDATE files SET training_stage='error',training_attempts=training_attempts+1,training_error=? WHERE relpath=?",('source missing',rel)); c.commit(); return 0,False
    chunks,meta=chunks_for(path,rel,row['category'])
    total=len(chunks); start=max(0,int(row['training_next_chunk'] or 0))
    c.execute('UPDATE files SET training_chunk_count=?,training_error=NULL WHERE relpath=?',(total,rel)); c.commit()
    if total==0:
        c.execute("UPDATE files SET training_stage='done',training_next_chunk=0,trained_ms=?,training_error=NULL WHERE relpath=?",(int(time.time()*1000),rel)); c.commit(); return 0,True
    sent=0
    for idx in range(start,min(total,start+max(1,chunk_limit))):
        content,derivation,chunk_meta=chunks[idx]
        result=ingest.call('runtime.training_observe',{
            'artifact_id':row['artifact_id'] or 'unknown',
            'source_path':f'{RUNTIME_ROOT}/{rel}',
            'source_digest':row['shake256_512'] or ingest.digest_file(path),
            'chunk_index':idx,
            'content':content,
            'adapter':meta.get('adapter'),
            'mime_type':meta.get('mime'),
            'derivation':derivation,
            'metadata':{'relative_path':rel,'chunk_count':total,**chunk_meta},
            'session_id':SESSION,
        },timeout=90)
        learning=result.get('recurrent_learning')
        if isinstance(learning,dict) and learning.get('status')=='error':
            raise RuntimeError('recurrent learning returned error: '+str(learning.get('error') or 'unknown'))
        sent+=1
        c.execute("UPDATE files SET training_stage='training',training_next_chunk=?,training_error=NULL WHERE relpath=?",(idx+1,rel)); c.commit()
    done=(start+sent)>=total
    if done:
        c.execute("UPDATE files SET training_stage='done',training_next_chunk=?,trained_ms=?,training_error=NULL WHERE relpath=?",(total,int(time.time()*1000),rel)); c.commit()
    return sent,done

def eligible_rows(c,limit):
    return c.execute("SELECT * FROM files WHERE stage='done' AND artifact_id IS NOT NULL AND training_stage IN ('pending','training','error') AND training_attempts<8 ORDER BY priority,COALESCE(processed_ms,discovered_ms),relpath LIMIT ?",(limit,)).fetchall()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--once',action='store_true'); ap.add_argument('--file-limit',type=int,default=1); ap.add_argument('--chunk-limit',type=int,default=2); ap.add_argument('--interval',type=int,default=12); a=ap.parse_args()
    c=ingest.conn()
    while True:
        active_experiment=experiment_active()
        file_limit=max(1,min(a.file_limit,8))
        chunk_limit=1 if active_experiment else max(1,min(a.chunk_limit,8))
        rows=[] if active_experiment else eligible_rows(c,file_limit)
        if active_experiment:
            print('trainer yielding-experiment',{'mode':'pause-recurrent-learning'},flush=True)
        if not rows and not active_experiment:
            print('trainer idle',flush=True)
        for row in rows:
            rel=row['relpath']
            try:
                sent,done=process_one(c,row,chunk_limit)
                print('trained',{'relpath':rel,'chunks_sent':sent,'done':done},flush=True)
            except Exception as e:
                msg=f'{type(e).__name__}: {e}'
                low=msg.lower(); transient=any(x in low for x in ('connection refused','connection reset','remote end closed','timed out','broken pipe','temporarily unavailable'))
                if transient:
                    c.execute("UPDATE files SET training_stage=CASE WHEN training_next_chunk>0 THEN 'training' ELSE 'pending' END,training_error=? WHERE relpath=?",(msg[:1000],rel)); c.commit(); print('trainer paused-runtime',rel,type(e).__name__,flush=True); break
                c.execute("UPDATE files SET training_stage='error',training_attempts=training_attempts+1,training_error=? WHERE relpath=?",(msg[:1000],rel)); c.commit(); print('trainer error',rel,type(e).__name__,flush=True)
        if a.once: break
        time.sleep(max(24,a.interval) if active_experiment else max(3,a.interval))
if __name__=='__main__': main()
