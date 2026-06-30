**ENGINEERING SPECIFICATION**

# Coherent Particle Beam (CPB) Device:  
Multi‑Modal Open‑Atmosphere Particle Valve

**Document ID:** CPB‑ENG‑001  
**Revision:** 4.0  
**Date:** 2026-07-02  
**Classification:** Technical Engineering Document  

---

## 1. Overview

The Coherent Particle Beam device is a compact, electro‑fluidic particle source built around a self‑pumping Bernoulli vacuum stage. In its **Core Plasma Module** it operates at 30-80 mbar, producing a collisional plasma jet for soft X‑ray generation, plasma RF antennas, and surface treatment. An optional **High‑Vacuum (HV) Stage** adds a turbomolecular pump to achieve ballistic acceleration of electrons and ions up to 100 keV, enabling focused beam modes and neutron production. All modes are explicitly differentiated by their pressure regime and underlying physics.

This document is a living specification; experimental validation will progressively replace estimated parameters with measured values.

---

# 2. Engineering Requirements

## 2.1 Core Plasma Jet Module (Collisional, 30-80 mbar)

The Core module produces a **collisional plasma jet**, not a coherent particle beam. All performance values are design targets requiring experimental validation.

| Parameter                          | Requirement                                              | Confidence | Validation Method                                                       |
| ---------------------------------- | -------------------------------------------------------- | ---------- | ----------------------------------------------------------------------- |
| Operating pressure (drift tube)    | 30-80 mbar                                               | Medium     | Calibrated pressure transducers (Kulite XCQ‑093), repeatability ±5 mbar |
| Pressure stability                 | ±10 mbar                                                 | Medium     | Continuous logging during 1 h operation                                 |
| Electron energy (afterglow)        | 0.2-2 keV                                                | Medium     | Retarding‑field analyser and X‑ray spectrum                             |
| Plasma current                     | 10 µA - 2 mA                                             | High       | Faraday cup (±1.5 %)                                                    |
| Plasma jet divergence (half‑angle) | <10°                                                     | Low        | Optical imaging and phosphor target                                     |
| Maximum operating voltage          | ±10 kV                                                   | High       | Calibrated HV divider                                                   |
| HV ripple                          | <1 % p‑p                                                 | High       | High‑voltage oscilloscope probe                                         |
| Duty cycle                         | Continuous (100 %)                                       | Medium     | 8‑hour endurance test                                                   |
| Core thermal load                  | ≤50 W                                                    | Medium     | Embedded thermocouples and IR imaging                                   |
| MTBF (excluding consumables)       | >500 h                                                   | Low        | Operational reliability testing                                         |
| Plasma stability                   | Continuous operation without self‑extinguishing for >1 h | Medium     | Automated discharge monitoring                                          |
| Current regulation bandwidth       | >1 kHz                                                   | Medium     | Closed‑loop step response                                               |

**Core Module Status:** Prototype engineering target. Performance values require experimental validation.

---

## 2.2 High‑Vacuum Beam Module (Ballistic, <10⁻⁵ mbar)

All HV‑mode parameters are **preliminary design targets** derived from scaling laws and literature. Confidence levels are deliberately conservative; values will be updated after construction and commissioning.

| Parameter                     | Requirement                              | Confidence | Validation Method                                 |
| ----------------------------- | ---------------------------------------- | ---------- | ------------------------------------------------- |
| Base pressure                 | <10⁻⁵ mbar                               | High       | Pirani + cold‑cathode gauges                      |
| Pump‑down time                | <30 min                                  | Medium     | Logged vacuum profile                             |
| Electron energy               | 5-100 keV                                | Low        | Retarding‑field analyser, X‑ray endpoint spectrum |
| Ion energy (H⁺, D⁺, He⁺)      | 10-300 keV                               | Low        | Acceleration voltage; time‑of‑flight (future)     |
| Beam current                  | 10 µA - 2 mA                             | Low        | Faraday cup                                       |
| Beam divergence (half‑angle)  | <5°                                      | Low        | Phosphor screen imaging                           |
| Normalised emittance (εₙ)     | ≤50 mm·mrad (design target)              | Low        | Pepper‑pot / slit‑scan diagnostic                 |
| Beam brightness (B)           | ≥5×10⁵ A/(m²·rad²) (predicted)           | Low        | Derived from emittance measurements               |
| Electron energy spread (FWHM) | <5 %                                     | Low        | Retarding‑field analyser                          |
| Beam spot diameter            | ≤500 µm at 100 keV, 1 mA                 | Low        | Knife‑edge scan and phosphor imaging              |
| Maximum HV supply             | ±100 kV operating (±120 kV design)       | High       | Calibrated HV divider                             |
| HV ripple                     | <0.1 % p‑p                               | High       | HV oscilloscope probe                             |
| Stored energy                 | <3 J                                     | Medium     | Capacitance measurement and calculation           |
| Target heat load              | ≤100 W at 100 keV, 1 mA                  | High       | Beam power calculation and calorimetry            |
| Target cooling capacity       | ≥200 W                                   | High       | Flow and thermal testing                          |
| Neutron yield (D‑D, 100 keV)  | ≥1×10⁵ n/s at 0.1 mA (design target)     | Low        | Calibrated neutron detector                       |
| X‑ray shielding               | <1 µSv/h at 30 cm (with shielding)       | High       | Survey meter measurements                         |
| Beam alignment repeatability  | <100 µm                                  | Low        | Alignment fixture and beam diagnostics            |

**HV Module Status:** Preliminary design targets only. All performance values require validation after prototype construction. Conservative estimates have been adopted pending experimental demonstration.

---

## 2.3 Parameter Provenance

| Confidence | Definition                                                                                                           |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| **High**   | Established by accepted physics, commercial hardware specifications, or direct calculation.                          |
| **Medium** | Supported by analytical models, simulations, or published literature, but requires confirmation in the CPB geometry. |
| **Low**    | Preliminary design target or engineering estimate requiring prototype validation.                                    |

## 2.4 Requirement Classification

| Classification      | Meaning                                                                                         |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| **Requirement**     | Mandatory engineering specification that the system must satisfy.                               |
| **Design Target**   | Expected performance based on calculations or literature; subject to experimental verification. |
| **Measured Value**  | Parameter verified experimentally and traceable to calibrated instrumentation.                  |
| **Predicted Value** | Derived from analytical models or numerical simulations awaiting validation.                    |

**Note:** Unless otherwise stated, all performance values in this specification are **design targets**. Parameters will transition to **measured values** as experimental validation progresses. This specification is intended to evolve alongside prototype development.

---

# 3. Physical Configuration

## 3.1 Inner Drift Tube

The inner drift tube forms the primary plasma channel in Core Plasma Jet Mode and the accelerating drift region in High‑Vacuum Beam Mode. It serves as the electrical reference geometry and the primary vacuum boundary for the optional high‑vacuum configuration.

**Material**  
- **Prototype:** Platinum‑clad (electroplated) 316L stainless steel, or Nickel 200.  
- **Validated geometry (later builds):** Platinum or Platinum‑Iridium (90/10).  
- **HV‑only option:** Molybdenum (requires oxidation protection).

Materials shall be chemically compatible with water mist, saline aerosols, hydrogen, deuterium, helium, and air. A full compatibility matrix is maintained in Appendix C.

**Dimensions**

| Parameter         | Value     | Tolerance                |
| ----------------- | --------- | ------------------------ |
| Length            | 80-150 mm | ±0.5 mm                  |
| Internal diameter | 2.00 mm   | ±0.02 mm                 |
| Wall thickness    | 0.30 mm   | ±0.05 mm                 |
| Straightness      | <0.05 mm  | over full length         |
| Concentricity     | <0.05 mm  | relative to outer casing |

**Surface Finish**  
- Internal bore: Ra ≤ 0.40 µm, electropolished to minimise field emission.  
- External: Ra ≤ 0.80 µm.

**Operating Modes**

*Core Plasma Jet Mode*  
- Rear end sealed with electrode feedthrough.  
- Front end opens into the collector/shroud region.

*High‑Vacuum Beam Mode*  
- Front end connects via a CF‑16 flange and all‑metal gate valve.  
- A 300 L s⁻¹ turbomolecular pump is mounted downstream of the valve.

**Manufacturing Notes**  
- Tube shall be vacuum cleaned and baked before assembly.  
- Ceramic‑compatible brazing alloys only.  
- All wetted surfaces free of machining oils, chlorides, and hydrocarbons.

**Cost Note**  
Initial prototypes shall use platinum‑clad steel or nickel. Solid platinum components are reserved for later validation units after the geometry and operating envelope have been experimentally verified.

---

## 3.2 Toroidal Emitter Assembly

The emitter provides the primary charged‑particle source.

### Geometry

| Parameter | Value |
|-----------|-------|
| Major diameter | 2.00 ± 0.05 mm |
| Minor diameter | 0.50 ± 0.02 mm |
| **Emitter‑to‑tube radial clearance** | **0.75 ± 0.10 mm** (critical for Paschen breakdown; see §4.3) |

### Primary Materials

- **Preferred:** Lanthanum Hexaboride (LaB₆, φ ≈ 2.6 eV) - non‑radioactive.  
- **Alternatives:** W‑2 % ThO₂ (requires radiation handling plan), Hafnium carbide, Tungsten, Gallium‑Indium liquid metal emitter.

### Mounting

- Insulator: 99.8 % Alumina or Boron Nitride.  
- Vacuum‑compatible ceramic feedthrough; torque 0.40 ± 0.05 N·m.

### Operating Regimes

#### Core Plasma Jet Mode (Collisional)
- **Dominant mechanism:** Glow discharge.  
- **Primary electron source:** Secondary emission from ion bombardment.  
- **Electron energies:** 200-600 eV in air; up to ~2 keV in hydrogen with suitable cathode materials.  
- **Behaviour:** Collisional plasma; no ballistic beam.

#### High‑Vacuum Beam Mode (Ballistic)
- **Dominant mechanism:** Fowler‑Nordheim field emission.  
- **Field enhancement factor β** will be extracted from experimental Fowler‑Nordheim plots; initial estimate β ≈ 50-100.  
- Surface conditioning, adsorbates, and work‑function variations may significantly affect emission; periodic in‑situ conditioning is planned.

---

## 3.3 Modulation Grid

**Construction**  
- Pt‑Ir wire, diameter 0.10 ± 0.01 mm.  
- Positioned 1-2 mm inside the drift tube exit.  
- Isolated from the tube by machinable ceramic spacers.

**Driver**  
- Wideband buffer amplifier (e.g., THS3491), bandwidth 200 MHz.  
- Load capacitance 5-20 pF; bias ±100 V.  
- Minimum pulse width 10 ns; maximum repetition rate 10 MHz.  
- Rise time target <5 ns.

*Note: For Core plasma modulation, a lower‑bandwidth amplifier may suffice and is acceptable for initial tests.*

---

## 3.4 Collector Assembly (Core Plasma Jet Mode)

**Material**  
- Platinum‑clad or tungsten‑lined 316L stainless steel.

**Geometry**  
- Concentric cylinder, ID 8.00 ± 0.05 mm, extending 15 mm beyond the drift tube exit.

**Functions**  
- Collector / ground reference.  
- Plasma stabilisation.  
- Thermal sink.  
- In HV Beam Mode, this assembly is replaced by the beam‑line.

---

