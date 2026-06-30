**ENGINEERING SPECIFICATION**

# Coherent Particle Beam (CPB) Device:  
Multi‑Modal Open‑Atmosphere Particle Valve

**Document ID:** CPB‑ENG‑001  
**Revision:** 4.0  
**Date:** 2026-07-02  
**Classification:** Technical Engineering Document  

---

## 1. Overview

The Coherent Particle Beam (CPB) device is a compact, electro‑fluidic particle source built around a self‑pumping Bernoulli vacuum stage. It is designed to operate in two fundamentally distinct physical regimes, separated by a rigorous vacuum gate.

**Core Plasma Module (30–80 mbar)**  
In its baseline configuration, the device sustains a collisional glow discharge within a narrow drift tube, using a conductive, residue‑free working fluid (a volatile electrolyte mist). The output is a weakly ionised plasma jet—not a particle beam—that supports applications such as soft X‑ray generation (<5 keV), plasma RF antennas, surface activation, and plasma‑assisted chemistry. The Bernoulli stage maintains the operating pressure without moving parts, and the mist chemistry can be tailored for specific processes.

**High‑Vacuum (HV) Beam Module (≤10⁻⁵ mbar at the emitter)**  
An optional upgrade integrates a differentially pumped high‑vacuum system and a dedicated field‑emission cathode. When the system is fully baked, purged, and the emitter‑end pressure is demonstrated to be ≤1×10⁻⁵ mbar, the device can operate as a conventional electrostatic accelerator. Under these conditions, ballistic transport of electrons (5–100 keV) or positive ions (10–300 keV) becomes possible, enabling focused beam modes and, with a deuterated target, D‑D neutron production. All HV‑mode performance targets are contingent upon successful completion of the vacuum gate requirements.

The two regimes are explicitly distinguished by their pressure range and dominant collision processes; the HV module is not an extension of Core operation but a separate operational mode that can only be entered after rigorous vacuum qualification. This revision of the specification incorporates a differential pumping architecture, separate emitter cartridges for each mode, and a volatile working fluid to resolve fundamental vacuum‑conductance and contamination issues identified in earlier designs.

This document is a living specification; as the experimental programme progresses, estimated parameters will be replaced by measured values, and the roadmap will be updated accordingly.

---

# 2. Engineering Requirements

## 2.1 Core Plasma Jet Module (Collisional, 30–80 mbar)

The Core module produces a **collisional plasma jet**, not a coherent particle beam. All performance values are design targets requiring experimental validation. The working fluid shall be chosen to enable eventual transition to HV mode; the baseline is a volatile electrolyte solution that leaves no solid residues after bake‑out (see §2.5).

| Parameter                          | Requirement                                              | Confidence | Validation Method                                                       |
| ---------------------------------- | -------------------------------------------------------- | ---------- | ----------------------------------------------------------------------- |
| Operating pressure (drift tube)    | 30–80 mbar                                               | Medium     | Calibrated pressure transducers (Kulite XCQ‑093), repeatability ±5 mbar |
| Pressure stability                 | ±10 mbar (with mist)                                     | Medium     | Continuous logging during 1 h operation                                 |
| Electron energy (afterglow)        | 0.2–2 keV                                                | Medium     | Retarding‑field analyser and X‑ray spectrum                             |
| Plasma current                     | 10 µA – 2 mA                                             | High       | Faraday cup (±1.5 %)                                                    |
| Plasma jet divergence (half‑angle) | <10°                                                     | Low        | Optical imaging and phosphor target                                     |
| Maximum operating voltage          | ±10 kV                                                   | High       | Calibrated HV divider                                                   |
| HV ripple                          | <1 % p‑p                                                 | High       | High‑voltage oscilloscope probe                                         |
| Duty cycle                         | Continuous (100 %)                                       | Medium     | 8‑hour endurance test                                                   |
| Core thermal load                  | ≤50 W                                                    | Medium     | Embedded thermocouples and IR imaging                                   |
| MTBF (excluding consumables)       | >500 h                                                   | Low        | Operational reliability testing                                         |
| Plasma stability                   | Continuous operation without self‑extinguishing for >1 h | Medium     | Automated discharge monitoring                                          |
| Current regulation bandwidth       | >1 kHz                                                   | Medium     | Closed‑loop step response                                               |

**Additional Requirement for Combined‑Mode Compatibility**

| Requirement                                          | Classification     | Validation Method                                       |
| ---------------------------------------------------- | ------------------ | ------------------------------------------------------- |
| Working fluid residue‑free behaviour                 | Gate Requirement   | Vacuum recovery test per §2.5; must leave no non‑volatile residues after 8 h run and bake‑out |
| Drift tube purge capability                          | Mandatory          | Dry N₂ flush system verified to reduce dew point ≤‑40 °C within 15 min |

**Core Module Status:** Prototype engineering target. Performance values require experimental validation. The module may be operated with any compatible working fluid during early prototyping; however, the fluid used during final Core validation runs must pass the residue‑free requirement if HV‑mode operation is planned thereafter.

---

## 2.2 High‑Vacuum Beam Module (Ballistic, <10⁻⁵ mbar at the Emitter)

All HV‑mode parameters are **preliminary design targets** that assume the successful implementation of a differential vacuum pumping architecture (§3.11) delivering an emitter‑end pressure ≤ 1 × 10⁻⁵ mbar. If that condition is not met, the beam will be heavily scattered and the performance values below are not physically achievable. Confidence levels are deliberately conservative; values will be updated after vacuum qualification and beam commissioning.

| Parameter                             | Requirement                                            | Confidence | Validation Method                                                 |
| ------------------------------------- | ------------------------------------------------------ | ---------- | ----------------------------------------------------------------- |
| Emitter‑end base pressure             | ≤1 × 10⁻⁵ mbar (during beam operation)                 | High       | Emitter‑end cold‑cathode/Pirani gauge; logged continuously        |
| Front‑end base pressure               | <1 × 10⁻⁶ mbar (pump gauge)                            | High       | Full‑range gauge at beamline                                      |
| Pump‑down time (after bake)           | <30 min to emitter‑end ≤ 10⁻⁵ mbar after gate‑valve open| Medium     | Logged vacuum profile                                             |
| Effective pump speed at emitter       | ≥2 L s⁻¹ (design goal)                                 | Medium     | Conductance calculation verified by pressure‑rise rate measurement|
| Electron energy                       | 5–100 keV                                              | Low        | Retarding‑field analyser, X‑ray endpoint spectrum                 |
| Ion energy (H⁺, D⁺, He⁺)              | 10–300 keV                                             | Low        | Acceleration voltage; time‑of‑flight (future)                     |
| Beam current                          | 10 µA – 2 mA                                           | Low        | Faraday cup                                                       |
| Beam divergence (half‑angle)          | <5°                                                    | Low        | Phosphor screen imaging                                           |
| Normalised emittance (εₙ)             | ≤50 mm·mrad (design target)                            | Low        | Pepper‑pot / slit‑scan diagnostic                                 |
| Beam brightness (B)                   | ≥5 × 10⁵ A/(m²·rad²) (predicted)                       | Low        | Derived from emittance measurements                               |
| Electron energy spread (FWHM)         | <5 %                                                   | Low        | Retarding‑field analyser                                          |
| Beam spot diameter                    | ≤500 µm at 100 keV, 1 mA                               | Low        | Knife‑edge scan and phosphor imaging                              |
| Maximum HV supply                     | ±100 kV operating (±120 kV design)                     | High       | Calibrated HV divider                                             |
| HV ripple                             | <0.1 % p‑p                                             | High       | HV oscilloscope probe                                             |
| Stored energy                         | <3 J                                                   | Medium     | Capacitance measurement and calculation                           |
| Target heat load                      | ≤100 W at 100 keV, 1 mA                                | High       | Beam power calculation and calorimetry                            |
| Target cooling capacity               | ≥200 W                                                 | High       | Flow and thermal testing                                          |
| Target temperature trip (D‑D mode)    | ≤250 °C                                                | High       | Embedded thermocouples; rate‑of‑rise alarm                        |
| Neutron yield (D‑D, 100 keV)          | ≥1 × 10⁵ n/s at 0.1 mA (design target)                 | Low        | Calibrated neutron detector                                       |
| X‑ray shielding                       | <1 µSv/h at 30 cm (with shielding)                     | High       | Survey meter measurements                                         |
| Beam alignment repeatability          | <100 µm                                                | Low        | Alignment fixture and beam diagnostics                            |

**Conditional Note:** All HV‑mode beam performance parameters (energy, emittance, brightness, spot size, neutron yield) are predicated on the vacuum gate requirements (§2.5) being satisfied. Until the emitter‑end pressure ≤ 1 × 10⁻⁵ mbar is demonstrated and maintained during operation, these targets must be regarded as speculative.

**HV Module Status:** Preliminary design targets; dependent on differential pumping system validation. Conservative estimates have been adopted pending experimental demonstration.

---

## 2.3 Parameter Provenance

| Confidence | Definition                                                                                                           |
| ---------- | -------------------------------------------------------------------------------------------------------------------- |
| **High**   | Established by accepted physics, commercial hardware specifications, or direct calculation.                          |
| **Medium** | Supported by analytical models, simulations, or published literature, but requires confirmation in the CPB geometry. |
| **Low**    | Preliminary design target or engineering estimate requiring prototype validation.                                    |

---

## 2.4 Requirement Classification

| Classification       | Meaning                                                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| **Requirement**      | Mandatory engineering specification that the system must satisfy.                               |
| **Design Target**    | Expected performance based on calculations or literature; subject to experimental verification. |
| **Measured Value**   | Parameter verified experimentally and traceable to calibrated instrumentation.                  |
| **Predicted Value**  | Derived from analytical models or numerical simulations awaiting validation.                    |
| **Gate Requirement** | A mandatory condition that must be satisfied before a subsequent development phase may proceed.  |

**Note:** Unless otherwise stated, all performance values in this specification are **design targets**. Parameters will transition to **measured values** as experimental validation progresses. This specification is intended to evolve alongside prototype development.

---

## 2.5 Vacuum Gate Requirements (Pre‑HV Commissioning)

The following requirements must be met before any attempt to operate the HV beam mode. They form a formal go/no‑go gate (Phase 6a in the roadmap). These are hard requirements, not design targets.

