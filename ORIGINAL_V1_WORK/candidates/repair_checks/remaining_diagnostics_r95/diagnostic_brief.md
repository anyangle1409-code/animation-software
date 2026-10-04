# ORIGINAL v1 Phase 3 diagnostic brief

Candidate: r95 / `8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd`

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

Measured ratio: 4.038957; development limit: 5; coarse failure: False.
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
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r95/grip_penetration.json` / `ead69e6f159210acb5eddb2db03ef56c848b501dec6710479d7c3965f45443b3`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r95/edge_extremes.json` / `8302d28488234ce6b632abadf431edded61d542f511a0bfe911e07cd03a5e2f5`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r95_merged_pose_report.json` / `c65a7e67ea38bd69b9edfbed1868d7f941d5e3c453f0a5e00f90cb122914932d`
- `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json` / `79e9fe78f2acc23e7dd045c80d8d40a85f152c951d49055dfdd6ae5d4d4b6e95`
- `scripts/pose_test_original_v1_o4_candidate_blender.py` / `78a5da50a63fcf7f63a5b7be42e919949c75e4e2a08b7887379c112fb81e12d3`

- Inspection IDs are not an edit mask or correspondence proof.
- A single candidate probe cannot prove weight independence or distinguish rest/pose/frame/geometry causes.
- Development-clear edge rows can still contain strict active-epoch regressions; use the machine-selected immutable epoch baseline plus committed lineage comparisons.
- No model, weights, rig, poses, handle frames, baseline or thresholds are changed.
