# Morning review pack: anatomical skeleton audit candidate a003 (7 October 2026)

Read-only renders of the **current, unchanged** audit candidate. Nothing in production was touched, and no new candidate (a004) was made for these images. The skeleton is **not** accepted as anatomically correct: Gates 6, 8 and 9 are not passed (see "Owner questions" and "Known defects").

## Identity

| Item | Value |
|---|---|
| Branch | `codex/whole-body-biomechanics-audit-20261007` |
| Rendered at commit | `fe91f3fbb9c154466b98d525b08be5715e14bc85` (the pack itself is committed on top of it) |
| Audit candidate | `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend`, sha256 `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56` |
| Fit record | `ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json`, sha256 `11712ba3…` |
| Source character | r95 BARE export `ORIGINAL_V1_WORK/candidates/exports/r95_phase4_freeze/HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_r95_BARE.glb`, sha256 `c4b8e388e624a4a3d22510b40c1fc45017b3374b1ff9de2cae79f2dbb0797c85`. It was exported from the r95 dev-freeze `.blend` `8a39a22d…` (not in the repository). r97–r102 were rejected, and no newer accepted revision exists. |
| Audit import | `audit/HGPT_ANATOMICAL_AUDIT_r95_a001.blend`, sha256 `0655dae1…` (receipt `audit/audit_copy_r95_a001_receipt.json`) |
| Pose source | `audit/HGPT_ANATOMICAL_AUDIT_r95_a003_isolated_tests_v14.blend`, sha256 `46db1e81…` (run `audit/runs/isolated_bone_only_014`) |
| Generator | `scripts/anatomy_fit/render_review_pack.py` (modes `views` and `poses`); per-file sha256 in `pack_manifest.json` |

## Contents (all current, generated from the files above)

