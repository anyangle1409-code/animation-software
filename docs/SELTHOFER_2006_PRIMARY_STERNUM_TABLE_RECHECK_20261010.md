# Selthofer 2006 full-text sternum primary source recovery (NONCANONICAL)

**Primary full-text PDF:** https://hrcak.srce.hr/file/11308. Selthofer et al., *Morphometric Analysis of the Sternum*, Collegium Antropologicum 30(1), 43–47 (2006), PMID 16617574. Five pages, original printed Table 2 visually checked. **No PDF bytes committed or locally hash verified.**

Original osteological sample: 55 male and 35 female sterna, average age approximately 65, fixed in formalin. The donor cohort is not the NLM Visible Human or a height-matched 182 cm male sample.

## Male primary Table 2, actual page 45

| Male measurement | Mean | SD | Qualification |
|---|---:|---:|---|
| Manubrium length | 55.2 mm | 3.6 mm | Jugular-notch centre to manubriosternal synchondrosis |
| Manubrium maximum breadth | 68.2 mm | 8.0 mm | Sample-specific notch-defined width |
| Manubrium minimum breadth | 36.8 mm | 5.5 mm | Distinct width landmark |
| Manubrium average breadth | 52.5 mm | 6.8 mm | Not a specific articular centre |
| Manubrium average thickness | 12.6 mm | 1.9 mm | Mean thickness |
| Sternal body length | 109.7 mm | 14.4 mm | Measured anatomic body, not vertical Blender stick |
| Sternal body average breadth | 30.7 mm | 4.3 mm | Width over sampled costal-notch sections |
| Sternal body average thickness | 10.0 mm | 1.1 mm | Not cartilage thickness |
| **Total sternum length** | **208.6 mm** | **14.6 mm** | From jugular notch to xiphoid distal end |
| Male sternal angle (Table 1) | 166.35° | 7.38° | Lateral posture/protractor; NOT a skeletal Euler angle |

Original male means: manubrium + body length = 55.2 + 109.7 = **164.9 mm**. Total minus these two = **43.7 mm**, a residual **not** an independently measured xiphoid length; differences in measurement line, collinearity, partitioning and endpoints are unverified.

## Why this changes the source investigation — not anatomy acceptance

**IMPORTANT PRIMARY SOURCE SEMANTIC CORRECTION.** The original Turkish 2018 CT paper (Ateşoğlu, Deniz and Uslu, DOI 10.5603/FM.a2018.0002, PMID 29345718) specifically defines its reported 154.1 ± 13.1 mm **total** as **CL = manubrium length M + sternal-body length B**. Its 97 male cases separately measured the **xiphoid at 39.1 ± 11.3 mm**; the xiphoid is **NOT included** in the 154.1mm CL total. See the primary Methods text at https://www.researchgate.net/publication/322588235_Evaluation_of_the_morphological_characteristic_and_sex_differences_of_sternum_by_multi-detector_computed_tomography (printed page 491) and original Table1.

The frozen record field name **population_male_means_mm.total_including_xiphoid_turkey_CT** is therefore **semantically WRONG**, although its number 154.1 and SD 13.1 remain faithful to the paper. The historical canonical file is intentionally NOT edited on this independent branch; a reviewed follow-up must correct that machine-readable key without breaking downstream provenance.

The old **54.5 mm** difference (208.6 − 154.1) compares **different anatomical endpoint definitions** and must not be treated as a 54.5mm population disagreement or a model correction. For the better-aligned manubrium+body *measurement family*, the male means are **164.9 mm** (Selthofer 55 cadavers) against **154.1 mm** (Turkish CT combined CL, 97 males), a descriptive **10.8 mm** difference. Summing Turkish component means separately gives 51.2 + 102.4 = 153.6 mm, hence **11.3 mm** difference from Selthofer; 0.5mm between Turkish combined CL mean and component sums may arise from rounding/measurement conventions. These remain distinct cohorts and measurement methods and cannot simply be averaged.

The pre-existing a003 Blender sternum control **213.2 mm** is specifically defined from the jugular notch to the **xiphisternal region, excluding the xiphoid**. Its numerical proximity to Selthofer's **208.6 mm including the xiphoid** is also **invalid as like-for-like anatomical validation**. It remains unaccepted until true matching anatomical endpoints and connected rib/sternum geometry are reconstructed.

The original Methods (printed page 44) defines breadths at segments relative to the first/second costal notches and different body segments between costal notches 2–7. While the method mentions second-to-fourth and fourth-to-xiphoid vertical subdivisions, **Table 2 does not publish a complete numerical notch-by-notch vertical depth table**. The previously missing primary full text has now been located and checked; the rib 1–7 actual cartilage-to-sternum joint targets are still missing.

Source data were published as human-population descriptive measurements, NOT a complete neutral-frame 3D sternum mesh, NOT a stature-regressed 182 cm male target, NOT joint centres or physiological ROM.

## Machine-checkable noncanonical deliverables

- ORIGINAL_V1_WORK/anatomy/sternum_selthofer_2006_primary_table_recheck_20261010.json — primary table provenance and unreconciled historical comparison.
- scripts/anatomy_fit/audit_selthofer_sternum_primary.py — validates paper identity, 55-male sample, table cells, prior frozen record and explicit nonacceptance flags; derives arithmetic comparisons.
- scripts/test_sternum_selthofer_primary_recheck_20261010.py — adversarial tests preventing wrong endpoints, false full-notch claims, altered source and acceptance promotion.
- .github/workflows/sternum_selthofer_primary_recheck.yml — isolated offline source validation, numerical diagnostic report only, no primary PDF or private data.

**Next:** preserve the newly verified Turkish xiphoid-exclusion correction, verify remaining non-collinear source methods and stature conditioning; obtain independent exact rib-specific costal-notch positions/cartilage contacts in one thorax frame; keep shoulder and sternum conflicts open. A003 and all accepted geometry unchanged, CP1/Gate6 open, **0 READY / 9 PARTIAL / 3 BLOCKED**.
