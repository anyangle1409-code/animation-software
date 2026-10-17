# ORIGINAL_v1 R38 — remaining arm-root marks

**Numerical checks passed. Owner visual review pending; not approved for production.**

R38 addresses the owner's 17 October marks on R37: the joint-like posterior upper-arm lobe at77%,69%, and broad rear bow at73%,32%, at135.625degrees. Only existing S7 coordinates at110/120/130/145degrees change. Frozen canonical skeleton, basis, topology, weights and every non-S7 key, includingHGPT_SHOULDER, matchR33/R34/R37 exactly. The156/166degree keys remain identical toR37/R34. Private reference photos are excluded.

The local skin target blends the rear outline toward an anchored chord and smooths the marked posterior patch. The raw target is scaled to45%, followed by material redistribution across both41-sample press paths. A local safety pass attenuates unsafe changes. A smooth0.75mm posterior shift through the lower junction preserves three-quarter continuity, followed by another safety pass. The original Blender guards remain unchanged. Final measurements use fresh native processes after saving.

## Measured R37 → R38

| Diagnostic | R37 | R38 | Result |
|---|---:|---:|---|
| Broad rear bow RMS, left/right, mm |9.575 /9.693|7.121 /7.385|Improved|
| Marked posterior surface residual p95, left/right, mm |2.715 /2.716|1.477 /1.501|Improved|
| Short rear corner, left/right, degrees |9.054 /10.004|11.371 /11.735|Worse; unchanged12.5degree limit passes|
| Short three-quarter corner, left/right, degrees |16.364 /52.736|18.916 /52.877|Worse; unchangedR34 limits35.408 /53.426 pass|
| Stretched triangles at135.625degrees |66|57|Improved|
| Front edge dihedral at130degrees |45.190|23.423|Improved; visible crease remains|

The new bow and posterior residual thresholds are local author goals, not proof of anatomical realism. R37 first reproduced four bilateral failures. Native final R38 passes both goals, every unchanged front/contour/guard/volume check, exact protection checks and no frame-count increases versus eitherR34 orR37 across41pressframes and all actual frames of13movement benchmarks. All82final native same-pose orientation comparisons have zero normal rotations over90degrees. No test was weakened or deleted.

## Remaining issues and tradeoffs

The native closeups show a straighter broad rear transition and reduced surface lobe, but a smaller junction crease remains visible. Short-corner diagnostics worsen as shown above. Top-of-press stretch remains80, and the shoulder-press benchmark still has two crushed triangles at its worst frame. The broader shape fits the oldR33 target less closely thanR34; versusR37 its whole-surface p99 error increases11.172→11.447mm at120degrees and11.433→12.024mm at145degrees. The protected front sentinel remains exactly0.0782/0.0912mm. These are not whole-patch errors.

## Evidence and reproduction

Candidate folder: `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r38_20261017/`. Model:`HGPT_ORIGINAL_V1_REVIEW_R38_CODEX.blend`. Native source commit:`0f830325e9572c65fdee32fe183610dff0013b39`; successful Blender5.2.1 run:`39017187577`; generated evidence commit:`c6821223ac133ad26c30f337a4388cf36ab75baf`.

`R37_R38_marked_angle_right.jpg` and its left counterpart compare the exact owner frame using unchanged native cameras. Full angle comparisons, bilateral junction/front sheets, press video, raw probe and reports remain alongside the model. `shoulder_press_r38_three_views.mp4` shows rear/front/three-quarter views.

Rebuild in a new candidate number using `.github/workflows/original-review-r38.yml`: export native response → staged solve → separate build with original guards → native identity/press/benchmarks/guard/orientation/front/contour/mark tests → matched renders and package. Existing candidates are immutable. The first full-gain target was rejected before saving a model; its failures and subsequent trials are retained in `docs/superpowers/plans/2026-10-17-r38-owner-marks.md`. No production assets, merge or force push.
