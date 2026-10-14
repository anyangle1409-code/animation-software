# ORIGINAL_v1 review candidate R4: the shoulder rebuilt on the anatomical scapula (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.**
- **Owner instruction (14 Oct):** "Yes, do all four including lowering the pivot."
- **Root cause it addresses:** `docs/CLAUDE_SHOULDER_DETACHED_ARM_ROOT_CAUSE_20261014.md`.
- **Unchanged:** a003, the production rig and Work's coupled-motion file; R1–R3 stay as they were.

## What R4 is

**Parent:** C5 (feet). R4 does **not** inherit R1–R3's W3A helper or S1 keys. Those were tuned to the old, wrong-way
scapula, and on the corrected motion they are not needed.

| # | Change | Where |
|---|---|---|
| 1 | Scapula oriented by the profile's ISB angles in its landmark frame, relative to the thorax | `scripts/original_v1_shoulder_r4.py` (runtime, via `drives.setup`) |
| 2 | Blade glides on a thorax ellipsoid fitted to the rib/sternum guides (see below) | same |
| 3 | New shoulder weights (see below) | baked into the R4 blend |
| 4 | Arm pivot: `upperarm_<s>` head moved to the anatomical GH-centre landmark, 52.6 mm lower (tail/elbow unchanged) | baked into the R4 blend |
| — | K1 keys re-solved on this base: knee 90/110/130, elbow 90/110, wrist extension 60/80/100 | baked |

**Change 2, scapulothoracic contact:**
- **What is held:** the medial border (TS) and inferior angle (AI) keep their rest distances to the ellipsoid.
- **Solver:** damped least squares over three small extra motions:
  - blade internal rotation, which wraps the blade around the chest (weakly penalised);
  - clavicle protraction (strongly penalised);
  - clavicle elevation (strongly penalised, to prevent a shrug).
- **Result:** 0–2° of extra clavicle motion, about 15° of extra wrap, and 16–23 mm of residual lift-off at 160°.

**Change 3, shoulder weights:**
- the scapula's influence fades from 10 to 18 cm from the AC joint, with the rest going to the thorax;
- 60 % of the deltoid cap's clavicle/scapula weight moves to the upper arm, ramped from 2 cm medial to 8 cm lateral of the AC joint;
- 10 Laplacian smoothing passes over the changed region, then a maximum of 4 influences.

**File:**
- `ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r4_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R4_CLAUDE.blend`
- Built by `scripts/build_original_review_candidate_r4_blender.py`; report `r4_build.json`.
- It is still a 67-bone file, with `scene["hgpt_shoulder_drive"] = "R4"`. The basis mesh is unchanged, and only the two upper-arm bones moved.

## How it got here (every variant measured; rejected ones kept out)

| Variant | Result | Verdict |
|---|---|---|
| Anatomical scapula, rotating about the AC joint only | arm attached, but the blade lifts 91–117 mm off the back at 160° | needs contact |
| Contact against the rib tubes, clavicle only | 25–30° shrug (tubes are not a surface; landmarks fall between ribs) | rejected |
| Contact on the thorax ellipsoid, clavicle only | still a 19–28° shrug | rejected |
| Contact with blade wrap + free clavicle protraction | creases between the shoulder blades | rejected |
| **Contact with blade wrap, clavicle held near the profile** | no shrug, faint line only | **selected** |
| Weights: 2–5 cm ramp, unsmoothed | sharp posterior-deltoid crease at 90° (18–74 upper-arm self-pairs at 80–100°) | rejected |
| **Weights: −2–8 cm ramp, 0.6, 10 smoothing passes** | crease gone (0 pairs at 80–100°) | **selected** |
| "No-leak" smoothing (no new arm weight on trunk skin) | no measurable effect | not used |

## Results

**Coupled 0–160° sweep, today (C5) → R4** (collapse / stretch > 2 / pairs / volume %):

