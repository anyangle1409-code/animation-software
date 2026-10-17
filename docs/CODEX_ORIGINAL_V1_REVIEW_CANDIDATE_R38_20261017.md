# ORIGINAL_v1 R38: the two remaining owner marks

**NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW. Owner visual approval pending.**

Parent: immutable R37. Owner feedback 17 October: remaining joint-like lobe at (77%,69%) in three-quarter and excess rear bow at (73%,32%), on the exact135.625-degree comparison. Private reference image is excluded.

R38 only changes existing S7 skin coordinates at110/120/130/145. The rear target blends the broad contour toward its anchored chord, capped at12mm; the posterior target blends a local quadratic surface capped at6mm. The front sentinel has a broad spatial protection fade. The raw target is scaled to45%, followed by coupled material-coordinate redistribution over both41-sample press paths. A local target attenuation safety stage then discards unsafe portions. A smooth0.75mm posterior blend through the lower junction preserves three-quarter continuity, followed by another safety pass. Final safety requires no extra stretch/collapse counts and no normal reversals versus the parent same-pose surface; it does not establish anatomical correctness. Endkeys156/166 remain exactly R37/R34. The original native guards are unchanged and must leave those endkeys untouched.

The local response trial increases the short rear corner peaks from R37 left9.0535/right10.0042 to approximately11.37/11.73degrees, while reducing the broader bow. This tradeoff must be checked again on the final saved model and visually reviewed. Both remain below the unchanged12.5degree goal.

All prior R34 front tests and R37 contour tests run unchanged. Two additional owner-mark goals require rear broad-bow RMS<7.5mm (R37 left9.5747/right9.6932mm) and local posterior quadratic-fit residual p95<2mm (R37 left2.7149/right2.7158mm), both at135.625degrees. These are local shape diagnostics, not substitutes for the owner's visual review. R37 reproduces all four expected failing side-goals before the change. A synthetic reversed triangle reproduced the unsigned-area blind spot and the new signed-area check passes after the correction. No prior test/tolerance was weakened or deleted.

Native checks: {"front_test_process": true, "original_lockout_volume": true, "original_guards_rechecked": true, "original_post95_collision_rule": true, "preservation": true, "no_frame_count_regressions": true, "new_contour_goals": true, "new_owner_mark_goals": true, "final_native_orientation": true}. Regressions retained: 0. Full measurements and logs are alongside the model. Numerical comparisons include R34 and R37 at every actual measured frame of the full press and13 benchmarks; every increase rejects the candidate.

Comparison files show R37/R38 at identical cameras and press times. The video is shoulder_press_r38_three_views.mp4. Bilateral native closeups include the exact135.625degree owner frame and front120/130/145degrees. The full-press top remains R37/R34; existing top stretch and crushed shoulder-press benchmark triangles are not claimed resolved by this local change. Broader fit to the old R33 target may worsen and is fully retained in r38_review.json.

Frozen canonical skeleton, basis, weights, topology and every non-S7 coordinate including HGPT_SHOULDER remain identical to R33/R34/R37. Workflow original-review-r38.yml uses pinned Blender5.2.1. No production assets, merge or force push.
