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

## CP1a SC-anchor evidence search (no value found; recorded to avoid repeat searches)

- **Literature (search snippets):** no accessible bilateral SC-centre separation was found. Li 2012 (PMID 22340551, 53 volunteers) measured "the distance between bilateral clavicles" but the value is not in the abstract. Whole-manubrium width is available (male 58.2 ± 5.55 mm, Iranian CT, n = 98; 53.2–57.1 mm, Dutch CT, n = 49) but is **not** an SC-centre breadth and must not be substituted.
- **Open models:** `opensim-org/opensim-models` (GitHub) contains no clavicle model; the listed models are Arm26, Rajagopal, gait and leg models, and Wrist. The models with an SC joint (MoBL-ARMS, Saul 2015; Seth thoracoscapular 2019) are distributed via SimTK, which this environment's network policy blocks.
- **Status:** the CP1a blocker stands. Next accessible route: the full text of Li 2012, or a SimTK download made on the owner's laptop.

## Third pass: endplate clearance checker and glenoid rim frame

| Item | Independent check | Result |
|---|---|---|
| `scripts/anatomy_fit/endplate_clearance.py` | Analytic derivation, plus brute force on 2,000 random plane pairs and footprints (24k samples on the boundary and filled ellipse per case). | **Correct.** The minimum differs from brute force by at most 2.0e-6 mm (sampling resolution). The reported witness point gives the minimum gap exactly (8.5e-14 mm), and the `separated_everywhere` flag never disagrees. Scope (planar, projected +Z gap, common footprint) is as documented. |
| `scripts/anatomy_fit/glenoid_rim_frame.py` | Index mapping read (LM15–18 = p[14..17]; anterior = LM17 − LM16; superior = LM18 − LM15; normal forced lateral). Then an **anatomical** check GPT did not run: a Friedman-like version and an inclination, measured against the rim-centroid → LM5 (medial border) axis in the LM5/LM7/rim-centroid blade plane, for all 45 raw males. | **Anatomically plausible.** Version is −6.7 ± 5.6° (retroversion) and inclination +5.0 ± 4.5° (superior). Both fall in published normal ranges: version about 0 ± 10° with a retroversion tendency, inclination around 8°. This independently supports GPT's rim-landmark semantics and the outward-normal sign. GPT's own `normal_anterior_projection_deg` (+11.9°) is measured against the LM5→LM25 spine axis, so it is a different angle, and it is correctly labelled as non-clinical. |

## Fourth pass: source duplicates, lumbar edge heights, hyoid (offline; primary sources unreachable)

The journal hosts (Wiley/Hindawi, PMC and Europe PMC, Crossref) were unreachable from this session, so none of these checks re-reads a primary table. They test the committed data for internal consistency, arithmetic and geometric feasibility. The related tests pass: `test_anatomical_source_identity`, `test_anatomical_source_statistics`, `test_canonical_hyoid_geometry` and `test_canonical_lumbar_wedge_decomposition`.

| Item | Independent check | Result |
|---|---|---|
| `canonical_source_identity_review_v1.json` | A fresh scan of all 106 records in `canonical_proportion_sources_v1.json`. It uses union-find over DOI, PMID, **PMCID** and any DOI or PMID embedded in the text, plus fuzzy citation matching. | **A fifth duplicate group was missed.** `BARRÔCO_2011_332_NORMAL_FEET` and `METATARSAL_RELATIONSHIPS_332_NORMAL_FEET` share `PMC4799308`, cite the same title and carry identical male values (M1–M5 125.4/127.8/123.4/114.2/99.5 mm; forefoot width 87.1 mm). `source_identity.py` ignores `pmcid`. As a result, 25 of the 36 "missing identifier" records actually have a PMCID. Only 11 have no identifier at all: ANSUR II, OpenSim, Australian forearm, the four sternum records, Trotter–Gleser, the forearm standard, Reinhold and Crawford. The other two shared PMCIDs (Holcombe 2023, Panjwani 2020) are already grouped through their PMID. The foot audit cites only the Barrôco ID, so nothing is double counted today. Fuzzy-title pairs (for example King 2014 against Panjwani 2020, or the three metatarsal-stature papers) are distinct papers. |
| `canonical_lumbar_edge_height_crosscheck_v1.json` | SD bound and physical-sign checks. | **The L1 posterior SD quarantine is correct.** For n = 46 values within 20–30 mm, the largest possible sample SD is 5 × √(46/45) = **5.06 mm**, so the printed 26.3 is impossible. It also equals the printed mean, so it is probably a copied column. Its value stays null. The other signs are physically consistent: L1–L2 bodies are posterior-taller (thoracolumbar wedge) and L4–L5 are anterior-taller; disc anterior gaps exceed posterior gaps at every level and grow caudally (8.9 to 14.4 mm). The other SDs cannot be bound-checked without their printed ranges. I agree with GPT that supine edge gaps must not become standing centre spacing. |
| `canonical_hyoid_geometry_targets_v1.json` | Plausibility of the BB′/CC′ mapping, and geometric feasibility of the 2025 spans. | **The mapping is plausible but unverified at source.** A body height of 11.3 mm (SI) and an AP thickness of 7.0 mm suit a flat, plate-like hyoid body; the old 11.32 mm "AP length" would not. **New constraint for CP3:** the three greater-horn spans cannot all hold with straight horns. A straight horn's lateral coordinate is linear along it, so a centre span of 39.65 mm and a posterior-end span of 35.32 mm would put the horn origins 2 × 39.65 − 35.32 = **43.98 mm** apart. That is wider than the 42.85 mm lateral-most width, which is impossible. Any hyoid geometry built from these targets therefore needs curved (inward-turning) greater horns, or must declare which span it keeps. |

Suggested for GPT:
- add `pmcid` (normalised as `PMC` plus digits) to `identity_groups` and regenerate the review; this should give 5 alias groups and 11 identifier-less records;
- record the straight-horn infeasibility in the hyoid target before CP3.
