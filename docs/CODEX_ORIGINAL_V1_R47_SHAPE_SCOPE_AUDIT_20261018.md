# R47 shape/scope investigation — no geometry candidate created

Status: READ_ONLY_DIAGNOSIS_COMPLETE; proposed broader skin scope awaits owner confirmation. No R47 blend, deformation, render, fitting workflow or candidate has been created.

## Owner target

On18October the owner re-supplied the older rear-view reference and explicitly rejected the R46 arm/body relationship: "This is the shape I want. Not what you have given me." Preserve newer elbow/distal-arm details while matching the overall arm-to-torso relationship. Skeleton, V assets and HGPT_SHOULDER remain frozen.

## R46 result

Run39135213833, evidence commit5c9fb322d7e29cf0916ccef05f78296f13f6cd18, artifact12143583474 SHA256faca558c7e1f4d0733a1a47aec4ebd456c929f2b050a66e9f68000f4ecf8e4c3. No saved model. The150-minute fit timed out (exit124) after five accepted iterations. All83 native responses and13 benchmarks passed, but all six previously failing junction measurements still fail: left3.867/3.099/2.323mm and right3.797/3.118/2.248mm versus minima20/12/6mm. Motion excess0.447695mm and crease excess1.818881deg, slightly worse than R45 but within unchanged0.5mm/2deg limits. Simply extending time did not materially resolve the shape.

## Confirmed scope obstruction

The fitter's free mask preserves upper-arm source coordinates. A read-only audit reconstructs the exact full-press frame25 affine response and intersects all projected mesh edges with horizontal rows of the existing512px rear camera. At six sampled rows180..230 on BOTH sides, every active coordinate of the outline edge endpoints is fixed. All12 records have maximum response to the free coordinates exactly0 and current increment exactly0mm. Consequently a correction restricted to that domain cannot move those outline edges inward. This is a structural obstruction, independent of fitting time.

Example left edge endpoints: row200=(2144,19169), row210=(15575,19050), row220=(8712,21318), row230=(15557,21317). Full bilateral certificate: ORIGINAL_V1_WORK/anatomy/audit/r47_scope_20261018.json.

Reproduce from the retained R46 artifact:
```
python scripts/audit_original_review_r47_scope.py /tmp/r46-response/source.npz /tmp/r46-response/solved.npz /tmp/r47_scope.json
```
The script asserts all12 zero-response certificates. It does not write or install any geometry.

## Whole-outline discrepancy

Inspection of the full-body R42 and R46 native frames reveals that R42's outward body-fill target adds a broad lower-back bulge. An approximate2D alignment of the owner's unchanged upper head, checked against the unchanged waist, shows the owner's side outline farther inward below the arm roots. Neighboring135.625/138.952-degree frames both retain this broad discrepancy. This is screen-space evidence, not a verified3D anatomical target or an exact pose match.

A private overlay was prepared for owner review, explicitly labelled as a guide over unchanged R46 geometry. Neither the reference photo nor its traced outline is committed to this repo.

## Proposed next scope — requires the owner's large-change confirmation

Allow local shoulder-side/proximal upper-arm skin and upper-flank skin to change together, retaining the elbow and distal upper-arm details, frozen skeleton, all protected asset families and all existing safety checks. Start with a short static native contour study and show full rear and three-quarter comparisons before any further long fit. The precise editable mask and displacement bounds must be documented and tested before that study is built.

The old R42 profile test encodes an outward-fill interpretation that conflicts with this newly checked full reference outline. Keep that test and its failures unchanged as historical evidence; do not silently remove it from acceptance or loosen its thresholds. Before a new candidate is accepted, explicitly resolve the target-policy change with the owner and document a replacement full-outline requirement. Area/contact/orientation, motion, crease, benchmark, frozen-skeleton and protected-key tests remain mandatory.

No production data, previous candidate, existing test or test limit was edited in this investigation.
