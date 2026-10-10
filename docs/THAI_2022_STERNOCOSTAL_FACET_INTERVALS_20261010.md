# Independent 2022 sternocostal notch-centre evidence — noncanonical

**Primary study:** Jeamamornrat V, Monum T, Keereewan W, Mahakkanukrauh P, "Stature estimation using the sternum in a Thai population", *Anatomy & Cell Biology* 55(2):170–178 (2022). DOI **10.5115/acb.22.045**, PMID 35773219, https://pmc.ncbi.nlm.nih.gov/articles/PMC9256492/. Original **Table 1** has the endpoint definition; original **Table 2** has the mean, SD and observed range. The article is licensed **CC BY-NC 4.0**; no article PDF, figures, source medical data or externally copyrighted 3D geometry is committed or distributed.

## Independent sample and exact facet-center distances

Original osteology cohort: 219 donated dry sterna from Northern Thailand, **199 training subjects (104 male, 95 female)** and 20 hold-out test subjects (10 male, 10 female), mean training age 66.5 years. Anatomical deformity cases affecting measurement were excluded. Training statures **140–180 cm**; HGPT male model target **182 cm**, outside the observed training stature range. This is independent of the NLM Visible Human CT cadaver and the Turkish CT/Selthofer studies. It is **not** automatically a normative UK/European 182cm male sample.

Source describes ICL as distance between **costal cartilage facet-centre landmarks on dry sternum**, NOT rib-head centre, 3D curve length, costal cartilage deformation, sternum world-Z, or physical whole-bone end.

| Measurement | Male training mean ± SD (mm) | Male observed range (mm) | Availability |
|---|---:|---:|---|
| 2nd to 3rd costal cartilage facet centres | **29.30 ± 3.11** | 18.88–36.07 | Measured |
| 3rd to 4th costal cartilage facet centres | **25.20 ± 2.71** | 15.14–32.29 | Measured |
| 4th to 5th costal cartilage facet centres | **19.56 ± 2.87** | 9.46–28.17 | Measured |
| Level 1→2, 5→6, 6→7 and other levels | Unknown | Unknown | **Not in this source table** |

Successive reported means decrease **4.10 mm**, then **5.64 mm**, with last/first interval ratio approximately **0.668**. These are independently measurable human sternocostal local-spacing context, not a template from which to place absolute anatomical joint centres.

For context, the existing schematic **a003 world/projection depth differences** at corresponding nominal levels are **35.2, 31.9, 31.0 mm**. These are **not proven geometrically or landmark-semantically commensurate** with the dry-sternum facet-centre measures. We must not subtract them and call the result an anatomical defect/correction without registering each actual source-to-model facet center, side definition and projection.

Male primary Table 2 also gives manubrium length **48.90±5.28 mm**, mesosternum **97.12±9.57 mm**, and direct combined jugular-notch→mesoxiphoidal straight chord **146.02±10.41 mm**. The combined chord must not be conflated with the sum of two separately measured lengths, Selthofer's **xiphoid-inclusive** total, or Turkish **xiphoid-exclusive M+B** combined length. All are method-specific and studied in different population cohorts.

## Machine-readable guardrails / next step

Numeric evidence: `ORIGINAL_V1_WORK/anatomy/sternum_thai_2022_three_facet_intervals_20261010.json`; first-party validation `scripts/anatomy_fit/audit_thai_sternocostal_intervals.py`; dedicated adversarial tests `scripts/test_thai_sternocostal_intervals_20261010.py`. New CI exercises this alongside the already validated **Selthofer 2006 + Turkish 2018 endpoint correction**.

Use this **only as 3-level source provenance** when Work reconstructs rib/sternum geometry in physical bone coordinates. Still need the absent notch levels, actual unilateral/bilateral centre definitions, 3D surface patches, full costal cartilage path and AC/SC thorax geometry, neutral pose, source frame registration, and population scale conditioning (182 cm outside source stature range). **No model/bone target automatically accepted; CP1/Gate6 OPEN, region READY 0/PARTIAL 9/BLOCKED 3.** Never copy this CC BY-NC source's figures or patient assets into a commercially distributed PT app without licensing review.
