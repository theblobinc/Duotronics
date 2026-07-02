# A Zero-Free Algebraic Framework for Analog Computing: The Duotronic Hexagonal Grid

**Author(s):** Hugh Armstrong, TBI Contracting Inc
**Date:** July 2, 2026
**Subject Classifications:** Analog Computing, Neuromorphic Lattices, Zero-Free Signal Processing, Positive Systems Theory.

---

## Abstract
Traditional analog and neuromorphic computing paradigms suffer from significant instabilities due to the ambiguity of the "zero" state, which often sits at the noise floor of physical hardware. This paper introduces the **Duotronic Hexagonal Grid**, a robust, state-driven computing system that fundamentally eliminates the zero-state. By anchoring all logic, arithmetic, and physical measurement to an irreducible baseline current of unity (\(1\)), the system guarantees a deterministic, always-on operational environment. We define a novel arithmetic calculus utilizing Bijective Base-10, redefine addition and subtraction to preserve \(1\) as the neutral element, and map these states onto a hexagonal spatial lattice, functioning explicitly as a **physical reservoir**. We further demonstrate the physical implementation constraints for FPGA architectures and magnetic flux coupling, proving that even when external physical observables drop to zero, the system's internal state remains strictly positive.

---

## 1. Introduction
In conventional digital and analog processing, the absolute zero (\(0\)) is treated as the ground state—an absence of signal or charge. However, in physical hardware, particularly in analog amplifiers, memristors, and field-programmable gate arrays (FPGAs), the zero-state is notoriously non-trivial. Noise, leakage currents, and thermal drift degrade the precision of \(0\), rendering threshold detection unreliable.

The **Duotronic** paradigm refers to a dual-fluid electronic/physical computing architecture where a conductive mist and a glow-discharge plasma interact physically. The **Duotronic Hexagonal Grid** addresses previous paradigm flaws by redefining the baseline. Instead of absence, the foundational building block is an *irreducible, always-on glow discharge current* established at \(I_{base} = 1\). Consequently, all subsequent arithmetic and topology are computed not as *deviations from zero*, but as *deviations from unity*. 

The grid is intended to function as a **physical reservoir** (extending the Continuous-Time Recurrent Neural Network (CTRNN) framework). Computation occurs when input is injected into the network via node biases or modulating edge conductances, evolving the states of the nodes, and generating an output via a linear readout layer over the state vector. This architecture is notably analogous to biological neural circuits, which rarely exhibit complete silence, instead maintaining a baseline firing rate—a "spontaneous activity" that mirrors the Duotronic baseline. This report outlines the axiom, mathematics, spatial lattice, and hardware requirements of this zero-free computing system.

## 2. The Zero-Free Axiomatic Foundation
The core postulate of the Duotronic system is the existence of a persistent baseline energy state.

**Definition 2.1 (Baseline Unit):** Let the baseline current be defined as \(I_{base} = 1\). This is the universal identity and the irreducible quantum of system existence.

**Definition 2.2 (State Space):** For any system state \(x\), the following inequality must strictly hold:
\[
x > \epsilon \gt 0
\]
where \(\epsilon\) represents a microscopic real-valued threshold arbitrarily close to \(0\), yet strictly positive. In practical hardware, \(\epsilon\) is defined as the minimum sustainment current of the glow discharge or the lowest reliable ADC count above zero; this bound may vary per node and can be determined via hardware calibration. Thus, the state space \(\mathcal{S}\) is bounded by:
\[
\mathcal{S} \in [\epsilon, R_{max}] \subset \mathbb{R}_{>0}
\]

*Remark (Positive Systems):* This axiom guarantees that no logical or physical node is ever "off". In the broader mathematical literature, this places the system within the strict subset of **positive linear systems** (Farina & Rinaldi). Whereas standard positive systems generally allow \(x \ge 0\), the Duotronic constraint enforces the stronger condition of *strict* positivity (\(x \ge \epsilon > 0\)), ensuring absolute resilience against noise-floor collapse. A state of \(x < 1\) represents a *deficit* relative to the baseline, while \(x > 1\) represents an *excess*. In both cases, \(x\) maintains a physically measurable, positive amplitude. This is philosophically analogous to the quantum vacuum, which always possesses zero-point energy, ensuring "true zero" is unattainable even at the quantum scale.

## 3. Bijective Numeral System and Baseline-Aligned Arithmetic
To support a zero-free paradigm, the system employs a unique numerical representation and custom arithmetic operators tailored to preserve unity as the mathematical identity.

