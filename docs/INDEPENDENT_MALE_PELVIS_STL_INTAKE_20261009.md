# First-party male pelvic STL source intake (2026-10-09)

**STATUS: BONE SURFACE FILE INSPECTION TOOLING COMPLETE ONLY; NO ACTUAL EXTERNAL BONES INGESTED.**

## Independent bone-mesh source identified

The U.S. NIH 3D contribution **<https://3d.nih.gov/entries/3DPX-015682>**, version 2, publicly lists **seven separate STL files**:

| Bone | Source filename |
|---|---|
| Left os coxae | `Os_L_Male_Final.STL` |
| Right os coxae | `Os_R_Male_Final.STL` |
| Sacrum | `Sacrum_Male_Final.STL` |
| Left proximal femur | `Femur_L_Male_Final.STL` |
| Right proximal femur | `Femur_R_Male_Final.STL` |
| L4 | `4th-Lumbar-Vertebrae_Male_Final.STL` |
| L5 | `5th-Lumbar-Vertebrae_Male_Final.STL` |

[NIH 3D source entry](https://3d.nih.gov/entries/3DPX-015682) · [download entry](https://3d.nih.gov/entries/download/15682/2) · [NIH 3D Terms](https://3d.nih.gov/terms)

**CRUCIAL scientific/legal distinctions:**
- Contributor description: images were anonymised, then processed/sculpted to repair original imaging artefacts and restore anatomical teaching landmarks. Anatomist/surgeon reviewed their *teaching suitability*; these are **NOT raw unchanged CT-segmented surfaces** and NOT clinically calibrated anatomical coordinate references for this project.
- Description states the 3D PRINTS were made at **125% scale**. This does **not** prove downloadable STL files contain that scale! No arbitrary divide-by-1.25 operation is permitted.
- NIH 3D permits visitors to download but **entry-specific licences differ**, and the live entry's plain web text does not establish its exact CC/public-domain/commercial licence. Do **not** treat government hosting as confirmation of unrestricted redistribution/commercial rights.
- Native STL files have **NO embedded reliable length units or anatomical world-frame matrices**. Scale and transform must be independently reconstructed.
- These are one donor's pelvis-related parts, not a population-level 1.82m male anatomical target.
- No source mesh files have been downloaded, checked, mirrored, modified, redistributed or added to this repository.

### New manifest

`ORIGINAL_V1_WORK/anatomy/audit/nih3d_male_pelvis_mesh_source_manifest_20261009.json` records precise source entry/version and names, bone IDs, teaching-sculpt provenance, and UNKNOWN licence, scaling, CT original fidelity, pose and population status. It intentionally has no imagined SHA-256, mesh local-to-world mapping or patient stature and explicitly blocks canonical promotion.

## First-party read-only asset byte audit

`scripts/anatomy_fit/stl_bone_mesh_intake.py`, a Python-standard-library-only script:

- parses actual **binary and ASCII STL** triangle data; robustly handles binary files whose header happens to begin with `solid`;
- rejects truncated/inconsistent binary lengths, malformed triangles, nonfinite vertex coordinates and degenerate facets;
- scans triangle counts, native-unit bounding box/diagonal and area without copying whole meshes into memory;
- computes the SHA-256 hash of the exact mesh *bytes*, optionally verifies it against a separately provided pinned digest;
- optionally computes distance between a reported local candidate landmark and the nearest ACTUAL triangle vertex. Unlike trusting a JSON assertion, this requires mesh bytes; it still cannot establish feature identity.
- checks seven filename-to-bone-ID mappings and requires source manifest status/identity.
- deliberately rejects previously unverified scaling and orientation even if manually inserted into source manifest.

**The tool NEVER converts an STL to the project coordinate frame or accepts a physical ASIS, pubic tubercle, femoral head or S1 endplate landmark.** A finite position on the source mesh could be any vertex, and its anatomical semantic identity still requires independent review.

Outputs always include:
- `entry_licence_verified: false`
- `source_mesh_scale_verified: false`
- `world_transform_verified: false`
- `bone_anatomical_geometry_verified: false`
- `bone_surface_reconstruction_permitted: false`
- `canonical_promotion_allowed: false`

No third-party runtime/toolchain package is installed, and the canonical skeleton, c004, the rejected P003 and provisional P004–P007, muscle/skin/rig assets, and Claude work remain unchanged.

### Reproduce tests

```bash
python3 -m unittest discover -s scripts -p 'test_stl_bone_mesh_intake.py' -v
```

The unit suite creates tiny **synthetic binary/ASCII STLs** in a temporary directory. It checks byte hashes, truthful mesh membership, nonfinite/degenerate/truncated geometry, wrong bone identity, unit/licence inference, lack of false acceptance and input immutability. **These tests are NOT a test of real NIH3D files and not an anatomical validation.**

When the entry's licence and file-scale provenance are confirmed, the actual individually downloaded STL can be inspected locally with:

```bash
python3 scripts/anatomy_fit/stl_bone_mesh_intake.py \
  --manifest ORIGINAL_V1_WORK/anatomy/audit/nih3d_male_pelvis_mesh_source_manifest_20261009.json \
  --bone-id hip_bone_left \
  --mesh /local/private/path/Os_L_Male_Final.STL \
  --expected-sha256 <EXACT_INDEPENDENTLY_KNOWN_DIGEST>
```

Omit the digest rather than fabricate it if no independent reference exists; the report will explicitly mark byte identity as unverified. Do not commit or redistribute 3D model bytes before licence review.

## Optional NLM original CT acquisition pilot (separate from sculpted meshes)

The NLM itself exposes lossless PNG-converted **original radiological CT** source images, rather than NIH 3D's sculpted teaching STL. See NLM's [Getting the Data](https://www.nlm.nih.gov/research/visible/getting_data.html) and the official [male normal CT PNG index](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/index.html).

The independent first-party utility `scripts/anatomy_fit/nlm_original_ct_png_probe.py` (Python standard library only) has a deliberately tiny allowlist:

- `cvm1012f.png` (indexed by NLM at **208,501 bytes**);
- `cvm1013f.png` (indexed at **193,332 bytes**).

Its opt-in `--download` mode fetches only from the exact official `data.lhncbc.nlm.nih.gov` URL, refuses redirects and existing output paths, caps the response size at **2 MiB**, verifies the PNG header and CRC of **every chunk**, and computes SHA-256 of the source bytes. The CI pilot keeps downloaded slices only in the GitHub runner's `$RUNNER_TEMP`; the original pixels are **never committed to GitHub**, redistributed, turned into meshes or fitted to the skeleton.

**Verified live original-source pilot (2026-10-09, GitHub Actions [run 37927362119](https://github.com/anyangle1409-code/animation-software/actions/runs/37927362119)):**

| Original NLM frame | PNG bytes | Format | Actual PNG SHA-256 |
|---|---:|---|---|
| `cvm1012f.png` | 208,501 | 512×512, 16-bit grayscale | `d771fb0b004a4189d200fdce3af97329990bdf9971a74e86f5cb1bdd72d7e0c6` |
| `cvm1013f.png` | 193,332 | 512×512, 16-bit grayscale | `449c665c97d2f4e093fd1434656ba1c5ac0f31a4dc07d189bde432dd49c3a77d` |

Both files were retrieved directly from the NLM HTTPS host to `$RUNNER_TEMP`, every PNG chunk CRC passed, both SHA-256s were printed and the same temporary bytes passed subsequent inspection. **No images were added to the repository or retained as downloadable artifacts.** These SHA values are now pinned in `ORIGINAL_V1_WORK/anatomy/audit/nlm_original_ct_png_pinned_preview_20261009.json`; the live pilot requires exact digest matches before treating source-file identity as checked. A future NLM source update must be reviewed explicitly rather than silently accepted.

### Original GE CT scanner header and physical geometry

The NLM exposes each original scanner text header separately under
[normalCTHeaders](https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCTHeaders/index.html).
The independently checked original `cvm1013f.txt` and `cvm1014f.txt` fields establish:

| Original scanner geometric field | `cvm1013f.txt` | `cvm1014f.txt` |
|---|---:|---:|
| Image matrix | 512×512 | 512×512 |
| In-plane pixel spacing | 0.488281 mm each axis | 0.488281 mm |
| Slice thickness | 1 mm | 1 mm |
| Nominal separation | 1 mm | 1 mm |
| Image-location superior scanner coordinate | +389 mm | +388 mm |
| Top-left scanner R/A/S coordinates (mm) | (+123,+125,+389) | (+123,+125,+388) |
| Top-right scanner R/A/S coordinates (mm) | (−127,+125,+389) | (−127,+125,+388) |
| Bottom-right scanner R/A/S coordinates (mm) | (−127,−125,+389) | (−127,−125,+388) |

These values are scanner **RAS** coordinates, **not HGPT world** skeletal coordinates. The 512×0.488281≈250 mm source field-of-view matches the displayed 250 mm corner geometry, and the adjacent locations differ by exactly 1 mm. Pixel *centre* versus image-corner origin interpretation, original anonymisation/registration, and CT HU calibration from PNG remain to be independently checked. The source header mentions a −1024 Hounsfield annotation offset, but we must not apply it blindly to PNG pixel values without verifying conversion data semantics.

**Privacy filtering:** `scripts/anatomy_fit/nlm_ct_scanner_geometry_header.py` extracts only a fixed allowlist of numeric geometry fields and emits NO historical patient names, patient IDs, hospital or operator fields. The raw header remains in temporary process memory, and its SHA may be recorded without uploading its contents. The `--check-adjacent-pair` mode requests only the two pinned NLM originals, verifies physical geometry consistency and never promotes a skeleton. `scripts/test_nlm_ct_scanner_geometry_header.py` includes synthetic metadata carrying intentionally fake confidential placeholders and confirms none appear in reports or errors.

The two source frames are **not located/labeled as pelvis slices** and their physical position, original 12-bit CT calibration, voxel origin, Hounsfield units and reconstructed axial scan registration remain **UNVERIFIED**. A valid 512×512 pixel header and CRC are container-integrity tests, not source anatomy or source-patient identity validation. Further scanner-header study and contiguous pelvic slice segmentation are needed for osseous pelvis landmark evidence.

`scripts/test_nlm_original_ct_png_probe.py` runs 14 synthetic **offline** CRC, header, malformed/truncated PNG, allowlist, file identity, create-only output and no-anatomy-claim tests. The `original-ct-pilot` job of `.github/workflows/independent-pelvis-stl-intake.yml` separately tests live network access. A failed network test must be reported as a source-acquisition blocker, not concealed by green offline geometry tests.

## Next actionable research and engineering gates

1. Obtain and record **exact per-entry licence** and whether downloaded STLs correspond to original 1:1 patient geometry or only print/sculpted geometry.
2. Obtain source data with independently verified units and coordinate transforms. Consider NLM original CT where authorised; it too is single-donor reference, not a population target.
3. Run first-party import byte/geometry tests and verify physical osseous landmark identity visually/anatomically, using bony ASIS, pubic tubercles, S1 endplate and femoral head articular features; never copy old skin mesh landmarks.
4. Register surfaces into canonical skeletal frame only after anatomical evidence independently agrees. Use the separate `bone_feature_observation_packet.py` / `pelvic_app_bone_frame.py` math, preserving explicit anatomical review status.
5. Re-evaluate S1 relative to the hip axis in osseous APP frame using multi-subject published cohorts and independent source geometry. Only then consider correction of the lumbar, ribs, sternum and SC/AC/GH system.
6. Never merge these diagnostics as a c005 canonical correction or fit final muscle/skin to them.

**Canonical readiness unchanged: 0 READY / 9 PARTIAL / 3 BLOCKED.**
