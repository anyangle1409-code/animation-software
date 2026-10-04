# ORIGINAL v1 Phase 3 diagnostic brief

Candidate: r81 / `fa95c0b4f6f4815202936639aa173f61fdc0db43837f8f0c40a7af95d74d2b0a`

Evidence only. No edit is authorised. This brief contains no visual review images.

| Pose / side | Before close (mm) | After close (mm) | Closing delta (mm) | Contact vertices |
|---|---:|---:|---:|---:|
| curl_handle / l | 0.0 | 1.6269 | 1.6269 | 269 |
| curl_handle / r | 0.0 | 1.6268 | 1.6268 | 269 |
| pullup_bar / l | 0.0 | 1.6269 | 1.6269 | 269 |
| pullup_bar / r | 0.0 | 1.6268 | 1.6268 | 269 |

See JSON for exact pre/post deepest vertices, weights and measured handle frames.
Pre-close penetration does not prove a causal diagnosis or permission to change a frozen structure.

## pushup_bottom / hand / max

Measured ratio: 4.020093; development limit: 5; coarse failure: False.
Inspection vertex IDs: 2378, 2387, 2406, 3900, 3909, 3928, 9220, 9238, 9240, 9271, 9272, 9273, 12279, 12297, 12299, 12331, 12332, 12334, 15837, 17377.
Read `docs/work_packages/PHASE_3D_WRIST_PUSHUP.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / pelvis / max

Measured ratio: 4.57336; development limit: 5; coarse failure: False.
Inspection vertex IDs: 1441, 1442, 1443, 7369, 7370, 7372, 7373, 7375, 7376, 7378, 10434, 10436, 10438, 14882, 14883, 14884, 16423, 16424, 16425.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / torso / min

Measured ratio: 0.185029; development limit: 0.15; coarse failure: False.
Inspection vertex IDs: 309, 341, 374, 375, 4910, 5004, 5005, 5008, 5068, 5069, 5135, 5138, 5201, 13672, 13704, 13705, 13738, 13770.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / torso / max

Measured ratio: 3.903947; development limit: 5; coarse failure: False.
Inspection vertex IDs: 244, 260, 292, 324, 576, 4908, 4911, 4954, 4955, 4957, 4959, 5002, 5035, 5038, 5603, 13640, 13655, 13656, 13671, 13688.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## Required continuation

Preserve the active immutable stress-pose epoch baseline (P3B1), direct-parent comparison and any specifically relevant committed historical controls. Do not hard-code R2/r28/r29 as current requirements. Run focused checks, full 15-pose evidence and mesh/weight audits for every NEW repair candidate. Publish actual review images; pending review does not stop safe work.

Source references:
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r81/grip_penetration.json` / `0db6c509c98a844d5242244ec86a64ef180cbb95f2325e707e34df955229b290`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r81/edge_extremes.json` / `c461e376084c2b3e4d8b4414e4901f306b6ae358e4f6fed8a162faa1ab709f30`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r81_merged_pose_report.json` / `84f8fc0bdfb38c1a43fa214cf558225d7fbb0c0295965cf4b2d994c14fc782c6`
- `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json` / `79e9fe78f2acc23e7dd045c80d8d40a85f152c951d49055dfdd6ae5d4d4b6e95`
- `scripts/pose_test_original_v1_o4_candidate_blender.py` / `3f429910dd129cbd0181f662ccacb726cf2410bf764bae5328a9adfadd59cb06`

- Inspection IDs are not an edit mask or correspondence proof.
- A single candidate probe cannot prove weight independence or distinguish rest/pose/frame/geometry causes.
- Development-clear edge rows can still contain strict active-epoch regressions; use the machine-selected immutable epoch baseline plus committed lineage comparisons.
- No model, weights, rig, poses, handle frames, baseline or thresholds are changed.
