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

## CP2 preflight checker (new tool, owner request)

`scripts/anatomy_fit/cp2_preflight.py` (tests: `scripts/test_cp2_preflight.py`, 13 tests, mutation-checked) runs the whole-skeleton hard invariants the CP2 plan asks for. It works on any candidate in the fit-record schema, which is what the CP3 builder consumes. It is read-only and invents no anatomical tolerance: gates are identity, finiteness, sign and strict `> 0`.

- **Checks:** 206 bone identities against `adult_bone_inventory_206.json`; finite coordinates (a null target counts as a FAIL, never a fill); no zero-length bone; the parent tree (acyclic, each articular parent joined by the named inventory joint, hyoid without an osseous parent); anatomical left = +X; 427 joint identities; proper joint frames (orthonormal, det +1); distinct SC/AC/GH centres per side; a positive centre-line disc gap C2/C3–L5/S1; full endplate clearance via GPT's `endplate_clearance.py`, which is UNVERIFIED until endplate surfaces exist. Bilateral asymmetry is measured only.
- **Ledger:** for each readiness region, it lists readiness, blockers, unselected (null) targets, bones and the a003 placement classes.

**Baseline run on a003** (`audit/runs/claude_cp2_preflight_a003_001/`): verdict **FAIL**, with 8 PASS, 1 FAIL, 1 UNVERIFIED and 1 INFO.
- The FAIL is the known zero-disc-gap defect, measured on all 22 levels from C2/C3 to L4/L5 (the gap is exactly 0.00 mm). L5/S1 is positive.
- The tool confirms the structural integrity of a003: 206 bones, 427 joints, proper frames and correct sides. Bilateral asymmetry is at most 0.38 mm.

**New finding from the ledger:** `humerus_left` and `humerus_right` are not covered by any region in `canonical_freeze_readiness_v1.json`. The text of every readiness region also omits the sternum, coccyx and ossicles (the ledger files these under ribs, spine and head as bookkeeping). The humerus matters because its length is one of the open F-PROP-001 proportion questions. Suggested for GPT: add humerus (and sternum) entries to readiness, or state where they are tracked.

## Open-data search for the three BLOCKED regions (ribs, carpus, tarsus)

**Reachable:** only public GitHub (git clone and raw files). **Blocked:** SimTK (Brown/Crisco Open Source Carpal Database, 90 subjects), the Brown Digital Repository copy, Zenodo (foot-bone shape-model meshes, RibSeg v2 rib centrelines), BodyParts3D's own server, Figshare, OSF, Hugging Face and the journal hosts. GitHub had no population dataset for these bones. `M3DV/RibSeg` is code only; its data is on Zenodo. **Laptop candidates:** the Open Source Carpal Database (simtk.org/projects/carpal-database), Zenodo record 3464747 (tarsal and metatarsal meshes) and RibSeg v2. These are population datasets that could actually unblock regions.

**What was usable:** BodyParts3D 4.0 (CC BY 4.0, one adult male reference anatomy), as packed in `ashemag/human-atlas` at commit `1c38bf35`. `scripts/anatomy_fit/bodyparts3d_crosscheck.py` produced `ORIGINAL_V1_WORK/anatomy/bodyparts3d_single_specimen_crosscheck_v1.json`, covering all 16 carpals, 14 tarsals and 24 ribs. Each bone has its volume centroid, volume, principal axes and extents; each rib has a geodesic centreline. The mesh files' SHA-256 hashes are recorded. The output is deterministic, and the tests are in `scripts/test_bodyparts3d_crosscheck.py` (8 tests, including synthetic box and curved-tube checks). **Status: SINGLE_SPECIMEN_LAYOUT_CROSSCHECK_NOT_A_TARGET.** One specimen is grade D: it supports layout plausibility and frame/contact topology and **unblocks no region by itself**.

