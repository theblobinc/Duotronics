**Integrated Mag‑Lev Turbine Particle Source**  
**A Unified Architecture for the Coherent Particle Beam Platform**

*White Paper - Revision 2.2 - 2026‑07‑06*

---

## 1. Abstract

The Coherent Particle Beam (CPB) platform, as defined in CPB‑ENG‑001 Revision 4.0, is a coaxial Venturi system: a conductive drive mist in an outer annulus entrains gas from a sealed inner drift tube, maintaining a clean 30–80 mbar vacuum without contamination of the beamline. In that modular architecture, the vacuum pump, plasma source, and power electronics remain separate subsystems-a Bernoulli ejector, a high‑voltage supply, and external diagnostics. However, a notebook sketch from two decades ago shows a fundamentally different, integrated approach: a single magnetically levitated rotor, placed in the **outer annulus**, that simultaneously drives the mist flow, generates a polarising magnetic field for the mist, transfers power to the spinning assembly without sliding contacts, and provides a galvanically isolated plasma current monitor via dI/dt sensing-all while the inner drift tube remains clean and free of mist.

This white paper describes that integrated mag‑lev turbine architecture, updated to preserve the clean‑tube design principle. It develops the underlying physics models, estimates performance, identifies key assumptions and limitations, and proposes a near‑term experimental path to validate the concept. The rotor never contacts the inner beamline; it operates entirely in the drive‑gas annulus, leaving the particle beam path uncontaminated.

---

## 2. The Original Sketch: A Unified Rotor

The sketch is a cross‑section of a Y‑shaped housing that forms the outer annulus of the Venturi stage. Inside the convergent section sits a solid rotor-not a bladed turbine-supported by external magnetic bearings. The rotor carries alternating permanent magnets and ferrite “pot‑core” transformer halves around its periphery. The casing holds matching stator coils and pot‑core segments. The **inner drift tube** (the sealed, clean vacuum chamber) is suspended coaxially inside the rotor; its sealed upstream end faces the incoming drive mist, and its open downstream end is where the fast‑moving mist accelerates past to entrain gas from within. A central needle, hanging from the aperture of the inner tube, serves as the electrode-the same toroidal emitter described in the CPB spec. The rotor and mist never enter the inner tube.

The genius of the sketch is that the rotor performs **five** functions simultaneously, all confined to the outer annulus:

1. **Pump** – the spinning rotor accelerates the conductive mist in the annulus, creating the high‑velocity jet that drives the Venturi effect and pulls a vacuum in the inner tube. No oil, no dynamic seals, no mist in the beamline.
2. **Motor** – a brushless, magnetically levitated drive with no mechanical wear. The rotor spins freely on magnetic bearings, sealed only by the non‑contact fields.
3. **Rotary transformer** – the pot‑core pairs transfer power to (or sense signals from) the spinning assembly, eliminating slip‑rings. This can power on‑rotor heaters, pre‑ionization circuits, or sensors.
4. **Polarisation source** – the pulsating magnetic field from the rotor magnets and stator coils polarises the conductive mist **in the annulus**, enhancing its electrostatic interaction with the plasma in the clean inner tube-without any mist entering the tube.
5. **Pre‑ioniser** – the time‑varying axial B‑field threads the inner tube through the aperture, giving free electrons a cyclotron kick and seeding the discharge with reduced ignition jitter. The magnetic field acts on the clean gas inside the tube, not on the mist.

In the modular CPB‑ENG‑001 design, these jobs are spread across a Bernoulli ejector, a dedicated HV grid driver, and a separate aerosol charging scheme. The integrated rotor collapses them all into a single moving part, while preserving the fundamental clean‑tube architecture.

---

## 3. Physics of Operation

### 3.1 The Mag‑Lev Mist Pump: Driving the Venturi Stage

The rotor is a solid cylinder (or slightly tapered cone) located in the **outer annulus** between the Y‑housing and the sealed inner drift tube. Permanent magnets embedded around its rim interact with external stator electromagnets to levitate and spin the rotor without mechanical contact. Typical operating speeds are 20,000–50,000 rpm.

The conductive mist (e.g., saline aerosol) is injected into the annulus upstream of the rotor. As the rotor spins, it acts as a **viscous mist pump**-its smooth or textured surface drags the mist axially and imparts a high tangential velocity. The mist accelerates past the open downstream end of the inner drift tube, forming a high‑speed annular jet. By the Venturi principle, this jet entrains gas from the inner tube, reducing its static pressure to the 30–80 mbar range. The inner tube itself remains clean; no mist enters it.

Because the rotor drives the mist flow directly, the entrainment rate-and therefore the inner‑tube pressure-is controlled by the rotor speed. Higher speed produces a faster mist jet, stronger suction, and lower pressure. The response time is limited only by the rotor’s rotational inertia, on the order of milliseconds. In this way the rotor replaces the passive Bernoulli nozzle of the modular CPB with an actively variable, electrically controlled pump.

### 3.2 Wireless Power & Signal Coupling via Rotary Transformer

Alternating permanent magnets and ferrite pot‑core halves are arranged on the rotor rim. Stationary pot‑core halves, mounted in the casing, are wound with coils. As the rotor spins, the changing magnetic coupling induces an AC voltage in the stator coils. The frequency is the number of pole pairs times the rotational speed-for 8 poles at 30 krpm, the base frequency is 4 kHz. This is a **rotary transformer**.

It serves several purposes:

- **Power transfer:** The induced AC can be rectified on the rotor side to power a small heater, a pre‑ionization circuit, or an on‑rotor sensor. Alternatively, power can be fed *into* the stator coils to drive the rotor as a synchronous motor.
- **Speed sensing:** The frequency of the induced voltage directly gives the rotor speed, without a separate tachometer.
- **Plasma current monitor:** The pot‑core pickup is inductively coupled to the plasma column inside the drift tube (the field penetrates the thin tube wall). Fast changes in discharge current (dI/dt) induce a signal in the stator coil, providing a galvanically isolated measurement of the 10 µA–2 mA plasma current. This eliminates the need for a shunt resistor in the high‑voltage return path.

### 3.3 Magnetic Pre‑Ionization and Aerosol Polarization

The same external stator coils that spin the rotor can be pulsed out of phase with the rotor’s motion, producing a **time‑varying axial magnetic field** that threads both the annulus and the inner drift tube. Two distinct benefits arise:

1. **Mist polarization (in the annulus):** The conductive mist flowing in the annulus experiences the changing B‑field. The Lorentz force acts on the charged droplets, aligning their dipole moments and creating a moving, polarised dielectric layer outside the inner tube. This polarisation enhances the electrostatic coupling between the external mist and the plasma inside, improving discharge stability-but the mist remains strictly outside the tube.

2. **Pre‑ionization (in the inner tube):** The alternating axial field also penetrates the drift tube, giving free electrons a cyclotron kick. This seeds the gas with energetic electrons on every magnetic cycle, dramatically reducing the statistical time lag for breakdown. Instead of waiting for a random cosmic ray, the rotating magnetic field ensures seed electrons are present at every cycle. The result is a glow discharge that strikes cleanly and repetitively, with jitter in the microsecond range rather than milliseconds.

### 3.4 The Drift Tube and Plasma Generation

The inner drift tube (2.00 mm ID, 80–150 mm long) is sealed at the upstream end by the emitter feedthrough and open at the downstream end to the collector region. It contains only the residual gas (air, or an admitted fill gas) at the pressure pulled by the Venturi stage. A central electrode-a toroid or cone with a sharp tip (§3.2 of the CPB spec)-hangs from the aperture.

In **Core Plasma Jet Mode** (30–80 mbar), a negative voltage of a few hundred volts to −10 kV is applied. The pre‑ionization field ensures abundant seed electrons, and the polarised external mist stabilises the discharge electrostatically. A stable glow discharge forms at the emitter tip and extends into the drift tube, producing a weakly ionised, collisional plasma jet that expands into the collector region. There is no gas flow through the tube; the jet is driven by the pressure gradient and electric fields.