## 3.5 Bernoulli Vacuum Stage

The Bernoulli stage maintains the 30-80 mbar operating environment for Core Plasma Jet Mode. It is the **highest‑risk subsystem** of the entire platform and will be validated first.

### Design Parameters

| Parameter | Target | Status |
|-----------|--------|--------|
| Drive pressure | 3-5 bar (gauge) | Design |
| Drive gas flow rate (STP) | 30-60 L min⁻¹ | Estimated |
| Drift tube pressure | 30-80 mbar | Experimental target |
| Pressure stability | ±10 mbar | Design target |
| Entrainment ratio | 1.5-3.0 | Estimated from CFD |

### Instrumentation  
- Pressure: Kulite XCQ‑093 transducers; optional Pirani gauge for cross‑check.  
- Flow: Mass flow controller + thermal flow meter.  
- Temperature: PT100 RTDs.  
- Gas composition: Residual gas analyser (HV mode) or quadrupole mass spectrometer (future).

### Engineering Risks & Validation  
- Primary uncertainties: back‑diffusion of atmospheric gases, mist loading effects, boundary‑layer separation, and compressor stability.  
- Phase 2 testing will map pressure profiles, quantify entrainment ratio, and correlate CFD models before further development.

---

## 3.6 Conductive Working Fluid (Mist)

The conductive aerosol provides charge transport, plasma stabilisation, and optional chemical functionality.

**Atomisation:** Ultrasonic nebuliser (1-5 MHz) or high‑pressure nozzle. Median droplet diameter 2-5 µm, span <1.5.

**Electrical Properties:** Charge relaxation time τ = ε₀εᵣ/σ. For 3 % saline, τ ≈ 1.4×10⁻¹⁰ s - effectively instantaneous. Droplets may approach the Rayleigh limit; Coulomb fission and evaporation will be studied experimentally.

**Required Characterisation (Pre‑Plasma Phase):**  
- Droplet size distribution (laser diffraction).  
- Charge distribution (Faraday pail).  
- Electrical conductivity vs. concentration.  
- Evaporation rate and residence time.  
- Mobility in electric fields.  
- Deposition on insulators and electrodes.

A **dedicated aerosol‑only test cell** will be constructed to quantify these parameters before integrating the plasma discharge. This phase is a prerequisite for Core Mode validation.

**Maintenance:** Filters will protect ceramics, optics, and pressure sensors; mist residues will be flushed periodically.

---

## 3.7 High‑Voltage Supply

Two configurations:  
- **Core Plasma Jet:** 0-12 kV design, operating ±10 kV, current‑limited.  
- **High‑Vacuum Beam:** 0-120 kV design, operating ±100 kV.

| Parameter | Core | HV |
|-----------|------|----|
| Ripple (p‑p) | <1 % | <0.1 % |
| Regulation bandwidth | >1 kHz | >1 kHz |
| Current limit | 0-5 mA | 0-5 mA |
| Stored energy | <1 J | <3 J |

**Protection:** Fast crowbar, current‑limiting resistor, arc detection, ground continuity monitor, emergency discharge relay, and fully interlocked enclosure.

---

## 3.8 Beam Optics (HV Beam Mode Only)

Beam transport uses an electrostatic immersion lens formed by the drift tube exit and a downstream grounded aperture. Optional magnetic correction (SmCo ring or air‑core solenoid) provides fine focus and steering.

**Design Targets (Conservative, Pre‑Validation):**

| Parameter | Design Target | Status |
|-----------|---------------|--------|
| Spot diameter | ≤500 µm at 100 keV, 1 mA | Predicted |
| Normalised emittance | ≤50 mm·mrad | Estimated |
| Beam brightness | ≥5×10⁵ A/(m²·rad²) | Predicted |

These values are deliberately conservative and will be refined using SIMION simulations and pepper‑pot/slit‑scan measurements after beam commissioning. The ambitious values of earlier revisions (≤200 µm, ≤20 mm·mrad) are retained as stretch goals but are not baseline requirements.

---

## 3.9 Target Assembly and Thermal Management (HV Mode)

**Target:** OFHC copper core, 5 µm titanium coating. For neutron generation, the titanium is converted to TiD₂ by in‑situ deuterium loading.

**Beam Power:** 100 keV × 1 mA = 100 W deposited into the target. The spot size (≤500 µm) leads to a power density ~5×10⁸ W m⁻²; effective heat spreading is critical. A water‑glycol cooling loop removes up to 200 W. Thermal FEA will be validated against calorimetric measurements.

**Instrumentation:** Embedded thermocouples, RTDs, IR camera, and flow sensors. A beam‑trip interlock is triggered if the target temperature exceeds 400 °C.

---

## 3.10 Ion Source (HV Beam Mode)

Supported configurations: hollow‑cathode insert or ECR source (2.45 GHz).  
Operating gases: H₂, D₂, He, Ar.  
Ion species and energy distributions will be characterised with a retarding‑field analyser before accelerator operation.

---

## 3.11 High‑Vacuum System

**Components:**  
- Oil‑free scroll roughing pump (15 m³ h⁻¹).  
- Turbomolecular pump (300 L s⁻¹ for N₂) with integrated controller.  
- All‑metal gate valve (DN 16 CF).  
- Full‑range gauge (Pirani + cold cathode).  
- Residual gas analyser (**mandatory** for D₂ operation to verify gas purity).

**Performance:** Base pressure <10⁻⁵ mbar, pump‑down <30 min, bake‑out at 150 °C for 24 h. Conductance calculations will be performed to confirm effective pumping speed at the drift tube.

---

## 3.12 Diagnostics Integration

Dedicated diagnostic ports are provided for:  
- Faraday cup, retarding‑field analyser, phosphor screen, pepper‑pot mask.  
- Optical viewport for emission spectroscopy.  
- X‑ray detector (Si‑PIN or CdTe).  
- Neutron detector (stilbene+SiPM) and activation foils (HV mode).  
- Pressure transducers, flow meters, thermocouples.

Ports allow insertion/retraction without breaking vacuum or major disassembly.

---

## 3.13 Manufacturing and Assembly

Precision components are manufactured to documented tolerances and inspected before assembly. Assembly includes ultrasonic cleaning, vacuum‑compatible handling, torque‑controlled fasteners, electrical continuity and high‑pot testing, leak checking (HV mode), alignment verification, and pressure calibration.

---

## 3.14 Prototype Cost and Development Strategy

Development proceeds in five gated phases (see §9). **Phase 1** uses low‑cost materials (Pt‑clad steel, commercial nebulisers) to validate the Bernoulli stage and mechanical fit. **Phase 2** adds the glow‑discharge plasma and aerosol transport, completing Core Plasma Jet validation. **Phase 3** integrates the high‑vacuum system and HV supply; beam commissioning begins in **Phase 4**. **Phase 5** covers advanced experiments (ion beams, neutrons) only after all safety reviews.

A preliminary Bill of Materials with cost ranges is provided in Appendix B. The phased approach limits financial exposure and ensures that no subsystem advances beyond its experimentally validated maturity.

---

# 4. Physics Basis and Regime Transitions

This section defines the governing physical principles underlying the Coherent Particle Beam (CPB) platform. Two fundamentally different operating regimes are supported:

- **Core Plasma Jet Mode:** Low-pressure (30-80 mbar), collisional glow-discharge plasma. Transport is dominated by electron‑neutral and ion‑neutral collisions; the output is a weakly ionised plasma jet, not a ballistic beam.
- **High‑Vacuum Beam Mode (HV‑CPB):** High‑vacuum (<10⁻⁵ mbar) electrostatic accelerator operating under conventional charged‑particle beam physics.

The transition between these regimes is determined primarily by gas density, mean free path, and plasma formation, not by electrode geometry alone. Unless otherwise stated, numerical values are design estimates based on published literature and require experimental validation.

---

## 4.1 Transport Regimes and Mean Free Path

The electron (or ion) mean free path λ is given by

\[
\lambda = \frac{1}{n\sigma}
\]

where

- *n* = neutral gas number density  
- *σ* = total collision cross‑section (elastic + inelastic) for the relevant particle energy and gas species.

Gas density follows the ideal gas law

\[
n = \frac{P}{k_B T}
\]

At 300 K:

| Pressure    | Number Density (m⁻³) |
|-------------|-----------------------|
| Atmospheric (1013 mbar) | 2.45 × 10²⁵ |
| 30 mbar     | 7.2 × 10²³ |
| 50 mbar     | 1.2 × 10²⁴ |
| 1 mbar      | 2.4 × 10²² |
| 10⁻³ mbar   | 2.4 × 10¹⁹ |
| 10⁻⁵ mbar   | 2.4 × 10¹⁷ |

Approximate electron mean free paths in **air** (cross‑sections from NIST and LXCat [8,11]):

| Electron Energy | 30 mbar  | 1 mbar   | 10⁻³ mbar | 10⁻⁵ mbar |
|----------------|----------|----------|-----------|-----------|
| 1 keV          | 28 µm    | 0.84 mm  | 8.4 cm    | 8.4 m     |
| 10 keV         | 0.10 mm  | 3 mm     | 30 cm     | 30 m      |
| 100 keV        | 0.28 mm  | 8.4 mm   | 84 cm     | 84 m      |

*In hydrogen or deuterium, cross‑sections are typically a factor 3-5 smaller, increasing λ by the same factor. Nevertheless, even in H₂ at 30 mbar, λ(100 keV) ≈ 1 mm, still far shorter than the 100 mm drift tube.*

**Conclusion:**  
- At 30-80 mbar, every particle undergoes many collisions while traversing the drift tube; transport is **collisional** and the device produces a plasma jet, not a directed beam.  
- To achieve true ballistic transport (λ ≫ tube length), the pressure must be reduced to the molecular‑flow regime, i.e., <10⁻⁵ mbar. This is accomplished by the HV vacuum stage.

---

## 4.2 Operating Regime Map

The CPB platform intentionally operates in multiple physical regimes, accessed by varying pressure, voltage, and current.

| Regime                       | Pressure            | Dominant Physics            | Expected Behaviour                |
|------------------------------|---------------------|-----------------------------|-----------------------------------|
| Corona / streamer discharge  | Near atmospheric    | Local gas ionisation, streamers | Surface discharge, transient     |
| Glow discharge               | 30-80 mbar          | Collisional plasma          | Stable plasma column; Core Jet Mode |
| Transitional plasma          | 1-30 mbar           | Mixed collisional‑ballistic | Increasing electron range        |
| Electron beam (ballistic)    | <10⁻⁵ mbar          | Ballistic charged particles | Conventional accelerator physics |
| Space‑charge‑limited beam    | High current, vacuum| Child-Langmuir flow         | Beam envelope expansion           |
| Arc discharge                | High current        | Thermal plasma              | Undesired; prevented by current limiting |

Experimental operation shall identify the active regime using plasma diagnostics (discharge voltage‑current characteristic, optical emission, pressure) rather than nominal pressure alone.

---

## 4.3 Gas Breakdown and Paschen Behaviour

Gas breakdown follows Paschen’s Law,

\[
V_b = \frac{B\,p\,d}{\ln(A\,p\,d) - \ln\left[\ln\left(1 + \frac{1}{\gamma}\right)\right]}
\]

where  
- *p* = gas pressure  
- *d* = electrode spacing  
- *A*, *B* = constants depending on gas  
- *γ* = secondary electron emission coefficient.

