# A Zero-Free Tensor Framework for Analog Computing: The Duotronic Hexagonal Grid

**Author(s):** Hugh Armstrong, TBI Contracting Inc
**Date:** July 2, 2026 (Revised August 2026)
**Subject Classifications:** Analog Computing, Tensor Networks, Positive Systems Theory, Neuromorphic Lattices, Zero-Free Signal Processing

---

## Abstract
Traditional analog and neuromorphic computing paradigms suffer from significant instabilities due to the ambiguity of the “zero” state, which often sits at the noise floor of physical hardware. This paper introduces the **Duotronic Hexagonal Grid**, a robust, state‑driven computing system that fundamentally eliminates the zero‑state. We recast the system in the language of **tensors over the positive reals**: the state of each node is a component of a rank‑1 tensor (a vector) that lives entirely in \(\mathbb{R}_{>0}^N\), the inter‑node coupling is a rank‑2 tensor (the conductance matrix), and the readout is again a rank‑1 tensor. By anchoring all logic, arithmetic, and physical measurement to an irreducible baseline current of unity (\(1\)), the system guarantees a deterministic, always‑on operational environment. We define a novel arithmetic calculus utilizing Bijective Base‑10, redefine addition and subtraction to preserve \(1\) as the neutral element, and map these strictly positive tensor components onto a hexagonal spatial lattice, functioning explicitly as a **physical reservoir**. The tensor viewpoint makes explicit the coordinate‑independence of the underlying physics and reveals that the Duotronic Hexagonal Grid is a multilinear machine whose components transform properly under changes of discretization or basis, while the positivity constraint keeps the state well clear of the fragile zero‑point. We further demonstrate the physical implementation constraints for FPGA architectures and magnetic flux coupling, proving that even when external physical observables drop to zero, the system’s internal tensor components remain strictly positive.

---

## 1. Introduction
In conventional digital and analog processing, the absolute zero (\(0\)) is treated as the ground state-an absence of signal or charge. However, in physical hardware, particularly in analog amplifiers, memristors, and field‑programmable gate arrays (FPGAs), the zero‑state is notoriously non‑trivial. Noise, leakage currents, and thermal drift degrade the precision of \(0\), rendering threshold detection unreliable.

The **Duotronic** paradigm refers to a dual‑fluid electronic/physical computing architecture where a conductive mist and a glow‑discharge plasma interact physically. The **Duotronic Hexagonal Grid** addresses previous paradigm flaws by redefining the baseline. Instead of absence, the foundational building block is an *irreducible, always‑on glow discharge current* established at \(I_{base} = 1\). Consequently, all subsequent arithmetic and topology are computed not as *deviations from zero*, but as *deviations from unity*. 

The grid is intended to function as a **physical reservoir** (extending the Continuous‑Time Recurrent Neural Network (CTRNN) framework). Computation occurs when input is injected into the network via node biases or modulating edge conductances, evolving the states of the nodes, and generating an output via a linear readout layer over the state vector.

**Why tensors?** A tensor is a multilinear machine that maps one set of vectors (or tensors) to another, and its defining property is that the physical result does not depend on the choice of coordinate axes. In the Duotronic Hexagonal Grid, the state \(\mathbf{x}\) is a **rank‑1 tensor** (a vector) living in the strictly positive cone \(\mathbb{R}_{>0}^N\). The inter‑node coupling is governed by the conductance matrix \(\mathbf{G}\), a **rank‑2 tensor** that linearly maps the state vector to the flow vector. The readout is again a **rank‑1 tensor** (a co‑vector) that extracts a scalar output. By formulating the entire computation in tensor language, we guarantee that any change of basis-whether a rotation of the spatial lattice, a permutation of the nodes, or a transformation to a modal representation-leaves the physical computation unchanged, while the positivity constraint keeps the tensor components safely bounded away from the information‑destroying zero. This tensor viewpoint unifies the bijective arithmetic, the hexagonal topology, and the reservoir dynamics into a single coherent framework.

---

## 2. The Zero‑Free Axiomatic Foundation
The core postulate of the Duotronic system is the existence of a persistent baseline energy state.

**Definition 2.1 (Baseline Unit):** Let the baseline current be defined as \(I_{base} = 1\). This is the universal identity and the irreducible quantum of system existence.