| Requirement                                                | Value                                     | Validation Method                                                                 |
| ---------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------- |
| Emitter‑end pressure after bake‑out (clean system)         | ≤1 × 10⁻⁵ mbar within 48 h pump‑down      | Emitter‑end vacuum gauge; logged data                                            |
| Emitter‑end pressure after 8 h Core run + purge + bake     | ≤1 × 10⁻⁵ mbar within 48 h pump‑down      | Repeat of above after a representative Core‑mode operation with the chosen fluid  |
| Differential pumping effective speed at emitter            | ≥2 L s⁻¹ (or as required by conductance analysis) | Pressure‑rise rate measurement; validated by molecular‑flow simulation           |
| Drift tube temperature uniformity during bake              | 150 ± 10 °C across all monitored points   | Multi‑point thermocouple array                                                   |
| Working fluid residue test                                 | No non‑volatile residues detected by RGA  | RGA scan after bake‑out; mass peaks of NaCl, etc. below detection limit           |
| Emitter interchange procedure                              | Core emitter replaced by HV emitter in <4 h, without contamination of HV surfaces | Cleanliness verification (RGA, visual inspection)                                 |
| HV emitter conditioning success                            | Stable FN plot (linear over ≥3 decades of I‑V) for >1 h with β ≥ 50 | Fowler‑Nordheim analysis of I‑V data; continuous emission stability               |

These gate requirements directly address the primary risks: insufficient vacuum at the emitter, contamination legacy from the working fluid, and emitter compatibility. No HV beam operation shall commence until all gate items are satisfied and documented.

---

## 3. Physical Configuration

The Coherent Particle Beam (CPB) platform is a modular electro‑fluidic system. This section describes the hardware for both the **Core Plasma Jet Mode** (collisional, 30–80 mbar) and the **High‑Vacuum (HV) Beam Mode** (ballistic, <10⁻⁵ mbar at the emitter). All HV‑mode capabilities are contingent upon the successful implementation of a differential vacuum pumping architecture that ensures true ballistic conditions at the electron/ion source. The following subsections incorporate the necessary design changes identified during revision.

---

### 3.1 Inner Drift Tube

The inner drift tube forms the primary plasma channel in Core Plasma Jet Mode and the accelerating drift region in High‑Vacuum Beam Mode. It serves as the electrical reference geometry and the primary vacuum boundary.

**Material**  
- **Prototype:** Platinum‑clad (electroplated) 316L stainless steel, or Nickel 200.  
- **Validated geometry (later builds):** Platinum or Platinum‑Iridium (90/10).  
- **HV‑only option:** Molybdenum (requires oxidation protection).  
- **For combined Core+HV operation:** The tube material must withstand repeated bake‑out cycles to 150 °C without degradation. Ceramic tubes (e.g., ALON, sapphire) are acceptable only if the braze joints and thermal expansion mismatches are qualified for thermal cycling and vacuum integrity.  

Materials shall be chemically compatible with the chosen working fluid (a volatile, residue‑free electrolyte; see §3.6), hydrogen, deuterium, helium, and air. A full compatibility matrix is maintained in Appendix C.

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

**Bake‑out Design**  
The drift tube shall be fitted with an integrated heating system (e.g., external heating jacket, cartridge heater block) capable of maintaining the entire length at 150 ± 10 °C for ≥24 hours. Multiple thermocouples along the tube verify temperature uniformity. The bake‑out system must be operable while the emitter feedthrough is installed and the tube is under vacuum.

**Operating Modes**

*Core Plasma Jet Mode*  
- Rear end sealed with electrode feedthrough (Core emitter, §3.2.1).  
- Front end opens into the collector/shroud region.  
- Working fluid mist travels through the tube.

*High‑Vacuum Beam Mode*  
- The Core emitter is replaced by the HV emitter assembly (§3.2.2).  
- A dedicated vacuum pump at the emitter end (see §3.11) and the front turbomolecular pump together evacuate the tube.  
- Front end connects via a CF‑16 flange and all‑metal gate valve to the beamline.  
- After Core mode operation, a rigorous purge and bake procedure is executed before HV pump‑down.

**Manufacturing Notes**  
- Tube shall be vacuum cleaned and baked before initial assembly.  
- Ceramic‑compatible brazing alloys only.  
- All wetted surfaces free of machining oils, chlorides, and hydrocarbons.

**Cost Note**  
Initial prototypes shall use platinum‑clad steel or nickel. Solid platinum components are reserved for later validation units after the geometry and operating envelope have been experimentally verified.

---

### 3.2 Emitter Assemblies

The CPB uses two distinct, interchangeable emitter assemblies: one for Core plasma operation and one for HV field‑emission operation. They shall not be the same physical unit.

#### 3.2.1 Core Plasma Jet Emitter (Glow Discharge Cathode)

This emitter is designed for robust secondary emission in a collisional plasma environment, tolerating mist exposure and ion bombardment.

**Geometry** (same as original toroid)

| Parameter | Value |
|-----------|-------|
| Major diameter | 2.00 ± 0.05 mm |
| Minor diameter | 0.50 ± 0.02 mm |
| Emitter‑to‑tube radial clearance | 0.75 ± 0.10 mm (critical for Paschen breakdown; see §4.3) |

**Materials**  
- **Preferred:** Lanthanum Hexaboride (LaB₆, φ ≈ 2.6 eV) – non‑radioactive.  
- **Alternatives:** W‑2 % ThO₂ (requires radiation handling plan), Hafnium carbide, Tungsten, or a Gallium‑Indium liquid metal reservoir for replenishment.

**Mounting**  
- Insulator: 99.8 % Alumina or Boron Nitride.  
- Vacuum‑compatible ceramic feedthrough; torque 0.40 ± 0.05 N·m.

**Operating Regime**  
- **Dominant mechanism:** Secondary emission from ion bombardment sustains a glow discharge.  
- **Electron energies:** 200–600 eV in air; up to ~2 keV in hydrogen.  
- **Behaviour:** Collisional plasma; not a ballistic beam.

#### 3.2.2 High‑Vacuum Beam Emitter (Field‑Emission Cathode)

This emitter provides the primary electron source for ballistic acceleration in HV Beam Mode. It is installed only after the system has been fully baked and the emitter‑end vacuum verified ≤1 × 10⁻⁵ mbar. The HV emitter must never be exposed to working fluid mist.

**Architecture**  
The HV emitter resides in a small, UHV‑compatible chamber adjacent to the rear of the drift tube. A conductance‑limiting aperture (≤1 mm diameter) separates this chamber from the main drift tube, enabling differential pumping while allowing the extracted electron beam to pass through. The emitter chamber is pumped by a dedicated ion pump (see §3.11).

**Emitter Geometry (preliminary)**  
- Sharp tip, small LaB₆ crystal, or multi‑tip array.  
- The exact shape will be optimised using SIMION; the key requirement is a reproducible field enhancement factor β ≥ 50 after conditioning.

**Materials**  
- Clean LaB₆ (φ ≈ 2.6 eV) or alternative low‑work‑function material (e.g., carbon nanotube forest, ZrC).  
- Handling and installation performed under UHV conditions or in a dry nitrogen glovebox.

**Mounting**  
- On a dedicated, clean ceramic (Al₂O₃) feedthrough with in‑situ heating capability for thermal conditioning (up to 800 °C).  
- Alignment must centre the emitter tip on the drift tube axis within ±0.1 mm.

**Operating Regime**  
- **Dominant mechanism:** Fowler–Nordheim field emission.  
- **Surface conditioning:** The emitter will be conditioned by gradual voltage increase under UHV, with continuous monitoring of the FN plot linearity and stability. A conditioning protocol with pass/fail criteria is defined in the operational procedures.  
- **Performance target:** Stable emission current 10 µA–2 mA at voltages up to 100 kV, with current noise <5 % RMS over 1 hour.

---

### 3.3 Modulation Grid

**Construction**  
- Pt‑Ir wire, diameter 0.10 ± 0.01 mm.  
- Positioned 1–2 mm inside the drift tube exit.  
- Isolated from the tube by machinable ceramic spacers.

**Driver**  
- Wideband buffer amplifier (e.g., THS3491), bandwidth 200 MHz.  
- Load capacitance 5–20 pF; bias ±100 V.  
- Minimum pulse width 10 ns; maximum repetition rate 10 MHz.  
- Rise time target <5 ns.  
*Note: The effective load impedance in the presence of plasma may differ significantly from a pure capacitance; bench‑testing in a representative plasma environment is required.*

*For Core plasma modulation, a lower‑bandwidth amplifier may suffice and is acceptable for initial tests.*

---

### 3.4 Collector Assembly (Core Plasma Jet Mode)

**Material**  
- Platinum‑clad or tungsten‑lined 316L stainless steel.

**Geometry**  
- Concentric cylinder, ID 8.00 ± 0.05 mm, extending 15 mm beyond the drift tube exit.

**Functions**  
- Collector / ground reference.  
- Plasma stabilisation.  
- Thermal sink.  
- In HV Beam Mode, this assembly is removed and replaced by the beamline.

---

### 3.5 Bernoulli Vacuum Stage

The Bernoulli stage maintains the 30–80 mbar operating environment for Core Plasma Jet Mode. It is the **highest‑risk subsystem** and will be validated first. The design shall include provisions for purging the drift tube with dry nitrogen after Core operation to aid the transition to HV mode.

**Design Parameters**

| Parameter | Target | Status |
|-----------|--------|--------|
| Drive pressure | 3–5 bar (gauge) | Design |
| Drive gas flow rate (STP) | 30–60 L min⁻¹ | Estimated |
| Drift tube pressure | 30–80 mbar | Experimental target |
| Pressure stability | ±10 mbar (with mist) | Design target |
| Entrainment ratio (no mist) | 1.5–3.0 | Estimated from CFD |
| Entrainment ratio (with mist) | ≥1.0 (target) | To be measured |

**Instrumentation**  
- Pressure: Kulite XCQ‑093 transducers at multiple axial locations; dedicated Pirani gauge near the emitter for mode‑transition monitoring.  
- Flow: Mass flow controller + thermal flow meter.  
- Temperature: PT100 RTDs.  
- Gas composition: Residual gas analyser (used during purge and pump‑down).

**Engineering Risks & Validation**  
- Primary uncertainties: back‑diffusion of atmospheric gases, mist loading effects, boundary‑layer separation, and compressor stability.  
- Phase 2 testing will map pressure profiles with and without mist, quantify entrainment ratio, and correlate CFD models.  
- The purge system will be verified by measuring the humidity drop after a simulated Core run.

---

### 3.6 Conductive Working Fluid (Mist)

The conductive aerosol provides charge transport, plasma stabilisation, and optional chemical functionality. The fluid must be chosen to satisfy both Core plasma performance and the stringent cleanliness requirements for subsequent HV operation.

