# ORIGINAL v1 Phase 3 diagnostic brief

Candidate: r39 / `f08842fa1eb2714555c0a288dd166724ab20473d7b9ae2f030960bb36f6e24e3`

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

Measured ratio: 4.114594; development limit: 5; coarse failure: False.
Inspection vertex IDs: 2378, 2387, 2388, 3900, 3909, 3910, 9220, 9222, 9238, 9240, 9277, 12279, 12281, 12297, 12299, 12338, 15837, 15840, 17377, 17380.
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
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r39/grip_penetration.json` / `9b16e82e95dd9b2da12f93626ca8e2204cb7b3af6904b7c9c820fc21b35b918f`
- `ORIGINAL_V1_WORK/candidates/repair_checks/remaining_diagnostics_r39/edge_extremes.json` / `053def88c3363789f5c52a55e776246e9e22db696eae67233aaa9329d1938909`
- `ORIGINAL_V1_WORK/candidates/repair_checks/full_r39_merged_pose_report.json` / `e02c81289cdf85a700ce9be395522ce0d17e4f58da79f8c489b0fe51f595e6bb`
- `ORIGINAL_V1_DEFORMATION_ACCEPTANCE.json` / `79e9fe78f2acc23e7dd045c80d8d40a85f152c951d49055dfdd6ae5d4d4b6e95`
- `scripts/pose_test_original_v1_o4_candidate_blender.py` / `11b90fe43bb6dafcb634ce41167b4a1d0ea4b6231b3ddc2151dab6776385d981`

- Inspection IDs are not an edit mask or correspondence proof.
- A single candidate probe cannot prove weight independence or distinguish rest/pose/frame/geometry causes.
- Development-clear edge rows can still contain strict R2 regressions; use all committed comparisons.
- No model, weights, rig, poses, handle frames, baseline or thresholds are changed.
