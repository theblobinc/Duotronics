from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import HTTPException

from .skill_library import SkillLibrary


def skill_tool_manifest() -> list[dict[str, Any]]:
    return [
        {"name":"skills.list","description":"List mounted Agent Skills as metadata only, optionally filtered by namespace.","read_only":True,"input_schema":{"type":"object","properties":{"namespace":{"type":["string","null"]}},"additionalProperties":False}},
        {"name":"skills.read","description":"Read one selected, path-contained SKILL.md document.","read_only":True,"input_schema":{"type":"object","required":["name"],"properties":{"name":{"type":"string","minLength":1}},"additionalProperties":False}},
        {"name":"skills.search","description":"Search mounted Agent Skills and return digest-backed excerpts.","read_only":True,"input_schema":{"type":"object","required":["query"],"properties":{"query":{"type":"string","minLength":1},"namespace":{"type":["string","null"]},"limit":{"type":"integer","minimum":1,"maximum":20,"default":8}},"additionalProperties":False}},
    ]


def _library(corpus_dir: Path) -> SkillLibrary: return SkillLibrary(corpus_dir / "skills")


def skill_resources(corpus_dir: Path | None) -> list[dict[str,str]]:
    resources=[{"uri":"skills://","name":"Agent Skill catalog","description":"Metadata catalog for all mounted Agent Skills.","mimeType":"application/json"}]
    if corpus_dir is None: return resources
    items=_library(corpus_dir).list().get("items",[])
    namespaces=sorted({str(item.get("namespace") or "default") for item in items})
    for namespace in namespaces:
        resources.append({"uri":f"skills://{namespace}","name":f"{namespace} skill catalog","description":f"Metadata catalog for {namespace} Agent Skills.","mimeType":"application/json"})
    for item in items:
        path=str(item.get("path") or ""); parts=path.split("/")
        if len(parts)<3: continue
        namespace=parts[0]; slug=parts[-2]
        resources.append({"uri":f"skills://{namespace}/{slug}/skill.md","name":str(item.get("name") or slug),"description":str(item.get("description") or "Agent Skill"),"mimeType":"text/markdown"})
    return resources


async def call_skill_tool(corpus_dir: Path, tool: str, args: dict[str,Any]) -> dict[str,Any]:
    aliases={"runtime.skills_list":"skills.list","runtime.skills_read":"skills.read","runtime.skills_search":"skills.search"}; tool=aliases.get(tool,tool); lib=_library(corpus_dir)
    if tool=="skills.list": return lib.list(namespace=args.get("namespace"))
    if tool=="skills.read":
        try: return lib.read(str(args.get("name","")))
        except (ValueError,FileNotFoundError) as exc: raise HTTPException(status_code=404 if isinstance(exc,FileNotFoundError) else 422,detail=str(exc)) from exc
    if tool=="skills.search":
        try: return lib.search(str(args.get("query","")),limit=int(args.get("limit",8)),namespace=args.get("namespace"))
        except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    raise HTTPException(status_code=404,detail=f"unknown skill MCP tool: {tool}")


def _name_from_uri(uri: str) -> tuple[str | None,str | None]:
    if uri=="skills://": return "", ""
    if uri.startswith("skills://"):
        tail=unquote(uri[len("skills://"):]).strip("/")
        if "/" not in tail: return tail,""
        namespace,rest=tail.split("/",1)
        if rest.endswith("/skill.md"): rest=rest[:-len("/skill.md")]
        return namespace,rest
    legacy="xavi-runtime://skills/"
    if uri.startswith(legacy):
        tail=unquote(uri[len(legacy):]).strip("/")
        if "/" not in tail: return tail,""
        return tuple(tail.split("/",1))
    return None,None


async def read_skill_resource(corpus_dir: Path, uri: str) -> dict[str,Any] | None:
    namespace,name=_name_from_uri(uri)
    if namespace is None: return None
    lib=_library(corpus_dir)
    if namespace=="" and name=="": return {"uri":uri,"mimeType":"application/json","contents":lib.list()}
    if name=="": return {"uri":uri,"mimeType":"application/json","contents":lib.list(namespace=namespace)}
    try: item=lib.read(f"{namespace}/{name}")
    except (ValueError,FileNotFoundError) as exc: raise HTTPException(status_code=404 if isinstance(exc,FileNotFoundError) else 422,detail=str(exc)) from exc
    return {"uri":uri,"mimeType":"text/markdown","contents":item["content"],"metadata":{k:v for k,v in item.items() if k!="content"}}