| Check against GPT's registered evidence | Result |
|---|---|
| Rib end-to-end span vs Holcombe 2017 Table A1 Sx (n = 1,659 per level) | The specimen lies within ±1 SD for ribs 3–12 and at +1.3 to +2.2 SD for ribs 1–2; left and right agree within 5 mm. **The specimen is a plausible ribcage.** For contrast, a003's straight rib chords are z +2.1 to +2.4 at ribs 3–5 and **−3.0 at rib 11**, which independently supports F-RIB-001 and the rib rebuild. |
| Carpal volume order vs Patterson 1995 | Same order except one adjacent swap: the specimen's triquetrum (1,019 mm³) is larger than its trapezoid (785 mm³). Identical on both sides. |
| Tarsal volume order vs GPT's tarsal hierarchy | Consistent: calcaneus > talus > cuboid > medial cuneiform > navicular > lateral > intermediate cuneiform. |
| Calcaneus and cuboid length | 77.7 mm against 75.2 mm (SEA CT), and 34.6 mm against 33.7 ± 2.6 mm (z +0.4). Consistent. |
| **Talus length (ZHANG_2018_TALUS_MALE)** | **Suspect source mapping.** The registered "talus_length" is 44.4 ± 2.9 mm and "talus_width" is 54.4 ± 2.7 mm, so width exceeds length. The specimen's whole-talus extents are 58.5 × 40.5 × 35.8 mm (z +4.9 against the registered length). The source is a *superior talar dome* study, so its length and width are probably dome-specific, or transposed. Recheck PMC6057431 before using either value as whole-talus scale. |
| **Canovas 2004 carpal spacing ratios** | **Normaliser is unclear.** With the capitate's first principal extent (23.7 mm) as "capitate axis", the specimen gives 85% and 43%, against the source's 157.6 ± 8.4% and 91.4 ± 7.3% (z −8.7 and −6.7). The specimen's actual centroid distances (capitate–triquetrum 20.1 mm, hamate–triquetrum 10.0 mm) both fit the source ratios if the normaliser is about **11–13 mm**, not the capitate's full length. Reading it as full length would put the capitate and triquetrum centroids about 37 mm apart, wider than the carpus. Check Canovas's definition of the capitate axis before these ratios become constraints. |
| Asseln 2024 carpal envelopes | Not interpretable. Sorted principal extents against sorted source box sides give z −4 to +0.7. Principal extents and anatomical-axis bounding boxes are different measures, and the source axes are unmapped. Recorded, not concluded. |

**Suite note:** the full suite gives 766 tests with the same 9 inherited failures plus **one environment-only failure**. GPT's `test_rib_spiral_reconstruction.test_export_is_reproducible…` compares floats exactly: with numpy 2.4.6, 13 floats differ by at most 8.6e-15 (relative), and `report_differences` finds none. It is the same brittle pattern as the two tests fixed in `78a4c38c`. **Fixed at the owner's request:** the test now uses `report_differences` (relative 1e-9). The suite is back to the 9 inherited failures, and a 0.01% change to a stored value is still caught.

## Same specimen: spine discs, shoulder girdle and hyoid

`scripts/anatomy_fit/bodyparts3d_axial_shoulder.py` produced `ORIGINAL_V1_WORK/anatomy/bodyparts3d_single_specimen_axial_shoulder_v1.json`. It is deterministic, and its tests are in `scripts/test_bodyparts3d_axial_shoulder.py`. The specimen is the same single BodyParts3D male, **grade D**, with status SINGLE_SPECIMEN_LAYOUT_CROSSCHECK_NOT_A_TARGET.