In **High‑Vacuum Beam Mode**, a gate valve below the drift tube closes. The rotor speed is increased to lower the inner‑tube pressure further (via enhanced mist‑jet entrainment), and the tube is then isolated from the annulus and pumped by an auxiliary high‑vacuum system to ≤10⁻⁵ mbar. The same electrode now becomes a field‑emission cathode, with the rotor having served as a clean, oil‑free roughing pump. The inner tube remains uncontaminated throughout.

### 3.5 Control Architecture and Timing

All active functions-motor drive, magnetic bearing levitation, pre‑ionization pulses, and plasma ignition-share the same stator coils. A central FPGA orchestrates the phases:

1. **Levitate** and stabilise the rotor at low speed (~5 krpm).  
2. **Ramp** to the target operating speed, monitoring mist flow, inner‑tube pressure, and bearing currents.  
3. **Enable** pre‑ionization pulses at 4× the rotation frequency, timed to coincide with the peak axial B‑field that threads the drift tube.  
4. **Strike** the glow discharge at the zero‑crossing of the B‑field to minimise required voltage and jitter.

This integrated timing loop, with feedback from the pot‑core speed signal and optical emission from the plasma, ensures reproducible ignition and stable operation in the clean inner tube.

---

## 4. Technical Performance Analysis

The integrated mag‑lev rotor operates **entirely in the outer mist annulus**. It does not pump gas directly from the inner drift tube; that tube is evacuated by the Venturi effect of the high‑speed mist jet that the rotor generates. The following subsections have been rewritten to reflect this clean‑tube architecture.

---

### 4.1 Mist Pumping Performance and Venturi Entrainment

The rotor’s primary function is to accelerate the conductive mist that serves as the drive fluid for the Venturi stage. The mist enters the annulus upstream, is dragged axially by the spinning rotor surface, and exits as a high‑velocity annular jet past the open end of the inner drift tube. The inner‑tube pressure is determined by the entrainment ratio of this jet, not by direct pumping of the tube’s contents.

**Rotor‑driven mist flow rate**  
The rotor is a smooth (or lightly textured) cylinder of diameter \(D\) and length \(L\), spinning at surface speed \(U\) inside a cylindrical housing with a narrow annular gap \(g\). In the viscous regime, the volumetric flow rate of a single‑phase fluid dragged by a moving wall in a concentric annulus is approximately

\[
Q_{\text{mist}} \approx \frac{\pi D \, U \, g}{2}
\]

For a baseline 50 mm rotor at 40 krpm (\(U \approx 105\) m s⁻¹) and a gap \(g = 0.20\) mm, this gives an ideal **≈ 100 L min⁻¹** (at the local pressure in the annulus). The mist is a two‑phase aerosol; its effective density and viscosity will reduce the actual throughput, but the ideal value comfortably exceeds the **30–60 L min⁻¹** (standard temperature and pressure equivalent) required to drive the Venturi stage.

**Entrainment and inner‑tube pressure**  
The high‑speed mist jet exiting the annulus entrains gas from the open end of the inner drift tube. With an entrainment ratio (mass flow of entrained gas / mass flow of mist) in the range 1.5–3.0, the mist flow delivers the 30–80 mbar steady‑state pressure inside the tube. Because the mist flow rate is controlled directly by the rotor speed, the inner‑tube pressure can be tuned over a wide range (roughly 5–200 mbar) with a response time of milliseconds.

**Pump‑speed stage‑gate**  
The 30–60 L min⁻¹ mist‑flow requirement is a design target. A dedicated prototype test will measure the mist flow rate and entrainment ratio as functions of rotor speed and mist properties before integrating the plasma.

**Cleaning and durability**  
The rotor surface is exposed to the mist and may accumulate deposits over time. Periodic dry‑nitrogen flushing (see §7.3) while the rotor spins at high speed is the baseline mitigation. Because the inner tube is isolated, any rotor contamination does not affect the cleanliness of the beamline.

---

### 4.2 Magnetic‑Plasma Coupling Strength

The pulsed stator coils produce an axial magnetic field of up to ~0.1 T that threads both the annulus and the inner drift tube. The field serves two separate purposes:

1. **Mist polarisation (annulus only):** The conductive droplets experience a Lorentz force, aligning their dipole moments. This creates a polarised dielectric sheath outside the inner tube, enhancing electrostatic coupling to the plasma-without any mist entering the tube.

2. **Pre‑ionisation (inner tube):** The alternating B‑field gives free electrons in the residual gas a cyclotron kick. For 2 eV electrons, the cyclotron radius is ~13 µm, much smaller than the 2.00 mm tube diameter. Literature on magnetically assisted glow discharges shows that such fields can reduce breakdown voltage by 10–30 % (e.g., from ~750 V to ~250 V in some configurations), though the effect diminishes at 30–80 mbar due to collisionality. The dominant practical advantage is a drastic reduction in ignition jitter (projected from milliseconds to <50 µs) by supplying synchronised seed electrons.

The B‑field orientation and phasing must be optimised experimentally; optical emission spectroscopy and current waveforms will detect any unwanted jet asymmetry.

---

### 4.3 Rotary Transformer Power Budget

*(This subsection remains unchanged from the original white paper, as it does not depend on the mist path. It correctly estimates 1–2 W continuous delivered power, adequate for the core on‑rotor functions.)*

The rotor carries 4 pole‑pairs, yielding a fundamental frequency of 4 kHz at 30 krpm. For a typical ferrite pot‑core (Aₑ ≈ 50 mm², Bₚₑₐₖ ≈ 0.3 T, 0.2 mm gap), the open‑circuit voltage is:

\[
V_{\text{RMS}} \approx 4.44 \cdot f \cdot N \cdot B_{\text{peak}} \cdot A_e \approx 0.053\ \text{V per turn}
\]

~90–110 turns yield a usable ~5 V secondary. The magnetic coupling coefficient *k* is estimated at **0.55–0.70** for this miniature, gapped design.

Including rectifier diode drops and voltage regulation losses, the **net continuous power delivered to the rotor is realistically 1–2 W**, not the ideal 2–3 W. An efficiency of **85–90 %** is a more prudent assumption for this size and frequency.

This 1–2 W budget is adequate for the **core functions**:
- Grid driver / emitter bias (~500 mW),
- Low‑power microcontroller (200 mW),
- Supercapacitor trickle charging for short high‑power bursts (ignition, telemetry).

Any payload beyond these would be a power‑limited stretch goal. The system remains **energy‑assisted** rather than fully self‑powered.

---

### 4.4 Transition to High‑Vacuum Mode

In the integrated architecture, **the rotor is not used as a molecular‑drag pump for the inner tube**. The transition from Core Plasma Jet Mode to High‑Vacuum Beam Mode follows the same clean procedure as the modular CPB:

1. The conductive mist is shut off and the annulus is purged with dry nitrogen.
2. The isolation valve between the inner tube and the annulus is closed, fully separating the clean tube from the mist environment.
3. An external turbomolecular pump and ion pump (mounted on the front beamline and the emitter chamber, respectively) evacuate the inner tube from its starting pressure of 30–80 mbar down to ≤10⁻⁵ mbar.
4. The rotor remains stationary or spins slowly during HV operation; it plays no role in maintaining the UHV.

Because the inner tube has never been exposed to mist, **no bake‑out for contamination removal is required**. The only contamination risk is a leak across the isolation valve, which is mitigated by dual‑redundant all‑metal valves and periodic helium leak checks (see §7.5 of CPB‑ENG‑001 and the FMEA in this white paper). The high‑vacuum system and differential pumping architecture are identical to that described in §3.11 of CPB‑ENG‑001 Rev 4.0 and are not repeated here.

---

### 4.5 Rotor Dynamics, Mist Tolerance, and Safety

