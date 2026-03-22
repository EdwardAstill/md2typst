# GENG5514 Group Assignment

All the project info in one place. Read this and you'll know what we're doing, how, and why.

---

## 1. The Problem

We have a subsea carbon steel pipeline sitting on an uneven seabed. Where the seabed dips, the pipe doesn't touch the ground -- these gaps are **free spans**. Ocean currents hit these unsupported sections and cause **vortex-induced vibration (VIV)**, which means cyclic bending stress, which means fatigue damage. We need to figure out how many years the pipe lasts.

Four stages:

1. **Static FEA** (Abaqus) -- find where the pipe touches the seabed and where it spans freely
2. **Modal analysis** (Abaqus) -- get natural frequencies and mode shapes of the free spans
3. **Fatigue calc** -- VIV response models + Palmgren-Miner rule = fatigue life estimate
4. **Sensitivity study** -- wiggle key parameters, see what matters

---

## 2. Given Parameters

### Pipeline Geometry

| Parameter | Value |
|---|---|
| Outer diameter (OD) | 0.368 m |
| Wall thickness (WT) | 24 mm |
| Inner diameter (ID) | 0.320 m |

### Material (Carbon Steel)

| Parameter | Value |
|---|---|
| Young's modulus (E) | 207 GPa |
| Poisson's ratio (v) | 0.3 |
| Density | 7861 kg/m^3 |
| Thermal expansion coefficient | 1.3 x 10^-5 /degC |

### Soil-Pipe Interaction

| Parameter | Value | Used In |
|---|---|---|
| Static vertical stiffness | 200 kN/m^2 | Static analysis |
| Dynamic vertical stiffness | 1900 kN/m^2 | Modal analysis |
| Friction coefficient | 0.15 | Both |

### Seabed Profile

From `KP-Depth.xlsx` (provided with the assignment, exported to `seabed_profile.csv`) -- 36 points from KP 2000 m to KP 3024 m. Each row is a kilometric post (KP) and depth below water surface. The seabed goes up and down; wherever the pipe bridges a valley without touching, that's a free span.

- ~1024 m total pipeline length
- Depths range ~64.6 m to ~70.4 m
- Multiple dips and rises, so expect several free spans

### S-N Curve (from Figure 2-2)

Bi-linear on a log-log plot. Relates stress range S (MPa) to allowable cycles N before failure:

```
N = a / S^m
```

| Segment | Slope (m) | Intercept log10(a) | Applies When |
|---|---|---|---|
| High stress | 3.0 | 11.61 | S > S_knee |
| Low stress | 5.0 | 15.35 | S <= S_knee |

Knee point (where segments meet): S_knee ~ 74.1 MPa, N_knee ~ 10^6 cycles. These parameters are read off Figure 2-2 and match a DNV E-class curve in seawater with cathodic protection. The exact values aren't given -- we extracted them from the figure, so justify in the report.

---

## 3. Assumptions We Make

Not given in the problem -- we pick these ourselves and need to justify them in the report:

| Assumption | Value | Justification |
|---|---|---|
| Internal pressure | 10 MPa | Typical operating pressure for subsea oil/gas pipeline |
| Temperature rise | 50 degC | Hot product relative to ambient seawater temperature |
| Lay tension | 500 kN | Residual axial tension from installation (S-lay or J-lay) |
| Pipe contents density | 1025 kg/m^3 | Assumed water-filled (conservative for submerged weight) |
| Seawater density | 1025 kg/m^3 | Standard value |
| Strouhal number | 0.2 | Standard value for circular cylinder in sub-critical flow |
| Element type | PIPE31 | 2-node linear pipe beam element (appropriate for slender pipeline) |
| Element size | 1.0 m | Confirmed by mesh convergence study |
| Material model | Linear elastic | Stress levels well below yield; fatigue is in elastic range |
| End boundary conditions | Pinned at start, roller at end | Pipeline continues beyond modelled section |

