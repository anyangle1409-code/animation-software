# Saved-report localization — no model changes

This pass follows the completed preservation report. Samples below are normalized benchmark samples, not Blender timeline frame numbers. Runtime group names are copied literally; _l/_r are NOT anatomical-side proof. Counts are tessellation/density-dependent. Group classifications identify dominant skin-weight labels, not anatomical causation.

| Candidate | Path | Metric | Maximum | Sample index / t |
|---|---|---|---|---|
| V14 | shoulder_press | collapse_lt_0_1 | 149 | 8 / 1.0 |
| V14 | shoulder_press | stretch_gt_2 | 4261 | 6 / 0.75 |
| V14 | shoulder_press | self_intersecting_pairs | 586 | 8 / 1.0 |
| V14 | squat | collapse_lt_0_1 | 211 | 7 / 0.875 |
| V14 | squat | stretch_gt_2 | 1324 | 8 / 1.0 |
| V14 | squat | self_intersecting_pairs | 3036 | 0 / 0.0 |

V14 grip: unchanged solver raised no thumb placement within the pair limit. Full contact candidate geometry is not stored in the summary; failure is localized to the thumb-placement solver stage, not certified as a particular anatomical-thumb defect.

| R120 | shoulder_press | collapse_lt_0_1 | 329 | 6 / 0.75 |
| R120 | shoulder_press | stretch_gt_2 | 9171 | 6 / 0.75 |
| R120 | shoulder_press | self_intersecting_pairs | 969 | 8 / 1.0 |
| R120 | squat | collapse_lt_0_1 | 247 | 8 / 1.0 |
| R120 | squat | stretch_gt_2 | 3585 | 8 / 1.0 |
| R120 | squat | self_intersecting_pairs | 3750 | 0 / 0.0 |

R120 grip: unchanged solver raised no thumb placement within the pair limit. Full contact candidate geometry is not stored in the summary; failure is localized to the thumb-placement solver stage, not certified as a particular anatomical-thumb defect.

At v14 press t=1, top self-intersection labels include shoulder_cap_r (175), neck (155), shoulder_cap_l (148). At R120 press t=1: neck (497), shoulder_cap_r (152), shoulder_cap_l (150). At squat t=1, shin/thigh same-suffix pairs appear prominently (465 runtime _r pairs and443 runtime _l pairs in each candidate). These are dominant weight-label classes, not independently verified anatomical locations.

Both squat runs have maximum pair counts already at t=0, where collapse/stretch counts are zero. That makes neutral setup/contact applicability a required control before blaming flexion geometry. It does not erase the failure or establish that the adapter is wrong. No geometry, weights, correctives, poses in saved files or acceptance thresholds were changed.

Remaining: read-only pose views and actual triangle/vertex IDs are required for spatial localization. Left/right remains uncertified until independent landmark-orientation evidence is recorded. No attachments can begin without accepted source content, reviewed landmarks and user approval.
