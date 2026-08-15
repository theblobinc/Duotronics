# Evidence Language Acceptance Matrix v1.0

**Draft:** v1.6 Draft 5.2

| Area | Acceptance requirement | Failure mode |
|---|---|---|
| Syntax | compound claims require composition policy | reject without witness |
| Syntax | inference creates InferenceWitness | reject silent inference |
| Pragmatics | force indicator explicit | reject deep-time/authority claim |
| Pragmatics | delegation scoped and time-bounded | reject excess scope |
| Replay | deep-time package includes assumption manifest | reject deep-time marker |
| Replay | verification grammar deterministic | reject nondeterministic grammar |
| Non-collapse | computation cannot become theorem | hard fail |
| Non-collapse | self-trained cannot become authoritative | hard fail |
| NLA | accepted activation witness remains audit-bound until gates | hard fail on auto-promotion |
| Math | proof witness required for theorem | hard fail |
