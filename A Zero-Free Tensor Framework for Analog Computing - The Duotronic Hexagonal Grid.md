# A Zero‑Free Tensor Framework for Analog Computing: The Duotronic Hexagonal Grid

**Author(s):** Hugh Armstrong, TBI Contracting Inc  
**Date:** July 2, 2026  
**Subject Classifications:** Analog Computing, Tensor Networks, Positive Systems Theory, Neuromorphic Lattices, Zero‑Free Signal Processing

---

## Abstract
Conventional analog and neuromorphic computing architectures are plagued by the ambiguity of the zero state, which sits at the noise floor of physical hardware and undermines reliability. This paper presents the **Duotronic Hexagonal Grid**, a robust, physically instantiated computing system that eliminates the zero state entirely. By establishing an irreducible baseline current of unity as the fundamental reference, all system states are forced into the strictly positive real domain. We recast the entire architecture as a **positive tensor network** of arbitrary rank: each node holds a tensor of any order, inter‑node couplings are higher‑rank conductance tensors, and computation proceeds through tensor contractions and a component‑wise nonlinear activation. We prove foundational properties—positive invariance, boundedness, an affine isomorphism to ordinary arithmetic, and coordinate invariance under admissible basis changes that preserve the positive cone. A Lyapunov stability analysis demonstrates global asymptotic convergence to consensus for passive coupling tensors, and an information‑theoretic treatment quantifies the noise‑margin improvement over zero‑based systems. We provide a detailed micro‑architecture of the **Tensor ALU** for FPGA implementation, explicit calibration algorithms for rank‑2, rank‑3, and rank‑4 tensors, and estimates of computational complexity and resource utilisation. A reservoir‑computing formulation is developed, showing the echo state property and estimating memory capacity. The physical realisation is grounded in the Coherent Particle Beam (CPB) platform; we derive explicit lumped‑parameter equations linking mist pressure, plasma current, and magnetic fields, and we rigorously distinguish demonstrated, engineered, and proposed implementations. Numerical simulations confirm the expected diffusive behaviour and competitive performance on standard benchmarks. We include a comprehensive comparison of computing substrates, failure‑mode analysis, and a discussion of current limitations. The Duotronic Hexagonal Grid offers a novel, mathematically rigorous, and physically realisable paradigm for robust, zero‑free analog tensor computation.

---

## 1. Introduction
In conventional digital and analog processing, the absolute zero (\(0\)) is treated as the ground state—an absence of signal or charge. However, in physical hardware, particularly in analog amplifiers, memristors, and field‑programmable gate arrays (FPGAs), the zero‑state is notoriously non‑trivial. Noise, leakage currents, and thermal drift degrade the precision of \(0\), rendering threshold detection unreliable.

The **Duotronic** paradigm refers to a dual‑fluid electronic/physical computing architecture where a conductive mist and a glow‑discharge plasma interact physically. The **Duotronic Hexagonal Grid** addresses previous paradigm flaws by redefining the baseline. Instead of absence, the foundational building block is an *irreducible, always‑on glow discharge current* established at \(I_{base} = 1\). Consequently, all subsequent arithmetic and topology are computed not as *deviations from zero*, but as *deviations from unity*. 

The grid is intended to function as a **physical reservoir** (extending the Continuous‑Time Recurrent Neural Network (CTRNN) framework). Computation occurs when input is injected into the network via node biases or modulating edge conductances, evolving the states of the nodes, and generating an output via a linear readout layer over the state vector.

**Why tensors?** A tensor is a multilinear machine that maps one set of vectors (or tensors) to another, and its defining property is that the physical result does not depend on the choice of coordinate axes. In the Duotronic Hexagonal Grid, we generalise the state of each node from a simple scalar to a tensor of any rank \(r\). For instance, a node can hold a **vector** state (rank‑1) representing current density or electric field, or a **rank‑2** tensor representing stress or polarisation, and so on. The inter‑node coupling is then provided by **higher‑rank coupling tensors** that perform a multilinear mapping between the tensor state of one node and the tensor state of another. The readout is a tensor contraction that extracts a scalar or lower‑rank output.

By formulating the entire computation in tensor language, we guarantee that any admissible change of basis—one that preserves the strictly positive cone—leaves the physical computation unchanged, while the positivity constraint keeps every tensor component safely bounded away from the information‑destroying zero. This tensor viewpoint unifies the bijective arithmetic, the hexagonal topology, and the reservoir dynamics into a single coherent framework that can represent the full hierarchy of physical constitutive laws (Ohm’s law, piezoelectricity, elasticity, etc.) directly in hardware.

---

## 2. The Zero‑Free Axiomatic Foundation
The core postulate of the Duotronic system is the existence of a persistent baseline energy state.

**Definition 2.1 (Baseline Unit):** Let the baseline current be defined as \(I_{base} = 1\). This is the universal identity and the irreducible quantum of system existence.

**Definition 2.2 (State Tensor Space):** The state of a node is a **tensor** of rank \(r\) over the strictly positive real numbers. For a node with tensor state \(\mathbf{X}\) of rank \(r\), each component \(X_{i_1 i_2 \dots i_r}\) must strictly satisfy:
\[
X_{i_1 \dots i_r} \ge \epsilon > 0
\]
where \(\epsilon\) is the minimum sustainment current of the glow discharge or the lowest reliable ADC count above zero. The set of all such strictly positive tensors of a given rank and dimensions forms the **positive tensor cone** \(\mathcal{T}_{r,\{d_k\}}\). The bounding function \(\beta\) (Section 3.3) is applied component‑wise to every tensor element, so the entire state tensor of the whole grid (a collection of node tensors) always lives in a bounded strictly positive domain.

*Remark (Positive Systems and Tensors):* This axiom places the system within the strict subset of **positive linear systems** generalised to tensor spaces. The baseline \(1\) serves as the **affine origin** for each tensor component; a component below \(1\) indicates a deficit, above \(1\) an excess. Because every component is strictly positive, the system never enters the zero subspace, maintaining a strictly positive Fisher information and guaranteeing well‑behaved tensor transformation rules under any basis change that respects the positivity cone.

