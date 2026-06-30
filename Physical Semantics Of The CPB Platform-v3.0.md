# Physical Semantics Of The CPB Platform
## A Candidate Isomorphism Between the Coaxial Venturi Geometry and SRNN Dynamics

*Document Version: 3.0 - Detailed Internal Exposition*  
*Corresponds to: Duotronics Chapters 1-17, CPB-ENG-001 v4.0, Integrated Mag-Lev Turbine v2.2, CPB-COMP-001 v2.7*  
*Derived from: 2004-2005 Notebook Geometry - First Principles*  
*Classification: Internal Technical Notes*  
*Author: Hugh Armstrong -  TBI Contracting Inc.*

---

### 0. Preamble: What This Document Is, and What It Is Not

#### 0.1 The Modular Nature of the Duotronics Repository

The Duotronics project is deliberately organised as a collection of modular, independently developable components. These include:

- **Hardware specifications** (CPB‑ENG‑001, Integrated Mag‑Lev Turbine white paper) that describe the physical geometry, materials, operating parameters, and engineering constraints of the Coherent Particle Beam platform.
- **A computing framework** (CPB‑COMP‑001, the reservoir computing white paper) that treats the CPB hardware as a candidate physical reservoir computer, with formal hypotheses, benchmarks, and an experimental validation roadmap.
- **Formal witness contracts** that define what it means for a measurement to be non‑invasive and independently verifiable.
- **A conformance harness** for automated testing and validation of physical nodes.
- **A bus protocol** for inter‑node communication across pneumatic, magnetic, and electrical channels.
- **A theory of Self‑Referential Recurrent Neural Networks** (SRNNs), developed in the Duotronics chapters, providing a formal language of state vectors, weight matrices, activation functions, training procedures, and semantic interpretation.

Each of these components can be developed, tested, and reasoned about independently. The modularity is a feature, not a bug: it allows different theoretical lenses to be applied to the same hardware, and it allows the hardware to evolve without breaking the theoretical superstructure.

#### 0.2 The Question This Document Addresses

The Coherent Particle Beam (CPB) platform-in its integrated magnetic levitation turbine (IMLT) form-provides a physical system of conductive mist, plasma discharge, and electromagnetic fields. The SRNN theory provides a formal language of computation. Between these two domains lies a question:

> **Is there a useful, structured correspondence between the formal symbols of an SRNN and the measurable observables of the CPB hardware?**

This document proposes one candidate answer to that question. It is **not** a claim of exact equivalence. It is **not** a proof that the CPB hardware implements an SRNN. It is a **structured hypothesis**: a proposed mapping, under explicitly stated idealisations and approximations, from the computational formalism to the physics. If this mapping holds to within experimentally determined tolerances, then the CPB node may be usefully interpreted as an effective physical instantiation of certain classes of recurrent networks.

#### 0.3 What a Physical Semantics Means

In formal logic and computer science, a **semantics** is a mapping from the symbols of a formal language to a domain of interpretation. For a programming language, the semantics tells you what a program *means*-what mathematical function it computes. For a physical computer, the semantics tells you what physical states correspond to what logical states.

A physical semantics for the CPB platform would answer questions like:

- What physical quantity represents the state vector \(\mathbf{S}(t)\)?
- What physical process implements the weight matrix multiplication \(\mathbf{W} \cdot \mathbf{S}\)?
- What physical nonlinearity provides the activation function \(f\)?
- How is the output \(y(t)\) read from the system without disturbing the computation?
- What defines a clock cycle or iteration?

This document proposes answers to these questions, grounded in the geometry of the coaxial Venturi stage-the high‑aspect‑ratio drift tube, the annular mist flow, the central electrode, and the inductive pickup.

#### 0.4 The Status of This Document

This is an **internal technical note**. It is not intended for publication in its current form. It is a working document for the Duotronics project team. It contains:

- Detailed physical reasoning at both intuitive and mathematical levels.
- Explicit statements of all assumptions and simplifications.
- Falsification criteria that can be tested experimentally.
- Connections to other components of the Duotronics architecture.

It does **not** claim to be the definitive semantics for the CPB platform. It is one theoretical lens among several. The reservoir computing framework (CPB‑COMP‑001) provides a different, more agnostic lens. Both are tools for understanding and exploiting the unique physics of the CPB platform.

---

### 1. Axiom I: Effective Dimensionality Reduction (The Quasi‑1D Constraint)

#### 1.1 Intuitive Statement

Imagine a long, thin tube filled with gas. If you strike a tuning fork and hold it at one end of the tube, the sound waves travel primarily along the tube, not across it. The tube is too narrow for the sound to bounce side‑to‑side at the frequencies you're producing; those transverse modes are "cut off" and die out. The only waves that propagate are the ones moving along the tube's length.

The CPB's inner drift tube is like that. It is 2 mm in diameter and 80 mm long-a factor of 40 in aspect ratio. The plasma discharge inside it produces density fluctuations, pressure waves, and electric field variations. To a first approximation, all of these dynamics happen along the tube axis. The radial and azimuthal directions are slaved to the axial dynamics; they don't contribute independent degrees of freedom.

This is the central idea of Axiom I: the infinite‑dimensional phase space of a 3D compressible plasma, when confined in such a high‑aspect‑ratio tube, collapses onto a finite‑dimensional, effectively one‑dimensional state space. The number of independent degrees of freedom \(N\) is determined by the tube's geometry and the frequency content of the driving signals.

#### 1.2 Detailed Physical Derivation

**Geometry and coordinate system.**  
The inner drift tube is a right circular cylinder of internal diameter \(d = 2.00 \text{ mm}\) and length \(L = 80 \text{ mm}\). We work in cylindrical coordinates \((r, \theta, z)\) with the \(z\)‑axis along the tube centreline. The tube wall is at \(r = d/2 = 1.00 \text{ mm}\). The upstream end (\(z = 0\)) is sealed by the emitter feedthrough. The downstream end (\(z = L\)) opens into the collector region.

**Wave equation in a cylindrical duct.**  
Consider a small perturbation \(\Phi(r, \theta, z, t)\) in the gas density, pressure, or plasma potential. The linearised wave equation in cylindrical coordinates is:

\[
\frac{\partial^2 \Phi}{\partial t^2} = c^2 \nabla^2 \Phi
\]

where \(c\) is the relevant wave speed (speed of sound for neutral gas, ion acoustic speed for plasma). We seek separated solutions of the form:

\[
\Phi(r, \theta, z, t) = R(r) \cdot \Theta(\theta) \cdot Z(z) \cdot T(t)
\]

Plugging this ansatz into the wave equation and dividing by \(\Phi\) yields:

\[
\frac{1}{c^2} \frac{\ddot{T}}{T} = \frac{1}{R} \left( \frac{d^2 R}{dr^2} + \frac{1}{r} \frac{dR}{dr} \right) + \frac{1}{r^2} \frac{1}{\Theta} \frac{d^2 \Theta}{d\theta^2} + \frac{1}{Z} \frac{d^2 Z}{dz^2} = -k^2
\]

where \(k\) is the total wavenumber. The azimuthal part gives \(\Theta(\theta) = e^{i m \theta}\) with integer \(m \ge 0\). The radial part gives Bessel's equation:

\[
r^2 \frac{d^2 R}{dr^2} + r \frac{dR}{dr} + (\lambda^2 r^2 - m^2) R = 0
\]

whose non‑singular solutions are \(R(r) = J_m(\lambda r)\), where \(\lambda\) is a radial eigenvalue to be determined by boundary conditions.

**Boundary condition at the tube wall.**  
The inner tube wall is rigid and non‑porous (the conductive mist flows outside it). For acoustic perturbations in the neutral gas, the radial velocity must vanish at the wall: \(\partial_r \Phi|_{r = d/2} = 0\). This implies:

\[
\left. \frac{d J_m(\lambda r)}{dr} \right|_{r = d/2} = 0
\]

For each azimuthal index \(m\), this transcendental equation has a discrete set of solutions \(\lambda_{mn}\) (\(n = 1, 2, 3, \dots\)). The smallest non‑zero eigenvalue for non‑axisymmetric modes (\(m \ge 1\)) is \(\lambda_{11} \approx 1.841 / (d/2)\).

**Cutoff frequency.**  
The dispersion relation for duct modes is:

\[
k^2 = \frac{\omega^2}{c^2} - \lambda_{mn}^2
\]

For a mode to propagate in the \(z\)‑direction, \(k\) must be real, which requires \(\omega > \omega_c = c \lambda_{mn}\). If \(\omega < \omega_c\), \(k\) is imaginary and the mode decays exponentially along \(z\).

For the first transverse mode (\(m = 1, n = 1\)):

\[
\omega_c = \frac{c \cdot \lambda_{11}}{d/2} \approx \frac{c \cdot 1.841}{0.001 \text{ m}}
\]

Taking \(c \approx 340 \text{ m/s}\) for air at STP:

\[
f_c = \frac{\omega_c}{2\pi} \approx \frac{340 \cdot 1.841}{2\pi \cdot 0.001} \approx 99.7 \text{ kHz}
\]

Our earlier rough estimate of 80 kHz is in the right ballpark; the exact value depends on the gas composition, temperature, and whether we're considering neutral acoustic waves or plasma ion acoustic waves. For the plasma case, \(c_s \approx 1000 \text{ m/s}\) gives \(f_c \approx 290 \text{ kHz}\).