| Item | Specimen | Against | Reading |
|---|---|---|---|
| Disc spaces C2/C3–L5/S1 (23) | Every level has a positive centre bone-to-bone gap (3.1–13.3 mm). Planes fitted to the real endplates also give a positive projected clearance at every level when run through GPT's `endplate_clearance.py`. | — | **The CP2 endplate-surface input works end to end.** Fed into `cp2_preflight.py`, the specimen's surfaces make `disc_endplate_clearance` PASS at all 23 levels. With a003's bone sticks, the centre-gap check still FAILs (tested), so surfaces cannot mask a zero gap. |
| Disc heights (mean of posterior, centre and anterior ray) | Cervical 3.9–4.5 mm; thoracic 3.3–6.9 mm; lumbar 5.0–11.9 mm (L3/L4 only 5.0) | Stack candidates: cervical z −1.6 to −2.7; lumbar z −2.4 to +1.9 | **Not useful for heights.** The specimen's discs are irregular (illustration-refined), and the definitions differ (radiographic vs ray thickness). Several posterior rays miss the thoracic disc meshes. Recorded only. |
| Clavicle | Max chord 153.0 mm; SC–AC contact-proxy chord 147.7 mm; axial-bin centreline 176.7 mm; left and right agree within 1 mm | 154.8 mm extremal chord (CT 2018); Qiu 152.9 ± 9.3 mm (z −0.6); 166.8 ± 7.3 mm centreline (z +1.3) | **Plausible clavicle.** a003's SC–AC span of 222.9 mm is 75 mm longer, an independent confirmation of the clavicle defect. |
| Scapula | Superior-to-inferior angle 157 mm; glenoid proxy to inferior angle 145 mm | 148.2 ± 10 mm (z +0.9) | **Plausible.** a003's GH to inferior angle is 211.7 mm, 66 mm longer than the specimen's: an independent confirmation of the oversized a003 scapula. |
| Bilateral AC | 282 mm (contact proxies) | a003 481.4 mm; ANSUR biacromial at HGPT stature 425 mm, measured at the lateral acromia | Context only, since the specimen's stature differs. Even adding the 2 × 34 mm AC-to-lateral-acromion distance from GPT's source to the specimen gives about 350 mm, well below a003's 481 mm. |
| **Bilateral SC** | **32.0–36.0 mm** (contact threshold 1–3 mm); manubrium X extent 54.9 mm | a003 50.0 mm; manubrium outer breadth 68.2 ± 8 mm (Selthofer) | **Does not close CP1a.** One specimen, and the proxy is the clavicle head's closest-approach patch to the manubrium, which may be biased medially. Use it only as a plausibility bracket for the laptop SC value. |
| **Hyoid horns** | Total width 37.8 mm; tip span 34.9 mm; horns turn inward by **0.0 and 0.3 mm**, i.e. essentially straight | Abdelkader: width 42.85, centre span 39.65, posterior-end span 35.32 mm | **This corrects my earlier hyoid note.** Straight horns cannot satisfy the three spans read literally (shown in the fourth pass). But this specimen's horns *are* straight, so the likelier explanation is that Abdelkader's "posterior end" and "centre" landmarks are not on the horn centreline (for example, a medial point of the tubercle). The fix is to check Abdelkader Figure 1's landmark definitions before CP3, not to bend the horns by default. |

## CP3 build rehearsal (Blender 5.2.1)

The record is `audit/runs/claude_cp3_rehearsal_001/`. GPT's `build_armature` and `build_markers` build a complete 206-bone, 427-marker master from target data alone, in an empty scene. The result reloads and captures back exactly (to single precision), and the capture passes through the CP2 preflight with the same verdict as its input. **The skeleton-first build path works.**

**Findings:**
1. **74 bones have an undefined roll.** Horizontal-bone frames put X along the bone, so `align_roll` has a parallel target. The movement tests are unaffected, but a defined convention is needed before CP3 and CP9.
2. My own checker's float tolerance was too strict for Blender's single precision. That is fixed, and the mutation test still catches a 1e-3 frame skew.

## Owner-approved fixes to GPT files (8 October)

- **`scripts/anatomy_fit/source_identity.py`** now groups by PMCID too, normalised to `PMC` plus digits; a malformed PMCID raises an error. The regenerated `canonical_source_identity_review_v1.json` has **5 alias groups** (Barrôco 2011 added) and **11** identifier-less records, down from 36. There are new tests for PMCID aliasing and malformed values. The handoff's "four groups" note is updated.
- **`canonical_target_selection_v1.json`**: `direct_ansur_report_builder` now names `scripts/test_forearm_direct_report_provenance.py`, with a note explaining that the direct report has no generator. No target value changed, `freeze_ready` is still false, and the selection validator passes.
- **Still open for GPT:** report the Qiu clavicle SD as per-bone. That is a wording change in GPT's evidence and is left to GPT.

## Real-skeleton check of these findings (owner request, 8 October)

