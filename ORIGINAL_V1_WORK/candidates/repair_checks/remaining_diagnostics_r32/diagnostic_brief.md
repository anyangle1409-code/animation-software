# ORIGINAL v1 Phase 3 diagnostic brief

Candidate: r32 / `56205ee89a4bd5f8d5999ce64cf97f3b09a14876465af2c8fe7f382abf989295`

Evidence only. No edit is authorised. This brief contains no visual review images.

| Pose / side | Before close (mm) | After close (mm) | Closing delta (mm) | Contact vertices |
|---|---:|---:|---:|---:|
| curl_handle / l | 4.7119 | 5.9283 | 1.2164 | 172 |
| curl_handle / r | 4.712 | 5.9282 | 1.2162 | 172 |
| pullup_bar / l | 4.7119 | 5.9283 | 1.2164 | 172 |
| pullup_bar / r | 4.7119 | 5.9284 | 1.2165 | 172 |

See JSON for exact pre/post deepest vertices, weights and measured handle frames.
Pre-close penetration does not prove a causal diagnosis or permission to change a frozen structure.

## pushup_bottom / hand / max

Measured ratio: 1.911918; development limit: 5; coarse failure: False.
Inspection vertex IDs: 2381, 2391, 2393, 3903, 3913, 3915, 9207, 9211, 9225, 9246, 9281, 9284, 12268, 12272, 12286, 12305, 12341, 12344, 15805, 15807, 15861, 17345, 17347, 17401.
Read `docs/work_packages/PHASE_3D_WRIST_PUSHUP.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / pelvis / max

Measured ratio: 7.559296; development limit: 5; coarse failure: True.
Inspection vertex IDs: 1441, 1442, 1443, 7370, 7372, 7373, 7375, 7376, 7378, 10434, 10436, 10438, 14883, 14884, 14885, 16423, 16424, 16425.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / torso / min

Measured ratio: 0.120208; development limit: 0.15; coarse failure: True.
Inspection vertex IDs: 309, 341, 342, 374, 4910, 5004, 5005, 5008, 5068, 5072, 5135, 5138, 13672, 13704, 13705, 13737, 13738.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## lunge / torso / max

Measured ratio: 7.200494; development limit: 5; coarse failure: True.
Inspection vertex IDs: 260, 292, 324, 356, 4954, 4955, 4956, 4957, 4959, 5035, 5036, 5038, 5099, 5102, 13655, 13656, 13687, 13688, 13720.
Read `docs/work_packages/PHASE_3E_HIP_LUNGE.md`. Inspect coordinates, weights and mirror-edge rows in the JSON; record a separate bilateral permitted edit mask before any repair.

## Required continuation

Preserve R2, r28, r29 and direct-parent comparisons. Run focused checks, full 15-pose evidence and mesh/weight audits for every NEW repair candidate. Publish actual review images; pending review does not stop safe work.

Source references:
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r32/grip_penetration.json` / `873cd60dd0e6434de996155f3a304ee4f0418637e6c1918373f1cb8328306138`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r32/edge_extremes.json` / `b09c2776e21d29e9c5b588e268dfc7acedc8318a394b92842589c5a0742c194c`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r32_merged_pose_report.json` / `f12456d58bab99d861dfd5bedd3bb24edebfe3ca5cda13987f378e1e6763d960`
- `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json` / `79e9fe78f2acc23e7dd045c80d8d40a85f152c951d49055dfdd6ae5d4d4b6e95`
- `scripts/pose_test_original_v1_o4_candidate_blender.py` / `0f65d66e511c7b8102a4490e488485e63370de991dfef5a8bc448bf8cdd02935`

- Inspection IDs are not an edit mask or correspondence proof.
- A single candidate probe cannot prove weight independence or distinguish rest/pose/frame/geometry causes.
- Development-clear edge rows can still contain strict R2 regressions; use all committed comparisons.
- No model, weights, rig, poses, handle frames, baseline or thresholds are changed.
