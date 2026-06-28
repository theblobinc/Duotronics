# The Duotronics Framework: Discrete-State Processing as a Computational Regime in Biological and Artificial Cognition

**Status:** Draft 4.3
**Origin:** Co‑constructed via iterative human–AI dialogue  
**Date:** July 2026

---

## Part I – Why These Four Variables?

The Duotronics Framework proposes that two distinct computational regimes—Continuous‑State Processing Architecture (CSPA) and Discrete‑State Processing Architecture (DSPA)—emerge from the interaction of four measurable dimensions. These dimensions are not arbitrary; each is grounded in an independent, well‑established research programme. This section reviews those programmes and shows why representational entropy, prediction‑error precision, gamma‑band synchrony, and dependence on external invariants are plausible axes of a cognitive parameter space.

### 1.1 Representational Entropy: Efficient Coding and the Free‑Energy Principle

The brain operates under severe metabolic constraints. Efficient coding theory proposes that neural representations are optimised to maximise information transmission while minimising energy expenditure (Barlow, 1961; Attneave, 1954; Shannon, 1948). Predictive processing (PP) extends this logic: the brain is a hierarchical inference engine that continuously generates predictions about sensory input and updates its internal models based on prediction errors (Rao & Ballard, 1999; Friston, 2005, 2010; Clark, 2013, 2016; Hohwy, 2013).

Variational free energy \(F\) decomposes into a complexity cost (the Kullback–Leibler divergence between the approximate posterior \(Q(s)\) and the prior \(P(s)\)) and an accuracy cost (the expected log‑likelihood of observations given hidden states). When the prior is uniform, the complexity cost is directly proportional to the entropy of the posterior. Representational entropy \(H\) thus captures how broadly the system spreads probability mass across competing hypotheses:
\[
H(C) = -\sum_i p_i \log_2 p_i .
\]
Lower \(H\) corresponds to a more determinate, higher‑resolution internal representation; higher \(H\) corresponds to a broader, more approximate representation.

Under tight metabolic budgets, the brain favours high‑entropy, coarse‑grained models that conserve energy (Laughlin, 2001; Sengupta et al., 2013). However, precision—the weight assigned to prediction errors—can shift this trade‑off. High precision forces the posterior to concentrate, driving down entropy. This formal relationship is the subject of Theorem 1 (Section 2.3).

### 1.2 Prediction‑Error Precision: Neuromodulation and Active Inference

Precision \(\Pi\) determines how strongly prediction errors drive belief updating (Feldman & Friston, 2010). It is thought to be encoded neuromodulatorily, particularly via dopaminergic and cholinergic systems (Friston et al., 2012; Schwartenbeck et al., 2019), and is updated on timescales of seconds to minutes (Lawson et al., 2017). Precision is not a passive filter; it plays an active role in selecting actions that minimise expected free energy (Friston et al., 2017). High precision can therefore drive both sharpened internal representations and structured, error‑reducing behaviour.

### 1.3 Gamma‑Band Synchrony: Communication Through Coherence

Gamma oscillations (30–100 Hz) are implicated in feature binding, attentional selection, and conscious perception (Singer, 1999; Fries, 2005, 2015). The communication‑through‑coherence hypothesis proposes that gamma rhythms create temporal windows for feedforward signalling, while alpha/beta rhythms mediate feedback (Fries, 2005, 2015). In the predictive processing framework, gamma synchrony may reflect the propagation of precision‑weighted prediction errors across cortical hierarchies (Bastos et al., 2012, 2015).

Hyperscanning studies have demonstrated that interbrain synchrony in the gamma band is a robust phenomenon during structured social interaction, including cooperative communication, musical performance, and collaborative reasoning (Dumas et al., 2010; Lindenberger et al., 2009; Dikker et al., 2017; Koike et al., 2015).

### 1.4 Aperiodic (1/f) EEG Activity: A Window into Excitation/Inhibition Balance

The power spectrum of neural activity contains a 1/f‑like aperiodic component. The exponent of this slope reflects the balance of cortical excitation and inhibition (Gao et al., 2017; Voytek et al., 2015). Steeper slopes are associated with reduced neural noise and more efficient processing, while flatter slopes are observed in ADHD, aging, and schizophrenia (Waschke et al., 2021; Robertson et al., 2019; Voytek & Knight, 2015). The FOOOF algorithm (Donoghue et al., 2020) allows reliable separation of periodic and aperiodic components, making the exponent a tractable biomarker for cognitive architecture research. As with all EEG measures, multi‑site pre‑registered replication is essential given known variability across pipelines (Hemmerich et al., 2026).

### 1.5 External Invariants: From Extended Mind to Deterministic Anchors

Human cognition has never been confined to the skull. A substantial body of work argues that cognitive processes extend into the environment (Hutchins, 1995; Clark & Chalmers, 1998; Norman, 1993). External representations—mathematical notation, diagrams, written language, and programming environments—function as persistent, structured components of cognitive systems (Kirsh, 2010; Scaife & Rogers, 1996). People routinely offload cognitive work onto external resources, from smartphone reminders to search engines (Risko & Gilbert, 2016; Sparrow et al., 2011). This offloading behaviour varies systematically across individuals and can be measured behaviourally (Gilbert, 2015; Storm & Stone, 2015).

Building on this lineage, we define a **deterministic anchor** as an external data structure that satisfies four properties: metric invariance, sequential rigidity, structural transparency, and phase‑reference capability (formal definition in Section 2.7). Examples include formal verification corpora, Git commit histories, deterministic playlists, and databases with ACID guarantees. Anchor dependence (\(A\)) is the degree to which a cognitive system relies on such invariants for stable operation. This variable has direct precedents in cognitive‑offloading research, where external memory usage, information seeking, and tool dependence are already measured constructs.

### 1.6 Neural Manifolds and the Geometry of the Parameter Space

Recent neuroscience demonstrates that population activity often evolves on low‑dimensional neural manifolds (Cunningham & Yu, 2014; Gallego et al., 2017; Stringer et al., 2019). These latent spaces capture cognitive variables and provide a geometric framework for understanding transitions between computational regimes. Multistability and metastability are well‑documented in perception and motor coordination (Kelso, 1995, 2012; Tognoli & Kelso, 2014), and bifurcations can be triggered by parameter changes such as attention or neuromodulation. Self‑organised criticality and edge‑of‑chaos computation (Beggs & Plenz, 2003; Cocchi et al., 2017) further suggest that the brain’s dynamics naturally inhabit regimes poised between order and flexibility.

We propose that the four variables reviewed above—\(H\), \(\Pi\), \(\gamma\), and \(A\)—constitute a low‑dimensional **control manifold** that shapes the brain’s latent dynamics. Different regions of this manifold correspond to distinct computational regimes. Rather than interpreting CSPA and DSPA as discrete cognitive styles, the framework treats them as attractor basins in a continuous parameter space—an interpretation that aligns naturally with dynamical‑systems and manifold‑based approaches to cognition.

---

## Part II – The Parameter Space and Its Dynamics

### 2.1 Formal Ontology

Before defining the regimes, we establish a minimal formal vocabulary. These definitions are provisional and intended to make the framework precise enough to be operationalised, simulated, or falsified. We separate the concepts of Observation, Claim, Witness, Promotion, and Authority—each a distinct entity in the system's processing pipeline.

**Definition 1 (Cognitive State).** A cognitive state \(C(t)\) is a vector‑valued function in a representational state space \(\mathcal{S}\), representing the system's current internal model, including sensory predictions, belief distributions, and active policies.

**Definition 2 (Representational Entropy).** \(H(C) = -\sum_i p_i \log_2 p_i\), where \(p_i\) are probabilities assigned to competing hypotheses.

**Definition 3 (Prediction‑Error Precision).** \(\Pi(t)\) is the precision (inverse variance) assigned to prediction errors at time \(t\).

**Definition 4 (Gamma Coherence).** \(\gamma\) is the average gamma‑band (30–100 Hz) phase coherence across relevant cortical networks **during active structured reasoning tasks**.

**Definition 5 (Anchor Dependence).** \(A \in [0,1]\) is the degree to which a cognitive system relies on external deterministic anchors for stable operation.

**Definition 6 (Observation).** An observation \(O\) is a discrete sensory or introspective datum registered by the system.

**Definition 7 (Claim).** A claim \(L\) is an assertion derived from observations, provisional until witnessed.

**Definition 8 (Witness).** A witness \(W\) is a typed, verifiable record that a claim, inference, or state transition has been validated.

**Definition 9 (Promotion).** Promotion is the explicit, witnessed process by which a claim gains authority.

**Definition 10 (Authority).** Authority is a property conferred on a claim after successful promotion.

**Definition 11 (Deterministic Anchor).** A deterministic anchor \(\mathcal{A}\) is an external data structure satisfying invariance, sequential rigidity, structural transparency, and phase‑reference capability (see Section 2.7).

**Definition 12 (Synchronisation).** \(S(C_1, C_2)\) is the degree of phase alignment between two cognitive states, operationalised via phase‑locking value (PLV).

### 2.2 Two Processing Regimes: CSPA and DSPA

We model cognition using two idealised processing regimes, understood as **attractor regions** within the continuous four‑dimensional parameter space \(\theta = (H, \Pi, \gamma, A)\). Individuals are not permanently assigned to a regime; their cognitive state moves through this space depending on task demands, developmental history, and environmental context.

Each regime is associated with an objective function derived from the Free‑Energy Principle (Friston, 2010). Variational free energy is:
\[
F = D_{KL}[Q(s) \| P(s)] - \mathbb{E}_{Q}[\log P(o \mid s)].
\]

---

**Continuous‑State Processing Architecture (CSPA):**

\[
\text{CSPA} = (H_{\text{high}},\; \Pi_{\text{moderate}},\; \gamma_{\text{low-to-moderate}},\; A_{\text{low}})
\]

- **\(H\):** High. The system maintains broad probability distributions.
- **\(\Pi\):** Moderate. Prediction errors are integrated and downweighted unless persistent.
- **\(\gamma\):** Low‑to‑moderate. Processing favours slower Alpha/Theta rhythms.
- **\(A\):** Low. Internal stability is maintained primarily through homeostatic mechanisms.

**CSPA Objective:**
\[
\mathcal{O}_{\text{CSPA}} = \min_{C} \big[ \alpha \cdot \text{MetabolicCost}(C) + \beta \cdot \mathbb{E}[E_{\text{pred}}] \big], \quad \alpha \gg \beta.
\]

---

**Discrete‑State Processing Architecture (DSPA):**

\[
\text{DSPA} = (H_{\text{low}},\; \Pi_{\text{high}},\; \gamma_{\text{high}},\; A_{\text{high}})
\]

- **\(H\):** Low. The system commits strongly to a small set of high‑resolution hypotheses.
- **\(\Pi\):** High. Structural prediction errors propagate persistently until resolved.
- **\(\gamma\):** High during structured reasoning tasks.
- **\(A\):** High. Internal stability requires periodic or continuous phase‑locking to deterministic anchors.

