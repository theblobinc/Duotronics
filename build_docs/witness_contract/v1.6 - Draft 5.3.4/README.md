# Duotronic Witness Contract v1.6 — Draft 5.3.3

**Status:** complete active living corrective draft; permanently not frozen.  
**Canonical descriptor:** `CANONICAL_CORPUS_v1_6_draft_5_3_3.json`  
**Primary contract:** `duotronic_witness_contract_v1_6_draft_5_3_3.md`

Draft 5.3.3 corrects the remaining proof-execution trust boundary: compiler
profiles are governance-signed, accepted sources are immutably snapshotted and
built clean, Lake and actual Lean are separately bound, the full dependency and
image closure is recorded, structured Lean results replace stdout parsing, and
key lifecycle/supersession records require signed governance authorization.

Start with `START_HERE.md`, then run:

```bash
python3 executable/validators/validate_draft5_3_3_corpus.py
```

Portable validation proves corpus closure, not real Lean execution or external
trust. Theorem authority is disabled unless a deployment supplies the protected
configuration and passes its real-image/strict activation evidence. The contract
remains permanently unfrozen.
