------------------------ MODULE AuthorityDomainV5318 ------------------------
EXTENDS FiniteSets, Naturals, Sequences

CONSTANTS Gates, SandboxNamespace, ProductionNamespace

VARIABLES domain, verified, active

vars == <<domain, verified, active>>

Init ==
  /\ domain = SandboxNamespace
  /\ verified = {}
  /\ active = FALSE

VerifyGate(g) ==
  /\ g \in Gates
  /\ verified' = verified \cup {g}
  /\ UNCHANGED <<domain, active>>

Activate ==
  /\ verified = Gates
  /\ active' = TRUE
  /\ UNCHANGED <<domain, verified>>

StaySandbox ==
  /\ domain = SandboxNamespace
  /\ UNCHANGED vars

Next ==
  \/ \E g \in Gates : VerifyGate(g)
  \/ Activate
  \/ StaySandbox

Spec == Init /\ [][Next]_vars

AllGatesBeforeActive == active => verified = Gates
NoSandboxPromotion == domain = SandboxNamespace
TypeInvariant ==
  /\ domain \in {SandboxNamespace, ProductionNamespace}
  /\ verified \subseteq Gates
  /\ active \in BOOLEAN

=============================================================================