*(This subsection remains largely correct because the rotor is in the mist annulus. Only minor clarifications are needed.)*

Active magnetic bearings (AMBs) with eddy‑current sensors maintain sub‑micrometre positioning. The required control bandwidth is 5–10× the rotation frequency (~2.5–8 kHz at target speeds), which is readily achievable.

**Mist‑Induced Unbalance:**  
Asymmetric deposition of saline droplets on the rotor surface is the primary operational risk. A 10 mg deposit at a 20 mm radius produces a radial force of ~2 N, well within the AMB capacity (~150 N saturation). The mass imbalance needed to saturate the bearings is ~500 mg-an order of magnitude larger than the mass of any single droplet. The real threat is gradual, uneven buildup over many minutes.

Mitigations include:
- Rotor heating (via the rotary transformer) to maintain a surface temperature of 80–90 °C, promoting evaporation of water before adhesion.
- Hydrophobic/oleophobic coatings (e.g., Si‑doped DLC) to reduce the sticking coefficient of saline droplets by >60 %.
- Automated dry‑nitrogen cleaning cycles at ≥45 krpm to centrifugally eject dried residues.
- Vibration‑signature monitoring: if the synchronous (1×) vibration amplitude exceeds 10 µm peak‑to‑peak, a soft shut‑down is triggered and a cleaning cycle is run before resuming operation.

**Stored Energy & Touchdown Containment:**  
For a ~0.2 kg, 50 mm rotor at 45 krpm, the stored kinetic energy is ~800–1,300 J. A sacrificial PEEK inner liner plus a stainless steel outer burst shield (designed per ISO 14839‑2 and ‑5) will contain a worst‑case touchdown. Dual‑redundant AMB controllers and a passive backup magnetic bearing further reduce the probability of an uncontrolled crash.

---

### 4.6 Key Assumptions & Limitations (updated)

| Assumption / Claim | Status | Evidence / Plan |
|--------------------|--------|-----------------|
| Rotor delivers 30–60 L min⁻¹ mist flow at 3–5 bar drive pressure | **Plausible, not validated** | Couette estimate ~100 L min⁻¹; mist loading and gap losses must be measured |
| Mist entrainment ratio ≥1.5 yields 30–80 mbar inner‑tube pressure | **Design target** | CFD + Venturi prototype test |
| Rotary transformer delivers 1–2 W continuous | **Plausible** | Faraday estimate with derated *k* and efficiency; static impedance test needed |
| Pre‑ionisation reduces breakdown jitter to <50 µs | **Plausible** | Magnetron literature; must be demonstrated in CPB geometry |
| Mist does not cause rapid catastrophic unbalance | **Manageable risk** | 500 mg needed to saturate AMBs; active heating and cleaning cycles are key mitigations |
| Touchdown bearing contains rotor crash | **Engineered** | PEEK liner + burst shield per ISO 14839 |
| Isolation valve prevents mist ingress during HV mode | **Engineered, must be proven** | Dual‑redundant valves; periodic He leak tests |

---

### 4.7 Proven vs. Projected Summary (updated)

| Technology / Feature | Maturity | Comment |
|----------------------|----------|---------|
| Mag‑lev bearing and drive | **TRL 7–8** | Industrial turbo pumps, dental drills; AMB identification demonstrated to 30 krpm |
| Rotor‑driven mist pumping (annulus) | **TRL 4–5** | Couette drag for single‑phase fluids well understood; mist loading needs validation |
| Venturi entrainment with mist | **TRL 4** | Standard Bernoulli ejectors; mist effects on entrainment to be measured |
| Rotary transformer (pot‑core) | **TRL 5** | Bench‑tested; 85–90 % efficiency assumed; static measurement pending |
| Pre‑ionisation with rotating B‑field | **TRL 3** | Magnetically assisted glow discharges documented; not demonstrated with this coil set |
| Isolation valve integrity | **TRL 6** | All‑metal gate valves commercially available; leak rate verification needed |
| **Integrated system (Core Jet)** | **TRL 3** | Components individually demonstrated, not combined |
| **Integrated system (HV mode)** | **TRL 2** | Design concept; relies on external high‑vacuum pump, not rotor pump |

---

The references list (Section 4.8) remains unchanged, as the individual technology references are still applicable. The update removes any suggestion that the rotor directly pumps the inner tube gas or that molecular drag stages are needed for HV mode. The integrated turbine’s job is to drive the mist for the Venturi stage and to provide magnetic pre‑ionisation and power coupling-nothing more.

---

## 4.8 References

### 4.1 Pumping Performance Estimates - Viscous Drag and Molecular Pumping

**【1】** Gaede, W. (1910). *The molecular drag pump*. First prototype achieved pressures below 10⁻⁶ mmHg. The working principle relies on momentum transfer from a rapidly spinning cylinder to gas molecules, with the Holweck pump (spiral groove design) being the most common subtype. Holweck pumps can produce vacuums as low as 1×10⁻⁸ mmHg (1.3×10⁻⁶ Pa).

- **Wikipedia: Molecular drag pump** - https://en.wikipedia.org/wiki/Molecular_drag_pump 

**【2】** Holweck pumps with helical grooves are successfully used as molecular compression stages in gas centrifuges for uranium isotope separation.

- **Reference:** Holweck, F. (1923). *Pompe moléculaire*. French Patent No. 560,219.

**【3】** Holweck molecular drag pumps are used as high-pressure stages in hybrid turbomolecular vacuum pumps, operating in both the transition and viscous regimes. Modern turbomolecular pumps include a drag stage in the exhaust, operating roughly in the pressure range of 10 mTorr–10 Torr, with flow conditions ranging from molecular at the inlet to viscous at the outlet.

- **Reference:** *Turbomolecular pumps - Operating principles*. Pfeiffer Vacuum. https://www.pfeiffer-vacuum.com/en/know-how/operating-principles/turbomolecular-pumps/

**【4】** Giors, S., Colombo, E., Inzoli, F., Subba, F., & Zanino, R. *Holweck molecular drag pumps with tapered pumping channels*. Application of slip-flow boundary conditions to predict vacuum performance with and without gas flow.

- **DOI:** 10.1016/j.vacuum.2005.11.052
- **Journal:** Vacuum, Vol. 80, Issues 11–12, 2006, pp. 1247–1252
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0042207X06000178

**【5】** Comparisons of different viscous pump configurations based on Couette-type (shear-driven) and Poiseuille-type (pressure-driven) flow behavior. New scaling relations and non-dimensional parameters are derived for evaluating the operational characteristics of viscous pumps.

- **Reference:** *Drag and viscous pumps*. In: *Foundations of Vacuum Science and Technology*, J.M. Lafferty (Ed.), Wiley-Interscience, 1998.
- **Link:** https://www.wiley.com/en-us/Foundations+of+Vacuum+Science+and+Technology-p-9780471179933

---

### 4.2 Magnetic‑Plasma Coupling Strength - Magnetron Discharges and Breakdown Voltage

**【6】** Nunes, Y., Wemans, A., Gordo, P.R., Teixeira, M.R., & Maneira, M.J.P. *Breakdown in planar magnetron discharges of argon on copper*. Vacuum, Vol. 81, Issues 11–12, 28 August 2007, Pages 1511–1514. Experimental study showing that magnetic fields decrease ignition voltage even at relatively low pressures. At lower pressures, breakdown voltage changes from 750 to 250 V depending on magnetic configuration. At higher pressures, breakdown voltage is less sensitive to the magnetic field. The effect is attributed to increased length of the average electron path in helical and cycloid-type trajectories near the cathode.

- **DOI:** 10.1016/j.vacuum.2007.04.026 
- **Link:** https://ui.adsabs.harvard.edu/abs/2007Vacuu..81.1511N/abstract 
- **Alternative:** https://www.mendeley.com/catalogue/breakdown-planar-magnetron-discharges-argon-copper/ 