Each finding was rechecked against independent published measurements of real skeletons (dry bone, cadaver or CT), found by web search. Search results are abstract-level evidence: they have not been added to GPT's register, and no target was set from them.

| Finding | Real-skeleton data | Verdict |
|---|---|---|
| Talus: ZHANG_2018 "talus_length" 44.4 mm cannot be whole-talus length | Male talus length 53.1 ± 2.4 mm (Indian dry bone, sulcus-to-head definition); 57.3 ± 3.6 mm (NE Thai dry bone). Specimen: 58.5 mm. | **Confirmed.** Real male tali are 53–58 mm long. The registered 44.4 mm is a dome or other partial measure, so it must not be used as whole-bone scale. |
| Canovas spacing ratios | The abstract defines the normaliser as "the length of the first principal axis of inertia of the capitate" (18 adult wrists, CT). | **Resolved, and my earlier figure was wrong.** The normaliser is an inertia length, not the bone's full length. Using the semi-axis of the capitate's inertia-equivalent ellipsoid (√5λ₁ = 12.3 mm), the specimen gives 164.7% against 157.6 ± 8.4% (z +0.85) and 83% against 91.4 ± 7.3% (z −1.1). Its wrist layout therefore matches the real CT population. The extractor now uses that definition. |
| Carpal size order | Celik 2024 (CT, 42 adults): capitate largest, then hamate > scaphoid > trapezium > lunate > triquetrum > trapezoid > pisiform. | **The specimen matches this order exactly**, including the triquetrum > trapezoid swap against Patterson 1995. The two sources disagree with each other on that one pair. |
| Specimen carpal *size* | Celik 2024 male means: capitate 3,480 ± 679 mm³; pisiform 810 ± 141 mm³. | **The specimen's carpals are small:** capitate 2,312 mm³ (z −1.7, close to the female mean of 2,207) and pisiform 460 mm³ (z −2.5). Use the specimen for wrist *layout*, never for carpal *size*. This also explains the negative Asseln envelope z-scores. |
| Clavicle | Male osteometric maximum length 150.7–151.9 mm (212 male cadavers) and 152.9 ± 9.1 mm (dry bone). CT centreline 166.8 ± 7.3 mm, with endpoint length 149.4 ± 10.3 mm. | **Confirmed.** The specimen's 153.0 mm is typical. a003's 222.9 mm SC–AC span exceeds every real male figure by 70 mm or more. |
| Scapula | Male scapular height 148.2 ± 10.0 mm; CT maximum length 145 mm (Iran). | **Confirmed.** The specimen's 157 mm is within 1 SD. a003's 211.7 mm (GH to inferior angle, which is shorter than full height) is far beyond real scapulae. |
| Hyoid horns straight | Gray's Anatomy: the greater horns "project backward from the lateral borders of the body … each ends in a tubercle". Elsevier: each horn runs posterosuperiorly. | **Consistent.** Textbooks describe straight, slanted horns that end in an expanded tubercle, not inward-curving horns. That supports the correction: the Abdelkader "posterior end" landmark is likely on the tubercle, so check its Figure 1. |
| Rib spans, glenoid angles | Already compared with population data: Holcombe 2017 (n = 1,659 per level) and published glenoid normal ranges. | **Confirmed** (see the earlier sections). |
| SC joint separation | No published centre-to-centre value was found. Searches returned only joint-space widths (7.6–9.0 mm) and distances to nearby vessels and organs. | **Still unverified.** The specimen's 32–36 mm proxy has no real-skeleton check. The laptop task remains the route. |
| Specimen disc heights | Not rechecked; already judged unusable. | No change. |

## Builder fixes (owner-approved, rehearsal 002)

`build_anatomical_master_blender.py` now gives every bone a defined roll: anterior, or superior where the frame puts anterior along the bone (74 bones). It also stores marker rotations as quaternions, after the rehearsal found that Euler storage lost up to 3.6e-4 in marker frames near gimbal lock. Both fixes were rehearsed in Blender on a003's data and on an exactly mirrored copy: the round trip passes, rolls match the rule within 0.024°, and mirrored rolls agree within 0.027°. Details are in `audit/runs/claude_cp3_rehearsal_002/`.