For air, the Paschen minimum occurs near *pd* ≈ 0.76 Torr·cm with a minimum breakdown voltage *V_b,min* ≈ 327 V.

**Critical gap in the CPB:** The highest electric field exists between the toroidal emitter and the inner wall of the drift tube. With a tube inner diameter of 4.00 mm and the emitter outer diameter of 2.50 mm, the radial clearance is **0.75 mm** (§3.2). This gap, combined with the operating pressure, determines the breakdown threshold.

**Example - Core Plasma Jet Mode at 50 mbar:**  
- *p* = 50 mbar = 37.5 Torr  
- *d* = 0.75 mm = 0.075 cm  
- *p d* ≈ 2.8 Torr·cm  

This places the device on the right‑hand branch of the Paschen curve, where the breakdown voltage is several kilovolts. For air, *V_b* is estimated to be >3 kV. Therefore, operating at ±10 kV with active current limiting ensures that a controlled glow discharge is sustained without transitioning to an arc. In hydrogen or deuterium, the breakdown voltage is lower; initial operation will map the safe operating area.

**High‑Vacuum Beam Mode:** Once the drift tube is evacuated to <10⁻⁵ mbar, gas breakdown is no longer the limiting factor. Instead, vacuum breakdown mechanisms dominate: field emission from microscopic protrusions, ceramic flashover, and triple‑junction effects. These are managed by electrode conditioning, smooth surfaces (Ra ≤0.4 µm), and shielding of ceramic‑metal‑vacuum junctions.

---

## 4.4 Plasma Parameters (Core Plasma Jet Mode)

Representative parameters for a 50 mbar glow discharge in air (from literature [3,19] and preliminary estimates):

| Quantity             | Typical Value    | Status      |
|----------------------|------------------|-------------|
| Electron density, nₑ | 10¹⁵ - 10¹⁶ m⁻³  | Estimated   |
| Electron temperature, Tₑ | 1-3 eV       | Literature  |
| Ion temperature      | ≈ 300 K          | Estimated   |
| Ionisation fraction  | 10⁻⁶ - 10⁻⁴      | Literature  |
| Debye length, λ\_D   | 7-20 µm          | Calculated  |
| Plasma frequency, fₚ | 0.3-3 GHz        | Calculated  |

These values define a **weakly ionised, collisional glow plasma**. The Debye length is much smaller than the tube diameter, so the plasma is quasi‑neutral, and electrostatic beam optics are ineffective in this regime.

**Primary diagnostics:** Optical emission spectroscopy (OES) for species identification and electron temperature estimation; current‑voltage (I‑V) characteristics; and, where practical, Langmuir probe measurements.

---

## 4.5 Electron Emission Mechanisms

### Core Plasma Jet Mode
Electrons are supplied by **secondary emission** from the toroidal cathode due to ion bombardment. The discharge is self‑sustaining: ions accelerated across the cathode sheath release electrons, which in turn ionise more gas. The electron energy is determined by the cathode fall voltage (200-600 V in air) and by collisional processes in the negative glow, not by the full applied voltage.

### High‑Vacuum Beam Mode
With the gas density reduced by a factor >10⁴, ion‑induced secondary emission cannot sustain a discharge. The primary emission mechanism becomes **Fowler‑Nordheim (FN) field emission** [5,6,14]:

\[
J = \frac{A \beta^2 E^2}{\phi \, t^2(y)} \exp\!\left(-\frac{B \, v(y) \, \phi^{3/2}}{\beta E}\right)
\]

where  
- *J* = emission current density  
- *β* = field enhancement factor (dimensionless)  
- *E* = macroscopic electric field = *V/d*  
- *φ* = work function (≈2.6 eV for LaB₆)  
- *A*, *B* = FN constants (A = 1.54 × 10⁻⁶ A·eV/V², B = 6.83 × 10⁹ eV⁻³/² V/m)  
- *t(y)*, *v(y)* = elliptic integral corrections (approximated as unity in simplified analyses).

