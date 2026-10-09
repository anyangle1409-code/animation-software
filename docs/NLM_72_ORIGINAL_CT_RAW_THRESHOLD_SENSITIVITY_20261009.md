# Original CT 72-frame threshold sensitivity — independent Work offload

**Source-derived diagnostic only. Not HU-calibrated, not a validated bone segmentation, and not a canonical correction.**

## Concrete new work

Work's earlier Blender occupancy scene contained **13,273 uncalibrated source-scalar blocks**. A single threshold (raw PNG value 1200) is not evidence that those blocks are bone. We now check a reproducible range of *raw stored image values* and 3D component stability instead of generating another cosmetic mesh.

- Original source: all 72 NLM CT PNGs from the two separate physically registered scanner groups, validated against the existing manifest, exact source SHA-256 and original byte count.
- Fixed raw-scalar cutoffs: **900, 1050, 1200, 1350, 1500 and 1800**. These are **not** approved Hounsfield or cortical-bone cutoffs.
- For each 8 × 8 native-pixel tile: both **any** (≥1 out of 64 stored scalars passes) and **eight** (≥8 out of 64 pass) occupancy operators.
- For each source group (37 and 35 slices) independently: occupied block count, largest 3D 6-connected component percentage, component counts, ten largest sizes, and Jaccard overlap with cutoff 1200.
- Never stitch the physically separate acquisition groups, remove smaller islands automatically, store patient images or private headers, change the skeleton, or promote an uncalibrated surface.

## Files

- scripts/anatomy_fit/nlm_original_ct_raw_threshold_sensitivity.py
- scripts/test_nlm_original_ct_raw_threshold_sensitivity.py — 18 first-party synthetic and source-manifest tests
- .github/workflows/independent-pelvis-stl-intake.yml — original 72-source live threshold sweep plus inherited regression tests

## Interpretation rules

The 13,273-block Blender occupancy may have used a different tile sampling/occupancy definition. Do **not** directly compare its block counts to the new independent operator and claim a regression. Compare the changes **within each operator** as the raw stored-scalar cutoff changes. Stability of numerical components alone is still not proof of correct human bones.

Upstream references: original NLM Visible Human CT PNG and scanner GE headers (https://www.nlm.nih.gov/research/visible/getting_data.html); original IDC DICOM conversion (https://github.com/ImagingDataCommons/NLM-Visible-Human-Project-DICOM-Conversion), which applies a manually selected display window but does **not** establish stored-PNG HU conversion.

### Next meaningful work, not repeated research

1. Independently verify the original 16-bit PNG-to-Hounsfield rescale and pixel-centre convention from source/converter/manufacturer evidence.
2. Source-label actual ilium, sacrum, pubis and proximal femoral articular regions; use qualified anatomical references, multiple slices, scanner RAS and quantified uncertainty.
3. Reconstruct separately segmented physical bone-surface candidates in private storage, inspect connected components and conservatively match source anatomical landmarks.
4. Independently compare landmarks with population sources and then consider an isolated skeletal correction; do not fit bones to the old skin mesh.

**Canonical readiness: 0 READY / 9 PARTIAL / 3 BLOCKED. Claude and existing Work worktree assets untouched.**

## Independently executed live NLM study — VERIFIED

GitHub Actions original-source threshold sweep: https://github.com/anyangle1409-code/animation-software/actions/runs/37997358527 . Every original PNG SHA-256/byte count matched the previously pinned 72-source bundle. Machine-readable complete results (all six thresholds, both tile rules and both physically separate scan groups) are stored at:

ORIGINAL_V1_WORK/anatomy/audit/nlm_ct_raw_threshold_sensitivity_verified_20261009.json

### Actual threshold effects for the any-pixel tile operator

| Source group | Raw cutoff 1200 | Raw cutoff 1800 | Blocks removed | Largest 6-connected component share at 1200 → 1800 | Components at 1200 → 1800 |
|---|---:|---:|---:|---|---|
| 37 superior scans | 10,452 | 3,704 | **64.6%** | 70.0% → 30.0% | 27 → 82 |
| 35 inferior scans | 7,311 | 2,798 | **61.7%** | 85.8% → 33.4% | 21 → 55 |

### Actual threshold effects for the eight-of-64-pixels tile operator

| Source group | Raw cutoff 1200 | Raw cutoff 1800 | Blocks removed | Largest 6-connected component share at 1200 → 1800 | Components at 1200 → 1800 |
|---|---:|---:|---:|---|---|
| 37 superior scans | 8,494 | 1,726 | **79.7%** | 72.4% → 23.3% | 3 → 129 |
| 35 inferior scans | 6,039 | 1,340 | **77.8%** | 88.5% → 21.3% | 6 → 99 |

**Conclusion supported by source calculations:** a small change in the uncalibrated PNG stored-scalar cutoff or the tile occupancy definition can dramatically change connected structures, topological fragmentation and spatial extent. A nice-looking single-cutoff occupancy block render is *not stable evidence for a physically correct human pelvic bone surface*. The earlier Blender block count (13,273) is under a potentially different implementation and is not an apples-to-apples count. No result here is a clinical interpretation of bone or tissue density.

**What this replaces for Work:** Work no longer needs to write a first raw-intensity-threshold sensitivity implementation, fetch 72 source frames for this test, independently hash them or calculate these aggregate 3D connectivity figures. It can read the pinned output and proceed directly to original PNG→HU calibration, actually bony feature identification and clinically validated surface segmentation.

**What this does not resolve:** CT sample-centre origin, image patient-to-HGPT transform, original PNG Hounsfield rescale, bone/soft-tissue classification and full pelvic-bone region coverage. These remain hard blockers to canonical corrections.