**Fluid Selection for Combined‑Mode Operation**  
- The baseline working fluid is **deionised water with 0.1–1 % ammonium acetate** (or an equivalent volatile organic salt). This electrolyte decomposes into gaseous products (NH₃, CO₂, H₂O) during bake‑out at 150 °C, leaving no solid residues.  
- Other volatile, non‑toxic electrolytes may be substituted after experimental validation of residue‑free behaviour.  
- **Saline (NaCl) solutions are prohibited in any configuration that will later be used for HV Beam Mode**, because sodium chloride is non‑volatile and leaves insulating, hygroscopic deposits that permanently compromise vacuum and field emission. Saline may be used only in dedicated Core‑only test stands where the drift tube will never be required to reach UHV.

**Atomisation:** Ultrasonic nebuliser (1–5 MHz) or high‑pressure nozzle. Median droplet diameter 2–5 µm, span <1.5.

**Electrical Properties:** For a 1 % ammonium acetate solution (σ ≈ 1 S m⁻¹, εᵣ ≈ 80), the charge relaxation time τ = ε₀εᵣ/σ ≈ 7 × 10⁻¹⁰ s – effectively instantaneous. The exact conductivity will be measured as a function of concentration. Droplets may approach the Rayleigh limit; Coulomb fission and evaporation will be studied experimentally. (The earlier example of 3 % saline gave τ ≈ 1.4 × 10⁻¹⁰ s, provided as a well‑known reference only.)

**Required Characterisation (Pre‑Plasma Phase):**  
- Droplet size distribution (laser diffraction).  
- Charge distribution (Faraday pail).  
- Electrical conductivity vs. concentration.  
- Evaporation rate and residence time.  
- Mobility in electric fields.  
- Deposition on insulators and electrodes.

A **dedicated aerosol‑only test cell** will be constructed to quantify these parameters before integrating the plasma discharge. This phase is a prerequisite for Core Mode validation.

**Vacuum Recovery Acceptance Test**  
After 8 hours of continuous Core‑mode operation with the chosen fluid, the system shall be purged with dry nitrogen for 15 minutes, then evacuated and baked at 150 °C. The emitter‑end vacuum gauge (see §3.11) shall indicate a pressure ≤1 × 10⁻⁵ mbar within 48 hours of bake‑out initiation. Successful completion of this test is mandatory before HV‑mode commissioning.

**Maintenance:** Filters will protect ceramics, optics, and pressure sensors; the mist chamber and tube will be flushed periodically with deionised water and dried with nitrogen.

---

### 3.7 High‑Voltage Supply

Two configurations:  
- **Core Plasma Jet:** 0–12 kV design, operating ±10 kV, current‑limited.  
- **High‑Vacuum Beam:** 0–120 kV design, operating ±100 kV.

| Parameter | Core | HV |
|-----------|------|----|
| Ripple (p‑p) | <1 % | <0.1 % |
| Regulation bandwidth | >1 kHz | >1 kHz |
| Current limit | 0–5 mA | 0–5 mA |
| Stored energy | <1 J | <3 J |

**Protection:** Fast crowbar, current‑limiting resistor, arc detection, ground continuity monitor, emergency discharge relay, and fully interlocked enclosure.

---

### 3.8 Beam Optics (HV Beam Mode Only)

Beam transport uses an electrostatic immersion lens formed by the drift tube exit and a downstream grounded aperture. Optional magnetic correction (SmCo ring or air‑core solenoid) provides fine focus and steering.

**Design Targets (Conservative, Pre‑Validation):**

| Parameter | Design Target | Status |
|-----------|---------------|--------|
| Spot diameter | ≤500 µm at 100 keV, 1 mA | Predicted |
| Normalised emittance | ≤50 mm·mrad | Estimated |
| Beam brightness | ≥5 × 10⁵ A/(m²·rad²) | Predicted |

*These values assume that the electron beam is emitted into a true vacuum (<1 × 10⁻⁵ mbar) and that transport is ballistic. If the vacuum fails to meet this condition, the beam will be heavily scattered and the optics will not function as designed.* The targets will be refined using SIMION simulations and pepper‑pot/slit‑scan measurements after beam commissioning. The ambitious stretch goals (≤200 µm, ≤20 mm·mrad) are retained as long‑term objectives.

---

### 3.9 Target Assembly and Thermal Management (HV Mode)

**Target:** OFHC copper core, 5 µm titanium coating. For neutron generation, the titanium is converted to TiD₂ by in‑situ deuterium loading.

**Beam Power:** 100 keV × 1 mA = 100 W deposited into the target. The spot size (≤500 µm) leads to a power density ~5 × 10⁸ W m⁻²; effective heat spreading is critical. A water‑glycol cooling loop removes up to 200 W. Thermal FEA will be validated against calorimetric measurements.

**Instrumentation:** Embedded thermocouples, RTDs, IR camera, and flow sensors. A beam‑trip interlock is triggered if the target temperature exceeds **250 °C during deuterium operation** (to prevent premature deuterium release from TiD₂ and limit tritium retention) or **400 °C for non‑deuterium modes**. A rate‑of‑rise temperature alarm provides early warning of cooling failure.

---

### 3.10 Ion Source (HV Beam Mode)

Supported configurations: hollow‑cathode insert or ECR source (2.45 GHz).  
Operating gases: H₂, D₂, He, Ar.  
Ion species and energy distributions will be characterised with a retarding‑field analyser before accelerator operation.

---

### 3.11 High‑Vacuum System and Differential Pumping

The high‑vacuum system is designed to achieve ballistic transport by maintaining the emitter region at ≤1 × 10⁻⁵ mbar while the remainder of the drift tube is evacuated from the front. The architecture overcomes the severe conductance limitation of the narrow drift tube through differential pumping.

#### 3.11.1 Pumping System Components

- Oil‑free scroll roughing pump (15 m³ h⁻¹).  
- Front‑end turbomolecular pump (300 L s⁻¹ for N₂) connected to the drift tube exit via a CF‑16 all‑metal gate valve.  
- **Emitter‑end differential pump:** a small ion pump (≥2 L s⁻¹) or turbomolecular pump cartridge mounted on the emitter chamber, providing local high‑vacuum at the electron/ion source. The pump shall be sized based on conductance calculations.  
- A second all‑metal gate valve isolates the emitter‑end pump during Core plasma operation.  
- Full‑range gauge (Pirani + cold cathode) at the front beamline.  
- **Emitter‑end vacuum gauge:** a miniature Pirani or cold‑cathode gauge located within 10 mm of the emitter surface, permanently integrated to verify local pressure.  
- Residual gas analyser (mandatory for D₂ operation).  
- Bake‑out heaters and multi‑point temperature sensors for the entire drift tube (§3.1).

#### 3.11.2 Differential Pumping Architecture

The drift tube (2 mm ID × 150 mm) has a molecular‑flow conductance of approximately 0.0065 L s⁻¹ for N₂. With only the front turbopump, the effective pumping speed at the emitter would be limited to this tiny value, making it impossible to reach <10⁻⁵ mbar at the emitter after mist exposure. Therefore, the HV configuration employs differential pumping:

- The HV emitter is housed in a small, UHV‑compatible chamber attached to the rear of the drift tube.  
- A small aperture (≤1 mm diameter) or a short conductance‑limiting tube separates the emitter chamber from the main drift tube, allowing the electron beam to pass while restricting gas flow.  
- The emitter chamber is evacuated by the dedicated ion pump, which maintains the emitter at ≤1 × 10⁻⁵ mbar even when the front of the drift tube is at a slightly higher pressure.  
- During HV beam operation, both the front turbopump and the emitter‑end pump operate. The resulting pressure profile along the tube is a gradient, with the lowest pressure at the emitter.  
- When transitioning from Core mode, the emitter‑end pump is initially isolated. The drift tube is purged, baked, and rough‑pumped from the front. Once the tube is dry, the emitter‑end gate valve is opened and the ion pump is activated, pulling the emitter region into UHV.

**Conductance Calculations**  
Detailed conductance calculations and, if necessary, Monte‑Carlo molecular‑flow simulations (Molflow+) shall be performed before procuring vacuum hardware. These calculations shall demonstrate that with the chosen aperture and pump speeds, the steady‑state emitter‑end pressure is ≤1 × 10⁻⁵ mbar under the expected outgassing load after bake‑out. The analysis is documented in Appendix D.

**Performance Acceptance**  
After assembly and bake‑out, the emitter‑end gauge shall read ≤1 × 10⁻⁵ mbar within 48 hours of pump‑down. This must be demonstrated both with a clean, dry system and after a full‑duration Core mode run followed by the purge‑and‑bake procedure (§3.6). The vacuum system is considered qualified only after passing these tests.

#### 3.11.3 Mode Transition Vacuum Procedure

A standard operating procedure (SOP) shall govern the transition from Core to HV mode:
1. Stop mist generation, allow residual droplets to evaporate, and flush the tube with dry N₂ for ≥15 min.  
2. Close the emitter‑end gate valve to protect the ion pump.  
3. Rough‑pump the drift tube from the front while heating the tube to 150 °C; hold for ≥24 h.  
4. Cool to room temperature; open the emitter‑end valve and start the ion pump.  
5. Monitor emitter‑end pressure; HV may be enabled only after the pressure is ≤1 × 10⁻⁵ mbar and has been stable for ≥1 h.

---

### 3.12 Diagnostics Integration

Dedicated diagnostic ports are provided for:  
- Faraday cup, retarding‑field analyser, phosphor screen, pepper‑pot mask.  
- Optical viewport for emission spectroscopy.  
- X‑ray detector (Si‑PIN or CdTe).  
- Neutron detector (stilbene+SiPM) and activation foils (HV mode).  
- Pressure transducers (including the emitter‑end gauge), flow meters, thermocouples.

Ports allow insertion/retraction without breaking vacuum or major disassembly. All vacuum‑related diagnostics are integrated into the central data acquisition system with real‑time logging.

---

### 3.13 Manufacturing and Assembly

Precision components are manufactured to documented tolerances and inspected before assembly. Assembly includes ultrasonic cleaning, vacuum‑compatible handling, torque‑controlled fasteners, electrical continuity and high‑pot testing, leak checking (HV mode), alignment verification, and pressure calibration. The HV emitter assembly is handled, stored, and installed under clean‑room or glovebox conditions to preserve surface integrity.

---

### 3.14 Prototype Cost and Development Strategy

Development proceeds in five gated phases (see §9), now including a dedicated vacuum feasibility gate (Phase 6a).  
- **Phase 1:** Low‑cost materials (Pt‑clad steel, commercial nebulisers) to validate the Bernoulli stage and mechanical fit.  
- **Phase 2:** Glow‑discharge plasma and aerosol transport with the residue‑free working fluid; complete Core Plasma Jet validation.  
- **Phase 3:** Integration of the high‑vacuum system, including the differential pumping hardware, emitter‑end gauge, and bake‑out. Conduct the vacuum recovery acceptance test.  
- **Phase 4:** Only after passing the vacuum gate, install the HV emitter and begin electron beam commissioning.  
- **Phase 5:** Advanced experiments (ion beams, neutrons) following full safety reviews.

