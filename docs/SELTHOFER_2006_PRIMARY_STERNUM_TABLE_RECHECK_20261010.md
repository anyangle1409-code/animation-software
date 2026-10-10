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

The historical frozen sternum target review cites an entirely different Turkish CT male total including xiphoid of **154.1 ± 13.1 mm**, a **54.5 mm** lower mean than Selthofer's original cadaver population. The existing a003 Blender sternum stick is **213.2 mm**, only **4.6 mm** above Selthofer's cohort mean, but this numeric proximity **does not validate** that stick, its world coordinate frame, its actual jugular/xiphoid endpoints, or its costal connections. The Turkish study's precise endpoints and patient selection must be checked before merging any means or explaining the differences.

The original Methods (printed page 44) defines breadths at segments relative to the first/second costal notches and different body segments between costal notches 2–7. While the method mentions second-to-fourth and fourth-to-xiphoid vertical subdivisions, **Table 2 does not publish a complete numerical notch-by-notch vertical depth table**. The previously missing primary full text has now been located and checked; the rib 1–7 actual cartilage-to-sternum joint targets are still missing.

Source data were published as human-population descriptive measurements, NOT a complete neutral-frame 3D sternum mesh, NOT a stature-regressed 182 cm male target, NOT joint centres or physiological ROM.

## Machine-checkable noncanonical deliverables

- ORIGINAL_V1_WORK/anatomy/sternum_selthofer_2006_primary_table_recheck_20261010.json — primary table provenance and unreconciled historical comparison.
- scripts/anatomy_fit/audit_selthofer_sternum_primary.py — validates paper identity, 55-male sample, table cells, prior frozen record and explicit nonacceptance flags; derives arithmetic comparisons.
- scripts/test_sternum_selthofer_primary_recheck_20261010.py — adversarial tests preventing wrong endpoints, false full-notch claims, altered source and acceptance promotion.
- .github/workflows/sternum_selthofer_primary_recheck.yml — isolated offline source validation, numerical diagnostic report only, no primary PDF or private data.

**Next:** verify original Turkish CT total endpoint definition and non-collinear source methods; obtain independent exact rib-specific costal-notch positions/cartilage contacts in one thorax frame; keep shoulder and sternum conflicts open. A003 and all accepted geometry unchanged, CP1/Gate6 open, **0 READY / 9 PARTIAL / 3 BLOCKED**.