**Definition 2.2 (State Tensor Space):** The state of the network is a **rank‑1 tensor** (a vector) \(\mathbf{x} \in \mathcal{S}^N\) where the scalar components \(x_i\) are drawn from the strictly positive set \(\mathcal{S}\). For any component \(x_i\), the following inequality must strictly hold:
\[
x_i > \epsilon \gt 0
\]
where \(\epsilon\) represents a microscopic real‑valued threshold arbitrarily close to \(0\), yet strictly positive. In practical hardware, \(\epsilon\) is defined as the minimum sustainment current of the glow discharge or the lowest reliable ADC count above zero; this bound may vary per node and can be determined via hardware calibration. Thus, the state component space \(\mathcal{S}\) is bounded by:
\[
\mathcal{S} \in [\epsilon, R_{max}] \subset \mathbb{R}_{>0}
\]
Consequently, the state vector \(\mathbf{x}\) is a **rank‑1 tensor over the positive reals**; all its components are strictly positive. No node is ever “off.”

*Remark (Positive Systems and Tensors):* This axiom places the system within the strict subset of **positive linear systems**. Standard positive systems allow \(x \ge 0\); the Duotronic constraint enforces \(x \ge \epsilon > 0\). From a tensor perspective, the state space is a convex cone in \(\mathbb{R}^N\), and the coupling tensors (rank‑2) preserve this cone. The baseline \(1\) serves as the **affine origin** for the tensor components; a component \(x_i < 1\) represents a deficit, while \(x_i > 1\) represents an excess. Because the state vector never visits the zero subspace, the system’s Fisher information remains strictly positive, and the tensor transformation rules are well‑behaved under any basis change that respects the positivity constraint.

---

## 3. Bijective Numeral System and Baseline‑Aligned Arithmetic
To support a zero‑free paradigm, the system employs a unique numerical representation and custom arithmetic operators tailored to preserve unity as the mathematical identity.

### 3.1 Bijective Base‑10 Numeration
Standard positional numeral systems rely heavily on zero as a placeholder. The Duotronic system utilizes **Bijective Base‑10** (also known as decimal without zero). 
*   **Digits:** \( \{1, 2, 3, 4, 5, 6, 7, 8, 9, A\} \) (where \(A\) represents the decimal value \(10\)).
*   **Properties:** The system contains no zero digit. Every string of digits corresponds to a unique, positive integer. This form of bijective numeration is well‑known in combinatorial mathematics and has a rich historical precedent, dating back to ancient Greek and Hebrew numeral systems. Even in modern computing, such encodings are used in cryptography and serialization formats to avoid leading zeros.
*   **Representing Reals:** While the arithmetic operators work directly on real values (not digit strings), the system representation handles non‑integers via a standard continued‑fraction expansion or a fixed‑point mantissa where the integer part utilizes the bijective base.

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

*Group‑Theoretic and Tensor Note:* \((S, \oplus)\) is isomorphic to the standard additive group \((\mathbb{R}, +)\) via the translation map \(x \mapsto x - 1\). This isomorphism extends to the vector space: if we define the shifted state \(\tilde{\mathbf{x}} = \mathbf{x} - \mathbf{1}\), then the dynamics in \(\tilde{\mathbf{x}}\) are linear (up to clamping). The tensor operations (matrix‑vector multiplication) are performed on the shifted components, and then the baseline is added back. Thus the Duotronic arithmetic is precisely the **affine tensor algebra** that preserves the cone \(\mathbb{R}_{>0}^N\).

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
This function acts component‑wise on the state tensor \(\mathbf{x}\). It is a monotonic, saturated nonlinearity that ensures the tensor components never leave the allowed domain. For \(\oplus\) and \(\ominus\), this transforms the arithmetic into **saturating fixed‑point DSP operations** that preserve the positive cone.

*(Footnote: While not idempotent, the hard lower‑bound saturation resembles the bounded nature of “tropical” or min‑plus algebra. In the Duotronic system, standard addition is retained, but the results are bounded away from zero. Log‑domain processing is another alternative, but it introduces severe nonlinear distortions to the additive tensor structure. The Duotronic linear‑offset approach elegantly preserves additive linearity within the clamped region, maintaining the affine tensor structure while safeguarding against zero.)*

---

## 4. The Spatial Lattice as a Tensor Network: Hexagonal Topology
The physical tensor components are distributed across a two‑dimensional hexagonal grid, chosen for its superior symmetry and nearest‑neighbor density.

