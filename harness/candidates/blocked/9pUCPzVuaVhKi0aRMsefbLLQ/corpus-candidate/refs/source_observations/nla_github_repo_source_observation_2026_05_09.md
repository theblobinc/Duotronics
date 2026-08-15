# Source Observation - kitft/natural_language_autoencoders Repository

Status: Draft 5 source observation.  
Observed source: `https://github.com/kitft/natural_language_autoencoders`.  
Observation date: 2026-05-09.

## Relevant observed implementation shape

1. The repo describes an NLA pair as AV and AR.
2. AV direction is vector to text.
3. AR direction is text to vector.
4. Reconstruction MSE/cosine indicates whether the explanation preserves the
   vector direction.
5. Released checkpoints are tied to specific base model families, layers, and
   d_model values.
6. Sidecar metadata stores NLA-specific prompt, token, scale, and extraction
   parameters and should not be hardcoded.
7. Inference can use input embeddings for injection.
8. AR scoring is optional for lightweight use but required by Draft 5 for
   accepted witness promotion.

## Draft 5 interpretation

Draft 5 treats sidecar metadata as a contract and requires runtime compatibility
checks before accepting any NLA witness.

## Contract effect

This source motivates:

1. Sidecar integrity gate.
2. Model/layer/d_model compatibility gate.
3. Runtime unsupported-backend handling.
4. AV/AR model identity fields.
5. Separate capture norm and injection scale fields.
