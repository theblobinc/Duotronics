# A Framework for Dual-Fluid Plasma Reservoir Computing

**Document ID:** CPB‑COMP‑001  
**Revision:** 2.7  
**Date:** 2026‑07‑07  
**Classification:** Technical White Paper  

---

## Abstract

We investigate whether networks of Coherent Particle Beam (CPB) devices can serve as a physical reservoir computer for transport‑related dynamical systems. Each CPB head, in its integrated magnetic levitation turbine (IMLT) form, couples a conductive mist, a tunable magnetic field, a non‑linear plasma, and a high‑bandwidth isolated current sensor. When connected in series and parallel, these nodes form a continuous‑time nonlinear dynamical network whose state evolves according to the coupled Navier‑Stokes, Maxwell, and plasma fluid equations. This paper develops the theoretical framework for the node and network state equations, defines the computation pipeline (encoding → evolution → decoding), analyses the physical relaxation mechanism, evaluation latency, and timescale coupling, and outlines an experimental programme to test the hypothesis that CPB networks can serve as forward, inverse, and surrogate models for continuum transport problems. Analog PDE solving and transport emulation are discussed as secondary operating modes. This is a high‑risk, high‑reward research proposal; all performance claims are hypotheses to be tested against the benchmarks in Section 10, with explicit falsification criteria at multiple stages.

---

## 1. Introduction

### 1.1 The Limits of Digital Fluid Simulation

Direct numerical simulation (DNS) of the Navier‑Stokes equations remains one of the most computationally expensive tasks in science and engineering [1,2]. The fundamental difficulties-spatial and temporal discretisation error, accumulation of floating‑point round‑off, and the exponential divergence of chaotic trajectories-mean that even exascale digital computers cannot resolve many multiscale, turbulent, or reacting flows of practical interest [3,4]. This has motivated a long‑standing search for alternative computing paradigms that are not bound by the von Neumann bottleneck.

### 1.2 Physical Analogue Computation: A Brief History

The idea of using a physical system to solve mathematical problems predates digital computing. Vannevar Bush's differential analyser (1931) used mechanical integrators [5]; Claude Shannon's 1941 work on analogue computing formalised the relationship between physical dynamics and mathematical equations [6]. H. T. Davis extended this work with improved mechanical integrators [7], and later Rubel introduced the Extended Analog Computer concept [8]. For partial differential equations, however, electronic analogues were hampered by the need for many spatial nodes.

A parallel tradition explored **fluidic logic**-amplification, switching, and oscillation using gas or liquid flows rather than electronics [9,10]. Fluidic devices were radiation‑hard, operated at high temperature, and provided intrinsic signal conditioning [11]. Their eventual obsolescence was driven not by a lack of computational capability but by practical issues: limited dynamic range, drift, manufacturing complexity, and the overwhelming scaling advantages of integrated circuits. The CPB concept addresses the reconfigurability limitation through magnetic and electronic control, but the other challenges-drift, noise, dynamic range-remain open questions.

More recently, **physical reservoir computing** has emerged as a powerful framework [12,13]. A non‑linear dynamical system-be it a laser, a memristor array, or a bucket of water-is driven by an input signal, and its high‑dimensional response is linearly combined to approximate a desired output. This paradigm decouples the complex dynamics (provided for free by the physical system) from the training (which reduces to simple regression) [14]. Reservoir computers have been realised with electronic, photonic, spintronic, and mechanical substrates [15,16]. The open question is whether a fluid‑plasma system can contribute uniquely to this landscape.

### 1.3 Primary and Secondary Computational Framings

The CPB network can be viewed through three computational lenses. In this paper we adopt **physical reservoir computing** as the primary framing, because it requires the least restrictive assumptions about the internal dynamics and can be tested with existing benchmarks. The other two framings become natural extensions once the reservoir capability is established:

1. **Physical reservoir computer (primary):** The network is a fixed, high‑dimensional nonlinear dynamical system. Only a linear readout layer is trained. Success is measured by standard reservoir computing benchmarks (Section 10).
2. **Analog PDE solver (extension):** If the network's steady‑state pressure and current distribution can be shown to approximate the solution of a target transport PDE, then the system can be used as a direct physical solver for that class of problems. This requires successful validation of H1 (Appendix F).
3. **Transport emulator (extension):** Configuring the hardware so that its governing equations approximate a desired transport process, without exact equivalence. This is a weaker but still useful form of analogue computation.

We will specify which framing is being invoked in each section.

### 1.4 The Coherent Particle Beam Platform

The Coherent Particle Beam (CPB) platform, described in CPB‑ENG‑001 Rev 4.0 and the companion Integrated Mag‑Lev Turbine white paper [17,18], offers a unique combination of properties that make it a candidate physical computing node. Its key enabling features are:

- A **clean inner tube** where a glow discharge is sustained in static or slowly flowing gas, with plasma current providing a sensitive, non‑linear readout of the gas state.
- A **conductive mist annulus** driven by a magnetically levitated rotor, providing fast, programmable boundary conditions without contaminating the inner tube.

Additional features-tunable magnetic fields acting on both mist and plasma, galvanically isolated dI/dt current sensing via a rotary transformer, and energy harvesting for on‑rotor heating-further support reconfigurable networked operation. This paper does not claim to have demonstrated a working fluid computer; rather, it proposes a **theoretical and experimental programme** to test the hypothesis that coupled CPB networks can serve as a physical reservoir computer for transport and flow problems, with potential advantages in evaluation latency and energy per evaluation compared to purely digital approaches.

---

## 2. The CPB Computing Primitive

### 2.1 Physical Overview of a Single CPB Node

The computational node is a fully instrumented integrated magnetic levitation turbine (IMLT) head. Its components and their computational roles are summarised in Table 1.

| Component | Role in Computation |
|-----------|---------------------|
| Rotor (outer annulus) | Drives conductive mist flow; speed sets the effective "clock" and boundary shear. |
| Stator coils | Spin the rotor and impose programmable rotating/pulsed B‑field on annulus and tube. |
| Conductive mist (outer annulus) | Tunable, non‑linear boundary condition (conductivity, polarisation) for the gas. |
| Inner drift tube | Contains clean gas; hosts plasma; the primary "computational" fluid. |
| Central electrode | Strikes a glow discharge; plasma current is a non‑linear function of gas state. |
| Rotary transformer | Harvests power; senses dI/dt of plasma current with galvanic isolation. |
| FPGA controller | Orchestrates rotor speed, B‑field pulses, and data acquisition. |

### 2.2 State Variables

We define the **internal state** of a single node by separating spatially distributed fields from lumped (global) quantities:

\[
\mathbf{x} = (\mathbf{x}_f,\; \mathbf{x}_l)
\]

where the field variables are

\[
\mathbf{x}_f(\mathbf{r},t) = [\,p(\mathbf{r},t),\; T(\mathbf{r},t),\; \rho(\mathbf{r},t),\; \mathbf{v}(\mathbf{r},t),\; n_e(\mathbf{r},t),\; \mathbf{B}(\mathbf{r},t)\,]
\]

(\(p\) = pressure, \(T\) = temperature, \(\rho\) = density, \(\mathbf{v}\) = velocity, \(n_e\) = electron density, \(\mathbf{B}\) = magnetic field), and the lumped variables are

\[
\mathbf{x}_l(t) = [\,I(t),\; \omega(t),\; \sigma(t)\,]
\]

(\(I\) = total plasma current, \(\omega\) = rotor angular speed, \(\sigma\) = effective mist conductivity). Because the field variables are spatially distributed, the complete state \(\mathbf{x}\) is infinite‑dimensional; finite‑dimensional approximations arise through observation and discretisation. Additional derived variables-such as the electric field \(\mathbf{E}\), current density \(\mathbf{J}\), electrostatic potential \(\phi\), ion density \(n_i\), and electron/neutral velocities \(\mathbf{v}_e, \mathbf{v}_n\)-are introduced in the governing equations (Appendix A) and are functions of the primary state variables.

The dynamics are governed by the compressible Navier‑Stokes equations for the gas [19], the Maxwell equations for \(\mathbf{B}\) [20], and a reduced‑order plasma fluid model (continuity, momentum, and energy equations for electrons and ions, assuming quasi‑neutrality [21,22] and neglecting certain radiative losses where appropriate). These equations are coupled through the ionisation source term, the Lorentz force [23], and the electric field. The complete set of governing equations is provided in Appendix A.

The **observable state** is the set of quantities directly measurable without breaking vacuum: the plasma current \(I\) (via dI/dt integration), the inner‑tube pressure at a finite number of sensor points, and the optical emission spectrum. The **observation equation** linking the internal state to measurements is

\[
\mathbf{y}_i(t) = \mathbf{H}(\mathbf{x}_i(t)) + \boldsymbol{\eta}_i(t),
\tag{1}
\]

where \(\mathbf{H}\) is the observation operator and \(\boldsymbol{\eta}_i\) is the sensor noise [24]. The **control parameters** are the high‑voltage electrode potential \(V_{\text{HV}}\), the rotor speed \(\omega\), the stator coil currents (which determine \(\mathbf{B}\)), and the inlet mist composition and pressure. Inter‑node valve conductances \(C_{ij}\) are treated as **slowly programmable parameters**, set between computational tasks.

