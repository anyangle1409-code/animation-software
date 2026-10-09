# New primary CT constraints — source-registered trunk closure (9 October 2026)

**STATUS: INDEPENDENT EVIDENCE & NONCANONICAL CONTROL COMPARISONS.**
This stage does not change any bone, source-selected coordinate, muscle, skin, production file, existing Claude code, P003, P004, P005 or accepted model. The observed source-to-model distances are not automatically diagnostic of a skeletal defect until anatomically equivalent endpoints and coordinate frames have been established.

## 1. Independently measured upper-thoracic bony distance — Baker et al.

**Original research:** Baker, *Analysis of Sagittal Thoracic Inlet Measures in Relation to Anterior Access to the Cervicothoracic Junction*, Global Spine Journal; DOI `10.1177/21925682211005730`, [full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10240579/), **Figure 1, Table 1**.

- **Exact CT endpoints:** midpoint of the T1 superior vertebral-body endplate to the **apex of the manubrium**; a straight distance in the *midsagittal CT plane*. This is **not** the sagittal AP component of the sternum-to-T2 vertebral-body depth, and not a surface skin IJ measurement.
- **Cohort:** 65 CT scans, 33 men, adults ≥16 years after exclusions for abnormal spinal count or structural pathology; scanned **supine**. No source-matched 1.82-m male stature regression is available.
- **Study discrepancy is explicitly retained:** Abstract reports **66.1 mm (SD 6.6)**, while **Table 1 reports mean 65.9 mm (SD 6.6), observed range 52–83 mm**. Both values are retained, not silently reconciled.
- **Model point proxies:** `bones.t1.tail_m` (control upper endplate midpoint) to `bones.sternum.head_m` (schematic jugular/manubrial head).
- **Read-only model output:** c004 **88.744 mm** (outside this population's 52–83-mm observed range); P003 **73.182 mm** (inside). P004/P005 are also computed by the new isolated CI tests.
- **Critical uncertainty:** schematic sternum.head is not independently verified as the *true bony manubrial apex*; T1.tail is an interpolated control not a fitted superior endplate centroid. Neither a range match nor a mismatch establishes an anatomical correction. A 5.7-mm gap outside the observed 83-mm upper range is not a clinical diagnosis.
- **Meaning:** supplies the first strongly endpoint-defined **CT thoracic inlet distance** to compare with a future feature-registered sternum/T1 reconstruction, but NOT a new anatomical target or full AP-depth closure.

## 2. Independently measured S1-to-hip axis components — Imai et al.

**Original research:** Imai et al., *Evaluation of anatomical pelvic parameters between normal, healthy men and women using three-dimensional computed tomography: a cross-sectional study of sex-specific and age-specific differences*, Journal of Orthopaedic Surgery and Research, 14:126 (2019), DOI `10.1186/s13018-019-1165-2`, [original article](https://link.springer.com/article/10.1186/s13018-019-1165-2), [complete seven-page PDF with Table 1 on page 4](https://d-nb.info/1193894271/34).

- **Anatomical endpoints:** S1 **superior endplate centre** defined midway left/right and anterior/posterior on that plate, relative to midpoint of the **two femoral head centres**, with the pelvic bone geometry registered to the **anterior pelvic plane (APP)**. This is an anatomy-frame quantity, **not** an arbitrary standing-pose world-frame Y or Z displacement.
- **Cohort:** 108 Japanese adults, **55 men** with average body height **166.0 cm**, shorter than the intended 182 cm male character.
- **Male Table 1 values:** sagittal total **107.0 ± 19.9 mm**, `DYp` AP component **18.8 ± 21.2 mm**, `DZp` craniocaudal component **104.7 ± 20.5 mm**. **IMPORTANT:** The authors expressly define those `±` spreads as **two standard deviations (2 SD)**, not the usual 1-SD notation.
- **Model controls:** `sacrum.tail_m` compared with midpoint of `femur_left.head_m` and `femur_right.head_m`. In the unreconstructed c004, S1 minus hip centres is **+59.268 mm on world Y** and **+116.345 mm on world Z**. The sagittal magnitude is ~130.6 mm.
- **Critical uncertainty:** `world +Y` is posterior but the skeleton's APP has **not** been built from trusted pelvic-bone *surface* landmarks. The existing model's `asis_skin` values derive from an aesthetic inguinal groove endpoint (confidence low, uncertainty ±20 mm), and `pubic_symphysis_side` is a provisional control point. They are **not** the independently verified osseous ASIS/pubic contact landmarks required for study-frame registration. Moreover, the 166 cm cohort must NOT be scaled uniformly to 182 cm.
- **Meaning:** This is substantially more useful than the earlier 107.0 mm *undifferentiated* total alone: it gives a **separate AP component**. But without a verified APP frame and matched endplate/femoral-head surfaces, the apparent +40 mm posterior difference is **a question to investigate, not a permissible numerical correction**.

## Source-grounded decision: what is now more constrained, and what remains blocked

| Claim | New evidence status | Can set anatomical target now? |
|---|---|---|
| 3D T1 top-to-manubrium **distance** | CT endpoint defined, 65 scans; external contextual check | **No** — model's bony points remain control proxies |
| T1/manubrium **AP distance alone** | Not supplied by TID (slanted scalar distance) | **No** |
| S1-to-hip **APP AP component** | CT male population source, **18.8 mm ± 21.2 mm (2 SD)** | **No** — APP registration, stature and endpoint identity missing |
| S1-to-hip APP vertical component | CT male population source, **104.7 ± 20.5 mm (2 SD)** | **No** — same restrictions |
| Thoracic T1–T12 per-level wedge tilt | T12 and L1 endplate orientation studies exist but not all levels and frame | **No** |
| 3D sternocostal cartilage/SC articular contact | Existing control-only P004–P007; no validated bone shapes | **No** |

## Required *next physical reconstruction*, not more circular control fitting

1. Independently register physical **manubrium apex**, **T1 superior endplate centroid**, **S1 superior endplate centre**, **left/right femoral head articular centres**, **bony ASIS**, and **pubic symphysis anterior surface**, using source-backed *skeletal features*, NOT old r95 skin/mesh groove positions.
2. Build a reproducible APP anatomical frame from three noncollinear bony landmarks with explicit posterior/anterior axis and the standing pelvis transformation as a separate operation.
3. Re-run both study comparisons with exact endpoint semantics; retain cohort sex/stature/pose and all uncertainty intervals.
4. Solve the actual lumbar MRI-edge vertebrae/disc stack and thoracic source B levels *with* lumbar lordosis, thoracic wedges, C7 height, rib joints, the bony sternum and shoulder/SC/AC/GH closure; do not flatten or simply translate the chest.
5. Verify biomechanics and surfaces in Blender and against real photos/clinical references before character mesh/muscle work or canonical promotion. A P004–P007 mechanical pass is never enough.
6. Preserve all prior attempts and source lineage. Keep c005 blocked until the above prerequisites are independently verified.

### Machine-readable evidence and tests

- `ORIGINAL_V1_WORK/anatomy/audit/external_trunk_landmark_source_registry_20261009.json`
- `scripts/anatomy_fit/external_trunk_landmark_bridge.py` (read-only; exclusive-create report option; **always** non-promotable)
- `scripts/test_external_trunk_landmark_bridge.py` (17 tests, covering source measurements, world frame, numerical references, mutation protection, no false acceptance)
- Independent GitHub Actions `.github/workflows/trunk-external-landmarks.yml`, including replay/regression of all 108 previous P004–P007 focused tests.

**Zero canonical regions READY; status remains 0 READY, 9 PARTIAL, 3 BLOCKED.**