**What this means in practice.**  
The CPB operates with driving signals-HV pulses, mist pressure oscillations, magnetic field modulations-in the kHz to tens‑of‑kHz range. The rotor spins at up to 50 krpm (833 Hz fundamental). The HV discharge pulses have durations of 1-100 µs, corresponding to bandwidths of 10 kHz-1 MHz. The mist pressure fluctuations are in the sub‑kHz range.

All of these operational frequencies are well below the transverse cutoff frequency. Therefore, any transverse modes that might be excited are evanescent: they decay exponentially with distance from their source and do not propagate along the tube. The only modes that propagate are the axisymmetric (\(m=0\)), purely axial modes.

**The role of the conductive mist.**  
The mist in the outer annulus provides an additional damping mechanism. The mist is a dense aerosol of conductive droplets (diameter ~2-5 µm). The droplets have substantial inertia and viscous drag. Any transverse acoustic wave in the gas that impinges on the tube wall encounters the mist layer on the other side. The acoustic impedance mismatch between the gas and the mist‑loaded annulus, combined with viscous dissipation in the droplet‑laden boundary layer, further attenuates transverse modes. In engineering terms, the mist acts as a broadband acoustic absorber for non‑axial modes.

**Eigenfunction expansion.**  
The general solution for axisymmetric (\(m=0\)) waves in the tube can be written as:

\[
\Phi(z, t) = \sum_{n=1}^{\infty} A_n(t) \cdot \Phi_n(z)
\]

where \(\Phi_n(z)\) are the axial eigenmodes determined by the boundary conditions at \(z = 0\) and \(z = L\). The specific form of \(\Phi_n\) depends on whether we treat the ends as closed, open, or something in between. We'll derive these eigenmodes in detail in Section 5.3. For now, the key point is that the axial direction admits a discrete set of modes, and the number of modes that are significantly excited depends on the frequency content of the driving signals.

#### 1.3 Discretisation into State Variables

The continuous field \(\Phi(z, t)\) can be represented in a discrete basis in (at least) two ways:

**Method 1: Finite‑volume cells.**  
Divide the tube length \(L\) into \(N\) equal cells of length \(\Delta z = L / N\). The state of the system is the vector of cell‑averaged quantities:

\[
\mathbf{S}(t) = [\bar{\rho}_1(t), \bar{\rho}_2(t), \dots, \bar{\rho}_N(t)]^T
\]

where \(\bar{\rho}_i(t) = \frac{1}{\Delta z} \int_{z_{i-1/2}}^{z_{i+1/2}} \rho(z, t) \, dz\). This is the approach used in finite‑volume CFD and is the most natural for the convection‑diffusion model in Axiom II.

**Method 2: Modal expansion.**  
Represent the state as the vector of mode amplitudes:

\[
\mathbf{S}(t) = [A_1(t), A_2(t), \dots, A_N(t)]^T
\]

where \(A_n(t)\) is the amplitude of the \(n\)-th axial eigenmode. This is the approach of Galerkin projection and is more natural for describing the system's resonant behaviour.

In practice, these two representations are related by a linear transformation. The finite‑volume representation is easier to connect to the Navier‑Stokes discretisation; the modal representation is easier to connect to the acoustic resonator picture. The choice of \(N\)-the effective dimensionality of the state space-depends on which representation is used and what frequency range is relevant.

**How many modes are relevant?**  
The HV pulse bandwidth provides a natural upper limit. For a pulse of duration \(\Delta t\), the excitation spectrum extends up to roughly \(f_{\max} \approx 1 / (2\Delta t)\). For \(\Delta t = 100 \text{ µs}\), \(f_{\max} \approx 5 \text{ kHz}\); for \(\Delta t = 10 \text{ µs}\), \(f_{\max} \approx 50 \text{ kHz}\).

The axial eigenfrequencies (derived in Section 5.3) are \(f_n = \frac{c_s}{4L} (2n-1)\). For \(c_s = 1000 \text{ m/s}\) and \(L = 0.08 \text{ m}\):

\[
f_1 \approx 3.1 \text{ kHz},\quad f_2 \approx 9.3 \text{ kHz},\quad f_3 \approx 15.6 \text{ kHz},\quad f_4 \approx 21.9 \text{ kHz},\quad \dots
\]

The number of modes with \(f_n < f_{\max}\) gives a lower bound on \(N\). For \(\Delta t = 100 \text{ µs}\) (\(f_{\max} \approx 5 \text{ kHz}\)), only the fundamental mode (\(n=1\)) is clearly within the bandwidth. For \(\Delta t = 10 \text{ µs}\) (\(f_{\max} \approx 50 \text{ kHz}\)), roughly 6-7 modes are accessible. Adding a safety factor for nonlinear harmonics, a practical range is \(N \in [10, 50]\) for the finite‑volume discretisation, or \(N \in [3, 15]\) for the modal discretisation.

**The Debye length constraint.**  
The plasma has a characteristic screening length, the Debye length:

\[
\lambda_D = \sqrt{\frac{\epsilon_0 k_B T_e}{n_e e^2}}
\]

For a typical glow discharge with \(T_e \approx 2 \text{ eV}\) and \(n_e \approx 10^{16} \text{ m}^{-3}\):

\[
\lambda_D \approx \sqrt{\frac{8.85 \times 10^{-12} \cdot 2 \cdot 1.6 \times 10^{-19}}{10^{16} \cdot (1.6 \times 10^{-19})^2}} \approx \sqrt{\frac{2.83 \times 10^{-30}}{2.56 \times 10^{-22}}} \approx \sqrt{1.11 \times 10^{-8}} \approx 105 \text{ µm}
\]

The cell size \(\Delta z\) must be larger than \(\lambda_D\) to avoid resolving sheath physics, which would require kinetic rather than fluid modelling. With \(N = 50\), \(\Delta z = 1.6 \text{ mm} \gg \lambda_D\), comfortably satisfying this constraint.

#### 1.4 Summary of Axiom I

**Proposed Correspondence (formal):**  
Under idealised conditions (high aspect ratio, low Mach number, operation below transverse cutoff), the infinite‑dimensional phase space of the 3D compressible plasma in the drift tube can be approximately projected onto a finite‑dimensional state vector \(\mathbf{S}(t) \in \mathbb{R}^N\).

**Physical mechanism:**  
Transverse (radial and azimuthal) modes are cut off by the narrow tube geometry. The mist annulus provides additional transverse damping. The axial dynamics are discretised by choosing \(N\) based on the acoustic cutoff and the HV pulse bandwidth.

**Key quantities:**
- Tube diameter \(d = 2.00 \text{ mm}\)
- Tube length \(L = 80 \text{ mm}\)
- Transverse cutoff frequency \(f_c \sim 100 \text{ kHz}\) (neutral gas) to \(\sim 300 \text{ kHz}\) (plasma)
- Effective dimensionality \(N \in [10, 50]\) (finite‑volume) or \([3, 15]\) (modal)

**Experimental tests:** See Section 5.4, Axiom I falsification.

---

### 2. Axiom II: The Recurrence Relation (Convection‑Diffusion as a Weight Matrix)

#### 2.1 Intuitive Statement

In a standard recurrent neural network (RNN), the core operation is:

\[
\mathbf{S}_{t+1} = f(\mathbf{W} \mathbf{S}_t + \mathbf{U} \mathbf{u}_t + \mathbf{b})
\]

The weight matrix \(\mathbf{W}\) mixes the previous state vector to produce the next state. The activation function \(f\) adds nonlinearity. The input \(\mathbf{u}_t\) injects external information.

In the CPB drift tube, something structurally similar happens. The neutral gas density (or ionisation fraction) at each axial position evolves according to two processes: **convection** (the mist drags the gas downstream) and **diffusion** (the gas spreads out due to viscosity). These two processes couple each cell to its immediate neighbours, producing a **tridiagonal mixing matrix** that looks exactly like \(\mathbf{W}\).

The nonlinearity comes from the **Townsend ionisation process**. When the electric field in a cell exceeds a threshold, the gas breaks down and conducts. The rate of ionisation is an exponential function of the local electric field-a natural sigmoid‑like activation.

The HV pulses act as the input \(\mathbf{u}_t\), injecting energy into the system at specific times. The rotor speed controls the convection strength, which directly tunes the entries of \(\mathbf{W}\).

#### 2.2 Detailed Derivation of the Weight Matrix \(\mathbf{W}\)

**The convection‑diffusion equation.**  
Consider the neutral gas density \(\rho(z, t)\) in the drift tube. The mist flows axially through the outer annulus at velocity \(\bar{v}_z\), entraining the gas and imparting a mean axial velocity. In the rest frame of the gas, the density evolves according to the 1D convection‑diffusion equation:

\[
\frac{\partial \rho}{\partial t} = - \bar{v}_z \frac{\partial \rho}{\partial z} + \nu \frac{\partial^2 \rho}{\partial z^2} + S(z, t)
\tag{2.1}
\]

where:
- \(\bar{v}_z\) is the mean axial gas velocity (driven by mist entrainment),
- \(\nu\) is the effective kinematic viscosity (enhanced by mist droplet momentum transfer),
- \(S(z, t)\) represents sources and sinks-ionisation, recombination, and external forcing.

This equation is linear in \(\rho\) for a given velocity field. The nonlinearities enter through the source term \(S\) (which depends on the plasma state) and through the coupling between \(\bar{v}_z\) and the mist flow.

**Discretisation.**  
We divide the tube into \(N\) cells of equal length \(\Delta z = L/N\). The cell centres are at \(z_i = (i - 1/2) \Delta z\) for \(i = 1, 2, \dots, N\). The density in cell \(i\) is \(\rho_i(t) = \rho(z_i, t)\).

