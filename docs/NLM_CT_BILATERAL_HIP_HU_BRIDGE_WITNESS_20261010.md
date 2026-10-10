# ORIGINAL-v1 pelvic CT — bilateral joint intensity-bridge witness, no anatomy acceptance

**10 October 2026 · Noncanonical independent branch** `codex/hip-hu-bridge-witness-20261010`  
**Source:** 35/35 verified original NLM Visible Human Male group-2 CT PNGs and matching GE scanner headers.  
**Status:** SOURCE HU PATH VERIFIED; ANATOMICAL HEAD/SOCKET IDENTITY **NOT VERIFIED**.

## Why this was necessary

On PR #19 an independent original-pixel audit found seven of ten proposed pelvic pixels fail the 300 HU screen, and both proposed head/socket pairs can belong to the same HU-connected voxel region. A shared region alone does not say *how* the point hypotheses connect. A region could be linked via a distant 3D route or through ROI clipping. A physically weighted six-neighbour shortest route gives a falsifiable, reproducible intensity-only witness.

## What was built

- `scripts/anatomy_fit/nlm_ct_hu_bridge_witness.py` — **Dijkstra's shortest path in physical millimetres**, not unweighted voxel hops. Uses the actual GE scanner FOV spacing (approximately 460/512 mm in plane) and 3 mm per axial slice. The unresolved FOV half-pixel-centre convention cancels for *relative distances* but remains an explicit impediment to canonical world-space registration.
- Inputs are **exact original source-pinned candidate pixel IDs**, original CT PNG/header SHA checks, verified −1024 scanner HU addend, one acquisition group and manually bounded ROI. Fails on altered CT source identity, missing seeds, wrong group, excessive mask or invalid geometry.
- Output includes seed intensity occupancy, the shortest route's actual minimum source HU, number of physical axial source slices crossed, cut contacts, route length, direct reference distance, and no-anatomy-approval flags. It does **not** commit source imagery, derived meshes or path point lists.
- The independently pinned metrics are stored in `ORIGINAL_V1_WORK/anatomy/audit/nlm_ct_hip_intensity_bridge_rejection_20261010.json` and tested against *fresh original-source downloads* by GitHub Actions.

## Verifiable original-source outcomes

| Hypothetical hip candidate pair | HU threshold | Physically shortest HU path | Direct distance | Through how many axial source slices? | ROI or source cut touched by path? | Minimum actual path HU |
|---|---:|---:|---:|---:|---|---:|
| Right head pixel (270,175) → right socket pixel (257,151), cvm1873f | 150 | **33.242 mm** (38 samples) | 24.523 mm | **1** | **No** | **184 HU** |
| Left head pixel (270,342) → left socket pixel (257,366), cvm1873f | 300 | **36.836 mm** (42 samples) | 24.523 mm | **1** | **No** | **302 HU** |

These HU paths are contained *within the same original axial plane*, **not** excursions along an external 3D boundary. This falsifies the hypothesis that the earlier HU connectedness must be an ROI-edge detour. It **does not** verify that the underlying pixel hypotheses identify the intended bones, nor that there is actual contact between femoral head and acetabulum. Thresholding of CT tissue can create arbitrary routes through incorrectly grouped structures and partial-volume effects.

The right head original pixel at 291 HU falls below 300 HU; the left head at 305 HU falls below 500 HU. At the higher thresholds the original seed is unoccupied; no path comparison can be used to prove anatomical separation.

## Mandatory next anatomy-specific work

1. In private Blender/image review, display the original **cvm1873f axial CT plane**, and neighbouring original slices with scanner RAS orientation. Keep right and left laterality based on original GE geometry.
2. Independently confirm whether any original candidate head/socket pixel actually lies on a recognisable cortex, trabecular region or acetabular roof; record source images/planes used and reviewer uncertainty. Do not snap to nearby dense pixels automatically.
3. Outline two **anatomically distinct** femoral and pelvic articular surfaces *using original image evidence*, not shortest intensity paths, bright connected components, or image colour alone.
4. Check the joint gap, acetabular rim and neighbouring axial/coronal/sagittal interpretations; distinguish real structures from threshold partial-volume bridges. Record bilateral independent anatomical corroboration.
5. Only then review a correctly source-registered (not assumed) scanner-to-`hgpt_canonical_v4_original` transformation, and verify anatomy and motion over the wider skeletal programme.
6. Retain canonical a003 and c001–c004, never promote c005 or any mesh-adjusted skeleton geometry absent proven anatomical acceptance.

**Hard gate:** 0/7 true pelvic osseous landmarks approved; full skeleton readiness **0 READY / 9 PARTIAL / 3 BLOCKED**. This is useful candidate *rejection and review-navigation evidence*, not evidence that the skeleton is complete, bones touch, or that exercise motion is realistic.


## NEW: independent, first-party CT source review plate for Blender/laptop

`scripts/anatomy_fit/nlm_ct_private_slice_review_plate.py` now builds a **single self-contained, zoomable SVG**, with three original CT slices (`cvm1870f`, `cvm1873f`, `cvm1876f`) in **bone** and **soft tissue** HU windows. It adds coloured markers at the **four exact original source pixels**, with their actual source HU values. All markers are explicitly labelled **unverified candidate hypotheses, not bones**. No third-party imaging library is needed; PNG is encoded with Python's standard library.

For an approved private original-source folder containing the image and matching header bytes, run:

```sh
python3 scripts/anatomy_fit/nlm_ct_private_slice_review_plate.py \
  --ct-dir /private/nlm_original_ct \
  --bundle ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_bundle_20261009.json \
  --calibration ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_hu_calibration_20261009.json \
  --review ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_review_20261009.json \
  --group 2 --source-id cvm1873f \
  --out /private/ct_review/cvm1873_original_review.svg
```

Open the `.svg` locally in a browser for the actual medical-source review before Blender segmentation. The accompanying `.json` lists source pins and exact point HU values. **Neither file is uploaded to GitHub**. CI runs this against SHA-pinned original NLM source files in a short-lived private runner path, checks six embedded CT windows and all four point values, then discards those files. The source pixels are never treated as authoritative anatomical labels.

The plate is a visual review aid, *not* computer vision evidence of correct bone identity. A qualified independent anatomical interpretation is required to identify the actual hip joint boundaries and accept seven true osseous pelvic landmarks.