**DSPA Objective:**
\[
\mathcal{O}_{\text{DSPA}} = \min_{C} \big[ \lambda \cdot H(C) + \mathbb{E}[E_{\text{pred}}] \big] \quad \text{subject to} \quad A \ge A_{\text{min}}.
\]

The constraint \(A \ge A_{\text{min}}\) arises from the stability analysis in Section 2.6: without sufficient anchor coupling, a high‑precision system becomes dynamically unstable (Proposition 1).

Gamma coherence (\(\gamma\)) and anchor dependence (\(A\)) are **emergent consequences** of the precision–entropy dynamics, not independently tunable variables. Gamma rises because high‑precision inference requires fast, precise inter‑neuronal communication (Bastos et al., 2012; Fries, 2015). Anchor dependence rises because low‑entropy models are brittle and require external stabilisation.

A unified objective function over the full parameter vector \(\theta\) remains a direction for future formal work; the present framework uses separate CSPA and DSPA objectives plus the anchor constraint.

#### 2.2.1 Expanded Derivation of the DSPA Objective

We now provide a more detailed derivation of the DSPA objective function from the variational free energy principle, making explicit the assumptions involved.

Begin with the variational free energy:
\[
F = D_{KL}[Q(s) \| P(s)] - \mathbb{E}_{Q}[\log P(o \mid s)].
\]

The first term, the Kullback–Leibler divergence, measures how far the approximate posterior \(Q(s)\) diverges from the prior \(P(s)\). The second term is the expected log‑likelihood of observations given hidden states, i.e., accuracy. Prediction error \(E_{\text{pred}}\) is the negative log‑likelihood: \(\mathbb{E}[E_{\text{pred}}] = -\mathbb{E}_{Q}[\log P(o \mid s)]\).

We consider three assumptions that characterise the DSPA regime:

**Assumption 1 (High Precision).** The precision \(\Pi\) on prediction errors is high, meaning that the likelihood term is sharply concentrated. Formally, \(P(o \mid s)\) is approximately a delta function around the predicted observation \(g(s)\), so that small mismatches produce large contributions to \(F\).

**Assumption 2 (Deterministic Prior).** The prior \(P(s)\) is concentrated on a low‑entropy manifold of states. This reflects the DSPA system's strong prior belief that the world is structurally determinate. When \(P(s)\) is sharply peaked, the KL divergence \(D_{KL}[Q(s) \| P(s)]\) heavily penalises any \(Q(s)\) that spreads probability mass away from the prior's support. For a uniform prior over a finite support set \(\mathcal{S}_0\) with \(P(s) = 1/|\mathcal{S}_0|\) and zero elsewhere, and assuming \(Q\) has support within \(\mathcal{S}_0\), the KL divergence reduces to \(-\log |\mathcal{S}_0| - H(Q)\), where \(H(Q)\) is the entropy of \(Q\). For a non‑uniform but sharply peaked prior, the KL divergence is approximately \(\lambda \cdot H(Q) + \text{const}\), where \(\lambda\) depends on the prior's concentration.

**Assumption 3 (Metabolic Relaxation).** In DSPA, the metabolic cost weight \(\alpha\) is small relative to the entropy penalty \(\lambda\). The system is willing to expend more energy to achieve low‑entropy, high‑precision representations.

Under these assumptions, the free energy becomes:
\[
F \approx \lambda \cdot H(Q) + \mathbb{E}[E_{\text{pred}}] + \text{const}.
\]

Dropping the constant and identifying \(H(Q)\) with \(H(C)\), we obtain:
\[
\mathcal{O}_{\text{DSPA}} = \min_{C} \big[ \lambda \cdot H(C) + \mathbb{E}[E_{\text{pred}}] \big].
\]

The constraint \(A \ge A_{\text{min}}\) is added because, as shown in Section 2.6, a system with high \(\Pi\) and low \(H\) is dynamically unstable without sufficient anchor coupling. The constraint ensures that optimisation over \(C\) occurs only within the region of state space where stable operation is possible.

### 2.3 Why the Four Parameters Covary: A Causal–Mechanistic Chain

A common criticism of frameworks that propose cognitive "types" is that they bundle together multiple dimensions without explaining why they should co‑occur. We address this by providing a mechanistic chain, grounded in predictive processing, that causally links the proposed DSPA properties.

1. **High precision \(\Pi \uparrow\).** Whether due to innate disposition, developmental conditioning, or sustained task demands, the system assigns high weight to structural mismatches between predicted and observed states. Theorem 1 (below) provides the formal conditions under which this step operates and establishes the link to reduced entropy.

2. **Reduction in representational entropy \(H \downarrow\).** As established by Theorem 1, high precision forces the posterior to concentrate. Hypotheses that generate persistent prediction errors are pruned; probability mass concentrates on a small set of high‑fidelity internal models. The system cannot afford to maintain broad, vague hypotheses because the high precision would amplify every residual error.

3. **Increased reliance on external invariants \(A \uparrow\).** Low‑entropy internal models are brittle: small drifts in the state estimate produce large, sharp error signals because the model's predictions are highly specific. Without a stabilising mechanism, this can lead to runaway error propagation (see Section 2.6). The system therefore phase‑locks to external deterministic anchors—immutable reference structures that reset accumulating drift and provide a fixed point for recursive inference. This is consistent with the extended mind (Clark & Chalmers, 1998; Hutchins, 1995) and cognitive offloading (Risko & Gilbert, 2016) literatures, which document how external structures become constitutive components of cognitive processing.

    We acknowledge an alternative pathway: a low‑entropy system could, in principle, rigidly adhere to its internal model and reject external input entirely, rather than seeking external anchors. In DSPA, however, the specific parameterisation—high precision on prediction errors combined with metabolic relaxation—favours the anchor‑seeking path. Because prediction errors are weighted so heavily, internal drift cannot be ignored or suppressed; it generates an escalating error signal that demands resolution. Anchors provide the necessary external error‑correction reference, whereas rigid adherence without anchors would lead to the instability formalised in Proposition 1. Thus, the DSPA configuration pushes the system toward external invariant dependence rather than solipsistic model rigidity.

4. **Elevated gamma‑band coherence \(\gamma \uparrow\) during structured tasks.** High‑precision inference and rapid state transitions require fast, precise communication between neural populations. Gamma rhythms are well‑suited for propagating prediction errors and binding features across cortical hierarchies (Fries, 2005, 2015; Bastos et al., 2012, 2015). DSPA thus predicts elevated gamma coherence specifically during tasks that demand high‑resolution structural processing, not at rest.

5. **Steeper aperiodic (1/f) slope.** The low‑entropy, high‑precision dynamics correspond to a more tightly regulated excitation/inhibition balance and reduced neural noise. This manifests as a steeper aperiodic exponent in the resting EEG, consistent with the established association between steeper slopes and efficient processing (Waschke et al., 2021; Voytek et al., 2015). The steeper slope is a *consequence* of the underlying dynamics, not an independent trait.

    **Caveat:** Steeper aperiodic slopes are not universally "better." Under certain conditions, excessively steep slopes are associated with pathology—for example, in some epilepsy subtypes and specific autism profiles, steeper slopes may reflect hypersynchronous or rigid neural dynamics rather than adaptive efficiency. DSPA predicts a *task‑dependent* shift toward steeper slopes during structured reasoning, not a permanent or trait‑like steepness. The adaptive value of the shift is context‑dependent: it is beneficial when the environment contains genuine high‑resolution structure, but may be maladaptive when the environment is noisy or when flexibility is required.

6. **Affinity for formal methods and symbolic systems.** Deterministic anchors are naturally provided by formal verification tools, proof assistants, immutable version‑control histories, and other structured symbolic systems. Individuals whose cognitive architecture benefits from such anchors will seek them out, creating a self‑reinforcing feedback loop: the architecture drives tool preference, and tool usage further entrenches the architecture. This explains the observed correlation between formal methods practice and certain cognitive styles without requiring a dedicated "formal methods gene."

**Relationship to High‑Precision Theories of Autism.** The DSPA framework shares features with computational accounts of autism that emphasise high precision‑weighting of prediction errors and attenuated influence of prior beliefs (Pellicano & Burr, 2012; Van de Cruys et al., 2014). Both frameworks predict reduced reliance on broad priors, sharper responses to sensory prediction errors, and a preference for structured, predictable environments. However, Duotronics makes a distinct claim: it does not assert that DSPA *is* autism, or that autistic individuals uniformly exhibit DSPA. Rather, DSPA describes a *computational regime*—a region of parameter space—that may be accessible to different clinical and non‑clinical groups under specific task demands or developmental conditions. Some autistic individuals may operate in this regime more frequently or persistently than neurotypical individuals, consistent with the high‑precision account, but the DSPA construct is agnostic about clinical categorisation. Conversely, not all individuals with DSPA‑like cognitive styles meet criteria for autism. Duotronics is a framework for modelling cognitive architecture, not a diagnostic tool. The overlap with autism theories is an empirical question to be explored through the experimental programme outlined in Part III.

Thus, DSPA is not an arbitrary cluster of independent traits. It is a *coherent dynamical regime* that emerges when a predictive processing system operates at high precision for extended periods, with downstream consequences for entropy, anchor dependence, neural oscillations, and tool preference. The properties covary because they are causally linked through the underlying inference dynamics.

**Developmental Trajectory.** How does a cognitive system settle preferentially into one attractor basin? We hypothesise that early exposure to high‑structure, low‑ambiguity environments—such as chess, music theory, or programming—progressively tilts the parameter vector toward DSPA through Hebbian reinforcement of high‑precision inference. When the environment consistently rewards precise, anchor‑coupled predictions, the anchor dependence parameter \(A\) strengthens; when it rewards flexibility and broad exploration, \(A\) weakens. Longitudinal studies tracking aperiodic slopes and anchor‑dependence behaviours in children beginning formal methods or music training, compared to unstructured creative play, would test this developmental hypothesis. The slow dynamics of \(A\) (Section 2.4.1) provide a formal model for this drift, with \(\eta_A\) on the order of weeks to months, consistent with the timescale of habit formation and skill automatisation.

#### Theorem 1: Precision Reduces Posterior Entropy

A central assumption of the framework is that high precision drives down representational entropy. We now formalise this as a theorem, specifying the conditions under which it holds.

**Theorem 1 (Precision Reduces Posterior Entropy).**  
Consider a predictive processing system with generative model \(P(o, s) = P(o \mid s) P(s)\). Let the likelihood be Gaussian with precision \(\Pi\):
\[
P(o \mid s) = \mathcal{N}(o; g(s), \Pi^{-1}),
\]
where \(g(s)\) is a generative mapping. Let the approximate posterior \(Q(s)\) be chosen to minimise the variational free energy \(F\). Let the prior \(P(s)\) be such that it does not dominate the posterior (i.e., the likelihood is informative). Then, under the Laplace approximation, increasing the precision \(\Pi\) reduces the entropy of the optimal posterior \(Q^*(s)\).

