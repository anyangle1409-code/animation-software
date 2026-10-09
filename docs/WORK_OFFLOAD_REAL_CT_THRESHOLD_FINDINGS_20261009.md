# Work/Claude offload: original 72-slice CT stability already computed

**Read this before repeating any CT threshold, header or 3D-component experiments.**

## Finished directly in GitHub, without Work or laptop

1. Reused the source-hashed 72 original NLM male CT images (37 upper group, 35 lower group) and independently re-downloaded them from the original NLM HTTPS custodian, verifying **all 72 PNG SHA-256s and byte counts**. No CT PNG pixels or historic patient header text were committed.
2. Decoded each real source 512×512 16-bit image and calculated independent 8×8 stored-value block masks using *at least one source pixel* and *at least eight of 64 source pixels* above six raw-scalar cutoffs (900, 1050, 1200, 1350, 1500, 1800). These numbers are NOT verified Hounsfield units.
3. Computed real 3D six-neighbour connected-component statistics separately for the **two physically registered source groups**, refusing cross-group joining or silent removal of smaller islands.
4. Verified all tests and live source analysis in https://github.com/anyangle1409-code/animation-software/actions/runs/37997358527.
5. Saved the complete machine-readable numerical results in ORIGINAL_V1_WORK/anatomy/audit/nlm_ct_raw_threshold_sensitivity_verified_20261009.json and the implementation in scripts/anatomy_fit/nlm_original_ct_raw_threshold_sensitivity.py.

## Concrete outcomes

| Original 72 CT subgroup | Mathematical tile rule | Raw cutoff 1200 blocks | Raw cutoff 1800 blocks | Fraction removed | Components at 1200 → 1800 |
|---|---|---:|---:|---:|---|
| Upper (37 slices) | Any of 64 | 10,452 | 3,704 | 64.6% | 27 → 82 |
| Lower (35 slices) | Any of 64 | 7,311 | 2,798 | 61.7% | 21 → 55 |
| Upper (37 slices) | Eight of 64 | 8,494 | 1,726 | 79.7% | 3 → 129 |
| Lower (35 slices) | Eight of 64 | 6,039 | 1,340 | 77.8% | 6 → 99 |

This is evidence that the **uncalibrated reconstructed occupancy topology is threshold sensitive**, not evidence for a particular CT value, bone identity or clinical diagnosis. Earlier Blender produced a 13,273-block occupancy trial using an unconfirmed operator; do NOT compare those block numbers to this new operator as if the methods were identical. Source objects are not accepted bones merely because they look human-shaped.

## Additional independent actual GE scanner calibration-header check

scripts/anatomy_fit/nlm_ct_original_ge_hu_evidence.py and scripts/test_nlm_ct_original_ge_hu_evidence.py now inspect two exact SHA-pinned original GE scanner text headers for strictly whitelisted CT-intensity-related numeric metadata, with all patient fields excluded. Its **live CI result must be checked**. In any case, a GE Hounsfield annotation offset is NOT automatically a proven PNG conversion intercept: same-image original PNG/DICOM/source converter calibration evidence is still required.

## Real original GE scanner intensity-header screen also finished

The independently executed GitHub Actions run https://github.com/anyangle1409-code/animation-software/actions/runs/37997758197 obtained and SHA-256 checked original GE headers for **cvm1734f (scanner S −342 mm)** and **cvm1800f (scanner S −408 mm)**. The strict physics-only field allowlist did not return a numeric `RescaleSlope`, `RescaleIntercept`, or recognised Hounsfield-offset key from those two headers. Actual safe results (no original patient header text) are committed to ORIGINAL_V1_WORK/anatomy/audit/nlm_original_GE_HU_source_screen_verified_20261009.json.

**This is a limited negative finding, not proof the scanner or raw GE images contain no other calibration metadata.** It rules out simply citing these two known recognised metadata keys as already-verified PNG conversion. Any proprietary field needs separate documented mapping. No one should invent the often guessed `HU = PNGvalue − 1024` or use window centre/width as conversion evidence.

GitHub successfully ran **401/401** focused regression tests across the previously established anatomy/tooling suite and this new source-calibration screen; source-network jobs also passed. A final new machine-record assertion has been added and will be verified by the latest CI before being called green.

## What Work can skip completely

- Reimplementing this 72-slice threshold-sensitivity audit, hashing/downloading original CT images for it, or creating more single-cutoff uncalibrated block-model renders.
- Re-checking the 72 original CT row/column orientations: separate PR #16 already independently verified all 72 source headers, both acquisition groups, and 34/34 focused tests.
- Redoing the synthetic CT connectivity and 8×8 operator sensitivity tests implemented here.

## Only remaining genuinely necessary tasks

1. Establish original PNG stored-scalar → Hounsfield unit conversion using original source or equivalent verified DICOM rescale, never a visualization WindowCenter/Width or a guessed -1024 offset.
2. Visually identify anatomical bone regions across full-resolution original source CT and a qualified second anatomical atlas; isolate actual sacrum, iliac bones, pubic tubercles and femoral heads.
3. Build one physically registered **source-supported osseous candidate segmentation** with conservative artifacts/threshold handling and independent review in Blender; retain scanner/world origin ambiguity and quantitative resolution limits.
4. Compare source features with multiple suitable population references before changing a 1.82 m original character. Claude can inspect physical bone surfaces in separate laptop worktree; do not merge canonical c005 or refit skin as a source of truth.

**Status: CT software evidence advanced; canonical readiness remains 0 READY / 9 PARTIAL / 3 BLOCKED.**