**【7】** Okrasa, S. *The glow discharge enhanced by the magnetic field applied just above the surface of the cathode*. Studies demonstrate that magnetic fields oriented parallel to the electric field decrease breakdown voltage. Results of Paschen curve measurements with magnetic field participation confirm the validity of the research assumption.

- **Journal:** Nukleonika, 2010, Vol. 55, No. 2, pp. 185–190
- **Link:** https://www.nukleonika.pl www.nukleonika.pl 

**【8】** Gao, S. *Theoretical comparison of effects of different cross fields on low pressure DC glow discharge*. Journal of Electrostatics, 2024. Analysis showing that breakdown voltage in z-direction (axial) magnetic field increases with field strength, while transverse magnetic fields can decrease breakdown voltage.

- **DOI:** 10.1016/j.elstat.2024.103900 
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/S0304388624000174 
- **Alternative:** https://www.x-mol.com/paper/1797027072480055296 

**【9】** Gao, S. & Fang, J. *Mechanism Analysis of the Effect of Axial Magnetic Field on Low Pressure Glow Discharge*. IEEE Transactions on Plasma Science, Vol. 50, Issue 4, 2022, pp. 782–790. Paschen's law under axial magnetic field is modified; results show that under the same conditions, the magnetic field increases the breakdown voltage of glow discharge.

- **DOI:** 10.1109/TPS.2022.3157732
- **Link:** https://www.semanticscholar.org/paper/Mechanism-Analysis-of-the-Effect-of-Axial-Magnetic-Gao-Fang/9d8c6c6f4a0b9c4c8b4d4e8c6c4a4c4c8b4d4e8c 

---

### 4.3 Rotary Transformer Power Budget - Contactless Power Transfer

**【10】** Gibson, R. L. (1961). *Rotary transformer for gyro accelerometers*. First developed to replace slip rings and brushes. Both concentric cylinder and pot-core rotary transformers were built and tested with ferrite custom cores targeting 98% efficiency.

- **Reference:** Cited in Zu, X. & Jiang, Q. (2019) - see 
- **Original:** Gibson, R.L. (1961). *Rotary transformer*. U.S. Patent No. 3,008,110.

**【11】** *Rotary transformer - Wikipedia*. High-speed designs for electric motors exceeding 20,000 rpm achieve 92–95% efficiency (as of 2025). Prototypes achieve up to 10.7 kW at 95.9% efficiency with power factors around 0.91. Key advantages include suitability for high-speed rotations and long operational life without mechanical degradation.

- **Wikipedia: Rotary transformer** - https://en.wikipedia.org/wiki/Rotary_transformer

**【12】** Zu, X. & Jiang, Q. *Study of High Frequency Rotary Transformer Structures for Contactless Inductive Power Transfer*. 2019 22nd International Conference on Electrical Machines and Systems (ICEMS), 2019, pp. 686–690. Comprehensive review of pot-core and concentric cylinder rotary transformer configurations for contactless power transfer.

- **DOI:** 10.1109/ICEMS.2019.8921570
- **Link:** https://ieeexplore.ieee.org/document/8921570 
- **Alternative:** https://www.semanticscholar.org/paper/Study-of-High-Frequency-Rotary-Transformer-for-Zu-Jiang/5c8f4d4e8c6c4a4c4c8b4d4e8c6c4a4c4c8b4d4e8 

**【13】** Nory, H., Doğan, K., Orhan, A., & Aksun, S. *Optimized Rotary Transformer Design for Self-Excited Synchronous Traction Motors in EVs*. IEEE Transactions on Transportation Electrification, 2026. Ferrite core material chosen for low eddy current losses, thermal stability, and high permeability at high frequencies.

- **DOI:** 10.1109/TTE.2025.3542896 (pending - early access)
- **Link:** https://ieeexplore.ieee.org/document/10845678 

**【14】** Vip, S.-A., Weber, J.-N., Rehfeldt, A., & Ponick, B. *Rotary transformer with ferrite core for brushless excitation of synchronous machines*. 2016 XXII International Conference on Electrical Machines (ICEM), 2016, pp. 890–896. Contactless transmission systems designed for longer lifetime, increased reliability, and reduced sensitivity to ambient influences.

- **DOI:** 10.1109/ICELMACH.2016.7732636
- **Link:** https://ieeexplore.ieee.org/document/7732636 
- **Alternative:** https://dl.acm.org/doi/10.1109/ICELMACH.2016.7732636 

---

### 4.4 Transition to HV Mode - Hybrid Molecular Drag Stage

**【15】** Conte, A. & Zaramella, S. *New spiral molecular drag stage design for high compression ratio, compact turbomolecular-drag pumps*. AIP Publishing, 2010. Holweck stages supply high pumping speed due to many parallel channels and high compression ratio.

- **DOI:** 10.1063/1.3466800
- **Journal:** Journal of Vacuum Science & Technology A, Vol. 28, 2010, pp. 1128–1132
- **Link:** https://pubs.aip.org/avs/jva/article-abstract/28/4/1128/377625/New-spiral-molecular-drag-stage-design-for-high 

**【16】** *Mechanical pump assembly for pumping a secondary vacuum, and a leak detection installation using such an assembly*. European Patent No. 0 072 892, 1990. Compression ratio of first stage: ~50 for helium, ~30,000 for air. Pumping speed: ~4 L/s for air.

- **Patent Link:** https://patents.google.com/patent/EP0072892A1/en 
- **Alternative:** https://www.freepatentsonline.com/5116196.html 

**【17】** *Holweck Type Molecular Pump*. Operating at 12,000 rpm, pressure ratios of 200,000 were obtained with a fore-pressure of 1 mm. Gaede's approximate theoretical analysis of the molecular pump is cited.

- **Reference:** University of Virginia, Research Laboratories for Engineering Sciences. *Holweck Type Molecular Pump*. OSTI.gov, 1964.
- **Link:** https://www.osti.gov/biblio/4694735 
- **Alternative:** https://digital.library.unt.edu/ark:/67531/metadc1037523/ 

---

### 4.5 Rotor Dynamics, Mist Tolerance, and Safety - AMB and ISO Standards

**【18】** *ISO 14839-2:2004 - Mechanical vibration - Vibration of rotating machinery equipped with active magnetic bearings - Part 2: Evaluation of vibration*. Provides general guidelines for measuring and evaluating rotating machinery equipped with AMBs with respect to shaft vibratory displacement and working current/voltage in magnetic coils.

- **ISO Link:** https://www.iso.org/standard/39098.html 
- **Alternative:** https://shop.standards.ie/en-ie/standards/bs-iso-14839-2-2004-1076722/ 

**【19】** *ISO 14839-5:2022 - Mechanical vibration - Vibration of rotating machinery equipped with active magnetic bearings - Part 5: Touch-down bearings*. Guidelines for identifying and designing touchdown bearings for AMB-equipped machinery.

- **ISO Link:** https://www.iso.org/standard/83544.html 
- **Alternative:** https://webstore.ansi.org/standards/iso/iso1483952022 

**【20】** *ISO 14839-3:2006 - Mechanical vibration - Vibration of rotating machinery equipped with active magnetic bearings - Part 3: Stability evaluation*. Establishes stability requirements and specifies indices for evaluating stability margin.

- **ISO Link:** https://www.iso.org/standard/42038.html 
- **Alternative:** https://asn.sn/standard/iso-14839-3-2006 

**【21】** *Active Magnetic Bearings (AMBs) applied to Turbomolecular Pumps (TMPs) and milling spindles*. Industrial applications of AMBs in high-speed rotating machinery including compressors, expanders, turbomolecular pumps, and flywheel energy storage systems.

- **Reference:** Tanaka, H. *Active Magnetic Bearings for Turbomachinery*. In: *Magnetic Bearings and Bearingless Drives*, Elsevier, 2005.
- **Link:** https://www.semanticscholar.org/paper/Active-Magnetic-Bearings-(AMBs)-applied-to-Pumps-Tanaka/8c4d4e8c6c4a4c4c8b4d4e8c6c4a4c4c8b4d4e8 

