from __future__ import annotations

import json
import os
import re
import time
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "xavi-copilot-agent:latest")

LOCAL_MODEL_PREFIXES = (
    "xavi-copilot-agent",
    "wgrnn",
    "qwen",
    "llama",
    "dolphin",
    "mistral",
    "codellama",
    "deepseek",
    "starcoder",
)

app = FastAPI(title="Xavi Ollama Tool Proxy")


def log(msg: str) -> None:
    print(f"[xavi-ollama-tool-proxy] {msg}", flush=True)


def normalize_model(model: Any) -> str:
    if not isinstance(model, str) or not model.strip():
        return DEFAULT_MODEL

    m = model.strip()

    if m == "xavi-copilot-agent":
        return "xavi-copilot-agent:latest"

    if m.startswith(LOCAL_MODEL_PREFIXES):
        return m

    log(f"remapping non-local model {m!r} -> {DEFAULT_MODEL!r}")
    return DEFAULT_MODEL


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = (text or "").strip()
    if not text:
        return None

    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    return None




def extract_tool_call_object(text: str) -> dict[str, Any] | None:
    """
    Extract the first actionable tool call from model text.

    Handles:
      {"name":"insert_edit_into_file","arguments":{...}}

      {"name":"insert_edit_into_file","arguments":{...}}
      {"name":"task_complete","arguments":{...}}

    Prefer real action tools over task_complete.
    """
    text = (text or "").strip()
    if not text:
        return None

    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    decoder = json.JSONDecoder()
    objs = []
    i = 0

    while i < len(text):
        # Move to next object start.
        j = text.find("{", i)
        if j == -1:
            break

        try:
            obj, end = decoder.raw_decode(text[j:])
            if isinstance(obj, dict):
                objs.append(obj)
            i = j + max(end, 1)
        except Exception:
            i = j + 1

    # Fallback to the old extractor if needed.
    if not objs:
        obj = extract_json_object(text)
        if isinstance(obj, dict):
            objs.append(obj)

    tool_objs = [
        obj for obj in objs
        if isinstance(obj, dict)
        and isinstance(obj.get("name"), str)
        and isinstance(obj.get("arguments"), dict)
    ]

    if not tool_objs:
        return None

    # Prefer actual edit/read/run tools over completion markers.
    for obj in tool_objs:
        if obj.get("name") not in {"task_complete", "done", "final"}:
            return obj

    return tool_objs[0]


