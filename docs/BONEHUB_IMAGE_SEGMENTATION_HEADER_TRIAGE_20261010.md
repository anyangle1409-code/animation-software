# Bounded image and segmentation header triage

Source-only follow-on to `fc6c639d` and Work PR34. No CT-to-HGPT transform,
accepted surface units, joint centre, fragment removal or geometry change.
Frozen upstream revision `ac8de2b38f5ae1a0996053ca0639dd6ae43358f1`.

## Fully verified small segmentation objects

From `visible_human_3d_models/CT/Segmentation/01_Male/`, immutable HF tree LFS
OIDs and byte counts compared with each complete downloaded object:

| File | Bytes | Exact SHA256 |
| --- | ---: | --- |
| FOOT_LEFT.seg.nrrd | 1101484 | acb38f4c4f6af83f580160ebd044d30f2908739e4670122823c13e8bfa60d964 |
| HAND_RIGHT.seg.nrrd | 1080518 | 94f70b738d823f70d4cf1f12f32cf44a7221f38ff8627a5c3c8c9ab60685d2dd |
| THORAX.seg.nrrd | 719376 | 786da6e14d9e57e9622ff74f49bfc0f9fae4ce99946149ddc41a73773dc04f46 |

All three actual headers declare `space: left-posterior-superior`, origin0/0/0,
domain directions(0.9375,0,0)/(0,0.9375,0)/(0,0,1), gzip-encoded unsigned char,
spatial sizes520/552/1873. Foot/hand have a **two-layer list axis**, dimensions
2/520/552/1873; thorax is3D. Never read layered files as a flat3D label map.
`Segment14_Name:=HAMATE_RIGHT`, label3, layer1 demonstrates why layer matters.
Segment status tags include `inprogress`; upstream segmentation is not accepted
anatomical truth. No explicit `space units:` field in any of these three headers.