## Sweep of GPT's registered values against real-skeleton data (owner request, step 2)

All 106 records in `canonical_proportion_sources_v1.json` were scanned for numeric male values and compared with standard osteometric and CT norms; outliers were rechecked by web search (abstract level). Public data repositories were read through the session's anonymous git lane: human-atlas, BMClab/BMC and RibSeg.

**Consistent with real skeletons (no action):**
- metacarpal lengths (three sources agree; M2 is longest);
- clavicle lengths (149–155 mm chord, 166.8 mm centreline);
- scapula (148–155 mm height; glenoid 37–40 × 27–30 mm; acromion and glenoid offsets);
- sacrum (breadth 103 mm, length 108 mm, S1 47 × 30 mm);
- patella (MRI 47 × 23 mm; the dry-bone Roman series is smaller, as expected without cartilage);
- fibula (374–387 mm);
- sternum segments (manubrium 46–55 mm, body 95–108 mm);
- SC joint space (8.2–8.7 mm, which matches an independent CT figure of 7.6–9.0 mm);
- pelvic anterior plane (238 × 93 mm);
- spinal sagittal angles (Hasegawa, Reinhold, Kim).

**Flagged:**

| Record | Problem | Real-skeleton evidence | Used in a target? | Suggested action |
|---|---|---|---|---|
| ZHANG_2018_TALUS_MALE | "talus_length" of 44.4 mm is not a whole-talus length | Male talus 53–58 mm (dry bone) | Yes: `canonical_tarsal_geometry_audit_v1` lists it as a whole-bone reference | Relabel it as a dome or partial measure and remove it from the whole-bone references |
| C2_VBH_CT_2008 | SD 0.66 mm is implausibly small | Dry-bone C2 anterior body height 23.2 ± 2.4 mm (n = 80) | Yes: carried as `male_CT_sd` in the spine stack and target selection | Treat it as a probable standard error until the source is reread, and do not use it as a corridor width |
| MANDIBLE_POSTMORTEM_INDIA_2023 | Bigonial 124.4 mm, gonion–gnathion 129.3 mm and condylion–gonion 43 mm are outside dry-mandible norms | Male bigonial breadth 95.7 ± 5.2 mm (about 5 SD away); the Iranian CT ramus in the same register is 60.8 mm | Listed only; the TMJ check uses a 3D-CT bicondylar breadth (121.9 mm, consistent) | Quarantine it as probably soft-tissue or method-inconsistent |
| RAUSCH_2018_RADIAL_HEAD_FOREARM | Ulna (231 mm) is shorter than the radius (238 mm) | Abstract: ulna measured styloid to *coronoid base*, mixed sex; real full ulna exceeds radius (Mall male 265 vs 246 mm; TG 283 vs 271 mm) | Listed only | Record the endpoint definition in the register |
| PATIL_2017_METATARSAL_PHALANGE | M1 56.4 mm (articular-landmark radiographic definition); M4 (66.5) listed longer than M3 (65.9) | Transcription confirmed by abstract; osteometric M1 is longer | Foot audit context | Keep its definition separate from osteometric lengths; the M3/M4 order stays unverified |

**a003 limb segments against real joint-centre proportions.** a003 is built from joint-centre spans, so maximum bone lengths (Trotter–Gleser) are the wrong yardstick; I nearly drew a wrong conclusion from them. de Leva 1996 gives male joint-centre segment lengths at stature 1,741 mm. Its thigh value of 0.4222 m is corroborated by a code-review snippet citing the paper's table; the other three values are as I recall them from the paper, unverified here. Scaled proportionally to 1.82 m:

| Segment | de Leva, scaled | a003 | Difference |
|---|---|---|---|
| Thigh, HJC–KJC | 441 mm | 412.9 mm | **−6.5%** |
| Shank, KJC–AJC | 454 mm | 439.1 mm | −3.2% |
| Upper arm, GH–EJC | 295 mm | 287.7 mm | −2.3% |
| Forearm, EJC–WJC | 281 mm | 256.2 mm | **−8.9%** |
| Shank/thigh ratio | 1.028 | 1.064 | thigh short relative to shank |
| Forearm/upper-arm ratio | 0.955 | 0.890 | forearm short relative to upper arm |

