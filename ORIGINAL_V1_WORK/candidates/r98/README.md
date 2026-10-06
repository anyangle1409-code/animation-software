# r98: axillary rest-slit repair (weights-only, NOT accepted)

| | |
|---|---|
| Candidate | `HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r98.blend` |
| SHA-256 | `89e98cc74cc7dfd17f6d5a0991a9f0f6954e8de4d99ea3d3b30be2ec617b2ce0` |
| Parent | r97 `8b2fbe50…962f`. GPT failed it; it is kept unmodified. r98 is rebuilt from the r95 reconstruction with r97's mechanics. |
| Declaration | `repair_preparation/r98_axillary_support_declared/` (commit c7c55a8b, before any edit) |
| Status | **BLOCKED** by the author's self-review. Production approval is false. Awaiting GPT validation. |

## Changes

- **Skeleton:** none. r97's AC-joint pivot and half-swing helpers are kept exactly.
- **Topology:** none. Support rings were declared, built and measured, and they made both collisions and stretch worse (`repair_checks/r98_support_topology_screening`). No edge flow was justified by the evidence.
- **Rest shape:** the 2 cm armpit slit is opened (trunk wall 8 mm, arm wall 6 mm) and its sharp V apex rounded. 1086 vertices move by at most 10.7 mm. Every shape key gets the same delta.
- **Weights:** a localized re-skin, using r97's solver on the new rest shape within 2 rings of the edited vertices and blending over 3 rings into r97's weights. Non-declared bones keep r95's weights exactly.
- **Correctives:** none fitted.

## Results

Weights-only, 56-pose matrix:

| | r95 | r97 | r98 |
|---|---:|---:|---:|
| Protected-zone self-intersection pairs | 1931 | 1536 | **708** |
| Minimum edge ratio | 0.031 | 0.078 | 0.078 |
| p99 edge ratio | 3.25 | 3.16 | 3.18 |
| Maximum edge ratio | 4.09 | 4.45 | 4.33 |

Repository pose test, self-intersection pairs (r95 / r97 / r98):

| Pose | r95 | r97 | r98 |
|---|---:|---:|---:|
| press_top | 58 | 4 | **0** |
| press_top_rhythm | 72 | 0 | **0** |
| squat_bottom | 82 | 99 | **76** |
| pullup_hang | 0 | 8 | **0** |
| pullup_hang_rhythm | 0 | 0 | **0** |
| pullup_top | 92 | 110 | **92** |
| press_bottom | 80 | 84 | **80** |

No pose regresses against r95 or r97 on self-intersections.

Stretched edges (ratio above 1.6) are still above r95 on overhead and press poses, for example press_top: 853 (r95), 1104 (r97), 1134 (r98). r95's lower count comes with a crushed shoulder: at press_top it has 286 compressed shoulder edges against r98's 68.

## Still failing

The overhead visuals look unchanged from r97:
- **SH-V02:** axillary membrane and crease.
- **SH-V01:** rear deltoid dent.
- **SH-V05:** back creases.
- **SH-M03:** protected-zone self-intersections are still not zero (708). The remaining pairs are concentrated at the posterior axilla, the top of the shoulder and the overhead anterior fold.

The rest-slit repair fixes collisions at low and mid elevation. It cannot change the overhead sheet, because the remaining defect is in the deformation mechanism: a linear blend across the half-swing helper spans the opened fossa.

**Next causal layer:** connected soft tissue for the axillary folds. Add declared anterior (pectoralis major lower border) and posterior (latissimus/teres) fold helper bones that run from their trunk origin to the humeral insertion, with stretch and partial-follow constraints, so the folds become rounded bands rather than a blended sheet. This needs a new declaration. Correctives should not come before it.
