import importlib.util, inspect, os, sys, tempfile, time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.environ['XAVI_OPS_RUNTIME_DIR'] = str(root.parent)
os.environ['XAVI_OPS_REPO_ROOT'] = str(root.parent)
os.environ['XAVI_MCP_TOOLS_CACHE_TTL'] = '5'
os.environ['XAVI_MCP_TOOLS_REFRESH_TIMEOUT'] = '1'

spec = importlib.util.spec_from_file_location('adapter_fastpath_test', root/'xavi_dev_mcp_adapter.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
assert a.SERVER_VERSION == '0.3.1-fastpath'
assert not inspect.iscoroutinefunction(a.mcp_root), 'MCP handler must be sync for FastAPI worker pool'

# stale-while-revalidate: stale schema must return without waiting on a slow refresh.
key = a._tools_cache_key(None)
a._RUNTIME_TOOLS_CACHE[key] = (time.monotonic()-100, [{'name':'runtime.old','inputSchema':{}}])
a._MERGED_TOOLS_CACHE.clear()
calls = {'n':0}
def slow_rpc(method, params=None, timeout=30, auth_header=None, session_id=None, agent_id=None):
    calls['n'] += 1
    time.sleep(.30)
    return {'result': {'tools': [{'name':'runtime.new','inputSchema':{}}]}}
a.runtime_mcp_rpc = slow_rpc
st = time.perf_counter(); tools = a.runtime_mcp_tools(None); dt = time.perf_counter()-st
assert dt < .08, dt
assert tools[0]['name'] == 'runtime.old'
time.sleep(.40)
assert a._RUNTIME_TOOLS_CACHE[key][1][0]['name'] == 'runtime.new'

# Ledger must enqueue without waiting on its slow network writer.
class State: xavi_session_id='test-session'
class Req:
    headers={'authorization':'Bearer test','user-agent':'test'}
    state=State()
def slow_tool(*args, **kwargs):
    time.sleep(.25)
    return {}
a.runtime_mcp_tool_call = slow_tool
st=time.perf_counter(); a._ledger_append_safe(request=Req(),event_type='test',actor='test',content={'x':1},tags=['test']); ledger_dt=time.perf_counter()-st
assert ledger_dt < .05, ledger_dt

# Collaboration must schedule without waiting on awareness RPCs.
def slow_awareness(*args, **kwargs):
    time.sleep(.25)
    return {'schema':'test'}
a._collaboration_awareness = slow_awareness
st=time.perf_counter(); first=a._schedule_collaboration_awareness(Req(),'proj',{'tool_name':'x'}); collab_dt=time.perf_counter()-st
assert collab_dt < .05, collab_dt
time.sleep(.35)
second=a._schedule_collaboration_awareness(Req(),'proj',{'tool_name':'x'})
assert second and second['schema']=='test'

# run_fixed must cap huge output and complete.
r=a.run_fixed([sys.executable,'-c','import sys;sys.stdout.write("x"*2000000)'], root, timeout=5)
assert r['returncode']==0
assert len(r['stdout'].encode()) <= a.RUN_FIXED_OUTPUT_BYTES + 200
assert 'truncated' in r['stdout']

# host_status must cache repeated calls.
count={'n':0}
def fake_run(cmd,cwd,timeout):
    count['n']+=1
    return {'command':' '.join(cmd),'returncode':0,'duration_ms':1,'stdout':'ok','stderr':''}
a._run_text=fake_run
if hasattr(a.tool_host_status,'_cache'): delattr(a.tool_host_status,'_cache')
h1=a.tool_host_status({}); h2=a.tool_host_status({})
assert count['n']==3, count
assert 'cache_age_ms' in h2

spec2=importlib.util.spec_from_file_location('ops_fastpath_test', root/'xavi_ops_agent.py')
o=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(o)
assert not inspect.iscoroutinefunction(o.call), 'Ops /call handler must be sync for FastAPI worker pool'
assert not inspect.iscoroutinefunction(o.health)

# Ops run_cmd also caps large output and times out a process group cleanly.
r2=o.run_cmd([sys.executable,'-c','print("y"*100000)'], cwd=root, timeout=5)
assert r2['returncode']==0
assert len(r2['stdout'].encode()) <= o.MAX_OUTPUT + 200
rt=o.run_cmd([sys.executable,'-c','import time;time.sleep(5)'], cwd=root, timeout=1)
assert rt['returncode']==124 and rt['timed_out']

print('FASTPATH_TEST=PASS')
print(f'stale_cache_return_ms={dt*1000:.2f}')
print(f'ledger_enqueue_ms={ledger_dt*1000:.2f}')
print(f'collab_schedule_ms={collab_dt*1000:.2f}')
print(f'run_fixed_return_chars={len(r["stdout"])}')
print(f'ops_run_cmd_return_chars={len(r2["stdout"])}')