**Reading:** this is real-skeleton support for the owner's standing caution not to accept the short femur and forearm as correct. The forearm agrees with F-PROP-001 (ANSUR z −2.85). The thigh is short by this measure, which conflicts with the lower-limb audit's "no gross proportion failure" reading of the femur. The humerus is close to the de Leva proportion. Caveats: de Leva's sample is 100 young male athletes, scaling is proportional, and there are no per-segment SDs here, so these are percentages, not z-scores. **Nothing changes:** these remain open proportion questions for CP1, and nothing is promoted.

## Owner decision and applied fixes (8 October)

**Owner:** the skeleton follows normal 1.82 m adult male proportions, and the mesh is refitted to it. This was applied to `canonical_target_selection_v1.json` and `canonical_freeze_readiness_v1.json` as an owner decision and as new blockers. The changes:
- a humerus region is added, so the ledger now covers all 206 bones;
- the ribs region has a sternum blocker;
- the forearm and femur have 1.82 m proportion blockers;
- the lower-limb next action no longer says to keep a003 lengths for lack of evidence.

**Data fixes (owner-approved):**
- the talus partial measure is excluded from the whole-bone references;
- the C2 SD is nulled, with the printed 0.66 kept;
- the India mandible record is quarantined;
- the Rausch endpoints are recorded;
- the Qiu SD is marked per-bone.

Tests are in `scripts/test_owner_proportion_policy_and_source_fixes.py`. The full suite is 782 tests with the same 9 inherited failures. The 7 October review pack is a dated record and was not edited: its "owner questions" section is superseded by this decision.

## 1.82 m limb-length proposal for GPT review (and a correction)

`scripts/anatomy_fit/limb_length_proposal.py` produced `ORIGINAL_V1_WORK/anatomy/canonical_limb_length_proposal_182_v1.json`, with status **PROPOSAL_FOR_GPT_REVIEW_NOT_SELECTED**. It reproduces from the committed ANSUR file, and its tests are in `scripts/test_limb_length_proposal.py`.
- **Primary method:** per-subject joint-centre spans from the ANSUR II men (n = 4,082), using the 7 October landmark conversions, regressed on stature and evaluated at 1.82 m.
- **Cross-checks:** Trotter–Gleser maximum lengths, converted with the same allowances, and de Leva's joint-centre proportions. Only de Leva's thigh value is corroborated here.

| Span | ANSUR at 1.82 m | Trotter–Gleser | de Leva | a003 | Reading |
|---|---|---|---|---|---|
| Forearm, EJC–WJC | 293.1 ± 10.8 (283–288 if WJC is 5–10 mm proximal of stylion) | 285.7 | 281.1 | **256.2, z −3.4** | **Robust: lengthen.** All methods agree within about 1 SD. |
| Thigh, HJC–KJC | 418.9 ± 21.2 (427 if HJC is level with trochanterion) | 455.0 (inflated by inversion) | 441.4 | 412.9, z −0.3 | **Contested.** Resolve the HJC endpoint relation first. |
| Upper arm, GH–EJC | 286.2 ± 10.6 (277 with the Rajagopal GH depth) | 322.8 | 294.5 | 287.7, z +0.1 | Consistent. The Trotter–Gleser conversion is the outlier. |
| Shank, KJC–AJC | 437.5 ± 14.0 | none (no defensible conversion) | 453.7 | 439.1, z +0.1 | Consistent. |

**Correction:** earlier today I reported the a003 thigh as "6.5% short", and it was added to the readiness blockers and the status page. That figure came from de Leva alone. Against ANSUR, the stature-conditioned primary source, the a003 thigh is within 0.3 SD. The femur blocker now records the method conflict instead of a shortfall. **Only the forearm is established as short.**

**Left for GPT:**
- map each span onto canonical bone endpoints (head, condyles, trochlea, styloids);
- set a separate ulna target;
- decide how to reconcile the thigh methods;
- reread de Leva Table 1 for the three unverified values.
