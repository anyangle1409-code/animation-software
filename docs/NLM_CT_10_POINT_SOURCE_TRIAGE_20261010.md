# ORIGINAL-v1 — Source-pinned CT proposed-pelvis-point rejection audit

**10 October 2026 · Anatomical status: NOT VERIFIED · Draft PR #19 only**

## Why this evidence matters

Earlier candidate points in ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_review_20261009.json used visual/source-review confidence values. These are NOT validated bony landmarks, osseous surfaces or approvals for canonical freeze. All ten proposed image pixels were examined against exact source-pinned NLM Visible Human Male 16-bit CT images and matching original GE scanner headers. The −1024 HU addend has already been independently reconciled with all 72 source PNGs and scanner records.

- Sources: 37 first-group slices, 35 second-group slices, with exact image/header SHA validation. NEVER silently co-register, bridge or weld the two acquisitions.
- Scanner frame: original scanner RAS millimetres. Positive R denotes anatomical right; all explicit left/right image-point labels have the expected sign.
- These are original centre-pixel HU values, NOT surrounding-ROI or inferred cortical HU.
- Code: scripts/anatomy_fit/nlm_ct_candidate_pixel_triage.py
- Source-pinned first successful original-pixel audit: https://github.com/anyangle1409-code/animation-software/actions/runs/38041987323
- Independent identity, registration to skeleton and first-pixel centre convention remain unresolved.

## Exact source-pixel results

A 300-HU threshold is an intensity sensitivity screen, NOT an anatomical bone classifier. An original point below 300 HU cannot seed a 300-HU connectivity reconstruction, but the anatomical structure might be present nearby or at another depth.

| Candidate observation | Original row, column | Centre HU | Passes 300 HU | Nearest intensity-only 300-HU lead in same slice, up to 32 px radius |
|---|---:|---:|:---:|---|
| cvm1764f right iliac blade | 285, 88 | −139 | No | None |
| cvm1764f left iliac blade | 280, 424 | −96 | No | Row 274 col 414; 411 HU; 10.48 mm |
| cvm1794f central sacrum | 322, 256 | 121 | No | Row 327 col 253; 306 HU; 5.24 mm |
| cvm1824f right iliac blade | 270, 93 | 26 | No | None |
| cvm1824f left iliac blade | 268, 418 | 60 | No | None |
| cvm1873f right femoral head | 270, 175 | 291 | No | Row 269 col 175; 337 HU; 0.90 mm |
| cvm1873f left femoral head | 270, 342 | 305 | Yes | Original pixel; 0 mm |
| cvm1873f right acetabulum | 257, 151 | 438 | Yes | Original pixel; 0 mm |
| cvm1873f left acetabulum | 257, 366 | 510 | Yes | Original pixel; 0 mm |
| cvm1903f central pubic region | 214, 256 | 38 | No | Row 218 col 255; 308 HU; 3.70 mm |

**Seven of ten fail 300-HU source-pixel seed screening. All five upper-group iliac/sacral points fail even 150 HU.** Three points have NO >=300-HU pixel within 32 image pixels (up to ~28.75 mm) on that same axial source image. This does NOT prove the absence of bone within 28.75 mm in 3D. None of the three high-HU pixels is a verified bone identity.


## NEW independent 35-slice hip joint connectivity contradiction (same source date)

The source-linked group-2 left femoral-head observation (cvm1873f row 270 col 342, 305 HU) and left acetabular observation (row 257 col 366, 510 HU) **both lie in a single 70,084-voxel, six-neighbour-connected candidate region at >=300 HU**, within ROI columns 275–449, rows 195–364, all 35 slices. The selected component contacts both ROI and acquisition end boundaries.

The source-linked group-2 right femoral-head observation (row 270 col 175, 291 HU) and right acetabular observation (row 257 col 151, 438 HU) **both lie in one 111,042-voxel region at >=150 HU**, in ROI columns 95–249, rows 195–364, all 35 slices. Again the selected component reaches ROI and source-slice end boundaries.

| Side | Source threshold | Both named candidate pixels meet threshold? | Same 3D HU component? | Interpretation |
|---|---:|:---:|:---:|---|
| Left | 300 HU | Yes | **Yes**, 70,084 voxels | Threshold cannot isolate head from socket on these seeds |
| Left | 500 HU | No — femoral candidate drops out | Indeterminate | Higher HU invalidates femoral original seed; surviving acetabular component 13,433 voxels |
| Right | 150 HU | Yes | **Yes**, 111,042 voxels | Threshold cannot isolate head from socket on these seeds |
| Right | 300 HU | No — femoral candidate drops out | Indeterminate | Higher HU invalidates femoral original seed; surviving acetabular component 68,206 voxels |

These **do not** prove actual femoral head and pelvis are fused or that the initial candidate labels are correct. They demonstrate failure of simple CT thresholding and six-connected voxel segmentation to separate the proposed joint structures in these ROIs. Anatomically labelled bone segmentation must use original source image interpretation and articular-joint boundaries; no global HU cut is a valid substitute.

Evidence: https://github.com/anyangle1409-code/animation-software/actions/runs/38042478442; original connected-region code in scripts/anatomy_fit/nlm_ct_source_component_stability.py. Reproducible, noncanonical snapshot: ORIGINAL_V1_WORK/anatomy/audit/nlm_ct_pelvis_pixel_and_hip_pair_rejection_20261010.json. The snapshot is machine-readable rejection evidence only and is not part of canonical skeleton geometry.

## Mandatory reviewer/Blender gates

1. **Preserve each original candidate coordinate** for audit traceability. Do not silently snap to the nearest bright pixel or treat a previous confidence score as anatomical verification.
2. Independently inspect each original exact source PNG and header, with correct scanner orientation and neighbouring CT slices. Revisit especially the extremely low/negative iliac points, sacral point and pubic point. Identify actual cortex, trabecula, articular surface and relevant anatomical boundaries.
3. Nearby 300-HU coordinates are **intensity-only navigation leads**. They do not establish a bone identity; they might be from the wrong structure, an artefact, or unrelated material.
4. After anatomical source identification, reviewers may generate an isolated provisional component using explicit --seed SLICE ROW COL in the same-group exporter. Never auto-select the largest HU component. Verify continuity, surface closure and clipping over multiple source planes, with independent clinical reference evidence.
5. Keep both image pixel-centre conventions explicitly unverified until pinned source geometry resolves FOV corner semantics. A scanner-to-HGPT/world rigid registration must be measured independently, and the two acquisition groups must not be artificially welded.
6. Only after all seven true osseous landmark requirements, complete named bone surfaces and registration are independently verified can readiness or canonical skeleton geometry be reconsidered. Assess articular joint motion and bilateral validity across poses; exercise skin/muscle deformation requires its own verification programme.
7. Preserve canonical a003, c001–c004 and approved skeleton-first rules. Do not approve c005 or merge/rewrite legacy V-series based on this CT intensity audit.

## Status

- Original candidate points accepted as verified bony landmarks: **0/10**.
- Required true osseous pelvic landmarks accepted: **0/7**.
- Whole skeleton regional readiness: **0 READY / 9 PARTIAL / 3 BLOCKED**.
- The 72 original images, GE headers and any derived OBJ geometries remain only in isolated temporary/private review storage, not the Git repository.
- This work **does not** establish the completed human skeleton, an accepted bone surface, a correct skin mesh, or realistic movement and exercise deformation.
