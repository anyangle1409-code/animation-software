# NLM full pelvic CT — 72 original image in-plane orientation preflight

**STATUS: independent source-safety engineering check, NOT a bone segmentation or anatomical target.** The current canonical source skeleton remains c004; anatomy readiness stays 0 READY / 9 PARTIAL / 3 BLOCKED.

## What the current Work checkpoint contained

- Original 72 NLM 512×512 CT images in **two physically contiguous source groups**, spanning original scanner superior positions **−342 mm to −553 mm**, with an **observed 2 mm physical slab overlap** at their group boundary.
- Published first-party scanner manifest validated 72 source hashes, centres, pixel spacings, slice thicknesses and axial normals.
- Blender 5.2.1 privately produced a **13,273-block** stored-image-value occupancy view. It had **eight 6-neighbour components** in the superior group and **three in the inferior group**, including dominant components representing 91.9% and 96.0% of group blocks. These numerical blocks are *not calibrated HU, confirmed cortical bone, a segmented human pelvis or a fit-ready muscle/skeletal surface*.
- At the point this branch was created, Work branch head `4fa41125`, Claude branch head `f3f725f4`.

## The previously unchecked source-data question

A CT image's scanner **centre, pixel spacing, slice thickness and normal** do NOT uniquely define where individual image pixels lie.

For example, rotating one 512×512 image **180° about its positive Z normal** preserves its centre, slice spacing, pixel dimensions and axial normal. All the original checks could pass while reconstructing that one slice backwards in 3D.

**A correct image-to-world mapping also requires the two source scanner row and column direction vectors** and an independently reviewed pixel-centre/edge origin interpretation.

## Deliverable

`scripts/anatomy_fit/nlm_ct_72_header_orientation_audit.py`:

1. Reads the existing 72-image source-bundle (no images or medical patient metadata are stored).
2. Fetches **only each original GE scanner text header** from the NLM allowlisted official HTTPS host, keeping downloads in process memory.
3. Verifies the **exact SHA-256 of every original header** against the 72 pinned source manifest rows.
4. Uses the existing strict privacy-filtered scanner-header parser, which emits only safe numeric fields and discards patient/operator identity lines.
5. Checks every slice's actual **top-left → top-right pixel-column vector** and **top-right → bottom-right pixel-row vector** against that slice's original image width/height, spacing, scanner centre and normal.
6. Confirms both vectors are perpendicular and their cross product agrees with the normal.
7. Fails closed if a slice is mirrored/rotated, if axes change within a group or change across the group boundary without independent registration, or if the original scanner headers/hash/centres change.
8. Returns **only aggregated group axis unit vectors**, 72-source SHA status and conservative unresolved-geometry flags.

The expected orientation for the earlier safely inspected GE frames was increasing image columns toward scanner **−R** and increasing image rows toward scanner **−A**, yielding scanner normal **+S**. That expectation is tested with synthetic original-sized frames; actual full-source verification must still be confirmed by a live CI run before claiming all 72 original headers agree.

### Regression suite

`scripts/test_nlm_ct_72_header_orientation_audit.py` tests all 72 source rows, safe source IDs, actual data immutability, axial handedness, source SHA mismatches, corrupted image centres, normal mismatch, 90°/180° frame rotation, one-sided reflection and intergroup orientation disagreement. An independent GitHub Actions job re-fetches only GE headers with bounded concurrency and no raw header exports.

### Limits and next meaningful Work step

Even a successful 72/72 source-header orientation audit **cannot confirm the origin refers to pixel outer corners rather than pixel centres**, cannot calibrate stored PNG scalars to Hounsfield units, cannot classify/segment individual human bones or correct skeletal joint surfaces.

Work should next: (a) independently verify the original NLM pixel-index origin conventions and PNG stored-scalar/HU mapping against scanner/converter documentation; (b) source-review 3D osseous morphology and separate non-bone/soft-tissue threshold islands; (c) reconstruct a true registered, physically sourced candidate bone surface; (d) identify ASIS, pubic tubercles, S1 endplate and both femoral articular surfaces with independent anatomical review; (e) keep candidate noncanonical until source/clinical validators permit progression.

**No c005, canonical skeleton, production skin, muscle or original rig changes are made.** No source image pixels are committed or distributed.
