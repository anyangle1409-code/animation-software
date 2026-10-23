# Body v2 — rig side-label consistency, not anatomical certification

23 October 2026. READ-ONLY, laptop-independent audit on three preserved reconstructions.

## Provenance and integrity

Evidence is the three immutable model-inventory ZIPs from cloud Actions [run 40010003731](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731). Each was retrieved, inspected, and its ZIP SHA256 independently computed again:

| Model | Artifact | SHA256 verified |
|---|---|---|
| W8 | [12526515608](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731/artifacts/12526515608) | `7734eab2983e4abdb6b8b3e70c8b4dcc8098b46545b9e28ca9862872e3839f34` |
| V14 | [12524939485](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731/artifacts/12524939485) | `89830afbf8ffd5466c305365d8ec673b245725658a0bd9114fd0ae6bf70b958e` |
| R120 | [12525029273](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731/artifacts/12525029273) | `0cc37915ecb4fdb0b96e6d6fdcfc5920784d76bfa7c8fd1ee2b9e4575158a561` |

Each contains `rest_anatomy_inventory.json`, `inventory.json`, and `integrity_checks.json`; the latter three recorded PASS for numeric integrity only, `approval: NOT_GRANTED`.

## Coordinate convention measured

The rest-bone head coordinates below are *body-object local metres*, with the rig rest transform incorporated by the native audit. They are rounded to 6 decimal places.

| Check | W8 | V14 | R120 |
|---|---:|---:|---:|
| Total bones | 77 | 77 | 77 |
| Bilateral suffix pairs (70 bones) | 35 | 35 | 35 |
| Unpaired central bones | 7 | 7 | 7 |
| Pairs with `_l` rest-head X negative and `_r` X positive | 35/35 | 35/35 | 35/35 |
| Maximum absolute bilateral *rest-head X-magnitude* mismatch | 2.432 mm | 2.432 mm | 2.432 mm |
| Maximum bilateral *weight-group X-centroid magnitude* mismatch | 0.463 mm | 0.473 mm | 0.376 mm |

The largest paired rest-head X-magnitude asymmetry is at `muscle_pec_l` versus `muscle_pec_r`. This may reflect intentional geometry or the authored data; **it is not evidence of an anatomical defect**.

Seven unpaired central names: `root`, `pelvis`, `spine_01`, `spine_02`, `spine_03`, `neck`, `head`.

Sample coordinate values from the pinned W8 audit:
- `clavicle_l` head X = −0.020000 m; `clavicle_r` = +0.020000 m.
- `scapula_l` head X = −0.176500 m; `scapula_r` = +0.176500 m.
- `shoulder_cap_l` head X = −0.218913 m; `shoulder_cap_r` = +0.218912 m.
- `upperarm_l` head X = −0.218913 m; `upperarm_r` = +0.218912 m.
- Weighted centroid X `shoulder_cap_l` = −0.204354 m, `shoulder_cap_r` = +0.204361 m.

No cross-model rest-head/parent mismatch was detected at the rounded audit precision in the prior [cross-model report](PHONE_CLOUD_CROSS_MODEL_EVIDENCE_20261023.md).

## What this establishes and what it does not

**Established:** the stored *suffix-to-X-sign convention* is internally consistent across all 35 recorded bilateral pairs in these reconstructions. Named mesh weight-group centroids follow the same sign pattern, and the rest inventory does not show a global L/R swap *within its own coordinate system*.

**Not established:** whether negative body X is the subject's anatomical left versus the camera's visual left; whether a Blender display pose reverses apparent left/right; whether runtime's 67-bone bridge uses the same orientation; whether a left/right muscle attachment is biologically correct; whether the original unsaved Blender source used the same convention.

A prior handover warns that anatomical left (+X) may correspond to runtime `_r`. Treat that as an unresolved convention conflict: do **not** mark F-SIDE-001 resolved using this audit alone. The source code's own suffix convention does not independently certify anatomical laterality.

## Safe next evidence needed before muscle attachments

1. Ground native body/local X orientation against independent anatomical landmarks (e.g. sternum position, shoulder and pelvic markers) and a reviewed camera coordinate transform.
2. Compare authoring rig, runtime pose bridge and saved exercise-solver suffix mappings on at least one asymmetric test pose, including full shoulder elevation and contralateral side.
3. Verify the shoulder/arm bone attachments and joint motion anatomy independently. Only after that may any exercise-to-muscle contract map `_l` / `_r` to biological left/right.
4. Preserve original source SHA256 and keep all reports read-only; do not alter the validated skeleton, existing production, `PT_MODEL_VERSION 1.0`, or Claude branches.

**Gate:** internal naming consistency PASS; anatomical laterality NOT_GRANTED; muscle attachment BLOCKED.