How to read the images:
- **Views** show the r95 body in X-ray with the anatomical master bones, coloured by placement class: red = regression, orange = surface landmark, blue = surface station, grey = proportional (low confidence).
- **Green balls** are joint markers; **magenta balls** are the runtime rig's joint heads, for comparison.
- **Sides:** the character faces −Y, so anatomical **left = +X** (the viewer's right in front views).

| Group | Files |
|---|---|
| Full body | `views/full_front.jpg`, `full_back.jpg`, `full_left_side.jpg`, `full_right_side.jpg`, `full_front_left_three_quarter.jpg`, `full_front_right_three_quarter.jpg`, `full_back_left_three_quarter.jpg` |
| Left shoulder and axilla | `views/shoulder_axilla_left_front.jpg`, `_side.jpg`, `_rear.jpg`, `shoulder_left_overhead.jpg`, `axilla_left_from_below_front.jpg` |
| Right shoulder and axilla | the same five views with `right` |
| Poses | `poses/pose_neutral_front.jpg`, `pose_neutral_left_side.jpg`, plus measured peak frames of shoulder complex (117.5° GH), GH flexion plane (120°), hip flexion (130.4°), knee with patellar follower (90°), elbow flexion (144.6°), thumb opposition components, C0–C1 flexion (8.95°) and L4/L5 extension (12.1°). Frames and values are in `poses/poses_manifest.json`. |
| Contact sheets | `sheets/sheet_full_body_views.jpg`, `sheet_shoulder_axilla_left.jpg`, `sheet_shoulder_axilla_right.jpg`, `sheet_poses_neutral_and_movement.jpg` |

**Pose renders are bone-only.** The body mesh is not skinned to the anatomical master, so there is no deformation to show. The spinal pose renders hide the upper-limb sticks so the spine is visible. Shoulder deformation (the rejected r97–r102 work) is out of scope for this pack.

## Movement clips (existing evidence, linked, not re-rendered)

| Clips | Status |
|---|---|
| `../audit/review/isolated_clips_005/` (19 GIFs: hip, knee, ankle, subtalar, GH, elbow, forearm, wrist, digit, C1–C2, C4–C5, T6–T7, L4–L5, TMJ, shoulder complex, screw-home) | **Current.** Run-006 test file; command authoring for these tests is unchanged through run 014. The C4–C5 clip shows the former ±5° TEST AMPLITUDE; that test now uses sourced 8.0°/7.9°. |
| `../audit/review/isolated_clips_007/` (C0–C1, C3–C4, rib 4, index and little-finger spreading, thumb opposition components, knee with patellar follower) | **Current.** Run-012 test file; these specs are unchanged in run 014. |
| `../audit/review/isolated_clips_006/` | **Stale.** It shows the superseded thumb opposition (37° added to rest, overshooting 61.2°). |
| `../audit/review/isolated_clips_001/` … `_004/` | **Stale.** They predate the sign-defect fixes. `isolated_clips_001/lumbar_l4_l5_extension.gif` actually shows flexion. Kept as history only. |
| `../audit/review/master_a002/` | **Superseded fit** (elbow axis tilted 23°). |
| `../audit/review/master_a003/` | Same candidate as this pack (earlier render set). |

## Test results (current)

| Check | Result |
|---|---|
| Isolated Blender sweeps, run 014 (`audit/runs/isolated_bone_only_014`) | **135/135 integrity PASS**, none unmeasured. Angle error ≤ 5.6e-5°, centre drift ≤ 1.9e-7 m, distal-marker primary lever ≥ 11 mm, fixed-axis radius constant within 3.6e-7 m. |
| Left/right mirror, run 014 | 41/41 pairs PASS on reflected world transforms of every commanded bone, followers included. 2 hip-rotation pairs are covered by an exact solver mirror test only. |
| Recorded failing runs (gate development, kept) | 005, 008, 010, 011, 013 |
| Blender toolchain smoke (`audit/runs/blender_smoke_002`) | 22/22 PASS |
| Master static capture (`audit/runs/master_static_003`) | Structure PASS (coverage 206/206, identity, geometry, bone scale). Placement and joint operation UNVERIFIED by design. |
| Unit tests | `scripts/test_anatomy_fit.py` 23/23; `scripts/test_blender_anatomical_validation.py` 28/28 |
| Whole repository | 601 tests, with the **same 9 inherited failures/errors** as before this work (ORIGINAL v1 production-control/orchestration tests; untouched) |
| Independent reviews | 3 read-only reviews. Every material finding was re-measured and fixed (see the findings document). |

## Known defects and limitations (unresolved items stay unresolved)

**Runtime-rig findings** (production unchanged; recorded only):
- F-SIDE-001: runtime `*_l` bones sit on the anatomical right.
- F-GH-001: the runtime GH sits above the acromion skin, about 53 mm above the fitted GH, which two open models corroborate.
- F-HJC-001: the runtime thigh head is about 30 mm above the fitted HJC, which ANSUR trochanterion −8 mm corroborates within 2 mm.
- F-SCAP-001: the runtime scapula head is a pivot, not an AC marker.
- F-HAND-001: runtime fingertips lie 1.5–5.4 mm outside the skin.

**Fit limitations:**
- F-SPINE-001: thoracic level anchors conflict by about 1.7 levels.
- F-HEAD-001: no ears, so skull frame landmarks are estimates.
- F-FOOT-001: long feet; one runtime toe bone.
- F-EXPORT-001: a stray icosphere in the export.
- F-HJC-002: the stored trochanterion landmark is a boundary artefact (affects only the unselected Davis method).
- F-RIB-001: straight fitted ribs make the rib-neck axis degenerate, so only a pump-handle component is tested.
- 115 proportional bone placements are low confidence.

**F-PROP-001 (reclassified):**
- The femur/humerus stature-check failures are method bias. The same chain on 4,082 ANSUR II men gives −6.4 cm and −9.7 cm, and the character sits at the 26th and 20th percentiles.
- The authored forearm and hand are genuinely short (z −2.2), and the radius follows them.
- The stature check remains recorded as FAIL.

**Unsourced, therefore untested or not applied:**
- spine and ribs: L1/L2, C2/C3, C7/T1, ribs 8–12;
- shoulder: SC elevation (sources conflict), rhythm plane dependence;
- foot and leg: first TMT, naviculocuneiform, calcaneocuboid, lesser toes, patellar translation path, fibular rotation;
- hand: wrist stage split, thumb pronation magnitude and the TMC/MCP/IP flexion needed to complete opposition.

**Never modelled:** contact rolling/sliding, moving centres of rotation, capsular translation, and rib–sternum coupling.

**Phase 10 (functional exercises)** is not started: Gate 9 has not passed, and the atlas has no task kinematics.

## Owner questions

1. Are the authored body's **short forearm and hand** (acromion-to-fingertip z −2.2, about the 1st percentile for 1.82 m), **long feet** (z +2.8) and **broad shoulders** intended styling? Changing the body is a production change and would need a new audit fit.
2. The runtime side naming (F-SIDE-001) and the runtime GH and hip pivots (F-GH-001, F-HJC-001) are production decisions for any later runtime-rig work (Phase 11).

## Evidence paths

| Topic | Path |
|---|---|
| Live tracker | `docs/COMPLETE_HUMAN_SKELETON_LIVE_TRACKER_20261007.md` |
| Findings and verification (all per-finding records) | `docs/COMPLETE_SKELETON_FINDINGS_AND_VERIFICATION_20261007.md` |
| Handoff and resume instructions | `docs/BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md` |
| Fit record and review addendum | `ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json`, `character_fit_r95_a003_review_addendum.json` |
| Proportion investigation | `ORIGINAL_V1_WORK/anatomy/audit/proportion_audit_001/` (`character_surface.json`, `proportion_report.json`) |
| Sources | `ORIGINAL_V1_WORK/anatomy/sources/ansur2/ANSUR_II_MALE_Public.csv`, `sources/open_musculoskeletal_models.json`, `phase9_supplementary_observations.json`, `whole_body_movement_atlas.json` |
| Isolated runs | `ORIGINAL_V1_WORK/anatomy/audit/runs/isolated_bone_only_001` … `_014` (current: `_014`) |
| Toolchain | `ORIGINAL_V1_WORK/anatomy/blender_toolchain_verification_20261007.json`, `audit/runs/blender_smoke_001`, `_002` |
| Scripts | `scripts/anatomy_fit/` (fit, master build, solver, isolated tests, runner, renderers, proportion audit), `scripts/test_anatomy_fit.py` |

GitHub view: `https://github.com/anyangle1409-code/animation-software/tree/codex/whole-body-biomechanics-audit-20261007/ORIGINAL_V1_WORK/anatomy/review_pack_a003_20261007`