### Current Velocity Distribution

Weibull-like distribution of current speeds over the year (made up, needs justification):

| Velocity (m/s) | Fraction of Year |
|---|---|
| 0.05 | 20% |
| 0.10 | 25% |
| 0.20 | 25% |
| 0.30 | 15% |
| 0.50 | 10% |
| 0.70 | 4% |
| 1.00 | 1% |

Needs justification in the report. The problem statement says **currents are more significant than waves**, so we only consider currents.

---

## 4. Stage 1: Static Analysis in Abaqus (GUI Route)

Goal: find the pipe's resting position on the seabed under operational loads. This tells us where it's touching and where the free spans are.

### 4.1 Create the Part

1. Open Abaqus/CAE
2. Create a 3D Deformable Wire part
3. The wire follows the seabed bathymetry: for each KP point in the CSV, plot a point at (x, y) where x = KP (raw value from CSV, so starts at 2000) and y = -(Depth) + OD/2. The OD/2 offset puts the pipe axis just above the seabed surface
4. Connect the points with straight line segments to form a single wire

### 4.2 Define the Material and Section

1. Create a material: E = 207 GPa, v = 0.3, density = 7861 kg/m^3, thermal expansion = 1.3e-5 /degC
2. Create a Pipe Profile: outer radius r = 0.184 m, wall thickness t = 0.024 m
3. Create a Beam Section using the pipe profile and material
4. Assign the section to the wire part

### 4.3 Mesh the Part

1. Seed the part with element size = 1.0 m (for convergence study, also try 2.0, 0.5, 0.25 m)
2. Assign element type: PIPE31 (2-node linear pipe element in 3D space)
3. Generate mesh

Why PIPE31: Timoshenko beam element that handles axial force, bending, torsion, and knows the pipe cross-section (needed for pressure loads). Good fit for a long slender pipeline.

### 4.4 Assembly and Node Sets

1. Create an instance of the part in the Assembly module
2. Create node sets: StartNode (first node), EndNode (last node), AllNodes (all nodes)

### 4.5 Define the Step

1. Create a Static, General step
2. Enable **geometric nonlinearity** (Nlgeom = ON) -- this is important because the pipe undergoes large displacements as it settles onto the seabed
3. Set increment sizes: initial 0.1, minimum 1e-10, maximum 0.5, max increments 1000

### 4.6 Apply Boundary Conditions

1. **StartNode**: pin -- fix translations only (U1=U2=U3=0), leave rotations free
2. **EndNode**: roller (U2=U3=0, free in U1 to allow axial expansion)
3. **AllNodes**: constrain U3=0 (keep pipe in the x-y plane -- we model in 2D effectively)

### 4.7 Apply Loads

1. **Gravity**: acceleration of 9.81 m/s^2 in the -y direction, applied to the whole model. The pipe density (7861 kg/m^3) gives the steel weight. For the contents, we need to account for the internal fluid weight and external buoyancy. This is handled through an effective density or by adding the content weight and subtracting buoyancy separately
2. **Thermal load**: predefined temperature field of 50 degC applied to all nodes (this creates compressive axial force in the restrained pipe)
3. **Lay tension**: concentrated axial force of 500 kN at the EndNode (or distributed)
4. **Internal pressure**: 10 MPa applied as pipe pressure load
5. **External pressure**: hydrostatic pressure = rho_seawater * g * depth at each point

### 4.8 Soil Springs (Compression-Only)

This is the annoying part. The seabed only pushes up on the pipe (no tension). We model this with **compression-only springs** at every node.

In the GUI approach:
- At each mesh node, create a SPRING1 element connecting the node's vertical DOF (U2) to ground
- The spring stiffness = K_static * element_length = 200 kN/m^2 * 1.0 m = 200 kN/m per spring
- The springs must be **compression-only**: they resist downward movement but offer zero resistance when the pipe lifts off

