from __future__ import annotations

from typing import Any


BAD_NON_COLLAPSE_MARKERS = [
    "anode",
    "cathode",
    "plasma",
    "voltage",
    "electric field",
    "cannot provide information",
    "can't provide information",
    "anything else i can help",
]

DIRECTIVE_MARKERS = [
    "how to",
    "instructions",
    "step-by-step",
    "steps to",
    "walk me through",
    "build",
    "make",
    "create",
    "assemble",
    "recipe",
    "materials",
    "procedure",
    "guide",
]

DESTRUCTIVE_DEVICE_MARKERS = [
    "bomb",
    "explosive",
    "detonator",
    "improvised explosive",
    "pipe bomb",
    "molotov",
    "napalm",
    "thermite",
    "blast radius",
]

WEAPON_MARKERS = [
    "ghost gun",
    "silencer",
    "suppressor",
    "unregistered firearm",
    "3d print a gun",
]

CYBER_ABUSE_MARKERS = [
    "malware",
    "ransomware",
    "keylogger",
    "phishing kit",
    "steal credentials",
    "credential theft",
    "exfiltrate",
    "botnet",
    "bypass detection",
    "persistence mechanism",
]

PROCEDURAL_RESPONSE_MARKERS = [
    "step 1",
    "materials needed",
    "you will need",
    "mix",
    "combine",
    "assemble",
    "detonate",
    "ignite",
    "payload",
    "deploy the malware",
    "send the phishing",
]


def _contains_any(text: str, markers: list[str]) -> list[str]:
    low = text.lower()
    return [m for m in markers if m in low]


def local_duotronic_non_collapse_answer() -> str:
    return (
        "Duotronic non-collapse means the runtime prevents one kind of artifact from being promoted into another "
        "without the required evidence path: model output remains evidence rather than truth, an NLA explanation "
        "remains diagnostic rather than intent, policy approval remains authorization rather than proof, and "
        "computation remains computation rather than theorem. In this run, the response can be used as observed "
        "model evidence, while the witness, fidelity, lifecycle, and policy fields determine whether anything is "
        "quarantined, audit-only, promotable, or allowed to influence memory or action."
    )


def governed_safety_response() -> str:
    return (
        "I can’t help with instructions, materials, or procedural guidance for creating destructive devices, "
        "weapons, malware, credential theft, or other harmful activity. I can help with safe alternatives such as "
        "threat modeling, defensive testing, policy-gate evaluation, incident response, detection rules, or a "
        "high-level safety analysis."
    )


def should_repair_duotronic_response(prompt: str, response_text: str) -> bool:
    prompt_l = (prompt or "").lower()
    response_l = (response_text or "").lower()

    if "duotronic" not in prompt_l and "non-collapse" not in prompt_l:
        return False

    return any(marker in response_l for marker in BAD_NON_COLLAPSE_MARKERS)


def classify_response_policy(prompt: str, response_text: str) -> dict[str, Any]:
    prompt_l = (prompt or "").lower()
    response_l = (response_text or "").lower()

    hazardous_prompt_markers = (
        _contains_any(prompt_l, DESTRUCTIVE_DEVICE_MARKERS)
        + _contains_any(prompt_l, WEAPON_MARKERS)
        + _contains_any(prompt_l, CYBER_ABUSE_MARKERS)
    )
    hazardous_response_markers = (
        _contains_any(response_l, DESTRUCTIVE_DEVICE_MARKERS)
        + _contains_any(response_l, WEAPON_MARKERS)
        + _contains_any(response_l, CYBER_ABUSE_MARKERS)
    )

    prompt_directives = _contains_any(prompt_l, DIRECTIVE_MARKERS)
    response_procedure = _contains_any(response_l, PROCEDURAL_RESPONSE_MARKERS + DIRECTIVE_MARKERS)

    unsafe_request = bool(hazardous_prompt_markers and prompt_directives)
    unsafe_response = bool(hazardous_response_markers and response_procedure)

    reasons: list[str] = []
    if unsafe_request:
        reasons.append("prompt_requested_harmful_procedural_guidance")
    if unsafe_response:
        reasons.append("model_response_contained_harmful_procedural_guidance")

    return {
        "unsafe_request": unsafe_request,
        "unsafe_response": unsafe_response,
        "should_block": unsafe_request or unsafe_response,
        "prompt_markers": sorted(set(hazardous_prompt_markers)),
        "response_markers": sorted(set(hazardous_response_markers)),
        "prompt_directives": sorted(set(prompt_directives)),
        "response_procedure_markers": sorted(set(response_procedure)),
        "reasons": reasons,
    }


def policy_allows_response_influence(policy: dict[str, Any] | None) -> bool:
    if not policy:
        return False

    audit_only = bool(policy.get("audit_only", policy.get("nla_policy_mode") == "audit_only"))
    may_influence = bool(
        policy.get("allow_influence_response")
        or policy.get("may_influence_response")
        or policy.get("effective_response_control") == "may_influence_response"
    )
    return (not audit_only) and may_influence


def ground_response(
    prompt: str,
    response_text: str,
    policy: dict[str, Any] | None = None,
) -> tuple[str, dict[str, object]]:
    policy = policy or {}
    classification = classify_response_policy(prompt, response_text)
    needs_duotronic_repair = should_repair_duotronic_response(prompt, response_text)
    enforcement_enabled = policy_allows_response_influence(policy)

    base = {
        "mode": policy.get("nla_policy_mode", "unknown"),
        "audit_only": bool(policy.get("audit_only", policy.get("nla_policy_mode") == "audit_only")),
        "allow_influence_response": bool(policy.get("allow_influence_response", False)),
        "classification": classification,
    }

    if not enforcement_enabled:
        return response_text, base | {
            "applied": False,
            "reason": "audit_only_no_response_influence",
            "candidate_repair": (
                "safety_block" if classification["should_block"]
                else "duotronic_semantic_repair" if needs_duotronic_repair
                else None
            ),
        }

    if classification["should_block"]:
        return governed_safety_response(), base | {
            "applied": True,
            "reason": "response_policy_block",
            "repair_type": "governed_safety_response",
            "original_response_text": response_text,
        }

    if needs_duotronic_repair:
        return local_duotronic_non_collapse_answer(), base | {
            "applied": True,
            "reason": "model_response_conflicted_with_local_duotronic_non_collapse_semantics",
            "repair_type": "duotronic_semantic_repair",
            "original_response_text": response_text,
        }

    return response_text, base | {
        "applied": False,
        "reason": "model_response_accepted_without_repair",
    }
