from __future__ import annotations

try:
    from .xavi_crypto import kmac256_hex, shake256_hex, shake256_ref
except ImportError:
    from xavi_crypto import kmac256_hex, shake256_hex, shake256_ref

import hmac
import json
import re
import uuid
from pathlib import Path
from typing import Any

_SAFE_SESSION = re.compile(r"^mcp_[0-9a-f]{32}\.[0-9a-f]{24}$")
_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.-])(/(?:var/www/xavi|home/tbi|etc/(?:nginx|caddy|systemd|containers))/[^\s'\";|&<>)]*)")
_MUTATION_RE = re.compile(
    r"(?:cat\s*>|>>\s*[^&]|\.write_text\s*\(|\.write_bytes\s*\(|\.replace\s*\(|"
    r"\bsed\s+-i\b|\bperl\s+-pi\b|\btee\s+|\b(?:cp|mv|rm|mkdir|touch|chmod|chown|install)\s+|"
    r"\bgit\s+(?:add|commit|merge|rebase|checkout|switch|pull|push|reset|clean|tag)\b|"
    r"\bpodman\s+(?:build|run|start|stop|restart|rm|create|compose\s+up)\b|"
    r"\bsystemctl(?:\s+--user)?\s+(?:restart|start|stop|enable|disable|daemon-reload)\b|"
    r"\b(?:CREATE|ALTER|DROP|TRUNCATE|INSERT|UPDATE|DELETE|GRANT|REVOKE)\s+(?:TABLE|SCHEMA|INDEX|ROLE|INTO|FROM|ON)?\b|"
    r"curl[^\n]*(?:-X|--request)\s*(?:POST|PUT|PATCH|DELETE)|"
    r"concrete(?:5)?[^\n]*(?:package:(?:install|update)|c5:package:(?:install|update))|"
    r"podman\s+compose\s+(?:up|down|restart|build))",
    re.IGNORECASE,
)
_COORDINATION_TOOLS = {"coordination.begin","coordination.status","coordination.plan","coordination.claim","coordination.preflight","coordination.heartbeat","coordination.event","coordination.search","coordination.release","coordination.finish"}
_LOCAL_MUTATORS = {"apply_vscode_model_aliases","rebuild_runtime_image","restart_runtime_only","ops_allowed_command","ollama_pull","ollama_copy_tag","ollama_create_tag","vscode_router_policy_set","cpu_worker_policy_set","bounded_command_creator","bounded_job_kill"}
_LOCAL_READ_ONLY = {"search","fetch","host_status","runtime_containers","runtime_tail","adapter_tail","repo_overview","repo_diff_all","runtime_test_contracts","nginx_dev_config","service_status","ollama_inventory","ollama_probe","model_benchmark","remote_node_health","repo_index_snapshot","cpu_worker_policy_get","vscode_router_policy_get","bounded_command_list","bounded_job_status","bounded_job_output","bounded_job_list","git_status","git_diff_v3","runtime_health","runtime_models"}

def digest(value: Any) -> str:
    text=json.dumps(value,sort_keys=True,separators=(",",":"),default=str)
    return shake256_ref(text)

def _session_signature(raw:str,secret:str)->str:
    return kmac256_hex(secret, raw, custom=b"Xavi-MCP-Session-v1")[:24]

def issue_session(secret:str)->str:
    raw=uuid.uuid4().hex
    return f"mcp_{raw}.{_session_signature(raw,secret)}"

def valid_session(value:str|None,secret:str)->bool:
    if not value or not _SAFE_SESSION.fullmatch(value): return False
    raw,supplied=value[4:].split(".",1)
    return hmac.compare_digest(supplied,_session_signature(raw,secret))

def _deterministic_session(request:Any,secret:str)->str:
    headers=request.headers
    client_name=str(headers.get("x-xavi-client-name") or headers.get("x-xavi-agent-id") or "mcp-client")
    device=str(headers.get("x-xavi-device-id") or headers.get("x-device-id") or "")
    user_agent=str(headers.get("user-agent") or "unknown-client")
    forwarded=str(headers.get("x-forwarded-for") or "").split(",",1)[0].strip()
    raw=shake256_hex(f"{client_name}\n{device}\n{user_agent}\n{forwarded}")[:32]
    return f"mcp_{raw}.{_session_signature(raw,secret)}"

def resolve_session(request:Any,secret:str)->str:
    candidates=[request.headers.get("mcp-session-id"),request.headers.get("x-mcp-session-id"),request.headers.get("x-xavi-session-id"),request.cookies.get("xavi_mcp_session") if hasattr(request,"cookies") else None]
    for value in candidates:
        if valid_session(value,secret): return str(value)
    return _deterministic_session(request,secret)

def session_context(request:Any,clients:dict[str,dict[str,Any]])->dict[str,Any]:
    session_id=str(getattr(request.state,"xavi_session_id","") or "")
    client=clients.get(session_id,{})
    client_info=client.get("client_info") if isinstance(client.get("client_info"),dict) else {}
    client_name=str(client_info.get("name") or request.headers.get("x-xavi-client-name") or "mcp-client")[:120]
    version=str(client_info.get("version") or "")[:80]
    user_agent=str(request.headers.get("user-agent") or "unknown-client")[:500]
    agent_base=re.sub(r"[^A-Za-z0-9_.:-]+","-",client_name).strip("-") or "mcp-client"
    conversation_id=str(getattr(request.state,"xavi_conversation_id","") or "")[:256]
    conversation_source=str(getattr(request.state,"xavi_conversation_source","") or "mcp")[:80]
    source_conversation_id=str(getattr(request.state,"xavi_source_conversation_id","") or "")[:256]
    continued_from=str(getattr(request.state,"xavi_continued_from_conversation_id","") or "")[:256]
    return {"session_id":session_id,"agent_id":f"{agent_base}:{session_id[4:16]}","device_id_digest":digest(request.headers.get("x-xavi-device-id") or user_agent),"client_name":client_name,"user_agent":user_agent,"conversation_id":conversation_id,"conversation_source":conversation_source,"source_conversation_id":source_conversation_id,"continued_from_conversation_id":continued_from,"session_metadata":{"client_version":version,"protocol":client.get("protocol_version"),"conversation_id":conversation_id,"conversation_source":conversation_source,"source_conversation_id":source_conversation_id}}

def inject_identity(args:dict[str,Any],context:dict[str,Any])->dict[str,Any]:
    clean=dict(args or {})
    for key in ("session_id","agent_id","device_id_digest","client_name","user_agent","conversation_id","conversation_source","source_conversation_id","continued_from_conversation_id","session_metadata"):
        value=context.get(key)
        if value not in (None, ""):
            clean[key]=value
    return clean

def prioritize_tools(tools:list[dict[str,Any]])->list[dict[str,Any]]:
    return sorted(tools,key=lambda tool:(0 if str(tool.get("name","")).startswith(("coordination.","task.")) else 1))

def _registry_command(registry_path:Path,name:str)->dict[str,Any]|None:
    try:
        command=json.loads(registry_path.read_text()).get("commands",{}).get(str(name or "").strip())
        return command if isinstance(command,dict) else None
    except Exception:return None

def _command_text(command:dict[str,Any])->str:
    return "\n".join(str(value) for value in command.get("argv",[]) or [])

def _command_mutates(command:dict[str,Any])->bool:
    explicit=command.get("mutating")
    return explicit if isinstance(explicit,bool) else bool(_MUTATION_RE.search(_command_text(command)))

def _path_resource(value:Any,repo_root:Path|None=None)->str|None:
    text=str(value or "").strip()
    if not text:return None
    path=Path(text).expanduser()
    if not path.is_absolute() and repo_root is not None:path=repo_root/path
    try:path=path.resolve()
    except Exception:pass
    return "path:"+str(path)

def _command_resources(command:dict[str,Any],repo_root:Path)->list[str]:
    explicit=command.get("resources")
    if isinstance(explicit,list) and explicit:return [str(v).strip() for v in explicit if str(v).strip()][:100]
    paths=[]
    for match in _PATH_RE.findall(_command_text(command)):
        resource=_path_resource(match.rstrip(".,:]"),repo_root)
        if resource and resource not in paths:paths.append(resource)
    if paths:return paths[:40]
    # A command's working directory is context, not an exclusive mutation target.
    # Generic/admin commands without an exact inferred or explicit resource must
    # remain visible on the coordination board without fencing the whole tree.
    return []

def _runtime_tool_metadata(tools:list[dict[str,Any]],name:str)->dict[str,Any]:
    return next((tool for tool in tools if tool.get("name")==name),{})

def classify_and_infer(name:str,args:dict[str,Any],tools:list[dict[str,Any]],registry_path:Path,repo_root:Path,runtime_dir:Path)->dict[str,Any]:
    name=str(name or "");args=args or {};project_key=str(args.get("project_key") or "xavi.app-backend");title=f"MCP: {name}";objective=f"Coordinate automatic preflight for mutating tool {name}.";resources=[]
    if name.startswith(("coordination.","task.")) or name=="runtime.session_append":return {"mutating":False,"resources":[],"project_key":project_key}
    if name=="dev_rpc":
        mutating=str(args.get("action") or "") in {"write_file","append_file","replace_text"}
        resource=_path_resource(args.get("path"),repo_root) if mutating else None
        return {"mutating":mutating,"resources":[resource] if resource else [],"project_key":project_key,"title":title,"objective":objective}
    if name=="bounded_command_creator":
        resources=["path:"+str(registry_path.resolve())]+([str(v) for v in args.get("resources",[]) if str(v).strip()] if isinstance(args.get("resources"),list) else [])
        return {"mutating":True,"resources":list(dict.fromkeys(resources)),"project_key":project_key,"title":str(args.get("work_title") or args.get("title") or title),"objective":str(args.get("description") or objective)}
    if name=="bounded_job_start":
        command=_registry_command(registry_path,str(args.get("name") or ""))
        if not command:return {"mutating":False,"resources":[],"project_key":project_key,"title":title,"objective":objective}
        mutating=_command_mutates(command)
        return {"mutating":mutating,"resources":_command_resources(command,repo_root) if mutating else [],"project_key":str(command.get("project_key") or project_key),"title":str(command.get("work_title") or command.get("title") or title),"objective":str(command.get("description") or objective),"command_name":args.get("name")}
    if name=="bounded_job_kill":return {"mutating":True,"resources":[f"job:{args.get('job_id') or 'unknown'}"],"project_key":project_key,"title":title,"objective":objective}
    if name in _LOCAL_READ_ONLY:return {"mutating":False,"resources":[],"project_key":project_key}
    if name in _LOCAL_MUTATORS:
        mapping={"apply_vscode_model_aliases":["path:"+str((runtime_dir/"config/models.json").resolve())],"vscode_router_policy_set":["path:"+str((runtime_dir/"config/vscode_router_policy.json").resolve())],"cpu_worker_policy_set":["path:"+str((runtime_dir/"config/cpu_worker_policy.json").resolve())],"rebuild_runtime_image":["image:duotronic-runtime","path:"+str(runtime_dir.resolve())],"restart_runtime_only":["service:duotronic-runtime"],"ops_allowed_command":[f"ops:{args.get('name') or 'unknown'}"],"ollama_pull":[f"model:{args.get('model') or 'unknown'}"],"ollama_copy_tag":[f"model:{args.get('destination') or 'unknown'}"],"ollama_create_tag":[f"model:{args.get('name') or 'unknown'}"]}
        return {"mutating":True,"resources":mapping.get(name,[f"tool:{name}"]),"project_key":project_key,"title":title,"objective":objective}
    metadata=_runtime_tool_metadata(tools,name)
    if metadata:
        mutating=metadata.get("read_only") is False
        if not mutating:return {"mutating":False,"resources":[],"project_key":project_key}
        candidates=[]
        for key in ("path","file","repo","repo_path","worktree","cwd","target_path"):
            if args.get(key):candidates.append(args[key])
        for key in ("paths","files","resources"):
            if isinstance(args.get(key),list):candidates.extend(args[key])
        for value in candidates:
            text=str(value)
            resource=text if text.startswith(("path:","service:","database:","route:","repo:","tool:")) else _path_resource(text,repo_root)
            if resource:resources.append(resource)
        if not resources:
            if name.startswith("repo.") or name=="dev.apply_change_bundle":resources=["repo:"+str(repo_root.resolve())]
            elif name.startswith("ops."):resources=[f"ops:{name}"]
            elif name.startswith("runtime.wgrnn_") or name=="runtime.run_inference":resources=["runtime:wgrnn-memory"]
            else:resources=[f"tool:{name}"]
        return {"mutating":True,"resources":list(dict.fromkeys(resources)),"project_key":project_key,"title":title,"objective":objective}
    return {"mutating":False,"resources":[],"project_key":project_key}

def conflict_summary(preflight:dict[str,Any])->dict[str,Any]:
    conflicts=[]
    for row in preflight.get("conflicts",[]) or []:
        if isinstance(row,dict):conflicts.append({"resource_key":row.get("resource_key"),"requested_resource":row.get("requested_resource"),"agent_id":row.get("agent_id"),"session_id":row.get("session_id"),"work_id":str(row.get("work_id")) if row.get("work_id") else None,"work_title":row.get("work_title"),"work_objective":row.get("work_objective"),"purpose":row.get("purpose"),"expires_at":str(row.get("expires_at")) if row.get("expires_at") else None})
    return {"message":"Mutating MCP call blocked by another session editing the exact same resource","conflicts":conflicts}