For the convective term \(- \bar{v}_z \partial_z \rho\), we use a first‑order upwind scheme. Since the gas flows from left to right (\(\bar{v}_z > 0\)), the upwind cell for cell \(i\) is cell \(i-1\):

\[
\left. \frac{\partial \rho}{\partial z} \right|_{z_i} \approx \frac{\rho_i - \rho_{i-1}}{\Delta z}
\tag{2.2}
\]

For the diffusive term \(\nu \partial^2_z \rho\), we use a central difference:

\[
\left. \frac{\partial^2 \rho}{\partial z^2} \right|_{z_i} \approx \frac{\rho_{i+1} - 2\rho_i + \rho_{i-1}}{\Delta z^2}
\tag{2.3}
\]

Substituting into (2.1) and ignoring \(S\) for the moment:

\[
\dot{\rho}_i = - \bar{v}_z \left( \frac{\rho_i - \rho_{i-1}}{\Delta z} \right) + \nu \left( \frac{\rho_{i+1} - 2\rho_i + \rho_{i-1}}{\Delta z^2} \right)
\tag{2.4}
\]

**Matrix form.**  
Collecting terms for \(\rho_{i-1}\), \(\rho_i\), and \(\rho_{i+1}\):

\[
\dot{\rho}_i = \underbrace{\left( \frac{\bar{v}_z}{\Delta z} + \frac{\nu}{\Delta z^2} \right)}_{W_{i,i-1}} \rho_{i-1} \; \underbrace{- \left( \frac{\bar{v}_z}{\Delta z} + \frac{2\nu}{\Delta z^2} \right)}_{W_{i,i}} \rho_i \; + \; \underbrace{\left( \frac{\nu}{\Delta z^2} \right)}_{W_{i,i+1}} \rho_{i+1}
\tag{2.5}
\]

This is a tridiagonal system:

\[
\mathbf{W} = \begin{bmatrix}
W_{1,1} & W_{1,2} & 0 & \cdots & 0 \\
W_{2,1} & W_{2,2} & W_{2,3} & \cdots & 0 \\
0 & W_{3,2} & W_{3,3} & \ddots & \vdots \\
\vdots & \ddots & \ddots & \ddots & W_{N-1,N} \\
0 & \cdots & 0 & W_{N,N-1} & W_{N,N}
\end{bmatrix}
\tag{2.6}
\]

Each row has at most three non‑zero entries. The structure is **nearest‑neighbour coupling**-exactly the sparsity pattern of a 1D discretised PDE.

**Boundary conditions.**  
The upstream end (\(i = 1\)) is the emitter face. The gas cannot flow through a solid wall, so the convective flux into the first cell from outside the domain is zero. Mathematically, we impose a reflecting boundary: \(\rho_0 \equiv \rho_1\). This modifies the first row:

\[
W_{1,0} \text{ (non‑existent)} \to \text{ absorbed into } W_{1,1}
\]

Specifically:

\[
W_{1,1} = -\frac{2\nu}{\Delta z^2}, \quad W_{1,2} = \frac{\nu}{\Delta z^2}
\tag{2.7}
\]

The downstream end (\(i = N\)) opens into the collector region, where the pressure drops to the ambient (much lower) value. We approximate this as an open boundary with \(\rho_{N+1} = 0\). The last row becomes:

\[
W_{N,N-1} = \frac{\bar{v}_z}{\Delta z} + \frac{\nu}{\Delta z^2}, \quad W_{N,N} = -\frac{\bar{v}_z}{\Delta z} - \frac{2\nu}{\Delta z^2}
\tag{2.8}
\]

**Rotor speed dependence.**  
The axial gas velocity \(\bar{v}_z\) is not an independent variable; it is driven by the mist flow in the annulus. The mist velocity at the rotor surface is \(U_{\text{rotor}} = \omega R\), where \(\omega = 2\pi \cdot \text{RPM}/60\) is the angular speed and \(R\) is the rotor radius. The mist transfers momentum to the gas through the tube wall via viscous shear, but there is a slip factor \(\eta\) because the mist and gas are separated by the tube wall:

\[
\bar{v}_z = \eta \cdot U_{\text{rotor}} = \eta \cdot \omega R
\tag{2.9}
\]

The slip factor \(\eta\) depends on the annulus gap \(g\) and the effective viscosities. A simple Couette‑flow estimate gives:

\[
\eta \approx \frac{\mu_{\text{mist}}}{\mu_{\text{mist}} + \mu_{\text{gas}}} \cdot \frac{R}{R + g}
\tag{2.10}
\]

For a saline aerosol (\(\mu_{\text{mist}} \approx 1.8 \times 10^{-5} \text{ Pa·s}\)), air (\(\mu_{\text{gas}} \approx 1.8 \times 10^{-5} \text{ Pa·s}\)-similar order), \(R = 25 \text{ mm}\), \(g = 0.2 \text{ mm}\):

\[
\eta \approx \frac{1.8}{1.8 + 1.8} \cdot \frac{25}{25.2} \approx 0.5 \cdot 0.992 \approx 0.5
\]

In practice, turbulent mixing in the annulus can increase \(\eta\) to 0.6-0.9, as stated in the earlier draft. The key point is that **every non‑zero element of \(\mathbf{W}\) scales linearly with RPM**. If we double the rotor speed, we double the convective coupling strength.

**Numerical example.**  
Take \(N = 20\), \(L = 0.08 \text{ m}\), \(\Delta z = 0.004 \text{ m}\). At 30 krpm with a 50 mm rotor (\(R = 0.025 \text{ m}\)), \(\omega = 3142 \text{ rad/s}\), \(U_{\text{rotor}} = 78.5 \text{ m/s}\). With \(\eta = 0.7\), \(\bar{v}_z = 55 \text{ m/s}\). Taking \(\nu \approx 1.5 \times 10^{-5} \text{ m}^2/\text{s}\) for air:

\[
\frac{\bar{v}_z}{\Delta z} = \frac{55}{0.004} = 13,750 \text{ s}^{-1}, \quad \frac{\nu}{\Delta z^2} = \frac{1.5 \times 10^{-5}}{1.6 \times 10^{-5}} = 0.94 \text{ s}^{-1}
\]

The convective term dominates by four orders of magnitude. This means \(\mathbf{W}\) is highly asymmetric: the sub‑diagonal entries (upstream → downstream) are much larger than the super‑diagonal entries (downstream → upstream). The system is strongly directional-information flows primarily downstream, with only weak back‑diffusion.

**Implication for reservoir computing.**  
A highly asymmetric weight matrix with strong directionality is not ideal for a conventional reservoir, which benefits from recurrent (feedback) connections. However, the weak back‑diffusion provides a small but non‑zero recurrent component. Furthermore, the plasma nonlinearity and the inter‑node pneumatic coupling in a parallel array (not captured by this single‑tube model) can introduce additional recurrence. The reservoir computing framework in CPB‑COMP‑001 does not require the weight matrix to have any particular structure; it only requires that the overall dynamics be sufficiently rich and high‑dimensional.

#### 2.3 The Activation Function: Townsend Ionisation

**Physical mechanism.**  
In a glow discharge, free electrons are accelerated by the electric field \(\mathbf{E}\). When an electron gains enough energy between collisions with neutral gas molecules, it can ionise a neutral, creating a new electron‑ion pair. This process is characterised by the **first Townsend coefficient** \(\alpha\), defined as the number of ionising collisions per unit length of electron drift.

Townsend's empirical formula (valid for a wide range of gases and E/p values) is:

\[
\alpha = A \cdot p \cdot \exp\left( -\frac{B \cdot p}{E} \right)
\tag{2.11}
\]

where:
- \(p\) is the gas pressure,
- \(E = |\mathbf{E}|\) is the electric field magnitude,
- \(A\) and \(B\) are experimentally determined constants that depend on the gas species.

For air, typical values are \(A \approx 15 \text{ cm}^{-1} \text{ Torr}^{-1}\), \(B \approx 365 \text{ V} \text{ cm}^{-1} \text{ Torr}^{-1}\). In SI units (with \(p\) in Pa, \(E\) in V/m), these become \(A \approx 1.1 \times 10^4 \text{ m}^{-1} \text{ Pa}^{-1}\), \(B \approx 2.7 \times 10^2 \text{ V} \text{ m}^{-1} \text{ Pa}^{-1}\).

**Sigmoidal shape.**  
When plotted against the reduced electric field \(E/p\), the Townsend coefficient has a characteristic shape:

- At low \(E/p\): the exponential term \(\exp(-Bp/E)\) is vanishingly small. Essentially no ionisation occurs. This is the **sub‑threshold** regime.
- As \(E/p\) increases past a critical value (roughly \(E/p \approx B / \ln(A p / \text{something})\)), the coefficient rises sharply. This is the **threshold** region, analogous to the "knee" of a sigmoid.
- At high \(E/p\): the exponential saturates toward 1, and \(\alpha \approx A p\). The ionisation rate becomes roughly linear in pressure. This is the **saturation** regime.

This three‑region behaviour-sub‑threshold, threshold, saturation-is structurally identical to the sigmoidal activation functions used in neural networks (e.g., the logistic function \(\sigma(x) = 1/(1 + e^{-x})\) or the hyperbolic tangent). The key difference is that the Townsend function is not bounded above by 1; it grows roughly linearly after saturation. In practice, the plasma current is limited by the external circuit impedance and by space‑charge effects, providing an effective upper bound.

