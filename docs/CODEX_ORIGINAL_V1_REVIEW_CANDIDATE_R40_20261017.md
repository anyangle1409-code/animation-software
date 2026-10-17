# R40 — straight arm-to-body line with front crease control

**NUMERIC_CHECKS_PASSED_AWAITING_VISUAL_REVIEW. Owner visual approval pending.** Built and tested in Blender 5.2.1, native run39039784992, source83720d43; preserved model commitc7b71bbc. R39 remains immutable and rejected.

R40 retains the owner-approved straight upper-arm edge into the body. It adds an explicit front-dihedral penalty to the local S7 material solve because area/count safety alone allowed R39’s sharp front fold. The authoring baseline remains immutable R38. Only S7 controls110/120/130/136/145 are authored; the136control preserves parent interpolation before correction. The skeleton, basis, topology, weights, every non-S7 key(including HGPT_SHOULDER), front anchors and156/166endkeys pass preservation.

| Saved-model measurement | R38 | R39(rejected) | R40 |
|---|---:|---:|---:|
| Arm-line max error L/R(mm),135.625° |17.517/17.433|1.148/1.122|1.148/1.122|
| Inward body-join deficit L/R(mm) |25.196/26.415|0.240/0.202|0.242/0.202|
| Front130° crease L/R(degrees) |23.065/23.423|90.678/102.267|23.147/23.020|
| Three-quarter short corner L/R(degrees) |18.916/52.877|8.510/35.406|7.676/37.045|
| Marked press frame: triangles stretched>2× |57|46|45|
| Top press: triangles stretched>2× |80|80|80|
| Old R33 target fit p99 at120°(mm) |11.447|19.716|19.729|
| Old R33 target fit p99 at145°(mm) |12.024|26.792|26.781|

The unchanged R34/R38 acceptance baselines show zero frame-count regressions. **Versus rejected R39**, five press samples have1–2 additional stretched triangles, and three shoulder-benchmark samples have one additional stretched triangle. No collapse or collision count increases versus R39 were measured. The right three-quarter corner worsened35.406→37.045°, while remaining below the unchanged53.427° limit. The left front crease increased slightly23.065→23.147° versus R38. Old R33 whole-surface target fit remains worse than R38; max errors are33.754mm at120° and40.368mm at145°. This is retained as a tradeoff for owner review, not hidden by the new line goal. Full per-sample increases are in `r39_r40_measurement_comparison.json`.

All original front, contour, mark, strict-volume, collision, guard and preservation gates passed. The original R39 line test runs unchanged. Added tests require bilateral front crease<=25° and preserve the existing2mm line goal. Native orientation passes all82 original path samples plus the added exact130° front pose; native BVH preflight also checks the added pose. No existing test was weakened or deleted. Independent code review found no Critical/Important issue; derivative and complete native-matrix-chain tests passed. The final original guards preserve the anchors and endkeys exactly.

**Still open:** top-press stretch80; shoulder-press benchmark collapse count2 at t=.875 and1 at t=1. Other inherited target-fit errors remain recorded. Numerical success does not replace owner review.

Candidate folder: `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r40_20261017/`. Review media:

- `r38_r40_marked_135625_r.jpg` and `_l.jpg`: requested rear/three-quarter angle, same cameras.
- `r39_r40_marked_135625_r.jpg`: previous-version comparison at the same angle.
- `r39_r40_front_130_r.jpg`: front crease before/after.
- `shoulder_press_r40_three_views.mp4`:8-second native press video.
- Native test logs, build/report/measurement JSON, pre-guard BVH diagnostics and immutable `.blend` model.

Reproduction: `.github/workflows/original-review-r40.yml`. Execution ledger: `docs/superpowers/plans/2026-10-17-r40-front-smoothness.md`. Work stays on `claude/original-v1-consolidated-review-20261014`; no merge or force push. Private reference photos are excluded.
