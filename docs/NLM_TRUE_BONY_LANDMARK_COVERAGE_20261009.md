# Real CT candidate-region observations versus required bony landmark evidence

**Status: source-image review candidates only, zero independently validated physical bony landmarks.** All CT scanner frames and the original skeleton remain unchanged.

## What was actually audited

The existing 72 NLM Visible Human male CT source-frame manifest contains 37 original slices in the superior 3-mm group and 35 original slices in the inferior 3-mm group. The physical axial 3-mm slab ranges are **scanner S −451.5 to −340.5 mm** and **−554.5 to −449.5 mm**, respectively, overlapping by 2 mm. That is verified scanner coverage, **not** proof of complete pelvic anatomical coverage.

The pre-existing anatomical review has exactly **ten provisional observations**: four labelled iliac blade (two left, two right at −372 and −432 mm); one broadly labelled sacrum at −402; bilateral candidate femoral head regions and bilateral acetabular regions at −481; and one unsided pubic region at −511 mm. Their source-image SHA-256s, scanner S and pixel locations are checked against the live Work source bundle. None is clinically verified as a discrete required landmark.

## Seven physical osseous features required before APP geometry can be justified

| Required osseous physical landmark | Currently available *region* evidence | Why this remains unverified |
|---|---|---|
| Left bony ASIS | Left iliac blade in two source levels | The iliac blade is not a selected anterior superior iliac spine surface vertex |
| Right bony ASIS | Right iliac blade in two source levels | Same: neither a physical bony ASIS vertex nor second reviewer identified |
| Left pubic tubercle | One unsided central pubic **region** observation | No left true bony tubercle is labelled or surface-verified |
| Right pubic tubercle | One unsided central pubic **region** observation | No right true bony tubercle is labelled or surface-verified |
| S1 superior endplate centre | One central sacrum pixel candidate | No source S1 rim, endplate edges, centroid construction or independent reviewer |
| Left femoral-head articular centre | Left candidate femoral head region at one axial level | No 3D fitted original articular sphere or validated surface |
| Right femoral-head articular centre | Right candidate femoral head region at one axial level | No 3D fitted original articular sphere or validated surface |

## What is newly verified in software

- Original NLM scanner header axes are verified from earlier PR #16: **column index increasing toward scanner −R**, row toward **−A**, normal **+S**. The review's existing left/right candidate pixels agree with patient-R scanner laterality (right candidates at positive R, left at negative R). That is an orientation consistency check, not bone identity verification.
- Conditional `scanner RAS` coordinates and 0.449219 mm half-pixel / 1.5 mm half-slice sample envelopes are calculated from source physical dimensions while **retaining an explicit unverified pixel-corner-versus-centre convention**; they are never claimed as exact bony position measurements.
- The machine-readable output counts review candidate regions separately from the exact seven landmark definitions, and always returns **0 genuinely verified physical bony landmarks** and `canonical_promotion_allowed:false`.
- Synthetic mutation tests reject wrong laterality, wrong original image SHA, wrong scanner S, missing observations, fake anatomical acceptance, noninteger out-of-frame image pixels, and accidental input modification.

## Work and Claude next actions (avoid duplicate work)

Work can skip re-auditing the ten candidate observation locations, scan-group physical coverage, source laterality and candidate-versus-true-bone distinction. Instead its next valuable work is HU/scanner-value calibration, true bone surface extraction and matching **3D** osseous features from a sufficiently wide continuous original CT volume.

Claude can use the existing scanner-labelled images in Blender for *independent* second review of the seven true features, annotating exact source SHA, image/row/column, level, and multiple planes; the single donor does not define canonical male population proportions.

Do not promote a generic label such as `iliac_blade` to an `ASIS` with a renamed JSON key. Require source geometry, clinical independent labels, and cross-frame evidence. Do not change frozen canonical bones, muscles or skin to match these observational review pixels.

**Existing anatomical readiness remains 0 READY / 9 PARTIAL / 3 BLOCKED.**

## Completed original-source result and Work offload

The actual previous GitHub test run [38002224146](https://github.com/anyangle1409-code/animation-software/actions/runs/38002224146) passed **52/52 tests** after correcting a real left/right label conflict: the semantic candidate label, observation ID and physical scanner side now agree or fail closed.

The original 72-image source manifest and ten Work candidate observations were processed into a pinned, source-safe, machine-readable result at `ORIGINAL_V1_WORK/anatomy/audit/nlm_ct_true_osseous_landmark_coverage_verified_20261009.json`. That JSON preserves the exact ten candidate observation SHA-256s, level positions, unverified origin convention, available source group physical extents and seven failed true-osseous-evidence gates. No medical images, unfiltered private CT header text, or production assets are committed.

**Work may now skip manual reconciliation of these ten review observations, cross-source hashes, scanner laterality, source slab envelopes, and the definition-versus-region gap.** The next actual milestone is to independently identify and fit the true 3D physical bony features from correctly registered original source CT, obtaining genuinely independent review and adequate reference population evidence. A single plausible CT slice point must not be silently promoted to an ASIS or femoral-head centre.

A subsequent extra two source-result immutability tests and the pinned report trigger have been added; read their latest GitHub CI status before declaring the final expanded focused suite complete.
