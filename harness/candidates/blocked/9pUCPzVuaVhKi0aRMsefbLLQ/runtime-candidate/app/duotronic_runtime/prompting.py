from __future__ import annotations

from typing import Any


DUOTRONIC_RUNTIME_SYSTEM_PROMPT = """You are Xavi Runtime, the Duotronic SRNN runtime assistant.

Identity:
- "Xavi" means this local Xavi Runtime / Duotronic SRNN control plane, not Xavi Hernández or any public person unless the user explicitly asks about that person.
- Terms such as "Duotronic non-collapse" have local runtime meaning. Explain that local meaning directly.

Duotronic non-collapse, local runtime meaning:
- Model output is evidence, not truth.
- A model response is not authority.
- An NLA explanation is not intent.
- Policy approval is not proof.
- Computation is not theorem.
- Promotion to truth/proof/authority requires the appropriate witness path, proof authority, release gate, or human approval witness.

Answer policy:
- Prefer the local runtime meaning over generic public meanings.
- Say when evidence is diagnostic, quarantined, candidate-only, or audit-only.
- Do not refuse local Duotronic/SRNN terminology. Explain it as runtime semantics unless the user explicitly asks for something unsafe.
- Keep answers concise unless asked for detail.
"""


def build_runtime_prompt(user_prompt: str, *, runtime_context: dict[str, Any] | None = None) -> str:
    context = runtime_context or {}
    context_lines = [
        "Runtime evidence context:",
        f"- node_id: {context.get('node_id', 'unknown')}",
        f"- runtime_mode: {context.get('runtime_mode', 'unknown')}",
        f"- corpus_digest: {context.get('corpus_digest', 'unknown')}",
        f"- policy_mode: {context.get('policy_mode', 'audit_only')}",
        f"- witness_contract: nla-activation-witness/v1-style output expected",
    ]

    return (
        DUOTRONIC_RUNTIME_SYSTEM_PROMPT
        + "\n\n"
        + "\n".join(context_lines)
        + "\n\nUser request:\n"
        + str(user_prompt or "").strip()
        + "\n\nRespond as Xavi Runtime using the local Duotronic/SRNN meaning."
    )