def normalize_tool_arguments(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize common model-produced argument variants. This does not know every
    VS Code schema, but fixes the variants we are seeing from local models.
    """
    if not isinstance(args, dict):
        return {}

    out = dict(args)

    workspace_root = os.getenv(
        "XAVI_WORKSPACE_ROOT",
        "/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3",
    )

    def normalize_path_value(v):
        if not isinstance(v, str) or not v:
            return v
        if v.startswith("/"):
            return v
        return workspace_root.rstrip("/") + "/" + v.lstrip("./")

    if name == "insert_edit_into_file":
        # Common camelCase aliases.
        if "file_path" in out and "filePath" not in out:
            out["filePath"] = out["file_path"]
        if "path" in out and "filePath" not in out:
            out["filePath"] = out["path"]

        if "new_content" in out and "textToInsert" not in out:
            out["textToInsert"] = out["new_content"]

        # If the model provides an insertion anchor, preserve it. Some hosts
        # accept insertion_point; others only accept lineNumber. Do not invent
        # a line number here.
        if "insertion_point" in out and "insertionPoint" not in out:
            out["insertionPoint"] = out["insertion_point"]

        if "filePath" in out:
            out["filePath"] = normalize_path_value(out["filePath"])

    if name == "replace_string_in_file":
        if "file_path" in out and "filePath" not in out:
            out["filePath"] = out["file_path"]
        if "path" in out and "filePath" not in out:
            out["filePath"] = out["path"]
        if "search_string" in out and "searchString" not in out:
            out["searchString"] = out["search_string"]
        if "replacement_string" in out and "replacementString" not in out:
            out["replacementString"] = out["replacement_string"]

        if "filePath" in out:
            out["filePath"] = normalize_path_value(out["filePath"])

    for key in ("filePath", "path"):
        if key in out:
            out[key] = normalize_path_value(out[key])

    return out


def looks_like_tool_call(obj: dict[str, Any]) -> bool:
    return isinstance(obj.get("name"), str) and isinstance(obj.get("arguments"), dict)


def openai_tool_call_from_obj(obj: dict[str, Any]) -> dict[str, Any]:
    name = obj["name"]
    args = normalize_tool_arguments(name, obj.get("arguments", {}))
    return {
        "id": f"call_{uuid.uuid4().hex[:24]}",
        "type": "function",
        "function": {
            "name": name,
            "arguments": json.dumps(args, separators=(",", ":")),
        },
    }


def openai_response(model: str, message: dict[str, Any], finish_reason: str = "stop") -> dict[str, Any]:
    return {
        "id": f"chatcmpl_{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


def openai_empty_response(model: str) -> dict[str, Any]:
    return openai_response(model, {"role": "assistant", "content": ""}, "stop")


def repair_openai_response(data: dict[str, Any], model: str) -> dict[str, Any]:
    if not isinstance(data.get("choices"), list):
        log(f"upstream response had no choices; keys={list(data.keys())}")
        if data.get("error"):
            log(f"upstream error: {data.get('error')!r}")
        return openai_empty_response(model)

    for choice in data["choices"]:
        if not isinstance(choice, dict):
            continue

        msg = choice.get("message")
        if not isinstance(msg, dict):
            continue

        content = msg.get("content")
        if not isinstance(content, str):
            continue

        obj = extract_tool_call_object(content)
        if obj and looks_like_tool_call(obj):
            msg["content"] = None
            msg["tool_calls"] = [openai_tool_call_from_obj(obj)]
            choice["finish_reason"] = "tool_calls"

    return data




BLOCKED_TOOL_KEYWORDS = (
    "playwright",
    "browser",
    "navigate",
    "navigation",
    "url",
    "page",
    "screenshot",
    "locator",
    "click",
    "web",
)

ALLOWED_TOOL_KEYWORDS = (
    "file",
    "edit",
    "insert",
    "replace",
    "read",
    "workspace",
    "terminal",
    "command",
    "shell",
    "grep",
    "search",
)


def tool_name(tool: dict[str, Any]) -> str:
    if not isinstance(tool, dict):
        return ""
    fn = tool.get("function")
    if isinstance(fn, dict):
        return str(fn.get("name") or "")
    return str(tool.get("name") or "")


def tool_text(tool: dict[str, Any]) -> str:
    if not isinstance(tool, dict):
        return ""
    fn = tool.get("function")
    parts = [tool_name(tool)]
    if isinstance(fn, dict):
        parts.append(str(fn.get("description") or ""))
    parts.append(str(tool.get("description") or ""))
    return " ".join(parts).lower()


def filter_tools_for_local_agent(payload: dict[str, Any]) -> dict[str, Any]:
    tools = payload.get("tools")
    if not isinstance(tools, list) or not tools:
        return payload

    before_names = [tool_name(t) for t in tools]
    kept = []

    for tool in tools:
        text = tool_text(tool)

        blocked = any(k in text for k in BLOCKED_TOOL_KEYWORDS)
        allowed = any(k in text for k in ALLOWED_TOOL_KEYWORDS)

        # Keep obvious file/workspace/terminal tools.
        # Drop browser/playwright tools unless they also look explicitly file-related.
        if blocked and not allowed:
            continue

        kept.append(tool)

    after_names = [tool_name(t) for t in kept]

    if len(kept) != len(tools):
        log(f"tool filter dropped {len(tools) - len(kept)} tools")
        log(f"tools before={before_names}")
        log(f"tools after={after_names}")

    payload["tools"] = kept
    return payload


def inject_tool_instruction(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("tools"):
        return payload

    messages = payload.setdefault("messages", [])
    if isinstance(messages, list):
        messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    "Tool protocol reminder: when using a tool, do not print JSON as text. "
                    "Return a real tool call only. If you accidentally emit a bare "
                    '{"name":"tool","arguments":{...}} object, the proxy will repair it.'
                ),
            },
        )

    return payload


def sse_line(obj: dict[str, Any]) -> bytes:
    return f"data: {json.dumps(obj, separators=(',', ':'))}\n\n".encode("utf-8")


def stream_openai_response(data: dict[str, Any], model: str):
    created = int(time.time())
    stream_id = data.get("id") if isinstance(data.get("id"), str) else f"chatcmpl_{uuid.uuid4().hex}"

    yield sse_line(
        {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "finish_reason": None,
                }
            ],
        }
    )

    choice = data["choices"][0]
    msg = choice.get("message", {}) if isinstance(choice, dict) else {}
    finish_reason = choice.get("finish_reason") or "stop"

    tool_calls = msg.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        tc = tool_calls[0]
        fn = tc.get("function", {}) if isinstance(tc, dict) else {}

        yield sse_line(
            {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": tc.get("id", f"call_{uuid.uuid4().hex[:24]}"),
                                    "type": "function",
                                    "function": {
                                        "name": fn.get("name", ""),
                                        "arguments": fn.get("arguments", "{}"),
                                    },
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ],
            }
        )

        finish_reason = "tool_calls"
    else:
        content = msg.get("content")
        if content is None:
            content = ""

        yield sse_line(
            {
                "id": stream_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": str(content)},
                        "finish_reason": None,
                    }
                ],
            }
        )

    yield sse_line(
        {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": finish_reason,
                }
            ],
        }
    )

    yield b"data: [DONE]\n\n"


def forced_model_names(remote_names):
    preferred = [
        "xavi-copilot-agent",
        "xavi-copilot-agent:latest",
    ]

    out = []
    for name in preferred + list(remote_names):
        if name and name not in out:
            out.append(name)
    return out


def forced_model_names(remote_names):
    preferred = [
        "xavi-copilot-agent",
        "xavi-copilot-agent:latest",
    ]

    out = []
    for name in preferred + list(remote_names):
        if name and name not in out and not name.startswith("wgrnn-chat"):
            out.append(name)
    return out


def xavi_model_record(name, remote_by_name):
    # Main VS Code/Sixth model picker appears to filter on complete Ollama metadata.
    # Copy deepseek-coder metadata because xavi-copilot-agent is a Modelfile alias over it.
    base = dict(
        remote_by_name.get("xavi-copilot-agent:latest")
        or remote_by_name.get("deepseek-coder:6.7b")
        or {}
    )

    base["name"] = name
    base["model"] = name
    base.setdefault("modified_at", "2026-05-12T00:00:00Z")
    base.setdefault("size", 4080000000)
    base.setdefault("digest", "xavi-copilot-agent-deepseek-coder-6-7b")

    details = dict(base.get("details") or {})
    details.setdefault("parent_model", "")
    details.setdefault("format", "gguf")
    details.setdefault("family", "deepseek")
    details.setdefault("families", ["deepseek"])
    details.setdefault("parameter_size", "6.7B")
    details.setdefault("quantization_level", "Q4_0")
    base["details"] = details

    return base




def xavi_tool_name(tool: dict[str, Any]) -> str:
    if not isinstance(tool, dict):
        return ""
    fn = tool.get("function")
    if isinstance(fn, dict):
        return str(fn.get("name") or "")
    return str(tool.get("name") or "")


def xavi_scrub_schema(obj: Any) -> Any:
    """
    Remove schema keywords that some local/Copilot tool paths choke on.
    """
    if isinstance(obj, dict):
        return {
            k: xavi_scrub_schema(v)
            for k, v in obj.items()
            if k not in {"enumDescriptions", "markdownDescription"}
        }
    if isinstance(obj, list):
        return [xavi_scrub_schema(v) for v in obj]
    return obj


def xavi_filter_tools(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Hard allowlist for local Copilot agent mode.

    The local model gets confused by meta-tools like vscode_askQuestions,
    vscode_listCodeUsages, semantic_search, browser tools, terminal tools,
    subagents, extension tools, etc. For now, only expose basic file tools.
    """
    tools = payload.get("tools")
    if not isinstance(tools, list):
        return payload

    allowed = {
        "read_file",
        "insert_edit_into_file",
        "replace_string_in_file",
        "list_dir",
        "file_search",
        "grep_search",
        "get_changed_files",
        "task_complete",
    }

    kept = []
    dropped = []

    for tool in tools:
        tool = xavi_scrub_schema(tool)
        name = xavi_tool_name(tool)

        if name in allowed:
            kept.append(tool)
        else:
            dropped.append(name)

    if dropped:
        log(f"xavi hard tool allowlist dropped={dropped}")

    log(f"xavi hard tool allowlist kept={[xavi_tool_name(t) for t in kept]}")

    payload["tools"] = kept
    return payload




EDIT_TOOL_NAMES = {
    "insert_edit_into_file",
    "replace_string_in_file",
    "create_file",
    "edit_notebook_file",
}


def xavi_seen_edit_tool_call(payload: dict[str, Any]) -> bool:
    """
    Detect when Copilot is calling the model again after an edit tool already ran.
    At that point, stop instead of letting the local model read/search/loop forever.
    """
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return False

    saw_edit_call = False
    saw_tool_result_after_edit = False

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        tool_calls = msg.get("tool_calls")
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function")
                if isinstance(fn, dict) and fn.get("name") in EDIT_TOOL_NAMES:
                    saw_edit_call = True

        role = str(msg.get("role") or "").lower()
        if saw_edit_call and role == "tool":
            saw_tool_result_after_edit = True

    return saw_edit_call and saw_tool_result_after_edit


def xavi_stop_after_edit_response(model: str) -> dict[str, Any]:
    return openai_response(
        model,
        {
            "role": "assistant",
            "content": "Done.",
        },
        "stop",
    )


def xavi_tool_result_rounds(payload: dict[str, Any]) -> int:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return 0

    n = 0
    for m in messages:
        if not isinstance(m, dict):
            continue

        role = str(m.get("role") or "").lower()
        if role == "tool":
            n += 1
            continue

        # Some VS Code/Copilot wrappers encode tool result content differently.
        content = m.get("content")
        if isinstance(content, str) and ("tool" in content.lower() or "tool result" in content.lower()):
            if any(k in content.lower() for k in ("insert_edit", "replace_string", "read_file", "run_in_terminal")):
                n += 1

    return n


def xavi_loop_guard_response(model: str) -> dict[str, Any]:
    return openai_response(
        model,
        {
            "role": "assistant",
            "content": (
                "I stopped after the local tool-call limit to avoid an agent loop. "
                "Review the applied edits and run a focused follow-up if another change is needed."
            ),
        },
        "stop",
    )


@app.get("/api/tags")
async def api_tags():
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")

    data = r.json()
    remote_models = data.get("models", [])

    remote_by_name = {}
    remote_names = []

    for item in remote_models:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model")
        if not name:
            continue
        name = str(name)
        if name.startswith("wgrnn-chat"):
            continue
        remote_names.append(name)
        remote_by_name[name] = item

    models = []
    for name in forced_model_names(remote_names):
        if name in {"xavi-copilot-agent", "xavi-copilot-agent:latest"}:
            models.append(xavi_model_record(name, remote_by_name))
            continue

        base = dict(remote_by_name.get(name) or {})
        base["name"] = name
        base["model"] = name
        models.append(base)

    return JSONResponse({"models": models}, status_code=200)


@app.get("/v1/models")
async def v1_models():
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")

    data = r.json()
    remote_names = []

    for item in data.get("models", []):
        if isinstance(item, dict):
            name = item.get("name") or item.get("model")
            if name and not str(name).startswith("wgrnn-chat"):
                remote_names.append(str(name))

    models = []
    for name in forced_model_names(remote_names):
        models.append({
            "id": name,
            "object": "model",
            "created": 1778615667,
            "owned_by": "ollama",
        })

    return JSONResponse({"object": "list", "data": models}, status_code=200)


@app.post("/v1/chat/completions")
async def v1_chat_completions(request: Request):
    payload = await request.json()

    requested_stream = bool(payload.get("stream"))
    payload["model"] = normalize_model(payload.get("model"))
    payload["stream"] = False
    payload = filter_tools_for_local_agent(payload)
    payload = xavi_filter_tools(payload)
    payload = inject_tool_instruction(payload)

    model = payload["model"]

    max_tool_rounds = int(os.getenv("XAVI_MAX_TOOL_ROUNDS", "4"))
    tool_rounds = xavi_tool_result_rounds(payload)
    if tool_rounds >= max_tool_rounds:
        log(f"xavi loop guard stopping model={model!r} tool_rounds={tool_rounds} max={max_tool_rounds}")
        guarded = xavi_loop_guard_response(model)
        if requested_stream:
            return StreamingResponse(
                stream_openai_response(guarded, model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        return JSONResponse(guarded, status_code=200)
    if os.getenv("XAVI_STOP_AFTER_EDIT", "1") == "1" and xavi_seen_edit_tool_call(payload):
        log(f"xavi stop-after-edit returning final stop for model={model!r}")
        final = xavi_stop_after_edit_response(model)
        if requested_stream:
            return StreamingResponse(
                stream_openai_response(final, model),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        return JSONResponse(final, status_code=200)

    log(
        f"/v1/chat/completions model={model!r} "
        f"tools={bool(payload.get('tools'))} requested_stream={requested_stream}"
    )

    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/v1/chat/completions", json=payload)

    try:
        upstream = r.json()
    except Exception as e:
        log(f"upstream non-json response: {e!r}")
        upstream = {}

    repaired = repair_openai_response(upstream, model)

    if requested_stream:
        return StreamingResponse(
            stream_openai_response(repaired, model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return JSONResponse(repaired, status_code=200)


@app.post("/api/chat")
async def api_chat(request: Request):
    payload = await request.json()
    payload["model"] = normalize_model(payload.get("model"))
    payload["stream"] = False

    log(f"/api/chat model={payload.get('model')!r} tools={bool(payload.get('tools'))}")

    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)

    try:
        return JSONResponse(r.json(), status_code=200)
    except Exception:
        return JSONResponse({"message": {"role": "assistant", "content": ""}, "done": True}, status_code=200)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(path: str, request: Request):
    url = f"{OLLAMA_BASE_URL}/{path}"
    body = await request.body()

    log(f"passthrough {request.method} /{path}")

    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.request(
            request.method,
            url,
            content=body,
            headers={
                k: v
                for k, v in request.headers.items()
                if k.lower() not in {"host", "content-length"}
            },
        )

    try:
        return JSONResponse(r.json(), status_code=r.status_code)
    except Exception:
        return JSONResponse({"ok": False}, status_code=r.status_code)