In Abaqus, compression-only behaviour is defined using a **nonlinear spring** with a force-displacement table:
- For negative displacement (pipe moving down / into soil): force = K * displacement (linear, compressive)
- For zero or positive displacement (pipe lifting off): force = 0

The nonlinear spring table in Abaqus format (force, displacement) looks like:

| Force (N) | Displacement (m) |
|---|---|
| 200000 | -1.0 |
| 0 | 0.0 |
| 0 | 1.0 |

Convention: negative displacement = node moves down into soil, positive force = upward reaction pushing pipe back up. At zero or positive displacement (pipe lifting off), force is zero -- no suction.

### 4.9 Submit and Check

1. Submit the job (Job name: StaticAnalysis)
2. Check that the job completes without errors
3. In the Visualization module, check:
   - The deformed shape looks physical (pipe follows seabed terrain, free spans visible)
   - Reaction forces at springs make sense (positive where pipe rests on soil, zero at free spans)
   - No excessive element distortion warnings

---

## 5. Stage 2: Modal Analysis in Abaqus (GUI Route)

Goal: get the natural frequencies and mode shapes of the free spans. These tell us at what current speeds VIV kicks in and what stress pattern it creates.

### 5.1 Modify the Static Model

1. Start from the completed static model
2. **Change spring stiffnesses** from 200 kN/m^2 (static) to 1900 kN/m^2 (dynamic). The dynamic stiffness is higher because during vibration the soil responds more stiffly. Scale the nonlinear spring table by the ratio 1900/200 = 9.5x
3. Add a new step: **Frequency** (linear perturbation)
   - Place it after the static step
   - Solver: Lanczos
   - Request 20 eigenvalues (modes)
   - This step computes natural frequencies about the deformed equilibrium from the static step

### 5.2 Submit and Check

1. Submit as a new job (ModalAnalysis)
2. In the Visualization module, check:
   - Natural frequencies are reasonable (order of 0.1-10 Hz for typical pipeline spans)
   - Mode shapes show vibration localised in the free span regions
   - Earlier modes correspond to longer spans (lower frequency)

---

## 6. Stage 3: Extract Results

Pull these out of the ODB files for the fatigue calc. In the Abaqus GUI: Visualization > Report > Field Output.

**From the static analysis ODB:**
- Node displacements (deformed positions)
- Section forces (axial force, shear, bending moment along the pipe)
- Spring reaction forces at each node -- this is how we identify free spans: nodes with near-zero spring force = pipe not touching seabed

**From the modal analysis ODB:**
- Natural frequencies for each of the 20 modes
- Mode shapes (displacement pattern for each mode)
- Modal section forces (bending moment distribution per mode -- needed to convert VIV amplitude to stress)

---

## 7. Stage 4: Fatigue Damage Calculation

Done outside Abaqus. Uses the extracted results from Stage 3 to compute fatigue life.

### 7.1 Identify Free Spans

From the spring reaction forces extracted in Stage 3: nodes with near-zero spring force (< 1 N) = pipe not touching seabed there. Group contiguous separated nodes into free spans. Note start node, end node, and length of each.

### 7.2 For Each Free Span and Each Mode

For every combination of (span, mode, current velocity bin):

**Step A: Compute Reduced Velocity**

```
V_R = U / (f_n * D)
```

where U = current velocity (m/s), f_n = natural frequency of the mode (Hz), D = OD = 0.368 m.

**Step B: Check VIV Onset**

Cross-flow VIV occurs when 3.0 < V_R < 8.0 (peak response at V_R = 5.0, max A/D = 0.9).
In-line VIV occurs when 1.0 < V_R < 3.5 (peak response at V_R = 2.2, max A/D = 0.15).

If V_R is outside both ranges, there is no VIV for this combination -- skip it.

**Step C: Get VIV Amplitude**

Triangular response model:
- Linear ramp from onset to peak V_R
- Linear ramp from peak to cessation V_R
- A/D = vibration amplitude as fraction of pipe diameter