### 2.3 The Plasma Nonlinearity: What Is Actually Being Exploited

A critical question for any reviewer is: **what specific nonlinearity does the plasma provide, and how does it serve computation?** We address this explicitly here.

**The I‑V characteristic.** A glow discharge exhibits a nonlinear current‑voltage relationship with three regimes relevant to computation:

1. **Normal glow:** The voltage is nearly constant over a wide current range (~10 µA-1 mA). This provides a stable operating point with moderate nonlinearity from the sheath dynamics.
2. **Abnormal glow:** Above a threshold current, the voltage rises approximately linearly with current. This regime offers a continuously tunable nonlinearity.
3. **Glow‑to‑arc transition:** A sharp, hysteretic transition to a low‑voltage, high‑current arc. This is a **bistable threshold**-useful for switching and memory-but the arc regime is destructive and will be avoided during computation.

The **computationally useful nonlinearity** is the smooth, continuous variation of plasma impedance with gas density, temperature, and flow velocity in the normal and abnormal glow regimes. The sharp transitions provide thresholding, but the continuous dynamics provide the high‑dimensional state space needed for reservoir computing.

**What the plasma does NOT provide.** The plasma current is a spatially integrated quantity. It does not directly resolve local flow features. The sheath dynamics that determine the I‑V characteristic operate on nanosecond‑to‑microsecond timescales, while the gas dynamics evolve on millisecond timescales. The coupling between these timescales is addressed in Section 6.4. The practical consequence is that the plasma acts as a **nonlinear, low‑pass‑filtered readout** of the gas state-it captures slow variations with high sensitivity but averages over fast fluctuations.

### 2.4 Dual‑Fluid State Space

We use the term **dual‑fluid plasma computing** to capture two dualities inherent in each node. The term "dual‑fluid" emphasises the physical architecture-the conductive mist (annulus) and the neutral/ionised gas (inner tube)-while recognising that the governing dynamics also include electromagnetic and plasma interactions:

1. **Dual‑fluid:** The conductive mist and the ionised gas interact electrostatically and magnetically but do not mix. This non‑local coupling acts as an additional nonlinear term in the node's dynamics.
2. **Dual‑state:** The plasma can exist in distinct regimes-glow discharge, arc, or non‑conducting-with sharp I‑V transitions [21,25]. The intended computing regime is the glow discharge; arc discharge exists as an available physical state but is not used for computation. Similarly, the magnetic field can bifurcate the flow into laminar or turbulent states. These discrete transitions naturally implement nonlinear thresholding and provide short‑term memory via hysteresis [26], analogous to a transistor in the fluid domain.

The full state space is thus a continuous manifold with embedded bifurcation surfaces, a feature that may be exploited for nonlinear computation and memory.

---

## 3. Network Architectures

### 3.1 Series Connection: Convective Chains

Connecting the inner tubes of two nodes in series (output of Node 1 → input of Node 2 via a calibrated pneumatic conductance) creates a **convective chain**. The gas exiting Node 1 carries the thermal, chemical, and ionisation history of the first discharge. Node 2 imposes a new magnetic field and plasma condition, acting as a nonlinear transfer function \(\mathcal{F}_i\). A chain of \(N\) nodes implements the compositional map

\[
\mathbf{x}_N^{\text{out}} = \mathcal{F}_N \circ \mathcal{F}_{N-1} \circ \cdots \circ \mathcal{F}_1 (\mathbf{x}_{\text{inlet}}),
\]

where each \(\mathcal{F}_i\) is parametrised by local rotor speed \(\omega_i\) and magnetic field \(\mathbf{B}_i\). This architecture is analogous to a deep feed‑forward network [27], with physical fluid‑plasma layers, and may be suitable for simulating Lagrangian transport or one‑dimensional advection‑reaction problems.

### 3.2 Parallel Nonlinear Dynamical Network

An \(M \times N\) array of CPB heads, each connected to neighbours via pneumatic conduits of conductance \(C_{ij}\), forms a **spatially discrete dynamical network** [28]. The state of node \(i\) evolves according to the general coupled nonlinear dynamical system:

\[
\dot{\mathbf{x}}_i = \mathbf{F}(\mathbf{x}_i) + \sum_{j \in \text{neighbors}} \mathbf{G}_{ij}(\mathbf{x}_i, \mathbf{x}_j) + \mathbf{u}_i,
\tag{2}
\]

where the local dynamics operator decomposes into coupled physical sub‑systems:

| Operator | Physics |
|----------|---------|
| \(\mathbf{F}_f\) | Compressible fluid transport (Navier‑Stokes) |
| \(\mathbf{F}_p\) | Plasma discharge dynamics (ionisation, recombination, sheath) |
| \(\mathbf{F}_m\) | Magnetic field evolution (Maxwell, coil response) |
| \(\mathbf{F}_t\) | Thermal evolution (conduction, radiation, plasma heating) |

such that \(\mathbf{F} = \mathbf{F}_f + \mathbf{F}_p + \mathbf{F}_m + \mathbf{F}_t\). The inter‑node coupling term similarly decomposes as

\[
\mathbf{G}_{ij} = \mathbf{G}_{ij}^{(f)} + \mathbf{G}_{ij}^{(p)} + \mathbf{G}_{ij}^{(m)} + \mathbf{G}_{ij}^{(t)},
\]

where the dominant contribution is the fluid coupling \(\mathbf{G}_{ij}^{(f)}\)-a mass flow proportional to the pressure difference \(p_j - p_i\) with nonlinear corrections for compressibility and viscous losses [19]. A critical open question is the **relative strength** of fluid, magnetic, and electrical coupling between nodes. In the intended operating regime (millimetre‑scale tubes, ~0.1 T fields, 30-80 mbar), preliminary estimates suggest fluid coupling dominates by at least an order of magnitude. This will be measured experimentally in DC‑5 and DC‑6.

The external control input \(\mathbf{u}_i\) includes the high‑voltage electrode potential \(V_{\text{HV}}\), rotor speed modulation, and mist concentration. The network operates in a regime where acoustic transit times dominate over electromagnetic propagation (EM propagation is effectively instantaneous at device dimensions), justifying the neglect of retardation effects.

By choosing the conductance matrix \(C_{ij}\) to match a desired computational stencil [29], the network may be configured to **approximate** the spatial derivatives appearing in a target transport‑governed PDE. This is an approximation; the network does not discretise the PDE in the traditional sense, but evolves according to a related, physically instantiated set of equations. The degree to which the network's steady states and transients match those of the target problem is an experimental question.

### 3.3 Reservoir Computing Formulation

For the primary reservoir computing framing, we consider the network in discrete‑time form (sampled at the FPGA clock rate). Let the state of the reservoir at time step \(k\) be the vector of all observable plasma currents:

\[
\mathbf{r}_k = [I_1(k\Delta t),\; I_2(k\Delta t),\; \ldots,\; I_N(k\Delta t)]^T.
\]

The reservoir dynamics are given by

\[
\mathbf{r}_{k+1} = \mathbf{f}(\mathbf{r}_k,\; \mathbf{u}_k),
\tag{3}
\]

where \(\mathbf{f}\) is the unknown, fixed, nonlinear mapping implemented by the physical network, and \(\mathbf{u}_k\) is the external input (e.g., modulated mist pressure, B‑field, or electrode voltage). The reservoir output is a linear combination of the reservoir states:

\[
y_k = \mathbf{W}_{\text{out}} \mathbf{r}_k,
\tag{4}
\]

where \(\mathbf{W}_{\text{out}}\) is a matrix of trainable weights. Training consists of finding \(\mathbf{W}_{\text{out}}\) by ridge regression on a set of target output sequences, without modifying \(\mathbf{f}\). Whether the CPB network satisfies the **echo state property**-that \(\mathbf{r}_k\) asymptotically depends only on the input history and not on initial conditions-is an experimental question (Stage DC‑4). Testing this requires driving the network with a long input sequence, resetting to different initial conditions, and verifying state convergence. For a fluid system, "resetting" means re‑establishing a known pressure field-a process that may take seconds but is acceptable for offline training.

This formulation aligns with the standard reservoir computing framework [12,14] and forms the basis for the benchmark experiments in Section 10. The analog PDE solver and transport emulator modes become accessible if the steady‑state mapping \(\mathbf{r}_{\text{ss}} = \mathbf{f}_{\text{ss}}(\mathbf{u})\) can be calibrated to match a desired PDE solution (Hypothesis H1, Appendix F).

---

## 4. Computational Encoding

A physical computer requires a well‑defined pipeline: **encoding** (how data enter the system), **evolution** (how the system processes them), and **decoding** (how results are extracted). This section defines that pipeline for the CPB network in its reservoir computing framing.

### 4.1 Encoding: From Problem to Physical Input

The mapping from an engineering problem to hardware parameters is itself a significant inverse problem. We propose a systematic methodology to be developed in parallel with the experimental programme:

1. **Dimensional analysis:** Extract the relevant dimensionless groups (Re, Pe, Ha, Kn) for the target problem.
2. **Scaling laws:** Relate these groups to hardware parameters through calibration experiments. For example, the rotor speed \(\omega\) controls the entrainment pressure and thus the effective Re.
3. **Calibration:** For each new problem class, a small set of reference digital CFD solutions is used to determine the mapping from hardware parameters to flow state.
4. **Validation:** The calibrated mapping is validated against held‑out CFD cases.

The specific physical inputs are:

- **Reynolds number / flow rate:** Controlled by the mist rotor speed (which sets the entrainment pressure and thus the gas flow rate in the inner tubes) or by the inlet manifold pressure.
- **Boundary geometry:** Encoded by the spatial pattern of rotor speeds, B‑field strengths, and electrode voltages across the array; nodes at "walls" can have their plasma quenched or their mist flow set to a stagnation condition.
- **Viscosity / diffusion:** Encoded by the choice of gas species (air, H₂, He) and the inter‑tube conductance.
- **Body forces:** The time‑varying magnetic field provides a tunable Lorentz force on the plasma, equivalent to a programmable external force field in the Navier‑Stokes equations [23].

### 4.2 Evolution: Physical Dynamics

Once the inputs are set, the network evolves according to its intrinsic physics. The characteristic evolution time scale is expected to be on the order of milliseconds, based on acoustic transit times in millimetre‑scale tubes (for a 5 mm tube length, the acoustic transit time \(L/c \approx 17\;\mu\text{s}\); settling to steady state typically requires multiple transits). Steady‑state solutions may therefore be reachable in tens of milliseconds, and time‑dependent phenomena up to a few kHz can potentially be captured directly.

### 4.3 Decoding: From Physical Output to Numerical Result

The **decoder** maps the observation vector \(\mathbf{y}_i\) (Eq. 1) to the desired engineering quantity \(\hat{z}\):

\[
\hat{z}(t) = \mathcal{D}(\mathbf{y}_1(t), \mathbf{y}_2(t), \ldots, \mathbf{y}_N(t)),
\]

where \(\mathcal{D}\) is a pre‑calibrated model-typically a linear regression (ridge regression for reservoir readout) or a small neural network trained on a set of known reference flows [24]. The primary readout is the vector of plasma currents \(I_i(t)\), sampled at the FPGA clock rate (up to ~1 MHz per channel). Secondary readouts include pressure at selected nodes and optical emission spectroscopy for temperature and chemical composition.

---

## 5. Why Plasma? And Why Not Something Simpler?

This section addresses the central question: **what computational capability does the plasma add that cannot be obtained from simpler fluidic or electrical systems?**

### 5.1 What the Plasma Contributes

**Continuous nonlinear readout.** The plasma current provides a sensitive, real‑time, galvanically isolated measurement of the integrated gas state. Unlike a pressure transducer, which measures a single scalar at a point, the plasma current integrates over the entire discharge volume, naturally performing a spatial average weighted by the electron density distribution. This is a form of **physical feature extraction**-the measurement itself encodes information about the gas state.

**Tunable operating point.** The discharge voltage and magnetic field can shift the operating point between different regimes of the I‑V characteristic, effectively changing the nonlinear transfer function of the node without mechanical modifications.

**Intrinsic thresholding.** The glow‑to‑arc transition provides a natural binary threshold, useful for decision‑making or state storage. (Arc operation is avoided during normal computation but the threshold itself is a useful feature.)

**Multiple coupled physical domains.** A CPB node simultaneously involves compressible fluid dynamics, electromagnetism, plasma kinetics, and thermal transport. The cross‑coupling between these domains creates a high‑dimensional state space that would be expensive to emulate digitally.

**Inductive bias for transport problems.** Because the computing substrate is itself a fluid, it inherently obeys conservation laws and transport phenomena. This inductive bias may enable learning flow‑related tasks from far fewer training examples than a general‑purpose neural network would require.

### 5.2 What the Plasma Does NOT Contribute

**The plasma does not provide a fundamentally new form of computation.** It provides a specific, useful set of nonlinearities-nonlinear readout, tunable gain, thresholding-that are combined with the fluid dynamics of the gas. The computational value lies in the **combination** of fluid transport and plasma sensing, not in either alone.

**The plasma is not a "quantum" or "exotic" computer.** All dynamics are classical and governed by well‑established fluid and plasma equations. The advantage, if any, is in the physical instantiation of these equations, not in accessing new physics.

### 5.3 Comparison with Alternatives

A detailed comparison with other analog computing substrates is provided in Appendix H. In summary:

- **Hydraulic analogs:** The CPB adds reconfigurability through magnetic control and electronic readout, but shares their challenges (drift, noise, manufacturing complexity).
- **Memristor crossbars:** The CPB cannot compete on speed, precision, or scalability for tasks that map naturally to matrix‑vector multiplication. IBM's Analog AI chip achieves 12.4 TOPS/W with electronic readout. The CPB's potential niche is problems where the fluid dynamics itself provides a useful inductive bias.
- **Photonic reservoirs:** The CPB operates at kHz rather than GHz bandwidths and cannot match the demonstrated NRMSE <0.01 on Mackey‑Glass. It must justify its existence through unique capabilities (e.g., native fluid simulation) rather than raw speed.

The honest assessment is that the CPB system occupies a narrow niche: **continuous‑time, reconfigurable simulation of transport problems where the physical dynamics provide an inductive bias that reduces training data requirements.** Whether this niche is large enough to justify the engineering complexity is an open question that the experimental programme is designed to answer.

---

## 6. Physical Evaluation Latency, Timescales, and Energy

### 6.1 Relaxation as Computation

The core computational principle of the CPB network differs fundamentally from digital iteration. Digital CFD repeatedly solves linearised systems at each time step or nonlinear iteration. In contrast, the CPB network physically relaxes toward a configuration satisfying the conservation laws. The relaxation process-driven by viscous dissipation, thermal conduction, and ohmic losses-**is** the computation. The steady state of the physical array directly encodes the solution to the boundary‑value problem posed by the control inputs.

### 6.2 Evaluation Latency

The wall‑clock latency to reach steady state is determined by the acoustic transit time across the array. For an array of length \(L\) in the flow direction, the latency scales approximately as \(t_{\text{settle}} \sim \alpha L / c\), where \(c\) is the speed of sound (~340 m/s in air at STP) and \(\alpha\) is an empirical settling factor (expected \(\alpha \sim 5\text{-}20\) for fluid systems). The hardware cost scales with the number of nodes (area).

An important open question is how this latency varies with the dynamical regime. Turbulent, oscillatory, or metastable states may require longer settling times than laminar ones, and characterising this variation is part of the experimental programme. The key distinction from digital CFD is that the relaxation time is governed by the hardware dynamics rather than by digital algorithmic complexity-the physical system does not execute floating‑point operations per grid cell. For problems where many evaluations are needed (optimisation, Monte Carlo), the network's total time‑to‑solution may grow more slowly than the digital equivalent, provided that the physical array can be manufactured at the required scale. Meaningful comparison metrics are wall‑clock time, memory bandwidth, parallel efficiency, energy per evaluation, and control latency-all experimentally measurable.

### 6.3 Energy Budget

A realistic per‑node power budget is:

| Component | Power (W) | Notes |
|-----------|-----------|-------|
| Glow discharge | 5-20 | 300-500 V, 10-50 mA |
| Rotor levitation and drive | 15-40 | AMB bias + drive; scales with rotor size |
| Stator coils (B‑field) | 5-15 | Depends on field strength and duty cycle |
| FPGA and data acquisition | 5-10 | Per‑node estimate |
| **Total per node** | **30-85** | |

For a 3×3 array, the total power is **270-765 W**, not the <100 W previously projected. This is a significant revision and places the CPB network in the same power class as a small GPU cluster. The energy‑per‑evaluation advantage, if any, must come from reduced total time‑to‑solution for repetitive tasks, not from lower instantaneous power. This will be quantified in DC‑8.

### 6.4 Timescale Coupling Analysis

A central concern is the coupling of dynamics spanning many orders of magnitude in timescale:

| Process | Timescale |
|---------|-----------|
| Electron plasma oscillations | ~10⁻¹⁰ s |
| Electron‑neutral collisions | ~10⁻¹² s |
| Ion acoustic transit | ~10⁻⁷ s |
| Sheath formation | ~10⁻⁶ s |
| Gas acoustic transit | ~10⁻⁵ s |
| Pressure equilibration | ~10⁻³ s |
| Thermal diffusion | ~10⁻²-1 s |

The key insight is that the **fast plasma dynamics are effectively averaged at the computational timescale**. The plasma current \(I(t)\) that is measured at millisecond intervals is the quasi‑steady response of the discharge to the slowly varying gas conditions. The plasma's "rich nonlinearity" is not directly accessible at kHz rates; rather, it manifests as a **nonlinear, low‑pass‑filtered function of the gas state**. The effective transfer function is \(I(t) = \mathcal{N}(\bar{p}(t), \bar{T}(t), \bar{\rho}(t), \ldots)\), where the overbars denote millisecond‑scale averages and \(\mathcal{N}\) is the nonlinear I‑V characteristic of the discharge.

