# ORIGINAL_v1 consolidated review candidate R1 (Claude, 14 Oct 2026)

**Status: REVIEW CANDIDATE — NOT ACCEPTED, not production, not clinically validated.** One isolated, reversible blend that
combines the corrections each verified on its own branch. Frozen a003, the canonical bones and the V-series assets are
unchanged. Rejected trials are kept out.

## What R1 is

| Part | Source | In R1 |
|---|---|---|
| Feet | C5 (`claude/original-v1-foot-shape-20261013`): C3 280 mm foot skeleton, C4 toes + ball breadth 104.1 mm, C5 heel contact | parent blend (SHA `92f5b34e…`) |
| Shoulder | W3 option A helper (`deltoid_helper_<s>`), stateless mid-elevation reference drive, transfer 0.6, 4 smoothing passes, 4-ring edge taper, zone z > 1.22 m | vertex groups, weights and reference vectors |
| Knee | K1 contact keys at 90/110/130° | 6 shape keys |
| Elbow | K1 contact keys at 90/110° only (120/140 rejected: tip pinch) | 4 shape keys |
| Motion | H1 4° arm carriage, H2 solved thumb opposition, P4 families | benchmark/sequence scripts, not the blend |

**Excluded (rejected):** C3W toe crumple, K1 hip fold, the W3A rotation/swing drives, the K1 elbow 120/140 keys.

- **Files:**
  - `ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r1_20261014/HGPT_ORIGINAL_V1_CONSOLIDATED_REVIEW_R1_CLAUDE.blend` (SHA in `r1_build.json`)
  - built by `scripts/build_original_consolidated_review_candidate_blender.py`
- **Runtime drives:** `scripts/original_v1_review_candidate_drives.py`.
  - The saved rig keeps exactly **67 bones**, so the shared bridge guard accepts it.
  - `install_helpers()` recreates the two helper bones in memory (69 deforming joints).
  - `drive(rig, body)` must run after every pose. It sets the helpers to half the arm's rotation relative to the scapula, on the branch closest to the stored 120° reference, and drives the K1 keys from the measured hinge angle.
- **Build checks (PASS):**
  - basis, faces, legacy keys and the 67 bone rests are unchanged from C5;
  - weights changed only in the helper zone (1,162 vertices);
  - ≤ 4 influences per vertex; 10 K1 keys; no guide objects left.

## Validation against a003 (all 13 benchmarks, same motions)

`scripts/validate_original_review_candidate_blender.py` → `r1_validation.json`. The worst frame per benchmark:

| Benchmark | Collapse a003 → R1 | Stretch > 2 | Self-intersecting pairs | Volume % R1 |
|---|---|---|---|---|
| Squat | 26 → **28** | 56 → 56 | 371 → 227 | −4.3..+0.2 |
| Bent-over row | 2 → 2 | 0 → **2** | 156 → 9 | −2.9..+0.6 |
| Shoulder press | 48 → 4 | 438 → **634** | 462 → 110 | −2.0..+3.1 |
| Lunge | 0 → 0 | 57 → 57 | 84 → 0 | −1.6..+0.3 |
| Walk stride | 0 → 0 | 0 → 0 | 0 → 0 | 0..+0.3 |
| Trunk rotation | 0 → 0 | 7 → 7 | 0 → 0 | −0.3..+0.2 |
| Grip | 0 → 0 | 4 → **6** | 150 → 22 | +0.2 |
| Single-leg stance | 0 → 0 | 53 → 53 | 42 → 0 | −1.3..+0.3 |
| Calf raise | 0 → 0 | 0 → 0 | 0 → 0 | −0.2..0 |
| Deadlift (start) | 38 → 38 | 76 → **78** | 455 → 319 | −5.1..+0.3 |
| Push-up | 12 → **14** | 64 → **74** | 196 → 192 | −0.3..+0.2 |
| Forearm rotation | 0 → 0 | 0 → 0 | 124 → 0 | −0.6..−0.4 |
| Wrist circuit | 0 → 0 | 16 → 16 | 136 → 12 | −0.4..−0.3 |

**Reading:**
- **Clear gains:**
  - self-intersections fall in 10 of 13 benchmarks (K1 knee/elbow contact and the W3A shoulder);
  - the press's collapsed faces fall from 48 to 4, and its worst volume loss improves from −5.0 to −2.0 %;
  - the torn axillary flap of a003 at full press is gone (`sequences/shoulder_press_sequence.jpg`).
- **Regressions (bold), retained and not hidden:**
  - the press gains +196 stretched faces (the known W3A armpit stretch, with an armpit bulge and a posterior axillary web) and a +3.1 % local volume gain;
  - squat +2 and push-up +2 collapsed faces; push-up +10, deadlift +2, grip +2 and row +2 stretched faces.
- **Unchanged known defects:**
  - hip fold (deadlift and squat spine_01/thigh contact; no accepted corrective);
  - dorsal wrist crease at full extension;
  - the thumb does not fully wrap;
  - the K1 knee band edge;
  - toes tall in cross-section, no nails, faceted heel (feet).

## Evidence for iPhone

- `fullbody/`: a003 vs R1 front, rear, both sides, three-quarter front and rear.
- `closeups/`: shoulder at 160° (front, rear, side), knee 110°, elbow 100°, fist, medial foot.
- `sequences/`: per benchmark, a 1080 px filmstrip (three-quarter and side, t = 0 / 0.25 / 0.5 / 0.75 / 1), the a003 vs R1 peak frame and its metrics, plus a looping GIF.

## Tests

- `scripts/blender_tests/test_original_review_candidate_r1.py`: 6 native tests (CI: `.github/workflows/original-review-candidate-r1.yml`).
  - **Identity:** the SHAs and the PASS verdict.
  - **Saved file:** 67 joints with the helper data.
  - **Rest mesh:** equals C5.
  - **Drives at rest:** identity (rest mesh unchanged).
  - **Helper:** equals half of an independently tracked continuous arm rotation over 0–160°. It is bilaterally symmetric and never flips.
  - **K1 keys:** follow the knee and elbow hinge.

## What shipping it would need (owner + Lane G, PR #26)

R1 cannot ship under the current 67-joint contract. It needs:
- two extra deforming joints with the reference-branch drive;
- driven K1 morphs;
- the C3 foot skeleton decision.

Until then it is a review artefact only.