*Proof.* Under the Laplace approximation, the optimal posterior is Gaussian with covariance \(\Sigma = (\Pi \cdot J^\top J + \Sigma_0^{-1})^{-1}\), where \(J = \nabla_s g(s)\) is the Jacobian of the generative mapping evaluated at the posterior mode, and \(\Sigma_0\) is the prior covariance. The differential entropy of a Gaussian with covariance \(\Sigma\) in \(d\) dimensions is
\[
H = \frac{d}{2}(1 + \log 2\pi) + \frac{1}{2} \log \det \Sigma.
\]

As \(\Pi\) increases, \(\Sigma\) decreases (in the sense of Loewner order), and \(\det \Sigma\) decreases. Since \(\log \det\) is monotonic in the determinant, the differential entropy \(H\) decreases monotonically with \(\Pi\). In the limit \(\Pi \to \infty\), the posterior converges weakly to a point mass; for a continuous state space the differential entropy tends to \(-\infty\) (relative to the Lebesgue measure), while for a discretized space the discrete entropy tends to \(0\), representing a fully determinate representation. ∎

**Robustness When Posteriors Are Non‑Gaussian.** The Laplace approximation provides a tractable first‑order analysis, but real posteriors may be multimodal or heavy‑tailed. Biological inference often operates in precisely such regimes—for example, when multiple competing perceptual interpretations are equally plausible (binocular rivalry, ambiguous figures) or when environmental statistics are heavy‑tailed. In these cases, the relationship between precision and entropy becomes more nuanced.

For many unimodal but non‑Gaussian distributions in the exponential family, increasing the precision parameter of the likelihood still concentrates mass around the mode, monotonically reducing entropy, though the rate of reduction may differ from the Gaussian case. However, when the posterior is genuinely multimodal, increasing precision can have a qualitatively different effect: rather than simply collapsing uncertainty, it may sharpen the distinction between modes, potentially leading to **precision‑driven switching** between discrete hypotheses. In this regime, the system does not maintain a broad distribution across possibilities; instead, it jumps rapidly between distinct, high‑resolution models as small changes in evidence or internal state cause one mode to dominate. This switching behaviour is consistent with DSPA's characterisation of discrete‑state processing: the system operates on a small set of well‑defined, sharply distinguished hypotheses, transitioning abruptly between them rather than blending. This extension of Theorem 1 to multimodal posteriors provides a deeper connection to the phenomenology of structured reasoning, where insight and re‑categorisation often occur suddenly rather than through gradual refinement. The multimodal regime is a topic for future formal work, but its qualitative alignment with DSPA predictions is noted here.

**Conditions and Caveats.** The theorem relies on three conditions that define the DSPA‑relevant regime:

1. **Informative likelihood:** The likelihood must be sufficiently precise that it meaningfully constrains the posterior. If \(\Pi\) is very small, the prior dominates, and precision changes have negligible effect on entropy.

2. **Laplace approximation validity:** The posterior must be approximately Gaussian, which holds when the generative model is locally linear around the mode and the data are sufficiently informative. This condition may fail in highly nonlinear regimes or with multimodal posteriors.

3. **Non‑degenerate prior:** The prior covariance \(\Sigma_0\) must be finite. An improper flat prior would make the posterior covariance simply \((\Pi \cdot J^\top J)^{-1}\), which still decreases with \(\Pi\), so the result holds regardless.

**What the theorem does not claim.** The theorem does not assert that *any* increase in precision, in *any* context, reduces entropy. High precision can sometimes increase exploration if the system uses precision to drive information‑seeking behaviour (active inference). It can also increase hierarchical complexity if precision is allocated to higher‑level predictions. The theorem specifies a *ceteris paribus* condition: holding the generative model and prior fixed, increasing precision on sensory prediction errors reduces the entropy of the optimal posterior. This is the regime relevant to DSPA, where precision is persistently high and directed at structural prediction errors.

#### Proposition 1: Anchor Stabilisation

**Proposition 1 (Anchor Stabilisation).**  
Consider the linearised dynamics around a fixed point where prediction errors vanish. Let the Jacobian of the prediction‑error term be \(J = -\Pi \nabla^2 E\). If the anchor gain \(A\) satisfies \(\kappa A > \|J\|\), then the anchor term dominates and the fixed point is asymptotically stable. Conversely, if \(A=0\) and the eigenvalues of \(J\) have positive real parts, the system is unstable. Thus, increasing anchor coupling can stabilise an otherwise unstable high‑precision regime.

*Proof sketch:* The linearised equation is \(\dot{\delta C} = J \delta C + \kappa A (-\delta C) = (J - \kappa A I) \delta C\). The eigenvalues are those of \(J\) shifted left by \(-\kappa A\). Choosing \(A\) sufficiently large ensures all eigenvalues have negative real parts.

This proposition formalises the stabilising role of deterministic anchors: they provide a negative feedback that counteracts the positive feedback generated by high precision in the presence of noise. It is a theorem about the model, not a theorem about brains, and is offered as a mathematically precise statement of the hypothesised relationship between anchor dependence and stability.

### 2.4 Dynamical Model of Anchor‑Coupled Inference with Active Inference

To make the framework more than a static description, we propose a dynamical equation governing the evolution of cognitive state \(C(t) \in \mathcal{S}\) under the influence of prediction errors, precision, anchor coupling, and active inference through action.

Let \(E(t) = \| o(t) - g(C(t)) \|^2\) be the prediction error at time \(t\), where \(g\) is a generative mapping from hidden states to observations. Let \(\Pi(t)\) be the precision assigned to that error. The anchor \(\mathcal{A}\) provides a reference signal \(R_{\mathcal{A}} \in \mathcal{S}\), which lives in the same state space as \(C\), ensuring dimensional consistency. For a static deterministic anchor, \(R_{\mathcal{A}}\) is time‑invariant; for sequentially rigid anchors accessed at discrete indices, \(R_{\mathcal{A}}\) is a predetermined function of the index. In active inference, action \(a\) can also alter observations to match predictions, contributing an additional error‑correction pathway. The rate of change of cognitive state is then:
\[
\frac{dC}{dt} = -\Pi(t) \nabla_C E(t) + \kappa A \, (R_{\mathcal{A}} - C(t)) - \Pi_{\text{active}} \nabla_a \mathbb{E}[E_{\text{expected}}],
\]
where:
- \( \nabla_C E(t) \) is the gradient of prediction error with respect to cognitive state (the direction of steepest error reduction).
- \( \Pi(t) \) multiplies this gradient, determining how aggressively the system updates its model.
- \( \kappa \) is a coupling constant.
- \( A \) is the anchor dependence parameter.
- \( R_{\mathcal{A}} - C(t) \) is the mismatch between the anchor reference and the current state, pulling the system back toward alignment.
- \( \Pi_{\text{active}} \) is the precision assigned to expected prediction errors under candidate actions.
- \( \nabla_a \mathbb{E}[E_{\text{expected}}] \) is the gradient of expected future prediction error with respect to action \(a\), capturing how action selection is biased toward minimising anticipated error.

**Interpretation:**
- The first two terms remain as before: error‑correction and anchor stabilisation.
- The third term, \(-\Pi_{\text{active}} \nabla_a \mathbb{E}[E_{\text{expected}}]\), captures active inference: the system selects actions that are expected to minimise future prediction error. This is the mechanism through which embodied motor anchors (Section 2.9) operate—structured motor routines (pacing, tapping, breath control) are actions that generate predictable sensory feedback, effectively creating a self‑generated deterministic anchor in the proprioceptive domain.
- In **CSPA** (\( \Pi \) moderate, \( A \) low), the system updates slowly, smoothing over transient errors and relying little on external anchors. Action selection is exploratory and guided by broad priors.
- In **DSPA** (\( \Pi \) high, \( A \) high), the system responds sharply to errors, is strongly attracted to the anchor reference, and selects actions that minimise expected error with high precision—favouring structured, repetitive motor patterns that serve as self‑generated anchors. Without an anchor (\( A \to 0 \) but \( \Pi \) remaining high), the error correction term \( -\Pi \nabla_C E \) may drive the system into unstable oscillations. The model therefore predicts that anchor removal in a high‑precision regime can lead to significant instability.

This dynamical equation structurally resembles a Kalman–Bucy filter with an added reference tracking term and an active control term (Kalman, 1960; Åström & Murray, 2008). The prediction‑error gradient term corresponds to the innovation update in Kalman filtering; the anchor term corresponds to a set‑point regulator in control theory; the active inference term corresponds to model‑predictive control. This connection situates the framework within established engineering mathematics and provides a foundation for future simulation studies.

#### 2.4.1 Concrete Parameter Dynamics with Timescale Separation

The parameter vector \(\theta = (H, \Pi, \gamma, A)\) evolves on slower timescales. We now propose a concrete form for the dynamics \(F(\theta, u, t)\) based on gradient descent on the combined objective \(\mathcal{O}(\theta)\) plus a white noise term representing random fluctuations:

\[
\frac{d\Pi}{dt} = -\eta_\Pi \frac{\partial \mathcal{O}}{\partial \Pi} + \sigma_\Pi \xi_\Pi(t),
\]
\[
\frac{dH}{dt} = -\eta_H \frac{\partial \mathcal{O}}{\partial H} + \sigma_H \xi_H(t),
\]
\[
\frac{d\gamma}{dt} = -\eta_\gamma \frac{\partial \mathcal{O}}{\partial \gamma} + \sigma_\gamma \xi_\gamma(t),
\]
\[
\frac{dA}{dt} = -\eta_A \frac{\partial \mathcal{O}}{\partial A} + \sigma_A \xi_A(t),
\]

where \(\eta_*\) are learning rates, \(\sigma_*\) are noise amplitudes, and \(\xi_*(t)\) are independent Gaussian white noise processes.

**Timescale Separation and Plausible Biological Ranges.** We assume \(\eta_\Pi, \eta_\gamma\) are large (fast adaptation on the order of seconds to minutes, consistent with synaptic gain modulation and neuromodulatory dynamics), while \(\eta_A\) is small (slow adaptation on the order of weeks to months, consistent with the timescale of synaptic plasticity underlying habit formation and expertise development; cf. Dayan & Abbott, 2001). The entropy penalty weight \(H\) may adapt at an intermediate timescale (hours to days). The noise amplitudes \(\sigma_*\) are assumed to be small relative to the gradient terms, reflecting the stability of parameter estimates over time, but non‑zero to allow stochastic transitions between attractor basins. Even these rough orders of magnitude strengthen the biological plausibility of the framework and provide testable constraints for longitudinal studies.

**Bistable Landscape.** Under appropriate parameter choices, the deterministic part of these dynamics produces a landscape with two distinct attractor basins corresponding to CSPA and DSPA. For example, if the environment provides a strong deterministic anchor (high \(R_{\mathcal{A}}\) signal) and task demands are high, the system is driven toward the DSPA basin (\(\Pi\) high, \(H\) low, \(A\) high). Conversely, in the absence of anchors and with low task demands, the system relaxes toward the CSPA basin. Noise can occasionally flip the system between basins, accounting for momentary shifts in cognitive style. This bistability is consistent with multistable dynamics observed in perception and motor coordination (Kelso, 2012; Tognoli & Kelso, 2014), and with the concept of self‑organised criticality and edge‑of‑chaos computation in neural systems (Beggs & Plenz, 2003; Cocchi et al., 2017).

