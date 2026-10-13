# Rejected standalone volume-skinning experiment — 13 October 2026

[Actual before/after front and rear phone sheet](https://chatgpt.com/api/library/files/libfile_0d0be283e6b88191b90fb65ee58709c3/download). Four1800×1400 shoulder-detail PNGs, same pose/cameras: [before front](https://chatgpt.com/api/library/files/libfile_d18361ce78e081919f89bce1faa4eba3/download), [after front](https://chatgpt.com/api/library/files/libfile_3fd4e68701f881919a0a08ba3a3a89bb/download), [before rear](https://chatgpt.com/api/library/files/libfile_152db577d1988191af32b480a85b727a/download), [after rear](https://chatgpt.com/api/library/files/libfile_ff6afe77924c8191b00eca0d9397db71/download). Shoulder crop excludes arm tips/legs; actual original full body is retained.

[Separate diagnostic BLEND](https://chatgpt.com/api/library/files/libfile_41b412abca1c819194db2fce5a6ecd89/download), [comparison report](https://chatgpt.com/api/library/files/libfile_548ab421843481919ad6122292eba654/download), [export hashes](https://chatgpt.com/api/library/files/libfile_b433c9d48d748191b91afa7781bc68bc/download). Signed-in owner downloads.

Input PR106 `codex/original-shoulder-joint-refit-20261013` full commit `f3d06591aeaff45d26d34af04b1cb19a2128af50`, actual `HomeGymPT_ORIGINAL_v1_SHOULDER_JOINT_REFIT_TRIAL.blend` SHA256 `a48ee389a064927f740b5ea294b7afed3ef1616cbe8ac6c121867b86581680c2`. New separate candidate `HomeGymPT_ORIGINAL_v1_SHOULDER_VOLUME_SKINNING_TRIAL.blend` SHA256 `91ac6b9845a7982e87c7fe0c44b114ee4382c7eb1720d1052ba2bdc29f648e09`. Original r95/a003 source SHA256 `670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56` is inherited unchanged; actual body17946vertices, copied67runtime, original67/206reference retained. Fitted source centres remain unverified; no original anatomical moves.

The intended deformation change is the copied body's native Armature modifier `use_deform_preserve_volume` false→true. Code review finds no mesh/weight/rig editing and source input bytes hash remains exact; there is no exhaustive output structural snapshot comparison, so this is not a proved all-field scene difference. This uses Blender dual-quaternion skinning, not realistic muscle simulation. It is not reproduced by ordinary linear GLB skinning; **no GLB exported or LaneG work changed**.

At the same authored160° reach in the same8660triangle upper-body region:

| Distortion diagnostic | Linear baseline | Volume trial |
| --- | ---: | ---: |
| Area ratio<0.1 triangles | 60 | 4 |
| Area ratio>2 triangles | 280 | 566 |
| Minimum area ratio | 0.009709 | 0.014285 |

The front-shoulder collapse guard now passes, but rear-shoulder guard FAILS (`test_rear_shoulder_does_not_collapse_below_tenth_area_at_authored_160`), so native current trial **3PASS/1FAIL**. The tenth-area guard is an engineering severe-collapse threshold, not anatomical validation. Worst rear triangle[4865,13619,4748] at rest approximately[0.1571,0.1084,1.5266]m blends scapula/clavicle/neck/upperarm. Volume preservation does not resolve the weight architecture.

Actual visual review finds excessive chest/shoulder bulges and fold-like transitions. **Rejected as a standalone correction.** No shape/motion/physiology/production acceptance. W4 must still refit shoulder/chest/axilla influences and author deliberate correctives, retaining both front/rear failure guards and checking stretch as well as compression. No further blind modifier/parameter sweep. Foot shape/28cm blocker and PR105 toe regression remain unchanged.

Eleven pure joint/bind tests PASS; native saved-candidate3PASS/1FAIL executed. Reports and per-export hashes in `docs/reviews/ORIGINAL_V1_SHOULDER_VOLUME_*_20261013.json`. CI pure/syntax only, not native model acceptance or inherited broad-suite success. Candidate and all images saved without replacing production. Continue from the actual source-joint trial, using this rejected experiment as evidence, not the chosen solution.