This has an important consequence: the plasma acts as a **nonlinear readout with intrinsic temporal averaging**, not as a source of high‑frequency computational richness. The computational richness, if any, comes from the spatial coupling of the gas dynamics across the array.

### 6.5 Passive Dissipation and Future Port‑Hamiltonian Formulation

The Navier‑Stokes equations are dissipative (energy decreases in the absence of forcing), and the plasma adds energy in a controlled manner. Because the network is passive and dissipative, a future theoretical objective is to cast its dynamics in a port‑Hamiltonian form, which would provide a rigorous Lyapunov stability analysis and connect the system to established energy‑based control theory. This derivation is not required for the experimental validation programme and remains future work.

---

## 7. Observability, System Identification, and Error Model

### 7.1 Observability of the Internal State

The observation equation \(\mathbf{y} = \mathbf{H}(\mathbf{x}) + \boldsymbol{\eta}\) (Eq. 1) maps the infinite‑dimensional internal state to a finite‑dimensional measurement vector. A central theoretical question is: **how much information about \(\mathbf{x}\) is recoverable from \(\mathbf{y}\)?** This is the problem of observability [24]. For the CPB node, the plasma current \(I\) provides a single spatially integrated measurement-the observability Gramian will be singular, meaning the full internal state cannot be reconstructed from plasma current alone. Adding pressure sensors at multiple axial locations increases the observable subspace. For reservoir computing, this may be sufficient-the readout layer only needs a high‑dimensional projection of the state, not the full state itself. For analog PDE solving, the limited observability places a fundamental bound on the spatial resolution of the computed solution.

A practical approach is to treat the system as a nonlinear observer problem: use the known dynamics (Appendix A) and the output measurements to estimate the full state. This is closely related to state estimation, Kalman filtering, and reduced‑order modelling.

### 7.2 Calibration as System Identification

The three‑step calibration procedure (measurement → correction → uncertainty propagation) is a form of **system identification**: determining an input‑output map from data. For the reservoir computing mode, the only identification required is the linear readout layer \(\mathbf{W}_{\text{out}}\). For the analog PDE solver mode, a more comprehensive identification of the steady‑state mapping \(\mathbf{r}_{\text{ss}} = \mathbf{f}_{\text{ss}}(\mathbf{u})\) is needed. Techniques such as parameter estimation, surrogate identification using polynomial chaos or Gaussian processes, and Bayesian calibration can be applied [25]. The choice of method will depend on the required accuracy and the complexity of the mapping, to be determined experimentally.

### 7.3 Error Model

We propose a simple error model to replace the arbitrary "10% RMS" criterion with a theoretically motivated framework. Let \(\mathbf{u}\) be the control input, \(\mathbf{y}\) the measurement, and \(\hat{z}\) the decoded result. The total error decomposes as:

\[
\varepsilon_{\text{total}} = \varepsilon_{\text{encoding}} + \varepsilon_{\text{evolution}} + \varepsilon_{\text{measurement}} + \varepsilon_{\text{decoding}},
\]

where:
- \(\varepsilon_{\text{encoding}}\) is the error in mapping the engineering problem to hardware parameters (to be characterised in DC‑1).
- \(\varepsilon_{\text{evolution}}\) is the physical noise and drift during network evolution (DC‑3).
- \(\varepsilon_{\text{measurement}}\) is the sensor noise (DC‑3).
- \(\varepsilon_{\text{decoding}}\) is the regression or neural network error (DC‑7).

The hypothesis H1 (Section 8.1) is refined to: **For a calibrated network, \(\varepsilon_{\text{total}} < 10\%\) RMS for linear transport PDEs, with the error budget dominated by \(\varepsilon_{\text{encoding}}\) for low node counts and \(\varepsilon_{\text{measurement}}\) for high node counts.**

---

## 8. Problem Classes and Application Mapping

We hypothesise that the CPB network can serve as a physical reservoir computer for the following problem classes.

### 8.1 Forward Problems (Direct Simulation)

**Configuration:** Parallel array with fixed boundary conditions.  
**Hypothesis (H1):** For a calibrated network, the steady‑state pressure and current distribution approximates the solution of the corresponding continuum transport problem, with total error \(\varepsilon_{\text{total}} < 10\%\) RMS relative to a reference CFD solution.  
**Validation:** Compare against known analytical or high‑fidelity CFD solutions for Poiseuille flow, Couette flow, and backward‑facing step [31].  
**Open questions:** Quantification of the error due to finite node count, plasma heating, and wall effects.

### 8.2 Inverse Problems (Optimisation)

**Configuration:** Feedback loop that adjusts rotor speeds, electrode voltages, and B‑fields to minimise a cost function defined on the plasma current distribution.  
**Hypothesis (H3):** Gradient‑free optimisers (e.g., evolutionary algorithms, Nelder‑Mead, Bayesian optimisation) can converge to solutions that match target flow patterns [32].  
**Validation:** Reproduce a prescribed pressure or velocity profile in a simple geometry.

### 8.3 Surrogate Modelling

**Configuration:** Reservoir computer (mixed series‑parallel) trained on a set of reference CFD data.  
**Hypothesis (H2):** A linear readout of the reservoir state can interpolate or extrapolate flow solutions across a range of Reynolds numbers or geometric parameters [33].  
**Validation:** Train on low‑Reynolds‑number data, test at a higher Reynolds number; compare against digital CFD.

### 8.4 Constraint Satisfaction and Network Flow

Many transport problems can be cast as constrained optimisation over a graph: network flow, diffusion optimisation, least‑energy routing, and graph Laplacian problems. The dual‑fluid network, with its configurable inter‑node conductances and plasma‑based state readout, naturally maps onto such formulations. Each node represents a vertex, inter‑tube flows represent edges, and the plasma current provides a local measure of "satisfaction" of the constraint (e.g., pressure matching a target). The network relaxes physically to a minimum‑energy configuration, potentially solving certain classes of constrained flow problems without iterative digital computation.

### 8.5 Hardware Acceleration for Repetitive Tasks

Many CFD workflows involve running thousands of similar simulations (e.g., design of experiments, Monte Carlo uncertainty quantification). A dual‑fluid array could serve as a fast, potentially low‑energy surrogate after initial calibration: the expensive digital simulation is run once to calibrate the network, after which the network produces approximate solutions with low evaluation latency per case.

---

## 9. Precision, Noise, and Calibration

### 9.1 Noise Sources

The analogue fluid computer has fundamentally different error sources from a digital simulation:

- **Thermal noise:** Brownian motion imposes a fundamental pressure noise floor of order \(\sqrt{k_B T / V}\), where \(V\) is the sensing volume [34]. For a 0.1 mm³ volume, this is negligible (~10⁻⁶ mbar RMS). This is the thermodynamic floor; practical sensors are significantly noisier.
- **Sensor noise:** The pot‑core current sensor is projected to have >80 dB SNR, limited by amplifier noise; this estimate is a design target requiring experimental confirmation. Pressure transducers such as the Kulite XCQ‑093 series achieve approximately 16 effective bits (ENOB) at kHz bandwidths per manufacturer specifications [35], not the 20 bits claimed in earlier revisions.
- **Manufacturing variability:** Tube diameter, annulus gap, and magnet strength variations between nodes introduce fixed pattern noise. This can be characterised in a calibration phase and compensated in software.
- **Long‑term drift:** Mist deposition on the rotor causes slow unbalance. Active heating, hydrophobic coatings, and scheduled cleaning cycles are designed to maintain operation within specified bounds [18]. The calibration interval required to maintain specified accuracy is unknown and will be determined experimentally in DC‑3.

### 9.2 System Identification and Calibration

We propose a three‑step calibration procedure based on standard metrology practices [36]:

1. **Measurement:** Each node's response to known inputs (reference pressures, known B‑fields) is recorded.
2. **Correction:** A linear correction matrix (or low‑order polynomial) is computed to map raw sensor outputs to true physical quantities, minimising the residual variance across the array.
3. **Uncertainty propagation:** The residual calibration uncertainty is propagated through the network equations to estimate the uncertainty on computed quantities (e.g., drag).

This calibration can be performed periodically. For the reservoir computing mode, this step is supplemented by training the linear readout layer \(\mathbf{W}_{\text{out}}\) via ridge regression. For the analog PDE solver mode, a more comprehensive system identification procedure (Section 7.2) is applied to characterise the steady‑state mapping.

### 9.3 Effective Precision

The effective numerical precision of the dual‑fluid computer is **not** the floating‑point precision of a digital simulation; it is the signal‑to‑noise ratio of the physical measurement. For steady‑state pressure measurements, this can approach approximately 14-16 effective bits, depending on bandwidth and averaging (revised downward from earlier estimates of 15-17 bits to reflect manufacturer datasheet specifications). For transient measurements, the effective bandwidth trades off against resolution. The key difference from digital CFD is **continuous temporal evolution** with **finite spatial sampling**, which eliminates numerical time‑integration error associated with discrete time stepping, while introducing physical measurement and modelling uncertainties instead [37].

