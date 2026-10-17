# R41 — bounded press strain redistribution

Numerical checks pass; **owner visual review pending**. R40 and R41 remain review candidates. The saved model is immutable, and nothing is promoted to production.

| Saved native measurement | R40 | R41 |
|---|---:|---:|
| Stretched triangles at 135.625° |45|19|
| Stretched triangles at 166° |80|53|
| Maximum crushed triangles, shoulder-press benchmark |2|0|
| Worst triangle area/rest-area ratio, 83 samples |12.4083|11.2847|

Stretch means area/rest-area>2; crushed means<0.1. All 41 dense benchmark samples are free of crushed triangles after guards. There are 0 triangle-count regressions against R34/R38/R40 across the measured press frames and 13 movement benchmarks. Native contact scans find 0 new contacts; final orientation and count/severity checks pass at 82 path samples plus exact 130°.

The straight-arm measurements at 135.625° remain 1.148 mm (left)/1.122 mm (right), with body inward deficits 0.2422/0.2032 mm, all below the unchanged 2mm limits. Both 130° front-crease peaks remain below 25°:23.122° left and 23.628° right. Both front sentinel coordinates remain exact. Bones, Basis, topology, weights and all non-S7 keys, including HGPT_SHOULDER_*, pass preservation checks. Canonical and V-series assets were not edited.

R41 authors local increments at the 7 existing bilateral S7 elevations 110/120/130/136/145/156/166. The earlier 5 controls have zero influence at the top/crushed poses, so 156/166 must be editable for this task. **Intentional R41 test-scope change:** replace its inherited end-key freeze with an independently measured 0.75mm saved-key bound. The immutable R40 freeze tests remain unchanged. Actual maximum saved S7 update is 0.699988 mm; end keys 156/166 changed. The solve uses smooth area energy, adjacency regularization, exact line/anchor constraints and native contact separation; the original Blender guards are unchanged.

Measurements that worsened are retained in `r40_r41_measurement_comparison.json`:

| Metric | R40 → R41 |
|---|---|
| Right front crease 130° |23.0197° → 23.6280° (+0.6083°)|
| Left three-quarter corner 135.625° |7.6763° → 8.6655° (+0.9893°)|
| Rear corner, left/right |1.6242°/1.6086° → 1.6280°/1.6300°|
|120° target-fit maximum |33.7540 → 33.7933mm|
| Target points over 5 mm at 120°/145° |2702/2957 → 2704/2958|
|156° target-fit p99 |1.0132 → 1.0437mm|
|166° target-fit p99 |0.1209 → 0.3131mm|
| Body inward deficit increase, left/right |+0.00021/+0.00073mm|

Remaining work includes 53 stretched triangles at the top and the old R33-target mismatch: maximum 33.793mm at 120° and 40.310 mm at 145°. The marked silhouette and remaining folds still need owner visual assessment.

Reproduction: `.github/workflows/original-review-r41.yml`, native source `2e39ad099302915e78c789832a043b1f752b25f0`, successful [Blender 5.2.1 run 39044792091](https://github.com/anyangle1409-code/animation-software/actions/runs/39044792091). Model SHA256:`4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e`. Artifact 12106011330 SHA256:`45b4d4d687808775e53a7fd6c2b089d14cb628674bb2a04ca0631a7a69a181c9`; both artifact and model hashes were verified after download.

Additional final verification uses fresh saved-model native measurements, beyond the 9 summarized benchmark frames:

```bash
out=ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017
HGPT_R41_NATIVE_AREA="$out/r41_orientation.json" python scripts/tests/test_original_review_r41_final_strain.py
```

All 3 tests pass. The same test reproduces 3 expected failures on the native R40 baseline (`r40_native_area_baseline.json`); both RED/PASS logs are retained. This adds a stricter final dense-sample check and does not relax any prior test. The repository consolidated Blender suite, including archived R33 tests, also passes.

The [first native trial 39043230358](https://github.com/anyangle1409-code/animation-software/actions/runs/39043230358) was rejected for 14 new armpit contacts before any model was saved. Its evidence remains in artifact 12104914194. Separation and crushed-area energy weights were increased; the measured contact pairs are retained as constraints, with unchanged native scans. Details and review corrections are recorded in `docs/superpowers/plans/2026-10-17-r41-bounded-strain.md`.

Review media in the R41 candidate folder: `r40_r41_marked_135625_r.jpg` (and `_l`), `r40_r41_top_166.jpg`, `r40_r41_front_130_r.jpg`, full multi-angle comparison sheets, and `shoulder_press_r41_three_views.mp4` (8 seconds, 12 fps, 1536×576). All images show native Blender geometry with matched poses/cameras; no owner photos were used or committed. No main merge or force push.