| HT | Today | R4 |
|---|---|---|
| 60 | 0 / 52 / 0 / +3.2 | 0 / 14 / 0 / +0.6 |
| 80 | 0 / 238 / 0 / +2.6 | 4 / 30 / 0 / +0.3 |
| 100 | 0 / 366 / 0 / +0.8 | 2 / 48 / 0 / −0.4 |
| 120 | 2 / 424 / 0 / −1.4 | **16** / 70 / **2** / −1.4 |
| 140 | 40 / 432 / 132 / −3.6 | 18 / 76 / 108 / −2.4 |
| 160 | 42 / 400 / 444 / −5.0 | 36 / 78 / 216 / −3.2 |

- **Improvements:**
  - stretch falls 80–95 % at every angle from 60°;
  - the 140–160° collapse, pairs and volume loss all improve;
  - visually the arm is attached at every angle (`closeups/`, x-ray sheets).
- **Retained cost:** mid-range collapsed faces, 2–16 at 80–120°, against 0–2 today.
- **Arm vs scapula:** the arm now turns 119° relative to the scapula at 160°, against 162° before.

**All 13 benchmarks** (`r4_validation.json`), worst frame collapse / stretch / pairs, with R3 for reference:

| Benchmark | a003 | R3 | R4 |
|---|---|---|---|
| Shoulder press | 48 / 438 / 462 | 4 / 542 / 106 | 36 / **78** / 218 |
| Squat | 26 / 56 / 371 | 28 / 56 / 227 | 28 / **12** / 227 |
| Bent-over row | 2 / 0 / 156 | 2 / 2 / 9 | 2 / 2 / **116** |
| Lunge | 0 / 57 / 84 | 0 / 57 / 0 | 0 / 37 / 0 |
| Single-leg stance | 0 / 53 / 42 | 0 / 53 / 0 | 0 / 33 / 0 |
| Deadlift | 38 / 76 / 455 | 38 / 78 / 319 | 38 / **22** / 319 |
| Push-up | 12 / 64 / 196 | 2 / 72 / 50 | 1 / 61 / 52 |
| Trunk rotation | 0 / 7 / 0 | 0 / 7 / 0 | 0 / 0 / 0 |
| Grip, walk, calf raise, forearm, wrist | — | — | ≈ R3 (grip pairs 22 → 26) |

**Regressions against R3, retained and not hidden:**
- **Shoulder press:** more collapsed faces (4 → 36) and pairs (106 → 218). R3's lower counts came from the W3A helper, at the cost of a detached-looking arm (stretch 542).
- **Bent-over row:** the back of the upper arm passes into the side of the chest (`spine_03`/upper arm, 46 pairs per side). With the anatomical pivot, the arm swings back closer to the trunk.
- **Volume:** the minimum is 1.1–1.3 points lower in the deadlift, push-up and grip.

## Evidence

- `sequences/`: all 13 benchmarks, a003 vs R4 (filmstrips + GIFs).
- `ORIGINAL_V1_WORK/anatomy/audit/claude_shoulder_rootcause_20261014/skeleton_xray/`: skeleton under the skin, today vs R4.

## Tests

`scripts/blender_tests/test_original_review_candidate_r4.py`, 5 native tests (CI: `original-review-candidate-r1.yml`):
- **Identity:** the SHAs and flags.
- **Bones:** only the upper-arm heads moved, each exactly onto the GH landmark (52.6 mm lower).
- **Weights:** normalised, at most 4 influences.
- **Live drive:** the blade stays within 30 mm of the thorax with no shrug (< 5° extra clavicle elevation); the glenoid rises; arm-vs-scapula stays < 125°; both sides mirror.
- **Sweep vs today:**
  - less stretch at every angle from 60°;
  - fewer pairs and collapses and less volume loss at 140–160°;
  - the mid-range cost is asserted, so it stays visible.

## Next

1. **Row arm–chest contact:** a K1-style contact key for the upper arm against the lateral chest, driven by shoulder extension.
2. **Posterior-axillary curl at 140–160°:** the remaining press pairs and collapses.
3. **Mid-range (80–120°) collapsed faces.**
4. **Upstream:**
   - Work/Lane G to adopt the anatomical-frame scapula drive in the coupled motion (PR #26);
   - shipping R4 also needs the canonical upper-arm pivot change and the K1 morphs (runtime contract; owner + Lane G).