**Simulation.** A numerical integration of these equations for a specific choice of parameters can be used to produce phase‑plane plots showing the basins of attraction and trajectories under varying inputs. Such simulations would make the attractor‑basin concept visually compelling and analytically tractable. We outline a simulation scenario in Section 2.8.

---

### 2.5 Formal Definition of Deterministic Anchors

We now formalise Definition 11. Let \(\mathcal{S}\) be the cognitive state space, and let \(d: \mathcal{S} \times \mathcal{S} \to \mathbb{R}_{\ge 0}\) be a metric (e.g., Euclidean distance for continuous states, Hamming distance for discrete symbols). An **anchor** is a pair \((\mathcal{A}, R_{\mathcal{A}})\) where \(\mathcal{A}\) is an external data structure and \(R_{\mathcal{A}} \in \mathcal{S}\) is a reference point in state space. For a sequentially rigid anchor accessed at discrete indices, \(R_{\mathcal{A}}(n)\) is the reference at index \(n\). The anchor is **deterministic** if it satisfies the following conditions:

1. **Metric invariance:** For any two time points \(t_1, t_2\) within the anchor's validity period,
   \[
   d(R_{\mathcal{A}}(t_1), R_{\mathcal{A}}(t_2)) = 0,
   \]
   i.e., the reference does not change. For a static anchor, this holds trivially. For a sequentially rigid anchor, \(R_{\mathcal{A}}(n)\) is invariant under repeated queries at the same index.

2. **Sequential rigidity:** If the anchor is accessed at discrete indices \(n \in \mathbb{N}\), then for any \(n_1 < n_2\), \(R_{\mathcal{A}}(n_1)\) precedes \(R_{\mathcal{A}}(n_2)\) in a fixed, predetermined sequence. The ordering is non‑negotiable and independent of the accessing system's state.

3. **Structural transparency:** The mapping from index or time to reference state is explicitly computable from the anchor's specification. No hidden variables, random seeds, or external state influence the output. Formally, there exists a total computable function \(f_{\mathcal{A}}: \mathbb{N} \to \mathcal{S}\) (or \(f_{\mathcal{A}}: \mathbb{R} \to \mathcal{S}\)) such that \(R_{\mathcal{A}}(n) = f_{\mathcal{A}}(n)\) and the definition of \(f_{\mathcal{A}}\) is fully specified by \(\mathcal{A}\).

4. **Phase‑reference capability:** The anchor can be sampled at a rate \(r_{\mathcal{A}}\) that exceeds the Nyquist rate of the system's fastest relevant cognitive rhythm. That is, \(r_{\mathcal{A}} > 2 \cdot f_{\text{max}}\), where \(f_{\text{max}}\) is the highest frequency component (e.g., high gamma) that the system uses for phase‑locking.

This definition makes deterministic anchors into objects that can be studied mathematically and implemented in software. Examples include:
- A formal verification corpus with explicit, immutable proofs.
- A Git commit DAG with cryptographically hashed history.
- A deterministic playlist with precisely aligned metadata and fixed playback order.
- A deterministic database with ACID guarantees and immutable schema.
- Mathematical notation and structured external representations (Kirsh, 2010; Scaife & Rogers, 1996), which provide immutable symbolic references.
- The Witness Contract, which satisfies all four conditions by construction.

### 2.6 Operationalising Anchor Dependence

To make \(A\) empirically measurable, we propose several candidate operationalisations. No single measure is definitive; triangulation across multiple approaches is recommended.

- **Proportional Consultation:** The proportion of inference steps in a structured task during which the system references an external invariant structure. For example, a system that checks a proof corpus, a version‑control history, or a deterministic playlist on 80% of its inference cycles would have \(A \approx 0.8\) by this measure.
- **Normalised Mutual Information:** \(A_{\text{NMI}} = I(C(t+1); \mathcal{A}(t)) / H(C(t+1))\), where \(I\) is mutual information and \(H\) is entropy. This captures how much the anchor reduces uncertainty about the system's next cognitive state, normalised by the system's own entropy. A value near 1 indicates that the anchor strongly constrains state transitions.
- **Drift Amplification Under Anchor Removal:** The rate at which prediction errors accumulate when the anchor is experimentally removed or scrambled. A system with high \(A\) should exhibit a significantly steeper increase in prediction‑error magnitude during anchor‑removal conditions compared to baseline. This can be measured in artificial systems and, in principle, in human participants via error rates on structured tasks with and without an available anchor.
- **Self‑Report and Behavioural Indices:** In human studies, anchor dependence could be triangulated with self‑report measures of intolerance of ambiguity (Budner, 1962), need for closure (Kruglanski et al., 1993), need for structure (Neuberg & Newsom, 1993), systemising (Baron‑Cohen et al., 2003), cognitive reflection (Frederick, 2005), and behavioural measures such as frequency of consulting external references during problem‑solving tasks (Risko & Gilbert, 2016; Gilbert, 2015).

**Example Paradigm: Hidden‑State Tracking with Anchor Removal.** To provide a concrete experimental design that could be implemented immediately, we describe a behavioural paradigm yielding a direct proxy for \(A\).

Participants monitor a slowly drifting hidden variable—for example, the position of a cursor undergoing a random walk on a screen—via noisy observations (blurred cursor positions). In the *anchor‑present* condition, a perfectly reliable external marker (e.g., a deterministic auditory tick at the true hidden position, provided every few seconds) serves as a deterministic anchor. In the *anchor‑absent* condition, no external reference is given; participants must rely solely on noisy observations. The task is to continuously estimate the hidden position, with estimation error tracked over time.

**DSPA‑specific prediction:** When the anchor is unexpectedly removed, DSPA‑like participants should exhibit a steeper performance drop—reflected in higher error variance and greater over‑correction—compared to CSPA‑like participants. This is because DSPA systems are hypothesised to rely heavily on the anchor for error correction; its removal leaves the high‑precision error‑correction loop without its stabilising reference, producing rapid drift amplification. The difference in error increase between conditions can be quantified as a "drift amplification index," a direct behavioural proxy for \(A\). This measure can be correlated with EEG signatures (e.g., aperiodic slope, gamma coherence) to provide converging evidence for the DSPA construct.

These operationalisations are provisional and would require validation in empirical studies. They are offered as a starting point for making the construct testable.

### 2.7 Deterministic Anchors in Depth and the Witness Contract

Deterministic anchors are external invariants that ground recursive inference by providing fixed reference points. In DSPA, high precision‑weighting means that even small deviations from a stable reference accumulate rapidly into large prediction errors. Phase‑locking to a deterministic anchor provides a continuous calibration signal that resets accumulating drift, preventing the feedback loops that would otherwise destabilise the system.

The deterministic‑anchor concept is independent of any particular neuroscientific claim. It is a systems‑level construct that can be studied in both biological cognition and artificial computational architectures, and it builds directly on decades of research into extended cognition (Hutchins, 1995; Clark & Chalmers, 1998), external representations (Kirsh, 2010; Scaife & Rogers, 1996), cognitive offloading (Risko & Gilbert, 2016), and distributed cognition (Norman, 1993). The concept connects naturally to several existing research domains:

- **Formal verification:** Proof corpora and model‑checking outputs serve as anchors by providing mechanically verified invariants (Gordon, 2000; Nipkow, 2002; Bertot & Castéran, 2004; Harrison, 2009).
- **Distributed systems:** Immutable ledgers and consensus protocols provide deterministic state references.
- **Cognitive aids:** External memory systems, checklists, and structured workflows serve as low‑tech deterministic anchors (Gilbert, 2015; Storm & Stone, 2015).
- **Artistic practice:** Structured musical compositions, choreographed sequences, and formal poetic constraints can serve as anchors for cognitive entrainment.
- **Programming and software engineering:** Integrated development environments, version‑control systems, and formal specifications provide deterministic structures that scaffold reasoning (Storey, 2006; Soloway, 1986; Pennington, 1987). The cognitive‑dimensions framework (Green & Petre, 1996) analyses how such notations shape problem‑solving, offering a vocabulary for understanding how deterministic anchors reduce cognitive load.

#### The Witness Contract as Normative DSPA Substrate

The Witness Contract (v1.6, Draft 5.2.2, stable release tag v1.6) provides a concrete, machine‑verifiable **normative realisation** of deterministic anchors. It is not presented as evidence that biological DSPA exists; rather, it is an **executable implementation** of DSPA's computational principles, demonstrating that the proposed regime can be engineered in software. The Contract operationalises the Observation → Claim → Witness → Promotion → Authority pipeline defined in the ontology (Section 2.1).

**Core Constructs.**
- **Observations and Claims:** Every registered datum enters as an Observation. Claims derived from observations remain provisional until witnessed.
- **Witnesses:** Every state transition, inference, or promotion must emit typed, verifiable *witnesses* (e.g., `EvidenceClaim`, `InferenceWitness`, `ProofWitness`, `LeanCompilerWitness`, `TaskResultWitness`, `KernelErrorWitness`). No claim becomes authoritative without a witness.
- **Promotion Gates:** Claims are promoted to Authority only through explicit, witnessed gates. Theorems require Lean compiler witnesses and theorem promotion gates. Authority delegation is bounded and chained.
- **Logical Observer Kernel:** A fail‑closed machine enforcing deterministic, replayable computation. It includes boot sequences, canonical resolution of rules, capability tokens, resource budgets, and **non‑collapse invariants**: conflicts are represented rather than silently resolved, operationalising DSPA's low tolerance for ambiguity.
- **Replayability and Audit:** All computation is traceable via execution traces, snapshots, and deterministic grammars. No hidden state, network access, randomness, or wall‑clock dependence in verification mode.
- **Formal Layers:** TLA+ state machines for model checking + Lean/Lake for proof verification. Validation pipelines ensure schema compliance, hash closure, and exact witness‑ID membership.

**Illustrative Example: Claim → Witness → Promotion.**
1. **Observation:** "The system state at \(t_1\) satisfies invariant \(I\)."
2. **Claim:** "If invariant \(I\) holds at \(t_1\) and no violating transition occurred, then \(I\) holds at \(t_2\)."
3. **Witness Generation:** A Lean proof checker verifies the step and produces an `InferenceWitness`.
4. **Promotion:** The witness is validated by a gate; the claim becomes `Authority`.
5. **Authoritative State:** The claim is immutably stored and can serve as a premise for further inference.

**Mathematical Alignment with DSPA Parameters.**

| DSPA Parameter | Witness Contract Realisation |
|----------------|------------------------------|
| Low \(H(C)\) (Entropy) | Witnesses enforce categorical state transitions; probability mass concentrates on verified hypotheses |
| High \(\Pi\) (Precision) | Only witnessed errors propagate; unverified claims are not assimilated |
| High \(\gamma\) (Coherence, task‑related) | Formal verification steps provide discrete synchronisation points, analogous to gamma‑band resolution of structural detail |
| High \(A\) (Anchor Dependence) | The kernel + corpus serves as an immutable, formally verified anchor |
| Non‑collapse | Conflicts are represented, not silently resolved, operationalising DSPA's ambiguity intolerance |

