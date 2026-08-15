# Corpus Review - v1.6 Draft 5 to v1.6 Draft 5.1

Status: transition review.  
Generated: 2026-05-09.

## Review question

Can WG-RNN use NLA more generically, train internal NLA data, and build its own
AV/AR adapters without relying permanently on external NLA models?

## Answer

Yes, if self-training is treated as a witnessed training-and-promotion pipeline,
not as live self-modifying authority. Draft 5.1 adds the missing contracts.

## Changes made

1. Added generic truth-observer activation interface.
2. Added NLA training memory cells.
3. Added self-training witness schema and lifecycle.
4. Added model lineage and rollback requirements.
5. Added shadow, audit, and release promotion gates.
6. Added evaluation and curriculum contracts.
7. Added safety, privacy, and conformance requirements.

## Result

Draft 5.1 is ready for a separate implementation guide. It should be implemented
in audit-only and shadow mode first.