A preliminary Bill of Materials with cost ranges is provided in Appendix B. The phased approach limits financial exposure and ensures that no subsystem advances beyond its experimentally validated maturity.

---

## 4. Physics Basis and Regime Transitions

This section defines the governing physical principles underlying the Coherent Particle Beam (CPB) platform. Two fundamentally different operating regimes are supported:

- **Core Plasma Jet Mode:** Low-pressure (30–80 mbar), collisional glow-discharge plasma. Transport is dominated by electron‑neutral and ion‑neutral collisions; the output is a weakly ionised plasma jet, not a ballistic beam.
- **High‑Vacuum Beam Mode (HV‑CPB):** High‑vacuum (<10⁻⁵ mbar at the emitter) electrostatic accelerator operating under conventional charged‑particle beam physics. This mode is **contingent upon a differential vacuum pumping architecture** that ensures the electron/ion source experiences true ballistic conditions; without it, the beam will be heavily scattered and the performance targets are not physically achievable.

The transition between these regimes is determined primarily by gas density, mean free path, and plasma formation, not by electrode geometry alone. Unless otherwise stated, numerical values are design estimates based on published literature and require experimental validation.

---

### 4.1 Transport Regimes and Mean Free Path

The electron (or ion) mean free path λ is given by

\[
\lambda = \frac{1}{n\sigma}
\]

where

- *n* = neutral gas number density  
- *σ* = total collision‑cross section (elastic + inelastic) for the relevant particle energy and gas species.

Gas density follows the ideal gas law

\[
n = \frac{P}{k_B T}
\]

At 300 K:

| Pressure    | Number Density (m⁻³) |
|-------------|-----------------------|
| Atmospheric (1013 mbar) | 2.45 × 10²⁵ |
| 30 mbar     | 7.2 × 10²³ |
| 50 mbar     | 1.2 × 10²⁴ |
| 1 mbar      | 2.4 × 10²² |
| 10⁻³ mbar   | 2.4 × 10¹⁹ |
| 10⁻⁵ mbar   | 2.4 × 10¹⁷ |

Approximate electron mean free paths in **air** (cross‑sections from NIST and LXCat [8,11]):

| Electron Energy | 30 mbar  | 1 mbar   | 10⁻³ mbar | 10⁻⁵ mbar |
|----------------|----------|----------|-----------|-----------|
| 1 keV          | 28 µm    | 0.84 mm  | 8.4 cm    | 8.4 m     |
| 10 keV         | 0.10 mm  | 3 mm     | 30 cm     | 30 m      |
| 100 keV        | 0.28 mm  | 8.4 mm   | 84 cm     | 84 m      |

*In hydrogen or deuterium, cross‑sections are typically a factor 3–5 smaller, increasing λ by the same factor. Nevertheless, even in H₂ at 30 mbar, λ(100 keV) ≈ 1 mm, still far shorter than the 100 mm drift tube.*

**Conclusion:**  
- At 30–80 mbar, every particle undergoes many collisions while traversing the drift tube; transport is **collisional** and the device produces a plasma jet, not a directed beam.  
- To achieve true ballistic transport (λ ≫ tube length), the pressure must be reduced to the molecular‑flow regime, i.e., <10⁻⁵ mbar. This is accomplished by the HV vacuum stage **with differential pumping at the emitter**.

#### 4.1.1 Vacuum Conductance Bottleneck and the Necessity of Differential Pumping

The drift tube is 2 mm ID × 150 mm long. For molecular flow, the tube’s conductance for N₂ is approximately

\[
C \approx 12.1\,\frac{d^3}{L}\; \text{L/s} \quad (d,\,L \text{ in cm})
\]

With \(d = 0.2 \text{ cm}\), \(L = 15 \text{ cm}\),

\[
C \approx 12.1 \times \frac{0.008}{15} \approx 6.5 \times 10^{-3} \; \text{L/s}.
\]

If a 300 L/s turbomolecular pump is connected only to the front end (downstream of the drift tube), the effective pumping speed at the emitter end is

\[
S_{\text{eff}} = \left( \frac{1}{C} + \frac{1}{300} \right)^{-1} \approx C = 6.5 \times 10^{-3} \; \text{L/s}.
\]

Even after a thorough bake‑out, the outgassing from the large internal surface area (~94 cm²) will produce a gas load \(Q\). For \(Q = 5 \times 10^{-9}\) mbar·L/s (optimistic for a tube exposed to water mist), the steady‑state pressure at the emitter would be

\[
P_{\text{emitter}} = \frac{Q}{S_{\text{eff}}} \approx \frac{5 \times 10^{-9}}{6.5 \times 10^{-3}} \approx 7.7 \times 10^{-7} \; \text{mbar},
\]

which is marginally acceptable. However, after exposure to any working fluid mist (even a volatile one) and before an extremely aggressive bake, \(Q\) can be orders of magnitude higher, easily keeping the emitter pressure in the 10⁻³–10⁻² mbar range—far above the ballistic threshold. In that regime, the mean free path is <1 cm, and the “beam” is a high‑voltage glow discharge, not an accelerator.

Therefore, to reliably achieve and maintain a pressure ≤1 × 10⁻⁵ mbar at the emitter after Core‑mode operation, a **dedicated high‑vacuum pump must be placed near the emitter end**, and the emitter must be housed in a small, differentially pumped chamber separated from the main drift tube by a conductance‑limiting aperture (§3.11). This architecture decouples the emitter pressure from the outgassing load of the long tube and is mandatory for ballistic transport.

---

### 4.2 Operating Regime Map

The CPB platform intentionally operates in multiple physical regimes, accessed by varying pressure, voltage, and current. The HV ballistic regime is accessible only after vacuum gate requirements (§2.5) are satisfied.

| Regime                       | Pressure at Emitter       | Dominant Physics              | Expected Behaviour                |
|------------------------------|---------------------------|-------------------------------|-----------------------------------|
| Corona / streamer discharge  | Near atmospheric          | Local gas ionisation, streamers | Surface discharge, transient     |
| Glow discharge               | 30–80 mbar                | Collisional plasma            | Stable plasma column; Core Jet Mode |
| Transitional plasma          | 1–30 mbar                 | Mixed collisional‑ballistic   | Increasing electron range        |
| **Pseudo‑beam (scattering)** | 10⁻³–1 mbar               | Frequent collisions, no true focus | High‑voltage diffuse discharge  |
| Electron beam (ballistic)    | **≤1 × 10⁻⁵ mbar**        | Ballistic charged particles   | Conventional accelerator physics |
| Space‑charge‑limited beam    | Vacuum, high current      | Child‑Langmuir flow           | Beam envelope expansion           |
| Arc discharge                | High current              | Thermal plasma                | Undesired; prevented by current limiting |

Experimental operation shall identify the active regime using plasma diagnostics (discharge voltage‑current characteristic, optical emission, pressure) rather than nominal pressure alone. The "pseudo‑beam" regime is explicitly noted as a failure mode of the HV configuration if differential pumping is not implemented.

---

### 4.3 Gas Breakdown and Paschen Behaviour

Gas breakdown follows Paschen’s Law,

\[
V_b = \frac{B\,p\,d}{\ln(A\,p\,d) - \ln\left[\ln\left(1 + \frac{1}{\gamma}\right)\right]}
\]

where *p* is gas pressure, *d* electrode spacing, *A*, *B* constants depending on gas, and *γ* the secondary electron emission coefficient.

For air, the Paschen minimum occurs near *pd* ≈ 0.76 Torr·cm with a minimum breakdown voltage \(V_{b,\min} \approx 327\) V.

**Critical gap in the CPB:** The highest electric field exists between the toroidal emitter and the inner wall of the drift tube. With a tube inner diameter of 4.00 mm and the emitter outer diameter of 2.50 mm, the radial clearance is **0.75 mm** (§3.2). This gap, combined with the operating pressure, determines the breakdown threshold.

**Example – Core Plasma Jet Mode at 50 mbar:**  
- *p* = 50 mbar = 37.5 Torr  
- *d* = 0.75 mm = 0.075 cm  
- *pd* ≈ 2.8 Torr·cm  

This places the device on the right‑hand branch of the Paschen curve, where the breakdown voltage is several kilovolts. For air, \(V_b\) is estimated to be >3 kV. Therefore, operating at ±10 kV with active current limiting ensures that a controlled glow discharge is sustained without transitioning to an arc. In hydrogen or deuterium, the breakdown voltage is lower; initial operation will map the safe operating area.

**High‑Vacuum Beam Mode:** Once the emitter‑end pressure is reduced to ≤1 × 10⁻⁵ mbar, gas breakdown is no longer the limiting factor. Vacuum breakdown mechanisms—field emission from microscopic protrusions, ceramic flashover, and triple‑junction effects—dominate. These are managed by electrode conditioning, smooth surfaces (Ra ≤0.4 µm), shielding of ceramic‑metal‑vacuum junctions, and the use of a dedicated, clean HV emitter that never sees the working fluid mist.

---

### 4.4 Plasma Parameters (Core Plasma Jet Mode)

Representative parameters for a 50 mbar glow discharge in air (from literature [3,19] and preliminary estimates):

| Quantity             | Typical Value    | Status      |
|----------------------|------------------|-------------|
| Electron density, \(n_e\) | 10¹⁵ – 10¹⁶ m⁻³  | Estimated   |
| Electron temperature, \(T_e\) | 1–3 eV       | Literature  |
| Ion temperature      | ≈ 300 K          | Estimated   |
| Ionisation fraction  | 10⁻⁶ – 10⁻⁴      | Literature  |
| Debye length, \(\lambda_D\)   | 7–20 µm          | Calculated  |
| Plasma frequency, \(f_p\) | 0.3–3 GHz        | Calculated  |

These values define a **weakly ionised, collisional glow plasma**. The Debye length is much smaller than the tube diameter, so the plasma is quasi‑neutral, and electrostatic beam optics are ineffective in this regime.

**Primary diagnostics:** Optical emission spectroscopy (OES) for species identification and electron temperature estimation; current‑voltage (I‑V) characteristics; and, where practical, Langmuir probe measurements.

---

### 4.5 Electron Emission Mechanisms

#### Core Plasma Jet Mode
Electrons are supplied by **secondary emission** from the toroidal cathode (Core emitter, §3.2.1) due to ion bombardment. The discharge is self‑sustaining: ions accelerated across the cathode sheath release electrons, which in turn ionise more gas. The electron energy is determined by the cathode fall voltage (200–600 V in air) and by collisional processes in the negative glow, not by the full applied voltage. The emitter operates in a dirty, aerosol‑laden environment and is designed for robustness, not for pristine field emission.