### 3.1 Bijective Base-10 Numeration
Standard positional numeral systems rely heavily on zero as a placeholder. The Duotronic system utilizes **Bijective Base-10** (also known as decimal without zero). 
*   **Digits:** \( \{1, 2, 3, 4, 5, 6, 7, 8, 9, A\} \) (where \(A\) represents the decimal value \(10\)).
*   **Properties:** The system contains no zero digit. Every string of digits corresponds to a unique, positive integer. This form of bijective numeration is well-known in combinatorial mathematics and has a rich historical precedent, dating back to ancient Greek and Hebrew numeral systems. Even in modern computing, such encodings are used in cryptography and serialization formats to avoid leading zeros.
*   **Representing Reals:** While the arithmetic operators work directly on real values (not digit strings), the system representation handles non-integers via a standard continued-fraction expansion or a fixed-point mantissa where the integer part utilizes the bijective base.

### 3.2 The Baseline-Aligned Operators
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

*Group-Theoretic Note:* It is important to note that \((S, \oplus)\) is isomorphic to the standard additive group \((\mathbb{R}, +)\) via the translation map \(x \mapsto x - 1\). Therefore, ideal versions of these operations maintain a clean algebraic structure. The physical nonlinearity is introduced solely by the clamping function \(\beta(x)\), which breaks the group symmetry in the limits of the dynamic range.

**3. Multiplication (\(\otimes\)) and Division (\(\oslash\)):**
For \(x, y \in \mathcal{S}\):
\[
x \otimes y = x \times y \quad \text{(Standard real multiplication)}
\]
\[
x \oslash y = x / y \quad \text{(Standard real division)}
\]
*Multiplicative Identity:* \(1 \otimes x = x\) (Since 1 is standard multiplicative identity).
*Remark:* In contrast to the additive side, the set \(\mathbb{R}_{>0}\) already forms a closed multiplicative group, requiring no adjustment.

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
This function acts as a monotonic, saturated nonlinearity. For \(\oplus\) and \(\ominus\), this transforms the arithmetic into **saturating fixed-point DSP operations**. Such saturation is not a drawback; in the context of physical reservoir computing, it prevents explosive divergence of the network states, effectively acting as a hard-bounding dissipative term. 

*(Footnote: While not idempotent, the hard lower-bound saturation bears a resemblance to the bounded nature of "tropical" or min-plus algebra, where standard addition is replaced by minimization. In the Duotronic system, however, standard addition is retained, but the results are bounded away from zero. For completeness, we note that log-domain processing (companding) is another common analog technique used to avoid zero, but it does so at the cost of introducing severe nonlinear distortions to the additive arithmetic domain. The Duotronic linear-offset approach elegantly preserves additive linearity within the clamped region, utilizing standard saturation rather than transcendental compression.)*

## 4. The Spatial Lattice: Hexagonal Topology
The mathematical states are physically distributed across a two-dimensional hexagonal grid, chosen for its superior symmetry and nearest-neighbor density.

### 4.1 Choice of Hexagonal Topology
The hexagonal tiling is specifically chosen over a Cartesian square grid for three distinct advantages: (1) Hexagonal grids offer higher sampling efficiency for circularly bandlimited signals. (2) They provide significantly more isotropic diffusion properties; the distance between the center of a hexagon and the center of all six of its neighbors is perfectly uniform, which is not true for the diagonal vs orthogonal neighbors in a square grid. (3) The maximal nearest-neighbor connectivity (6 neighbors in 2D) improves wave propagation and network mixing. This architectural preference is widely documented in image processing and cellular automaton literature.

### 4.2 Axial Coordinate System and Origin Relocation
The grid utilizes axial coordinates \((q,r)\). The six nearest-neighbor relationships (the Moore neighborhood of an infinite hex grid) are defined by the following vector shifts relative to a node \((q,r)\):
\[
\{(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)\}
\]

To geometrically embed the zero-free axiom, the Duotronic grid establishes its origin at **\((1,1)\)** on the axial axes, rather than the conventional \((0,0)\). This is a semantic shift; the underlying Euclidean geometry remains unchanged. The origin relocation ensures that no node carries an absolute zero index, perfectly aligning the spatial coordinates with the algebraic baseline of unity.

### 4.3 State Vector and Boundaries
Let \(\mathbf{x} = [x_1, x_2, \dots, x_N]^T\) be the state vector of the grid, where \(\mathbf{x} \in \mathbb{R}_{>0}^N\).
The grid's boundaries are governed by two predetermined modes:
1.  **Open boundaries:** Nodes on the perimeter have no outgoing flow to non-existent neighbors, effectively corresponding to physical containment walls.
2.  **Wrap-around (Toroidal boundaries):** Edges connect to opposite edges, ensuring every node has the full six-neighbor complement. This is highly useful for emulating infinite-domain partial differential equations (PDEs) and preserving translational invariance.

## 5. Topological Dynamics and Flow
Computation within this grid is driven by the physical flow of charge and pressure differentials between adjacent nodes.