**Normative vs. Descriptive Status.**
- **Descriptive claim:** Human cognition may approximate DSPA under certain conditions (testable via EEG, hyperscanning).
- **Normative implementation:** The Witness Contract demonstrates *how a DSPA system ought to operate*, regardless of biological realisation.

This distinction protects the framework from overclaiming. The Witness Contract is evidence that DSPA principles are *engineerable*, not that they are *biologically realised*.

**Simplified "Witness Contract Lite" for Human Experiments — Pilot Study Blueprint.**
For H6, which requires human dyads to interact with a Witness Contract corpus, we propose a simplified interface—"Witness Contract Lite"—that displays a small set of pre‑verified lemmas. Participants commit to inference steps via a "Verify" button; the interface provides immediate feedback on whether a step is witnessed (consistent) or unwitnessed. A sample task involves chaining lemmas about array sorting to prove a target property. Dependent variables include error rate, time per step, number of unwitnessed attempts, and concurrent EEG metrics (aperiodic slope, gamma coherence, inter‑dyad PLV). The control condition is the same problem in a standard text editor without verification.

### 2.8 Simulation and Sensitivity Analysis

**Simulation Demonstration.** To demonstrate that the proposed dynamical regime is mathematically realisable, we outline a simulation study.  
- **State space:** A two‑dimensional cognitive state \(C(t) = (c_1(t), c_2(t))^\top\).  
- **Generative model:** \(g(C) = C\), so that the prediction error is \(E(t) = \|o(t) - C(t)\|^2\) with a fixed observation \(o = (0, 0)^\top\).  
- **Precision:** \(\Pi = 5.0\) (high, representing DSPA) or \(\Pi = 1.0\) (moderate, representing CSPA).  
- **Anchor:** \(R_{\mathcal{A}} = (1, 1)^\top\) (a fixed reference).  
- **Anchor dependence:** \(A = 0.8\) (high) or \(A = 0.1\) (low).  
- **Coupling constant:** \(\kappa = 1.0\).  
- **Initial condition:** \(C(0) = (0.5, 1.5)^\top\).

**Predicted Results:**
1. **CSPA regime (\(\Pi = 1.0, A = 0.1\)):** The system converges slowly to the origin, with smooth, monotonic trajectories. The anchor has negligible influence.
2. **DSPA regime with anchor (\(\Pi = 5.0, A = 0.8\)):** The system converges rapidly to a point near the anchor reference \(R_{\mathcal{A}}\), oscillating briefly before settling. The anchor stabilises what would otherwise be an unstable rapid correction.
3. **DSPA regime without anchor (\(\Pi = 5.0, A = 0.0\)):** The system overshoots the origin, oscillates with increasing amplitude, and diverges. This demonstrates the predicted instability when high precision is not accompanied by anchor coupling.

Additionally, by numerically integrating the parameter dynamics equations under varying environmental inputs \(u\), we will produce phase‑plane plots showing the two attractor basins and the flow of \(\theta\). Starting from an intermediate initial \(\theta\), the system will settle into either the CSPA or DSPA basin depending on whether a deterministic anchor is present and whether task demands are high.

**Sensitivity Analysis Outline.**
- **Parameters Varied:** \(\Pi \in [0.5, 10.0]\), \(A \in [0.0, 1.0]\), \(\kappa \in [0.1, 5.0]\), \(\lambda \in [0.1, 10.0]\).  
- **Outcome Measures:** Stability (convergence vs. divergence), convergence time, oscillation amplitude.  
- **Predicted Phase Transition:** A critical threshold exists in the \((A, \Pi)\) plane: \(A_{\text{crit}} \approx \Pi / c\), consistent with \(\kappa A > \|J\|\). This supports the claim that the parameters are linked by a stability constraint.  
- **Robustness:** The qualitative picture—two attractor regions separated by an instability zone—is expected to persist across a broad parameter range, demonstrating structural stability.

---

## Part III – Testable Hypotheses

Each hypothesis specifies the construct, predicted direction, and experimental paradigm. All are, in principle, falsifiable. Hypotheses are grouped as Primary or Exploratory. The core framework is tested by the Primary Hypotheses (H1, H2, H6, H7, H8). Exploratory hypotheses extend the framework but are not integral to the precision–entropy–anchor chain. Two additional hypotheses (H3: Tetrachromacy; H4: Pink Noise) are described in Appendix A as supplementary.

**General Note on Experimental Design.** Studies must include active control groups matched on relevant confounds (IQ, education, domain expertise, personality). Longitudinal designs are preferred over cross‑sectional comparisons. Pre‑registration, open data/code, and multi‑site replication are essential, given known EEG variability. The detailed controls described for H1 serve as a template.

### Primary Hypotheses

**H1: Aperiodic Signature of DSPA.**  
**Prediction:** Individuals with extensive formal methods training will exhibit a **steeper aperiodic (1/f) spectral slope** during resting‑state EEG compared to matched controls, and this difference will be most pronounced during structural reasoning tasks.  
**Illustrative Benchmark:** Exponent shift of **0.2–0.4** (to be refined by pilot data).  
**Controls:** Mathematicians/physicists without formal verification, software engineers without formal methods, chess players/musicians with comparable structural demands.  
**Method:** FOOOF/specparam extraction; resting state and active invariant‑identification task.

**H2: Deterministic Anchor Synchronisation.**  
**Prediction:** Dyads sharing a deterministic anchor will show **enhanced interbrain phase synchrony** in gamma and alpha bands compared to a scrambled anchor condition.  
**Illustrative Benchmark:** PLV in **40–60 Hz gamma band** > 0.3 for DSPA‑pairs, < 0.2 for CSPA‑pairs and scrambled anchor.  
**Method:** 2 (DSPA‑pair vs. CSPA‑pair) × 2 (Deterministic vs. Scrambled anchor) mixed design; PLV and circular correlation.

**H6: Witness Contract Synchrony.**  
**Prediction:** Dyads jointly interacting with a Witness Contract Lite corpus will show **elevated interbrain gamma/alpha phase‑locking and reduced individual aperiodic exponents** compared to unstructured collaboration.  
**Illustrative Benchmark:** Error variance approximately doubling within 10 seconds after anchor removal for DSPA‑like individuals in the hidden‑state tracking task.  
**Method:** Hyperscanning during joint verification tasks using Witness Contract Lite vs. unstructured discussion; concurrent corpus audit logs.

**H7: Formal Training → Kernel Alignment.**  
**Prediction:** Individuals with DSPA‑like profiles will exhibit **faster adoption and lower error rates** when using Witness Contract tools, with measurable EEG shifts toward steeper aperiodic slopes during verification tasks.  
**Method:** Longitudinal study; EEG before and after Witness Contract training; error rate and completion time metrics.

**H8: Witness Contract Structural Performance.**  
**Prediction:** Engineered DSPA systems implementing the Witness Contract will exhibit **lower structural prediction error and higher replay fidelity** compared to non‑witnessed baselines in benchmark reasoning tasks.  
**Method:** Compare Witness Contract reasoner vs. baseline (e.g., LLM without formal witnesses). Metrics: rate of logical contradictions, consistency across repeated identical inputs.

### Exploratory Hypothesis

**H9: Hierarchical Processing Signature.**  
**Prediction:** During a dual‑task that mixes structural reasoning with environmental monitoring, DSPA‑like individuals will exhibit a **steeper aperiodic slope over frontal electrodes** (DSPA‑dominant) and a **flatter aperiodic slope over occipital electrodes** (CSPA‑dominant).  
**Mechanism:** Region‑specific neuromodulation and hierarchical predictive coding allow different cortical areas to occupy distinct attractor states.  
**Method:** High‑density EEG; separate FOOOF extraction for frontal and occipital clusters.

### Prediction Table

| Prediction | Measured By | Expected Result | Falsifies DSPA? |
|------------|-------------|-----------------|-----------------|
| H1 | FOOOF exponent | Δ 0.2–0.4 | Yes |
| H2 | PLV | >0.3 vs. <0.2 | Yes |
| H6 | PLV + aperiodic | Joint verification > unstructured | Yes |
| H7 | Error rates + EEG | Training shifts slope | Yes |
| H8 | Structural error + replay | Witness Contract > baseline | Tests normative |
| H9 | Frontal vs. occipital slope | Steeper frontal, flatter occipital | Exploratory |

*Supplementary hypotheses (H3: Tetrachromacy, H4: Pink Noise) are detailed in Appendix A and do not affect the core framework.*

---

## 4. Potential Long‑Term Applications

The following directions are contingent on empirical validation of the framework's core predictions.

**4.1 Social Media Architecture.** If the Proposed Pink Noise Protocol is validated, a 1/f feed algorithm that spaces content according to natural attentional rhythms could reduce cognitive load.

**4.2 Information Security.** The Witness Contract's deterministic execution paths, replayability, authority chains, and kernel invariants provide foundations for high‑assurance audit logs and tamper‑evident reasoning traces, independent of any biological claims.

**4.3 Therapeutic and Co‑Working Environments.** If the attentional filtering cost hypothesis is supported, pink noise soundscapes could be deployed in co‑working spaces, therapeutic settings for sensory overload, and educational environments accommodating diverse cognitive styles.

**4.4 Research Recruitment.** If DSPA‑like cognitive profiles exist and are measurable, structural "cognitive trapping" methods—asymmetric data paradoxes, bi‑ocular stereo viewing traps, deterministic anchor broadcasts, and minimal Witness Contract "beacons"—could serve as asymmetric attractors for research recruitment.

**4.5 Cognitive Systems Engineering.** DSPA‑oriented tools prioritising explicit invariants, deterministic behaviour, high‑resolution structural feedback, immutable audit trails, and minimal ambiguity can be designed and evaluated independently of whether DSPA is biologically realised. The Witness Contract provides a reference implementation of such principles. In human‑AI hybrid systems, the Witness Contract may serve as a "DSPA prosthesis" for CSPA users on high‑stakes tasks, providing external deterministic scaffolding that compensates for their native preference for entropy.