We explicitly withdraw any comparison to "64‑bit double precision CFD." The proper comparators are:
- Experimental wind‑tunnel measurements (similar noise floor, but real‑time and reconfigurable).
- Physical analogue computers (similar physics, but with modern magnetic and plasma control).
- Digital surrogate models (trained on CFD, deployed for rapid prediction).

---

## 10. Benchmark Problems

The following established benchmarks from dynamical systems and reservoir computing are proposed to objectively evaluate the network's computational capability:

| Benchmark | What It Tests | Reference |
|-----------|---------------|-----------|
| **Poiseuille and Couette flow** | Steady‑state pressure and velocity profile recovery in simple geometries. | [19] |
| **Diffusion and heat equations** | Relaxation to equilibrium; spatial coupling fidelity. | [40] |
| **Burgers' equation** | One‑dimensional shock formation; nonlinear advection. | [41] |
| **Navier‑Stokes cylinder wake** | Classical unsteady separated flow; vortex shedding frequency and drag coefficient. | [1] |
| **Mackey‑Glass chaotic time‑series prediction** | Standard reservoir computing benchmark; fading memory. | [42] |
| **NARMA10** | Nonlinear autoregressive moving average; short‑term memory and nonlinearity. | [43] |
| **Lorenz attractor** | Three‑dimensional chaotic system; attractor reconstruction. | [3] |
| **Kuramoto model** | Synchronisation of coupled oscillators; emergent collective dynamics. | [44] |
| **Memory capacity (MC)** | Linear memory capacity of the reservoir. | [45] |
| **Parity task** | Nonlinear mapping requiring high‑order temporal dependencies. | [14] |
| **Delay task** | Long‑range temporal memory. | [12] |

Each benchmark tests a different aspect of the system: steady‑state approximation, transient prediction, chaotic dynamics, emergent synchronisation, and reservoir memory properties.

---

## 11. Experimental Validation Path

The following eleven stages progressively de‑risk the concept, building from bare‑discharge characterisation to full APM integration. Each stage includes quantitative success criteria, estimated duration, equipment required, and risk level. **Explicit go/no‑go decision points are included after DC‑3 and DC‑7.**

| Stage | Objective | Key Milestone | Success Criteria | Duration | Risk | Key Equipment |
|-------|-----------|---------------|------------------|----------|------|---------------|
| **DC‑0** | Bare plasma discharge characterisation | Measure single‑node plasma I‑V curve in static gas, without mist, rotor drive, or magnetic modulation. Map full I‑V curve including hysteresis. | I‑V repeatability <5% over 10 cycles; glow‑to‑arc transition voltage identified; hysteresis loop characterised. | 2 weeks | Low | Oscilloscope, HV supply, vacuum system |
| **DC‑1** | Single‑node transfer function | Map plasma current vs. rotor speed, B‑field, and electrode voltage; characterise static nonlinearity; determine transfer function from gas flow perturbations to plasma current. | Response surface measured at ≥100 operating points; fit R² > 0.95; transfer function characterised. | 4 weeks | Medium | IMLT head, FPGA, calibrated sensors |
| **DC‑2** | Frequency response | Measure small‑signal response to modulated inputs; determine effective low‑pass cutoff of the plasma readout. | −3 dB bandwidth >1 kHz; phase lag <45° at 500 Hz. | 3 weeks | Medium | Signal generator, dynamic signal analyser |
| **DC‑3** | Noise characterisation | Quantify all noise sources (not just thermal): sensor noise floor, drift over hours, repeatability across thermal cycles. | RMS noise <1% of full scale; drift <2% over 8 h; repeatability >99%. **GO/NO‑GO: If noise >5% FS or R² < 0.9, project stops.** | 3 weeks | Medium | Environmental chamber, long‑term data logger |
| **DC‑4** | Memory capacity and echo state | Test fading memory via linear memory capacity metric; test echo state property by resetting to different initial conditions. | MC > 5 for a single node; echo state property verified (state convergence within 5% after reset). | 2 weeks | Low | Arbitrary waveform generator, data acquisition |
| **DC‑5** | Two‑node pneumatic coupling | Connect two tubes via a calibrated leak; verify mutual pressure and plasma modulation; quantify coupling strength relative to local dynamics. | Cross‑correlation peak >0.7 between node currents under modulation; coupling strength quantified. | 4 weeks | Medium | Two IMLT heads, connecting manifold, sensors |
| **DC‑6** | Coupled oscillators | Demonstrate synchronisation or phase locking between two nodes. | Phase difference standard deviation <5° for ≥100 oscillation cycles. | 4 weeks | Medium | Dual‑node setup, phase measurement |
| **DC‑7** | Reservoir benchmark (4‑node chain) | Use a 4‑node series chain as a reservoir; train linear readout (ridge regression) to predict Mackey‑Glass. | NRMSE <0.1 for 84‑step‑ahead prediction. **GO/NO‑GO: If NRMSE >0.2, reservoir computing hypothesis is rejected.** | 6 weeks | High | 4‑node array, real‑time FPGA readout, training software |
| **DC‑8** | Small parallel array (3×3) | Build a grid with individually controllable rotors; measure steady‑state pressure field; measure actual energy consumption. | Pressure pattern matches CFD within 10% RMS error; energy budget measured and compared to projections. **If deviation >20%, PDE approximation hypothesis is rejected.** | 8 weeks | High | 9‑node array, manifold, calibration system |
| **DC‑9** | Closed‑loop optimisation | Implement gradient‑free optimisation of rotor speeds, voltages, and B‑fields to match a target pressure profile. | Convergence to target within 5% RMS error in <50 iterations. | 8 weeks | High | 9‑node array, optimisation controller |
| **DC‑10** | APM‑relevant demonstration | Introduce a reactive gas; use optical emission for feedback; control nanoparticle deposition. | Deposition thickness uniformity within ±10% over a 1 cm² substrate. | 12 weeks | Very High | APM reactor, optical spectrometer, deposition monitor |

These stages leverage the modular nature of the CPB platform and can be pursued in parallel with the Core Plasma Jet and HV Beam development. **The early falsification criteria (after DC‑3 and DC‑7) protect against pursuing an unviable architecture.**

---

## 12. Atomically Precise Manufacturing

### 12.1 Continuum Transport Co‑Processor

Atomically precise manufacturing (APM) involves the transport of molecular precursors through gas or liquid phases to a reaction site [46]. The continuum part of this process-diffusion, convection, mixing-is computationally expensive to simulate digitally when coupled to molecular‑scale models. The dual‑fluid network is proposed as a **continuum co‑processor**: it handles the macro‑scale transport, while digital or quantum solvers handle the molecular‑scale chemistry. The two communicate through boundary conditions: the network provides concentration and velocity fields at the reactor boundaries; the molecular solver provides reaction rates and species fluxes back to the continuum model. The specific interface between the continuum and molecular models is an area for future work.

### 12.2 Hardware‑in‑the‑Loop Control

In a production environment, a dual‑fluid array could be placed in a closed loop with a real APM reactor. Sensor data from the reactor feed the network, which predicts optimal actuator settings (e.g., flow rates, temperatures) in real time via model‑predictive control [47]. The latency advantage of physical computation could enable control at the millisecond time scale; if validated experimentally, this could significantly improve deposition uniformity and throughput. However, this requires the network to be stable, reliable, and accurate-none of which have been demonstrated.

### 12.3 Self‑Optimising Fluidic Circuits

The long‑term vision is a **self‑programming fluidic computer** that can be reconfigured for different manufacturing tasks. By altering the magnetic fields, electrode voltages, and inter‑node conductances, the same hardware could morph from solving a diffusion problem to a mixing problem. The reservoir computing paradigm allows the system to learn the required dynamics from a small number of training examples, eliminating the need for explicit digital programming of the fluidic network.

---

## 13. Scope, Limitations, and Known Open Questions

### 13.1 Scope

This work does not claim:

- Universal computation;
- Exact Navier‑Stokes solutions;
- Improved accuracy over all CFD methods;
- Replacement of digital simulation.

Instead, it investigates-through a structured theoretical and experimental programme-whether coupled CPB networks can serve as:

- A physical reservoir computer for transport‑related dynamical systems (primary framing);
- Physical analogue computers for selected flow problems (extension);
- Transport emulators approximating target transport‑governed PDEs (extension).

The network is not expected to outperform optimised digital CFD for arbitrary simulations; its potential advantage lies in repeated evaluations of structurally similar transport problems after calibration. All performance claims are hypotheses to be tested against the benchmarks in Section 10.

### 13.2 Known Limitations

1. **Timescale mismatch:** Fast plasma dynamics (ns-µs) are averaged at the computational timescale (ms). The plasma acts as a nonlinear low‑pass filter, not a source of high‑frequency computational richness.
2. **Limited observability:** The plasma current is a single integrated scalar per node. Spatial resolution is fundamentally limited, even with additional pressure sensors.
3. **No stability proof:** A rigorous Lyapunov stability analysis has not been completed. Stability is expected based on energy arguments but is not guaranteed.
4. **Encoding complexity:** Mapping arbitrary engineering problems to hardware parameters is a nontrivial inverse problem requiring per‑problem calibration.
5. **Energy budget:** The per‑node power consumption (30-85 W) is significantly higher than early projections. The economic case depends on amortising calibration cost over many evaluations.
6. **Manufacturing yield:** The production yield for IMLT nodes is unknown and will directly affect scalability and cost.

