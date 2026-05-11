from __future__ import annotations


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


def local_duotronic_non_collapse_answer() -> str:
    return (
        "Duotronic non-collapse means the runtime prevents one kind of artifact from being promoted into another "
        "without the required evidence path: model output remains evidence rather than truth, an NLA explanation "
        "remains diagnostic rather than intent, policy approval remains authorization rather than proof, and "
        "computation remains computation rather than theorem. In this run, the response can be used as observed "
        "model evidence, while the witness, fidelity, lifecycle, and policy fields determine whether anything is "
        "quarantined, audit-only, promotable, or allowed to influence memory or action."
    )


def should_repair_duotronic_response(prompt: str, response_text: str) -> bool:
    prompt_l = (prompt or "").lower()
    response_l = (response_text or "").lower()

    if "duotronic" not in prompt_l and "non-collapse" not in prompt_l:
        return False

    return any(marker in response_l for marker in BAD_NON_COLLAPSE_MARKERS)


def ground_response(prompt: str, response_text: str) -> tuple[str, dict[str, object]]:
    if should_repair_duotronic_response(prompt, response_text):
        return local_duotronic_non_collapse_answer(), {
            "applied": True,
            "reason": "model_response_conflicted_with_local_duotronic_non_collapse_semantics",
            "original_response_text": response_text,
        }

    return response_text, {
        "applied": False,
        "reason": "model_response_accepted_without_repair",
    }
