# R39 — rejected: straight outline, worse front crease

Native Blender 5.2.1 run39022461257 built this isolated candidate. **REJECTED_NUMERIC_CHECKS; not approved.** R38 and all protected production/canonical assets remain unchanged.

| Measurement | R38 | R39 |
|---|---:|---:|
| Maximum arm-line error, left/right (mm) | 17.517 /17.433 | 1.148 /1.122 |
| Inward body-join deficit, left/right (mm) | 25.196 /26.415 | 0.240 /0.202 |
| Front crease at130°, right (degrees) | 23.423 | 102.267 |
| Old R33 target fit, p99 at120° (mm) | 11.447 | 19.716 |
| Old R33 target fit, p99 at145° (mm) | 12.024 | 26.792 |

The straight outline passed, but the unchanged front test failed. The new anchor taper already produces an82.812° front crease in the raw target; area/orientation safety cannot bound dihedral smoothness. R40 will add explicit front-quality control. No test was weakened or deleted.

There were zero measured frame-count regressions against R34/R38. Both original guard baselines, all82 native orientation comparisons, preservation, R37contour/R38mark tests and the new line test passed. Front anchors and S7 endkeys156/166 remained exact; every non-S7 key (including HGPT_SHOULDER), basis, topology, weights and skeleton passed preservation. The first pre-save trial was blocked when guards moved an anchor; native contact separation resolved that issue before this saved attempt.

Top-press stretch80 and the two crushed benchmarktriangles remain open. Whole-surface fit to the old R33 target worsened as shown; max errors also increased24.585→33.777mm at120° and22.044→40.382mm at145°.

Evidence: `ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r39_20261017/` contains the immutable model, JSON measurements, test logs, matching R38/R39 images and `shoulder_press_r39_three_views.mp4`. The exact marked-angle comparison is `r38_r39_marked_135625_r.jpg`.

Reproduction: `.github/workflows/original-review-r39.yml`. Execution ledger: `docs/superpowers/plans/2026-10-17-r39-approved-arm-line.md`. Private owner photos are excluded.
