# NLM original CT — 12-slice scanner-located pelvis-region scout (2026-10-09)

**STATUS: SCANNER LOCATIONS AND SOURCE BYTES VERIFIED. ANATOMICAL REGION NOT VERIFIED.** No CT image bytes are stored in the repository; no physical pelvic landmark, scanner-to-HomeGymPT frame transform, segmentation, bone geometry, bone candidate or canonical anatomy accepted.

## What was independently executed

The [official U.S. National Library of Medicine original normalCT index](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/index.html) lists the original radiological PNG frames. In [GitHub Actions run 37929286672](https://github.com/anyangle1409-code/animation-software/actions/runs/37929286672), `scripts/anatomy_fit/nlm_pelvis_region_scout.py`:

1. Loaded 12 explicitly allowlisted NLM PNG frames directly from the original HTTPS custodian.
2. Validated PNG chunk CRC, format and SHA-256; decoded every 16-bit, 512×512 grayscale pixel via a **first-party streaming-limited PNG filter implementation**. No PNG-to-Hounsfield calibration or density threshold is asserted.
3. Independently fetched each paired original GE scanner header, processed only a safe numeric field allowlist (no private identifiers) and recorded actual scanner **RAS** positions, per-frame pixel spacings and slice thicknesses.
4. Printed only SHA-256, geometry and raw intensity histograms/percentiles. Raw original pixels and raw scanner-header text **were never committed, attached, retained or redistributed**.
5. Pinned every source PNG and scanner-header SHA-256 in `ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvis_scout_pinned_source_positions_20261009.json`.

| NLM frame | Physical scanner superior Z (mm) | Pixel spacing (mm) | Thickness (mm) | Anatomical region confirmed? |
|---|---:|---:|---:|---|
| `cvm1300f` | +102 | 0.898438 | 3 | No |
| `cvm1399f` | +3 | 0.898438 | 3 | No |
| `cvm1451f` | −54 | 0.898438 | 3 | No |
| `cvm1500f` | −108 | 0.898438 | 3 | No |
| `cvm1551f` | −159 | 0.898438 | 3 | No |
| `cvm1602f` | −210 | 0.898438 | 3 | No |
| `cvm1650f` | −258 | 0.898438 | 3 | No |
| `cvm1701f` | −309 | 0.898438 | 3 | No |
| `cvm1752f` | −360 | 0.898438 | 3 | No |
| `cvm1800f` | −408 | 0.898438 | 3 | No |
| `cvm1906f` | −514 | 0.898438 | 3 | No |
| `cvm1948f` | −556 | 0.898438 | 3 | Original NLM pelvis gallery shows an image labelled *upper thigh below femoral heads*, but the correspondence should still be checked |

### Critical geometry discovery: filename number is NOT scanner Z

- The filename index difference `cvm1399→cvm1451` is 52, but the real scanner position changes **57 mm**: from +3 to −54.
- `cvm1451→cvm1500` is a filename difference of 49 but a scanner movement of **54 mm**.
- Therefore a calculation such as `scanner_S = 1402 − filename_number` does NOT hold across the archive. The source must be reconstructed using **each file's own header**, not a guessed global origin/offset.
- Elsewhere the normalCT archive uses 1 mm thick 0.488281 mm pixels; these inspected 12 images are **3 mm** thick and 0.898438 mm per pixel. A universal 1 mm isotropic volume reconstruction would produce unacceptable geometric distortion.
- With 3 mm slice thickness and a single cadaver, the source is suitable to investigate gross bony morphology, **not** a submillimetre articular-surface or 1.82 m anthropometric target. Any quantitative accuracy claim requires slice-gap/interpolation/error analysis and independent references.

### What can be concluded?

The PNG and corresponding original scanner text files **are real, accessible and numerically registered to the original scanner RAS frame**. The code returns a source SHA fingerprint and stores no pixel data. However the **bone-to-pixel semantic identity has not been established**: a numerical mean/99th percentile cannot identify pelvic ASIS, S1 endplate, hip centre or cortical bone reliably. Nor are stored scalar values established as true calibrated Hounsfield units: the original scanner mentions a −1024 annotation offset, but its application to the PNG conversion pipeline remains unverified.

The 1948 NLM gallery source is available [as the original pelvis-labelled example](https://www.nlm.nih.gov/research/visible/fresh_ct.html). It explicitly illustrates an **upper thigh below femoral heads**. That is an *exclusion/fiducial reference*, not proof any of the other specific images contains the desired landmark.

## New software and verification

- `scripts/anatomy_fit/nlm_pelvis_region_scout.py`: byte-limited NLM-only scout, complete 16-bit PNG row filter decoder (0–4), privacy-filtered scanner positions and noncanonical raw-intensity summary.
- `scripts/test_nlm_pelvis_region_scout.py`: first-party synthetic PNG decoding, filter, CRC, malformed-asset, patient-field exclusion, actual-pinned manifest and file-number scanner-gap tests.
- `ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvis_scout_pinned_source_positions_20261009.json`: live-run original PNG+scanner header SHA and actual scanner position matrix per source image, **no raw medical images**.
- GitHub Actions workflow verifies source bytes and header positions against previously pinned SHA on re-download. Source custodial changes **fail closed**, rather than silently introducing new body geometry.

Command (source access required):

```bash
python3 scripts/anatomy_fit/nlm_pelvis_region_scout.py --live-scout \
  --pinned-manifest ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvis_scout_pinned_source_positions_20261009.json \
  --slice-ids 1300 1399 1451 1500 1551 1602 1650 1701 1752 1800 1906 1948
```

## Follow-on source pixel coordinate envelope (no bone identity)

`scripts/anatomy_fit/nlm_ct_pixel_ras_envelope.py` is a separate, read-only first-party mapper. Given a **source scanner geometry report** and a future human-reviewed `(row,col)` image index, it returns:

- a candidate **pixel centre in original scanner RAS coordinates**, conditional on an explicitly **unverified outer-FOV-corner origin convention**;
- the **four pixel-cell corner coordinates** for the same stated convention;
- a **3 mm thick axial slab**, centred on the slice location and extending ±1.5 mm along scanner S;
- the original 0.898438 mm in-plane pixel step and approximately **0.449219 mm half-pixel extent** on each axis.

These are *physical sampling bounds*, not measurement precision, clinically validated landmark position, HU density calibration or independent bone-source identification. The true voxel index to patient-space sample-centre convention, image registration, pixel-array axis direction and scanner-to-Home Gym PT canonical world transform must be checked before the point becomes a geometric anatomical observation.

`scripts/test_nlm_ct_pixel_ras_envelope.py` adds 15 independent tests on known original GE scanner corner coordinates for `cvm1300f`, including edge and last-pixel placement, handedness, frame translation invariance, pixel selection bounds, 3 mm slab, false-approval flags and malformed scales. No patient identifiers or image pixels are emitted.

## Visual triage bridge for Claude (coarse signal only)

A new optional `--density-ascii` option to the 16-bit source scout creates a **32×32 lossy tile summary** from the *fraction* of original stored image values above two deliberately provisional raw-scalar thresholds (1200 and 1600). It is off by default, used only on an explicit subset of original NLM frames, and does **not** export source PNG bytes or original identifying header fields. Such a grid is **not a clinical CT image**, cortical bone classification, Hounsfield-calibrated threshold, named bone localisation, or a substitute for reviewing full-resolution slices.

Successful GitHub Actions [review run 37939278584](https://github.com/anyangle1409-code/animation-software/actions/runs/37939278584) confirms working source previews for `cvm1451f` (scanner S −54), `cvm1602f` (−210), `cvm1752f` (−360) and `cvm1800f` (−408). The coarse patterns vary substantially between source levels; they **do not establish** a pelvis/femoral-head/sacral slice identity. Claude's laptop should use the source PNG image itself, not this downsampled map, for landmark annotation.

A dedicated laptop handoff now exists at `docs/CLAUDE_BLENDER_PELVIS_CT_LAPTOP_HANDOFF_20261009.md` covering source hashes, known physical scanner levels, copy-safe worktree isolation, bone features to label and independent Blender review deliverables. No laptop work or additional user approval is required just to perform source-review research; **canonical anatomical acceptance remains blocked** until geometric and biological evidence gates genuinely pass.

## Immediate anatomical next gate

Review selected original **source images in physical sequence** against a qualified labelled pelvic CT atlas and visually identify the sacral promontory, osseous bilateral ASIS, pubic tubercles, acetabula and left/right femoral head surfaces, recording the relevant scanner RAS Z ranges. Then verify HU pixel coding with manufacturer/original converter evidence and the voxel/sample-centre convention; segment relevant **continuous** scan groups rather than sparse scouting frames, validating topology and source resolution before selecting any landmark coordinate. Finally compare against independent clinical 3D CT population measurements and map to the project coordinate frame. These steps have **NOT** been completed.

Canonical skeleton remains **0 READY / 9 PARTIAL / 3 BLOCKED**. This exploratory source evidence must never deform approved bones to match skin or old models.