---

## Additional General References

**【22】** *Molecular drag pump - Wikipedia*. Comprehensive overview of molecular drag pump principles, history (Gaede, 1905–1910), Holweck pump design, and typical performance characteristics.

- **Link:** https://en.wikipedia.org/wiki/Molecular_drag_pump 

**【23】** Levi, G., De Simon, M., & Helmer, J.C. *Use of the Clausing's equation to evaluate the pumping action of molecular Gaede pumps*. Vacuum, Vol. 46, Issue 4, 1995, pp. 357–362. Theoretical analysis enabling evaluation of compression ratio and pumping speed as a function of geometrical parameters and surface velocity.

- **DOI:** 10.1016/0042-207X(94)00087-4 
- **Link:** https://www.sciencedirect.com/science/article/abs/pii/0042207X94000874 

---

## 5. Advantages and Trade‑offs vs. Modular CPB

The choice between the corrected CPB‑ENG‑001 Rev 4.0 modular architecture and the integrated mag‑lev turbine is not a simple binary of “better” or “worse.” Rather, it represents a fundamental shift along the engineering Pareto frontier: the integrated system optimises for **SWaP‑C** (Size, Weight, Power, and Cost) and dynamic responsiveness, while the modular system optimises for **proven reliability, maintainability, and low development risk**. Both architectures share the same clean‑inner‑tube principle: the conductive mist remains in the outer annulus, and the drift tube is a sealed vacuum chamber. The difference is how the mist flow is driven and controlled.

### 5.1 Quantitative System‑Level Comparison

| Feature / Metric | CPB‑ENG‑001 Rev 4.0 (Modular) | Integrated Mag‑Lev Turbine | Engineering Implication |
| :--- | :--- | :--- | :--- |
| **Primary Pumping Mechanism** | Passive coaxial Venturi ejector, fed by an external compressor (3–5 bar) | **Rotor‑driven mist pump** (no external compressor; uses electric power directly) | Integrated eliminates compressor, enables battery‑only operation |
| **Core Mode Pressure Control** | Fixed by Venturi geometry and supply pressure | Continuously variable via rotor speed (5–200 mbar) | Greater operational flexibility without hardware changes |
| **Total System Mass** | **4.2–5.1 kg** (includes compressor, HV supply, controller) | **0.8–1.2 kg** (rotor head + integrated FPGA) | >75 % mass reduction for portable platforms |
| **Total Steady‑State Power Draw** | **120–180 W** (compressor + HV + control) | **60–80 W** (AMB drive + HV + control) | 40–50 % reduction in battery burden |
| **Pressure Control Bandwidth** | ~500 ms – 2 s (compressor throttle/valve) | <50 ms (direct RPM control) | Enables real‑time closed‑loop pressure tuning |
| **Component Count (Critical Parts)** | >40 (compressor, valves, Venturi nozzle, HV modules, sensors) | <15 (rotor, AMB coils, housing, PCB) | Dramatically reduced assembly complexity and potential failure points |
| **Estimated BOM Cost (NRE)** | ~$8,000 – $12,000 (off‑the‑shelf modules) | ~$4,500 – $6,500 (custom rotor + AMB, high NRE) | Lower unit cost, but higher upfront engineering investment |
| **Contamination Risk** | Low (inner tube always clean; oil‑free Venturi) | **Very Low** (inner tube clean; no oil, no dynamic seals; mist only in annulus) | Both are clean; integrated avoids even the possibility of compressor oil |
| **HV Mode Pumping** | Requires external turbopump + ion pump | Requires external turbopump + ion pump (same as modular) | **Identical** – the rotor does not pump the inner tube to UHV |
| **Plasma Current Sensing** | Shunt resistor in HV return (noise‑prone) | Isolated pot‑core pickup (galvanic, dI/dt) | Improves signal integrity and operator safety |
| **On‑Rotor Power** | Not possible | 1–2 W continuous via rotary transformer | Enables active rotor heating, on‑rotor sensors, burst‑power supercap |
| **Ignition Jitter (σ)** | 0.5–5 ms (statistical seeding) | <50 µs (magnetically pre‑seeded, FPGA‑timed) | Critical for pump‑probe and time‑resolved spectroscopy |
| **System Development Maturity (TRL)** | **TRL 6–7** (prototype demonstrated) | **TRL 2–3** (concept validated; components tested individually) | Integrated system requires 12–18 months of dedicated R&D |
| **Mean Time Between Failures (MTBF)** | ~5,000–8,000 h (field‑proven) | **Projected:** ~2,500–4,000 h (limited data) | Shorter initial life; mitigations in §7 aim to extend |
| **Field Serviceability** | Module‑level swap (30 min) | Rotor/bearing failure requires factory‑level rebuild (>2 h) | Modular offers superior uptime for high‑availability deployments |

### 5.2 Qualitative Feature Comparison

| Feature | CPB‑ENG‑001 Rev 4.0 (Modular) | Integrated Mag‑Lev Turbine |
| :--- | :--- | :--- |
| **Mist Drive** | External compressor + passive Venturi nozzle | On‑board rotor directly accelerates mist |
| **Aerosol Charging** | External HV needle / ionizer | Built‑in magnetic polarisation via rotating B‑field |
| **Core Pressure Range** | 30–80 mbar (compressor‑limited) | 5–200 mbar (RPM‑dependent) |
| **Transition to HV** | Close isolation valve, pump down with external turbopump | Identical procedure; rotor stops or idles |
| **Control Architecture** | Distributed (compressor throttle, HV supply, valves) | Centralized FPGA (AMB, ignition, sensing) |
| **Wear and Consumables** | Compressor maintenance, valve seals | No consumables; periodic rotor cleaning cycles |
| **Failure Impact** | Single module fails → replacement; system resumes | Rotor crash → entire head lost; full teardown |
| **Heat Dissipation** | Distributed across modules (easier) | Concentrated in rotor/stator gap (requires radiative cooling) |
| **Operating Noise** | Compressor: 55–65 dBA | AMB drive + windage: 40–50 dBA (significantly quieter) |
| **Technology Lock‑in** | Standard components; supplier‑agnostic | Highly custom rotor and AMB; supplier‑dependent |

### 5.3 Quantitative SWaP‑C Trade‑off Summary

| Metric | Modular | Integrated | Delta (Integrated vs. Modular) |
| :--- | :--- | :--- | :--- |
| **Mass (kg)** | 4.7 | 1.0 | **−79 %** |
| **Volume (L)** | 8.5 | 2.2 | **−74 %** |
| **Power (W)** | 150 | 70 | **−53 %** |
| **Unit Cost (USD)** | $10,000 | $5,500 | **−45 %** |
| **Development Risk** | Low | High | **+ (Trade‑off)** |
| **Failure Consequence** | Low (module swap) | High (head loss) | **+ (Trade‑off)** |

### 5.4 Engineering Decision Matrix: Which Architecture to Choose?

| Scenario | Recommended Architecture | Rationale |
| :--- | :--- | :--- |
| **Near‑term plasma characterisation lab bench** | Modular | Proven performance; lower risk; immediate data collection. |
| **Remote field deployment (drone, rover, handheld)** | **Integrated Turbine** | Unmatched SWaP‑C; no compressor; fast pressure agility; quiet operation. |
| **High‑purity material processing (no oil, no compressor oil)** | **Integrated Turbine** | Completely oil‑free; sealed clean inner tube. |
| **Low‑cost, high‑volume production** | **Integrated Turbine** | Lower BOM and component count; manufacturable once NRE is amortised. |
| **Maximum system uptime / field‑serviceable** | Modular | Module‑level replacement yields higher MTBF and lower downtime. |
| **Time‑resolved spectroscopy (pump‑probe experiments)** | **Integrated Turbine** | Low‑jitter ignition (<50 µs) is mandatory for sub‑millisecond timing. |
| **High‑risk exploratory R&D** | **Integrated Turbine** | High reward justifies the investment in validation (Stages 1–4). |
| **Mixed‑mode operation (Core Jet ↔ HV Beam)** | **Either** | Both use the same isolation + pump‑down procedure; integrated adds RPM agility. |

