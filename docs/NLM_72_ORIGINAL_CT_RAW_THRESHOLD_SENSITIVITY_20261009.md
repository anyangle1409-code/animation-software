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