**Element‑wise activation assumption.**  
In a standard RNN, the activation function \(f\) is applied element‑wise to each component of the pre‑activation vector \(\mathbf{W}\mathbf{S} + \mathbf{U}\mathbf{u} + \mathbf{b}\). For the CPB, we propose that the Townsend coefficient \(\alpha_i\) in each cell acts as an element‑wise function of the local reduced field \((E/p)_i\):

\[
\alpha_i = f( (E/p)_i ) \quad \text{with} \quad f(x) = A p_i \exp(-B / x)
\tag{2.12}
\]

This is an approximation. In reality, the electric field \(E_i\) in cell \(i\) is not locally determined; it depends on the entire plasma column through Poisson's equation \(\nabla \cdot \mathbf{E} = \rho_c / \epsilon_0\) (where \(\rho_c\) is the charge density) and through the requirement that the total voltage drop across the tube equals the applied HV. The plasma is a globally coupled nonlinear medium. The element‑wise activation is a **mean‑field approximation** that becomes exact only in the limit of weak axial coupling or highly localised electric fields.

#### 2.4 Input Matrix and Bias

**Input \(\mathbf{u}(t)\).**  
The external drive to the system is the HV pulse sequence applied to the central electrode. The time‑varying voltage \(V_{\text{HV}}(t)\) creates an axial electric field \(E_z(z, t) \approx V_{\text{HV}}(t) / L\) (to zeroth order, ignoring sheath drops). This electric field enters the plasma momentum equation (A6 in Appendix A of CPB‑COMP‑001) and drives the ionisation process.

In the discretised model, the input at time \(t\) is the scalar \(u(t) = V_{\text{HV}}(t)\). The input matrix \(\mathbf{U}\) is a vector \(\mathbf{u}_{\text{in}} \in \mathbb{R}^N\) that distributes the applied voltage across the axial cells. To first order, \(\mathbf{u}_{\text{in}} = [1, 1, \dots, 1]^T\) (uniform field), but the actual distribution depends on the sheath structure and the plasma conductivity profile.

**Bias \(\mathbf{b}\).**  
The background ionisation from the magnetic pre‑ionisation field (Section 3.3 of the IMLT white paper) provides a baseline electron density even before the HV pulse is applied. This acts as a bias term \(\mathbf{b} \in \mathbb{R}^N\) in the RNN equation:

\[
\mathbf{S}_{k+1} = f(\mathbf{W} \mathbf{S}_k + \mathbf{U} u_k + \mathbf{b})
\tag{2.13}
\]

The bias ensures that the activation function is not stuck in the sub‑threshold regime when the input is small. It is the physical analogue of the bias term in artificial neural networks, which shifts the operating point of the activation function.

#### 2.5 Summary of Axiom II

**Proposed Correspondence (formal):**  
Under linearised, quasi‑1D conditions, the time evolution of the state vector \(\mathbf{S}(t)\) is governed by coupled ODEs that are structurally analogous to a continuous‑time RNN. The weight matrix \(\mathbf{W}\) is a tridiagonal matrix determined by mist‑driven convection and viscous diffusion, with entries proportional to rotor RPM. The activation function \(f\) is provided by the Townsend ionisation coefficient, which is sigmoidal in the reduced electric field \(E/p\).

**Physical mechanism:**
- Convection (−\(\bar{v}_z \partial_z\)) → sub‑diagonal entries of \(\mathbf{W}\) (downstream coupling)
- Diffusion (\(\nu \partial^2_z\)) → super‑ and sub‑diagonal entries (symmetric spreading)
- Townsend ionisation → element‑wise sigmoidal activation
- HV pulses → input \(\mathbf{u}(t)\)
- Magnetic pre‑ionisation → bias \(\mathbf{b}\)

**Key quantities:**
- Convective timescale: \(\tau_{\text{conv}} = L / \bar{v}_z \sim 1.5 \text{ ms}\) at 30 krpm
- Diffusive timescale: \(\tau_{\text{diff}} = L^2 / \nu \sim 430 \text{ s}\) (negligible on computational timescales)
- Townsend constants for air: \(A \approx 1.1 \times 10^4 \text{ m}^{-1} \text{ Pa}^{-1}\), \(B \approx 2.7 \times 10^2 \text{ V} \text{ m}^{-1} \text{ Pa}^{-1}\)
- Rotor speed control: \(\mathbf{W} \propto \text{RPM}\)

**Experimental tests:** See Section 5.4, Axiom II falsification.

---

### 3. Axiom III: The Readout and Witness (Inductive Current Sensing)

#### 3.1 Intuitive Statement

In an RNN, after the state has been updated, we need to extract an output. The output is typically a linear combination of the state variables: \(y = \mathbf{\alpha}^T \mathbf{S}\). The readout weights \(\mathbf{\alpha}\) are trained (in a reservoir computer) or fixed by the problem.

In the CPB, the plasma current \(I(t)\) is a natural, physically integrated measure of the entire plasma column. It is the sum of all the tiny currents contributed by each axial cell. The constant of proportionality between the local plasma density and the local current contribution depends on the electron drift velocity and the tube cross‑section.

The key engineering insight is that this current can be measured **without making electrical contact with the plasma**. The pot‑core rotary transformer encircles the drift tube. The plasma current acts like a single‑turn primary winding. The changing magnetic flux induces a voltage in a multi‑turn secondary winding on the stator side. By integrating this voltage, we recover the plasma current waveform.

This is a **non‑invasive witness** of the computation. The measurement does not load the plasma, does not introduce noise into the HV circuit, and provides galvanic isolation between the high‑voltage plasma and the low‑voltage control electronics.

#### 3.2 Detailed Derivation of the Readout

**Plasma current decomposition.**  
In a quasi‑1D plasma column, the total axial current \(I(t)\) is the sum of the convective current (moving charges) and the displacement current (changing electric field):

\[
I(t) = \int_0^L \left( e \, n_e(z, t) \, v_d(z, t) + \epsilon_0 \frac{\partial E_z(z, t)}{\partial t} \right) A_{\text{tube}} \, dz
\tag{3.1}
\]

where:
- \(e = 1.602 \times 10^{-19} \text{ C}\) is the elementary charge,
- \(n_e(z, t)\) is the electron number density (m⁻³),
- \(v_d(z, t)\) is the electron drift velocity (m/s),
- \(E_z(z, t)\) is the axial electric field (V/m),
- \(A_{\text{tube}} = \pi (d/2)^2 = \pi (0.001)^2 = 3.14 \times 10^{-6} \text{ m}^2\) is the tube cross‑sectional area.

The displacement current term \(\epsilon_0 \partial_t E_z\) is significant only during the rising and falling edges of HV pulses (when \(E_z\) changes rapidly). During the quasi‑steady glow, the convective term dominates.

**Discretised form.**  
Dividing the tube into \(N\) cells of length \(\Delta z\), the current becomes:

\[
I(t) = \sum_{i=1}^N \left( e \, n_{e,i}(t) \, v_{d,i}(t) + \epsilon_0 \dot{E}_{z,i}(t) \right) A_{\text{tube}} \, \Delta z
\tag{3.2}
\]

If we take the state vector \(\mathbf{S}\) to represent the electron density \(n_e\) in each cell, and if we assume that the drift velocity \(v_{d,i}\) is approximately constant across cells (to leading order), then:

\[
I(t) \approx \sum_{i=1}^N \beta_i \cdot S_i(t) \quad \text{with} \quad \beta_i = e \, v_{d,i} \, A_{\text{tube}} \, \Delta z
\tag{3.3}
\]

plus a displacement current term. This is a **linear functional** of the state.

**Mutual inductance of the pot‑core pickup.**  
The pot‑core rotary transformer is described in detail in Section 4.3 of the IMLT white paper. Here we focus on its role as a current sensor.

The plasma column acts as a single‑turn conductor carrying current \(I(t)\). This current produces a magnetic field that circulates around the tube according to Ampère's law:

\[
\oint \mathbf{B} \cdot d\mathbf{l} = \mu_0 I_{\text{enclosed}}
\tag{3.4}
\]

The pot‑core is a toroidal ferrite core that encircles the drift tube. It concentrates the magnetic flux. The magnetic field inside the core (assuming no saturation) is:

\[
B = \frac{\mu_r \mu_0 I(t)}{l_{\text{path}}}
\tag{3.5}
\]

where:
- \(\mu_r\) is the relative permeability of the ferrite (typically 2000-5000 for MnZn ferrites),
- \(\mu_0 = 4\pi \times 10^{-7} \text{ H/m}\) is the vacuum permeability,
- \(l_{\text{path}}\) is the mean magnetic path length around the toroid.

The magnetic flux through the core cross‑section \(A_{\text{core}}\) is:

\[
\Phi = B \cdot A_{\text{core}} = \frac{\mu_r \mu_0 A_{\text{core}}}{l_{\text{path}}} I(t)
\tag{3.6}
\]

If the pickup coil has \(N\) turns wound around the core, the total flux linkage is \(\lambda = N \Phi\). The mutual inductance between the plasma (primary) and the pickup coil (secondary) is:

\[
M = \frac{\lambda}{I} = \frac{\mu_r \mu_0 N A_{\text{core}}}{l_{\text{path}}}
\tag{3.7}
\]

In practice, the ferrite core has an air gap (to prevent saturation), which dominates the magnetic reluctance. If the gap length is \(l_{\text{gap}}\) and \(\mu_r\) is large, then:

\[
M \approx \frac{\mu_0 N A_{\text{core}}}{l_{\text{gap}}}
\tag{3.8}
\]

For typical dimensions (\(A_{\text{core}} \approx 50 \text{ mm}^2\), \(l_{\text{gap}} \approx 0.2 \text{ mm}\), \(N = 100\)):