#### High‑Vacuum Beam Mode
With the gas density reduced by a factor >10⁴, ion‑induced secondary emission cannot sustain a discharge. The primary emission mechanism becomes **Fowler‑Nordheim (FN) field emission** from a dedicated, clean HV emitter (§3.2.2) that is never exposed to the working fluid mist. The emitter is housed in its own differentially pumped chamber and is installed only after UHV conditions are confirmed.

The Fowler‑Nordheim equation is

\[
J = \frac{A \beta^2 E^2}{\phi \, t^2(y)} \exp\!\left(-\frac{B \, v(y) \, \phi^{3/2}}{\beta E}\right)
\]

where  
- *J* = emission current density  
- *β* = field enhancement factor (dimensionless)  
- *E* = macroscopic electric field = *V/d*  
- *φ* = work function (≈2.6 eV for LaB₆)  
- *A*, *B* = FN constants (A = 1.54 × 10⁻⁶ A·eV/V², B = 6.83 × 10⁹ eV⁻³/² V/m)  
- *t(y)*, *v(y)* = elliptic integral corrections (approximated as unity in simplified analyses).

The field enhancement factor *β* depends on the microscopic geometry and surface condition; it will be extracted from experimental FN plots (ln(*I/V²*) vs. 1/*V*). Initial estimates place *β* in the range 50–100 for a properly conditioned tip. The actual emission current will deviate from the ideal FN law if the surface is contaminated; therefore, the HV emitter will be conditioned *in situ* under UHV and its emission stability will be verified before beam operation.

---

### 4.6 Space‑Charge Limited Flow (Child‑Langmuir)

Once electrons enter the vacuum accelerating gap, their current density is ultimately bounded by the Child‑Langmuir law for a planar diode:

\[
J_{CL} = \frac{4\epsilon_0}{9} \sqrt{\frac{2e}{m}} \, \frac{V^{3/2}}{d^2}
\]

For *V* = 100 kV and *d* = 0.75 mm (emitter‑to‑tube gap),  
\(J_{CL} \approx 1.3 \times 10^5\) A/m². Our design target (~10⁴ A/m² for 2 mA) is well below this limit; space‑charge does not restrict the total current. However, perveance effects can still cause beam envelope growth, which is addressed by the beam envelope equation (§4.7) and numerical simulations. All such analyses assume the gap is in true vacuum; if residual gas is present, scattering will dominate over space‑charge forces.

---

### 4.7 Beam Optics (HV Beam Mode)

In HV Beam Mode, the transition from the drift tube (at accelerating potential) to the grounded beam‑line forms an **electrostatic immersion lens**. The optics are designed under the assumption that electrons travel ballistically from a clean emitter in a vacuum of ≤1 × 10⁻⁵ mbar. If the pressure at the emitter is higher, scattering will destroy beam coherence and the optical design is invalid.

**Conservative design targets (initial operation):**

| Parameter             | Design Target       | Status     |
|----------------------|---------------------|------------|
| Beam spot diameter   | ≤500 µm (100 keV, 1 mA) | Predicted  |
| Normalised emittance (εₙ) | ≤50 mm·mrad      | Estimated  |
| Beam brightness (B)  | ≥5 × 10⁵ A/(m²·rad²) | Predicted  |

These values are deliberately conservative for a first‑generation prototype. Higher brightness (εₙ <20 mm·mrad, spot <200 µm) is a stretch goal that will be pursued after the basic beam transport has been validated under ballistic conditions. Chromatic and spherical aberrations will be quantified by ray‑tracing and compared with experiment.

**Optional magnetic correction:** A compact SmCo ring or air‑core solenoid can provide fine focusing and steering. Alignment tolerance <1 mrad.

---

### 4.8 Space‑Charge Neutralisation

When an electron beam passes through residual gas, some ionisation occurs, producing positive ions that can partially neutralise the beam’s space charge. At the design base pressure (≤1 × 10⁻⁵ mbar at the emitter), neutralisation is expected to be minor but could become significant if the drift tube pressure is higher (e.g., 10⁻⁴ mbar). The effect will be characterised experimentally by observing beam profile evolution at different pressures and currents. In the collisional “pseudo‑beam” regime, neutralisation is overwhelmed by scattering, and the concept of a coherent beam envelope is not applicable.

---

### 4.9 Plasma Chemistry (Core Plasma Jet Mode)

The core plasma jet contains a variety of reactive neutral and ionic species formed by electron‑impact dissociation and ion‑molecule reactions. Expected species include:

- **Air plasma:** O, O₂⁺, N₂⁺, NO, NO₂, O₃, OH, electrons, positive and negative ions.  
- **Hydrogen/deuterium plasma:** H (D), H₂⁺ (D₂⁺), H₃⁺ (D₃⁺), electrons.

These species influence electrical conductivity, optical emission, electrode corrosion, and aerosol chemistry. OES will be the primary tool for species identification; residual gas analysis will complement it in HV mode.

---

### 4.10 Dimensionless Parameters

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

### 4.11 Experimental Unknowns

The following quantities are critical for model validation and will be measured during the experimental programme:

| Quantity                                | Importance                        | Measurement Method            |
|-----------------------------------------|-----------------------------------|-------------------------------|
| Bernoulli pressure distribution         | Defines operating regime          | Pressure transducer array     |
| Emitter‑end pressure (HV mode)          | Determines whether transport is ballistic | Emitter‑end vacuum gauge, RGA |
| Plasma density (nₑ)                     | Conductivity & Debye length       | OES, microwave interferometry |
| Electron energy distribution (EEDF)     | Discharge model validation        | Retarding‑field analyser      |
| Droplet charge distribution             | Aerosol transport & Rayleigh stability | Faraday pail / electrometer |
| Beam divergence & emittance             | Beam optics validation            | Phosphor screen + pepper‑pot  |
| Space‑charge neutralisation fraction    | Beam envelope evolution           | Beam profile vs. pressure     |
| Gas composition (Core & HV)             | Plasma chemistry & target poisoning | RGA / OES               |
| Working fluid residue outgassing        | Vacuum recovery feasibility       | RGA during bake‑out, pressure rise |

A dedicated **aerosol‑only test phase** (§3.6) will characterise droplet charge, size, and evaporation before plasma integration. The vacuum gate tests (§2.5) will quantify outgassing and prove the differential pumping concept.

---

### 4.12 Physics Validation Strategy

The CPB platform advances through progressive validation levels:

| Validation Level | Evidence                                                                 |
|------------------|--------------------------------------------------------------------------|
| Analytical       | Governing equations and first‑principles scaling laws                    |
| Numerical        | CFD (COMSOL), electrostatic (SIMION), beam envelope, and Monte Carlo simulations |
| Experimental     | Laboratory measurements with calibrated, traceable instrumentation        |
| Correlated       | Agreement between theory, simulation, and experiment within stated uncertainty |
| Verified         | Independent replication and consistent performance across multiple prototypes |

All values presented in this specification are **engineering design targets**. Final acceptance of any performance claim requires direct experimental verification with documented uncertainty budgets. The physics basis described here provides the framework for designing experiments, interpreting data, and progressively refining the models that underpin the CPB platform. In particular, the transition from Core to HV mode is gated by physics‑based vacuum and emission criteria that must be satisfied before ballistic beam operation can be claimed.

---

## 5. Modes of Operation

The Coherent Particle Beam (CPB) platform supports multiple operating modes spanning collisional plasma physics and conventional charged‑particle beam transport. Each mode has distinct hardware configurations, operating parameters, diagnostics, and intended applications.

**Important:** The high‑vacuum (HV) beam modes (§5.4–§5.6) are **contingent upon successful completion of the vacuum gate requirements** (§2.5). Until the differential pumping architecture is commissioned and the emitter‑end pressure ≤1 × 10⁻⁵ mbar is demonstrated, these modes are design targets only.

Unless otherwise noted, all performance values represent **engineering design targets** requiring experimental validation.

---

### 5.1 Plasma Electron Mode (Core Mode)

**Operating Pressure**  
30–80 mbar (maintained by the Bernoulli vacuum stage)

**Polarity**  
- Core emitter (toroidal glow‑discharge cathode, §3.2.1): Negative  
- Drift tube: Ground reference  
- Collector: Ground or positive bias  

**Operating Voltage**  
−200 V to −10 kV  

**Physical Process**  
A stable glow discharge forms between the toroidal emitter and the drift tube wall.  
Secondary electrons generated in the cathode fall region are transported through the drift tube as part of a weakly ionised, collisional plasma.  
The electron mean free path is much shorter than the tube length; transport is dominated by collisions with the background gas and aerosol droplets.  
The output is a **conductive plasma jet**, not a monoenergetic electron beam.

**Working Fluid**  
The baseline is a volatile electrolyte solution (e.g., 0.1–1 % ammonium acetate in deionised water) that leaves no solid residues after bake‑out. Saline is prohibited in any system intended for later HV operation (§3.6).

**Expected Operating Parameters**

| Parameter              | Design Target     |
| ---------------------- | ----------------- |
| Electron energy (afterglow) | 0.2–2 keV    |
| Plasma current         | 10 µA–2 mA       |
| Operating pressure     | 30–80 mbar        |
| Plasma jet divergence (half‑angle) | <10° (initial, subject to experimental validation) |
| Continuous duty cycle  | 100 % with active cooling |

**Primary Diagnostics**  
- Voltage/current monitoring (I‑V characteristics)  
- Optical emission spectroscopy (OES) for species identification and electron temperature estimation  
- High‑speed imaging of the plasma jet  
- Retarding‑field analyser for electron energy distribution (where feasible)  
- Pressure transducers along the drift tube and collector  
- Thermal monitoring of the emitter and tube

**Representative Applications**  
- Low‑energy X‑ray generation (<5 keV)  
- Plasma RF antenna (conductive plasma column)  
- Surface activation and cleaning  
- Plasma‑assisted chemistry and aerosol charging  
- Soft X‑ray and VUV source for spectroscopy

---

### 5.2 Positive‑Ion Plasma Mode (Core Mode)

**Operating Pressure**  
30–80 mbar  

**Polarity**  
- Core emitter: Positive  
- Collector: Negative  

**Physical Process**  
Positive ions generated in the glow discharge are accelerated toward the collector through the plasma column.  
Transport remains strongly collisional; the system behaves as an ion‑assisted plasma reactor, not an ion accelerator.

**Typical Ion Species**  
N₂⁺, O₂⁺, Ar⁺, H⁺, H₃⁺, D⁺, He⁺ (depending on operating gas)

**Applications**  
- Plasma etching and surface activation  
- Ion‑assisted deposition and sputtering  
- Thin‑film processing  

**Diagnostics**  
- Optical emission spectroscopy  
- Collector current measurement  
- Mass spectrometry (future upgrade)  
- Surface profilometry of treated substrates

---

### 5.3 Plasma RF Antenna Mode (Core Mode)

**Configuration**  
The plasma column generated during Plasma Electron Mode is RF‑modulated through the control grid. The conductive plasma acts as a dynamically reconfigurable antenna.

**Governing Physics**  
Radiation characteristics depend on plasma conductivity, density, column geometry, modulation frequency, and aerosol conductivity. The upper operating frequency is limited by the plasma frequency and electron collision rate.

**Expected Operating Range**  
VLF through UHF (design objective). Microwave operation requires resonant cavity structures and remains experimental.

**Diagnostics**  
- Vector network analyser  
- Near‑field probe  
- Far‑field antenna measurements  
- Optical plasma diagnostics  

**Applications**  
- Reconfigurable antennas  
- Low‑observable communications  
- Plasma RF research

---

### 5.4 Electron Beam Mode (HV Mode)

**Operating Pressure**  
≤1 × 10⁻⁵ mbar at the emitter (differential pumping active)  

**Polarity**  
- Dedicated HV field‑emission cathode (§3.2.2): Negative  
- Drift tube: Ground reference (beam extracted through electrostatic immersion lens)  

**Operating Voltage**  
5–100 kV  

**Physical Process**  
Electrons are extracted from a clean, conditioned field‑emission tip via Fowler–Nordheim tunnelling. They are accelerated through the evacuated drift tube and focused by electrostatic optics with optional magnetic correction. Transport is ballistic because the electron mean free path (≥ 8 m at 10⁻⁵ mbar) greatly exceeds the tube length. This mode **can only be activated after the vacuum gate requirements (§2.5) are satisfied** and the emitter‑end pressure is verified.

**Design Targets**  

| Parameter              | Design Target (Baseline) | Aspirational Stretch Goal |
| ---------------------- | ------------------------ | ------------------------- |
| Electron energy        | 5–100 keV                |                           |
| Beam current           | 10 µA–2 mA               |                           |
| Energy spread (FWHM)   | <5 %                     | <2 %                      |
| Beam spot diameter (at target) | ≤500 µm (100 keV, 1 mA) | ≤200 µm               |
| Beam divergence (half‑angle) | <5°                   | <2°                       |
| Normalised emittance (εₙ) | ≤50 mm·mrad            | ≤20 mm·mrad               |

*Note: The ≤200 µm spot and ≤20 mm·mrad emittance are ambitious goals that will be pursued only after the baseline performance is demonstrated under stable ballistic conditions.*

**Diagnostics**  
- Faraday cup (beam current)  
- Phosphor screen and knife‑edge scan (beam profile)  
- Pepper‑pot or slit‑scan emittance measurement  
- Retarding‑field analyser (energy spread)  
- Beam current monitor (stability)

**Representative Applications**  
- Bremsstrahlung X‑ray generation (up to 100 keV)  
- Electron irradiation and materials research  
- Electron optics experiments  
- Beam diagnostics development

---

### 5.5 Positive‑Ion Beam Mode (HV Mode)

**Operating Pressure**  
≤1 × 10⁻⁵ mbar at the ion source (differential pumping)  

**Ion Sources**  
- Hollow‑cathode insert  
- Electron Cyclotron Resonance (ECR, 2.45 GHz)  
- Future RF plasma source  

**Supported Species**  
H⁺, D⁺, He⁺, Ar⁺  

**Beam Energy**  
10–300 keV  

**Physical Process**  
Positive ions are generated in a dedicated ion source, extracted electrostatically, and accelerated through the evacuated drift tube. Transport is ballistic, and beam focusing is provided by electrostatic lenses. The ion source and extraction optics are independent of the Core plasma hardware; they are installed only after the vacuum gate is passed.

**Diagnostics**  
- Faraday cup  
- Beam‑profile monitor (phosphor screen or wire scanner)  
- Energy analyser (retarding‑field or magnetic spectrometer)  
- Residual gas analyser (for beam purity and target poisoning monitoring)  
- Beam‑current monitor

**Applications**  
- Hydrogen/deuterium implantation  
- Surface modification and ion‑beam analysis  
- Accelerator physics research  
- Fusion target irradiation (pre‑neutron qualification)

---

### 5.6 Neutron Generator Mode (HV Mode)

This operating mode is based on established sealed‑tube neutron generator principles. It is accessible only after the HV vacuum system, ion source, and deuterium handling are fully commissioned and all safety reviews are complete.

**Configuration**  
A focused D⁺ beam impinges on a titanium deuteride (TiD₂) target. The target is actively cooled, and the temperature is limited to ≤250 °C to prevent deuterium loss.

**Primary Reaction**  
\[
\mathrm{D + D \rightarrow ^3He + n + 3.27\ MeV}
\]

**Operating Parameters**

| Parameter      | Design Target (Baseline)                   | Comment                                      |
| -------------- | ------------------------------------------ | -------------------------------------------- |
| Ion energy     | 50–100 keV                                 |                                              |
| Beam current   | up to 0.1 mA initially                     | Higher currents after target qualification   |
| Target         | Titanium deuteride (TiD₂) on OFHC copper   | In‑situ deuterium loading                    |
| Expected yield | ≥1 × 10⁵ n/s at 0.1 mA, 100 keV            | Conservative baseline; 10⁷ n/s is a literature‑based potential at higher currents and optimal loading |
| Neutron energy | 2.45 MeV                                   | Monoenergetic from D‑D reaction              |

Yield depends strongly on target loading, beam purity, beam energy, target temperature, and surface contamination. Actual performance will be determined experimentally.

**Diagnostics**  
- Calibrated neutron detector (stilbene+SiPM with pulse‑shape discrimination)  
- Activation foils (indium, copper) for integrated yield  
- Beam current and target temperature monitors  
- Radiation survey meters (interlocked)

**Shielding**  
At least 30 cm of borated polyethylene + 2 mm lead, validated by MCNP/GEANT4 simulations. Full radiation survey and regulatory approval are required before operation.

---

### 5.7 Advanced Experimental Configurations

The following configurations are exploratory research modes. No performance claims are made. Operation requires rigorous experimental controls, calibrated instrumentation, uncertainty analysis, and independent verification.

**Electron‑Screening Experiments**  
Investigate the influence of high electron density and plasma environments on low‑energy nuclear reaction cross sections. Potential measurements: neutron emission, gamma spectroscopy, helium isotope analysis, charged‑particle spectroscopy.

**Deuterated Aerosol Experiments**  
Investigate interactions between plasma, conductive aerosols, and deuterated materials. Primary diagnostics: high‑resolution mass spectrometry, calorimetry, gas analysis, radiation monitoring.

**Status:** Exploratory only. These experiments lie outside the established engineering objectives and shall not be considered validated operational capabilities.

---

### 5.8 Plasma Chemical Processing Mode (Core Mode)

**Configuration**  
A conductive aerosol carrying dissolved reactants or catalysts passes through the plasma discharge. Electron‑impact ionisation and radical formation drive non‑equilibrium plasma chemistry.

**Representative Reactive Species**  
O, OH, O₃, H, N, NO, electrons, positive ions.

**Potential Applications**  
- Plasma‑assisted catalysis  
- Water treatment and sterilisation  
- Surface functionalisation  
- Waste remediation  
- CO₂ activation and hydrogen production research

**Diagnostics**  
- Optical emission spectroscopy  
- Gas chromatography and mass spectrometry  
- FTIR spectroscopy  
- pH and conductivity monitoring

---

### 5.9 Mode Transition Requirements

Transition between operating modes shall occur only after satisfying predefined system conditions. The table below incorporates the new vacuum gate and differential pumping prerequisites.

| Transition                  | Required Conditions                                                                                                           |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Atmospheric → Core Plasma   | Stable Bernoulli pressure (30–80 mbar), verified gas flow, HV interlocks enabled, working fluid mist operational              |
| Core Plasma → HV Mode       | **Vacuum gate requirements satisfied (§2.5):** Core emitter removed, HV emitter installed, system baked and pumped to ≤1 × 10⁻⁵ mbar at the emitter, FN emission stability verified |
| HV Mode → Ion Beam          | Stable base pressure, ion source conditioned and beam extracted, beam diagnostics operational                                |
| HV Mode → Neutron Generator | Radiation shielding installed and validated, neutron detectors calibrated, safety interlocks and regulatory approvals verified |

No transition shall occur automatically. Each mode change requires confirmation that pressure, electrical, thermal, and safety limits remain within their specified operating envelopes.

---

### 5.10 Operational Validation Levels

Each operating mode shall progress through the following maturity levels before being considered validated.

| Validation Level | Requirement                                                               |
| ---------------- | ------------------------------------------------------------------------- |
| Analytical       | Supported by first‑principles calculations and literature                 |
| Simulated        | Corroborated by numerical modelling (CFD, SIMION, COMSOL, GEANT4, etc.)   |
| Prototype        | Demonstrated under controlled laboratory conditions                       |
| Validated        | Reproducible using calibrated instrumentation with documented uncertainty |
| Verified         | Independently replicated using equivalent hardware and procedures         |

This staged validation framework ensures that operational claims remain proportional to the available theoretical, numerical, and experimental evidence while providing a clear roadmap for progressively maturing the CPB platform. HV modes require the vacuum gate to be passed before advancing beyond the “simulated” level.

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

## 8. Safety Systems

Safety is paramount given the combination of high voltage, ionising radiation (X‑rays, potentially neutrons), flammable gases, reactive plasmas, and conductive aerosols. The safety architecture follows a defence‑in‑depth philosophy: **prevention**, **detection**, **mitigation**, and **administrative controls**. All safety‑critical functions incorporate redundancy and fail‑safe design. Compliance with relevant standards (IEC 60071, IEC 61010, IAEA neutron generator guidelines, and national radiation regulations) is mandatory. A detailed safety case will be documented in CPB‑SAF‑001 before any HV or neutron operation.

---

### 8.1 High‑Voltage Safety

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
- **Differential Pumping High‑Voltage**: The ion pump and its controller operate at several kilovolts; these are enclosed and interlocked in the same manner as the main HV supply. The ion pump’s magnetic field is static and contained; no special magnetic safety measures are required beyond standard labelling.

---

### 8.2 Radiation Safety

#### X‑ray Protection (Core and HV Modes)
- **Core Plasma Jet Mode** produces soft X‑rays (<5 keV). The collector region is shielded by the metal casing (≥2 mm steel equivalent), which is adequate to reduce dose rates below 1 µSv/h at 30 cm.
- **HV Beam Mode** generates bremsstrahlung up to 100 keV. The target chamber is surrounded by at least 2 mm of lead (providing >10⁶ attenuation at 100 keV). Local lead blankets are used around viewports and flanges.
- A thin‑window ionisation chamber (e.g., Ludlum 9‑3) or energy‑compensated survey meter at the operator’s position will trip the beam if dose rate exceeds 0.5 µSv/h (Core) or 1 µSv/h (HV). Audible and visual alarms are integrated.

#### Neutron Protection (HV Beam Mode – D‑D operation)
- The target area is enclosed by at least 30 cm of borated polyethylene (5 % boron by weight) to thermalise and capture 2.45 MeV neutrons, plus 2 mm of lead to absorb capture gamma rays.
- Monte Carlo simulations (MCNP or GEANT4) will be performed to validate the shielding design before first neutron production. The final shielding thickness may be adjusted based on these simulations.
- A neutron rem‑counter (e.g., Ludlum 12‑4) provides real‑time dose rate monitoring. If the dose rate exceeds 2 µSv/h (or a lower limit set by local regulations), the beam is automatically tripped.
- Activation foils (indium, copper) are used for time‑integrated yield verification and to cross‑check active detector calibration.
- Post‑operation, a mandatory cooldown period is observed before accessing the target area. Swipe tests for contamination are performed regularly to monitor tritium accumulation.

#### Personal and Environmental Monitoring
- All personnel working in the controlled area during HV/neutron operation must wear whole‑body and extremity dosimeters (TLD/OSL). Dosimeters are processed monthly.
- Fixed area monitors (neutron and gamma) with local alarm and remote readout are installed. A controlled access zone is established around the device; entry during operation requires authorisation.

#### Regulatory Compliance
- Operation of a neutron generator producing >10⁶ n/s (or any sealed source) may require a license from the national regulatory body (e.g., NRC, CNSC, ONR). The safety case, including shielding calculations and procedures, will be submitted for approval before any neutron‑producing experiments. A qualified Radiation Safety Officer (RSO) will oversee all such work.

---

### 8.3 Chemical, Gas, and Aerosol Safety

#### Flammable and Hazardous Gases
- **Hydrogen / Deuterium**: Gas supply lines are constructed of stainless steel tubing with welded or high‑integrity compression fittings (no polymeric tubing). Each line includes a flame arrestor and an excess‑flow valve.
- Gas detectors for H₂/D₂ are installed in the experimental enclosure and the room, set to alarm at 10 % of the Lower Explosive Limit (LEL) and automatically shut off gas supply at 25 % LEL.
- Forced ventilation provides a minimum of 12 air changes per hour. The system is interlocked such that gas flow is inhibited if ventilation is not confirmed.
- Buffer tanks and closed‑loop recirculation are used to minimise total gas inventory; the maximum stored volume does not exceed the design limit of the ventilation system to dilute any accidental release below the LEL.

#### Mercury (if used)
- Mercury is only used in sealed emitters with cold‑trap recovery. A mercury vapour detector monitors the enclosure; an alarm is triggered at the occupational exposure limit (e.g., 25 µg/m³ TWA). Spill kits and a mercury clean‑up plan are in place.

#### Conductive Aerosol and Plasma By‑products
- The working fluid for combined Core+HV operation is a **volatile electrolyte solution** (e.g., 0.1–1 % ammonium acetate in deionised water). This substance is of low acute toxicity, but its decomposition products in the plasma (ammonia, CO₂, possible traces of HCN) and plasma‑generated ozone (O₃) and nitrogen oxides (NOₓ) require local exhaust ventilation at the collector exit.  
- pH‑neutral mist formulations are preferred to minimise corrosion risk. The mist chamber, drift tube, and collector are regularly flushed with deionised water to remove any residues.  
- All wetted materials are selected for compatibility with the chosen working fluid; a compatibility matrix is maintained in Appendix C.  
- **Saline (NaCl) solutions are strictly prohibited in any system intended for later HV operation**, as they leave non‑volatile, hygroscopic deposits that permanently compromise vacuum and field emission.

#### Bake‑out Safety
- During bake‑out at 150 °C, external surfaces of the drift tube and vacuum chamber can cause burns. The heated sections are clearly marked, insulated where possible, and interlocked such that bake‑out heaters are disabled when access doors are open. Operators must wear thermal protective gloves during bake‑out setup and cool‑down.

#### Fire Suppression
- Only CO₂ or clean‑agent extinguishers are permitted in the experimental area. Water‑based extinguishers are prohibited near high‑voltage equipment. Automatic fire suppression is not installed to avoid accidental discharge; instead, the interlock system shuts down all potential ignition sources (HV, plasma) and isolates gas supplies upon detection of a fire by smoke or heat detectors.

---

### 8.4 Emergency Shutdown and Alarms

- **E‑Stop System**: Red mushroom‑head emergency stop buttons are located at the control rack, near the device, and at each exit from the experimental area. Activation of any E‑stop initiates a hard‑wired safety shutdown (ISO 13849 Cat. 4) that:
  - Immediately disables all HV supplies (main and ion pump).
  - Fires the crowbar discharge circuit.
  - Closes all gas valves and de‑energises compressors.
  - Cuts power to the turbomolecular pump and closes the gate valve (HV mode) to preserve vacuum integrity.
  - Sounds a continuous audible alarm and flashes a strobe light.
- **Layered Alarms**:
  - **Warning (Yellow)** – Minor deviations such as pressure drift, low mist level, or approaching maintenance intervals.
  - **Critical (Red)** – Interlock violation, high radiation, or detection of flammable gas.
  - **Emergency (Audible + Strobe)** – E‑stop activation or fail‑safe trip.
- **Power Failure**: Upon loss of mains power, the system fails to a safe state (all HV off, gas valves closed). Uninterruptible power supplies (UPS) maintain the control system, safety interlocks, and critical monitors for at least 30 minutes to permit orderly shutdown and data preservation.
- **Remote Operation**: For HV and neutron modes, the operator is located outside the controlled area, with full video monitoring and remote E‑stop capability.

---

### 8.5 Administrative and Procedural Controls

- **Training**: All operators must complete a structured safety training programme covering high‑voltage, radiation, chemical, and emergency procedures. Only certified personnel may operate the neutron generator mode. Refresher training is conducted annually.
- **Standard Operating Procedures (SOPs)**: Detailed, step‑by‑step SOPs are provided for every operating mode and maintenance activity, including the mode‑transition purge and bake procedure (§3.11.3) and the HV emitter interchange under dry nitrogen. Checklist‑based mode transitions ensure that all prerequisites (pressure, interlocks, shielding, personnel) are verified before proceeding.
- **Lockout/Tagout (LOTO)**: A formal LOTO programme is in place for maintenance of all hazardous energy sources (HV, pressurised gas, rotating machinery). The HV emitter assembly is treated as a contamination‑sensitive item and is handled only under clean, dry conditions.
- **Audits and Inspections**:
  - Monthly proof‑testing of all safety interlocks and E‑stop circuits.
  - Quarterly radiation surveys and leak checks.
  - Annual independent safety audit of the facility and documentation.
- **Documentation**: A safety case file (CPB‑SAF‑001) will compile the FMEA, shielding calculations, interlock diagrams, training records, SOPs, and regulatory submissions. This file is a controlled document, updated as the system evolves.

---

**Status**: Safety systems are designed to meet or exceed applicable standards for a research prototype. Detailed implementation drawings, interlock logic diagrams, and radiation shielding simulations will be developed during Phases 2–3. Full safety system verification and regulatory approval will be completed prior to any HV or neutron operation. Core‑mode operation can begin once the E‑stop, ventilation, and basic electrical interlocks are commissioned.

---

## 9. Experimental Roadmap and Validation

The CPB platform follows a gated, risk‑reduced development path. Each phase builds on the previous, with explicit quantitative success criteria and formal go/no‑go decisions. Technology Readiness Levels (TRL, per NASA/DoD scale) track subsystem maturity. All phases require safety reviews, documented procedures, and data‑driven decisions. Core Plasma Jet validation receives priority; the High‑Vacuum Beam upgrade is gated by a dedicated vacuum feasibility demonstration (Phase 6a) before any beam commissioning.

---

### 9.1 Technology Readiness Levels (TRL)

| Subsystem                               | TRL | Comment |
|-----------------------------------------|-----|---------|
| Ultrasonic nebuliser / mist generation  | 9   | Commercial off‑the‑shelf components |
| HV power supply (120 kV)                | 9   | Industrial / commercial units available |
| Bernoulli vacuum stage                  | 4   | Bench‑tested flow and pressure mapping; plasma integration pending |
| Aerosol characterisation (stand‑alone)  | 3–4 | Initial droplet charge/size measurements completed; in‑situ validation needed |
| Core plasma generation & stability      | 3–4 | Preliminary glow discharge tests; stability at design pressure not yet demonstrated |
| Core plasma electron extraction         | 3   | Basic Faraday cup measurements in progress |
| Modulation grid & driver                | 5   | Bench‑tested electronics; system integration pending |
| High‑vacuum system (turbo + gauges)     | 6   | Commercial components; integrated pumping tests needed |
| Differential pumping & emitter‑end gauge| 3–4 | Design level; conductance calculations to be verified experimentally |
| HV field‑emission cathode               | 2–3 | Concept and simulation; no UHV conditioning data yet |
| HV ballistic electron beam              | 2   | Design and simulations only; dependent on vacuum gate |
| Beam diagnostics suite                  | 4   | Individual instruments calibrated; full integration pending |
| Neutron generation (D‑D)                | 2   | Design target; no experimental demonstration |
| Multi‑unit coherent operation           | 1–2 | Conceptual only |
| **Overall Core Plasma Jet Module**      | **3–4** | Integrated prototype under construction |
| **Overall HV Beam Module**              | **2**   | Detailed design stage; vacuum gate not yet demonstrated |

**TRL Note:** Progression to TRL 5+ (component validated in relevant environment) requires successful integrated prototype testing under representative conditions. The HV module TRL remains low because the vacuum feasibility gate has not been passed.

---

### 9.2 Experimental Phases with Success Criteria

Progress through phases is strictly gated. Each phase includes a formal review (design review + safety review + data review) before authorisation to proceed. Quantitative success criteria must be met consistently across multiple runs. The HV programme now contains a mandatory vacuum feasibility gate (Phase 6a) before any beam is generated.

| Phase  | Configuration                | Primary Objective                                              | Quantitative Success Criteria                                                                                                      | Duration / Deliverables              |
|--------|------------------------------|----------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| **0**  | Aerosol test cell (no plasma)| Characterise droplet charge, size, evaporation, and stability in electric fields | Droplet size distribution d₅₀ = 2–5 µm, span <1.5; charge distribution measured; Rayleigh limit verified; stable aerosol transport through drift tube without arcing for >30 min | 4 weeks; aerosol characterisation report |
| **1**  | Core (atmospheric → 30–80 mbar) | Glow discharge I‑V characterisation in air                   | Stable discharge at ≥1 mA for >1 h at 5 kV; repeatable I‑V curves with <10 % hysteresis                                         | 4–6 weeks; I‑V datasets, stability logs |
| **2**  | Core                         | Bernoulli pressure mapping & stability with mist              | Achieve 30–80 mbar at drift tube with ±5 mbar stability; entrainment ratio ≥1.5 (no mist), ≥1.0 (with mist)                       | 4 weeks; pressure maps, CFD correlation |
| **3**  | Core                         | Plasma electron extraction & current transport                | Faraday cup current >500 µA sustained; plasma jet optical emission stable for >30 min                                             | 4 weeks; current vs. voltage/power curves |
| **4**  | Core                         | Electron energy distribution & OES species identification     | Retarding‑field analyser confirms 200–600 eV (air) peak with tail to ~2 keV; dominant plasma species identified via OES            | 6 weeks; energy spectra, plasma report |
| **5**  | Core                         | Soft X‑ray generation & chemical effects                      | Detectable X‑rays (1–5 keV) with Si‑PIN detector; dose rate within limits; mist chemistry stability demonstrated                  | 6 weeks; X‑ray spectra, application feasibility |
| **6a** | HV upgrade – vacuum gate     | Differential pumping installation and vacuum recovery test    | All vacuum gate requirements of §2.5 satisfied: emitter‑end pressure ≤1 × 10⁻⁵ mbar after clean bake and after a representative Core run + purge + bake; FN emission stability on the clean HV emitter ≥1 h | 8–10 weeks; vacuum qualification & gate report |
| **6b** | HV – electron beam           | Ballistic electron beam & optics validation                   | Faraday cup current >100 µA at 50 kV; beam spot ≤500 µm; divergence <5° half‑angle; normalised emittance ≤50 mm·mrad              | 8–10 weeks; beam profile, emittance data |
| **7**  | HV – ion beam & neutrons     | Positive‑ion beam & D‑D neutron production                    | Deuterium ion current >50 µA at 100 keV; neutron yield ≥1 × 10⁵ n/s (calibrated detector); target thermal stability; no vacuum degradation | 10–12 weeks; neutron spectra, yield curves, safety validation |
| **8**  | Multi‑unit (future)          | Coherent beam combining & advanced experiments                | Synchronise two+ units with <1 ns jitter; measurable coherent intensity increase; advanced experiments as approved                | 12+ weeks; array performance report |

**Success Criteria Notes:**
- Phase 0 is a prerequisite: no plasma operation before aerosol stability is proven.
- Phase 6a is the **hard vacuum gate**. No HV beam operation (Phase 6b) may commence until all gate items in §2.5 are satisfied and formally reviewed.
- Phase 6b and 7 conservative targets (spot ≤500 µm, εₙ ≤50 mm·mrad, neutron yield ≥1 × 10⁵ n/s) are baselines. Stretch goals (≤200 µm, ≤20 mm·mrad, ≥1 × 10⁶ n/s) will be pursued only after baseline performance is reproducible.
- All phases require verification that safety interlocks, radiation monitors, and ventilation are fully functional.

---

### 9.3 Gating Criteria

Before proceeding to any subsequent phase, the following must be satisfied:

- All safety interlocks, E‑stop circuits, and area monitors are verified and documented.
- Radiation surveys confirm dose rates are within safe limits (≤0.5 µSv/h at operator position for X‑rays; ≤2 µSv/h for neutrons).
- Measured performance agrees with models and simulations within stated uncertainty budgets.
- No unresolved high‑severity FMEA items remain.
- **For the Core‑to‑HV transition, the full vacuum gate requirements (§2.5) must be met**, including the differential pumping performance, emitter‑end pressure after a Core run, working fluid residue test, and HV emitter conditioning stability. A formal go/no‑go review is held, and the decision is documented in CPB‑LOG‑001.

---

### 9.4 Risk Management and Contingencies

**Primary Technical Risks (Updated):**
1. **Bernoulli‑plasma compatibility:** The mist‑loaded flow may not sustain a stable pressure or may cause plasma instability. *Mitigation:* Phase 0 and 2 will fully characterise the flow before plasma integration; a small fore‑pump can augment the Bernoulli stage if necessary.
2. **Aerosol charging and droplet instability:** Conductive aerosols in strong electric fields may undergo Coulomb fission or cause corona. *Mitigation:* Dedicated Phase 0 quantifies safe operating envelopes; in‑line conductivity and charge monitoring.
3. **Differential pumping performance:** The ion pump and conductance‑limiting aperture may not achieve ≤1 × 10⁻⁵ mbar at the emitter after a Core run, despite bake‑out. *Mitigation:* Conservative conductance design; Monte‑Carlo simulations (Molflow+); fallback to a larger ion pump or additional pumping stage; rigorous outgassing characterisation in Phase 6a.
4. **Working fluid residue:** Even the volatile electrolyte may leave trace residues that degrade vacuum or emitter performance. *Mitigation:* Vacuum recovery test (§3.6) is the acceptance gate; alternative fluids can be tested during Phase 0; if residues persist, a dedicated Core‑only drift tube with separate HV accelerator tube is the ultimate contingency.
5. **Emitter interchange contamination:** Swapping the Core emitter for the HV emitter without contaminating the clean UHV surfaces is challenging. *Mitigation:* Detailed SOP for emitter exchange under dry N₂ flow; glovebox installation; RGA verification after pump‑down.
6. **HV emitter lifetime:** LaB₆ field‑emission tips may degrade due to ion bombardment from residual gas or accidental pressure bursts. *Mitigation:* Conservative current limits; in‑situ reconditioning protocol; backup emitter cartridges.
7. **Neutron yield:** Actual yield may be lower than baseline due to incomplete target loading, beam impurity, or target overheating. *Mitigation:* In‑situ deuterium loading and target temperature control (≤250 °C); rotating or rastered beam for larger target area; extended conditioning runs.

**Tracking:** Weekly progress reports, key performance indicators (KPIs) aligned with success criteria, and a live risk register (CPB‑RISK‑001) will be maintained. A contingency budget (≈15 % of hardware cost) is reserved for mitigation actions.

**Budget & Resources:** Phased funding release tied to milestone completion. Collaboration with external laboratories for specialised diagnostics (neutron detector calibration, MCNP simulations) is planned to reduce in‑house cost and improve credibility.

---

### 9.5 Documentation and Knowledge Capture

Each phase produces:
- Raw data archives (stored in CPB‑DATA‑001).
- Analysis notebooks (Python/Jupyter scripts with full uncertainty analysis).
- Updated FMEA and risk register (CPB‑RISK‑001).
- Calibration records (traceable to national standards).
- A lessons‑learned report, feeding into the next phase’s design review.

Supporting documents: CPB‑LOG‑001 (experimental log), CPB‑SIM‑00x (simulation reports).

---

**Overall Status:** The roadmap is structured to achieve a fully characterised Core Plasma Jet Module within 6–9 months of prototype assembly, followed by a dedicated vacuum feasibility phase (6a). Only after passing the vacuum gate will HV beam commissioning (6b) and neutron production (7) proceed, estimated over the subsequent 12–18 months. This phased approach minimises technical and financial risk while systematically building experimental evidence for all claimed performance parameters. All decision points are transparent and based on quantitative data, ensuring that the project remains scientifically credible and resource‑efficient.

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

The Coherent Particle Beam (CPB) device is a compact, modular electro‑fluidic platform built around a self‑pumping Bernoulli vacuum stage. In its **Core Plasma Module** (30–80 mbar), it generates a stable, collisional glow‑discharge plasma jet using a conductive, residue‑free working fluid. This enables practical low‑to‑medium energy applications—soft X‑ray production, plasma antennas, surface treatment, and plasma‑assisted chemistry—all without high vacuum and with the flexibility to tailor the aerosol chemistry.

When upgraded with a **differentially pumped High‑Vacuum (HV) Stage** and a dedicated field‑emission cathode, the same core hardware architecture transitions into a ballistic particle accelerator. This HV module can produce focused electron beams (5–100 keV), positive ion beams (10–300 keV), and neutrons via the D‑D reaction on a deuterated target. The transition is gated by strict vacuum and emitter‑conditioning requirements that must be satisfied before any beam operation, ensuring that every performance claim is underpinned by verified physics.

**Revision 4.0** is a major update that addresses fundamental vacuum‑conductance and contamination issues identified in earlier designs. Key changes include:
- **Differential pumping:** A dedicated ion pump at the emitter end overcomes the extreme conductance bottleneck of the narrow drift tube, making high vacuum at the electron source physically achievable.
- **Separate Core and HV emitter assemblies:** A robust glow‑discharge cathode for the wet, collisional Core mode and a pristine field‑emission tip for HV operation—never the same part.
- **Volatile working fluid:** Ammonium acetate solution replaces saline for any combined Core+HV hardware, leaving no solid residues after bake‑out; saline is prohibited in shared systems.
- **Formal vacuum gate (Phase 6a):** All HV beam operation is contingent on demonstrated emitter‑end pressure ≤ 1 × 10⁻⁵ mbar after a full Core run, purge, and bake, plus verified FN emission stability.
- **Realigned performance targets:** Beam optics, neutron yield, and other HV parameters are presented as conservative baselines with aspirational stretch goals, clearly conditioned on vacuum performance.
- **Updated safety, FMEA, and roadmap:** The experimental programme now includes a dedicated vacuum feasibility gate, revised risk items, and a clear sequence of go/no‑go decisions.

The CPB remains a multi‑modal research platform: a **plasma jet source** in its Core configuration and a **conventional particle accelerator** in its HV configuration, with the same tube geometry serving both roles only after rigorous purification. The design is honest about the physics that separates these two worlds—collisional vs. ballistic—and has been re‑engineered to bridge that gap credibly.

**Key Recommendation:** Rapidly validate the Core Plasma Module (Phases 1–5) to confirm Bernoulli performance, plasma stability, emitter lifetime, and mist compatibility. Simultaneously, build and test the differential pumping and HV emitter subsystems in a parallel bench‑scale effort, culminating in the vacuum gate test (Phase 6a). Only after passing that gate should the project commit to full HV beam commissioning. This approach de‑risks the platform, provides immediate scientific and application value from the Core module, and ensures that the HV upgrade is pursued on a foundation of proven vacuum and emission physics.

The CPB represents a versatile research and technology platform with potential applications ranging from compact X‑ray/neutron sources to plasma processing and advanced beam experiments. Continued iterative prototyping, rigorous diagnostics, and safety‑first operation will determine its ultimate performance and utility.

---