### 5.1 Pressure Difference Formulation
Let \(p_i\) and \(p_j\) represent the current "pressure" (state value) at two adjacent nodes \(i\) and \(j\). The driving force for information flow is the pressure difference:
\[
\Delta p_{ij} = p_i - p_j
\]
*Consistency Note:* While the Duotronic domain uses specialized addition and subtraction (\(\oplus, \ominus\)) to maintain node states, this pressure gradient uses standard arithmetic subtraction. Given the underlying isomorphism of \((S, \oplus)\) to standard addition, taking the difference on raw state values yields the exact same result as \((p_i - 1) - (p_j - 1)\), making it perfectly consistent within the physical framework. Because the node states are constrained by the zero-free axiom, any directional flow reversal (negative sign) simply denotes net movement toward the lower-energy node.

### 5.2 Conductance and the Graph Laplacian
The volume of flow between \(i\) and \(j\) is governed by the conductivity coefficient \(G_{ij}\), which can be viewed as a learned synaptic weight or a fixed physical parameter of the hardware:
\[
Flow_{ij} = G_{ij} \cdot \Delta p_{ij}
\]
The nearest-neighbor connections define a graph with adjacency and degree matrices. The local connectivity diffuses information identically to the **graph Laplacian** framework. When the dynamics are expanded across all nodes, the system behaves as a classic **distributed averaging consensus protocol** widely used in distributed sensor networks.

### 5.3 Explicit State Update and Nonlinearity
In order to function as a computationally capable reservoir, the network must possess inherent nonlinearity. A purely linear diffusion network cannot separate complex input signals. In the Duotronic system, the nonlinearity does not reside in the diffusive flow itself, but rather in the plasma nodes. We define the explicit time-evolution equation for node \(i\) as a **Continuous-Time Recurrent Neural Network (CTRNN)**:
\[
\frac{dx_i}{dt} = \sum_{j \in \mathcal{N}(i)} G_{ij} (p_j - p_i) + \text{input}_i + \text{Plasma}_{NL}(x_i)
\]
Where \(\text{Plasma}_{NL}(x_i)\) represents the nonlinear transduction relationship generated by the local glow-discharge plasma. This nonlinearity is essential for computation. After each numerical integration step, the system state \(x_i\) is immediately passed through the clamping function \(\beta(\cdot)\) defined in Section 3.3. This ensures that the mathematical constraint \(x_i \in [\epsilon, R_{max}]\) is strictly enforced at all physical timesteps, preventing the accumulation of subtractive noise from collapsing a node to zero.

*Passivity Note:* The underlying diffusive coupling is strictly **passive**. From a port-Hamiltonian systems perspective, when combined with the external energy inputs sustaining the plasma, the network operates as a Hamiltonian dynamical system with dissipative damping, ensuring stability.

## 6. Physical Observability and Hardware Implementation
Translating this pure mathematical framework into physical hardware requires specific engineering constraints that map external physical phenomena to the baseline of unity.

### 6.1 Magnetically Coupled State Representation
A primary physical input mechanism can be derived from magnetic flux orientation. Let \(\Phi\) be the magnetic flux, \(B\) the magnetic field, and \(A\) the area, defined classically as:
\[
\Phi = BA \cos \theta
\]
In classical systems, when \(\theta = 90^\circ\), \(\Phi = 0\). In the Duotronic system, the physical measurement is modulated by the current \(I\) such that *even when* \(\Phi = 0\), the current remains at \(I = 1\).
This is achieved by the affine mapping \(I_{observed} = I_{base} + k \cos \theta\), where \(k\) is a hardware-specific scaling factor derived from the CPB's plasma transduction gain (\(k = B A \cdot \text{transduction gain}\)). 
*Bijection Note:* As long as \(k < I_{base}\), this mapping is **bijective** for \(\theta \in [0, \pi]\), ensuring that every input angle corresponds to a unique, strictly positive current without ambiguity.
*Observable examples:*
*   \(\theta = 0^\circ \rightarrow I = 1.48\)
*   \(\theta = 45^\circ \rightarrow I = 1.34\)
*   \(\theta = 90^\circ \rightarrow I = 1.00\) *(Baseline)*
*   \(\theta = 135^\circ \rightarrow I = 0.66\)
*   \(\theta = 180^\circ \rightarrow I = 0.52\)