### 4.1 Choice of Hexagonal Topology
The hexagonal tiling is chosen over a Cartesian square grid for three distinct advantages: (1) Hexagonal grids offer higher sampling efficiency for circularly bandlimited signals. (2) They provide significantly more isotropic diffusion properties; the distance between the center of a hexagon and the center of all six of its neighbors is perfectly uniform, which is not true for the diagonal vs orthogonal neighbors in a square grid. (3) The maximal nearest‑neighbor connectivity (6 neighbors in 2D) improves wave propagation and network mixing. In tensor language, an isotropic rank‑2 diffusion tensor looks identical (up to a scalar) when expressed on a hexagonal lattice, whereas on a square grid the discrete Laplacian tensor has different weights for axial and diagonal neighbors, breaking isotropy.

### 4.2 Axial Coordinate System and Origin Relocation
The grid utilizes axial coordinates \((q,r)\). The six nearest‑neighbor relationships (the Moore neighborhood of an infinite hex grid) are defined by the following vector shifts relative to a node \((q,r)\):
\[
\{(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)\}
\]

To geometrically embed the zero‑free axiom, the Duotronic grid establishes its origin at **\((1,1)\)** on the axial axes, rather than the conventional \((0,0)\). This is a semantic shift; the underlying Euclidean geometry remains unchanged. The origin relocation ensures that no node carries an absolute zero index, perfectly aligning the spatial coordinates with the tensor component baseline of unity.

### 4.3 State Tensor and Boundaries
Let \(\mathbf{x} = [x_1, x_2, \dots, x_N]^T\) be the state vector (rank‑1 tensor) of the grid, where \(\mathbf{x} \in \mathbb{R}_{>0}^N\).
The grid’s boundaries are governed by two predetermined modes:
1.  **Open boundaries:** Nodes on the perimeter have no outgoing flow to non‑existent neighbors, effectively corresponding to physical containment walls. The coupling tensor (graph Laplacian) is modified accordingly at the boundary.
2.  **Wrap‑around (Toroidal boundaries):** Edges connect to opposite edges, ensuring every node has the full six‑neighbor complement. This makes the coupling tensor a circulant matrix, preserving translational invariance and allowing the simulation of infinite‑domain PDEs.

