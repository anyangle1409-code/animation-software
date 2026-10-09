# Work restart handoff — original pelvic CT physical orientation verified

**Saved 2026-10-09; branch `codex/ct-72-frame-orientation-preflight-20261009`; stacked DRAFT PR #16 on PR #15.** Never overwrite Claude/Work or canonical c004. Before resuming, fetch LIVE GitHub HEADs and preserve any intervening commits.

## Actually completed before Work allowance returns

- **Original full-series**: prior Work checkpoint created private 72-image NLM CT source set, two valid scanner groups, −342 to −553 mm superior scanner coordinate, 2 mm physical slab overlap at boundary; produced a 13,273-block Blender stored-scalar preview with eight and three disconnected components by group, expressly NOT a bone segmentation.
- **New independent scanner geometry gap closed:** `scripts/anatomy_fit/nlm_ct_72_header_orientation_audit.py` retrieved the original, source SHA-256-pinned GE scanner headers **for all 72 slices** into temporary GitHub runner memory and verified both actual pixel-axis direction vectors on every slice. Source headers contain historical identifying fields; all raw headers were excluded from tool outputs and repository.
- **Live outcome:** all 72 original source header hashes match the full-series bundle; **37 superior-group + 35 inferior-group** frames have increasing columns toward scanner **−R**, increasing rows toward **−A**, right-handed axial normal **+S**; both groups align and no 90°/180° in-plane rotation/mirror flip is present in their original headers.
- **Focused CI:** https://github.com/anyangle1409-code/animation-software/actions/runs/37995818874 — **15 new orientation mutation tests + 19 existing full-series tests = 34/34**, original live header check success.
- **Full regression CI:** https://github.com/anyangle1409-code/animation-software/actions/runs/37995818885 — **369/369 tests** in the intake job, and **all five original-source/scan jobs green**, including a second independent 72-header source audit.
- **No canonical bone corrections, c005, approved anatomical landmarks or production mesh changes**. Readiness is unchanged: 0 READY / 9 PARTIAL / 3 BLOCKED.

## Important original-source limitation discovered in upstream conversion documentation

Imaging Data Commons' independently published [Visible Human DICOM conversion notes](https://github.com/ImagingDataCommons/NLM-Visible-Human-Project-DICOM-Conversion) state that the converted male CT DICOM process **removed the proprietary gantry-specific ImagePosition and ImageOrientation** and used the CT slice filename as a SliceLocation. It also explicitly preserved original missing/broken source data. Therefore:

- **Do not assume IDC-converted DICOM alone contains verified spatial positioning or HU calibration.**
- The NLM original GE scanner headers plus source SHA and individually verified row/column vectors are the controlling **scanner RAS** spatial reference used here.
- A matching GE header orientation still does NOT independently prove whether TL/TR/BR corners mark the external FOV edge or the first pixel sample centre.
- The published DICOM **WindowCenter 40 / WindowWidth 400** was manually chosen for visualization and does NOT prove that the PNG stored scalars are HU or establish a rescale slope/intercept.

## Next highest-value Work actions, in order

1. **Do not redo the 72-source orientation audit.** Read the above reports and tests, review PR #16, then continue on an isolated Work-owned branch/worktree without force-pushing the CT geometry checkpoint.
2. Resolve **original 16-bit PNG stored value → calibrated CT Hounsfield units** from NLM original GE header, manufacturer/technical converter documentation and genuinely independent verification. Do not assume an offset of −1024 merely because it is mentioned in an old header; do not use a soft-tissue display window as rescale evidence.
3. Verify the *pixel-centre versus image-edge* origin interpretation independently against documented GE Genesis image geometry; include synthetic 0.5-pixel shift and out-of-plane rotation controls.
4. Revisit the existing 13,273-block occupancy view: dominant 92–96% connected components are not evidence of bone; check threshold sensitivity, islands, no implicit across-group topology welding. Complete segmentation only with source-supported bone labels.
5. Full-resolution source review of bony bilateral ASIS, sacrum/S1 endplate, pubic tubercles, acetabula and both femoral articular heads. Record physical scanner coordinates, pixel support, source digest and independent reviewer. **One cadaver cannot set the ideal 1.82m proportions.**
6. Apply independently verified geometry to an isolated correction candidate only when anatomical surface and coupling gates are satisfied. The skeleton, not the old mesh or skin, governs.

### Critical source references
- [NLM original Visible Human access and PNG description](https://www.nlm.nih.gov/research/visible/getting_data.html).
- [IDC independently documented CT conversion and intentionally removed gantry ImagePosition/ImageOrientation](https://github.com/ImagingDataCommons/NLM-Visible-Human-Project-DICOM-Conversion).
- Local `docs/WORK_PELVIC_CT_CONTINUATION_20261009.md` and `docs/NLM_72_CT_IMAGE_ORIENTATION_AUDIT_20261009.md`.
- Original 72-image pinned bundle: `ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_bundle_20261009.json`.

**Treat this as an evidence handoff. Anatomical source position, bone identity and clinical acceptance remain separate stages.**
