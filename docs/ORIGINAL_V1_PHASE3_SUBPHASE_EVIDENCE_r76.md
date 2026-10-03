# Phase 3 sub-phase evidence for r76 (measured, 2026-10-03)

Status: EVIDENCE ONLY. Nothing here accepts a regression, changes a threshold or baseline, enters Phase 4 or approves production. Candidate r76 (SHA-256 `e484dd99907d88838a8ef3633dbbbc932db1a8dc12ae35a63f2df51a1ab3a8fd`), rig rev2c (67 bones / 66 deform, structure hash unchanged), stress poses P3a, active baseline P3B1.

| Sub-phase | Result | Evidence |
|---|---|---|
| 3A shoulder/axilla | gate clear; 15 of 24 owned rows regress strictly versus P3B1 (all inside every development gate) | `repair_checks/axilla_r76/p3b1_regression_attribution.md`, `phase3_subphase_evidence.md`, `si_r76.json`, `sidepth_r76.json` |
| 3B hands/fingers | 33 rows, 0 gate failures, 0 strict regressions, values identical to P3B1; finger-flexion audit flags none | `phase3_subphase_evidence.md`, `subphase_audits_r76/finger_flexion.json` |
| 3C grip/equipment contact | every bilateral row inside the gate: penetration 1.63 mm (gate 2.0, identical to P3B1), 269 contact vertices (gate >= 20) | `phase3_subphase_evidence.md` |
| 3D wrist | 0 gate failures, 0 strict regressions; push-up hand minimum edge ratio 0.24 versus 0.119 in P3B1 (improved) | `phase3_subphase_evidence.md` |
| 3E hip/pelvis/legs | 0 gate failures, 0 strict regressions (lunge pelvis max 4.573 and torso min 0.185 are inherited from P3B1 with gate margins 0.43 and 0.035) | `phase3_subphase_evidence.md`, `subphase_audits_r76/floor_contact.json` |

Whole-character checks (all corrections active simultaneously, 15 stress poses): 0 development failures; independent re-run reproduces every measured field exactly (`determinism_rerun_pose_test_report.json`, 0 differences); continuous joint kinematics shows no path discontinuity and finger flexion flags no joint (`subphase_audits_r76/`); floor contact is exact (toes and thumbs at z = 0 in the push-up, feet flat in squat/lunge/neutral); axial-twist stress worst edges forearm 0.93, thigh 0.91, shin 0.94, upper arm 0.50 (the known shoulder-blend case); rig structure hash and four forearm twist helpers verified.

## The only open Phase 3 item: strict shoulder regressions versus P3B1

All 23 strict comparison regressions are in the 3A shoulder zone or are shoulder-corrective side effects in poses where the arms move (squat, push-up). Mechanical attribution (`p3b1_regression_attribution.md`): 9 inherited from the anchored shoulder weights (the fix for the tent flaps that P3B1 contains), 8 inherited from the weights with a further contribution from the corrective, 4 added by the corrective, 2 in poses outside the shoulder set. Every value is inside the development gate (smallest margin 0.141); none meets the stricter production-target limits for self-intersections (P3B1 does not either).

Measured cause of the largest family (self-intersections, 102-132 face pairs per overhead pose versus 0-91): they are all shoulder-region pairs, mirror-symmetric, inside a posed box of about 5 x 10 x 5 cm at the top of each shoulder, and about 90 percent are clavicle-driven skin crossing upper-arm-driven skin (59 of 66 per side in the press top), median depth 1.5-1.7 cm and up to 4.8 cm. P3B1 had fewer because its lateral torso tented with the arm and its armpit web was torn open (r42: 326 torso vertices more than 10 cm from the trunk-driven position).

Attempts to resolve the crossing locally (preserved):
- r72/r73/r76 guarded local trials fixed every flipped/collapsed declared face (declared-face audit LOCAL_FACE_NUMERIC_CLEAR) but do not address the deep sheet crossing.
- r77 (collision-zone declaration `repair_preparation/r77_axilla_pit_declared/`, 264 left vertices) with a new anti-penetration barrier was REFUSED by the numeric pre-apply selection: the barrier took its rest-side reference from the rest pose, but at rest the arm underside and the shoulder-top skin are not facing each other, so about a third of the constrained pairs started on the "wrong" side and the solve distorted the surface (flips 8-116, edge stretch +0.33). No candidate was created.

What a correct resolution needs (not yet built): sidedness taken from physics rather than the rest pose (the arm-driven web belongs on the inner side of the clavicle-driven skin), for example offline collision relaxation per pose sample producing intersection-free target positions that the corrective is then fitted to, or a tri-tri signed-distance barrier whose side is taken from the last non-penetrating arc sample of the same pair.

## Phase 3 exit status

Blocked solely by `unresolved_regressions` (the 23 above). Development failures 0, grip, wrist, hand and hip evidence clear, determinism verified. Phase 4 preflight: PHASE4_BLOCKED (strict severity regressions remain; control does not select ENTER development freeze validation) - correct and unchanged.
