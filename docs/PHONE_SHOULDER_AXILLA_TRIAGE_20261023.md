# Home Gym PT — shoulder/axilla deformation triage, phone-cloud lane

**Date:** 23 October 2026  
**Status:** READ-ONLY forensic plan; **NOT** anatomical approval or permission to alter a preserved model.

## Primary evidence

- Source: pinned Blender 5.2 native [read-only diagnosis run 39937882229](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229), three model evidence ZIPs. Each downloaded ZIP independently matched its published SHA256.
- Existing [failure localization](PHONE_NATIVE_SHOULDER_SQUAT_GRIP_LOCALIZATION_20261023.md), verified in [five-job cloud run 40019877883](https://github.com/anyangle1409-code/animation-software/actions/runs/40019877883).
- Newly committed `scripts/cloud_body_analysis/track_rest_hotspots.py` tracks the **same rest-space triangle IDs** at shoulder-press samples 0/6/8 and squat samples 0/7/8, verifies rest vertices and triangle index arrays are identical within each model/path, and reports 5cm rest-space concentration bins. Its new CI execution must be verified before the script's GitHub Actions results are treated as tested.

## Exact within-model signal from independently verified original ZIPs

| Model | Shoulder press newly stretched at sample6 relative to sample0 | Of those still stretched at sample8 | Squat newly stretched at sample7 relative to sample0 | Of those still stretched at sample8 |
|---|---:|---:|---:|---:|
| W8 | 3072 | 491 | 885 | 862 |
| V14 | 3550 | 699 | 1238 | 1210 |
| R120 | 7337 | 3025 | 3363 | 3345 |

**Interpretation:** Flags persisting over saved poses identify surface areas worth inspecting and testing first. Counts depend on topology, density and native metric definitions. They are **not** cross-model anatomical quality rankings, and not a claim that the same failing triangles persist between different models.

### Press: W8 newly stretched triangles at sample6

Top dominant weight-group corner proxies: `spine_03` (1208 triangle-corner equivalents), `shoulder_cap_r` (422), `shoulder_cap_l` (352.667), `scapula_r` (229.333), `scapula_l` (203), `upperarm_l` (157.667). These are recorded weight labels and not muscle-activation estimates.

Most populated 5cm **rest-space** cells (centre in body-object local metres) for newly stretched W8 triangles:
- `(+0.125,+0.175,1.475)`: 363
- `(-0.125,+0.175,1.475)`: 325
- `(+0.125,+0.175,1.425)`: 255
- `(-0.125,+0.175,1.425)`: 230

These four cells provide repeatable geometry-localization targets in rest pose; cell centres are not validated anatomical landmark coordinates.

W8 newly collapsed triangles at sample6 (relative to sample0): 110, with neck (25.333), clavicle_r (19.333), shoulder_cap_r (15.667), shoulder_cap_l (14.667) corner equivalents. Prior saved back-view overlay shows concentrated flagged areas around the posterior shoulder/upper-back junction. Rest-cell and label concentration **cannot distinguish causes** such as wrong surface shape, weights, skeletal transform, shape key or posing rules.

### Squat: W8 newly stretched at sample7

885 new; 862 remain at sample8. Top weighted proxies: hip_crease_r (249.667), hip_crease_l (239.333), spine_01 (148.333), pelvis (124.333); separate collapsed flags occupy shin/thigh proxy regions. This is a separate workstream; do not let shoulder changes silently alter pelvis/leg weights or lower-body acceptance.

## Next read-only diagnostic programme

1. **Source correspondence:** preserve W8, V14 and R120 exact SHA256 and inventory. Do not assume archived W8/v14 geometry is recovered exactly; V14 238065 vs archived 238067 remains failed.
2. **Triangulation identity:** compare only *within the same model and movement* after proving identical rest triangle array, rest coordinates and dominant-group labels. Never compare raw triangle IDs across W8/V14/R120.
3. **Physical viewing evidence:** review the existing front, back, side and three-quarter plain/overlay PNGs at press samples 0/6/8; correlate obvious posterior shoulder and axilla slits with rest-space 5cm cells and the saved flagged triangle IDs.
4. **Competing hypotheses:** (A) shoulder/scapula skin influences overextend into upper spine, (B) arm-elevation corrective shape activation produces local fold or sharp cap transition, (C) chosen authoring pose/kinematic bridge lacks appropriate scapula/clavicle motion, (D) mesh surface/underarm junction already contains pre-existing self-intersection. All are untested hypotheses, not established defects. A new read-only candidate analysis should separately quantify each parameter without relaxing acceptance thresholds.
5. **Laterality:** saved source rig labels `_r` often sit at positive body-local X; `_l` often sit at negative X. That numerical convention does not independently certify *anatomical* left/right. Do not bind new muscle IDs to them until landmark and camera orientation are independently reviewed.
6. **Sensitivity experiments only with explicit scope:** If separately authorized, run controlled **in-memory** A/B pose/corrective/weight sensitivity experiments on isolated reconstruction copies, output exact before/after hashes and deformation metrics, and never persist an edited .blend over an input. Do not call results repaired without all exercise gates.
7. **Acceptance:** require anatomical landmark evidence, both-side grip, new shoulder-press motion paths and complete sampled movement reports with unchanged collision/stretch/collapse thresholds; verify foot contacts and squat don't regress. No merge, release, app deployment or PT_MODEL_VERSION change.

## Strict boundaries

No production or original `.blend`, validated rig skeleton, PR124 muscle attachment or Claude branch changed. No inferred muscle anchor, skin weight fix, shoulder correction, or archived original reconstruction claim. All numbers are raw saved diagnostic signal at the specified pose positions, not clinical or anatomical certification.