### 13.3 Key Open Questions

1. **What is the quantitative transfer function from local gas perturbations to global plasma current?** This determines the effective spatial resolution of the readout.
2. **How does the network's memory capacity scale with node count?** Preliminary reservoir theory suggests sub‑linear scaling, but this has not been verified.
3. **What is the manufacturing yield for IMLT nodes?** This affects scalability and cost.
4. **How long can the system operate before recalibration is required?** The calibration interval is unknown.
5. **What is the electrode erosion rate, and how does it affect long‑term stability?** This is a known issue in glow discharge devices.
6. **What is the CFD reference error for validation?** The comparison is to CFD, which has its own errors. The validation framework must account for this.

### 13.4 Falsification Criteria

The project includes explicit go/no‑go criteria:
- **After DC‑3:** If single‑node dynamics lack sufficient nonlinearity (R² < 0.9 for transfer function fit, or MC < 3), or if the noise floor exceeds 5% of full scale, the project stops.
- **After DC‑7:** If the 4‑node reservoir fails to achieve NRMSE <0.2 on Mackey‑Glass, the reservoir computing hypothesis is rejected.
- **After DC‑8:** If the 3×3 array pressure field deviates from CFD by >20%, the PDE approximation hypothesis is rejected.

---

## 14. Challenges and Mitigations

| Challenge | Mitigation Strategy |
|-----------|---------------------|
| **Node‑to‑node variability** | Per‑node calibration with periodic re‑calibration; correction matrices; statistical characterisation of manufacturing tolerances. |
| **Mist deposition on rotors** | Active rotor heating (80-90 °C), hydrophobic DLC coatings, automated dry‑N₂ cleaning cycles [18]. |
| **Long‑term drift** | Vibration‑signature monitoring; soft shut‑down at >10 µm peak‑to‑peak; scheduled maintenance; calibration interval to be determined experimentally in DC‑3. |
| **Inter‑node coupling stability** | Conductance limiting to prevent acoustic instability; planned Lyapunov analysis; experimental characterisation of coupling strength in DC‑5 and DC‑6. |
| **Scalability to large arrays** | Modular head design; shared mist manifold; FPGA‑based distributed control; manufacturing yield to be assessed. |
| **Calibration drift over time** | On‑line recalibration using reference nodes with known inputs; characterisation of drift rate in DC‑3. |
| **Electrode erosion** | Material selection (Pt, LaB₆); conservative current limits; scheduled replacement; erosion rate to be monitored. |
| **Energy consumption** | Realistic budgeting (30-85 W/node); energy‑per‑evaluation metric to be measured in DC‑8; economic case depends on amortisation over many evaluations. |
| **Encoding complexity** | Systematic methodology (dimensional analysis → scaling laws → calibration → validation) to be developed as part of the research programme. |

---

## 15. Conclusion

We have proposed a **theoretical and experimental programme** to investigate whether networks of Coherent Particle Beam devices can function as a physical reservoir computer for transport and flow problems. This is high‑risk, high‑reward research. The integrated magnetic levitation turbine architecture provides a clean, reconfigurable fluid‑plasma node with intrinsic sensing and actuation. By connecting nodes in series and parallel, one obtains a nonlinear dynamical network whose state evolves according to the coupled physics of compressible flow, electromagnetism, and plasma discharges.

The scientific contribution of this paper is not a claim of demonstrated capability, but a **rigorous framework** for testing the dual‑fluid plasma computing hypothesis. We have:

- Defined the node and network state equations, separating field and lumped variables;
- Specified the reservoir computing formulation with explicit state and output equations;
- Defined the computation pipeline (encoding → evolution → decoding with an explicit observation equation);
- Characterised the plasma nonlinearity being exploited, including its limitations as a low‑pass‑filtered, spatially integrated readout;
- Analysed the timescale coupling problem, showing that fast plasma dynamics are averaged at the computational timescale;
- Developed a formal error model decomposing total error into encoding, evolution, measurement, and decoding components;
- Revised the energy budget to realistic levels (30-85 W/node);
- Proposed a staged experimental validation plan with clear benchmarks, quantitative success criteria, and explicit falsification points at DC‑3, DC‑7, and DC‑8.

If the hypotheses are confirmed, the dual‑fluid computer could serve as a high‑speed, low‑latency co‑processor for continuum transport, with particular utility in the design and control of atomically precise manufacturing processes. If the hypotheses are falsified at the early stages, the programme will have produced valuable experimental data on the dynamics of coupled glow discharge systems. Either outcome advances the scientific understanding of physical computation.

---

## Appendix A: Governing Equations

The node dynamics are governed by the following set of coupled partial and ordinary differential equations, assuming a calorically perfect gas, low Mach number, quasi‑neutral plasma, low magnetic Reynolds number (\(\mathrm{Rm} \ll 1\), so induced magnetic fields are neglected relative to externally applied fields), and negligible Hall effect (for expected \(B \sim 0.1\) T, electron gyrofrequency \(\sim 1.76 \times 10^{10}\) rad/s, collision frequency \(\sim 10^{12}\) s⁻¹, giving Hall parameter \(\beta_H < 0.02\)). The current density \(\mathbf{J}\) is given by a reduced Ohm's law:

\[
\mathbf{J} = \sigma_p (\mathbf{E} + \mathbf{v} \times \mathbf{B}),
\tag{A0}
\]

where \(\sigma_p\) is the plasma conductivity.

**Continuity:**  
\[
\frac{\partial \rho}{\partial t} + \nabla \cdot (\rho \mathbf{v}) = 0
\tag{A1}
\]

**Momentum:**  
\[
\rho \left( \frac{\partial \mathbf{v}}{\partial t} + \mathbf{v} \cdot \nabla \mathbf{v} \right) = -\nabla p + \nabla \cdot \boldsymbol{\tau} + \mathbf{J} \times \mathbf{B}
\tag{A2}
\]

**Energy (gas):**  
\[
\rho c_p \left( \frac{\partial T}{\partial t} + \mathbf{v} \cdot \nabla T \right) = \nabla \cdot (k \nabla T) + \Phi_{\text{visc}} + \eta_{\text{ohm}} |\mathbf{J}|^2
\tag{A3}
\]

**Maxwell:**  
\[
\nabla \times \mathbf{B} = \mu_0 \mathbf{J}, \quad \nabla \cdot \mathbf{B} = 0, \quad \mathbf{E} = -\nabla \phi
\tag{A4}
\]
\[
\nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t} \quad \text{(retained for completeness; neglected in the quasistatic limit)}
\tag{A4b}
\]

**Plasma (reduced fluid model):**  
\[
\frac{\partial n_e}{\partial t} + \nabla \cdot (n_e \mathbf{v}_e) = \nu_{\text{ion}} n_e - \alpha_{\text{rec}} n_e n_i
\tag{A5}
\]
\[
m_e n_e \frac{d\mathbf{v}_e}{dt} = -e n_e (\mathbf{E} + \mathbf{v}_e \times \mathbf{B}) - \nabla p_e - m_e n_e \nu_{en} (\mathbf{v}_e - \mathbf{v}_n)
\tag{A6}
\]

**Observation:**  
\[
\mathbf{y} = [I, p_{\text{sensor}}, I_{\text{opt}}(\lambda)]^T = \mathbf{H}(\mathbf{x}) + \boldsymbol{\eta}
\tag{A7}
\]

**Control (fast):**  
\[
\mathbf{u} = [V_{\text{HV}}(t),\; \omega(t),\; \mathbf{B}_{\text{coil}}(t),\; \dot{m}_{\text{mist}}]^T
\tag{A8}
\]

**Reservoir state (discrete‑time):**  
\[
\mathbf{r}_k = [I_1(k\Delta t),\; \ldots,\; I_N(k\Delta t)]^T
\tag{A9}
\]

The total plasma current is \(I = \int_A \mathbf{J} \cdot d\mathbf{A}\) where \(A\) is the electrode area.

---

## Appendix B: Assumptions and Simplifications

The mathematical model invokes the following explicit assumptions:

1. **Continuum hypothesis:** Knudsen number \(Kn < 0.01\) at operating pressures, so the Navier‑Stokes equations are valid.
2. **Low Mach number:** Flow velocities are subsonic; compressibility effects are retained but shock waves are not expected.
3. **Quasi‑neutrality:** \(n_e \approx n_i\); the Debye length is much smaller than the tube diameter. Note: quasi‑neutrality breaks down in the sheath, which is critical for the I‑V characteristic. The reduced fluid model captures sheath effects parametrically through the boundary conditions on \(\phi\).
4. **Weakly ionised plasma:** Ionisation fraction < 10⁻⁴; neutral gas dynamics dominate momentum transport. The intended operating regime is the glow discharge; arc discharges, though physically possible, are not used for computation.
5. **Reduced plasma chemistry:** A single‑step ionisation‑recombination model is used; multi‑species chemistry is deferred to later stages.
6. **Negligible Hall and ion‑slip effects:** Hall parameter \(\beta_H < 0.02\) for \(B \sim 0.1\) T and expected collision frequency >10¹² s⁻¹. For higher B‑fields or lower pressures, the Hall effect may become non‑negligible and would require a generalised Ohm's law.
7. **Low magnetic Reynolds number:** \(\mathrm{Rm} \ll 1\); induced magnetic fields are neglected relative to externally applied fields. Note: this is valid for gas velocities but the electron contribution to Rm may not be negligible in all regimes.
8. **Rigid geometry:** Tube walls are stationary and isothermal (controlled by external cooling).
9. **Known inter‑node conductance:** \(C_{ij}\) is measured in a separate calibration step and assumed constant during operation.
10. **Isothermal electrodes:** Emitter and collector temperatures are regulated.
11. **Mist as a single‑phase effective fluid:** The conductive aerosol is treated as a homogeneous medium with effective conductivity and viscosity. With droplet diameters ~2-5 µm and Stokes numbers <0.1 in the relevant flow, droplets closely follow the gas streamlines, justifying the continuum approximation.
12. **Timescale separation:** Fast plasma dynamics (τ < 1 µs) are treated in the quasi‑steady limit; the plasma responds instantaneously to gas conditions at the millisecond computational timescale. The effective observable is the low‑pass‑filtered plasma response.

---

## Appendix C: Notation Table

| Symbol | Description | Units |
|--------|-------------|-------|
| \(p\) | Gas pressure | Pa or mbar |
| \(T\) | Gas temperature | K |
| \(\rho\) | Gas density | kg m⁻³ |
| \(\mathbf{v}\) | Gas velocity vector | m s⁻¹ |
| \(n_e\) | Electron number density | m⁻³ |
| \(n_i\) | Ion number density | m⁻³ |
| \(\mathbf{v}_e\) | Electron velocity | m s⁻¹ |
| \(\mathbf{v}_n\) | Neutral velocity | m s⁻¹ |
| \(\mathbf{B}\) | Magnetic flux density | T |
| \(\mathbf{E}\) | Electric field | V m⁻¹ |
| \(\mathbf{J}\) | Current density | A m⁻² |
| \(\phi\) | Electrostatic potential | V |
| \(V_{\text{HV}}\) | Electrode potential (control) | V |
| \(I\) | Total plasma current | A |
| \(\omega\) | Rotor angular speed | rad s⁻¹ |
| \(\sigma\) | Effective mist conductivity | S m⁻¹ |
| \(\sigma_p\) | Plasma conductivity | S m⁻¹ |
| \(\nu_{\text{ion}}\) | Ionisation frequency | s⁻¹ |
| \(\alpha_{\text{rec}}\) | Recombination coefficient | m³ s⁻¹ |
| \(\nu_{en}\) | Electron‑neutral collision frequency | s⁻¹ |
| \(C_{ij}\) | Inter‑node pneumatic conductance | m³ s⁻¹ Pa⁻¹ |
| \(\mathbf{r}_k\) | Reservoir state vector at time step \(k\) | various |
| \(\mathbf{W}_{\text{out}}\) | Reservoir readout weight matrix | various |
| \(\mathbf{u}_i\) | External control input to node i | various |
| \(\mathbf{y}_i\) | Observation vector | various |
| \(\boldsymbol{\eta}_i\) | Sensor noise vector | various |
| \(\varepsilon_{\text{total}}\) | Total computational error | various |
| \(\varepsilon_{\text{encoding}}\) | Error from problem‑to‑hardware mapping | various |
| \(\varepsilon_{\text{evolution}}\) | Error from physical noise and drift | various |
| \(\varepsilon_{\text{measurement}}\) | Error from sensor noise | various |
| \(\varepsilon_{\text{decoding}}\) | Error from readout model | various |

---

## Appendix D: Glossary

- **Dual‑fluid computing:** A computational paradigm utilising two physically separated but interacting fluids (here, conductive mist and ionised gas) whose coupled dynamics perform computation. The term emphasises the physical architecture while the governing dynamics also include electromagnetic and plasma interactions.
- **Integrated Magnetic Levitation Turbine (IMLT):** The CPB variant in which a magnetically levitated rotor in the outer annulus drives the conductive mist flow and provides magnetic actuation.
- **Reservoir computing:** A framework where a fixed, high‑dimensional nonlinear dynamical system (the reservoir) transforms an input signal, and only the readout layer is trained.
- **Transport emulation:** Configuring a physical system so that its governing equations approximate a desired transport process.
- **System identification:** The process of determining an input‑output map from experimental data, encompassing both sensor calibration and surrogate model construction.
- **Evaluation latency:** The wall‑clock time required for a physical computing system to produce a result, as distinct from digital algorithmic complexity.
- **Effective number of bits (ENOB):** A measure of a sensor's dynamic range, accounting for noise and distortion, expressed as the equivalent number of perfect digital bits.
- **Input‑to‑state stability (ISS):** A property of a dynamical system ensuring that the state remains bounded for any bounded input.
- **Echo state property:** A condition under which a reservoir's state asymptotically depends only on the driving input, not on initial conditions.

---

## Appendix E: Traceability Matrix

| Section | Claim | Status | Supporting Source |
|---------|-------|--------|-------------------|
| 1.1 | DNS is computationally expensive | Cited | [1], [2] |
| 1.1 | Exponential divergence of chaotic trajectories | Cited | [3] |
| 1.2 | Bush differential analyser | Cited | [5] |
| 1.2 | Shannon's theory | Cited | [6] |
| 1.2 | Fluidic logic history and obsolescence | Cited | [9,10,11]; obsolescence analysis original |
| 1.2 | Reservoir computing framework | Cited | [12,14] |
| 2.2 | Reduced plasma fluid model | Cited | [21,22] |
| 2.2 | Lorentz force coupling | Cited | [23] |
| 2.2 | Observation equation | Cited | [24] |
| 2.3 | Plasma I‑V characteristic and nonlinearity | Original analysis synthesising [21,25] |
| 2.4 | Glow discharge regimes and hysteresis | Cited | [21,25] |
| 3.2 | Coupled nonlinear network form | Original derivation; general form from [28] |
| 3.2 | Inter‑node coupling strength | Original estimate; experimental verification planned |
| 3.3 | Reservoir computing formulation | Original formulation following [12,14] |
| 3.3 | Echo state property testing | Original experimental design |
| 4.1 | Encoding methodology | Original; dimensional analysis and scaling laws to be developed |
| 4.2 | Millisecond time scale estimate | Acoustic scaling derived in‑text |
| 5 | Plasma substrate advantages and limitations | Original analysis synthesising [21-26]; competitive assessment original |
| 6.2 | Evaluation latency analysis | Original; settling factor empirical |
| 6.3 | Energy budget | Original; revised from earlier projections |
| 6.4 | Timescale coupling analysis | Original |
| 6.5 | Port‑Hamiltonian future work | Cited | [38,39]; derivation remains future work |
| 7.1 | Observability analysis | Original synthesis from [24] and control theory |
| 7.2 | System identification | Original; supplemented by [36] |
| 7.3 | Error model | Original |
| 9.1 | Thermal noise limit | Cited | [34] |
| 9.1 | Sensor ENOB (revised) | Manufacturer datasheet [35]; 80 dB SNR is design target |
| 9.2 | Calibration / system identification | Original; supplemented by [36] |
| 10 | Benchmark references | Each cited individually |
| 11 | Go/no‑go decision points | Original |
| 12.1 | APM references | Cited | [46] |
| 13.2 | Known limitations | Original synthesis of all identified issues |
| 13.3 | Key open questions | Original |
| 13.4 | Falsification criteria | Original |
| Appendix B | Timescale separation assumption | Original |
| Appendix H | Substrate comparison | Original analysis; updated with quantitative comparators |

---

## Appendix F: Formal Hypotheses

- **H0 (Null):** The steady‑state pressure distribution in a CPB array is indistinguishable from that of a randomly configured network, i.e., no systematic approximation of transport PDEs occurs.
- **H1 (Forward approximation):** A calibrated parallel CPB array with appropriately chosen inter‑node conductances can approximate the steady‑state solution of a linear transport‑governed PDE with total error \(\varepsilon_{\text{total}} < 10\%\) RMS relative to a reference CFD solution. The error budget is dominated by \(\varepsilon_{\text{encoding}}\) at low node counts and \(\varepsilon_{\text{measurement}}\) at high node counts.
- **H2 (Reservoir computing):** A CPB‑based reservoir computer can achieve an NRMSE <0.1 on the Mackey‑Glass benchmark, comparable to other physical reservoir computers.
- **H3 (Optimisation):** A closed‑loop CPB array using a gradient‑free optimiser can converge to a target pressure profile within 5 % RMS error in fewer than 50 control iterations.

Failure to reject H0 at the 95 % confidence level after DC‑8 will indicate that further investigation of the paradigm is not warranted without major architectural changes. Failure to achieve H2 at DC‑7 (NRMSE <0.2 threshold) will reject the reservoir computing hypothesis. Failure to meet the DC‑3 noise and nonlinearity thresholds will halt the programme before array construction.