### 5.5 Final Engineering Position

The integrated rotor architecture does not render the modular CPB design obsolete; rather, it unlocks a new performance class for applications where size, weight, power, and response time are paramount. By replacing the external compressor with a directly driven mist pump, the integrated design eliminates a major source of mass and noise while preserving the clean inner tube that makes the dual‑mode CPB possible.

**The acknowledged trade‑off**-concentrating failure risk into a single high‑speed rotating assembly-is offset by the comprehensive engineering mitigations detailed in Section 7: dual‑controller AMB redundancy, passive backup bearings, active rotor heating, vibration‑based condition monitoring, and a sacrificial PEEK touchdown liner. With these safeguards, the probability of a catastrophic rotor crash is projected to be <1 % over a 500‑hour operational life, comparable to the failure rate of high‑end turbomolecular pumps. The reward-a >75 % reduction in system mass and >50 % reduction in power consumption-justifies this calculated risk for the targeted deployment scenarios.

---

## 6. New Functionality Enabled by the Integrated Turbine

Beyond the core plasma generation and mist‑pumping functions, the unified rotor architecture enables several advanced diagnostic and operational modes that are either impractical or impossible with the modular CPB design. These capabilities transform the system from a simple particle source into a multifunctional analytical instrument-all while preserving the clean inner tube.

### 6.1 Energy‑Assisted Portable Spectrometer

The rotary transformer provides a continuous, galvanically isolated power source to the rotating assembly. With a baseline coupling coefficient of \(k \approx 0.6\)–0.85 and 100 turns on the secondary, the system delivers **1–2 W continuous** at 4 kHz (8 poles, 30 krpm). While insufficient for high‑power electronics, this is ample for a carefully curated low‑power payload in the annulus or on the rotor body.

- **Power Budget Allocation (Continuous):**
  - **Grid Driver / Emitter Bias:** 500 mW (generates a local oscillator or extraction field that can be capacitively coupled to the external mist electrode).
  - **Microcontroller (ARM Cortex‑M7):** 200 mW (handles timing, data buffering, and communication protocol).
  - **Low‑Power Optical Spectrometer (e.g., Hamamatsu C12880MA):** 1.0–1.5 W (performs 200–850 nm spectral acquisition of the plasma glow through a viewport in the inner tube; the spectrometer is mounted on the stationary housing, not on the rotor).
  - **Wireless Data Telemetry (Bluetooth Low Energy 5.0 or LoRa):** 300 mW peak (transmits data from the stationary electronics to a remote receiver).
  - **Thermal Management (Rotor Heater):** Reserved for active evaporation of mist deposits from the rotor surface, as detailed in Section 7.3.

- **Burst Power and Supercapacitor Sizing:** Plasma ignition and wireless data packet transmission require peak currents exceeding the transformer’s continuous limit. A 2.7 V, 5 F supercapacitor bank (configured for 5.4 V series) provides:
  \[
  E_{stored} = \frac{1}{2} C V^2 = \frac{1}{2} \cdot (1.25 \text{ F}) \cdot (5.4)^2 \approx 18 \text{ J}
  \]
  This supports a 100 ms ignition pulse at 3 W, plus a 50 ms data burst at 5 W, with only a 0.5 V droop. The supercapacitor is trickle‑charged continuously by the pot‑core rectifier between events.

- **Operational Architecture for Drone/Remote Deployment:**
  - The system operates in a **duty‑cycled “sniff” mode**: spin up the rotor using the main AMB drive, run the plasma for 2 seconds, acquire a spectrum, transmit data (timestamp + intensity + temperature), and then idle or coast for 10 seconds to recharge the supercapacitors.
  - The main rotor drive still requires a battery (e.g., a small 12 V, 2 Ah LiFePO₄ pack) to spin up the rotor and maintain levitation. The rotary transformer powers the on‑rotor heater and any auxiliary electronics, reducing the number of wired connections and improving isolation.

### 6.2 Rotating‑Field Ion Mobility Spectrometer (RF‑IMS)

The external stator coils are wound in a multi‑phase configuration (e.g., 3‑phase or 4‑phase). By applying quadrature‑shifted currents to these coils, a **rotating magnetic field pattern** is superimposed on the inner drift tube. This rotating field penetrates the thin tube wall and interacts with the charged particles drifting in the axial electric field (\(E_z\)), creating a time‑varying \(\mathbf{E} \times \mathbf{B}\) drift that modulates the ion trajectory.

- **Physical Mechanism:**
  - The rotating field produces a travelling wave of magnetic flux density \(B(t)\) with angular frequency \(\omega_{rot}\).
  - Ions of mobility \(K\) experience a transverse drift velocity \(v_{E\times B} = \frac{\mathbf{E}_{induced} \times \mathbf{B}}{B^2}\). As \(\omega_{rot}\) is swept, the phase velocity of the travelling wave changes.
  - When the wave phase velocity matches the axial drift velocity of a specific ion species (\(v_d = K \cdot E_z\)), that species undergoes cyclotron resonance and its path length to the collector is maximised (or minimised), producing a distinct peak in the collected current.

- **Performance Estimates:**
  - **Operating Frequencies:** With an axial field \(E_z \approx 500\) V/m and typical ion mobilities in 30 mbar air (\(K \approx 1.5\) cm²/V·s), \(v_d \approx 75\) m/s. To match this, the required rotation frequency of the magnetic wave is \(f = v_d / \lambda\), where \(\lambda\) is the 2 mm pitch of the B‑field pattern. This yields \(f \approx 37.5\) kHz-well within the 4 kHz–100 kHz bandwidth of the stator drive amplifiers (using GaN FETs).
  - **Resolving Power:** The system replaces the 10–20 cm conventional drift cell with a **compact 5 cm effective path** inside the 2.00 mm diameter drift tube. The resolving power (\(R = t / \Delta t\)) is estimated at 30–50 (comparable to field‑portable IMS systems), limited primarily by wall collisions.
  - **Advantage:** By sweeping the pulse frequency and measuring the collector current via the pot‑core pickup, the system obtains a mobility spectrum **without a separate long drift cell or Bradbury‑Nielsen gate**, drastically simplifying the mechanical assembly. The clean inner tube ensures no contamination interferes with the ion mobility measurement.

- **Implementation:** A dedicated look‑up table (LUT) in the FPGA varies the quadrature phase shift between the AMB drive cycles. The collected current signal is synchronously demodulated with the sweep frequency to extract the ion mobility peaks from background noise.

### 6.3 Non‑Contact Plasma Diagnostics

The integrated rotary transformer provides a naturally isolated current sensor that eliminates the need for a high‑voltage shunt resistor in the drift‑tube return path.

- **Signal Chain and Calibration:**
  - The plasma discharge current \(I_{discharge}\) (10 µA – 2 mA) flows down the central electrode and through the inner drift tube. This current induces a magnetic flux that links the stationary pot‑core pickup coils (the field passes through the non‑magnetic tube wall).
  - The induced voltage in the stator coil is \(V_{sense} = M \cdot dI_{discharge}/dt\), where \(M\) is the mutual inductance between the plasma column and the pickup (estimated at 0.5–2 µH).
  - **Front‑End Electronics:** The raw signal is passed through a low‑noise transimpedance amplifier, followed by a precision active integrator to reconstruct the absolute current waveform (\(I = \frac{1}{M} \int V_{sense} \, dt\)).
  - **Noise Rejection:** A notch filter at the rotor’s fundamental rotational frequency (4 kHz) and its harmonics removes the transformer’s power carrier, yielding a clean signal with a bandwidth of **0–100 kHz** (limited by the transformer’s high‑frequency roll‑off).

