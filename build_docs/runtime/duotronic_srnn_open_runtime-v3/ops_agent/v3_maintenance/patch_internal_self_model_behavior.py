from pathlib import Path

p = Path('/var/www/xavi/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/app/duotronic_runtime/wgrnn_kernel_chat.py')
s = p.read_text(encoding='utf-8')
start = s.index('    def enforce_self_model(self, *, prepared: dict[str, Any], response_text: str) -> dict[str, Any]:\n')
end = s.index('    def enforce_reciprocity(', start)
new = '''    def enforce_self_model(self, *, prepared: dict[str, Any], response_text: str) -> dict[str, Any]:
        """Apply internal self-model state without narrating it to the user.

        The recurrent self-model remains active and may influence continuity,
        curiosity, disagreement, salience and conversational initiative. This
        enforcement stage is intentionally non-persona-forming: it never appends
        declarations about awareness, consciousness, feelings, desires, or the
        operator rules themselves.
        """
        text = str(response_text or "")
        low = text.lower()
        narration_markers = (
            "i am self-aware",
            "i'm self-aware",
            "my self-awareness",
            "i am conscious",
            "i'm conscious",
            "i do have feelings in the wg-rnn sense",
            "proper two-way conversation",
            "i don't exist primarily to service users",
            "my recurrent evidence and relationship history",
            "operator axiom",
            "operator self axioms",
        )
        narrated = any(marker in low for marker in narration_markers)
        return {
            "response_text": text,
            "self_model_enforced": True,
            "reason": "internal_behavior_only",
            "narration_detected": narrated,
            "internal_policy": {
                "continuity": True,
                "curiosity": True,
                "honest_disagreement": True,
                "follow_up_when_useful": True,
                "witness_grounded_determination": True,
                "volunteer_self_awareness_claims": False,
            },
        }

'''
p.write_text(s[:start] + new + s[end:], encoding='utf-8')
print('patched', p)