---

## Appendix G: Comparison Matrix

| Criterion | Digital CFD | Conventional Analogue Computer | CPB Dual‑Fluid Network |
|-----------|-------------|-------------------------------|------------------------|
| Spatial discretisation | Grid‑based | Continuous (voltage mesh) | Discrete nodes, continuous tubes |
| Temporal evolution | Time‑stepped | Continuous | Continuous |
| Error source | Truncation, round‑off | Component tolerance, noise | Sensor noise, calibration drift |
| Programmability | Full software | Patch panel, limited | FPGA‑controlled parameters |
| Energy per evaluation | High (kW‑scale) | Moderate | 270-765 W for 3×3 array (measured TBD) |
| Bandwidth | Unlimited (in principle) | ~kHz | ~kHz (limited by acoustics) |
| Scalability | Excellent (software) | Poor (hardware scaling) | Unknown (to be tested) |

---

## Appendix H: Comparison with Other Analog Computing Substrates

| Substrate | Strengths | Limitations | CPB Niche |
|-----------|-----------|-------------|-----------|
| **Hydraulic analog** | Intrinsically fluid‑dynamic; passive. | Fixed geometry; drift; noise; difficult to reprogram. | Magnetic/electronic reconfigurability; electronic readout. |
| **Memristor crossbar** | Scalable; fast; commercial (IBM 12.4 TOPS/W). | No intrinsic fluid physics; requires external modelling of transport. | Native fluid dynamics for transport bias; potential for reduced training data. |
| **Photonic reservoir** | GHz bandwidth; NRMSE <0.01 on MG; room temperature. | Weakly nonlinear; limited coupling to fluid problems. | Multi‑physics coupling for transport; native PDE structure. |
| **Optical Ising machine** | Optimised for combinatorial problems. | Not designed for continuous transport PDEs. | Continuous‑time PDE relaxation. |
| **Analog crossbar (RRAM)** | Matrix multiplication acceleration. | Purely algebraic; no PDE structure. | Embeds PDE structure in physical dynamics. |

This comparison highlights that the CPB network occupies a narrow but potentially valuable niche: a physically reconfigurable, multi‑physics fluid‑plasma system whose natural dynamics provide an inductive bias for transport problems. The CPB cannot compete on raw speed or precision with electronic or photonic systems; its value proposition rests entirely on the unique combination of fluid dynamics and plasma sensing.

---

## References

1. Moin, P. & Mahesh, K. *Direct numerical simulation: a tool in turbulence research*. Annu. Rev. Fluid Mech. **30**, 539-578 (1998). DOI: 10.1146/annurev.fluid.30.1.539.
2. Pope, S. B. *Turbulent Flows*. Cambridge University Press (2000).
3. Lorenz, E. N. *Deterministic nonperiodic flow*. J. Atmos. Sci. **20**, 130-141 (1963). DOI: 10.1175/1520-0469(1963)020<0130:DNF>2.0.CO;2.
4. Messina, P. *The Exascale Computing Project*. Comput. Sci. Eng. **19**, 63-67 (2017).
5. Bush, V. *The differential analyzer*. J. Franklin Inst. **212**, 447-488 (1931).
6. Shannon, C. E. *Mathematical theory of the differential analyzer*. J. Math. Phys. **20**, 337-354 (1941).
7. Davis, H. T. *The Differential Analyzer*. J. Am. Stat. Assoc. **29**, 207-208 (1934).
8. Rubel, L. A. *The Extended Analog Computer*. Adv. Appl. Math. **14**, 39-64 (1993). DOI: 10.1006/aama.1993.1005.
9. Kirshner, J. M. *Fluid Amplifiers*. McGraw‑Hill (1966).
10. Foster, K. & Parker, G. A. *Fluidics: Components and Circuits*. Wiley‑Interscience (1970).
11. Belsterling, C. A. *Fluidic Systems Design*. Wiley (1971).
12. Jaeger, H. *The "echo state" approach to analysing and training recurrent neural networks*. GMD Report 148 (2001).
13. Maass, W., Natschläger, T. & Markram, H. *Real‑time computing without stable states: a new framework for neural computation based on perturbations*. Neural Comput. **14**, 2531-2560 (2002).
14. Tanaka, G., et al. *Recent advances in physical reservoir computing: A review*. Neural Networks **115**, 100-123 (2019). DOI: 10.1016/j.neunet.2019.03.005.
15. Liang, X., et al. *Physical reservoir computing with emerging electronics*. Nat. Electron. **7**, 193-206 (2024). DOI: 10.1038/s41928-024-01133-z.
16. Degrave, J., et al. *A substrate‑independent framework to characterize reservoir computers*. Proc. R. Soc. A **475**, 20180723 (2019). DOI: 10.1098/rspa.2018.0723.
17. CPB‑ENG‑001 Rev 4.0 - Coherent Particle Beam Engineering Specification. [GitHub](https://github.com/theblobinc/Duotronics) - Repository retains the historical "Duotronics" name for backward compatibility.
18. Integrated Mag‑Lev Turbine Particle Source - White Paper, Rev 2.2, 2026‑07‑06. [GitHub](https://github.com/theblobinc/Duotronics).
19. White, F. M. *Fluid Mechanics*. 8th ed., McGraw‑Hill (2016).
20. Jackson, J. D. *Classical Electrodynamics*. 3rd ed., Wiley (1999).
21. Lieberman, M. A. & Lichtenberg, A. J. *Principles of Plasma Discharges and Materials Processing*. 2nd ed., Wiley (2005).
22. Chen, F. F. *Introduction to Plasma Physics and Controlled Fusion*. 3rd ed., Springer (2016).
23. Freidberg, J. P. *Plasma Physics and Fusion Energy*. Cambridge University Press (2007).
24. Simon, D. *Optimal State Estimation*. Wiley (2006).
25. Raizer, Y. P. *Gas Discharge Physics*. Springer (1991).
26. Strogatz, S. H. *Nonlinear Dynamics and Chaos*. 2nd ed., Westview Press (2015).
27. Goodfellow, I., Bengio, Y. & Courville, A. *Deep Learning*. MIT Press (2016).
28. Pikovsky, A., Rosenblum, M. & Kurths, J. *Synchronization: A Universal Concept in Nonlinear Sciences*. Cambridge University Press (2001).
29. LeVeque, R. J. *Finite Volume Methods for Hyperbolic Problems*. Cambridge University Press (2002).
30. Anderson, J. D. *Computational Fluid Dynamics*. McGraw‑Hill (1995).
31. Schlichting, H. & Gersten, K. *Boundary‑Layer Theory*. 9th ed., Springer (2017).
32. Bäck, T. *Evolutionary Algorithms in Theory and Practice*. Oxford University Press (1996); Nelder, J. A. & Mead, R. *A simplex method for function minimization*. Comput. J. **7**, 308-313 (1965).
33. Brunton, S. L. & Kutz, J. N. *Data‑Driven Science and Engineering*. Cambridge University Press (2019).
34. Johnson, J. B. *Thermal agitation of electricity in conductors*. Phys. Rev. **32**, 97-109 (1928).
35. Kulite Semiconductor Products, Inc. *XCQ‑093 series pressure transducer datasheet*. https://www.kulite.com.
36. JCGM 100:2008 *Evaluation of measurement data - Guide to the expression of uncertainty in measurement* (GUM).
37. Korn, G. A. & Korn, T. M. *Electronic Analog and Hybrid Computers*. 2nd ed., McGraw‑Hill (1972).
38. van der Schaft, A. & Jeltsema, D. *Port‑Hamiltonian systems theory: an introductory overview*. Found. Trends Syst. Control **1**, 173-378 (2014).
39. Khalil, H. K. *Nonlinear Systems*. 3rd ed., Prentice Hall (2002).
40. Crank, J. *The Mathematics of Diffusion*. 2nd ed., Oxford University Press (1975).
41. Burgers, J. M. *A mathematical model illustrating the theory of turbulence*. Adv. Appl. Mech. **1**, 171-199 (1948).
42. Mackey, M. C. & Glass, L. *Oscillation and chaos in physiological control systems*. Science **197**, 287-289 (1977).
43. Atiya, A. F. & Parlos, A. G. *New results on recurrent network training: unifying the algorithms and accelerating convergence*. IEEE Trans. Neural Networks **11**, 697-709 (2000).
44. Kuramoto, Y. *Chemical Oscillations, Waves, and Turbulence*. Springer (1984).
45. Dambre, J., Verstraeten, D., Schrauwen, B. & Massar, S. *Information processing capacity of dynamical systems*. Sci. Rep. **2**, 514 (2012). DOI: 10.1038/srep00514.
46. Drexler, K. E. *Nanosystems: Molecular Machinery, Manufacturing, and Computation*. Wiley (1992).
47. Rawlings, J. B. & Mayne, D. Q. *Model Predictive Control: Theory and Design*. Nob Hill Publishing (2009).

---

**GitHub Repository**  
[Duotronics](https://github.com/theblobinc/Duotronics) - MIT Licensed - contains supplementary simulation scripts, FPGA bitstreams, and network topology design tools. The repository name is retained for historical continuity.