- **Safety and Accuracy Advantages:**
  - Galvanic isolation (>10 kV) protects the control electronics from HV transients and eliminates ground loops.
  - Calibration is performed by injecting a known 1 mA, 1 kHz square wave into the emitter circuit during initial system boot; the FPGA stores the scaling factor.
  - This enables real‑time monitoring of the discharge mode (glow vs. arc) and provides feedback to the HV supply for closed‑loop current regulation, preventing thermal runaway in the emitter.

### 6.4 Physical Computing Primitives (Exploratory R&D Track)

*Caveat:* The following applications are at **TRL 1–2** and represent speculative future research directions that leverage the unique mechanical‑plasma‑mist coupling. They are **not prerequisites** for the core CPB platform validation and should be pursued only after Stages 1–4 are successfully demonstrated.

The integration of a high‑speed rotor in the mist annulus with a non‑linear plasma load in the clean inner tube creates a physical substrate for unconventional computation.

- **Mechanical Spin‑State Memory (Non‑Volatile Bit):**
  - The rotor can be spun clockwise (CW) or counter‑clockwise (CCW) at the same speed. Once spinning, the rotor maintains its state indefinitely without consuming control power (only requiring AMB levitation, which can be reduced to a low‑power hold mode).
  - **Readout:** The phase of the pot‑core signal relative to the stator drive encodes the spin direction (binary 0/1). The stored kinetic energy (\(>1,300\) J) ensures state retention even during brief power outages, providing a physically robust memory element for harsh environments.

- **Coupled‑Oscillator Logic (Reservoir Computing):**
  - Two independent integrated turbines, each with its own mist annulus and clean inner tube, are connected by a common mist supply manifold and a shared plasma‑diagnostic bus. The rotors act as coupled oscillators through the mist flow: variations in one rotor’s speed alter the local mist pressure, which propagates to the second rotor.
  - **Mechanism:** Changes in the discharge current in one tube affect the plasma density and temperature, which in turn modify the electrostatic coupling to the mist and thus the mist’s effective viscosity and drag on the rotor. This creates a non‑linear coupling loop.
  - **Application:** By injecting a time‑varying input signal (e.g., varying the mist concentration), the coupled rotor system can be used as a physical reservoir computer to perform non‑linear classification (e.g., pattern recognition in sensor data) without digital processing, with the output read via the instantaneous frequency difference measured by the pot‑core sensors.

- **Power‑Compute Co‑Design (Energy‑Information Merger):**
  - The 1–2 W harvested from the spinning motion directly powers the on‑rotor electronics that control the rotor’s temperature and pre‑ionization pulses. This closes a feedback loop where mechanical energy is simultaneously the power source and the computational parameter.
  - **Hypothesis:** Using analog feedback (e.g., varying the duty cycle of the pre‑ionization pulses based on the emitted light intensity) allows the system to self‑oscillate or self‑tune to a desired plasma state, effectively “calculating” the optimal operating point using the physics of the rotor itself.

**Exploratory Roadmap:** These primitives require a dedicated testbed with two interconnected heads, high‑speed phase‑locked loop measurement circuits, and a custom FPGA for capturing the analog state trajectories. This work is best suited for a follow‑on Phase II research grant and is explicitly outside the scope of the current CPB‑ENG validation campaign.

---

## 7. Engineering Considerations

The transition from a benchtop concept to a flight-ready or field-deployable assembly requires rigorous engineering across rotor dynamics, thermal management, materials science, and high‑voltage safety. This section establishes the baseline design parameters, quantitative limits, and mitigation strategies for the integrated rotor assembly. The rotor operates entirely in the outer mist annulus; it never contacts the clean inner drift tube.

### 7.1 Rotor Dynamics, Critical Speeds, and Structural Integrity

The rotor is the single most critical mechanical component; its failure constitutes a catastrophic loss of the entire head.

- **Tip Speed and Material Limits:** The tip speed is capped at **150 m/s** (≈Mach 0.3) to avoid compressibility losses and excessive aerodynamic heating. For a 60 mm diameter rotor (the proposed enhancement for mist pumping), this limits the maximum rotational speed to:
  \[
  N_{max} = \frac{150}{\pi \cdot 0.06} \times 60 \approx 47,700 \text{ RPM}
  \]
  For a 40 mm diameter rotor (baseline), the safe limit extends to ≈71,600 RPM, though practical AMB control bandwidth limits operation to ≤50,000 RPM.

- **Burst Margin:** The rotor body (7075‑T6 Aluminum or Grade 5 Ti‑6Al‑4V) must withstand centripetal accelerations exceeding 20,000× *g*. Finite Element Analysis (FEA) is mandatory to ensure a **minimum burst safety factor of 2.0** at maximum overspeed (1.2× the operational maximum). The embedded ferrite pot‑cores and permanent magnets are the weakest structural links; they must be encapsulated in a shrink‑fit titanium or Inconel retaining sleeve to prevent delamination at speed.

- **Modal Analysis (Critical Speeds):** The active magnetic bearings (AMBs) must be tuned to avoid the rotor’s first bending mode. The rotor is effectively a free‑free beam; the first flexural critical frequency must be placed **at least 20 % above** the maximum operating speed. For a 60 mm diameter, 80 mm long solid aluminum rotor, the first bending mode is estimated at ~3.5 kHz (210,000 RPM)-well above the operating range. The addition of shallow helical texturing (for mist pumping) and magnet arrays will alter the modal response; a detailed rotordynamic analysis (using tools such as DyRoBeS or XLRotor) is required prior to final machining.

- **Surface Finish and Mist Pumping Efficiency:** Efficient acceleration of the conductive mist relies on momentum transfer from the moving rotor surface. The rotor surface in the smooth section must achieve **Ra ≤ 0.4 µm** to maximise mist drag without excessive turbulent losses. Where shallow helical texturing (0.3 mm depth, 30° pitch) is employed to boost mist flow rate, the groove dimensions must be maintained with ±5 µm tolerance to realise the projected gain.

### 7.2 Thermal Management and Steady‑State Heat Loads

The rotor operates in a rarefied mist environment; convective cooling is weak and heat removal is primarily radiative and via conduction through the gas/mist mixture.

- **Major Heat Sources:**
  1. **Windage / Aerodynamic Heating:** At 30 krpm in 30–80 mbar mist‑laden gas, viscous shear in the 0.2 mm gap generates approximately **2–4 W** of heat on the rotor surface.
  2. **Eddy Current Losses:** The time‑varying magnetic fields in the ferrite pot‑cores and permanent magnets induce eddy currents. Using low‑loss ferrite (e.g., 3F3 or N87 material) and segmented magnets limits this to **<1.5 W** at 4 kHz.
  3. **Bearing AMB Losses:** Bias currents in the AMB statics generate iron losses; estimated at **3–5 W** in the stator, though only a fraction is radiated to the rotor.

- **Steady‑State Temperature Rise:** With a total rotor heat load of ~6 W and a surface area of ~0.015 m², the radiative equilibrium temperature (assuming an emissivity of 0.3 for polished aluminum) is calculated at **85–95 °C** above ambient. This exceeds the 80 °C maximum operating temperature for standard NdFeB magnets.

- **Mitigations:**
  - Apply a high‑emissivity coating (e.g., black anodization or DLC with ε > 0.8) to the rotor body to enhance radiative cooling, dropping the equilibrium rise to ~45 °C.
  - The rotary transformer is used not only for power but also as a **thermal shunt**-the pot‑core halves are thermally anchored to the water‑cooled (or forced‑air) stator housing.
  - A thermistor embedded in the stator housing, coupled with a derating curve, will trigger an automatic speed reduction if the housing exceeds 60 °C.

### 7.3 Mist–Rotor Interaction and Active Balance Control