\[
M \approx \frac{4\pi \times 10^{-7} \cdot 100 \cdot 5 \times 10^{-5}}{2 \times 10^{-4}} = \frac{6.28 \times 10^{-9}}{2 \times 10^{-4}} \approx 3.1 \times 10^{-5} \text{ H} = 31 \text{ µH}
\]

This is within the 1-100 µH range typical for such pickups.

**Sensed voltage.**  
By Faraday's law, the voltage induced in the pickup coil is:

\[
V_{\text{sense}}(t) = - \frac{d\lambda}{dt} = - M \frac{dI}{dt}
\tag{3.9}
\]

The negative sign indicates polarity (Lenz's law); for magnitude, we take \(V_{\text{sense}} = M |dI/dt|\). This voltage is proportional to the **derivative** of the plasma current.

**Signal reconstruction.**  
To recover the current waveform \(I(t)\), the sensed voltage must be integrated:

\[
I_{\text{reconstructed}}(t) = \frac{1}{M} \int_0^t V_{\text{sense}}(\tau) \, d\tau + I(0)
\tag{3.10}
\]

The initial current \(I(0)\) (DC offset) can be measured separately or assumed zero between pulses. The integration is performed by an active integrator circuit (op‑amp with capacitive feedback) in the front‑end electronics, sampled by the FPGA ADC.

**Readout vector.**  
Combining (3.3) and the mutual inductance calibration:

\[
y(t) = I_{\text{reconstructed}}(t) = \sum_{i=1}^N \alpha_i S_i(t) \quad \text{with} \quad \alpha_i = M \cdot e \, v_{d,i} \, A_{\text{tube}} \, \Delta z
\tag{3.11}
\]

The vector \(\mathbf{\alpha} \in \mathbb{R}^N\) is the **readout vector**. It maps the hidden state \(\mathbf{S}\) to the observable output \(y\).

#### 3.3 The Witness Contract: Non‑Invasive Measurement

The Duotronics Witness Contract requires that a measurement be:

1. **Non‑invasive:** The act of measuring does not significantly perturb the system state.
2. **Independently verifiable:** The measurement can be cross‑checked by an independent method.
3. **Faithful:** The measured signal is a deterministic, known function of the state.

The inductive pickup satisfies these requirements as follows:

**Non‑invasiveness.**  
The pickup coil is galvanically isolated from the plasma. There is no physical electrical contact. The magnetic coupling is reciprocal: the plasma induces a voltage in the pickup, and (in principle) a current in the pickup would induce a magnetic field in the plasma. However, the measurement circuit is designed with a very high input impedance (typically >1 MΩ for the integrator input). The current flowing in the pickup coil is therefore minuscule (\(I_{\text{pickup}} = V_{\text{sense}} / Z_{\text{in}} \sim \text{mV} / \text{MΩ} \sim \text{nA}\)). The magnetic field produced by this nanoamp‑level current is utterly negligible compared to the rotor's permanent magnets (~0.1 T) and the stator coils.

Furthermore, the energy extracted from the plasma by the measurement is:

\[
P_{\text{extracted}} = I_{\text{pickup}}^2 \cdot R_{\text{coil}} \sim (10^{-9})^2 \cdot 10 \sim 10^{-17} \text{ W}
\]

while the plasma dissipates 5-50 W. The fractional perturbation is \(\sim 10^{-18}\)-truly negligible.

**Independent verifiability.**  
The witness signal can be cross‑checked against a conventional shunt resistor measurement (a small, precision resistor in the HV return path) during calibration. Once the mutual inductance \(M\) is calibrated, the integrated pot‑core signal should match the shunt measurement to within the combined uncertainty of the two methods. The falsification test in Section 5.4 formalises this check.

**Faithfulness.**  
The mapping \(\mathbf{S} \mapsto y\) is linear and deterministic (to the extent that the drift velocity \(v_d\) is known and stable). The calibration procedure (Section 9.2 of CPB‑COMP‑001) determines the exact proportionality constant.

#### 3.4 Summary of Axiom III

**Proposed Correspondence (formal):**  
The plasma current \(I(t)\) is a linear functional of the state vector \(\mathbf{S}(t)\). The pot‑core inductive pickup measures \(dI/dt\) with negligible back‑action. Integration recovers \(I(t) = \mathbf{\alpha}^T \mathbf{S}(t)\), providing a faithful, non‑invasive readout of the computation.

**Physical mechanism:**
- Plasma current = sum of local convective + displacement currents
- Mutual inductance \(M\) couples plasma (primary) to pot‑core pickup (secondary)
- Sensed voltage \(V_{\text{sense}} = -M \, dI/dt\)
- Integration yields \(y(t) = I(t)\)

**Key quantities:**
- Mutual inductance \(M \sim 10\text{-}100 \text{ µH}\) (design‑dependent)
- Pickup turns \(N = 50\text{-}200\)
- Measurement bandwidth: limited by integrator and coil self‑resonance (~100 kHz-1 MHz)
- Back‑action: energy extraction \(< 10^{-15} \text{ W}\), negligible relative to plasma power

**Experimental tests:** See Section 5.4, Axiom III falsification.

---

### 4. Axiom IV: Temporal Hierarchy (Separating Parameters from State)

#### 4.1 Intuitive Statement

A neural network has two distinct phases: **training** (where the weights are adjusted) and **inference** (where the fixed weights are used to process new inputs). These phases operate on very different timescales. Training might take hours or days; inference takes milliseconds.

The CPB exhibits an analogous separation, but rooted in physics rather than software. The rotor and mist have mechanical inertia; they can't change speed instantly. The plasma, by contrast, responds to HV pulses on microsecond timescales. This means we can use the rotor speed to set the "weights" (the \(\mathbf{W}\) matrix) relatively slowly, while the plasma processes a rapid sequence of inputs.

This temporal hierarchy is not an accident; it's a consequence of the large mass difference between the rotor (grams) and the electrons (\(10^{-30}\) kg). The system naturally separates into a slow parameter space and a fast state space.

#### 4.2 Characteristic Timescales

**Slow timescales (parameter updates).**  

| Process | Timescale | Physics |
|---------|-----------|---------|
| Rotor spin‑up / spin‑down | 10-100 ms | Rotational inertia: \(I_{\text{rotor}} \approx 2.7 \times 10^{-4} \text{ kg·m}^2\), motor torque \(T_{\text{motor}} \sim 0.1 \text{ N·m}\) |
| Mist flow establishment | 1-5 ms | Advection time \(L_{\text{annulus}} / v_{\text{mist}} \sim 0.08 / 50 \sim 1.6 \text{ ms}\) |
| Thermal equilibrium of rotor | 1-10 s | Heat capacity of aluminum rotor, radiative cooling |
| Mist concentration stabilisation | 0.1-1 s | Nebuliser response, droplet transport |

The fastest parameter change we can make is a rotor speed adjustment, which takes \(\sim 10 \text{ ms}\) to settle. This sets the minimum time for a "training epoch"-if we want to test a new \(\mathbf{W}\) matrix.

**Fast timescales (state evolution).**  

| Process | Timescale | Physics |
|---------|-----------|---------|
| Electron impact ionisation | 0.1-1 ns | Electron collision frequency \(\nu_{\text{coll}} \sim 10^{10} \text{ s}^{-1}\) |
| Electron energy relaxation | 1-10 ns | Energy exchange with neutrals |
| Sheath formation | 0.1-1 µs | Ion transit across sheath |
| Ion acoustic transit | 80 µs | \(L / c_s\), \(c_s \sim 1000 \text{ m/s}\) |
| Neutral gas pressure equilibration | 0.5-2 ms | Acoustic transit, multiple reflections |

The fastest plasma process is electron impact ionisation at \(\sim 0.1 \text{ ns}\). However, the **macroscopic** state of the plasma-the density profile, the electric field distribution, the current-evolves on the ion acoustic timescale of \(\sim 80 \text{ µs}\). This is the relevant timescale for state updates.

**The separation ratio.**  
The ratio of the slowest parameter timescale to the fastest state timescale is:

\[
\frac{\tau_{\text{slow}}}{\tau_{\text{fast}}} \sim \frac{10 \text{ ms}}{80 \text{ µs}} \approx 125
\]

There are over two orders of magnitude between them. This is a comfortable separation: the plasma state can be updated many times before the weight matrix changes appreciably.

#### 4.3 Proposed Clock Cycle

We propose the following operational interpretation:

**Discrete time index \(k\):** Each HV pulse defines a time step. The pulse is applied at \(t_k\), and the plasma responds. After a waiting period \(\Delta t_{\text{clock}} \ge \tau_{\text{acoustic}} \approx 80 \text{ µs}\), the plasma has relaxed to its new quasi‑steady state. The pot‑core pickup samples the current at this moment, yielding \(y_k\).

**State update equation:**
\[
\mathbf{S}_{k+1} = f(\mathbf{W} \cdot \mathbf{S}_k + \mathbf{U} \cdot u_k + \mathbf{b})
\tag{4.1}
\]

where:
- \(\mathbf{S}_k\) is the state vector just after the \(k\)-th pulse,
- \(u_k\) is the amplitude or shape of the \(k\)-th HV pulse,
- \(\mathbf{W}\) is fixed during the inner loop,
- \(f\) is the Townsend activation.

**Inner loop (inference):**  
Apply a sequence of \(M\) HV pulses \(u_1, u_2, \dots, u_M\) with spacing \(\Delta t_{\text{clock}}\). Record the output sequence \(y_1, y_2, \dots, y_M\). This takes \(M \cdot \Delta t_{\text{clock}}\) seconds. For \(M = 100\) and \(\Delta t_{\text{clock}} = 100 \text{ µs}\), the total inference time is 10 ms.

**Outer loop (parameter update / training):**  
Adjust the rotor speed \(\omega\) (which changes \(\mathbf{W}\)). Wait for the mist flow to stabilise (\(\sim 5 \text{ ms}\)). Repeat the inner loop. Compare the output sequence to a target. Adjust \(\omega\) again. This is the physical analogue of a training epoch.

#### 4.4 Limitations and Caveats

**Not a perfect separation.**  
The separation of timescales is useful but not absolute. Fast mist turbulence (e.g., droplet density fluctuations) can introduce noise into \(\bar{v}_z\) on timescales of 100 µs-1 ms, overlapping with the inference timescale. This noise acts as a multiplicative perturbation on \(\mathbf{W}\) and may degrade the reproducibility of the computation.

**Incomplete relaxation.**  
If the HV pulse spacing \(\Delta t_{\text{clock}}\) is shorter than \(\tau_{\text{acoustic}}\), the plasma does not fully relax between pulses. The state at step \(k+1\) then depends not only on \(\mathbf{S}_k\) and \(u_k\) but also on the residual transients from previous pulses. This introduces longer‑range temporal dependencies-which might actually be beneficial for reservoir computing (increased memory) but violates the simple discrete‑time RNN model.

**Rotor control bandwidth.**  
The rotor speed cannot be changed arbitrarily fast. The AMB drive and motor controller have a finite bandwidth (typically 100-500 Hz for the speed control loop). Rapid online adaptation of \(\mathbf{W}\)-e.g., for reinforcement learning-may be slower than the ideal outer loop suggests.

**Alternative operational modes.**  
The hierarchical interpretation proposed here is **one of several possible operational modes**. The reservoir computing framework (CPB‑COMP‑001) does not require strict timescale separation; it treats the entire system as a continuous‑time reservoir and only samples the output. The hierarchical mode is proposed as a way to make contact with the SRNN formalism; it is not the only way to use the hardware.

#### 4.5 Summary of Axiom IV

**Proposed Correspondence (formal):**  
The CPB system exhibits a useful separation of timescales: the mist flow and rotor speed determine \(\mathbf{W}\) on millisecond timescales, while the plasma state \(\mathbf{S}\) responds to HV pulses on microsecond timescales. This allows the system to be operated with an outer loop (parameter update) and an inner loop (state inference), analogous to training and inference in a neural network.

**Key quantities:**
- Separation ratio \(\tau_{\text{slow}} / \tau_{\text{fast}} \sim 125\)
- Proposed clock spacing \(\Delta t_{\text{clock}} \ge 80 \text{ µs}\)
- Inner loop duration for 100 steps: \(\sim 10 \text{ ms}\)
- Outer loop update: \(\sim 10\text{-}100 \text{ ms}\) per epoch

**Experimental tests:** See Section 5.4, Axiom IV falsification.

---

### 5. Extended Derivations and Supplementary Material

This section provides additional mathematical detail to support the four axioms.

#### 5.1 Full Derivation of the Tridiagonal Matrix \(\mathbf{W}\)

*(This section is expanded from the earlier draft, with additional intermediate steps and commentary.)*

**Step 1: The 1D convection‑diffusion equation.**  
We start from the conservation of mass for the neutral gas in one spatial dimension:

\[
\frac{\partial \rho}{\partial t} + \frac{\partial}{\partial z}(\rho v_z) = \frac{\partial}{\partial z}\left( \nu \rho \frac{\partial \rho}{\partial z} \right) + S
\tag{5.1}
\]

For small density perturbations around a mean density \(\rho_0\), and with a constant mean velocity \(\bar{v}_z\), this linearises to:

\[
\frac{\partial \rho}{\partial t} + \bar{v}_z \frac{\partial \rho}{\partial z} = \nu \frac{\partial^2 \rho}{\partial z^2} + S
\tag{5.2}
\]

which is Equation (2.1).

**Step 2: Finite‑volume discretisation.**  
We partition the domain \([0, L]\) into \(N\) cells of equal width \(\Delta z\). The cell centres are \(z_i = (i - 1/2)\Delta z\) for \(i = 1, \dots, N\). The cell faces are at \(z_{i-1/2} = (i-1)\Delta z\) and \(z_{i+1/2} = i\Delta z\).

The finite‑volume method integrates (5.2) over cell \(i\):

\[
\frac{d}{dt} \int_{z_{i-1/2}}^{z_{i+1/2}} \rho \, dz + \bar{v}_z \left[ \rho(z_{i+1/2}) - \rho(z_{i-1/2}) \right] = \nu \left[ \left. \frac{\partial \rho}{\partial z} \right|_{z_{i+1/2}} - \left. \frac{\partial \rho}{\partial z} \right|_{z_{i-1/2}} \right] + \int S \, dz
\tag{5.3}
\]

Defining the cell‑averaged density \(\rho_i = \frac{1}{\Delta z} \int \rho \, dz\):

\[
\Delta z \frac{d\rho_i}{dt} + \bar{v}_z (\rho_{i+1/2} - \rho_{i-1/2}) = \nu \left( \left. \frac{\partial \rho}{\partial z} \right|_{i+1/2} - \left. \frac{\partial \rho}{\partial z} \right|_{i-1/2} \right) + \Delta z \, S_i
\tag{5.4}
\]

**Step 3: Reconstruction and flux evaluation.**  
For the convective flux, we use first‑order upwind reconstruction. Since \(\bar{v}_z > 0\), the value at the left face of cell \(i\) is the cell‑averaged value from cell \(i-1\):

\[
\rho_{i-1/2} = \rho_{i-1}
\tag{5.5}
\]

For the diffusive flux, we use central differencing:

\[
\left. \frac{\partial \rho}{\partial z} \right|_{i-1/2} \approx \frac{\rho_i - \rho_{i-1}}{\Delta z}
\tag{5.6}
\]

Substituting:

\[
\Delta z \frac{d\rho_i}{dt} + \bar{v}_z (\rho_i - \rho_{i-1}) = \nu \left( \frac{\rho_{i+1} - \rho_i}{\Delta z} - \frac{\rho_i - \rho_{i-1}}{\Delta z} \right) + \Delta z \, S_i
\tag{5.7}
\]

Dividing by \(\Delta z\):

\[
\frac{d\rho_i}{dt} + \frac{\bar{v}_z}{\Delta z} (\rho_i - \rho_{i-1}) = \frac{\nu}{\Delta z^2} (\rho_{i+1} - 2\rho_i + \rho_{i-1}) + S_i
\tag{5.8}
\]

Moving the convective term to the RHS:

\[
\frac{d\rho_i}{dt} = -\frac{\bar{v}_z}{\Delta z} (\rho_i - \rho_{i-1}) + \frac{\nu}{\Delta z^2} (\rho_{i+1} - 2\rho_i + \rho_{i-1}) + S_i
\tag{5.9}
\]

**Step 4: Extracting the matrix elements.**  
Collecting coefficients:

- Coefficient of \(\rho_{i-1}\): \(+\frac{\bar{v}_z}{\Delta z} + \frac{\nu}{\Delta z^2}\)
- Coefficient of \(\rho_i\): \(-\frac{\bar{v}_z}{\Delta z} - \frac{2\nu}{\Delta z^2}\)
- Coefficient of \(\rho_{i+1}\): \(+\frac{\nu}{\Delta z^2}\)

These are precisely the tridiagonal entries \(W_{i,i-1}\), \(W_{i,i}\), and \(W_{i,i+1}\) defined in Section 2.2.

**Step 5: Verification of conservation.**  
The sum of the weights in each row (excluding boundaries) is:

\[
W_{i,i-1} + W_{i,i} + W_{i,i+1} = \left( \frac{\bar{v}_z}{\Delta z} + \frac{\nu}{\Delta z^2} \right) + \left( -\frac{\bar{v}_z}{\Delta z} - \frac{2\nu}{\Delta z^2} \right) + \left( \frac{\nu}{\Delta z^2} \right) = 0
\tag{5.10}
\]

This means that, in the absence of sources and with periodic boundary conditions, the total mass \(\sum_i \rho_i\) is conserved. The convection‑diffusion operator is conservative, as required by physics.

#### 5.2 Mutual Inductance Calculation with Detailed Geometry

**Geometry of the pot‑core.**  
A typical pot‑core consists of two ferrite halves that clamp around the drift tube. The core has a central hole (for the tube), an outer rim, and a winding window. The magnetic circuit can be modelled as a toroid with a small air gap.

Parameters:
- Core cross‑sectional area \(A_{\text{core}} = 50 \text{ mm}^2 = 5 \times 10^{-5} \text{ m}^2\)
- Mean magnetic path length (ferrite) \(l_{\text{ferrite}} \approx 60 \text{ mm}\)
- Air gap length (total, both interfaces) \(l_{\text{gap}} = 0.2 \text{ mm} = 2 \times 10^{-4} \text{ m}\)
- Ferrite relative permeability \(\mu_r = 3000\) (typical for MnZn power ferrite at 4 kHz)
- Number of pickup turns \(N = 100\)

**Reluctance model.**  
The total magnetic reluctance is the sum of the ferrite reluctance and the gap reluctance:

\[
\mathcal{R}_{\text{total}} = \mathcal{R}_{\text{ferrite}} + \mathcal{R}_{\text{gap}} = \frac{l_{\text{ferrite}}}{\mu_r \mu_0 A_{\text{core}}} + \frac{l_{\text{gap}}}{\mu_0 A_{\text{core}}}
\tag{5.11}
\]

\[
\mathcal{R}_{\text{ferrite}} = \frac{0.06}{3000 \cdot 4\pi \times 10^{-7} \cdot 5 \times 10^{-5}} = \frac{0.06}{1.88 \times 10^{-7}} \approx 3.2 \times 10^5 \text{ A/Wb}
\]

\[
\mathcal{R}_{\text{gap}} = \frac{2 \times 10^{-4}}{4\pi \times 10^{-7} \cdot 5 \times 10^{-5}} = \frac{2 \times 10^{-4}}{6.28 \times 10^{-11}} \approx 3.18 \times 10^6 \text{ A/Wb}
\]

The gap reluctance is \(\sim 10\) times larger than the ferrite reluctance, so the gap dominates. The total reluctance is \(\mathcal{R}_{\text{total}} \approx 3.5 \times 10^6 \text{ A/Wb}\).

**Flux and inductance.**  
The magnetomotive force (MMF) produced by the plasma current \(I\) (acting as a single turn) is \(\mathcal{F} = I\). The flux is \(\Phi = \mathcal{F} / \mathcal{R}_{\text{total}} = I / \mathcal{R}_{\text{total}}\). The flux linkage for the \(N\)‑turn pickup is \(\lambda = N \Phi = N I / \mathcal{R}_{\text{total}}\). Therefore:

\[
M = \frac{\lambda}{I} = \frac{N}{\mathcal{R}_{\text{total}}} \approx \frac{100}{3.5 \times 10^6} \approx 2.86 \times 10^{-5} \text{ H} = 28.6 \text{ µH}
\tag{5.12}
\]

This is comfortably in the 10-100 µH range.

**Signal amplitude.**  
For a plasma current of \(I = 1 \text{ mA}\) changing over \(\Delta t = 10 \text{ µs}\):

\[
V_{\text{sense}} = M \frac{\Delta I}{\Delta t} \approx 28.6 \times 10^{-6} \cdot \frac{10^{-3}}{10^{-5}} = 2.86 \text{ mV}
\tag{5.13}
\]

This is easily measurable with a low‑noise instrumentation amplifier (e.g., INA128 with 1 nV/√Hz input noise).

#### 5.3 Eigenmode Analysis of the Drift Tube

**Why eigenmodes?**  
The finite‑volume discretisation is convenient for connecting to the Navier‑Stokes equation, but it's not the only representation. The axial eigenmodes provide a complementary view: they are the "natural" patterns of oscillation of the gas column, analogous to the harmonics of an organ pipe.

**Setup.**  
Consider small pressure perturbations \(p'(z, t)\) in a stationary gas column (no mean flow, for simplicity). The linearised wave equation is:

\[
\frac{\partial^2 p'}{\partial t^2} = c_s^2 \frac{\partial^2 p'}{\partial z^2}
\tag{5.14}
\]

**Boundary conditions.**
- At \(z = 0\) (emitter end): The electrode is a rigid surface. The gas velocity must vanish: \(v_z(0) = 0\). By the linearised momentum equation, \(\partial_z p' = 0\) at \(z = 0\).
- At \(z = L\) (collector end): The tube opens into the low‑pressure collector region. The pressure perturbation must match the ambient, so \(p'(L) = 0\). This is an idealisation; in practice, the open end has a finite radiation impedance, but the pressure‑release condition is the leading‑order approximation.

**Separation of variables.**  
Assume \(p'(z, t) = P(z) \cdot T(t)\). The wave equation becomes:

\[
\frac{\ddot{T}}{T} = c_s^2 \frac{P''}{P} = -\omega^2
\tag{5.15}
\]

The spatial equation is \(P'' + k^2 P = 0\) with \(k = \omega / c_s\). Solutions are:

\[
P(z) = C_1 \cos(kz) + C_2 \sin(kz)
\tag{5.16}
\]

Apply boundary conditions:
- \(P'(0) = 0 \Rightarrow -C_1 k \sin(0) + C_2 k \cos(0) = 0 \Rightarrow C_2 = 0\).
- \(P(L) = 0 \Rightarrow \cos(kL) = 0 \Rightarrow kL = (2n-1)\pi/2\) for \(n = 1, 2, 3, \dots\)

**Eigenmodes and eigenfrequencies.**
\[
\Phi_n(z) = \cos\left( \frac{(2n-1)\pi z}{2L} \right), \quad \omega_n = \frac{(2n-1)\pi c_s}{2L}, \quad f_n = \frac{(2n-1) c_s}{4L}
\tag{5.17}
\]

For \(L = 0.08 \text{ m}\) and \(c_s = 1000 \text{ m/s}\) (ion acoustic speed in weakly ionised plasma):

| \(n\) | \(f_n\) (kHz) | \(\lambda_n\) (mm) | Nodes |
|------|---------------|------------------|-------|
| 1 | 3.125 | 160 | 0 |
| 2 | 9.375 | 53.3 | 1 |
| 3 | 15.625 | 32.0 | 2 |
| 4 | 21.875 | 22.9 | 3 |
| 5 | 28.125 | 17.8 | 4 |
| 6 | 34.375 | 14.5 | 5 |

**Effect of mean flow.**  
With a mean axial velocity \(\bar{v}_z\), the eigenfrequencies are Doppler‑shifted:

\[
f_n^{\text{shifted}} = f_n \left( 1 - \frac{\bar{v}_z^2}{c_s^2} \right)^{-1/2} \approx f_n \left( 1 + \frac{\bar{v}_z^2}{2c_s^2} \right) \quad \text{for } \bar{v}_z \ll c_s
\tag{5.18}
\]

For \(\bar{v}_z \approx 50 \text{ m/s}\) and \(c_s \approx 1000 \text{ m/s}\), the correction is \(\sim 0.125\%\), negligible.

**Mode orthogonality.**  
The eigenmodes are orthogonal with respect to the standard inner product:

\[
\int_0^L \Phi_n(z) \Phi_m(z) \, dz = \begin{cases} L/2 & n = m \\ 0 & n \neq m \end{cases}
\tag{5.19}
\]

This allows the state vector to be expressed in the modal basis:

\[
\rho(z, t) = \sum_{n=1}^\infty A_n(t) \Phi_n(z), \quad A_n(t) = \frac{2}{L} \int_0^L \rho(z, t) \Phi_n(z) \, dz
\tag{5.20}
\]

**Choosing \(N\) in the modal basis.**  
The HV pulse bandwidth sets the maximum mode number that can be excited. For a pulse of duration \(\Delta t\), the excitation spectrum has significant content up to \(f_{\max} \approx 1/(2\Delta t)\). The number of resolvable modes is the largest \(n\) such that \(f_n < f_{\max}\):

\[
N_{\text{modes}} \approx \frac{4 L f_{\max}}{c_s} + \frac{1}{2}
\tag{5.21}
\]

For \(\Delta t = 100 \text{ µs}\) (\(f_{\max} = 5 \text{ kHz}\)): \(N_{\text{modes}} \approx (4 \times 0.08 \times 5000 / 1000) + 0.5 \approx 1.6 + 0.5 \approx 2\). Only the fundamental and possibly the second mode are accessible.

For \(\Delta t = 10 \text{ µs}\) (\(f_{\max} = 50 \text{ kHz}\)): \(N_{\text{modes}} \approx 16 + 0.5 \approx 16\). Many modes are accessible.

#### 5.4 Falsification Criteria (Experimental Protocol)

A proposed semantics is only meaningful if it is falsifiable. The following experiments are designed to test whether the physical system behaves consistently with the proposed correspondence. Failure of these tests does not invalidate the CPB platform; it indicates that the particular simplified mapping described here does not hold under the tested conditions.

**Test I‑1: Quasi‑1D Validation.**  
*Objective:* Verify that transverse modes are not significantly excited.  
*Method:* Image the plasma column from the side using a high‑speed camera with a narrow bandpass filter (e.g., isolating a nitrogen or argon emission line). Take a time‑averaged image and a sequence of instantaneous images during a discharge pulse.  
*Analysis:* Extract the radial intensity profile at several axial positions. Fit to a Bessel function \(J_0(\lambda_{01} r)\) (the fundamental axisymmetric mode). Compute the residual after subtracting the axisymmetric fit.  
*Pass criterion:* The RMS residual is less than 20% of the mean intensity across all axial positions and time frames.  
*Failure implication:* If significant non‑axisymmetric structure (spiral patterns, off‑centre bright spots, azimuthal asymmetries) is observed, the quasi‑1D assumption is violated. The dimensionality of the state space is larger than \(N\), and the simple tridiagonal coupling model may not apply.

**Test II‑1: Tridiagonal Structure Validation.**  
*Objective:* Test whether the coupling between axial cells is predominantly nearest‑neighbour.  
*Method:* With the plasma in a steady glow (no HV pulses), apply a small‑signal sinusoidal perturbation to the electrode voltage at a frequency \(f_{\text{pert}}\). Measure the amplitude and phase of the resulting plasma current modulation at the perturbation frequency. Sweep \(f_{\text{pert}}\) from 100 Hz to 50 kHz.  
*Analysis:* Fit the measured transfer function \(H(\omega) = \tilde{I}(\omega) / \tilde{V}(\omega)\) to the Laplace transform of the tridiagonal model (which, for a uniform tube, has a known closed form).  
*Pass criterion:* The fitted model captures >80% of the variance (R² > 0.8) in the magnitude and phase of \(H(\omega)\).  
*Failure implication:* If the transfer function contains sharp resonances at frequencies other than the predicted axial eigenmodes, or if the phase response indicates long‑range (non‑nearest‑neighbour) coupling, the tridiagonal model is insufficient.

**Test II‑2: Townsend Activation Validation.**  
*Objective:* Verify that the measured ionisation rate follows the Townsend form.  
*Method:* Vary the DC electrode voltage while measuring the plasma current and the optical emission intensity. From the current‑voltage characteristic, extract the effective Townsend coefficient \(\alpha_{\text{eff}}\) as a function of \(E/p\). (This requires an independent measurement of the gas pressure and an estimate of the electric field from the voltage and sheath drop.)  
*Analysis:* Fit \(\alpha_{\text{eff}}(E/p)\) to the Townsend formula \(A p \exp(-B p / E)\).  
*Pass criterion:* The fitted curve captures >85% of the variance (R² > 0.85) over the operating range of \(E/p\).  
*Failure implication:* If the data deviate significantly from the Townsend form (e.g., due to multi‑step ionisation, Penning effects, or secondary emission), the activation function is not simply exponential, and the element‑wise model requires revision.

**Test III‑1: Witness Faithfulness.**  
*Objective:* Verify that the integrated pot‑core signal faithfully reproduces the plasma current.  
*Method:* Install a calibrated shunt resistor (e.g., 100 Ω, 0.1% tolerance) in the HV return path. Simultaneously record the shunt voltage \(V_{\text{shunt}}(t)\) and the integrated pot‑core signal \(y(t)\) during a sequence of HV pulses with varying amplitudes and repetition rates.  
*Analysis:* Compute the ratio \(R(t) = y(t) / (V_{\text{shunt}}(t) / R_{\text{shunt}})\).  
*Pass criterion:* The ratio \(R(t)\) remains within 0.95-1.05 for 95% of the data points across all tested conditions.  
*Failure implication:* Deviations >5% indicate either a calibration error in \(M\), a nonlinearity in the magnetic core (saturation), or a frequency‑dependent effect (the integrator does not perfectly invert the differentiator). Systematic investigation is required.

**Test III‑2: Back‑Action Assessment.**  
*Objective:* Verify that the measurement does not perturb the plasma.  
*Method:* Operate the plasma at a fixed DC condition. Record the I‑V characteristic (current vs. voltage) with the pot‑core pickup connected normally. Then disconnect the pickup (open‑circuit the coil) and repeat the measurement.  
*Analysis:* Compare the two I‑V curves.  
*Pass criterion:* The two curves agree within the measurement uncertainty (e.g., <2% deviation in current at any given voltage).  
*Failure implication:* If connecting/disconnecting the pickup changes the discharge current, the measurement is loading the plasma-possibly by drawing power from the HV circuit through capacitive coupling, or by altering the resonant frequency of the electrode circuit.

**Test IV‑1: Temporal Hierarchy Validation.**  
*Objective:* Test whether the plasma relaxes between HV pulses.  
*Method:* Apply pairs of identical HV pulses with variable spacing \(\tau\). For each \(\tau\), record the plasma current response to the second pulse and compare it to the response to the first pulse (which serves as a baseline).  
*Analysis:* Compute the relative difference \(\Delta I(\tau) = |I_2 - I_1| / I_1\). Plot \(\Delta I\) vs. \(\tau\).  
*Pass criterion:* For \(\tau > 80 \text{ µs}\), \(\Delta I < 10\%\).  
*Failure implication:* If the second pulse response differs significantly from the first even for \(\tau > 100 \text{ µs}\), the plasma has long‑lived memory (e.g., metastable species, thermal transients) that violates the simple clock cycle assumption. This doesn't break the system-it just means the discrete‑time RNN model with short memory is not appropriate. A continuous‑time reservoir model (CPB‑COMP‑001) would be more suitable.

**Global Consistency Test.**  
*Objective:* Test whether the rotor speed controls \(\mathbf{W}\) as predicted.  
*Method:* Fix an input pulse sequence (e.g., a repeating pattern of two different pulse amplitudes). Run the sequence at three different rotor speeds: \(\omega_1, \omega_2 = 1.5\omega_1, \omega_3 = 2\omega_1\). Record the output sequences.  
*Analysis:* The tridiagonal model predicts that the output should change in a specific, deterministic way as \(\mathbf{W}\) scales with \(\omega\). In particular, the characteristic time for a density perturbation to be convected out of the tube is \(\tau_{\text{conv}} \propto 1/\omega\). The autocorrelation time of the output should scale inversely with \(\omega\).  
*Pass criterion:* The measured autocorrelation time scales as \(1/\omega\) to within ±20%.  
*Failure implication:* If the output does not change systematically with rotor speed, or if the changes are not consistent with the convection‑diffusion model, then the rotor is not functioning as the primary \(\mathbf{W}\) tuner, and the correspondence is broken.

---

### 6. Unified Correspondence Table

| Formal SRNN Element | Physical CPB Subsystem | Mathematical Expression | Axiom | Status |
| :--- | :--- | :--- | :--- | :--- |
| **State \(\mathbf{S}(t)\)** | Axial density/ionisation profile | \(\rho_i(t)\) or mode amplitudes \(A_n(t)\) | I | Approximate; assumes quasi‑1D |
| **Weight Matrix \(\mathbf{W}\)** | Mist convection + viscous diffusion | \(W_{i,i-1} = \frac{\bar{v}_z}{\Delta z} + \frac{\nu}{\Delta z^2}\), etc. (tridiagonal) | II | Leading‑order; neglects long‑range coupling |
| **Activation \(f\)** | Townsend ionisation | \(f(x) = A p \exp(-B p / E)\) | II | Element‑wise approx; neglects global coupling |
| **Input \(\mathbf{u}(t)\)** | HV pulse sequence | \(u_k = V_{\text{HV}}(t_k)\) | II | Direct mapping |
| **Bias \(\mathbf{b}\)** | Magnetic pre‑ionisation background | Baseline electron density from B‑field | II | To be characterised |
| **Readout \(\mathbf{\alpha}\)** | Pot‑core inductive pickup geometry | \(\alpha_i \propto M \cdot e v_d A_{\text{tube}} \Delta z\) | III | Linear; requires calibration |
| **Witness \(y(t)\)** | Integrated sense voltage | \(y(t) = \frac{1}{M} \int V_{\text{sense}} dt\) | III | Faithful if tests pass |
| **Clock / Iteration** | HV pulse spacing | \(\Delta t_{\text{clock}} \ge \tau_{\text{acoustic}} \approx 80 \text{ µs}\) | IV | Valid if relaxation test passes |
| **Parameter Update** | Rotor speed variation | \(\mathbf{W} \propto \text{RPM}\) | IV | Valid if consistency test passes |

---

### 7. Relationship to the Broader Duotronics Architecture

This document is a **companion theoretical note** to the primary CPB documentation. Its relationship to other components is:

- **CPB‑ENG‑001 (Hardware Spec):** Defines the physical geometry, materials, operating parameters. This semantics document takes that hardware as given and proposes an interpretive layer on top.
- **IMLT White Paper:** Describes the integrated mag‑lev turbine in engineering detail. The rotor's role as \(\mathbf{W}\)‑tuner and the pot‑core as readout are directly derived from that document.
- **CPB‑COMP‑001 (Reservoir Computing Framework):** The primary computational document. The SRNN semantics proposed here are complementary: the reservoir framework treats the internal dynamics as a black box; this document attempts to open the box. If the semantics are validated, they can inform reservoir design (e.g., optimal \(N\), choice of \(\Delta t_{\text{clock}}\)).
- **Witness Contracts:** Axiom III directly addresses witness requirements. The falsification tests provide an experimental verification protocol.
- **Bus Protocol:** Inter‑node communication is not addressed here. Extending the semantics to multi‑node networks requires coupling matrices \(\mathbf{G}_{ij}\) (see CPB‑COMP‑001, Section 3.2).
- **Conformance Harness:** The falsification tests in Section 5.4 are designed to be automatable and can be integrated into the harness.

---

### 8. Summary and Path Forward

We have proposed a candidate physical semantics linking the coaxial Venturi geometry of the CPB platform to the formalism of Self‑Referential Recurrent Neural Networks. The correspondence is built on four axioms:

1. **Quasi‑1D dynamics** → finite‑dimensional state vector \(\mathbf{S}(t) \in \mathbb{R}^N\)
2. **Convection‑diffusion** → tridiagonal weight matrix \(\mathbf{W}\) (tunable via rotor RPM)
3. **Inductive pickup** → linear readout \(\mathbf{\alpha}\) with negligible back‑action
4. **Temporal hierarchy** → separable parameter update (slow) and state inference (fast)

Each axiom is accompanied by explicit assumptions, limitations, and falsification criteria.

**This is a hypothesis, not a claim.** The experimental programme in CPB‑COMP‑001 (DC‑0 through DC‑10) is designed to characterise the system. The falsification tests in Section 5.4 of this document can be run in parallel with or as part of that programme. If the tests pass, the SRNN semantics provide a useful interpretative lens. If they fail, the hardware is not broken-the semantics are simply not the right lens, and the reservoir computing framework (which makes fewer assumptions about internal dynamics) remains valid.

The 2004 notebook sketch-a single rotor in the outer annulus, a clean inner tube, and an inductive pickup-contains the geometric kernel of all these ideas. Whether that geometry can support the computational abstractions proposed here is an experimental question. The semantics are now documented, derived to leading order, and explicitly falsifiable. The next step is measurement.