# Claude independent review of GPT skeleton-first evidence — 8 October 2026

Scope: items from `docs/CLAUDE_WORK_SKELETON_INSPECTION_HANDOFF_20261008.md`, checked on branch head `78a4c38c` (GPT head `c956b25c` plus the test fix below). Read-only on all evidence files. No gate is promoted, and `freeze_ready` stays false.

| Check | Result |
|---|---|
| Report reproducibility tests (glenoid rim, scapular landmarks) | **Defect, fixed in `78a4c38c`.** Both required bit-identical floats and failed on this machine by one final digit. They now use `scripts/report_compare.py` (exact structure; floats within relative 1e-9). A 0.01% value change still fails. |
| Scapular landmark model recomputed from the raw workbook | Reproduces `canonical_scapula_measured_landmark_model_v1.json` with no differences. Groups: 45 males (42 with stature) and 34 asymptomatic males (33 with stature). |
| Distal rib source curves recomputed | Reproduces `rib_distal_source_mean_curves_v1.json` with no differences. |
| Forearm report builder | **Reproducibility gap.** `canonical_target_selection_v1.json` names `scripts/anatomy_fit/build_forearm_target_report.py` as the builder of `canonical_forearm_ansur_direct_report_v1.json`, but the script emits a smaller schema, so the committed file cannot be regenerated from it. Shared values agree: predicted radiale–stylion 278.14 mm, residual SD 10.78 mm, a003 short by 30.7 mm (z −2.85). The 95th residual percentile differs slightly (18.970 vs 19.008 mm, a percentile-method difference). Fix: make the builder emit the committed schema, or name the true generator. |
| Lumbar body/disc decomposition (item 5) | **No double counting.** Recomputed independently from the P1 frames: superior slopes step by exactly each segmental angle (S1 40.9° to L1 −15.5° = 56.4° lordosis), and body wedge + disc wedge equals the source superior-to-superior angle at every level (L1/L2 1.34°, L2/L3 6.59°, L3/L4 10.16°, L4/L5 14.18°, L5/S1 24.12°). Body wedge signs are plausible (L1 −4.06° and L2 −1.28° kyphotic; L5 +8.01° lordotic); discs are all lordotic. Cross-cohort provenance remains as documented. |

Full suite after the fix: 742 tests, the same 9 inherited production/recovery failures (unchanged).

## Second pass: handoff items 2, 3, 4 and 7

| Item | Independent check | Result |
|---|---|---|
| 2 Scapular landmark semantics | Mean landmark positions recomputed from the raw workbook in GPT's frame; all 125 subject IDs unique (no repeated person); 45 males. | **Consistent.** LM5 lies at the medial border, 120.6 mm from LM25, the most medial spine point. LM14 lies 91.7 ± 4.6 mm lateral to LM5 near the glenoid neck, so it is genuinely distinct. LM11 is 12 mm from LM5, a separate nearby point. The anterior axis sign is confirmed by an independent cue: the coracoid landmarks LM22/LM23 are the most anterior points. Male glenoid rim: 38.9 mm superior–inferior and 31.7 mm anterior–posterior. Table 1 of the paper was not reachable, so landmark names were not re-read from the source. |
| 3 2022 source semantics | Male raw-data dimensions against the 2022 cohort (94 men, 165 cm). | **Consistent with GPT's semantics.** d1 (tubercle-to-tubercle, 44.8 mm) is longer than the articular rim (38.9 mm), as expected. d2 is 33.1 against an anterior–posterior rim of 31.7 mm. AA to medial spine is 127.9 ± 7.6 mm in men of 178 cm, against d3 113 ± 6.6 mm at 165 cm, which is consistent after scaling. LM3–LM7 is 165.1 mm against d4 159.4 ± 11.7 mm. **Confirms GPT's a003 finding:** a003 AA–TS is about 227 mm, against 128 ± 7.6 mm here, so the a003 scapula is far too wide. |
| 4 Clavicle definitions | Read `canonical_clavicle_endpoint_crosscheck_v1.json`. | **Policy sound.** The three definitions are kept separate, and their order is physically consistent: centre chord 152.9 < extremal chord 154.8 < curved length 166.8 mm. One weakness: the Qiu SD (9.3 mm) is over 52 bilateral bones from 26 men, so it understates between-person uncertainty. There is no stature adjustment and the cohort is Chinese (flagged by GPT). |
| 7 Carpal projections | Re-derived the conversion; mirror and mutation probes. | **Correct.** For projected sagittal and coronal angles the direction is proportional to (tan coronal, tan sagittal, 1), and the basis signs (left radial +X, palmar −Y) are right. The left/right mirror is exact (error 0). The validator rejects an all-proximal stub and a left/right swap. The transcribed source angles themselves could not be re-read (journal blocked). |

Still open: item 6 (rib proximal Eq 2.18, source blocked for both agents) and item 8 (a003 recheck, which is Claude's own earlier evidence and was not re-reviewed by Claude).

## Follow-up: forearm report provenance (closed by test)

`canonical_forearm_ansur_direct_report_v1.json` has no generator. `build_forearm_target_report.py` writes a different file (`canonical_forearm_target_report_v1.json`, never committed) with a smaller schema, and the extra sections were added by hand in `4a7c96a0`. `canonical_target_selection_v1.json` therefore misnames its builder. Rather than rewrite GPT's file, `scripts/test_forearm_direct_report_provenance.py` now recomputes every number in it from the committed ANSUR II file:

- the radiale–stylion regression (slope, intercept, prediction, residual SD, mean, ±1 SD);
- the a003 comparison (proxy, difference, z, empirical percentile);
- all six supporting regressions.

All of them match to relative 1e-9. The committed residual percentiles use NumPy's **'lower'** percentile method (default 'linear' gives p95 19.008 instead of 18.970 mm). That was undocumented and is now recorded in the test. Injecting two value changes makes the test fail.

Suggested for GPT: correct the `direct_ansur_report_builder` reference in `canonical_target_selection_v1.json`, and report the Qiu clavicle SD as per-bone (52 bilateral bones, 26 men).