The field enhancement factor *β* depends on the microscopic geometry and surface condition; it will be extracted from experimental FN plots (ln(*I/V²*) vs. 1/*V*). Initial estimates place *β* in the range 50-100. The actual emission current may deviate from the ideal FN law due to adsorbates, surface migration, and thermal effects.

---

## 4.6 Space‑Charge Limited Flow (Child-Langmuir)

Once electrons enter the vacuum accelerating gap, their current density is ultimately bounded by the Child-Langmuir law for a planar diode:

\[
J_{CL} = \frac{4\epsilon_0}{9} \sqrt{\frac{2e}{m}} \, \frac{V^{3/2}}{d^2}
\]

For *V* = 100 kV and *d* = 0.75 mm (emitter‑to‑tube gap),  
*J_CL* ≈ 1.3 × 10⁵ A/m². Our design target (~10⁴ A/m² for 2 mA) is well below this limit; space‑charge does not restrict the total current. However, perveance effects can still cause beam envelope growth, which is addressed by the beam envelope equation (§4.7) and numerical simulations.

---

## 4.7 Beam Optics (HV Beam Mode)

In HV Beam Mode, the transition from the drift tube (at accelerating potential) to the grounded beam‑line forms an **electrostatic immersion lens**. A thin‑lens approximation gives an initial focal length estimate, but accurate design requires numerical trajectory simulations (e.g., SIMION).  

**Conservative design targets (initial operation):**

| Parameter             | Design Target       | Status     |
|----------------------|---------------------|------------|
| Beam spot diameter   | ≤500 µm (100 keV, 1 mA) | Predicted  |
| Normalised emittance (εₙ) | ≤50 mm·mrad      | Estimated  |
| Beam brightness (B)  | ≥5 × 10⁵ A/(m²·rad²) | Predicted  |

These values are deliberately conservative for a first‑generation prototype. Higher brightness (εₙ <20 mm·mrad, spot <200 µm) is a stretch goal that will be pursued after the basic beam transport has been validated. Chromatic and spherical aberrations will be quantified by ray‑tracing and compared with experiment.

**Optional magnetic correction:** A compact SmCo ring or air‑core solenoid can provide fine focusing and steering. Alignment tolerance <1 mrad.

---

## 4.8 Space‑Charge Neutralisation

When an electron beam passes through residual gas (even at HV pressures), some ionisation occurs, producing positive ions that can partially neutralise the beam’s space charge. This effect reduces the net perveance and can improve transport. The degree of neutralisation depends on pressure, beam current, ion mass, and time scale. In the CPB HV mode, the base pressure of 10⁻⁵ mbar may still support a low level of neutralisation; it will be characterised experimentally by observing beam profile evolution at different pressures and currents.

---

## 4.9 Plasma Chemistry (Core Plasma Jet Mode)

The core plasma jet contains a variety of reactive neutral and ionic species formed by electron‑impact dissociation and ion‑molecule reactions. Expected species include:

- **Air plasma:** O, O₂⁺, N₂⁺, NO, NO₂, O₃, OH, electrons, positive and negative ions.  
- **Hydrogen/deuterium plasma:** H (D), H₂⁺ (D₂⁺), H₃⁺ (D₃⁺), electrons.

These species influence electrical conductivity, optical emission, electrode corrosion, and aerosol chemistry. OES will be the primary tool for species identification; residual gas analysis will complement it in HV mode.

---

## 4.10 Dimensionless Parameters

Key dimensionless numbers aid in regime identification and scaling:

| Parameter            | Significance                                            |
|----------------------|--------------------------------------------------------|
| Reynolds Number (Re) | Gas‑flow regime (laminar vs. turbulent)                |
| Mach Number (Ma)     | Compressibility effects in the Bernoulli nozzle        |
| Knudsen Number (Kn)  | Continuum vs. molecular flow; Kn > 0.01 indicates transition to free‑molecular flow |
| Child‑Langmuir Ratio | Beam loading relative to the space‑charge limit        |
| Debye Number         | Ratio of Debye length to characteristic dimension; plasma shielding |
| Electric Bond Number | Electrostatic stress vs. surface tension for aerosol droplets |

These will be computed from measured pressures, velocities, and plasma parameters to validate scaling relationships.

---

## 4.11 Experimental Unknowns

The following quantities are critical for model validation and will be measured during the experimental programme:

| Quantity                                | Importance                        | Measurement Method            |
|-----------------------------------------|-----------------------------------|-------------------------------|
| Bernoulli pressure distribution         | Defines operating regime          | Pressure transducer array     |
| Plasma density (nₑ)                     | Determines conductivity & Debye length | OES, microwave interferometry |
| Electron energy distribution (EEDF)     | Confirms discharge model          | Retarding‑field analyser      |
| Droplet charge distribution             | Controls aerosol transport & Rayleigh stability | Faraday pail / electrometer |
| Beam divergence & emittance             | Validates beam optics             | Phosphor screen + pepper‑pot  |
| Space‑charge neutralisation fraction    | Influences beam envelope          | Beam profile vs. pressure     |
| Gas composition (Core & HV)             | Governs plasma chemistry & target poisoning | RGA / OES               |

A dedicated **aerosol‑only test phase** (§3.6) will characterise droplet charge, size, and evaporation before plasma integration.

---

## 4.12 Physics Validation Strategy

The CPB platform advances through progressive validation levels:

| Validation Level | Evidence                                                                 |
|------------------|--------------------------------------------------------------------------|
| Analytical       | Governing equations and first‑principles scaling laws                    |
| Numerical        | CFD (COMSOL), electrostatic (SIMION), beam envelope, and Monte Carlo simulations |
| Experimental     | Laboratory measurements with calibrated, traceable instrumentation        |
| Correlated       | Agreement between theory, simulation, and experiment within stated uncertainty |
| Verified         | Independent replication and consistent performance across multiple prototypes |

All values presented in this specification are **engineering design targets**. Final acceptance of any performance claim requires direct experimental verification with documented uncertainty budgets. The physics basis described here provides the framework for designing experiments, interpreting data, and progressively refining the models that underpin the CPB platform.

---

# 5. Modes of Operation

The Compact Plasma Beam (CPB) platform supports multiple operating modes spanning collisional plasma physics and conventional charged-particle beam transport. Each mode has distinct hardware configurations, operating parameters, diagnostics, and intended applications.

Unless otherwise noted, all performance values represent **engineering design targets** requiring experimental validation.

---

## 5.1 Plasma Electron Mode (Core Mode)

**Operating Pressure**

30-80 mbar

**Polarity**

* Toroidal emitter: Negative
* Drift tube: Ground reference
* Collector: Ground or positive bias

**Operating Voltage**

−200 V to −10 kV

### Physical Process

A stable glow discharge forms between the toroidal emitter and the drift tube.

Secondary electrons generated in the cathode fall region are transported through the partially evacuated drift tube as part of a weakly ionised plasma.

Because the electron mean free path is much shorter than the drift tube length, transport is dominated by repeated collisions with the background gas.

The output is therefore a **conductive plasma jet**, not a monoenergetic electron beam.

### Expected Operating Parameters

| Parameter             | Design Target     |
| --------------------- | ----------------- |
| Electron energy       | 0.2-2 keV         |
| Plasma current        | 10 µA-2 mA        |
| Pressure              | 30-80 mbar        |
| Plasma divergence     | <10°              |
| Continuous duty cycle | 100% with cooling |

### Primary Diagnostics

* Voltage/current monitoring
* Optical emission spectroscopy
* High-speed imaging
* Retarding-field analyser (where practical)
* Pressure monitoring
* Thermal monitoring

### Representative Applications

* Low-energy X-ray generation (<5 keV)
* Plasma antennas
* Surface activation
* Plasma cleaning
* Plasma-assisted chemistry
* Aerosol charging

---

## 5.2 Positive-Ion Plasma Mode (Core Mode)

**Operating Pressure**

30-80 mbar

**Polarity**

* Toroidal emitter: Positive
* Collector: Negative

### Physical Process

Positive ions generated within the glow discharge are accelerated toward the collector through the plasma column.

Transport remains strongly collisional.

The system behaves as an ion-assisted plasma reactor rather than an ion accelerator.

### Typical Ion Species

* N₂⁺
* O₂⁺
* Ar⁺
* H⁺
* H₃⁺
* D⁺
* He⁺

(depending on operating gas)

### Applications

* Plasma etching
* Surface activation
* Ion-assisted deposition
* Sputtering
* Thin-film processing

### Diagnostics

* Optical spectroscopy
* Collector current
* Mass spectrometry (future)
* Surface profilometry

---

## 5.3 Plasma RF Antenna Mode (Core Mode)

### Configuration

The plasma column generated during Plasma Electron Mode is RF-modulated through the control grid.

The conductive plasma acts as a dynamically reconfigurable antenna.

### Governing Physics

Radiation characteristics depend on

* plasma conductivity
* plasma density
* column geometry
* RF modulation frequency
* aerosol conductivity

The upper operating frequency is limited by the plasma frequency and electron collision rate.

### Expected Operating Range

Design objective

VLF through UHF

Microwave operation requires resonant cavity structures and remains experimental.

### Diagnostics

* Vector network analyser
* Near-field probe
* Far-field antenna measurements
* Optical plasma diagnostics

### Applications

* Reconfigurable antennas
* Low-observable communications
* Plasma RF research

---

## 5.4 Electron Beam Mode (HV Mode)

**Operating Pressure**

<10⁻⁵ mbar

**Polarity**

Toroidal emitter negative

**Operating Voltage**

5-100 kV

### Physical Process

Electrons are emitted by Fowler-Nordheim field emission and accelerated through the evacuated drift tube.

Ballistic transport replaces collisional plasma transport.

Beam focusing is provided by electrostatic optics with optional magnetic correction.

### Design Targets

| Parameter       | Design Target |
| --------------- | ------------- |
| Electron energy | 5-100 keV     |
| Beam current    | 10 µA-2 mA    |
| Energy spread   | <5% FWHM      |
| Spot diameter   | ≤200 µm       |
| Beam divergence | <5°           |

### Diagnostics

* Faraday cup
* Phosphor screen
* Pepper-pot emittance measurement
* Retarding-field analyser
* Beam current monitor

### Representative Applications

* Bremsstrahlung X-ray generation
* Electron irradiation
* Materials research
* Electron optics experiments
* Beam diagnostics development

---

## 5.5 Positive-Ion Beam Mode (HV Mode)

**Operating Pressure**

<10⁻⁵ mbar

### Ion Sources

* Hollow cathode
* Electron Cyclotron Resonance (ECR)
* Future RF plasma source

### Supported Species

* H⁺
* D⁺
* He⁺
* Ar⁺

### Beam Energy

10-300 keV

### Physical Process

Positive ions are generated in a dedicated ion source, extracted electrostatically, accelerated, and transported ballistically through the high-vacuum beamline.

### Diagnostics

* Faraday cup
* Beam-profile monitor
* Energy analyser
* Residual gas analyser
* Beam-current monitor

### Applications

* Hydrogen implantation
* Surface modification
* Ion-beam research
* Accelerator development
* Fusion target irradiation

---

## 5.6 Neutron Generator Mode (HV Mode)

This operating mode is based on established sealed-tube neutron generator principles.

### Configuration

Accelerated D⁺ ions strike a titanium deuteride target.

### Primary Reaction

[
\mathrm{D + D \rightarrow ^3He + n + 3.27\ MeV}
]

### Operating Parameters

| Parameter      | Design Target                            |
| -------------- | ---------------------------------------- |
| Ion energy     | 50-100 keV                               |
| Beam current   | up to 0.1 mA initially                   |
| Target         | Titanium deuteride (TiD₂)                |
| Expected yield | >10⁷ n/s (literature estimate at 0.1 mA) |
| Neutron energy | 2.45 MeV                                 |

Yield depends strongly on

* target loading
* beam purity
* beam energy
* target temperature
* surface contamination

Actual performance shall be determined experimentally.

### Diagnostics

* Neutron detector
* Activation foils
* Beam current
* Target temperature
* Radiation survey meter

### Shielding

Final shielding design shall be based on Monte Carlo transport simulations (e.g., MCNP or GEANT4) and validated by radiation measurements.

---

## 5.7 Advanced Experimental Configurations

The following configurations are considered exploratory research modes rather than established operating modes.

No performance claims are made.

Operation requires rigorous experimental controls, calibrated instrumentation, uncertainty analysis, and independent verification.

### Electron-Screening Experiments

Investigate the influence of high electron density and plasma environments on low-energy nuclear reaction cross sections.

Potential measurements include

* neutron emission
* gamma spectroscopy
* helium isotope analysis
* charged-particle spectroscopy

### Deuterated Aerosol Experiments

Investigate interactions between plasma, conductive aerosols, and deuterated materials.

Primary diagnostics include

* high-resolution mass spectrometry
* calibrated calorimetry
* gas analysis
* radiation monitoring

### Status

Exploratory research only.

These experiments lie outside established engineering objectives and shall not be considered validated operational capabilities.

---

## 5.8 Plasma Chemical Processing Mode (Core Mode)

### Configuration

A conductive aerosol carrying dissolved reactants or catalysts passes through the plasma discharge.

Electron-impact ionisation and radical formation drive non-equilibrium plasma chemistry.

### Representative Reactive Species

* O
* OH
* O₃
* H
* N
* NO
* electrons
* positive ions

### Potential Applications

* Plasma-assisted catalysis
* Plasma water treatment
* Surface functionalisation
* Sterilisation
* Waste remediation
* CO₂ activation
* Hydrogen production research

### Diagnostics

* Optical emission spectroscopy
* Gas chromatography
* Mass spectrometry
* FTIR spectroscopy
* pH monitoring
* Conductivity measurement

---

## 5.9 Mode Transition Requirements

Transition between operating modes shall occur only after satisfying predefined system conditions.

| Transition                  | Required Conditions                                                                                   |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| Atmospheric → Core Plasma   | Stable Bernoulli pressure (30-80 mbar), verified gas flow, HV interlocks enabled                      |
| Core Plasma → HV Mode       | Plasma extinguished, gate valve closed, vacuum system pumped to <10⁻⁵ mbar, vacuum integrity verified |
| HV Mode → Ion Beam          | Stable base pressure, ion source conditioned, beam diagnostics operational                            |
| HV Mode → Neutron Generator | Radiation shielding installed, neutron detectors calibrated, safety interlocks verified               |

No transition shall occur automatically. Each mode change requires confirmation that pressure, electrical, thermal, and safety limits remain within their specified operating envelopes.

---

## 5.10 Operational Validation Levels

Each operating mode shall progress through the following maturity levels before being considered validated.

| Validation Level | Requirement                                                               |
| ---------------- | ------------------------------------------------------------------------- |
| Analytical       | Supported by first-principles calculations and literature                 |
| Simulated        | Corroborated by numerical modelling (CFD, SIMION, COMSOL, GEANT4, etc.)   |
| Prototype        | Demonstrated under controlled laboratory conditions                       |
| Validated        | Reproducible using calibrated instrumentation with documented uncertainty |
| Verified         | Independently replicated using equivalent hardware and procedures         |

This staged validation framework ensures that operational claims remain proportional to the available theoretical, numerical, and experimental evidence while providing a clear roadmap for progressively maturing the CPB platform.

---

# 6. Beam Diagnostics & Instrumentation

Beam and plasma diagnostics are essential for validating operating regimes, quantifying performance against design targets, and ensuring safe operation. The diagnostic suite is modular and shared wherever possible between Core Plasma Jet Mode and High‑Vacuum (HV) Beam Mode. All instruments shall be calibrated traceable to national standards (e.g., NIST or equivalent) with documented uncertainty budgets. Diagnostic ports on the drift tube, collector, and target chamber allow insertion, retraction, and exchange without breaking vacuum or major disassembly.

---

## 6.1 Faraday Cup (Primary Current Monitor)

- **Design**: Retractable, electrically isolated tungsten cup (5 mm diameter, 10 mm depth), biased at +50 V to suppress secondary electrons. A magnetic electron‑suppression ring (SmCo or NdFeB, ~0.1 T) provides additional suppression. An interchangeable entrance aperture (2-4 mm) allows matching to the beam/plasma diameter.
- **Measurement Range**: 10 nA - 5 mA DC; pulsed mode with suitable integration.
- **Uncertainty**: ±1.5 % (k = 2) after calibration against a Keithley 6517B electrometer or equivalent. Cross‑calibration with a Rogowski coil or current transformer for pulsed operation.
- **Applications**:
  - *Core Plasma Jet Mode*: Total plasma current, jet uniformity, and current-voltage (I‑V) characteristics.
  - *HV Beam Mode*: Beam current, transmission efficiency, and stability.
- **Integration**: Linear actuator for in‑situ insertion; water‑cooled option for high‑power HV operation.
- **Maintenance**: Regular inspection for sputter‑deposited material or mist residue; cleaned with isopropyl alcohol and de‑ionised water.

---

## 6.2 Beam Profile and Emittance Diagnostics

### Profile Imaging
- **Phosphor Screen**: P43 (Gd₂O₂S:Tb) on a quartz substrate, 50 mm active diameter, imaged by a 1920 × 1080 (or higher) CMOS camera through a viewport with optical band‑pass filtering to reject plasma glow. Spatial resolution ≈ 10 µm/pixel.
- **Alternative**: Knife‑edge scan or thin‑wire scanner (tungsten, 50 µm wire) for higher dynamic range or when phosphor lifetime is a concern.
- **Analysis**: Real‑time centroid, FWHM, and RMS beam width; data archived for comparison with simulation.

### Emittance Measurement
- **Pepper‑Pot Method**: Molybdenum or tantalum mask with 50-100 µm holes on a 500 µm pitch; beamlets imaged on a phosphor screen downstream. The hole size (50-100 µm) is comparable to the expected beam size (≤500 µm) and may cause partial transmission; this method is most reliable when the beam is significantly larger than the hole, so it will be used at lower beam energies where the spot is larger, or with defocused beams.  
- **Alternative / Backup**: Slit‑scan technique (moving a narrow slit across the beam while measuring transmitted current) or quadrupole‑scan method (varying a magnetic lens strength and measuring beam size) to extract emittance without a pepper‑pot.
- **Normalised emittance (εₙ)** will be computed from beamlet divergence and Twiss parameters using standard software (e.g., TraceWin, Python scripts). Initial target: εₙ ≤ 50 mm·mrad; future stretch goal ≤ 20 mm·mrad.
- **Brightness** (B = 2I/π²εₙ²) derived from measured current and emittance. Initial target: B ≥ 5 × 10⁵ A/(m²·rad²).
- **Uncertainty**: Spatial ~10 µm; emittance ±15-25 % initially, improving with accumulated statistics and calibration.
- **Applications**:
  - *Core*: Plasma jet divergence (<10° half‑angle) and uniformity.
  - *HV*: Beam spot size (≤500 µm design target), divergence (<5°), and emittance.

---

## 6.3 Energy Analyser

- **Type**: Retarding‑field analyser (RFA) consisting of two or three high‑transmission tungsten mesh grids (80 % optical, 50-100 lines/inch) and a collector plate.
- **Voltage Range**: 0-12 kV (Core), 0-120 kV (HV) using a precision high‑voltage supply and calibrated voltage divider.
- **Resolution**: Target < 1 % FWHM with proper grid spacing and shielding; practical resolution < 5 % in early prototypes.
- **Calibration**:
  - *Low energy*: ⁶³Ni beta source (endpoint ~67 keV, useful lines at ~18 keV).
  - *High energy*: Known electron‑gun energies or characteristic X‑ray fluorescence lines (e.g., Cu Kα at 8.0 keV, Mo Kα at 17.5 keV, Ag Kα at 22.1 keV) for indirect cross‑check.
- **Applications**:
  - *Core*: Electron energy distribution in the afterglow plasma (0.2-2 keV).
  - *HV*: Beam energy, energy spread (FWHM), and HV‑ripple verification.
- **Integration**: Retractable assembly mounted downstream of the modulation grid or in the target diagnostics chamber.

---

## 6.4 Neutron and Radiation Diagnostics (HV Beam Mode)

- **Neutron Detector**: Stilbene scintillator (or EJ‑309 liquid scintillator) coupled to a silicon photomultiplier (SiPM) with pulse‑shape discrimination (PSD) for gamma/neutron separation. Energy range ~1-15 MeV.  
  *Calibration*: ²⁵²Cf spontaneous fission source; efficiency uncertainty ±8 % (k = 2).  
  *Background*: Periodic beam‑off subtraction; detector surrounded by borated polyethylene to reduce room‑return background.
- **Activation Foils**: Indium, gold, or copper foils for time‑integrated, threshold‑based neutron yield validation (cross‑check with active detector).
- **X‑ray Monitor**:  
  - *Core*: Si‑PIN diode or CdTe spectrometer for soft X‑rays (1-10 keV).  
  - *HV*: Thin‑window ionisation chamber (e.g., Ludlum 9‑3) for bremsstrahlung dose rate, plus a survey meter for area monitoring.
- **Area Radiation Monitors**: Real‑time neutron rem‑counter and gamma survey meter interlocked to the safety system to trip the beam if dose rate exceeds 2 µSv/h (or lower per local regulations).

---

## 6.5 Plasma Diagnostics (Core Plasma Jet Mode)

- **Optical Emission Spectroscopy (OES)**: 200-1100 nm fibre‑optic spectrometer (e.g., Ocean Optics or Avantes) for species identification (N₂, O, H, OH, etc.), electron temperature estimation via Boltzmann plot or line‑ratio methods, and qualitative plasma stability monitoring.
- **Langmuir Probe**: Single or double cylindrical probe. Usable only in the transitional pressure regime (<10 mbar) where probe theory is valid; deployment is limited due to the risk of contamination from the conductive mist. Where feasible, it provides direct measurement of electron density and temperature.
- **High‑Speed Imaging**: Intensified CCD or fast CMOS camera (frame rates >10 kfps) for visualising plasma‑jet dynamics, constriction, and instabilities.
- **Microwave Diagnostics (Future)**: Microwave interferometry or cavity perturbation for non‑invasive electron density measurement (10¹⁵-10¹⁶ m⁻³ range), essential when Langmuir probes cannot be used.

---

## 6.6 Supporting Instrumentation

- **Pressure**: Kulite XCQ‑093 transducers (Core); Pirani gauge (10⁻³-1000 mbar) + cold‑cathode gauge (10⁻⁹-10⁻² mbar) for HV transition; full‑range gauge in target chamber.
- **Thermal**: Embedded thermocouples/RTDs at key locations (emitter mount, drift tube flange, target carrier); forward‑looking IR camera for target and emitter surface monitoring.
- **Electrical**: High‑voltage probes (e.g., Tektronix P6015A, 1000:1), DC/pulsed current monitors, and fast oscilloscopes for ripple, pulse shape, and arc detection.
- **Data Acquisition**: FPGA‑based or National Instruments system with real‑time logging of all sensors, Python scripting for experiment control, and SQL database for long‑term archiving. All data time‑stamped and correlated with operating parameters.
- **Synchronisation**: 10 MHz reference clock distributed to all digitisers and pulse generators to enable multi‑unit coherence and precise timing of diagnostic triggers.

---

## 6.7 Diagnostic Strategy and Validation

- **Core Mode Focus**: Plasma parameters (OES, pressure mapping, total current), jet divergence, and stability are the primary deliverables. The initial diagnostic set will be used to verify the I‑V characteristics and compare them with glow‑discharge models.
- **HV Mode Focus**: After successful vacuum commissioning, emphasis shifts to beam quality metrics: spatial profile, emittance, energy spread, and radiation output. These measurements directly validate the physics assumptions and the beam optics design.
- **Uncertainty Management**: All measurements will be reported with Type A (statistical) and Type B (systematic) uncertainties, combined in quadrature and expressed as expanded uncertainty with coverage factor k = 2.
- **Data Analysis**: Automated analysis pipelines for I‑V curves, beam envelopes, and emittance will be developed in Python. Results will be compared against SIMION simulations and, where applicable, against COMSOL plasma models.
- **Maintenance**: Optical surfaces (meshes, phosphor screens, viewports) will be inspected regularly for aerosol deposition or sputtering. Spare diagnostic inserts will be kept on hand to minimise downtime.
- **Calibration**: All instruments will be calibrated before each experimental phase and periodically thereafter (at least annually). Calibration records are maintained in the CPB‑LOG.

**Status**: Diagnostic suite is at design maturity (TRL 4-6 for most components). Integration and calibration will occur during Phase 1-3 Core testing. Full HV beam characterisation (emittance, brightness) will follow successful vacuum commissioning in Phase 4.

---

# 7. Engineering Margins and FMEA

Engineering margins provide robustness against uncertainties in materials, manufacturing, operating conditions, and the partially validated physics of the Core Plasma Jet and High‑Vacuum Beam regimes. The Failure Modes and Effects Analysis (FMEA) identifies credible risks and defines mitigation strategies, with particular attention to the high‑risk transition to high‑voltage and neutron‑producing modes.

---

## 7.1 Margin Analysis (Key Subsystems)

Margins are calculated as (Design Value - Operating Value) / Operating Value for quantitative parameters, or expressed as a multiplicative factor where appropriate. All values incorporate safety factors derived from applicable standards (e.g., IEC 60071 for HV insulation) and conservative engineering practice. Because many parameters are unvalidated, margins are generous; they will be refined as experimental data become available.

| Subsystem                  | Design Value          | Operating Value          | Margin      | Notes / Basis |
|----------------------------|-----------------------|--------------------------|-------------|---------------|
| Core HV supply             | 12 kV                 | 10 kV                    | 20 %        | Paschen‑limited; current‑regulated |
| HV‑mode supply             | 120 kV                | 100 kV                   | 20 %        | Vacuum insulation + crowbar protection; stored energy <3 J |
| Target cooling capacity (HV) | 200 W               | ≤100 W (100 keV, 1 mA)   | 100 %       | Water‑glycol loop; oversizing accommodates transient heat loads |
| Core thermal load (mist + air convection) | ≤50 W   | ≤30 W (glow discharge + collector) | ~67 % | Passive air cooling, validated in endurance tests |
| Grid amplifier Vpp         | 150 V                 | 100 V                    | 50 %        | THS3491 driving 5-20 pF; sufficient for full modulation depth |
| Bernoulli drive pressure   | 6 bar (gauge)         | 3-5 bar                  | 20-100 %    | Compressor capability; actual operating point depends on mist loading |
| Emitter current density    | 2× nominal design current | 1× (design target)     | Factor 2    | Field emission / erosion lifetime; tested in accelerated life tests |
| Stored energy (HV)         | <3 J                  | <1 J at 100 kV           | >200 %      | Fast crowbar reduces risk of arc damage |
| Neutron shielding (D‑D)    | 40 cm borated polyethylene | 30 cm (baseline)      | 33 %        | Conservative; final thickness to be confirmed by MCNP/GEANT4 |

**Notes**:
- Margins are preliminary and will be re‑evaluated after Phases 1-3 (Core) and 4-5 (HV) testing. Low‑confidence parameters (e.g., mist‑plasma interaction, long‑term emitter lifetime) carry inherently higher safety factors.
- Thermal margins assume worst‑case 100 % duty cycle and include fouling/contamination effects.

---

## 7.2 Failure Modes and Effects Analysis (FMEA)

The FMEA focuses on safety‑critical and performance‑limiting failures. Severity, Occurrence, and Detection are rated qualitatively (Low/Medium/High) based on current design maturity; numerical Risk Priority Number (RPN) scoring will be adopted as failure rate data become available. The table will be updated after each experimental phase.

| Failure Mode                          | Cause                                      | Effect                                      | Detection Method                          | Mitigation / Prevention                          | Probability | Severity | RPN   |
|---------------------------------------|--------------------------------------------|---------------------------------------------|-------------------------------------------|--------------------------------------------------|-------------|----------|-------|
| HV arc / flashover                    | Moisture, particulates, triple‑junction stress | System shutdown, component damage, EMI     | Over‑current spike (>5 mA), voltage drop | Fast crowbar (<100 ns), dry N₂ purge, grading rings, clean assembly | Medium      | High     | High  |
| Emitter erosion / failure             | Excessive current, ion sputtering, poisoning | Current drop, unstable emission            | Beam current drop >20 %, increased ripple | Liquid‑metal reservoir (if used), scheduled replacement, current limiting, conditioning protocol | Medium      | Medium   | Med   |
| Mist nozzle clogging                  | Salt/particulate buildup, evaporation      | Pressure rise, unstable flow, plasma instability | Nebuliser pressure sensor, flow drop     | Auto‑purge cycle, inline filters, backup nozzle, periodic maintenance | Medium      | Medium   | Med   |
| Ceramic insulator cracking / leakage  | Thermal shock, mechanical stress           | HV leakage current, arc risk               | Leakage current monitor (>1 µA at 50 kV) | Controlled thermal ramp, flexible mounts, replaceable insulators | Low         | High     | Med   |
| Plasma instability / extinction       | Pressure drift, gas composition change, mist loading | Unstable jet, poor repeatability           | Optical emission flicker, pressure sensor, current fluctuation | PID mass flow control, closed‑loop voltage regulation, gas analyser feedback | Medium      | Medium   | Med   |
| Target overheating / melting (HV)     | Cooling failure, misalignment, excessive current | Target damage, vacuum breach, radiation spike | IR camera / thermocouples (>400 °C)      | Beam trip interlock, redundant flow sensors, conservative cooling margin | Low         | High     | Med   |
| Radiation overexposure                | Shielding breach, misalignment, mode error | Personnel dose exceedance                  | Area neutron & gamma monitors            | Interlock trips, administrative controls, Monte Carlo validated shielding, training | Low         | High     | Med   |
| Aerosol charge‑buildup / Rayleigh instability | Droplet evaporation, high field      | Corona, irregular discharge, plasma flicker | Optical inspection, current noise        | Pre‑plasma aerosol characterisation, in‑line conductivity control | Medium      | Medium   | Med   |
| Mist‑chemical corrosion / contamination | Unexpected plasma‑aerosol reactions, saline | Electrode/tube degradation, conductivity loss | Visual inspection, pressure/conductivity trends | Material compatibility testing, flush cycles, pH‑neutral fluids, corrosion inhibitors | Medium      | Medium   | Med   |
| Vacuum leak (HV mode)                 | Seal failure, thermal cycling              | Loss of base pressure, arcing              | Pressure rise, RGA scan                    | Helium leak testing, metal seals (ConFlat), bake‑out capability | Low         | High     | Med   |
| Control system / interlock failure    | Software bug, sensor drift, power loss     | Unsafe operation                           | Watchdog timers, redundant hard‑wired interlocks | Dual‑redundant E‑stops, fail‑safe design, regular proof‑testing | Low         | High     | Med   |
| Compressor / gas supply failure       | Mechanical wear, filter clogging           | Loss of Bernoulli pressure, mode collapse  | Flow/pressure alarms                       | Redundant compressor option, auto‑shutdown, buffer tank | Medium      | Medium   | Med   |

**FMEA Notes**:
- Probability ratings assume proper implementation of mitigations and adherence to operating procedures.
- High‑severity items (arc, target melt, radiation, vacuum leak, interlock failure) will receive additional design review and early prototype testing.
- The FMEA is a living document; after each experimental phase, actual failure frequencies and detectability will be recorded, and the table will be updated with quantitative RPNs.

---

## 7.3 Design for Reliability and Maintainability

- **Modularity**: Key wear items (emitter, mist nozzle, target, insulators) are designed for rapid replacement (<1 h downtime). Spare assemblies will be kept on hand.
- **Condition‑Based Maintenance**: Real‑time monitoring of current drop, pressure trends, leakage current, and thermal signatures triggers preventive actions before hard failures occur.
- **Redundancy**: Dual hard‑wired interlocks for safety‑critical functions; backup diagnostic channels where feasible.
- **Lifetime Targets**: >500 h MTBF (excluding consumables) for the Core Plasma Jet module; >200 h MTBF for early HV Beam campaigns (to be extended with design maturity).
- **Testing**: Accelerated life testing (elevated temperature/current) and environmental stress screening will be performed during prototype qualification. Critical components (emitters, HV feedthroughs) will be qualified beyond nominal ratings.

**Status**: Margin analysis and FMEA are at preliminary maturity. Quantitative RPN scoring and failure rate data will be developed during Phases 1-4. All high‑severity failures have defined detection and mitigation paths, and the FMEA will be formally updated after each major test campaign.

---

# 8. Safety Systems

Safety is paramount given the combination of high voltage, ionising radiation (X‑rays, potentially neutrons), flammable gases, reactive plasmas, and conductive aerosols. The safety architecture follows a defence‑in‑depth philosophy: **prevention**, **detection**, **mitigation**, and **administrative controls**. All safety‑critical functions incorporate redundancy and fail‑safe design. Compliance with relevant standards (IEC 60071, IEC 61010, IAEA neutron generator guidelines, and national radiation regulations) is mandatory. A detailed safety case will be documented in CPB‑SAF‑001 before any HV or neutron operation.

---

## 8.1 High‑Voltage Safety

- **Clearances and Insulation**: Minimum air clearances per IEC 60071‑1 and IEC 60071‑2. For the 120 kV design, a clearance of >300 mm in dry air is maintained between live parts and grounded enclosure. Where compact sections require reduced spacing, oil or SF₆ insulation may be employed. All HV components (multiplier, capacitors, feedthroughs) are housed in a grounded, interlocked metal cabinet.
- **Stored Energy Management**: Total stored energy is limited to <3 J at 120 kV by design (HV capacitor bank <100 pF plus parasitic cabling). Dual‑redundant discharge systems:
  - Fast triggered spark‑gap crowbar (<100 ns response) directly shunts the HV output.
  - A high‑voltage relay mechanically shorts the capacitor bank to ground within 100 ms of any interlock trip.
- **Interlocks**: Hard‑wired safety circuit (ISO 13849 Category 4 / PL e) monitors:
  - Enclosure door switches (HV disabled if opened).
  - Visible‑break grounding stick insertion.
  - Coolant flow sensors (flow < minimum trips HV).
  - Emergency stop buttons.
  - All interlocks must be in a “safe” state before HV can be enabled.
- **Monitoring**: Real‑time leakage current is measured at the HV return; a trip is generated if leakage exceeds 1 µA at 50 kV (or proportionally lower at higher voltage). Arc detection via over‑current spike (>5 mA) and optical flash sensors provides additional protection.
- **Personnel Protection**: The HV enclosure is marked with warning signs and lights. Access is controlled by a key system. Personnel working on de‑energised equipment follow lockout/tagout procedures and use HV‑rated insulating gloves and tools.

---

## 8.2 Radiation Safety

### X‑ray Protection (Core and HV Modes)
- **Core Plasma Jet Mode** produces soft X‑rays (<5 keV). The collector region is shielded by the metal casing (≥2 mm steel equivalent), which is adequate to reduce dose rates below 1 µSv/h at 30 cm.
- **HV Beam Mode** generates bremsstrahlung up to 100 keV. The target chamber is surrounded by at least 2 mm of lead (providing >10⁶ attenuation at 100 keV). Local lead blankets are used around viewports and flanges.
- A thin‑window ionisation chamber (e.g., Ludlum 9‑3) or energy‑compensated survey meter at the operator’s position will trip the beam if dose rate exceeds 0.5 µSv/h (Core) or 1 µSv/h (HV). Audible and visual alarms are integrated.

### Neutron Protection (HV Beam Mode - D‑D operation)
- The target area is enclosed by at least 30 cm of borated polyethylene (5 % boron by weight) to thermalise and capture 2.45 MeV neutrons, plus 2 mm of lead to absorb capture gamma rays.
- Monte Carlo simulations (MCNP or GEANT4) will be performed to validate the shielding design before first neutron production. The final shielding thickness may be adjusted based on these simulations.
- A neutron rem‑counter (e.g., Ludlum 12‑4) provides real‑time dose rate monitoring. If the dose rate exceeds 2 µSv/h (or a lower limit set by local regulations), the beam is automatically tripped.
- Activation foils (indium, copper) are used for time‑integrated yield verification and to cross‑check active detector calibration.
- Post‑operation, a mandatory cooldown period is observed before accessing the target area. Swipe tests for contamination are performed regularly.

### Personal and Environmental Monitoring
- All personnel working in the controlled area during HV/neutron operation must wear whole‑body and extremity dosimeters (TLD/OSL). Dosimeters are processed monthly.
- Fixed area monitors (neutron and gamma) with local alarm and remote readout are installed. A controlled access zone is established around the device; entry during operation requires authorisation.

### Regulatory Compliance
- Operation of a neutron generator producing >10⁶ n/s (or any sealed source) may require a license from the national regulatory body (e.g., NRC, CNSC, ONR). The safety case, including shielding calculations and procedures, will be submitted for approval before any neutron‑producing experiments. A qualified Radiation Safety Officer (RSO) will oversee all such work.

---

## 8.3 Chemical, Gas, and Aerosol Safety

### Flammable and Hazardous Gases
- **Hydrogen / Deuterium**: Gas supply lines are constructed of stainless steel tubing with welded or high‑integrity compression fittings (no polymeric tubing). Each line includes a flame arrestor and an excess‑flow valve.
- Gas detectors for H₂/D₂ are installed in the experimental enclosure and the room, set to alarm at 10 % of the Lower Explosive Limit (LEL) and automatically shut off gas supply at 25 % LEL.
- Forced ventilation provides a minimum of 12 air changes per hour. The system is interlocked such that gas flow is inhibited if ventilation is not confirmed.
- Buffer tanks and closed‑loop recirculation are used to minimise total gas inventory; the maximum stored volume does not exceed the design limit of the ventilation system to dilute any accidental release below the LEL.

### Mercury (if used)
- Mercury is only used in sealed emitters with cold‑trap recovery. A mercury vapour detector monitors the enclosure; an alarm is triggered at the occupational exposure limit (e.g., 25 µg/m³ TWA). Spill kits and a mercury clean‑up plan are in place.

### Conductive Aerosol and Plasma By‑products
- The mist (typically saline) is non‑toxic, but plasma operation can produce ozone (O₃), nitrogen oxides (NOₓ), and acidic vapours. Local exhaust ventilation is positioned at the collector exit to capture these by‑products before they enter the room.
- pH‑neutral mist formulations are preferred to minimise corrosion risk. The mist chamber and collector are regularly flushed with de‑ionised water to remove residues.
- All wetted materials are selected for compatibility with the chosen working fluid; a compatibility matrix is maintained in Appendix C.

### Fire Suppression
- Only CO₂ or clean‑agent extinguishers are permitted in the experimental area. Water‑based extinguishers are prohibited near high‑voltage equipment. Automatic fire suppression is not installed to avoid accidental discharge; instead, the interlock system shuts down all potential ignition sources (HV, plasma) and isolates gas supplies upon detection of a fire by smoke or heat detectors.

---

## 8.4 Emergency Shutdown and Alarms

- **E‑Stop System**: Red mushroom‑head emergency stop buttons are located at the control rack, near the device, and at each exit from the experimental area. Activation of any E‑stop initiates a hard‑wired safety shutdown (ISO 13849 Cat. 4) that:
  - Immediately disables all HV supplies.
  - Fires the crowbar discharge circuit.
  - Closes all gas valves and de‑energises compressors.
  - Cuts power to the turbomolecular pump and closes the gate valve (HV mode) to preserve vacuum integrity.
  - Sounds a continuous audible alarm and flashes a strobe light.
- **Layered Alarms**:
  - **Warning (Yellow)** - Minor deviations such as pressure drift, low mist level, or approaching maintenance intervals.
  - **Critical (Red)** - Interlock violation, high radiation, or detection of flammable gas.
  - **Emergency (Audible + Strobe)** - E‑stop activation or fail‑safe trip.
- **Power Failure**: Upon loss of mains power, the system fails to a safe state (all HV off, gas valves closed). Uninterruptible power supplies (UPS) maintain the control system, safety interlocks, and critical monitors for at least 30 minutes to permit orderly shutdown and data preservation.
- **Remote Operation**: For HV and neutron modes, the operator is located outside the controlled area, with full video monitoring and remote E‑stop capability.

---

## 8.5 Administrative and Procedural Controls

- **Training**: All operators must complete a structured safety training programme covering high‑voltage, radiation, chemical, and emergency procedures. Only certified personnel may operate the neutron generator mode. Refresher training is conducted annually.
- **Standard Operating Procedures (SOPs)**: Detailed, step‑by‑step SOPs are provided for every operating mode and maintenance activity. Checklist‑based mode transitions ensure that all prerequisites (pressure, interlocks, shielding, personnel) are verified before proceeding.
- **Lockout/Tagout (LOTO)**: A formal LOTO programme is in place for maintenance of all hazardous energy sources (HV, pressurised gas, rotating machinery).
- **Audits and Inspections**:
  - Monthly proof‑testing of all safety interlocks and E‑stop circuits.
  - Quarterly radiation surveys and leak checks.
  - Annual independent safety audit of the facility and documentation.
- **Documentation**: A safety case file (CPB‑SAF‑001) will compile the FMEA, shielding calculations, interlock diagrams, training records, SOPs, and regulatory submissions. This file is a controlled document, updated as the system evolves.

---

**Status**: Safety systems are designed to meet or exceed applicable standards for a research prototype. Detailed implementation drawings, interlock logic diagrams, and radiation shielding simulations will be developed during Phases 2-3. Full safety system verification and regulatory approval will be completed prior to any HV or neutron operation. Core‑mode operation can begin once the E‑stop, ventilation, and basic electrical interlocks are commissioned.

---

# 9. Experimental Roadmap and Validation

The CPB platform follows a gated, risk‑reduced development path. Each phase builds on the previous, with explicit quantitative success criteria and formal go/no‑go decisions. Technology Readiness Levels (TRL, per NASA/DoD scale) track subsystem maturity. All phases require safety reviews, documented procedures, and data‑driven decisions. Core Plasma Jet validation receives priority before committing significant resources to the High‑Vacuum Beam upgrade.

---

## 9.1 Technology Readiness Levels (TRL)

| Subsystem                        | TRL | Comment |
|----------------------------------|-----|---------|
| Ultrasonic nebuliser / mist generation | 9   | Commercial off‑the‑shelf components |
| HV power supply (120 kV)         | 9   | Industrial / commercial units available |
| Bernoulli vacuum stage           | 4   | Bench‑tested flow and pressure mapping; plasma integration pending |
| Aerosol characterisation (stand‑alone) | 3-4 | Initial droplet charge/size measurements completed; need in‑situ validation |
| Core plasma generation & stability | 3-4 | Preliminary glow discharge tests completed; stability at design pressure not yet demonstrated |
| Core plasma electron extraction  | 3   | Basic Faraday cup measurements in progress |
| Modulation grid & driver         | 5   | Bench‑tested electronics; system integration pending |
| High‑vacuum system (turbo + gauges) | 6   | Commercial components; integrated pumping tests needed |
| HV ballistic electron beam       | 2   | Design and simulations only; no beam demonstrated |
| Beam diagnostics suite           | 4   | Individual instruments calibrated; full integration pending |
| Neutron generation (D‑D)         | 2   | Design target; no experimental demonstration |
| Multi‑unit coherent operation    | 1-2 | Conceptual only |
| **Overall Core Plasma Jet Module** | **3-4** | Integrated prototype under construction |
| **Overall HV Beam Module**       | **2**   | Detailed design stage |

**TRL Note:** Progression to TRL 5+ (component validated in relevant environment) requires successful integrated prototype testing under representative conditions.

---

## 9.2 Experimental Phases with Success Criteria

Progress through phases is strictly gated. Each phase includes a formal review (design review + safety review + data review) before authorisation to proceed. Quantitative success criteria must be met consistently across multiple runs.

| Phase | Configuration | Primary Objective | Quantitative Success Criteria | Duration / Deliverables |
|-------|---------------|-------------------|-------------------------------|-------------------------|
| **0** | Aerosol test cell (no plasma) | Characterise droplet charge, size, evaporation, and stability in electric fields | Droplet size distribution d₅₀ = 2-5 µm, span <1.5; charge distribution measured; Rayleigh limit verified; stable aerosol transport through drift tube without arcing for >30 min | 4 weeks; aerosol characterisation report |
| **1** | Core (atmospheric → 30-80 mbar) | Glow discharge I-V characterisation in air | Stable discharge at ≥1 mA for >1 h at 5 kV; repeatable I-V curves with <10 % hysteresis | 4-6 weeks; I-V datasets, stability logs |
| **2** | Core | Bernoulli pressure mapping & stability with mist | Achieve 30-80 mbar at drift tube with ±5 mbar stability under varying drive gas flows; entrainment ratio ≥1.5 | 4 weeks; pressure maps, CFD correlation report |
| **3** | Core | Plasma electron extraction & current transport | Faraday cup current >500 µA sustained; plasma jet optical emission stable for >30 min | 4 weeks; current vs. voltage/power curves |
| **4** | Core | Electron energy distribution & OES species identification | Retarding‑field analyser confirms 200-600 eV (air) peak with tail to ~2 keV; identify dominant plasma species via OES | 6 weeks; energy spectra, plasma parameter report |
| **5** | Core | Soft X‑ray generation & chemical effects | Detectable X‑rays (1-5 keV) with Si‑PIN detector; dose rate within safety limits; mist chemistry stability demonstrated | 6 weeks; X‑ray spectra, application feasibility data |
| **6** | HV upgrade | Vacuum system integration & base pressure | Achieve <10⁻⁵ mbar in drift tube within 60 min pump‑down; leak rate <10⁻⁹ mbar·L/s; RGA scan shows no hydrocarbon or water peaks above acceptable limits | 8 weeks; vacuum qualification report |
| **7** | HV | Ballistic electron beam & optics validation | Faraday cup current >100 µA at 50 kV; beam spot ≤500 µm at target; divergence <5° half‑angle; normalised emittance ≤50 mm·mrad | 8-10 weeks; beam profile, emittance data |
| **8** | HV | Positive‑ion beam & D‑D neutron production | Deuterium ion beam current >50 µA at 100 keV; neutron yield ≥1×10⁵ n/s (D‑D) measured with calibrated detector; target thermal stability and no vacuum degradation | 10-12 weeks; neutron spectra, yield curves, safety validation |
| **9** | Multi‑unit | Coherent beam combining & advanced experiments | Synchronise two+ units with <1 ns jitter; measurable coherent intensity increase; advanced experiments as approved by safety review | 12+ weeks; array performance report |

**Success Criteria Notes:**
- Phase 0 is a prerequisite: no plasma operation before aerosol stability is proven.
- The conservative targets for Phase 7 (spot ≤500 µm, εₙ ≤50 mm·mrad) and Phase 8 (yield ≥1×10⁵ n/s) represent the baseline validation. Stretch goals (≤200 µm, ≤20 mm·mrad, ≥1×10⁶ n/s) will be pursued only after the baseline is achieved and the system is well‑characterised.
- All phases require verification that safety interlocks, radiation monitors, and ventilation are fully functional before starting.

---

## 9.3 Gating Criteria

Before proceeding to any subsequent phase, the following must be satisfied:

- All safety interlocks, E‑stop circuits, and area monitors are verified and documented.
- Radiation surveys confirm dose rates are within safe limits (≤0.5 µSv/h at operator position for X‑rays; ≤2 µSv/h for neutrons).
- Measured performance agrees with models and simulations within stated uncertainty budgets.
- No unresolved high‑severity FMEA items remain.
- A formal go/no‑go review is held with key stakeholders, and the decision is documented in the project log (CPB‑LOG‑001).

---

## 9.4 Risk Management and Contingencies

**Primary Technical Risks:**
1. **Bernoulli-plasma compatibility:** The mist‑loaded flow may not sustain a stable pressure or may cause plasma instability. *Mitigation:* Phase 0 and 2 will fully characterise the flow before plasma integration; if needed, a small fore‑pump can be added to augment the Bernoulli stage.
2. **Aerosol charging and droplet instability:** Conductive aerosols in strong electric fields may undergo Coulomb fission or cause corona. *Mitigation:* Dedicated Phase 0 will quantify safe operating envelopes.
3. **HV vacuum integrity:** Outgassing from mist residues may limit base pressure. *Mitigation:* Bake‑out, cold traps, and rigorous cleaning protocols; provision for a larger turbomolecular pump if needed.
4. **Emitter lifetime:** LaB₆ cathodes may degrade faster than expected due to ion sputtering or contamination. *Mitigation:* Liquid‑metal emitter backup, scheduled replacement, and in‑situ conditioning.
5. **Neutron yield:** Actual yield may be lower than the conservative design target due to incomplete target loading or beam impurity. *Mitigation:* In‑situ deuterium loading, rotating target, and extended conditioning runs.

**Tracking:** Weekly progress reports, key performance indicators (KPIs) aligned with success criteria, and a live risk register will be maintained. A contingency budget (≈15 % of hardware cost) is reserved for mitigation actions.

**Budget & Resources:** Phased funding release is tied to milestone completion. Collaboration with external laboratories for specialised diagnostics (e.g., neutron detector calibration, MCNP simulations) is planned to reduce in‑house cost and improve credibility.

---

## 9.5 Documentation and Knowledge Capture

Each phase produces:
- Raw data archives (stored in CPB‑DATA‑001).
- Analysis notebooks (Python/Jupyter scripts with full uncertainty analysis).
- Updated FMEA and risk register (CPB‑RISK‑001).
- Calibration records (traceable to national standards).
- A lessons‑learned report, feeding into the next phase’s design review.

Supporting documents: CPB‑LOG‑001 (experimental log), CPB‑SIM‑00x (simulation reports).

---

**Overall Status:** The roadmap is structured to achieve a fully characterised Core Plasma Jet Module within 6-9 months of prototype assembly, followed by HV Beam validation over the subsequent 12-18 months. This phased approach minimises technical and financial risk while systematically building experimental evidence for all claimed performance parameters. All decision points are transparent and based on quantitative data, ensuring that the project remains scientifically credible and resource‑efficient.

---

## 10. Glossary

This glossary defines key technical terms used throughout the specification. Definitions are tailored to the CPB platform while remaining consistent with standard plasma, vacuum, accelerator, and safety engineering usage.

| Term | Definition |
|------|------------|
| **Activation Foil** | A thin metal foil (e.g., indium, gold, copper) exposed to neutron flux; the induced radioactivity provides a time‑integrated, threshold‑based measurement of neutron yield. |
| **Ballistic Transport** | Movement of charged particles in vacuum where the mean free path is much larger than the characteristic length; particles follow deterministic trajectories governed by electric and magnetic fields. |
| **Beam Brightness (B)** | Figure of merit for a particle beam, defined as \(B = 2I / (\pi^2 \varepsilon_n^2)\), where \(I\) is the beam current and \(\varepsilon_n\) the normalised emittance. Higher brightness indicates more current packed into a smaller phase‑space volume. |
| **Bernoulli Vacuum Stage** | Self‑pumping mechanism that uses a high‑velocity annular gas jet to entrain gas from the drift tube, reducing its static pressure to 30-80 mbar via the Bernoulli principle and momentum exchange. |
| **Cathode Fall** | The steep voltage drop in the thin sheath region adjacent to the cathode of a glow discharge. Ions accelerated across this fall produce secondary electrons that sustain the discharge. |
| **Child-Langmuir Law** | The space‑charge‑limited current density in a planar vacuum diode: \(J = (4\varepsilon_0/9)\sqrt{2e/m}\,V^{3/2}/d^2\). It sets the theoretical maximum current for a given voltage and gap. |
| **Collisional Plasma** | A plasma in which the mean free path for electron-neutral or ion-neutral collisions is much shorter than the system dimensions; transport is dominated by collisions rather than free‑streaming. The Core Plasma Jet Mode operates in this regime. |
| **Coulomb Fission** | Explosive disintegration of a charged droplet when the electrostatic repulsion exceeds the surface tension (Rayleigh limit). A key instability for conductive aerosols in strong electric fields. |
| **Crowbar** | A fast‑acting circuit that short‑circuits a high‑voltage output, safely dissipating stored energy in the event of an arc or interlock trip. |
| **Debye Length (λ_D)** | Characteristic distance over which electric fields are screened in a plasma; \(\lambda_D = \sqrt{\varepsilon_0 k_B T_e / (n_e e^2)}\). For λ_D ≪ system size, the plasma is quasi‑neutral. |
| **Electron Cyclotron Resonance (ECR)** | A method of plasma generation in which electrons are resonantly heated by microwaves at the cyclotron frequency, \(\omega = eB/m_e\), often used in ion sources. |
| **Entrainment Ratio** | Ratio of the mass flow induced from the drift tube to the mass flow of the driving gas. A measure of the Bernoulli stage’s pumping efficiency. |
| **Faraday Cup** | A conductive cup that intercepts a charged‑particle beam; the collected current, when properly suppressed for secondary electrons, yields an absolute measurement of beam current. |
| **Field Enhancement Factor (β)** | Dimensionless factor relating the local electric field at an emitter tip to the macroscopic field: \(E_{local} = \beta V/d\). β depends on nano‑scale geometry and surface condition. |
| **Fowler-Nordheim (FN) Emission** | Quantum‑mechanical tunnelling of electrons from a cold cathode under an intense electric field. The current density \(J\) is described by the Fowler-Nordheim equation. |
| **Glow Discharge** | A self‑sustaining, low‑current electrical discharge in a gas, characterised by a distinct cathode‑fall region, negative glow, and positive column. The Core Plasma Jet Mode is based on a glow discharge. |
| **Interlock** | A safety system that prevents equipment operation unless all pre‑defined safe conditions (e.g., doors closed, coolant flowing) are satisfied. Safety‑critical interlocks are hard‑wired and redundant. |
| **Knudsen Number (Kn)** | Ratio of the molecular mean free path to a characteristic length; Kn ≫ 1 indicates free‑molecular flow, Kn ≪ 1 indicates continuum flow. |
| **Langmuir Probe** | A diagnostic electrode inserted into a plasma; the current-voltage characteristic yields electron temperature and density (usable only at low pressure where probe theory is valid). |
| **Mean Free Path (λ)** | Average distance a particle (electron, ion, or neutral) travels between successive collisions: \(\lambda = 1/(n\sigma)\). Fundamental for distinguishing collisional vs. ballistic transport. |
| **Normalised Emittance (ε_n)** | A measure of beam quality that accounts for relativistic and geometric effects: \(\varepsilon_n = \beta\gamma\,\varepsilon_{rms}\). Conserved under ideal linear focusing; lower values indicate higher brightness. |
| **Optical Emission Spectroscopy (OES)** | Diagnostic technique that analyses light emitted by a plasma to identify species, estimate electron temperature, and monitor stability. |
| **Paschen Curve** | Plot of breakdown voltage vs. the product of pressure and electrode spacing (\(pd\)). The minimum of the curve corresponds to the most favourable conditions for gas breakdown. |
| **Pepper‑Pot Diagnostic** | An emittance measurement method in which a mask with small holes samples beamlets; their divergence and position on a downstream screen yield the beam’s phase‑space distribution. |
| **Perveance (K)** | Dimensionless parameter characterising space‑charge strength: \(K = (I/I_0)(1/\beta^3\gamma^3)\), where \(I_0 = 4\pi\varepsilon_0 m c^3/e\). Influences beam envelope growth. |
| **Phosphor Screen** | A material (e.g., P43, Gd₂O₂S:Tb) that emits visible light when struck by charged particles, used to image beam profiles. |
| **Plasma Frequency (f_p)** | Natural oscillation frequency of electrons in a plasma: \(f_p = \frac{1}{2\pi}\sqrt{n_e e^2/(\varepsilon_0 m_e)}\). Determines the upper frequency limit for electromagnetic wave propagation in the plasma. |
| **Rayleigh Limit** | The maximum charge \(Q_R = 8\pi\sqrt{\varepsilon_0 \gamma r^3}\) that a spherical droplet can hold before electrostatic stress overcomes surface tension, causing Coulomb fission. |
| **Residual Gas Analyser (RGA)** | A mass spectrometer that monitors the composition and partial pressures of gases in a vacuum system; essential for detecting contaminants and verifying deuterium purity. |
| **Retarding‑Field Analyser (RFA)** | Diagnostic that uses biased grids to filter charged particles by energy; scanning the grid voltage yields the energy distribution function. |
| **Space‑Charge Limited Flow** | The regime in which the current in a vacuum diode is limited by the self‑field of the charged particles, as described by the Child-Langmuir law. |
| **Technology Readiness Level (TRL)** | A scale from 1 (basic principles) to 9 (proven system) used to assess the maturity of a technology or subsystem. |
| **Townsend Coefficient (α)** | The number of ionising collisions per unit length made by an electron drifting in an electric field; fundamental to gas breakdown theory and the Paschen curve. |
| **Triple‑Junction** | The point where metal, insulator, and vacuum (or gas) meet; a common site for field‑enhanced electron emission and vacuum breakdown. |
| **Work Function (φ)** | Minimum energy required to remove an electron from the Fermi level of a solid to vacuum; a critical parameter in field emission (e.g., φ ≈ 2.6 eV for LaB₆, ≈ 2.7 eV for thoriated tungsten). |

---

---

## 11. References

[1] J. W. Gadzuk and E. W. Plummer, “Field Emission Energy Distribution (FEED),” *Rev. Mod. Phys.* **45**, 487 (1973). DOI:10.1103/RevModPhys.45.487

[2] J. M. Lafferty, “Boride Cathodes,” *J. Appl. Phys.* **22**, 299 (1951). DOI:10.1063/1.1699946

[3] Y. P. Raizer, *Gas Discharge Physics*, Springer (1991). ISBN:978-3-642-64760-4

[4] E. M. Oks, *Plasma Cathode Electron Sources*, Wiley-VCH (2006). ISBN:978-3-527-40634-4

[5] R. G. Forbes, “Fowler-Nordheim Plot Analysis: A Progress Report,” arXiv:1504.06134 (2015). DOI:10.48550/arXiv.1504.06134

[6] R. G. Forbes, “Extraction of emission parameters for large-area field emitters,” arXiv:1111.7298 (2011). DOI:10.48550/arXiv.1111.7298

[7] Lord Rayleigh, “On the Equilibrium of Liquid Conducting Masses Charged with Electricity,” *Phil. Mag.* **14**, 184 (1882). DOI:10.1080/14786448208628425

[8] NIST Electron-Impact Cross Section Database, https://www.nist.gov/pml/electron-impact-cross-sections (accessed 2026).

[9] D. J. Malbrough et al., “Thick-target neutron yield measurements using metal occluders,” ORNL/TM-11718 (1990). DOI:10.2172/720914

[10] IAEA, *Neutron Generators for Analytical Purposes*, IAEA Radiation Technology Reports No. 1 (2012). https://www-pub.iaea.org/MTCD/Publications/PDF/P1535_web.pdf

### Additional References

[11] A. Anders, “Glows, arcs, and ohmic discharges: An electrode-centered review,” *Appl. Phys. Rev.* **11**, 031310 (2024). DOI:10.1063/5.0210301

[12] K. H. Schoenbach et al., “Plasma Cathodes for High Pressure Glow Discharges,” Air Force Research Laboratory Report (2000). (DTIC ADA382817)

[13] Z. Machala et al., “DC Glow Discharge in Atmospheric Pressure Air,” *J. Adv. Oxid. Technol.* **7**, 133 (2004).

[14] R. G. Forbes and J. H. B. Deane, “Reformulation of the standard theory of Fowler-Nordheim tunnelling,” *Proc. R. Soc. A* **467**, 2927 (2011). DOI:10.1098/rspa.2011.0226

[15] J. R. Riba Ruiz et al., “Effect of Pressure and Supply Frequency on the Mean Free Path of Electrons in Air,” *J. Quant. Spectrosc. Radiat. Transfer* (relevant cross-section study).

[16] NIST ESTAR, PSTAR, and ASTAR Databases - Stopping-Power and Range Tables for Electrons, Protons, and Helium Ions, https://physics.nist.gov/Star

[17] SRIM - The Stopping and Range of Ions in Matter, http://www.srim.org (Ziegler et al.)

[18] D. E. Gray (ed.), *American Institute of Physics Handbook*, 3rd ed., McGraw-Hill (1972). (Paschen curve and breakdown data)

[19] M. A. Lieberman and A. J. Lichtenberg, *Principles of Plasma Discharges and Materials Processing*, 2nd ed., Wiley (2005). ISBN:978-0-471-72001-0

[20] P. W. Hawkes and E. Kasper, *Principles of Electron Optics*, Volumes 1-3, Academic Press (various editions). (Beam optics and immersion lenses)

[21] L. Reimer, *Scanning Electron Microscopy*, 2nd ed., Springer (1998). DOI:10.1007/978-3-540-38967-5 (interaction volumes and X-ray production)

[22] IAEA Nuclear Data Services - Evaluated Nuclear Data for D-D and D-T reactions, https://www-nds.iaea.org/

[23] C. A. Brau, “Electron-Ion Recombination in Gas Discharges,” *Phys. Rev. A* (relevant plasma parameter references)

[24] J. D. Lawson, *The Physics of Charged-Particle Beams*, 2nd ed., Oxford University Press (1988). ISBN:978-0-19-851719-1 (emittance, brightness, space charge)

---

## Data Sources
- Electron cross‑sections: NIST, LXCat (www.lxcat.net)
- Stopping powers: NIST ESTAR/PSTAR/ASTAR, SRIM (www.srim.org)
- Neutron yields: IAEA Evaluated Nuclear Data Library

---

## 12. Summary

The Coherent Particle Beam (CPB) device is a compact, modular electro-fluidic platform built around a self-pumping Bernoulli vacuum stage. In its **Core Plasma Module** (30-80 mbar), it generates a stable, collisional glow-discharge plasma jet using a conductive aerosol working fluid. This enables practical low-to-medium energy applications including soft X-ray production, plasma antennas, surface treatment, and plasma-assisted chemistry - all without requiring high vacuum.

By adding a compact high-vacuum stage (turbomolecular pump + gate valve), the same core hardware transitions into a **High-Vacuum (HV) particle accelerator** capable of ballistic transport, producing focused electron beams (5-100 keV), positive ion beams (10-300 keV), and neutrons via D-D reactions on a deuterated target. This dual-regime architecture preserves the original multi-modal vision while grounding every operating mode in correct physics: collisional plasma in the Core regime and vacuum beam physics in the HV regime.

This Revision 3.4 incorporates:
- Realistic performance targets with confidence levels and validation methods.
- Clear separation of Core and HV operating regimes based on mean free path analysis.
- Expanded diagnostics, safety systems, FMEA, and a gated experimental roadmap.
- Strengthened references and engineering margins.
- Emphasis on modularity, maintainability, and incremental development.

**Key Recommendation**: Prioritise rapid validation of the Core Plasma Module (Phases 1-5) to confirm Bernoulli performance, plasma stability, emitter lifetime, and mist compatibility before committing significant resources to the HV upgrade. Successful Core demonstration will de-risk the platform and provide immediate scientific and application value.

The CPB represents a versatile research and technology platform with potential applications ranging from compact X-ray/neutron sources to plasma processing and advanced beam experiments. Continued iterative prototyping, rigorous diagnostics, and safety-first operation will determine its ultimate performance and utility.

---