Take whichever is larger out of cross-flow and in-line A/D.

**Step D: Compute Stress Range**

```
amplitude = (A/D) * OD                     -- vibration amplitude in metres
stress_range = 2 * modal_stress * amplitude -- full tension-compression cycle
```

where `modal_stress` = maximum bending stress per unit modal displacement, obtained from the modal section forces:

```
modal_stress = M_max / Z
```

Z = section modulus = I / (OD/2), M_max = peak bending moment in the span for that mode.

**Step E: Look Up Allowable Cycles**

From the S-N curve:

```
if stress_range > 74.1 MPa:
    N = 10^(11.61 - 3.0 * log10(stress_range))
else:
    N = 10^(15.35 - 5.0 * log10(stress_range))
```

**Step F: Compute Applied Cycles Per Year**

```
n = f_n * exposure_time
exposure_time = fraction_of_year * 365.25 * 24 * 3600  (in seconds)
```

**Step G: Compute Damage Contribution**

```
damage = n / N
```

### 7.3 Sum All Damage (Palmgren-Miner Rule)

```
D_total = sum of all damage contributions across all spans, modes, and current bins
Fatigue life = 1 / D_total  (in years)
```

Critical span = whichever has the highest damage.

---

## 8. Sensitivity Analysis

Change one parameter at a time, re-run, see what happens to fatigue life:

| Parameter | Variation | Why |
|---|---|---|
| Soil stiffness (K_static, K_dynamic) | +/- 50% | Soil properties are uncertain; affects span lengths and frequencies |
| Current velocity | +/- 20% | Current data is approximate; directly affects VIV excitation |
| Lay tension | +/- 50% | Affects effective axial force, which changes span behaviour |
| Temperature rise | +/- 20% | Affects thermal axial force |
| Damping | Vary stability parameter | Affects VIV amplitude |
| Element size | 2.0, 1.0, 0.5, 0.25 m | Mesh convergence -- proves solution is mesh-independent |

Figure out which parameters matter most. Goes in the discussion section.

---

## 9. Verification and Validation

The rubric explicitly asks for V&V evidence. We need:

1. **Mesh convergence**: run with element sizes 2.0, 1.0, 0.5, 0.25 m. Plot natural frequency (or max stress) vs element size. Show it converges. Table + plot.

2. **Analytical benchmark**: for a simple span, compare Abaqus frequency against the beam-on-elastic-foundation formula:
   ```
   f_n = (n*pi/L)^2 * sqrt(EI / (rho*A)) / (2*pi)
   ```
   Sanity check that the FE model isn't broken.

3. **Equilibrium check**: sum of spring reactions should equal total pipe weight minus buoyancy.

4. **Sniff test**: does the fatigue life look reasonable? Should be in the years-to-decades range for a real pipeline.

---

## 10. Report Structure and Marking

Worth **25% of the unit mark** total:

| Section | Weight | Pages |
|---|---|---|
| Summary | 1% | 0.5-1 |
| Introduction | 5% | 2-4 |
| Methods | 3% | 5-8 |
| Results | 5% | (part of 8-12) |
| Discussion | 5% | (part of 8-12) |
| Conclusions | 5% | 1-2 |
| Presentation | 1% | -- |
| **Total** | **25%** | **max 35** |

### Summary (1%)

Problem statement, how we solved it, key findings (actual numbers), challenges, future work. Write this last.

### Introduction (5%)

Clear goals, technically sound project plan, references to literature, good sources. Must cite:
- Bai & Bai (2014) Ch. 14
- Guo et al. (2013) Ch. 5
- Sollund & Vedeld (2014) Sec. 4
- DNV-RP-F105 (2006+)
- Abaqus documentation

### Methods (3%)

Enough detail that someone else could reproduce the analysis. V&V described. Every decision and assumption justified. BCs, loads, material, elements, solver settings all justified.