### 4.4 The Coupling Tensor: Rank‑2 Conductance on the Lattice
The inter‑node coupling is a **rank‑2 tensor** \(\mathbf{G}\) (the conductance matrix). In the standard basis, its components \(G_{ij}\) give the flow coefficient from node \(j\) to node \(i\). Because the lattice is nearest‑neighbor, \(\mathbf{G}\) is sparse (6 non‑zero entries per row). The tensor \(\mathbf{G}\) maps the state vector (rank‑1) to the diffusive flow vector (rank‑1):
\[
(\text{Flow})_i = \sum_{j} G_{ij} (p_j - p_i)
\]
Under a change of basis-for example, relabeling nodes, rotating the coordinate system, or transforming to a modal (Fourier) representation on the hex grid-the components of \(\mathbf{G}\) transform according to the tensor transformation law \(\mathbf{G}' = \mathbf{P} \mathbf{G} \mathbf{P}^{-1}\), while the physical flow vector remains invariant. The positivity of the state components is preserved under any basis change that respects the cone.

---

## 5. Topological Dynamics as Tensor Flow
Computation within this grid is driven by the physical flow of charge and pressure differentials between adjacent nodes, which can be expressed entirely in the language of tensor algebra.

### 5.1 Pressure Difference as a Tensor Contraction
Let \(p_i\) and \(p_j\) represent the current “pressure” (state component) at two adjacent nodes \(i\) and \(j\). The driving force for information flow is the pressure difference:
\[
\Delta p_{ij} = p_i - p_j
\]
*Consistency Note:* While the Duotronic domain uses specialized addition and subtraction (\(\oplus, \ominus\)) to maintain node states, this pressure gradient uses standard arithmetic subtraction. Because the additive group is isomorphic to standard addition via the baseline shift, the difference computed on the raw state components is identical to the difference of the shifted components \((p_i - 1) - (p_j - 1)\). Thus the tensor contraction \(\mathbf{G} \cdot (\mathbf{1} - \mathbf{P})\) (where \(\mathbf{P}\) is an appropriate permutation) is perfectly consistent within the framework.

### 5.2 The Graph Laplacian as a Rank‑2 Tensor
The volume of flow between \(i\) and \(j\) is governed by the conductivity coefficient \(G_{ij}\), which can be viewed as a learned synaptic weight or a fixed physical parameter of the hardware:
\[
Flow_{ij} = G_{ij} \cdot \Delta p_{ij}
\]
Assembling these flows yields the **graph Laplacian** tensor \(\mathbf{L}\), a rank‑2 tensor defined by \(L_{ij} = -G_{ij}\) for \(i \neq j\) and \(L_{ii} = \sum_{j} G_{ij}\). The diffusive dynamics then become \(\dot{\mathbf{x}} = -\mathbf{L} \mathbf{x} + \dots\). This is a classic **distributed averaging consensus protocol**; the tensor \(\mathbf{L}\) is symmetric positive semi‑definite (in the metric of the positive cone) and encodes the topology of the lattice.

### 5.3 Explicit State Update: A Tensor ODE
The full time‑evolution equation for the state tensor \(\mathbf{x}(t)\) is a **Continuous‑Time Recurrent Neural Network (CTRNN)**:
\[
\frac{d\mathbf{x}}{dt} = \mathbf{L} \mathbf{x} + \mathbf{u} + \mathbf{f}_{NL}(\mathbf{x})
\]
Here \(\mathbf{u}\) is the input tensor (rank‑1), \(\mathbf{L}\) is the rank‑2 Laplacian tensor, and \(\mathbf{f}_{NL}(\mathbf{x})\) is a component‑wise nonlinearity derived from the plasma (the Townsend activation in the CPB context). After each numerical integration step, the state tensor \(\mathbf{x}\) is passed through the component‑wise clamping function \(\beta(\cdot)\) of Section 3.3, ensuring that every component remains in \(\mathcal{S}\). This clamping operation can be viewed as a **rank‑preserving nonlinear tensor map** that enforces the positivity constraint.

*Passivity Note:* The diffusive coupling tensor \(\mathbf{L}\) is strictly **passive**. From a port‑Hamiltonian perspective, the tensor \(\mathbf{L}\) defines the dissipation structure, and the system’s energy flows are governed by symmetric tensor contractions, guaranteeing stability.

---

## 6. Physical Observability and Tensor Readout
Translating this tensor framework into physical hardware requires specific engineering constraints that map external physical phenomena to the baseline of unity.

### 6.1 Magnetically Coupled Input Tensor
A primary physical input mechanism can be derived from magnetic flux orientation. Let \(\Phi\) be the magnetic flux, \(B\) the magnetic field, and \(A\) the area, defined classically as:
\[
\Phi = BA \cos \theta
\]
In classical systems, when \(\theta = 90^\circ\), \(\Phi = 0\). In the Duotronic system, the physical measurement is modulated by the current \(I\) such that *even when* \(\Phi = 0\), the current remains at \(I = 1\).
This is achieved by the affine mapping \(I_{observed} = I_{base} + k \cos \theta\), where \(k\) is a hardware‑specific scaling factor derived from the CPB’s plasma transduction gain (\(k = B A \cdot \text{transduction gain}\)). 
*Bijection Note:* As long as \(k < I_{base}\), this mapping is **bijective** for \(\theta \in [0, \pi]\), ensuring that every input angle corresponds to a unique, strictly positive current without ambiguity. The input vector \(\mathbf{u}\) thus has components drawn from this mapping, keeping the input tensor in \(\mathbb{R}_{>0}^M\).
*Observable examples:*
*   \(\theta = 0^\circ \rightarrow I = 1.48\)
*   \(\theta = 45^\circ \rightarrow I = 1.34\)
*   \(\theta = 90^\circ \rightarrow I = 1.00\) *(Baseline)*
*   \(\theta = 135^\circ \rightarrow I = 0.66\)
*   \(\theta = 180^\circ \rightarrow I = 0.52\)

### 6.2 Tensor Readout and FPGA Integration
The output of the computation is a linear combination of the state components, i.e., a **rank‑1 tensor readout** (co‑vector) \(\mathbf{w}_{\text{out}}\) applied to the state tensor \(\mathbf{x}\):
\[
y = \mathbf{w}_{\text{out}}^T \mathbf{x}
\]
The weights \(\mathbf{w}_{\text{out}}\) are trained by linear regression, with the state components always strictly positive. On the FPGA, the following strict guidelines are adhered to:
1.  **Unsigned ADC Utilization:** ADCs must be configured as unsigned, reading values \(\ge 1\) LSB; the physical floor is shifted to 1.
2.  **Hardware Error Handling:** A reading of \(0\) is interpreted as a catastrophic missing‑data error. Internal reservoir states must strictly reside in \(\mathbb{R}_{>0}^N\).
3.  **Saturation and Training:** The hard clamping \(\beta(x)\) makes the dynamics non‑differentiable at the saturation boundaries, but since training uses only linear regression on the final readout tensor, this poses no obstacle. For possible future gradient‑based learning, a smooth tensor clamping (e.g., softplus) can be substituted.

The entire tensor algebra (matrix‑vector multiply, affine offset, clamping) can be implemented in fixed‑point DSP on the FPGA, ensuring deterministic, low‑latency tensor contractions.

---

## 7. Conclusion
The Duotronic Hexagonal Grid provides a radical but physically justified departure from traditional zero‑based computing. By shifting the foundational baseline from \(0\) to \(1\), and by redesigning core arithmetic operators (\(\oplus, \ominus\)) to enforce this baseline, the architecture achieves a mathematically and physically closed system where *silence* does not exist. 

**Tensor‑Theoretic Novelty:** We have reformulated the entire grid as a **strictly positive tensor network**: the state is a rank‑1 tensor in \(\mathbb{R}_{>0}^N\), the coupling is a rank‑2 tensor (the graph Laplacian), the input and readout are rank‑1 tensors, and the arithmetic operations preserve the positive cone under affine shifts. This tensor viewpoint makes manifest the coordinate‑independence of the computation and reveals that the Duotronic Hexagonal Grid is a multilinear machine whose components transform properly under changes of discretization or basis, while the positivity constraint keeps the state well clear of the fragile zero‑point. 

The system is fundamentally Archimedean, with the caveat that the lower‑bound clamp introduces a **pseudo‑non‑Archimedean** behavior akin to a minimum quantum of physical action. This makes it exceptionally resilient against hardware noise, leakage currents, and the stochastic nature of analog magnetic sensing. The integration of this positive‑tensor arithmetic over a hexagonal spatial lattice offers a promising frontier for robust reservoir computing and neuromorphic hardware platforms, ensuring that “the origin is a presence, not an absence.” Future work should include a formal information‑theoretic analysis of the tensor cone, quantifying how the persistent baseline guarantees a minimum Fisher information and entropy relative to standard zero‑point noise.

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

### References

To ground the interdisciplinary concepts presented in this paper, we provide the following references which form the theoretical backbone of the Duotronic architecture.

**[1] Positive Systems Theory**
Farina, L., & Rinaldi, S. (2000). *Positive Linear Systems: Theory and Applications*. Wiley‑Interscience.
> *Used to define the strict positivity constraint (\(x \ge \epsilon > 0\)) and its tensor‑cone implications.*

**[2] Hexagonal Image Processing and Grid Topology**
Middleton, L., & Sivaswamy, J. (2005). *Hexagonal Image Processing: A Practical Approach*. Springer.
> *Cited for the superior sampling efficiency, isotropic diffusion, and connectivity of hexagonal lattices compared to Cartesian grids, which makes the discrete Laplacian tensor more isotropic.*

**[3] Graph Laplacians and Consensus Dynamics**
Olfati‑Saber, R., Fax, J. A., & Murray, R. M. (2007). Consensus and cooperation in networked multi‑agent systems. *Proceedings of the IEEE, 95*(1), 215‑233.
> *Provides the foundational tensor (graph Laplacian) framework for diffusive averaging flows utilized in Section 5.*

**[4] Reservoir Computing & Echo State Networks**
Jaeger, H. (2001). The “echo state” approach to analysing and training recurrent neural networks. *GMD Report 148*. German National Research Center for Information Technology.
> *Defines the concept of the physical reservoir and the use of linear readout tensors for computation.*

**[5] Bijective Numeration & Non‑Standard Bases**
Knuth, D. E. (1997). *The Art of Computer Programming, Volume 2: Seminumerical Algorithms* (3rd ed.). Addison‑Wesley.
> *Addresses the mathematical history and combinatorial properties of bijective base‑10 numeration systems (decimal without zero).*

**[6] Port‑Hamiltonian Systems**
van der Schaft, A. J., & Jeltsema, D. (2014). Port‑Hamiltonian systems theory: An introductory overview. *Foundations and Trends in Systems and Control, 1*(2‑3), 173‑378.
> *Provides the theoretical grounding for the passivity and tensor dissipation structure of the diffusive coupling network.*

**[7] Tensor Analysis on Manifolds**
Bishop, R. L., & Goldberg, S. I. (1980). *Tensor Analysis on Manifolds*. Dover Publications.
> *General reference for the coordinate‑invariance and multilinear machine viewpoint of tensors adopted in this paper.*
