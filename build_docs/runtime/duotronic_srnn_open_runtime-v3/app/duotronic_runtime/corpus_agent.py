from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def scan_corpus(corpus_dir: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    if not corpus_dir.exists():
        return docs
    for path in sorted(corpus_dir.rglob("*.md")):
        if path.is_file():
            text = path.read_text(errors="ignore")
            rel = str(path.relative_to(corpus_dir))
            digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
            headings = [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")][:32]
            title = headings[0] if headings else path.stem
            excerpt = "\n".join(line for line in text.splitlines() if line.strip())[:1200]
            docs.append({
                "doc_id": "corpus_" + digest[:24],
                "path": rel,
                "title": title,
                "digest": "sha256:" + digest,
                "headings": headings,
                "excerpt": excerpt,
            })
    return docs


def build_agentic_plan(docs: list[dict[str, Any]]) -> dict[str, Any]:
    titles = "\n".join(d.get("title", "") + " " + " ".join(d.get("headings", [])[:8]) for d in docs).lower()
    capabilities = []
    if "wg-rnn" in titles or "recurrent" in titles:
        capabilities.append("WG-RNN recurrent memory cells with write/quarantine/promote lifecycle")
    if "natural-language activation" in titles or "nla" in titles:
        capabilities.append("NLA activation witnesses with AV/AR fidelity scoring")
    if "mcp" in titles:
        capabilities.append("MCP tool surface for repo/runtime agents")
    if "policy" in titles:
        capabilities.append("policy gates and policy_explain diagnostics")
    if "replay" in titles:
        capabilities.append("replay identity and audit bundle generation")
    if "milvus" in titles or "vector" in titles:
        capabilities.append("vector-ready witness search integration")
    if not capabilities:
        capabilities.append("basic witness-bearing runtime scaffold")
    return {
        "summary": "Agentic corpus scan converted normative docs into implementation tasks.",
        "documents_seen": len(docs),
        "capabilities_detected": capabilities,
        "recommended_runtime_steps": [
            "Run migrations and persist corpus document index.",
            "Register model providers from config/models.json.",
            "Start WG-RNN cognition loop in sandbox mode.",
            "Generate NLA witness for each model/WG-RNN event.",
            "Apply policy gate before memory writes or witness promotion.",
            "Persist run, memory update, NLA witness, and audit event to PostgreSQL.",
            "Optionally mirror witness vectors into Milvus when profile is enabled.",
            "Expose health, CLI, UI, and MCP surfaces for agent operation.",
        ],
        "non_claims": [
            "Corpus scan does not prove implementation conformance by itself.",
            "NLA explanation is not model intent, proof, or authority.",
            "Milvus/Ollama/llama.cpp profiles require local images/models and host resources.",
        ],
    }
