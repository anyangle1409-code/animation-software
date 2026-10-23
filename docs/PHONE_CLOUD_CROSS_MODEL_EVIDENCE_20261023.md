# Home Gym PT: verified cloud rest-audit comparisons — 23 October 2026

**Scope:** read-only numerical evidence from reconstructed W8/V14/R120 files. **NOT** original reconstruction acceptance, anatomical approval, or permission to attach muscles.

## Verified source evidence

Cloud run [40010003731](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731) passed all W8/V14/R120 Blender 5.2 jobs and produced three report archives. Each archive was independently downloaded and its ZIP SHA256 computed; results exactly matched the GitHub Actions API digest:

| Model | Artifact | ZIP SHA256 confirmed |
|---|---:|---|
| W8 | [12526515608](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731/artifacts/12526515608) | `7734eab2983e4abdb6b8b3e70c8b4dcc8098b46545b9e28ca9862872e3839f34` |
| V14 | [12524939485](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731/artifacts/12524939485) | `89830afbf8ffd5466c305365d8ec673b245725658a0bd9114fd0ae6bf70b958e` |
| R120 | [12525029273](https://github.com/anyangle1409-code/animation-software/actions/runs/40010003731/artifacts/12525029273) | `0cc37915ecb4fdb0b96e6d6fdcfc5920784d76bfa7c8fd1ee2b9e4575158a561` |

Each ZIP contains `inventory.json`, `rest_anatomy_inventory.json`, `integrity_checks.json`. All three `integrity_checks.json` files say PASS, `approval: NOT_GRANTED`, and `unweighted_vertices: 0`. Cloud input SHA256 was checked before and after opening the reconstruction. No source saved. These approvals do not apply to anatomy.

| Measure | W8 | V14 | R120 |
|---|---:|---:|---:|
| Vertices | 219974 | 238065 | 347840 |
| Bones in authoring rig | 77 | 77 | 77 |
| Named vertex groups | 77 | 77 | 77 |
| Shape keys | 79 | 79 | 79 |
| Unweighted vertices | 0 | 0 | 0 |

All 77 named bone records have identical parents, head and tail positions, and deformation flags **at the reports' six-decimal-metre precision** across W8, V14 and R120. This is not proof of binary-identical rest matrices or correct anatomical attachment. All 77 vertex-group names match bone names within each model (a naming property, not an anatomical validation).

## Weight-distribution changes

Distances below are **Euclidean separations of vertex-weighted body-local centroids** (millimetres). These are not direct geometric correspondences, not tissue translations and not evidence that bone positions changed.

| Pair | Groups with centroid shift >10 mm | Key regions |
|---|---:|---|
| W8 → V14 | 4 / 77 | shin_r 31.389; shin_l 31.066; toe_l 11.405; toe_r 11.404 mm |
| V14 → R120 | 24 / 77 | clavicle_l 15.446, clavicle_r 15.430; scapula_l 15.420, scapula_r 15.430; shoulder_cap_l 9.498, shoulder_cap_r 9.442 mm |
| W8 → R120 | 30 / 77 | includes changed upper-body and lower-body influence distributions |

**Additional key detail:** W8→V14 shoulder-cap centroid shifts are only ~0.35 mm while shin distributions shift ~31 mm, consistent with the leg-focused change *in this limited metric*. This does **not** mean the shoulders are anatomically correct; previous press movement tests still fail. V14→R120 shoulder/clavicle/scapula centroids shift more, and vertex counts in those influenced groups rise with changed topology. Counts should not be read as activation changes.

## Prior model failures still binding

- V14 reconstructed 238065 vs expected archived 238067 vertices (2 missing relative to archive).
- W8 archived offset-array maximum disagreement 3.59286 mm versus 0.01 mm guard.
- Prior native [read-only visual diagnosis](BODY_V2_READONLY_VISUAL_DIAGNOSIS_RESULTS_20261023.md): shoulder press, squat deformation/triangle gates FAIL in all three; grip solver FAIL. Numeric failures recorded, not repaired.
- 67-bone production bridge still unsuitable for these 77-bone authoring rigs without a separately tested adapter.
- Anatomical side mapping must be established using independent landmarks/camera/body-axis evidence before treating `_l`/`_r` as real anatomical left/right.
- R120 is EXPERIMENTAL. No muscle attachment, source promotion, merge or deployment authorized.

## New cloud analyzer

Added `scripts/cloud_body_analysis/compare_reports.py`, unit tests under `scripts/cloud_body_analysis/tests/`, and a new `compare-rest-audits` GitHub Actions job on the isolated phone workbench branch. Workflow commit: `3f25e5737c0668cfa005417a82f0d14e36ca83d1`, run [40015895314](https://github.com/anyangle1409-code/animation-software/actions/runs/40015895314). **Its outcome was not yet verified at the time this evidence page was authored.** The job is intended to upload `rest_comparison.json` and `rest_comparison.md` without touching model binaries.

## Safe next phase

1. Verify the new analyzer job and its ZIP artifact, fix any CI-only issues strictly in this cloud lane.
2. Use existing read-only visual and per-frame numerical evidence to localize shoulder-press/scapula/clavicle deformation and squat hip/shin defects.
3. Diagnose V14 two-vertex archive discrepancy from build scripts and the archived original evidence; do not invent vertices or modify the preserved reconstruction.
4. Keep all model-edit proposals as separate candidate-only plans pending explicit owner scope and anatomical landmark approval.

Source .blend hashes, production assets, validated skeletal data, PT_MODEL_VERSION 1.0, and Claude branches were not changed by this analysis.
