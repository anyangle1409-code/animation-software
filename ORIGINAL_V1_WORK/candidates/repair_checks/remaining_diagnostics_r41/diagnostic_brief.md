# ORIGINAL v1 Phase 3 diagnostic brief

Candidate: r41 / `19a3f9b4581693df103d5740bb0e3b03c4ad39d7f09a9898959894746803a94f`

Evidence only. No edit is authorised. This brief contains no visual review images.

| Pose / side | Before close (mm) | After close (mm) | Closing delta (mm) | Contact vertices |
|---|---:|---:|---:|---:|
| curl_handle / l | 0.0 | 1.6271 | 1.6271 | 269 |
| curl_handle / r | 0.0 | 1.6271 | 1.6271 | 269 |
| pullup_bar / l | 0.0 | 1.6267 | 1.6267 | 269 |
| pullup_bar / r | 0.0 | 1.627 | 1.627 | 269 |

See JSON for exact pre/post deepest vertices, weights and measured handle frames.
Pre-close penetration does not prove a causal diagnosis or permission to change a frozen structure.

## pushup_bottom / hand / max

Measured ratio: 4.114655; development limit: 5; coarse failure: False.
Inspection vertex IDs: 2378, 2387, 3900, 3909, 9220, 9222, 9238, 9240, 9276, 9277, 12279, 12281, 12297, 12299, 12335, 12338, 15837, 15838, 15840, 17377, 17378, 17380.
Read `docs/work_packages/PHASE_3D_WRIST_PUSHUP.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / pelvis / max

Measured ratio: 4.57336; development limit: 5; coarse failure: False.
Inspection vertex IDs: 1441, 1442, 1443, 7369, 7370, 7372, 7373, 7375, 7376, 7378, 10434, 10436, 10438, 14882, 14883, 14884, 16423, 16424, 16425.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / torso / min

Measured ratio: 0.185026; development limit: 0.15; coarse failure: False.
Inspection vertex IDs: 309, 341, 374, 375, 4910, 5004, 5005, 5008, 5068, 5069, 5135, 5138, 5201, 13672, 13704, 13705, 13738, 13770.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / torso / max

Measured ratio: 3.903947; development limit: 5; coarse failure: False.
Inspection vertex IDs: 244, 260, 292, 324, 576, 4908, 4911, 4954, 4955, 4957, 4959, 5002, 5035, 5038, 5603, 13640, 13655, 13656, 13671, 13688.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## Required continuation

Preserve R2, r28, r29 and direct-parent comparisons. Run focused checks, full 15-pose evidence and mesh/weight audits for every NEW repair candidate. Publish actual review images; pending review does not stop safe work.

Source references:
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r41/grip_penetration.json` / `0f6b2ff418da697a460723007408dca4202395d37344bad5fd0707cf2020aeb3`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r41/edge_extremes.json` / `dbe2391a639ad13b24502edbac23bbe61e9883e470052c7d863359b8287728b0`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r41_merged_pose_report.json` / `74978cf41db29d3893e5611aed60ffd0372a329600dac65bbfe459d6f3264f7d`
- `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json` / `79e9fe78f2acc23e7dd045c80d8d40a85f152c951d49055dfdd6ae5d4d4b6e95`
- `scripts/pose_test_original_v1_o4_candidate_blender.py` / `0395264b92af74a8c1eefca612499be5104ae0d25567c38f3ea4a8af114ed23e`

- Inspection IDs are not an edit mask or correspondence proof.
- A single candidate probe cannot prove weight independence or distinguish rest/pose/frame/geometry causes.
- Development-clear edge rows can still contain strict R2 regressions; use all committed comparisons.
- No model, weights, rig, poses, handle frames, baseline or thresholds are changed.