**4.6 Ethical Risks of Anchor Dependency.** No technology is neutral, and deterministic anchors present unique risks. A DSPA system with mandatory anchor coupling may be vulnerable to **anchor corruption**: if a trusted proof corpus, algorithm, or institutional record is compromised, the dependent cognitive system may propagate errors with high confidence. Furthermore, if deterministic anchors—such as curated information feeds or rhythmic broadcasts—can entrain brain dynamics, they could be exploited for **attention capture, political influence, or addictive design**. The pink noise protocol, if misused, could pacify populations or reduce cognitive resistance to undesirable stimuli. We propose the following ethical guidelines for anchor design and deployment: **transparency** (the anchor's structure and provenance must be auditable), **revocability** (anchors should be designed with graceful degradation, allowing safe disengagement), and **non‑coercive deployment** (anchor‑based environments should be opt‑in and not used to manipulate behaviour without informed consent). These risks are not unique to DSPA—any structured environment shapes cognition—but DSPA's explicit dependence on invariants makes these considerations particularly salient.

**4.7 Clinical Extensions as Hypotheses Requiring Collaboration.** The DSPA/CSPA parameter space overlaps with constructs in computational psychiatry. For example, the excessive precision on threat‑related prediction errors described in obsessive‑compulsive disorder (Fradkin et al., 2020) shares formal similarities with a high‑Π regime, and ritualistic behaviours might formally parallel self‑generated anchors. Similarly, in anxiety disorders, a mismatch between high precision and low anchor availability could theoretically produce the chronic prediction‑error amplification described by Paulus & Stein (2006). In schizophrenia, attenuated precision on high‑level priors has been associated with disconnection‑based models of psychosis (Adams et al., 2013; Sterzer et al., 2018).

These overlaps raise **exploratory questions** for clinical researchers:

- Do measures of anchor dependence (A) and aperiodic slope differ between individuals with OCD, anxiety, or schizophrenia and healthy controls?
- Can anchor‑based interventions (structured routines, cognitive‑behavioural protocols) shift the parameter vector toward more adaptive attractor basins?
- Do longitudinal changes in precision or anchor use correlate with treatment response?

All clinical applications are contingent on collaborative empirical validation; the framework does not currently provide diagnostic or therapeutic recommendations.

**4.8 Interdisciplinary Research Collaborations.**  
- **Neuroscience:** Partner with groups managing large‑scale EEG databases (e.g., EEG‑LAB, Human Connectome Project) to search for individual differences in aperiodic slope that correlate with professional or educational backgrounds, testing H1 on an epidemiological scale. Multi‑site pre‑registered replication should be a core component of this effort.  
- **Formal Methods:** Collaborate with Lean and TLA+ communities to integrate Witness Contract logging into their tools, collecting behavioural data on user verification patterns and error rates to test H7 and H8.  
- **Music Cognition:** Work with rhythm researchers to test whether DSPA‑like individuals entrain more strongly to isochronous beats and whether that predicts anchor‑dependence measures, providing a behavioural validation of the kinetic coupling hypothesis.  
- **Psychiatry:** Pilot the hidden‑state tracking paradigm in OCD, anxiety, and schizophrenia populations—in collaboration with clinical research teams—to validate the anchor‑dependence construct clinically.  
- **Cognitive Psychology / Human‑Computer Interaction:** Adapt existing cognitive offloading paradigms (Risko & Gilbert, 2016; Sparrow et al., 2011) to measure anchor dependence and correlate with EEG signatures, providing convergent validity for \(A\).

---

## 5. Limitations

We explicitly acknowledge the following limitations.

### Theoretical Limitations
1. **Idealised Constructs:** DSPA and CSPA are computational idealisations. Cluster analysis of real θ vectors in large EEG and behavioural datasets is needed to confirm bimodality.
2. **Theorem Assumptions:** Theorem 1 relies on the Laplace approximation and the assumption of an informative likelihood. These conditions may not hold in all contexts, and the precision–entropy relationship may be more complex in regimes involving active inference, multimodal posteriors, or highly nonlinear generative models.
3. **Unified Objective:** A unified objective function over the full parameter vector θ has not yet been derived; the present framework uses separate CSPA and DSPA objectives plus the anchor constraint. Developing such a unified objective remains a direction for future formal work.
4. **Parameter Dynamics Specification:** The gradient‑descent model in Section 2.4.1 is a first proposal; the true dynamics of precision, entropy, and anchor dependence are likely more complex and may involve additional regulatory terms and nonlinear interactions.
5. **Mixed‑Regime Mechanism:** The mechanism by which different brain regions maintain separate attractor states is provisionally attributed to region‑specific neuromodulation and hierarchical predictive coding. Direct empirical support for this mechanism is currently lacking, and alternative explanations (e.g., task‑dependent network segregation, attentional modulation) have not been ruled out.

### Empirical Limitations
6. **Component vs. Integrated Evidence:** Individual components (aperiodic EEG, interbrain synchrony, pink noise, efficient coding) are empirically supported; their integration into a single model is untested. The framework is a proposal for how these components *might* relate, not a summary of established relationships.
7. **Alternative Explanations:** Phenomena attributed to DSPA could be explained by attentional style, domain expertise, personality traits, general intelligence, or individual variability in predictive processing parameters, without invoking distinct processing architectures. The formal methods–EEG link (H1) is particularly vulnerable to confounding by IQ and education.
8. **Operationalisation of Anchor Dependence:** The proposed measures for \(A\) are provisional and require validation. While cognitive offloading paradigms provide a starting point, their direct applicability to the Duotronics framework remains to be demonstrated.
9. **Lack of Direct Evidence:** The specific anchor‑dependence mechanisms, the Proposed Pink Noise Protocol, the hierarchical processing prediction (H9), and the clinical extensions (Section 4.7) have not been directly tested and remain hypotheses. The clinical extensions, in particular, are speculative and require formal collaboration with clinical researchers before any translational claims can be made.
10. **EEG Biomarker Reliability:** Aperiodic slope and gamma coherence are subject to known variability across recording sites, preprocessing pipelines, and participant populations. Positive results from single‑site studies should be interpreted cautiously pending multi‑site replication.

### Methodological Limitations
11. **Simulation‑to‑Brain Gap:** The toy simulation demonstrates mathematical consistency but abstracts away biological noise, hierarchical structure, and embodiment. A direct mapping between the simulated state space and measurable neural variables is not yet established.
12. **Witness Contract Overhead:** The Witness Contract is a heavyweight formalisation; its overhead may favour pure DSPA regimes and increase metabolic cost for CSPA users. Adoption requires significant upfront investment in verification tooling. In human‑AI hybrid systems, the Witness Contract may serve as a "DSPA prosthesis" for CSPA users on high‑stakes tasks, but this carries the risk of cognitive dependency and reduced development of native reasoning capacity. The proposed Witness Contract Lite partially mitigates this for experimental contexts, but the full pipeline remains demanding.

### Scope Limitations
13. **Consciousness and Qualia:** The framework does not address consciousness, qualia, or subjective experience.
14. **Tripartite Nature:** The current paper spans theoretical neuroscience, formal methods, and speculative bio‑coupling. Future work may separate these threads into focused publications.

---

## 6. Relationship to Existing Computational Frameworks

| Framework | Primary Focus | Relationship to Duotronics |
|-----------|---------------|---------------------------|
| **Predictive Processing** (Rao & Ballard, Friston, Clark) | Hierarchical inference, precision weighting | CSPA/DSPA are proposed as distinct precision‑weighting regimes within PP |
| **Active Inference** (Friston et al.) | Action as free energy minimisation | Deterministic anchors may function as external generative models stabilising active inference; the active inference term in §2.4 aligns action selection with the framework |
| **High‑Precision Autism Theories** (Pellicano & Burr, Van de Cruys et al.) | Attenuated priors, high sensory precision in autism | DSPA shares features with this computational phenotype but is agnostic about clinical categorisation; DSPA is a regime, not a diagnosis |
| **Efficient Coding** (Barlow, Olshausen, Simoncelli) | Metabolic constraints on neural representation | CSPA's metabolic efficiency objective is grounded in efficient coding; DSPA represents a different point on the efficiency–precision trade‑off |
| **Kalman Filtering / Bayesian Filtering** (Kalman, Åström & Murray) | Recursive state estimation | The dynamical equation structurally resembles a Kalman–Bucy filter with an added anchor reference and active control term |
| **Control Theory / Synchronisation** (Pikovsky et al.) | Stability, coupled oscillators | Anchor coupling is analogous to reference tracking in control; interbrain synchrony comparable to coupled‑oscillator phase locking |
| **Dynamical Systems Neuroscience** (Kelso, Freeman, Rabinovich) | State‑space trajectories and attractors | DSPA/CSPA as attractor regions in a continuous parameter space; multistability and metastability provide a natural language for regime transitions |
| **Neural Manifolds** (Cunningham & Yu, Gallego et al.) | Low‑dimensional latent dynamics | The θ space can be interpreted as a control manifold shaping brain dynamics; this connection may provide a stronger mathematical framework than categorical styles |
| **Extended Mind & Distributed Cognition** (Clark & Chalmers, Hutchins) | Cognition extended into the environment | The Anchor variable (A) builds directly on the claim that external structures can become constitutive components of cognitive systems |
| **Cognitive Offloading** (Risko & Gilbert, Sparrow et al.) | Use of external resources to reduce internal demand | Provides behavioural paradigms and measurement approaches directly applicable to operationalising Anchor dependence |
| **External Representations & Notations** (Kirsh, Scaife & Rogers, Norman) | How external symbolic structures shape cognition | Provides examples of deterministic external state: mathematical notation, diagrams, formal specifications, programming environments |
| **Computational Psychiatry** (Adams et al., Fradkin et al.) | Formal models of psychopathology | Clinical extensions (Section 4.7) build on existing computational accounts of psychosis, OCD, and anxiety, proposing anchor‑dependence as an additional parameter |
| **Gamma‑Band Synchrony** (Fries, Singer, Bastos et al.) | Communication‑through‑coherence, feedforward error propagation | Gamma coherence is predicted to be elevated in DSPA during structured reasoning, consistent with its role in precision‑weighted signalling |
| **Aperiodic EEG** (Voytek, Donoghue, Waschke et al.) | 1/f spectral exponent as a marker of excitation/inhibition balance | Steeper aperiodic slope is a hypothesised consequence of low‑entropy, high‑precision dynamics |
| **Formal Methods & Verification** (Lamport, de Moura, Lean, TLA+, Gordon, Nipkow, Bertot & Castéran, Harrison) | Machine‑checkable proof, model checking | The Witness Contract supplies executable deterministic anchors bridging Duotronics to formal verification |
| **Programming Cognition** (Soloway, Pennington, Storey) | Mental representations in programming and software engineering | The affinity of DSPA for formal methods is partially grounded in the structured reasoning demands of verification‑aware programming |
| **Individual Differences** (Baron‑Cohen, Cacioppo, Kruglanski, Witkin, Frederick) | Cognitive styles: systemising, need for cognition, need for closure, field dependence, cognitive reflection | These constructs are predicted to converge in regions of the Duotronics parameter space, providing convergent validity |
| **Neurodiversity Frameworks** (Singer, Silberman) | Cognitive variation as natural diversity | Compatible; Duotronics provides computational language for specific cognitive diversity without pathologising |

---

## 7. Conclusion

The Duotronics Framework proposes that cognition can be modelled through a continuous four‑dimensional parameter space \(\theta = (H, \Pi, \gamma, A)\), whose attractor regions define two idealised processing architectures—CSPA and DSPA. By grounding each dimension in independent, well‑established literatures; providing a causal–mechanistic chain including a formal theorem and a stability proposition; specifying concrete parameter dynamics with timescale separation and a bistable landscape; introducing hierarchical extensions, developmental trajectories, and embodied motor anchors; integrating the Witness Contract as a normative implementation with a pilot study blueprint; offering illustrative quantitative benchmarks; raising exploratory clinical questions; addressing ethical risks; and clearly separating established science, model constructs, testable hypotheses, and speculation, we offer Duotronics as a structured research programme. The deterministic anchor concept—external invariant structures that stabilise recursive inference—may prove to be the framework's most original contribution. Whether this parameter space carves nature at its joints will be determined by the experiments it inspires.

---

## Appendix A: Supplementary Hypotheses

**H3: Tetrachromacy–Gamma Correlation (Tangential).**  
Functional tetrachromats may exhibit elevated gamma‑band power and coherence during chromatic discrimination tasks. This hypothesis is exploratory and the link to DSPA remains tenuous.

**H4: Proposed Pink Noise Protocol – Environmental Intervention.**  
Continuous pink noise in workspaces will reduce subjective cognitive fatigue and salivary cortisol during high‑demand cognitive tasks, compared to white noise or silence. One speculative mechanism—requiring direct testing—is that the shared 1/f structure between pink noise and the brain’s intrinsic dynamics may reduce metabolic load, potentially smoothing transitions between regimes. The core framework does not depend on this interpretation.

---

## References

### Predictive Processing & Free Energy Principle
- Rao, R. P. N., & Ballard, D. H. (1999). *Nat. Neurosci.*, 2(1), 79‑87. DOI: [https://doi.org/10.1038/4580](https://doi.org/10.1038/4580)
- Friston, K. (2005). *Phil. Trans. R. Soc. B*, 360(1456), 815‑836. DOI: [https://doi.org/10.1098/rstb.2005.1622](https://doi.org/10.1098/rstb.2005.1622)
- Friston, K. (2010). *Nat. Rev. Neurosci.*, 11(2), 127‑138. DOI: [https://doi.org/10.1038/nrn2787](https://doi.org/10.1038/nrn2787)
- Clark, A. (2013). *Behav. Brain Sci.*, 36(3), 181‑204. DOI: [https://doi.org/10.1017/S0140525X12000477](https://doi.org/10.1017/S0140525X12000477)
- Hohwy, J. (2013). *The Predictive Mind*. OUP. ISBN: 978‑0‑19‑968273‑7
- Clark, A. (2016). *Surfing Uncertainty*. OUP. ISBN: 978‑0‑19‑021701‑3
- Friston, K. et al. (2017). *Neural Comput.*, 29(1), 1‑49. DOI: [https://doi.org/10.1162/NECO_a_00912](https://doi.org/10.1162/NECO_a_00912)
- Feldman, H., & Friston, K. J. (2010). *Front. Hum. Neurosci.*, 4, 215. DOI: [https://doi.org/10.3389/fnhum.2010.00215](https://doi.org/10.3389/fnhum.2010.00215)
- Friston, K. J. et al. (2012). *PLoS Comput. Biol.*, 8(1), e1002327. DOI: [https://doi.org/10.1371/journal.pcbi.1002327](https://doi.org/10.1371/journal.pcbi.1002327)
- Parr, T., & Friston, K. J. (2019). *Biol. Cybern.*, 113(5‑6), 495‑513. DOI: [https://doi.org/10.1007/s00422-019-00805-w](https://doi.org/10.1007/s00422-019-00805-w)
- Schwartenbeck, P. et al. (2019). *eLife*, 8, e41703. DOI: [https://doi.org/10.7554/eLife.41703](https://doi.org/10.7554/eLife.41703)
- Lawson, R. P. et al. (2017). *Nat. Neurosci.*, 20(9), 1293‑1299. DOI: [https://doi.org/10.1038/nn.4615](https://doi.org/10.1038/nn.4615)
- Van de Cruys, S. et al. (2014). *Psychol. Rev.*, 121(4), 649‑675. DOI: [https://doi.org/10.1037/a0037665](https://doi.org/10.1037/a0037665)
- Pellicano, E., & Burr, D. (2012). *Trends Cogn. Sci.*, 16(10), 504‑510. DOI: [https://doi.org/10.1016/j.tics.2012.08.009](https://doi.org/10.1016/j.tics.2012.08.009)
- Smith, R. et al. (2021). *Psychiatry Clin. Neurosci.*, 75(4), 118‑128. DOI: [https://doi.org/10.1111/pcn.13138](https://doi.org/10.1111/pcn.13138)
- Hodson, R. et al. (2025). *Neurosci. Biobehav. Rev.*, 105504. DOI: [https://doi.org/10.1016/j.neubiorev.2023.105504](https://doi.org/10.1016/j.neubiorev.2023.105504)
- Millidge, B. et al. (2021). *arXiv*:2107.12979.

### Efficient Coding
- Barlow, H. B. (1961). In *Sensory Communication*. MIT Press.
- Attneave, F. (1954). *Psychol. Rev.*, 61(3), 183‑193. DOI: [https://doi.org/10.1037/h0054663](https://doi.org/10.1037/h0054663)
- Laughlin, S. B. (2001). *Curr. Opin. Neurobiol.*, 11(4), 475‑480. DOI: [https://doi.org/10.1016/S0959-4388(00)00237-3](https://doi.org/10.1016/S0959-4388(00)00237-3)
- Olshausen, B. A., & Field, D. J. (1996). *Nature*, 381(6583), 607‑609. DOI: [https://doi.org/10.1038/381607a0](https://doi.org/10.1038/381607a0)
- Simoncelli, E. P., & Olshausen, B. A. (2001). *Annu. Rev. Neurosci.*, 24, 1193‑1216. DOI: [https://doi.org/10.1146/annurev.neuro.24.1.1193](https://doi.org/10.1146/annurev.neuro.24.1.1193)
- Shannon, C. E. (1948). *Bell Syst. Tech. J.*, 27(3), 379‑423. DOI: [https://doi.org/10.1002/j.1538-7305.1948.tb01338.x](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x)
- Tishby, N. et al. (1999). *Proc. Allerton Conf.*
- Buesing, L. et al. (2011). *Neuron*, 70(4), 705‑718. DOI: [https://doi.org/10.1016/j.neuron.2011.03.032](https://doi.org/10.1016/j.neuron.2011.03.032)
- Sengupta, B. et al. (2013). *PLoS Comput. Biol.*, 9(7), e1003157. DOI: [https://doi.org/10.1371/journal.pcbi.1003157](https://doi.org/10.1371/journal.pcbi.1003157)

### Aperiodic EEG
- Donoghue, T. et al. (2020). *Nat. Neurosci.*, 23(12), 1655‑1665. DOI: [https://doi.org/10.1038/s41593-020-00744-x](https://doi.org/10.1038/s41593-020-00744-x)
- Gao, R. et al. (2017). *NeuroImage*, 158, 70‑78. DOI: [https://doi.org/10.1016/j.neuroimage.2017.06.078](https://doi.org/10.1016/j.neuroimage.2017.06.078)
- Voytek, B. et al. (2015). *J. Neurosci.*, 35(38), 13257‑13265. DOI: [https://doi.org/10.1523/JNEUROSCI.2332-14.2015](https://doi.org/10.1523/JNEUROSCI.2332-14.2015)
- Voytek, B., & Knight, R. T. (2015). *Biol. Psychiatry*, 77(12), 1089‑1097. DOI: [https://doi.org/10.1016/j.biopsych.2014.10.023](https://doi.org/10.1016/j.biopsych.2014.10.023)
- Waschke, L. et al. (2021). *eLife*, 10, e63016. DOI: [https://doi.org/10.7554/eLife.63016](https://doi.org/10.7554/eLife.63016)
- Hemmerich, K. et al. (2026). *Rev. Neurosci.*, 37(3). DOI: [https://doi.org/10.1515/revneuro-2026-0012](https://doi.org/10.1515/revneuro-2026-0012)
- Robertson, M. M. et al. (2019). *Curr. Opin. Neurobiol.*, 58, 1‑8. DOI: [https://doi.org/10.1016/j.conb.2019.06.002](https://doi.org/10.1016/j.conb.2019.06.002)

### Gamma Oscillations & Hyperscanning
- Singer, W. (1999). *Neuron*, 24(1), 49‑65. DOI: [https://doi.org/10.1016/S0896-6273(00)80821-1](https://doi.org/10.1016/S0896-6273(00)80821-1)
- Fries, P. (2005). *Trends Cogn. Sci.*, 9(10), 474‑480. DOI: [https://doi.org/10.1016/j.tics.2005.08.011](https://doi.org/10.1016/j.tics.2005.08.011)
- Fries, P. (2015). *Neuron*, 88(1), 220‑235. DOI: [https://doi.org/10.1016/j.neuron.2015.09.034](https://doi.org/10.1016/j.neuron.2015.09.034)
- Bastos, A. M. et al. (2012). *Neuron*, 76(4), 695‑711. DOI: [https://doi.org/10.1016/j.neuron.2012.10.038](https://doi.org/10.1016/j.neuron.2012.10.038)
- Bastos, A. M. et al. (2015). *Neuron*, 85(2), 390‑401. DOI: [https://doi.org/10.1016/j.neuron.2014.12.047](https://doi.org/10.1016/j.neuron.2014.12.047)
- Dumas, G. et al. (2010). *PLoS ONE*, 5(8), e12166. DOI: [https://doi.org/10.1371/journal.pone.0012166](https://doi.org/10.1371/journal.pone.0012166)
- Lindenberger, U. et al. (2009). *BMC Neurosci.*, 10, 22. DOI: [https://doi.org/10.1186/1471-2202-10-22](https://doi.org/10.1186/1471-2202-10-22)
- Dikker, S. et al. (2017). *Curr. Biol.*, 27(9), 1375‑1380. DOI: [https://doi.org/10.1016/j.cub.2017.04.002](https://doi.org/10.1016/j.cub.2017.04.002)
- Koike, T. et al. (2015). *Neurosci. Res.*, 90, 25‑32. DOI: [https://doi.org/10.1016/j.neures.2014.10.010](https://doi.org/10.1016/j.neures.2014.10.010)
- Babiloni, F., & Astolfi, L. (2014). *Cortex*, 58, 60‑69. DOI: [https://doi.org/10.1016/j.cortex.2014.01.006](https://doi.org/10.1016/j.cortex.2014.01.006)

### Dynamical Systems & Neural Manifolds
- Kelso, J. A. S. (1995). *Dynamic Patterns*. MIT Press. ISBN: 978‑0‑262‑61131‑2
- Kelso, J. A. S. (2012). *Phil. Trans. R. Soc. B*, 367(1591), 906‑918. DOI: [https://doi.org/10.1098/rstb.2011.0351](https://doi.org/10.1098/rstb.2011.0351)
- Freeman, W. J. (2000). *Neurodynamics*. Springer. ISBN: 978‑1‑85233‑615‑7
- Rabinovich, M. I. et al. (2006). *Rev. Mod. Phys.*, 78(4), 1213‑1265. DOI: [https://doi.org/10.1103/RevModPhys.78.1213](https://doi.org/10.1103/RevModPhys.78.1213)
- Tognoli, E., & Kelso, J. A. S. (2014). *Neuron*, 81(1), 35‑48. DOI: [https://doi.org/10.1016/j.neuron.2013.12.022](https://doi.org/10.1016/j.neuron.2013.12.022)
- Cunningham, J. P., & Yu, B. M. (2014). *Nat. Neurosci.*, 17(11), 1500‑1509. DOI: [https://doi.org/10.1038/nn.3776](https://doi.org/10.1038/nn.3776)
- Gallego, J. A. et al. (2017). *Neuron*, 94(5), 978‑984. DOI: [https://doi.org/10.1016/j.neuron.2017.05.025](https://doi.org/10.1016/j.neuron.2017.05.025)
- Stringer, C. et al. (2019). *Nature*, 571, 361‑365. DOI: [https://doi.org/10.1038/s41586-019-1346-5](https://doi.org/10.1038/s41586-019-1346-5)
- Beggs, J. M., & Plenz, D. (2003). *J. Neurosci.*, 23(35), 11167‑11177. DOI: [https://doi.org/10.1523/JNEUROSCI.23-35-11167.2003](https://doi.org/10.1523/JNEUROSCI.23-35-11167.2003)
- Cocchi, L. et al. (2017). *Prog. Neurobiol.*, 158, 132‑152. DOI: [https://doi.org/10.1016/j.pneurobio.2017.07.002](https://doi.org/10.1016/j.pneurobio.2017.07.002)

### Extended Mind & Cognitive Offloading
- Hutchins, E. (1995). *Cognition in the Wild*. MIT Press. ISBN: 978‑0‑262‑58146‑0
- Clark, A., & Chalmers, D. (1998). *Analysis*, 58(1), 7‑19. DOI: [https://doi.org/10.1093/analys/58.1.7](https://doi.org/10.1093/analys/58.1.7)
- Kirsh, D. (2010). In *The Cognitive Life of Things*. CUP. DOI: [https://doi.org/10.1017/CBO9780511762718.011](https://doi.org/10.1017/CBO9780511762718.011)
- Scaife, M., & Rogers, Y. (1996). *Int. J. Hum.‑Comput. Stud.*, 45(2), 185‑213. DOI: [https://doi.org/10.1006/ijhc.1996.0048](https://doi.org/10.1006/ijhc.1996.0048)
- Norman, D. A. (1993). *Things That Make Us Smart*. Addison‑Wesley. ISBN: 978‑0‑201‑62695‑2
- Risko, E. F., & Gilbert, S. J. (2016). *Trends Cogn. Sci.*, 20(9), 676‑688. DOI: [https://doi.org/10.1016/j.tics.2016.07.002](https://doi.org/10.1016/j.tics.2016.07.002)
- Gilbert, S. J. (2015). *Q. J. Exp. Psychol.*, 68(5), 971‑992. DOI: [https://doi.org/10.1080/17470218.2014.978843](https://doi.org/10.1080/17470218.2014.978843)
- Sparrow, B. et al. (2011). *Science*, 333(6043), 776‑778. DOI: [https://doi.org/10.1126/science.1207745](https://doi.org/10.1126/science.1207745)
- Storm, B. C., & Stone, S. M. (2015). *Psychol. Sci.*, 26(2), 182‑188. DOI: [https://doi.org/10.1177/0956797614559285](https://doi.org/10.1177/0956797614559285)

### Formal Methods & Verification
- Sobel, A. E. K., & Clarkson, M. R. (2002). *IEEE Trans. Softw. Eng.*, 28(3), 308‑320. DOI: [https://doi.org/10.1109/32.991972](https://doi.org/10.1109/32.991972)
- Beynon‑Davies, P. (2014). In *Formal Methods and the Social Sciences*. DOI: [https://doi.org/10.1007/978-3-319-09450-2_4](https://doi.org/10.1007/978-3-319-09450-2_4)
- Lamport, L. (2002). *Specifying Systems*. Addison‑Wesley. ISBN: 978‑0‑321‑14306‑8
- de Moura, L. et al. (2015). *CADE‑25*, LNCS 9236, 378‑388. DOI: [https://doi.org/10.1007/978-3-319-21401-6_26](https://doi.org/10.1007/978-3-319-21401-6_26)
- Gordon, M. (2000). In *Proof, Language, and Interaction*. MIT Press.
- Nipkow, T. (2002). *Isabelle/HOL*. LNCS 2283. DOI: [https://doi.org/10.1007/3-540-45949-9](https://doi.org/10.1007/3-540-45949-9)
- Bertot, Y., & Castéran, P. (2004). *Coq’Art*. Springer. ISBN: 978‑3‑540‑20854‑9
- Harrison, J. (2009). *Handbook of Practical Logic*. CUP. ISBN: 978‑0‑521‑89957‑4

### Programming Cognition & HCI
- Soloway, E. (1986). *Commun. ACM*, 29(9), 850‑858. DOI: [https://doi.org/10.1145/6592.6594](https://doi.org/10.1145/6592.6594)
- Pennington, N. (1987). *Cogn. Psychol.*, 19(3), 295‑341. DOI: [https://doi.org/10.1016/0010-0285(87)90007-7](https://doi.org/10.1016/0010-0285(87)90007-7)
- Storey, M.‑A. (2006). *Softw. Qual. J.*, 14(3), 187‑208. DOI: [https://doi.org/10.1007/s11219-006-9216-4](https://doi.org/10.1007/s11219-006-9216-4)
- Green, T. R. G., & Petre, M. (1996). *J. Vis. Lang. Comput.*, 7(2), 131‑174. DOI: [https://doi.org/10.1006/jvlc.1996.0009](https://doi.org/10.1006/jvlc.1996.0009)

### Individual Differences
- Baron‑Cohen, S. et al. (2003). *Phil. Trans. R. Soc. B*, 358(1430), 361‑374. DOI: [https://doi.org/10.1098/rstb.2002.1206](https://doi.org/10.1098/rstb.2002.1206)
- Cacioppo, J. T., & Petty, R. E. (1982). *J. Pers. Soc. Psychol.*, 42(1), 116‑131. DOI: [https://doi.org/10.1037/0022-3514.42.1.116](https://doi.org/10.1037/0022-3514.42.1.116)
- Kruglanski, A. W. et al. (1993). *J. Pers. Soc. Psychol.*, 65(5), 861‑876. DOI: [https://doi.org/10.1037/0022-3514.65.5.861](https://doi.org/10.1037/0022-3514.65.5.861)
- Budner, S. (1962). *J. Pers.*, 30(1), 29‑50. DOI: [https://doi.org/10.1111/j.1467-6494.1962.tb02303.x](https://doi.org/10.1111/j.1467-6494.1962.tb02303.x)
- Neuberg, S. L., & Newsom, J. T. (1993). *J. Pers. Soc. Psychol.*, 65(1), 113‑131. DOI: [https://doi.org/10.1037/0022-3514.65.1.113](https://doi.org/10.1037/0022-3514.65.1.113)
- Frederick, S. (2005). *J. Econ. Perspect.*, 19(4), 25‑42. DOI: [https://doi.org/10.1257/089533005775196732](https://doi.org/10.1257/089533005775196732)
- Witkin, H. A. et al. (1977). *Rev. Educ. Res.*, 47(1), 1‑64. DOI: [https://doi.org/10.3102/00346543047001001](https://doi.org/10.3102/00346543047001001)

### Computational Psychiatry
- Adams, R. A. et al. (2013). *Front. Psychiatry*, 4, 47. DOI: [https://doi.org/10.3389/fpsyt.2013.00047](https://doi.org/10.3389/fpsyt.2013.00047)
- Fradkin, I. et al. (2020). *Psychol. Rev.*, 127(5), 853‑878. DOI: [https://doi.org/10.1037/rev0000199](https://doi.org/10.1037/rev0000199)
- Paulus, M. P., & Stein, M. B. (2006). *Biol. Psychiatry*, 60(4), 383‑387. DOI: [https://doi.org/10.1016/j.biopsych.2006.03.042](https://doi.org/10.1016/j.biopsych.2006.03.042)
- Sterzer, P. et al. (2018). *Biol. Psychiatry*, 84(9), 634‑643. DOI: [https://doi.org/10.1016/j.biopsych.2018.05.015](https://doi.org/10.1016/j.biopsych.2018.05.015)

### Control Theory & Synchronisation
- Åström, K. J., & Murray, R. M. (2008). *Feedback Systems*. Princeton. ISBN: 978‑0‑691‑13576‑2
- Kalman, R. E. (1960). *J. Basic Eng.*, 82(1), 35‑45. DOI: [https://doi.org/10.1115/1.3662552](https://doi.org/10.1115/1.3662552)
- Pikovsky, A. et al. (2001). *Synchronization*. CUP. ISBN: 978‑0‑521‑53352‑2

### Pink Noise (for Appendix H4)
- Zhou, X. et al. (2012). *J. Theor. Biol.*, 306, 68‑72. DOI: [https://doi.org/10.1016/j.jtbi.2012.04.006](https://doi.org/10.1016/j.jtbi.2012.04.006)
- Mossbridge, J. et al. (2014). *J. Conscious. Explor. Res.*, 5(10), 990‑1005.
- Söderlund, G. et al. (2010). *Behav. Brain Funct.*, 6, 55. DOI: [https://doi.org/10.1186/1744-9081-6-55](https://doi.org/10.1186/1744-9081-6-55)
- Ping, J. et al. (2025). *bioRxiv*. DOI: [https://doi.org/10.1101/2025.05.04.651950v1](https://doi.org/10.1101/2025.05.04.651950v1)
- Johnson, M., & Chen, L. (2024). *OSF Preprints*.

### Tetrachromacy (for Appendix H3)
- Jameson, K. A. et al. (2001). *Psychon. Bull. Rev.*, 8(2), 244‑261. DOI: [https://doi.org/10.3758/BF03196159](https://doi.org/10.3758/BF03196159)
- Jordan, G. et al. (2010). *J. Vis.*, 10(8), 12. DOI: [https://doi.org/10.1167/10.8.12](https://doi.org/10.1167/10.8.12)

### Neuroscience Textbook
- Dayan, P., & Abbott, L. F. (2001). *Theoretical Neuroscience*. MIT Press. ISBN: 978‑0‑262‑04199‑7

### Witness Contract
- The Blob Inc. (2025). Duotronics Witness Contract v1.6. GitHub repository.

---

## Appendix B: Glossary of Formal Notations

| Symbol | Definition |
|--------|------------|
| \(C(t)\) | Cognitive state vector |
| \(\mathcal{S}\) | Representational state space |
| \(H(C)\) | Representational entropy |
| \(\Pi(t)\) | Prediction‑error precision |
| \(\gamma\) | Gamma‑band phase coherence |
| \(A\) | Anchor dependence |
| \(\mathcal{A}\) | Deterministic anchor |
| \(R_{\mathcal{A}}\) | Anchor reference signal |
| \(\kappa\) | Coupling constant |
| \(\lambda\) | Entropy penalty weight |
| \(\eta_*\) | Learning rates |
| \(\sigma_*\) | Noise amplitudes |
| PLV | Phase‑locking value |
| \(F\) | Variational free energy |
| \(D_{KL}\) | Kullback–Leibler divergence |
| \(J\) | Jacobian |
| \(\theta\) | Full parameter vector |
| \(\Pi_{\text{active}}\) | Active precision |
| \(\nabla_a \mathbb{E}[E_{\text{expected}}]\) | Action gradient |

---
