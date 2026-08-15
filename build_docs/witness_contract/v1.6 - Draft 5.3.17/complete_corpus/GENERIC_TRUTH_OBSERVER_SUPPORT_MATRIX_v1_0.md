# Generic Truth Observer Support Matrix v1.0

Status: active Draft 5.1 support matrix.

| Backend type | Hidden states | Logits | Output text | NLA mode |
|---|---:|---:|---:|---|
| transformers local | yes | yes | yes | full activation NLA possible |
| sglang/vllm with embeds/hidden-state support | partial | yes | yes | activation NLA if enabled by backend |
| llama.cpp / llama-server chat only | no by default | limited | yes | output/logit witness fallback |
| ollama chat only | no by default | limited | yes | output/logit witness fallback |
| hosted API | no by default | maybe | yes | output witness only |
| custom truth observer | declared by profile | declared by profile | declared by profile | profile-gated |

A truth observer may not claim activation-language evidence unless the profile
proves activation capture support for the relevant layer, token selection, and
activation space.