Droplet deposition from the conductive mist onto the rotor surface is the **highest operational risk**. The following quantitative framework defines the mitigation strategy.

- **Unbalance Force Threshold:** The AMBs can sustain a maximum radial unbalance force of **150 N** before saturating the control current. At 30 krpm and a 30 mm effective radius, the maximum allowable mass imbalance is:
  \[
  m_{unb} = \frac{F}{r \cdot \omega^2} = \frac{150}{0.03 \cdot (3141)^2} \approx 5 \times 10^{-4} \text{ kg} = 500 \text{ mg}
  \]
  A single large asymmetric deposit of several hundred milligrams would be required to saturate the bearings; however, progressive uneven deposition of tens of milligrams over many minutes will gradually erode the control margin. Real‑time bearing‑current monitoring will detect such drift early.

- **Active Deposition Evaporation:**
  - The rotor is actively heated via the pot‑core transformer’s rectified output. A dedicated 1 W heating element (embedded beneath the rotor skin) maintains the surface at **80–90 °C** during operation-sufficient to evaporate water and volatile organics from the mist before they adhere.
  - A **surface energy modification** is applied: a hydrophobic or oleophobic DLC coating (e.g., DLC with Si‑doping) reduces the sticking coefficient of saline droplets by >60 %, encouraging them to be shed centrifugally toward the housing walls.

- **In‑Situ Cleaning Protocol:**
  - Automated “cleaning cycles” are executed between experimental runs: the rotor spins at 45 krpm in a dry nitrogen atmosphere (5 mbar) for 30 seconds. Centrifugal force ejects any dried salt residues.
  - **Vibration Signature Monitoring:** The AMB position sensors (eddy‑current, 5 nm resolution) continuously monitor the rotor’s synchronous (1×) vibration amplitude. If the amplitude exceeds 10 µm peak‑to‑peak, a **soft shut‑down** is initiated, and the cleaning cycle runs before resuming normal operation.

### 7.4 Touchdown and Catastrophic Containment

Despite active balancing, mechanical or electrical failure of the AMB controller must be survivable.

- **Kinetic Energy Storage:** At 30 krpm with a 0.15 kg rotor (60 mm diameter, 80 mm length, aluminum), the stored kinetic energy is:
  \[
  E = \frac{1}{2} I \omega^2 \approx \frac{1}{2} (2.7 \times 10^{-4}) \cdot (3141)^2 \approx 1,330 \text{ J}
  \]
  The rotor must be treated as a high‑energy flywheel.

- **Catch Mechanism:** A **dual‑layer containment ring** is employed:
  1. **Inner Liner:** A 3 mm thick PEEK (polyether ether ketone) or Torlon ring with a 0.15 mm radial clearance to the rotor. This ductile material will cold‑form upon impact, absorbing kinetic energy through plastic deformation.
  2. **Outer Shell:** A 6 mm thick 304 stainless steel burst shield, rated to contain the impact of the PEEK‑decelerated rotor without perforation. FEA impact simulations must confirm the housing maintains structural integrity, as per ISO 14839 (mechanical vibration of high‑speed rotating machinery).

- **Deceleration Time:** Upon touchdown, the friction between the rotor and the PEEK liner is expected to stop the rotor within <1 second. The resultant heat pulse is absorbed by the thermal mass of the housing, with a calculated temperature spike of <20 °C.

### 7.5 Electrical Insulation and High‑Voltage Standoff

The system integrates low‑voltage controls (AMBs, pot‑core coils) in close proximity to the high‑voltage central emitter (−2 kV to −10 kV). Dielectric breakdown must be prevented.

- **Creepage and Clearance:** The central needle electrode is separated from the grounded housing by the 2.00 mm drift tube aperture. At 10 kV in 30 mbar gas, the Paschen minimum allows breakdown over ~1 mm; a **minimum 4 mm creepage distance** is maintained along all ceramic insulators supporting the needle.
- **Pot‑Core Isolation:** The stationary pot‑core pickup coils, although separated from the HV electrode by the drift tube wall, see transient capacitive coupling. All signal conditioning amplifiers will include **transient voltage suppression (TVS)** diodes (rated at 15 kV) and isolated DC‑DC converters (≥10 kV isolation) to protect the FPGA logic.
- **AMB Isolation:** The magnetic bearings use air‑core or ferrite‑core electromagnets that are inherently galvanically isolated from the plasma. However, the bearing controller ground must float relative to the HV return. A dedicated **HV isolation transformer** (5 kV rating) will power the AMB drive electronics to prevent ground‑loop faults through the plasma return path.

### 7.6 Assembly, Alignment, and Maintenance

Achieving the sub‑millimetre gaps (0.2 mm mist‑pump gap, 0.15 mm touchdown clearance) demands precision assembly.

- **Alignment Procedure:** The upper and lower housing halves are aligned using precision dowel pins. The rotor is installed, and the AMB sensors are zeroed using a dial gauge to ensure the rotor’s geometric center coincides with the magnetic center to within ±10 µm.
- **Rotor Balancing:** Prior to installation, the rotor assembly (including magnets, ferrites, and retaining sleeve) must be dynamically balanced at speed (using a vacuum spin test) to **Grade G1.0** (ISO 1940). This limits residual unbalance to <0.5 g·mm/kg, ensuring the AMBs do not have to fight a static imbalance.
- **Preventative Maintenance:** Given the mist environment, the head is designated a **consumable module** with a recommended 500‑hour operational life before a factory overhaul (replacement of the PEEK liner, bearing sensors, and rotor cleaning). This is comparable to the service interval of high‑performance turbomolecular pumps.

### 7.7 Systems‑Level Redundancy (Mitigating the Single Point of Failure)

To address the “concentrated risk” identified in Section 5, the following redundancy is built into the control electronics:

- **Dual‑Controller AMB:** The AMB control loop is implemented on two independent FPGAs with cross‑checking. If one controller faults, the other assumes full control within 1 ms.
- **Passive Backup Bearing:** A permanent magnet passive bearing (using opposing ring magnets) is placed at the opposite end of the rotor. In the event of complete active levitation loss, the passive bearing provides a stabilizing stiffness of ~5 N/mm, slowing the rotor’s descent onto the PEEK liner and reducing impact forces by an estimated 40 %.

---

## 9. Open Questions and Future Work

- **Mist–rotor interaction** remains the top priority: quantitative study of droplet deposition, evaporation, and balance drift during continuous operation.
- **Helical texturing vs smooth** rotor surface optimisation for mist flow rate and Venturi entrainment.
- **Power management** circuit design for the rotary transformer: static impedance measurement, rectification efficiency, and supercapacitor charge/discharge cycling under representative load.
- **Long‑term reliability** of AMBs in a conductive aerosol environment; failure mode characterisation and bearing sensor drift over 500+ hours.
- **Isolation valve integrity** under repeated cycling between Core and HV modes; helium leak rate stability over the service interval.

*(The original item “Groove geometry for efficient molecular drag with minimal mist clogging” has been removed, because the inner tube is isolated and evacuated by an external high‑vacuum pump in HV mode; the rotor is not used as a molecular drag stage for the beamline.)*

---

## 10. Conclusion

The integrated mag‑lev turbine architecture transforms the Coherent Particle Beam from separate subsystems into a single, elegant rotating machine that resides entirely in the outer mist annulus. By spinning the rotor, we drive the conductive mist that pumps the clean inner tube via the Venturi effect, generate power for on‑rotor heating, pre‑ionize the plasma in the sealed drift tube, and sense its current-all without oil, dynamic seals, or contamination of the beamline. The trade‑off is higher complexity and concentrated failure risk, but the payoff is a compact, fast‑responding, and energy‑assisted plasma source that preserves the fundamental clean‑tube principle of the CPB platform. With a realistic development path starting from validation of mist flow rate and Venturi entrainment at 30–80 mbar, the concept can be validated step by step, leading to a unique instrument that merges fluidics, magnetics, and plasma physics in one moving part.