*(Remark: This approach differs fundamentally from artificial mathematical remappings (e.g., exponential mappings like \(\Phi_w = BA e^{\cos\theta}\)) which require complex transcendental functions. The Duotronic framework achieves a zero-free measurement via the hardware's intrinsic physical baseline—no transcendental computations are required.)*

### 6.2 FPGA Integration Principles and Training Constraints
To implement this system on a Field Programmable Gate Array (FPGA), the following strict guidelines must be adhered to during data acquisition and processing:
1.  **Unsigned ADC Utilization:** Analog-to-digital converters (ADCs) must be configured as unsigned, reading values \(\ge 1\) Least Significant Bit (LSB). In unipolar sensor interfaces, this is equivalent to using an offset binary code, where the physical floor is shifted to 1.
2.  **Hardware Error Handling:** The system must reject any implicit state of \(0\). If an ADC reads \(0\), it is interpreted as a catastrophic missing-data error. Internal reservoir states must strictly reside in \(\mathbb{R}_{>0}^N\).
3.  **Saturation and Training Implications:** Because of the hard clamping function \(\beta(x)\), the dynamical system is **non-differentiable** at the saturation thresholds. However, in physical reservoir computing, training is conducted solely via linear regression on the final readout layer. Therefore, the non-differentiable internal dynamics pose no obstacle to standard linear training. For potential future use of gradient-based backpropagation through the reservoir, one could replace the hard clamp with a smooth alternative (e.g., a softplus or smooth clamping function).

## 7. Conclusion
The Duotronic Hexagonal Grid provides a radical but physically justified departure from traditional zero-based computing. By shifting the foundational baseline from \(0\) to \(1\), and by redesigning core arithmetic operators (\(\oplus, \ominus\)) to enforce this baseline, the architecture achieves a mathematically and physically closed system where *silence* does not exist. 

**Statement of Novelty:** To our knowledge, this is the first algebraic framework to definitively replace the additive identity with an active physical baseline for analog reservoir computing, and the first to map such arithmetic onto a hexagonal spatial lattice with physically realizable, strictly positive state constraints. 

The system is fundamentally Archimedean, with the caveat that the lower-bound clamp introduces a **pseudo-non-Archimedean** behavior akin to a minimum quantum of physical action. This makes it exceptionally resilient against hardware noise, leakage currents, and the stochastic nature of analog magnetic sensing. The integration of this arithmetic over a hexagonal spatial lattice offers a promising frontier for robust reservoir computing and neuromorphic hardware platforms, ensuring that "the origin is a presence, not an absence." Future work should include a formal information-theoretic analysis, quantifying how the persistent baseline guarantees a minimum Fisher information and entropy relative to standard zero-point noise.

---

### Appendix A: Working Examples of Arithmetic
*(Based on the infographic's sample data)*

In the examples provided from the infographic, a specific hardware calibration yields an illustrative lower bound of \(\epsilon = 0.40\). In a practical deployment, this floor would correspond to exactly 40% of the baseline value (1.0), representing the minimum sustainable plasma current threshold of a low-sensitivity node operating within a wide, deeply saturated dynamic range. While \(\epsilon\) can be calibrated per-node for optimal signal-to-noise ratio, we use this universal 0.40 value to demonstrate the saturation effect in the subtraction example below.

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
Farina, L., & Rinaldi, S. (2000). *Positive Linear Systems: Theory and Applications*. Wiley-Interscience.
> *Used to define the strict positivity constraint (\(x \ge \epsilon > 0\)) and compare it to standard non-negative systems.*

**[2] Hexagonal Image Processing and Grid Topology**
Middleton, L., & Sivaswamy, J. (2005). *Hexagonal Image Processing: A Practical Approach*. Springer.
> *Cited for the superior sampling efficiency, isotropic diffusion, and connectivity of hexagonal lattices compared to Cartesian grids.*

**[3] Graph Laplacians and Consensus Dynamics**
Olfati-Saber, R., Fax, J. A., & Murray, R. M. (2007). Consensus and cooperation in networked multi-agent systems. *Proceedings of the IEEE, 95*(1), 215-233.
> *Provides the foundational mathematical framework for the graph Laplacian dynamics and diffusive averaging flows utilized in Section 5.*

**[4] Reservoir Computing & Echo State Networks**
Jaeger, H. (2001). The "echo state" approach to analysing and training recurrent neural networks. *GMD Report 148*. German National Research Center for Information Technology.
> *Defines the concept of the physical reservoir and the use of linear readout layers for computation, as applied to the Duotronic Hexagonal Grid.*

**[5] Bijective Numeration & Non-Standard Bases**
Knuth, D. E. (1997). *The Art of Computer Programming, Volume 2: Seminumerical Algorithms* (3rd ed.). Addison-Wesley.
> *Addresses the mathematical history and combinatorial properties of bijective base-10 numeration systems (decimal without zero).*

**[6] Port-Hamiltonian Systems**
van der Schaft, A. J., & Jeltsema, D. (2014). Port-Hamiltonian systems theory: An introductory overview. *Foundations and Trends in Systems and Control, 1*(2-3), 173-378.
> *Provides the theoretical grounding for the passivity and energy-dissipative properties of the diffusive coupling network described in Section 5.3.*