Exact header-only SHA256s (bytes before first LF/LF, not including separator):
foot`c49c24cd203b12b8be73653d0a5bbe62a8b44a5c990c19dc0ee2d84225ca0a35`,
hand`f83a2b2d1da489a699d570266dd1ce3dff22890378dfa955e6e8ccaddce72e6f`,
thorax`8747b44c8155818e2fd9b7c4bdb39e0a2992f9661635c4c7e0a5e9692524f13b`.
[NRRD specification](https://teem.sourceforge.net/nrrd/format.html) distinguishes
list/domain axes, space directions, origin and optional units. These header
values define a label-grid coordinate declaration; no payload registration test
has yet been performed. Compressed size hides substantial decoded volume:
foot/hand each1,075,251,840bytes, thorax537,625,920bytes. Avoid eager decoding.

## Partial image prefix, not full image verification

Immutable image metadata: `CT/Image/01_Male.nii.gz`,418636727bytes;
upstream LFS SHA256`2ad6bb4129aa529e0d8d0f059694fccb4d996867cff3cfdf3c1cf1f4250fc776`.
**The full image was NOT downloaded or hash-verified.** Requested only
bytes0–65535; actual HTTP206 Content-Range`bytes 0-65535/418636727` was checked.
Private prefix SHA256
`6d20b86aa76ace5a82a1b3219a40e3bae3f676eb33020feafc8c7a71aeee010b`.
Gzip decoder limited to352output bytes; no image-pixel decoding undertaken.

Actual NIfTI-1 header: size348, magic`n+1\0`, spatial dimensions520/552/1873,
pixdim0.9375/0.9375/1; xyzt_units10, qform_code1, sform_code1.
Sform RAS rows(-0.9375,0,0,0)/(0,-0.9375,0,0)/(0,0,1,0).
Quaternion b/c/d=0/0/1 with qfac1 and offsets0/0/0, consistent with that sform.
[Reference NIfTI header implementation](https://github.com/NIFTI-Imaging/nifti_clib/blob/master/niftilib/nifti1.h)
defines MM=2, SEC=8;10declares spatial millimetres plus temporal seconds.
[Official NIfTI coordinate documentation](https://nifti.nimh.nih.gov/nifti-1/documentation/nifti1fields/nifti1fields_pages/qsform.html/document_view.html)
defines RAS voxel-centre coordinates. Flipping only RAS X/Y signs gives an LPS
grid with the same direction/origin declarations as these segmentation headers.

This is **header-level declared image/segmentation-grid compatibility**, not
full-image byte verification, voxel correspondence, segmentation accuracy, raw
NLM scanner registration, or established STL physical scale. Do not silently
replace source-unit labels in prior reports with mm or install any model transform.
BoneHub derives from aligned/rescaled CT; original raw NLM coordinates differ.

## Next safe action

Develop tested bounded streaming label sampling that respects layers, checks
exact gzip decoded length/trailer and avoids allocating a1GB volume. Compare
small component locations with their upstream label values, initially foot,
then thorax/hand. Surface smoothing means nearest-voxel membership alone cannot
certify anatomical contact or justify island deletion. A full immutable image
download, if later needed, must pass its full LFS hash before accepted pixel use.
All medical objects/prefixes remain private outside Git.

## Subsequent bounded label sampling

Implemented `source_segmentation_stream.sample`: grid indices only, no geometry
transform or unit acceptance. Three actual private objects were read through
their entire gzip streams in bounded512KBchunks; CRC/trailer and exact decoded
sizes verified (foot/hand1,075,251,840each; thorax537,625,920). No decoded volume
allocated or saved. Eleven synthetic tests PASS: hand-derived fastest-axis/layer
order, duplicate/unsorted samples, split chunks, truncation/extra bytes, corrupt
trailer after requested sample, unsupported frame/type/encoding/duplicate fields,
detached/skipped payloads, invalid layer/indices, malformed spatial syntax and
oversized decoded budget. Independent reviewer ran the first10tests and found
the malformed-spatial-field gap; exact refusal regression RED -> GREEN observed.
Both Windows/Linux CI configured; new sampler checkpoint CI still pending.

One diagnostic invocation **assumed**, did not accept, mesh coordinate units
matching these header grid units. Source triangle-area centres were divided by
0.9375/0.9375/1, nearest index selected with floor(index+0.5), then27grid points
in a3x3x3neighbourhood sampled in the source segment's named layer. Mathematical
centres are not bone landmarks and need not lie on/in a curved source shell.

| Small component | Faces | Assumed nearest XYZ | Named label | Own-label samples /27 |
| --- | ---: | --- | ---: | ---: |
| Calcaneus left | 196 | 451/264/110 | 2 | 23 |
| Intermediate cuneiform left | 48 | 439/252/105 | 5 | 8 |
| Talus left | 2 | 451/268/112 | 1 | 4 |
| Rib1left | 2 | 370/115/1587 | 2 | 1 |
| Rib3left | 8 | 376/116/1585 | 4 | 1 |
| Rib4left | 64 | 467/111/1585 | 5 | 10 |
| Rib4left | 8 | 438/116/1586 | 5 | 1 |
| Rib4left | 6 | 459/115/1585 | 5 | 1 |
| Rib4left | 6 | 466/115/1586 | 5 | 1 |
| Rib4left | 4 | 429/116/1585 | 5 | 1 |
| Rib4left | 2 | 445/119/1585 | 5 | 1 |

All11small-component centre samples equal their named upstream label. This is
consistent with their presence in upstream label data, not proof of bone
identity or correct segmentation. Do not describe all detached components as
STL-only exporter mistakes or erase them without independently verified anatomy.
Main-shell hamate sample136/123/1070 is label3 on layer1 (27/27neighbours), while
main rib1right/rib3left/rib4left mathematical centres have0/27own-label samples;
rib1left centre is0but8/27neighbours match. Rib curvature explains why a surface
average may lie off the bone; these observations neither prove a registration
defect nor provide usable rib landmarks. No anatomical readiness changed.

Next: test targeted surface-point/voxel correspondence and inspect label-image
overlays before any articular/fragment interpretation; retain unaccepted scale
relation and raw-NLM registration barriers. Full CT image remains unverified.

## Subsequent complete image acquisition and bounded pixel read

The earlier partial-only state is superseded: full male image now privately
downloaded with exact418,636,727-byte size and upstream LFS SHA256
`2ad6bb4129aa529e0d8d0f059694fccb4d996867cff3cfdf3c1cf1f4250fc776` verified.
No CT bytes committed. `source_nifti_pixel_stream.sample` verifies the complete
compressed hash before/after a read-only bounded512KBstream, checks gzip CRC and
exact1,075,251,840decoded pixel bytes. Actual datatype512/bitpix16 is **unsigned16**;
vox_offset352, slope1/intercept0. Do not reinterpret as signed16 or silently apply
a guessed -1024/-1000HU calibration. Header scalar scaling does not prove HU.
Seven synthetic tests PASS after observed missing-feature RED; new pixel CI pending.

Twenty-one requested source-grid pixels sampled:19component mathematical centres
plus two nonanatomical grid controls. No surface/image registration accepted.

| Small component | Faces | Actual stored unsigned16 CT value at assumed centre index |
| --- | ---: | ---: |
| Calcaneus left | 196 | 1356 |
| Intermediate cuneiform left | 48 | 1498 |
| Talus left | 2 | 1434 |
| Rib1left | 2 | 19 |
| Rib3left | 8 | 13430 |
| Rib4left | 64 | 29 |
| Rib4left | 8 | 11 |
| Rib4left, XYZ459/115/1585 | 6 | 22 |
| Rib4left, XYZ466/115/1586 | 6 | 6 |
| Rib4left | 4 | 25 |
| Rib4left | 2 | 47290 |

These diverse values under identical source label names demonstrate why label
membership is insufficient for independent bone acceptance. Values are not
calibrated HU and no bone threshold was applied; single mathematical-centre
samples alone cannot classify anatomy, especially curved main rib shells.
Candidate investigation must inspect actual spatial patches, source intensity
calibration and correspondence before treating source labels as trusted anatomy.

Sampler implementation560a8083 subsequently passed actual CI38076420293 all3jobs;
11new label tests on both OS, native Blender and unchanged reconstruction checks.
Clean short detached checkout62targeted tests PASS in14.586seconds.