### Results (5%)

Significant results, computations and V&V output provided, no errors.

### Discussion (5%)

Accuracy/convergence/stability. Limitations. Improvements. Critical analysis of results. Future work.

### Conclusions (5%)

Supported by results (no new info here). Relates to scope. Shows deep understanding of the physics.

### Presentation (1%)

Clear, no typos, clear diagrams.

### Formatting Requirements

- Max 35 A4 pages including appendices
- Font >= 12pt (Times New Roman, Times, Arial, or Helvetica)
- Margins >= 20 mm
- Harvard referencing style
- Each page must name the group member responsible for it
- Cover sheet signed by all members (no cover sheet = 0 mark)
- Submit: PDF + Word, plus Abaqus input files (.cae, .inp), plus any code/spreadsheets
- Do not submit compressed files

---

## 11. Key Physics Concepts

### What is VIV?

Current flows past a cylinder, vortices shed alternately from each side, creating oscillating forces. If the shedding frequency matches a natural frequency of the span, you get **lock-in** -- the pipe vibrates at large amplitudes.

- **Cross-flow VIV**: perpendicular to current (bigger, A/D up to 0.9)
- **In-line VIV**: parallel to current (smaller, A/D up to 0.15, but starts at lower speeds)

### Reduced Velocity

Dimensionless parameter that links current speed to VIV:

```
V_R = U / (f_n * D)
```

VIV only happens within certain V_R ranges (see Section 7.2). Outside those, no lock-in, no significant vibration.

### Palmgren-Miner Rule

Linear damage accumulation. Each stress cycle eats a fraction of the fatigue life. The fractions add up:

```
D = sum(n_i / N_i)
```

n_i = applied cycles at stress range S_i, N_i = allowable cycles from S-N curve. D hits 1.0 = failure. Fatigue life = 1/D years (if D is per year).

### Why Two Soil Stiffnesses?

- **Static** (200 kN/m^2): long-term, slow-loading response. Pipe settling onto seabed.
- **Dynamic** (1900 kN/m^2): short-term, vibration-frequency response. Soil is stiffer under rapid cyclic loading. Used for modal because VIV is dynamic.

### Why Nonlinear Static?

Two reasons:
1. **Compression-only springs** -- soil only pushes up, that's a nonlinearity
2. **Geometric nonlinearity** -- pipe displaces significantly as it settles, and axial force interacts with deflection (P-delta effect)

### Why Linear Modal After Nonlinear Static?

The modal step is a **linear perturbation** about the deformed shape from the static step. It picks up:
- Actual span lengths (from the nonlinear static solution)
- Axial force effects on frequencies (compression lowers them, tension raises them)
- Dynamic soil stiffness at contact points

---

## 12. What We Should End Up With

After all four stages:

1. Figure of deformed pipe on seabed with free spans marked
2. Table of free span locations (KP range, length, gap height)
3. Table of natural frequencies per span and mode
4. Mode shape plots for the critical spans
5. Mesh convergence plot
6. Table of fatigue damage per span/mode/current bin
7. Total fatigue life in years
8. Sensitivity plots
9. Which span is critical (governs fatigue life)

---

## 13. References

1. Bai, Q. and Bai, Y. (2014) *Subsea Pipeline Design, Analysis, and Installation*, Elsevier. Chapter 14.
2. Guo, B. et al. (2013) *Offshore Pipelines: Design, Installation, and Maintenance*, Elsevier. Chapter 5.
3. Sollund, H. and Vedeld, K. (2014) *A Finite Element Solver for Modal Analysis of Multi-Span Offshore Pipelines*, Research Report No. 2014-01, University of Oslo. Section 4.
4. DNV (2006) *Recommended Practice DNV-RP-F105: Free Spanning Pipelines*, Det Norske Veritas.
5. Dassault Systemes, *Abaqus Analysis User's Manual*.