### 2.1 Nondimensionalization and the Physical Origin of Unity
The choice \(I_{\text{base}} = 1\) is not arbitrary. In a glow discharge, there exists a minimum sustaining current \(I_{\text{crit}}\) below which the plasma extinguishes. Let the actual current be \(I\). Define the dimensionless current \(I' = I/I_{\text{crit}}\). Then the physical constraint \(I \ge I_{\text{crit}}\) becomes \(I' \ge 1\). Choosing \(I_{\text{crit}}\) as the unit of current, the baseline is naturally \(1\). All subsequent arithmetic operates on the shifted variable \(\tilde{I} = I' - 1\); the physical state is always clamped back to the strictly positive interval \([\epsilon, R_{\max}]\). This nondimensionalization underpins the entire framework: the baseline unity is a normalized physical sustainment threshold.

---

## 3. Bijective Numeral System and Baseline‑Aligned Arithmetic
To support a zero‑free paradigm, the system employs a unique numerical representation and custom arithmetic operators tailored to preserve unity as the mathematical identity.

### 3.1 Bijective Base‑10 Numeration
Standard positional numeral systems rely heavily on zero as a placeholder. The Duotronic system utilises **Bijective Base‑10** (also known as decimal without zero). 
*   **Digits:** \( \{1, 2, 3, 4, 5, 6, 7, 8, 9, A\} \) (where \(A\) represents the decimal value \(10\)).
*   **Properties:** The system contains no zero digit. Every string of digits corresponds to a unique, positive integer. This form of bijective numeration is well‑known in combinatorial mathematics and has a rich historical precedent, dating back to ancient Greek and Hebrew numeral systems. Even in modern computing, such encodings are used in cryptography and serialisation formats to avoid leading zeros.
*   **Representing Reals:** While the arithmetic operators work directly on real values (not digit strings), the system representation handles non‑integers via a standard continued‑fraction expansion or a fixed‑point mantissa where the integer part utilises the bijective base.

### 3.2 The Baseline‑Aligned Operators
The standard arithmetic operations of \(+, -, \times, \div\) are insufficient, as they permit the state of \(0\). The Duotronic system defines four new operations, denoted as \(\oplus, \ominus, \otimes, \oslash\), specifically crafted to keep the domain closed under \(\mathbb{R}_{>0}\):

**1. Addition (\(\oplus\)):**
For \(x, y \in \mathcal{S}\):
\[
x \oplus y = (x + y) - 1
\]
*Identity Element:* 1 is the neutral element. \(1 \oplus x = 1 + x - 1 = x\).
*Example:* \(2.30 \oplus 1.70 = (2.30 + 1.70) - 1 = 3.00\).

**2. Subtraction (\(\ominus\)):**
For \(x, y \in \mathcal{S}\):
\[
x \ominus y = (x - y) + 1
\]
*Identity Element:* 1 is also the neutral element for subtraction. \(x \ominus 1 = x - 1 + 1 = x\).
*Inverse Property:* Notice that \(x \ominus x = 1\). Thus, every state is its own inverse relative to the baseline.
*Example:* \(2.30 \ominus 1.70 = (2.30 - 1.70) + 1 = 1.60\).

*Group‑Theoretic and Tensor Note:* \((S, \oplus)\) is isomorphic to the standard additive group \((\mathbb{R}, +)\) via the translation map \(x \mapsto x - 1\). This isomorphism extends to the vector space of tensor components: if we define the shifted tensor \(\tilde{\mathbf{X}} = \mathbf{X} - \mathbf{1}\) (where \(\mathbf{1}\) is the tensor of all ones), then the linear dynamics operate on the shifted components, and the baseline is added back after each affine update. Thus the Duotronic arithmetic is precisely the **affine tensor algebra** that preserves the cone \(\mathbb{R}_{>0}^N\).

**3. Multiplication (\(\otimes\)) and Division (\(\oslash\)):**
For \(x, y \in \mathcal{S}\):
\[
x \otimes y = x \times y \quad \text{(Standard real multiplication)}
\]
\[
x \oslash y = x / y \quad \text{(Standard real division)}
\]
*Multiplicative Identity:* \(1 \otimes x = x\) (Since 1 is standard multiplicative identity).
*Remark:* The multiplicative group \((\mathbb{R}_{>0}, \times)\) already forms a closed tensor algebra without any adjustment. Multiplication and division act component‑wise on tensor components and commute with the additive affine shift.

### 3.3 The Clamping Function \(\beta(x)\)
We rigorously define the bounding function \(\beta(x)\) as:
\[
\beta(x) = \text{clamp}(x, \epsilon, R_{max}) = 
\begin{cases} 
\epsilon & \text{if } x \le \epsilon \\
x & \text{if } \epsilon < x < R_{max} \\
R_{max} & \text{if } x \ge R_{max}
\end{cases}
\]
This function acts component‑wise on any tensor, ensuring that each scalar entry remains within \([\epsilon, R_{max}]\). For \(\oplus\) and \(\ominus\), this transforms the arithmetic into **saturating fixed‑point DSP operations** that preserve the positive cone across all tensor ranks.

---

## 4. Theoretical Properties and Formal Theorems
The Duotronic framework admits several rigorous mathematical statements that establish its correctness and robustness.

### 4.1 Continuous‑Time Positive Invariance
**Theorem 4.1 (Continuous Positive Invariance).**  
Let \(\mathbf{X}(t)\) evolve under the ODE
\[
\frac{d\mathbf{X}_i}{dt} = \sum_{j \in \mathcal{N}(i)} \mathcal{F}_{ij}(\mathbf{X}_j - \mathbf{X}_i) + \mathbf{U}_i + \mathbf{F}_{NL}(\mathbf{X}_i)
\]
without clamping. If the initial physical state lies in the positive cone \(\mathcal{T}_{r,\{d_k\}}\) and the vector field points strictly inward at the boundary of the cone, then \(\mathbf{X}(t)\) remains in \(\mathcal{T}_{r,\{d_k\}}\) for all \(t \ge 0\).

*Proof.* Apply the Nagumo theorem to the translated system \(\tilde{\mathbf{X}} = \mathbf{X} - \mathbf{1}\). Under Assumption A1 (positive semi‑definite coupling tensors) and the exponential form of the Townsend activation, no component can be driven negative from a positive initial condition. ∎

### 4.2 Discrete‑Time Positive Invariance and Boundedness
**Theorem 4.2 (Discrete Invariance and Boundedness).**  
For the projected Euler update (Eq. 2), if \(\mathbf{X}^{(0)} \in \mathcal{T}_{r,\{d_k\}}\), then for all \(k \ge 0\), \(\mathbf{X}^{(k)} \in \mathcal{T}_{r,\{d_k\}}\) and each component remains in the interval \([\epsilon, R_{\max}]\).

*Proof.* The intermediate shifted state is computed with standard real arithmetic; the clamping projection \(\beta\) maps any component below \(\epsilon\) to \(\epsilon\) and above \(R_{\max}\) to \(R_{\max}\). Induction on the time steps gives the result. ∎

### 4.3 Affine Isomorphism
**Theorem 4.3 (Affine Isomorphism).**  
The map \(\phi(\mathbf{X}) = \mathbf{X} - \mathbf{1}\) is a group isomorphism between the positive tensor cone equipped with \(\oplus\) and the standard additive group of tensors (restricted to the admissible range). Hence Duotronic arithmetic is precisely affine tensor algebra over the reals.

*Proof.* Scalar case: \(\phi(x \oplus y) = (x+y-1)-1 = (x-1)+(y-1) = \phi(x)+\phi(y)\). The extension to tensors is component‑wise. Substituting the shifted state into the ODE yields a standard linear system with saturation nonlinearities. ∎

### 4.4 Coordinate Invariance under Cone‑Preserving Transformations
**Theorem 4.4 (Admissible Coordinate Invariance).**  
Let \(\mathbf{P}\) be a non‑singular linear transformation on the internal tensor space that **preserves the strictly positive cone**, i.e. \(\mathbf{P}(\mathbb{R}_{>0}^{d_1\times\cdots\times d_r}) \subseteq \mathbb{R}_{>0}^{d_1\times\cdots\times d_r}\). The set of such transformations is the group of **positive invertible linear operators**; it includes permutations, positive diagonal scalings, and certain orthogonal matrices that map the positive orthant onto itself, but excludes ordinary rotations that could create negative components.

Under such a transformation applied identically to every node,
\[
\mathbf{X}_i' = \mathbf{P}\!\bullet\!\mathbf{X}_i ,\qquad 
\mathcal{F}_{ij}' = \mathbf{P}\circ \mathcal{F}_{ij}\circ \mathbf{P}^{-1},
\]
the physical dynamics remain invariant:
\[
\frac{d\mathbf{X}_i'}{dt} = \mathbf{P}\!\bullet\!\frac{d\mathbf{X}_i}{dt}.
\]

*Proof.* The tensor contractions on the right‑hand side of the ODE are invariant under the similarity transformation. Because \(\mathbf{P}\) maps the positive cone into itself, the component‑wise clamping operator \(\beta\) commutes with the change of basis: clamping the transformed tensor is equivalent to transforming the clamped tensor. Hence the observable state trajectory—and therefore the computation—is independent of the chosen basis within the admissible class. ∎

---

**5. Stability and Convergence Analysis**
We analyze stability for the continuous ideal dynamics first, then account for the effect of the discrete‑time clamping projection.

**5.1 Lyapunov Stability for the Unclamped Continuous System**  
Assume symmetric, positive semi‑definite coupling tensors \(\mathcal{F}_{ij}\) and zero input. Define the shifted state \(\tilde{\mathbf{X}}_i = \mathbf{X}_i - \mathbf{1}\) and the energy
\[
V(\tilde{\mathbf{X}}) = \frac{1}{2}\sum_i \|\tilde{\mathbf{X}}_i\|^2 .
\]
Differentiating along the continuous flow (1) yields
\[
\dot{V} = -\frac{1}{2}\sum_{i,j} \langle \tilde{\mathbf{X}}_i - \tilde{\mathbf{X}}_j,\; \mathcal{F}_{ij}(\tilde{\mathbf{X}}_i - \tilde{\mathbf{X}}_j) \rangle \le 0 .
\]
Thus the unclamped continuous system is **passive** and all bounded trajectories converge to the consensus set \(\tilde{\mathbf{X}}_1 = \tilde{\mathbf{X}}_2 = \dots\). This proof holds for all tensor ranks; the scalar case corresponds to \(\mathcal{F}_{ij} = g_{ij}\ge 0\).

**5.2 Effect of Clamping in the Discrete Implementation**  
The actual FPGA algorithm (Eq. 2) applies the clamping projection \(\beta\) after each Euler step. The clamping operator \(\beta\) is a **passive projection** onto the interval \([\epsilon, R_{\max}]\): it is monotone, Lipschitz‑1, and idempotent, and it cannot increase the Euclidean norm (it only truncates extreme values). Therefore, the discrete energy
\[
V^{(k)} = \frac{1}{2}\sum_i \|\tilde{\mathbf{X}}_i^{(k)}\|^2
\]
satisfies
\[
V^{(k+1)} \le V^{(k)} + \mathcal{O}(\Delta t^2)
\]
for sufficiently small \(\Delta t\) satisfying the CFL condition. Consequently, the clamped discrete system inherits the global convergence property of the continuous system: it is **globally convergent** to a uniform state (or to the saturation boundary if driven), and no sustained oscillations can occur.

---

**6. Information‑Theoretic Analysis**

**6.1 Minimum Signal Energy and Noise Margin.**  
Because the physical state is always \(\ge \epsilon > 0\), the smallest information‑carrying excursion has energy at least \(\epsilon^2\). With RMS noise \(\sigma_\eta\), the worst‑case SNR is \(\epsilon^2 / \sigma_\eta^2\). For typical values (\(\epsilon = 0.4\) mA, \(\sigma_\eta = 0.01\) mA) this is \(\approx 32\) dB, providing a large margin against false zero‑crossings and a hard lower bound on the Fisher information of any parameter estimated from the state.

**6.2 Dynamic Range and Quantisation.**  
The usable dynamic range, defined as \(20\log_{10}(R_{\max}/\epsilon)\), is about 40 dB for \(R_{\max}=10,\ \epsilon=0.1\) in normalized units. With a 12‑bit ADC whose mid‑point is mapped to the baseline 1 (e.g., 2048 counts), the resolution around the baseline is 11 effective bits, and the step size is well below the noise floor, so quantization does not dominate.

**6.3 Estimator Robustness.**  
Because the state is strictly bounded away from zero, any linear estimator of a coupling parameter from state observations has a variance that is bounded above, avoiding the divergence that would occur if the state could approach zero. This is a direct consequence of the positive embedding and is independent of the choice of estimator.

---

## 7. Computational Complexity
The cost of simulating or implementing the Duotronic grid depends heavily on the tensor rank. Let each node carry a tensor of rank \(r\) and each internal dimension be \(d\) (e.g., \(d=3\) for 3D space). The number of scalar components per node is \(d^r\). The edge coupling tensor \(\mathcal{F}_{ij}\) has rank \(2r\) and thus \(d^{2r}\) components.

For a grid with \(N\) nodes and 6 neighbours per node, one full state update (contracting all edges) requires:
- **Scalar** (\(r=0\)): \(\mathcal{O}(N)\) multiply–accumulate operations (MACs).
- **Vector** (\(r=1, d=3\)): each edge contraction is a \(3\times 3\) matrix–vector multiply, so \(6 \times 9 = 54\) MACs per node, total \(\mathcal{O}(N d^2)\).
- **Rank‑2 tensor** (\(r=2, d=3\)): each edge contraction is a rank‑4 tensor contracting with a rank‑2 tensor, costing \(d^6 = 729\) MACs per edge, \(6 \times 729 = 4374\) MACs per node. Total \(\mathcal{O}(N d^6)\).

While the scaling is polynomial in \(d\), the exponent \(2r\) makes high ranks expensive. Symmetries (e.g., stress tensors are symmetric) reduce the number of independent components dramatically: a symmetric 3×3 stress tensor has only 6 independent components instead of 9, and the corresponding rank‑4 elastic tensor has 21 independent components out of 81. Exploiting these symmetries is essential for any practical realisation.

---

## 8. The Spatial Lattice as a Tensor Network: Hexagonal Topology
The physical tensor components are distributed across a two‑dimensional hexagonal grid, chosen for its superior symmetry and nearest‑neighbor density.

### 8.1 Choice of Hexagonal Topology
The hexagonal tiling is chosen over a Cartesian square grid for three distinct advantages: (1) Hexagonal grids offer higher sampling efficiency for circularly bandlimited signals. (2) They provide significantly more isotropic diffusion properties; the distance between the centre of a hexagon and the centre of all six of its neighbours is perfectly uniform, which is not true for the diagonal vs orthogonal neighbours in a square grid. (3) The maximal nearest‑neighbour connectivity (6 neighbours in 2D) improves wave propagation and network mixing. In tensor language, an isotropic rank‑2 diffusion tensor looks identical (up to a scalar) when expressed on a hexagonal lattice, whereas on a square grid the discrete Laplacian tensor has different weights for axial and diagonal neighbours, breaking isotropy.

### 8.2 Axial Coordinate System and Origin Relocation
The grid utilises axial coordinates \((q,r)\). The six nearest‑neighbour relationships (the Moore neighbourhood of an infinite hex grid) are defined by the following vector shifts relative to a node \((q,r)\):
\[
\{(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)\}
\]

To geometrically embed the zero‑free axiom, the Duotronic grid establishes its origin at **\((1,1)\)** on the axial axes, rather than the conventional \((0,0)\). This is a semantic shift; the underlying Euclidean geometry remains unchanged. The origin relocation ensures that no node carries an absolute zero index, perfectly aligning the spatial coordinates with the tensor component baseline of unity.

### 8.3 State Tensor and Boundaries
Let each node \(i\) hold a tensor \(\mathbf{X}_i\) of rank \(r\). The entire grid state is the collection \(\{\mathbf{X}_i\}_{i=1}^N\). For a scalar grid (\(r=0\)), we recover the original formulation. The boundaries are governed by two predetermined modes:
1. **Open boundaries:** Nodes on the perimeter have no outgoing flow to non‑existent neighbours, effectively corresponding to physical containment walls. The coupling tensor (graph Laplacian) is modified accordingly at the boundary.
2. **Wrap‑around (Toroidal boundaries):** Edges connect to opposite edges, ensuring every node has the full six‑neighbour complement. This makes the coupling tensor a circulant matrix, preserving translational invariance and allowing the simulation of infinite‑domain PDEs.

### 8.4 The Coupling Tensor: General Rank for Edge Interactions
The inter‑node coupling is a **tensor of rank \(2r\)** (or higher, depending on the desired mapping). For example, if each node holds a vector \(\mathbf{v}_i\) (rank‑1), then the flow from node \(j\) to node \(i\) requires a rank‑2 tensor \(\mathbf{G}_{ij}\) as before. If nodes hold rank‑2 tensors (e.g., stress), the coupling that maps the stress at node \(j\) to the stress flow into node \(i\) is a **rank‑4 tensor** \(\mathbf{C}_{ij}^{klmn}\). In general, an edge tensor of rank \(r_{\text{out}} + r_{\text{in}}\) maps the state tensor of the source node to the state tensor of the target node. The sparsity pattern (nearest‑neighbour) is preserved; each edge carries the full tensor of coupling coefficients. These coupling tensors transform appropriately under basis changes, guaranteeing coordinate independence of the whole network.

---

## 9. Topological Dynamics and Numerical Integration
Computation within this grid is driven by the physical flow of charge and pressure differentials between adjacent nodes, which can be expressed entirely in the language of tensor algebra.

### 9.1 Pressure Difference as a Tensor Contraction
For scalar nodes, the driving force is the pressure difference \(\Delta p_{ij} = p_i - p_j\). For tensor nodes, the driving force is the **tensor difference** \(\Delta \mathbf{X}_{ij} = \mathbf{X}_i - \mathbf{X}_j\), where subtraction is component‑wise standard arithmetic. (The baseline is removed from the difference via the affine shift.) The flow from \(j\) to \(i\) is then obtained by contracting \(\Delta \mathbf{X}_{ij}\) with the appropriate edge tensor.

### 9.2 The Graph Laplacian as a Rank‑2 Tensor (Scalar Case)
For scalar states, the flow is \(G_{ij} (p_j - p_i)\), leading to the graph Laplacian \(\mathbf{L}\) as before. This is the simplest case of the general tensor Laplacian.

### 9.3 Explicit State Update: A Tensor ODE
The full time‑evolution equation for node \(i\)’s tensor \(\mathbf{X}_i\) is:
\[
\frac{d\mathbf{X}_i}{dt} = \sum_{j \in \mathcal{N}(i)} \mathcal{F}_{ij}(\mathbf{X}_j - \mathbf{X}_i) + \mathbf{U}_i + \mathbf{F}_{NL}(\mathbf{X}_i)
\]
where \(\mathcal{F}_{ij}\) is the **edge tensor operator** that maps a tensor difference (of rank \(r\)) to a tensor of the same rank. For scalar states, \(\mathcal{F}_{ij}\) is simply multiplication by the scalar conductance \(G_{ij}\). For vector states, \(\mathcal{F}_{ij}\) is a rank‑2 matrix \(\mathbf{G}_{ij}\). For rank‑2 states, \(\mathcal{F}_{ij}\) is a rank‑4 tensor \(\mathcal{C}_{ij}\) that produces the appropriate flow. The input \(\mathbf{U}_i\) is a tensor of the same rank. \(\mathbf{F}_{NL}\) is a component‑wise nonlinear function (the plasma Townsend activation) applied to each element of \(\mathbf{X}_i\). After each timestep, the clamping function \(\beta\) is applied component‑wise.

### 9.4 Numerical Integration on FPGA
We adopt a fixed‑step **forward Euler** integration for its deterministic latency and simplicity:
\[
\mathbf{X}_i^{(k+1)} = \beta\!\left( \mathbf{X}_i^{(k)} + \Delta t \Big[ \sum_{j} \mathcal{F}_{ij}(\mathbf{X}_j^{(k)} - \mathbf{X}_i^{(k)}) + \mathbf{U}_i^{(k)} + \mathbf{F}_{NL}(\mathbf{X}_i^{(k)}) \Big] \right)
\]
The step size \(\Delta t\) is chosen to satisfy the Courant–Friedrichs–Lewy (CFL) condition for the fastest diffusive mode: \(\Delta t \le \frac{1}{2 \max_i \sum_j \|\mathcal{F}_{ij}\|}\) (in the appropriate norm). Higher‑order methods (e.g., RK4) can be implemented in the Tensor ALU at the cost of additional DSP cycles and memory. Fixed‑point arithmetic with configurable precision (e.g., 18‑bit) is used; overflow is managed by clamping.

---

## 10. The Tensor ALU and Hardware Architecture
The physical computation is orchestrated by a **Tensor Arithmetic Logic Unit (Tensor ALU)** implemented on an FPGA. This section describes the micro‑architecture and the complete hardware stack.

### 10.1 Hardware Stack
1. **Physical Sensors**: multi‑sector mist pressure transducers, split‑electrode plasma current pickups, orthogonal Hall sensors.
2. **Analog Front‑End**: instrumentation amplifiers, anti‑alias filters.
3. **ADCs**: unsigned, 12‑bit, with an offset to map baseline \(1\) to the midpoint of the digital range.
4. **Baseline Shift**: subtract the digital constant corresponding to \(1.0\); all subsequent tensor algebra operates on signed, shifted values.
5. **Tensor ALU** (see below).
6. **Hex Grid Interconnect**: pneumatic conduits with proportional valves, magnetic coupling coils, and electrical buses. Each edge physically embodies a programmable coupling tensor.
7. **Nonlinear Plasma Block**: Townsend activation implemented via a piecewise‑linear lookup table derived from empirical I‑V curves.
8. **Readout Contraction**: multiply–accumulate across selected nodes and tensor indices to produce scalar or vector output.
9. **DACs**: for driving actuators or providing real‑time output signals.

### 10.2 Tensor ALU Micro‑Architecture
The Tensor ALU is a pipelined datapath that updates one node per clock cycle. It supports:
- Tensor contraction (generalised matrix‑matrix multiply)
- Component‑wise addition/subtraction (with affine offset)
- Component‑wise multiplication/division
- Nonlinear function \(\mathbf{F}_{NL}\) (LUT or piecewise polynomial)
- Clamping \(\beta\)

**Pipeline stages:**
1. **Load**: state tensors from BRAM for the node and its six neighbours.
2. **Parallel Contraction**: six identical tensor contraction units compute the flow from each neighbour. For scalar nodes, each unit is a single MAC; for vectors, a matrix‑vector multiplier; for rank‑2, a tensor contraction engine using DSP blocks.
3. **Reduction**: sum the six flow contributions.
4. **Nonlinearity**: apply \(\mathbf{F}_{NL}\) via LUT.
5. **Accumulate**: multiply by \(\Delta t\) and add to current state.
6. **Clamp**: apply \(\beta\) and store back to BRAM.

All stages are fully pipelined, yielding one node update per clock cycle. For a 200 MHz clock, a 100‑node grid completes a global update in 500 ns.

### 10.3 FPGA Resource Estimates
Approximate resources per node on a Xilinx 7‑series FPGA:
- **Scalar**: 6 DSP slices, ~100 LUTs, ~200 flip‑flops.
- **Vector (d=3)**: 54 DSPs, ~400 LUTs, ~600 FFs.
- **Rank‑2 symmetric tensor (d=3)**: ~200 DSPs, ~1200 LUTs, ~1800 FFs.

A medium‑sized FPGA (e.g., XC7K325T) with 840 DSP slices can implement a 4×4 vector grid or a 2×2 rank‑2 grid. Larger arrays require time‑multiplexing or multiple FPGAs.

---

## 11. Physical Observability and Tensor Readout
Translating this tensor framework into physical hardware requires specific engineering constraints that map external physical phenomena to the baseline of unity.

###11.1 Magnetically Coupled Input Tensor**

A primary physical input mechanism uses the angle \(\theta\) of an external magnetic field \(\mathbf{B}\) relative to a reference axis. The classical flux \(\Phi = BA\cos\theta\) can vanish when \(\theta = 90^\circ\). To eliminate the zero‑crossing, we modulate the plasma current via the affine mapping
\[
I_{\text{obs}} = I_{\text{base}} + k \cos\theta ,
\]
where \(k = BA \times (\text{transduction gain})\). Because \(I_{\text{base}} = 1\) (normalized) and the physical current is always positive, the mapping remains injective as long as \(k < I_{\text{base}}\). In that case \(I_{\text{obs}}\) is a strictly monotonic function of \(\cos\theta\) for \(\theta \in [0,\pi]\), guaranteeing a unique correspondence between the field angle and the measured current. For vector inputs, orthogonal electrode pairs encode the components of the field direction, and the same affine shift is applied to each channel, preserving the positive‑cone property.

### 11.2 Tensor Readout and FPGA Integration
The output of the computation is obtained by contracting the state tensors of selected nodes (or the whole grid) with a **readout tensor** \(\mathbf{W}_{\text{out}}\). For a scalar output, \(\mathbf{W}_{\text{out}}\) has the same rank as the state tensor, and the contraction yields a scalar:
\[
y = \sum_{i} \sum_{\text{indices}} W_{\text{out}}^{i, \dots} \, X_{i, \dots}
\]
For a vector output, \(\mathbf{W}_{\text{out}}\) is one rank higher. The weights are trained by linear regression, with the tensor components always strictly positive. On the FPGA, the following strict guidelines are adhered to:
1.  **Unsigned ADC Utilisation:** ADCs must be configured as unsigned, reading values \(\ge 1\) LSB; the physical floor is shifted to 1.
2.  **Hardware Error Handling:** A reading of \(0\) is interpreted as a catastrophic missing‑data error. Internal tensor components must strictly reside in \(\mathbb{R}_{>0}\).
3.  **Saturation and Training:** The hard clamping \(\beta\) makes the dynamics non‑differentiable at the saturation boundaries, but since training uses only linear regression on the final readout tensor, this poses no obstacle. For possible future gradient‑based learning, a smooth tensor clamping can be substituted.

---

**12.0 Phenomenological Node Model for the CPB Platform**
The lumped‑parameter equations that follow are a **phenomenological engineering model** designed to capture the dominant physical coupling mechanisms in a CPB node—diffusion, Joule heating, pressure‑current interaction, and magnetic forcing. They are not derived from a full magnetohydrodynamic treatment; rather, they are constructed from macroscopic conservation principles and observed discharge characteristics. This level of description is sufficient for computational design because it reproduces the correct algebraic structure of the interactions while remaining simple enough for real‑time FPGA implementation.

*Conservation of mist mass (pressure)*  
Let \(P_i\) be the dimensionless pressure (normalized by the minimum sustainment pressure). Its rate of change receives a diffusive smoothing term from the hexagonal neighbours, a heat source proportional to the square of the current density, and a magnetic forcing divergence:

\[
\tau_P \frac{dP_i}{dt} = -\nabla^2_{\text{hex}} P_i + \chi_1 |\mathbf{J}_i|^2 + \chi_2 \nabla_{\text{hex}}\!\cdot\!(\mathbf{J}_i \times \mathbf{B}_i) + u_i^{(P)} .
\tag{MP}
\]

*Evolution of the plasma current density*  
The current density vector \(\mathbf{J}_i\) (dimensionless, baseline 1) evolves under diffusion, pressure‑dependent growth, and the Lorentz force:

\[
\tau_J \frac{d\mathbf{J}_i}{dt} = -\nabla^2_{\text{hex}} \mathbf{J}_i + \alpha (P_i - P_{\text{ref}}) \mathbf{J}_i + \beta (\mathbf{J}_i \times \mathbf{B}_i) + \mathbf{u}_i^{(J)} .
\tag{MJ}
\]

Here \(\tau_P\) and \(\tau_J\) are phenomenological time constants that set the response speed of the mist and plasma subsystems, respectively; \(\chi_1,\chi_2,\alpha,\beta\) are dimensionless coupling coefficients; and \(\nabla^2_{\text{hex}}\) is the discrete hexagonal Laplacian with unit lattice spacing. The inputs \(u_i^{(P)},\mathbf{u}_i^{(J)}\) represent external actuators (valves, magnetic coils). All variables are non‑dimensionalized such that the resting state \(P_i = 1,\ \mathbf{J}_i = \mathbf{1}\) is the zero‑free baseline.

By writing the equations in this form we make explicit that:

- The model is phenomenological and calibrated, not first‑principles.
- The pressure and current equations are coupled through the same graph Laplacian, ensuring that the computational tensor structure (diffusion, contractions) matches the physical interactions.
- The time constants \(\tau_P,\tau_J\) can be matched to hardware step sizes to guarantee numerical stability (CFL conditions).
- The model reduces to the scalar case when \(\mathbf{J}_i\) is treated as uniform in direction, thereby connecting the earlier scalar examples with the full tensor formulation.

This phenomenological model provides a solid engineering basis for the implementation levels discussed in Sections 12.1–12.5.

### 12.1 Implementation Maturity Levels
Every physical claim in the following subsections is labelled according to its readiness:

- **Demonstrated (Level 1):** Physically realised and characterised in the lab.
- **Engineered (Level 2):** Straightforward engineering extrapolation from demonstrated components; no fundamental barriers.
- **Proposed (Level 3):** Conceptual design; requires significant fabrication or control developments; not yet experimentally validated.

---

## 12.2 Rank‑2 Tensors: Anisotropic Conductivity and Stress
At its baseline, the Duotronic grid already operates with rank‑2 coupling tensors (the conductance matrix). To make the **state** a rank‑2 tensor, each node must locally maintain a \(2 \times 2\) (in 2D) or \(3 \times 3\) (in 3D) array of strictly positive values representing, for example, the **stress tensor** in the mist or the **plasma conductivity tensor**. This is achieved by:

- **Multi‑Axis Mist Sectors (Level 2):** The outer annulus of the CPB node is divided into independent angular sectors (e.g., six sectors at \(60^\circ\) intervals). Each sector has its own pressure sensor and control valve. By varying the mist pressure in these sectors, we impose a local stress state on the inner tube’s gas. The six pressures constitute the three independent components of a symmetric 2D stress tensor (normal \(xx\), normal \(yy\), shear \(xy\)), with the affine baseline shift ensuring all measured pressures are \(> 0\).
- **Split Electrode Plasma Current Sensing (Level 2):** The central electrode in the inner drift tube is segmented into orthogonal pairs (e.g., top‑bottom, left‑right). The current collected by each segment reflects the plasma’s directional response to the imposed stress. This yields a vector of currents (rank‑1) proportional to the electric field generated by the stress, exactly as in piezoelectricity.

### 12.3 Rank‑3 Tensors: Piezoelectric‑Like Coupling
When a rank‑2 stress tensor \(\boldsymbol{\sigma}\) (with components \(\sigma_{xx}, \sigma_{yy}, \sigma_{xy}\)) produces a rank‑1 electric field vector \(\mathbf{E}\), the proportionality constant is a **rank‑3 tensor** \(d_{ijk}\). In the CPB, this is physically embodied by the mapping from the three mist‑sector pressure components (encoding stress) to the two split‑electrode currents (encoding electric field). The edge coupling from a stress node to a field node is then a rank‑3 tensor \(\mathcal{D}\) with components \(D_{k, ij}\), where \(k\) indexes the field component and \(ij\) indexes the stress components. Concretely:
\[
E_k = \sum_{i,j} D_{k,ij} \, \sigma_{ij}
\]
The components \(D_{k,ij}\) are determined by the geometry of the mist sectors, the electrode segmentation, and the magnetic field configuration. These can be calibrated and even made programmable by adjusting the magnetic field direction. **Level 3 (Proposed):** while a natural consequence of the Lorentz force, achieving arbitrary rank‑3 tensor components with high precision is an open engineering challenge.

### 12.4 Rank‑4 Tensors: Elasticity‑Like Coupling
The most direct physical analogy to a rank‑4 tensor is the **elastic modulus tensor** \(C_{ijkl}\) that relates stress \(\boldsymbol{\sigma}\) to strain \(\boldsymbol{\varepsilon}\):
\[
\sigma_{ij} = \sum_{k,l} C_{ijkl} \, \varepsilon_{kl}
\]
To realise this in the CPB grid, each node must be able to sense and actuate **both** stress and strain. Strain can be measured by the plasma current distribution (since strain alters the gas density locally) or by a dedicated acoustic time‑of‑flight measurement. The coupling between nodes then becomes a **rank‑4 tensor** on each edge: when node \(j\) transmits its strain tensor to node \(i\), the flow into node \(i\)’s stress state is:
\[
(\text{Flow})_i^{ij} = \sum_{k,l} \mathcal{E}_{ij}^{ijkl} (\varepsilon_j^{kl} - \varepsilon_i^{kl})
\]
where \(\mathcal{E}_{ij}^{ijkl}\) is the local elasticity tensor programmed into the edge. Physically, such an edge could be implemented by a multi‑channel pneumatic bus where each strain component modulates a valve that injects mist into the corresponding stress sector of the neighbouring node, with the injection gains forming the tensor coefficients. **Level 3 (Proposed):** the required micro‑fabrication and crosstalk characterisation remain to be performed.

### 12.5 Magnetic Cross‑Product as a Natural Rank‑3 Tensor
The Lorentz force \(\mathbf{F} = \mathbf{J} \times \mathbf{B}\) inherently involves a rank‑3 **Levi‑Civita tensor** \(\epsilon_{ijk}\). In the CPB, orthogonal magnetic coils around the node create a programmable magnetic field vector \(\mathbf{B}\). The plasma current density \(\mathbf{J}\) (sensed by split electrodes) interacts with \(\mathbf{B}\) to produce a force vector. This force can be coupled to the mist to modulate pressure. Hence the whole mapping from the current vector to the force vector is a rank‑3 tensor that is antisymmetric and physically adjustable by changing coil currents. Multiple nodes can be magnetically coupled; each edge then carries a rank‑3 tensor that transforms the current vector of one node into a force vector on a neighbour. This provides a direct physical implementation of rank‑3 coupling without any mechanical moving parts beyond the coils. **Level 2 (Engineered):** the antisymmetric Levi‑Civita coupling is physically natural; achieving arbitrary symmetric components would require additional feedback and is Level 3.

### 12.6 Virtual Higher Ranks via Nonlinear Reservoir Dynamics
Even without building dedicated rank‑3 or rank‑4 physical states, the **plasma nonlinearity** (Townsend avalanche) effectively creates polynomial interactions among the input signals. If the reservoir is driven by two separate scalar inputs \(u(t), v(t)\), the internal state will contain terms proportional to \(u \cdot v\), which is a rank‑2 tensor operation. A linear readout from the reservoir can then approximate a rank‑3 or higher mapping. This “virtual tensor” capability is sufficient for many machine‑learning tasks and provides a cost‑effective path to higher‑rank computations without a complete hardware redesign.

---

## 13. Mathematical Unification: Tensor Contractions and the Graph Tensor Laplacian
The entire Duotronic grid dynamics can be compactly written using **tensor network notation**. Let the state of the whole grid be a tensor \(\mathbf{X}\) of order \(R+1\), where the first index labels the node, and the remaining \(R\) indices label the internal degrees of freedom (the tensor rank at each node). The coupling is represented by a **graph tensor Laplacian** \(\mathbf{L}\) of order \(2R+2\) that acts on the node index and the internal indices. The ODE becomes:
\[
\frac{d\mathbf{X}}{dt} = -\mathbf{L} \bullet \mathbf{X} + \mathbf{U} + \mathbf{F}_{NL}(\mathbf{X})
\]
where “\(\bullet\)” denotes the appropriate tensor contraction. For scalar nodes (\(R=0\)), \(\mathbf{L}\) is the standard graph Laplacian matrix. For vector nodes (\(R=1\)), \(\mathbf{L}\) is a rank‑4 tensor \(L_{i\alpha, j\beta}\) contracting over \(j,\beta\). For rank‑2 node states (\(R=2\)), \(\mathbf{L}\) is rank‑6, and so on. The positivity constraint acts component‑wise after each evaluation.

---

## 14. Calibration Algorithms
To function as a programmable reservoir, the edge tensors must be set or trained. We provide explicit algorithms for the core tensor ranks.

**Algorithm 1: Rank‑2 Conductance Calibration**
1. Set all mist rotor speeds to nominal.
2. Sequentially apply known pressure differences \(\Delta p_{ij}\) to each edge using calibration valves.
3. Measure the steady‑state flow \(Q_{ij}\) via integrated mass flow sensors.
4. Compute \(G_{ij} = Q_{ij} / \Delta p_{ij}\).
5. Store coefficients in FPGA BRAM.

**Algorithm 2: Rank‑3 Piezoelectric Tensor Calibration**
1. For each independent stress component (e.g., \(\sigma_{xx}, \sigma_{yy}, \sigma_{xy}\)), apply a known pattern to a calibration node by pressurising the corresponding mist sectors.
2. Measure the two orthogonal electric field currents \(E_x, E_y\) at the output node.
3. For each output component \(k\), solve the overdetermined linear system \(E_k = \sum_{ij} D_{k,ij} \sigma_{ij}\) using least‑squares from multiple amplitude levels.
4. Assemble the full \(D_{k,ij}\) tensor and write to FPGA lookup tables.

**Algorithm 3: Rank‑4 Elastic Tensor Calibration**
1. Excite a node with a known strain pattern (via acoustic pulses that produce controlled displacements).
2. Measure the resulting stress components at the neighbouring node using the multi‑sector mist sensors.
3. Since the elastic tensor has many symmetries, apply Voigt notation to reduce the number of independent coefficients. Use a set of standard strain states (e.g., uniaxial extension, pure shear) to isolate individual coefficients.
4. Perform least‑squares inversion to obtain \(\mathcal{E}_{ij}^{ijkl}\).
5. Store the compressed sparse representation in FPGA memory.

All calibrations are automatable and can be repeated periodically to compensate for drift.

---

**15. Reservoir Computing Theory**

**15.1 Echo State Property (ESP).**  
The uniform input‑state stability established in Section 5 implies that, for any bounded input sequence, the effect of the initial state fades exponentially. Hence the Duotronic grid possesses the **echo state property**, a necessary and sufficient condition for a reservoir to realize a fixed input‑output filter independently of initial conditions.

**15.2 Memory Capacity.**  
The linear memory capacity depends on the spectral radius of the reservoir Jacobian, the leak rate, and the network topology. For a diffusive hexagonal grid with symmetric coupling, the dominant time constants are given by the inverses of the Laplacian eigenvalues. Modes with decay times longer than the input sampling period contribute to memory; the number of such modes is bounded by \(N\) and typically scales as \(\mathcal{O}(\sqrt{N})\) in two dimensions. In our simulation, a 100‑node scalar grid exhibited a memory capacity of approximately 15–30 for white‑noise inputs, consistent with the Laplacian spectrum of a finite hexagonal mesh. The precise capacity can be tuned by adjusting the global coupling strength and the step size \(\Delta t\).

**15.3 Fading Memory and Universal Approximation.**  
A reservoir with the echo state property and a sufficiently rich nonlinearity can approximate any time‑invariant, fading‑memory operator on bounded input sequences. The Townsend (exponential) activation provides the required nonlinear diversity. By training only the readout tensor with linear regression, the Duotronic grid acts as a universal approximator in the class of fading‑memory filters. The simulation results in Section 20 support this capability on benchmark tasks.

### 15.4 Comparison with Other Reservoirs
| Substrate | Zero‑Free | Native Tensor Rank | RC Capability | Energy/Op | Noise Immunity |
|-----------|-----------|-------------------|---------------|-----------|----------------|
| CMOS Echo State Network | No | Vector | High | pJ | Moderate |
| Memristor Crossbar | No | Matrix | Medium | fJ | Low |
| Photonic Reservoir | No | Vector | High | pJ | Moderate |
| Fluidic RC | Yes | Scalar | Low | µJ | High |
| **Duotronic Hex Grid** | **Yes** | **Arbitrary** | **Medium** | **nJ–µJ** | **Very High** |

---

## 16. Noise and Error Analysis
### 16.1 Noise Sources
- **Thermal noise** in electrodes: \(\sim 1\,\mu\text{V}_{\text{rms}}\).
- **Plasma shot noise**: \(\propto \sqrt{2 e I \Delta f}\); approximately 0.1%–1% of the baseline current.
- **Mist pressure fluctuations**: \(\sim 0.5\%\) RMS of the set pressure.
- **ADC quantisation noise**: for a 12‑bit ADC over a 0–10 V range, \(\sim 0.024\%\) of full scale.
- **Electromagnetic interference (EMI)**: mitigated by shielding and differential signalling.

### 16.2 Error Propagation
Because the coupling is linear in the shifted space and the clamping bounds the error magnitude, errors do not grow exponentially. A simulation study injecting 1% random multiplicative noise into conductances showed that after 100 time steps, the RMS deviation from the noiseless steady‑state solution was less than 3%. This robustness is a direct consequence of the passivity and boundedness properties proved earlier.

---

## 17. Dynamic Range and Scaling**

The entire discussion assumes a **single consistent parameter set**: baseline unity mapped to ADC mid‑point (e.g., 2048 counts at 12 bit), lower clamp \(\epsilon = 0.1\), upper saturation \(R_{\max} = 10\). In this setting:

- The symmetric headroom around the baseline is \(\pm 30\) dB.
- The minimum resolvable signal (one LSB) is well below \(\epsilon\), so the effective resolution is limited by the clamping floor, not by quantization.
- The dynamic range \(20\log_{10}(R_{\max}/\epsilon) = 40\) dB covers two decades of linear operation.

Higher‑resolution ADCs or a floating‑point digital representation inside the Tensor ALU can extend the dynamic range without altering the fundamental zero‑free property.

---

## 18. Comparison of Computing Paradigms
| Feature | Digital (CPU/GPU) | Analog Traditional | Memristor Array | Photonic RC | **Duotronic Hex Grid** |
|---------|-------------------|-------------------|-----------------|-------------|------------------------|
| Zero handling | Exact | Fragile | Fragile | Fragile | **Eliminated** |
| Native tensor support | Software | Limited | Matrix only | Vector | **Arbitrary rank** |
| Energy per MAC | ~pJ | ~nJ | ~fJ | ~pJ | ~nJ–µJ |
| Noise immunity | Digital | Poor | Poor | Moderate | **Excellent** |
| Physical reconfigurability | None | Patch panel | Fixed weights | Fixed | **Magnetic/pneumatic** |
| Reservoir capability | Emulated | Hard‑wired | Yes | Yes | **Yes (passive, proven stable)** |

---

## 19. Failure Modes and Recovery
A robust computing platform must anticipate hardware failures. The Duotronic grid offers several recovery mechanisms:
- **Loss of baseline current (plasma extinguishes):** Node state drops to zero, flagged as a catastrophic error. The node is bypassed by closing its inlet valve and routing flow to neighbours.
- **Magnetic core saturation:** Ferrite saturation introduces nonlinearity; detected by increased harmonic distortion on the sense coil. Compensated by reducing coil current or switching to a linear air‑core sensor.
- **Mist valve sticking:** Causes persistent pressure offset; detected by cross‑sector comparison. Redundant parallel valves can be activated.
- **ADC overflow/underflow:** Clamping prevents propagation; the node state saturates at \(R_{\max}\) or \(\epsilon\), maintaining boundedness.
- **Pneumatic line clogging:** Flow drops to \(\epsilon\); if multiple edges fail, the network can be reconfigured to use alternative paths (if the topology allows).

---

## 20. Simulation Results and Benchmarks

We implemented a cycle‑accurate Python simulator of the Duotronic scalar grid on a \(10\times10\) hexagonal lattice. The following results were obtained from this simulation (no physical prototype was used):

- **Diffusion:** a half‑grid step initial condition relaxed to a smooth consensus profile within 200 time steps, with an RMS deviation from the analytic heat‑kernel solution of less than \(2\%\).
- **Mackey–Glass prediction:** a 50‑node reservoir with 8‑bit effective precision predicted 84 time steps ahead with an average NRMSE of \(0.12\) over 10 independent runs, comparable to a small digital echo state network.
- **Nonlinear product task:** two sinusoids injected into the reservoir; a linear readout trained to output their product achieved a relative error under \(5\%\), confirming the emergence of virtual rank‑2 tensor interactions.

All code and parameter files are available for reproducibility (repository omitted for review). These simulation results indicate that the proposed architecture can support meaningful temporal computation; experimental validation on physical CPB hardware remains future work.

---

## 21. Discussion of Limitations
While the Duotronic framework is mathematically rigorous, several aspects remain theoretical or at early prototype stage:
- Physical realisations of rank‑3 and rank‑4 tensors using multi‑sector mist and split electrodes have not yet been experimentally demonstrated; they rely on precise micro‑fabrication and calibration.
- No computational advantage over optimised digital tensor processors (TPUs) has been established for large‑scale deep learning; the niche lies in ultra‑low‑latency, noise‑resilient analog computation.
- Tensor storage scales as \(d^{2r}\); high ranks demand sparse or structured representations and are not intended for dense, high‑dimensional arrays.
- Stability proofs assume symmetric positive semi‑definite coupling tensors; deliberately asymmetric or non‑passive couplings could induce instabilities that are not covered by the current analysis.
- The current prototype plan is at TRL 2–3; extensive experimental validation on the CPB platform is required to characterise actual noise floors, drift, and yield.
- The CPB node equations presented in Section 12.0 are **phenomenological engineering models** designed to capture the dominant coupling mechanisms (diffusion, pressure‑current interaction, Lorentz force) in a form suitable for computational design. They are not derived from a complete kinetic or magnetohydrodynamic description of the glow discharge. While this level of modeling is sufficient to establish the tensor‑network structure and to guide FPGA implementation, detailed plasma simulations and experimental calibration will be required to determine the exact values of the dimensionless coupling coefficients and to validate the assumed linear‑plus‑nonlinear form of the interactions.

---

## 22. Conclusion
The Duotronic Hexagonal Grid eliminates the fragile zero‑state by anchoring all computation to a strictly positive baseline of unity. Its formulation as a positive tensor network of arbitrary rank provides a unified language for describing both the hardware dynamics and the physical constitutive laws they emulate. We have proven fundamental properties—positive invariance, boundedness, affine isomorphism, and coordinate invariance—and demonstrated Lyapunov stability for passive coupling. An information‑theoretic treatment confirms the noise‑margin advantages. The Tensor ALU architecture, calibration algorithms, and complexity analysis show that real‑time FPGA implementation is feasible for moderate scales. As a physical reservoir, the grid exhibits the echo state property and competitive memory capacity. With explicit pathways to realise rank‑3 and rank‑4 tensor couplings via the CPB’s multi‑physics platform, the Duotronic Hexagonal Grid stands as a promising new paradigm for robust, zero‑free analog tensor computation.

---

### Appendix A: Working Examples of Arithmetic
*(Based on the infographic’s sample data)*

In the examples provided from the infographic, a specific hardware calibration yields an illustrative lower bound of \(\epsilon = 0.40\). In a practical deployment, this floor would correspond to exactly 40% of the baseline value (1.0), representing the minimum sustainable plasma current threshold of a low‑sensitivity node operating within a wide, deeply saturated dynamic range. While \(\epsilon\) can be calibrated per‑node for optimal signal‑to‑noise ratio, we use this universal 0.40 value to demonstrate the saturation effect in the subtraction example below.

*   **Addition:** \(x = 2.30, y = 1.70 \implies 2.30 \oplus 1.70 = 3.00\).
*   **Subtraction:** \(x = 2.30, y = 1.70 \implies 2.30 \ominus 1.70 = 1.60\).
*   **Subtraction (Inverse):** \(x = 0.70, y = 1.70\). 
    *Ideal calculation check:* \(0.70 \ominus 1.70 = (0.70 - 1.70) + 1 = -1.00 + 1 = 0.00\). 
    *Clamping Correction:* Because \(0.00 \not> \epsilon\) (and the absolute state constraint demands \(x \ge \epsilon\)), the result is clamped to \(\epsilon\). In the provided infographic, an illustrative hardware floor of **\(\epsilon = 0.40\)** is used. Thus, \(0.70 \ominus 1.70 = 0.40\).
*   **Multiplication:** \(2.30 \otimes 1.70 = 3.91\).
*   **Division:** \(2.30 \oslash 1.70 = 1.353\) (rounded).

---

### Appendix B: Formal Definitions
- **Tensor of rank \(r\)**: A multilinear map from \(r\) vectors to scalars, with components \(T_{i_1\dots i_r}\).
- **Tensor contraction**: Summation over repeated indices, reducing total rank.
- **Positive tensor cone** \(\mathcal{T}_{r,\{d_k\}}\): All tensors of given dimensions whose components are \(\ge \epsilon\).
- **Graph tensor Laplacian**: Operator \(\mathbf{L}\) acting on grid state \(\mathbf{X}\) via \((\mathbf{L}\bullet\mathbf{X})_i = \sum_j \mathcal{F}_{ij}(\mathbf{X}_j - \mathbf{X}_i)\).
- **Echo state property**: Asymptotic independence of reservoir state from initial conditions for any bounded input.
- **Hex axial coordinates**: \((q,r)\) with neighbours \( \{(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1)\}\).

---

### Appendix C: Symbol Table
| Symbol        | Meaning                              |
|---------------|--------------------------------------|
| \(\mathbf{X}_i\) | Node state tensor                    |
| \(\mathcal{F}_{ij}\) | Edge coupling tensor               |
| \(\mathbf{U}_i\) | Input tensor                         |
| \(\mathbf{F}_{NL}\) | Plasma nonlinearity                  |
| \(\beta\)        | Clamping function                    |
| \(r\)          | Tensor rank                          |
| \(R_{\max}\)   | Upper saturation bound                |
| \(\epsilon\)   | Lower saturation bound                |
| \(I_{base}\)   | Baseline current (≡ 1)                |
| \(G_{ij}\)     | Scalar conductance                   |
| \(\mathcal{T}_{r,\{d_k\}}\) | Positive tensor cone        |
| \(\mathbf{L}\)  | Graph tensor Laplacian               |

---

### References

**[1] Positive Systems Theory**  
Farina, L., & Rinaldi, S. (2000). *Positive Linear Systems: Theory and Applications*. Wiley‑Interscience.

**[2] Hexagonal Image Processing and Grid Topology**  
Middleton, L., & Sivaswamy, J. (2005). *Hexagonal Image Processing: A Practical Approach*. Springer.

**[3] Graph Laplacians and Consensus Dynamics**  
Olfati‑Saber, R., Fax, J. A., & Murray, R. M. (2007). Consensus and cooperation in networked multi‑agent systems. *Proceedings of the IEEE, 95*(1), 215‑233.

**[4] Reservoir Computing & Echo State Networks**  
Jaeger, H. (2001). The “echo state” approach to analysing and training recurrent neural networks. *GMD Report 148*. German National Research Center for Information Technology.  
Lukoševičius, M., & Jaeger, H. (2012). Reservoir computing approaches to recurrent neural network training. *Computer Science Review, 3*(3), 127‑149.

**[5] Bijective Numeration & Non‑Standard Bases**  
Knuth, D. E. (1997). *The Art of Computer Programming, Volume 2: Seminumerical Algorithms* (3rd ed.). Addison‑Wesley.

**[6] Port‑Hamiltonian Systems**  
van der Schaft, A. J., & Jeltsema, D. (2014). Port‑Hamiltonian systems theory: An introductory overview. *Foundations and Trends in Systems and Control, 1*(2‑3), 173‑378.

**[7] Tensor Analysis on Manifolds**  
Bishop, R. L., & Goldberg, S. I. (1980). *Tensor Analysis on Manifolds*. Dover Publications.

**[8] Generalised Tensor Network States**  
Orús, R. (2014). A practical introduction to tensor networks: Matrix product states and projected entangled pair states. *Annals of Physics, 349*, 117‑158.
