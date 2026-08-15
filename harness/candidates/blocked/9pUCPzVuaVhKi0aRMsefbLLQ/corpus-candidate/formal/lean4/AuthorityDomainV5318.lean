namespace Duotronic.AuthorityDomainV5318

inductive AuthorityProfile
  | sandbox
  | production
  deriving DecidableEq

structure EvidenceDomain where
  profile : AuthorityProfile
  productionEligible : Bool
  namespaceTag : Nat
  registryTag : Nat
  deriving DecidableEq

def validDomain (d : EvidenceDomain) : Prop :=
  match d.profile with
  | .sandbox => d.productionEligible = false
  | .production => d.productionEligible = true

def mayLink (left right : EvidenceDomain) : Prop := left = right

theorem sandbox_never_production_eligible
    (d : EvidenceDomain)
    (hProfile : d.profile = .sandbox)
    (hValid : validDomain d) :
    d.productionEligible = false := by
  simp [validDomain, hProfile] at hValid
  exact hValid

theorem link_preserves_profile
    (left right : EvidenceDomain)
    (hLink : mayLink left right) :
    left.profile = right.profile := by
  simpa [mayLink] using congrArg EvidenceDomain.profile hLink

structure MeasurementPair where
  originalId : Nat
  revalidationId : Nat
  originalExactResult : Nat
  freshExactResult : Nat
  originalStableProjection : Nat
  freshStableProjection : Nat

def volatilePairValid (p : MeasurementPair) : Prop :=
  p.originalStableProjection = p.freshStableProjection

theorem volatile_exact_results_need_not_collapse
    (p : MeasurementPair)
    (hValid : volatilePairValid p) :
    p.originalStableProjection = p.freshStableProjection := hValid

end Duotronic.AuthorityDomainV5318
