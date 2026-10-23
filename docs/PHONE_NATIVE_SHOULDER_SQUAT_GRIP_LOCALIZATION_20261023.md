# Home Gym PT — shoulder, squat and grip read-only localization (23 October 2026)

**Status:** independent analysis of stored native diagnostic artifacts; NOT anatomical or movement approval, NOT a model edit, NOT an accepted muscle attachment.

## Precise immutable source evidence

Blender 5.2 [read-only visual diagnosis run 39937882229](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229), branch `work/body-v2-readonly-visual-diagnosis-20261023`.

The following original diagnostic ZIP archives were downloaded and independently SHA256 checked against the existing published digests:

| Model | Artifact ID | ZIP digest (SHA256 verified) |
|---|---:|---|
| W8 | [12495910312](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495910312) | `3be4322ba67da8b3827c96c0afdb58ffa8adb998cf8d1814aab0978a9e68d63e` |
| V14 | [12494932817](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12494932817) | `5f11a9441cf5bb1d29ba3fae72c945f59c9109a26023cea15508d3310cb774e0` |
| R120 | [12495970648](https://github.com/anyangle1409-code/animation-software/actions/runs/39937882229/artifacts/12495970648) | `cf26902334a90cb3928821d797fcc88e27340a7837911a0e080b6973b5017a2f` |

All three retained `diagnosis.json` reports show their pinned `.blend` SHA256, `source_and_copy_unchanged: true`, and `anatomical_approval: NOT_GRANTED`. The exact source hashes remain documented in `PHONE_START_HERE.md`.

## New exact-frame geometric localization

The new independent Python analysis reads each saved `triangles.json` and corresponding `geometry.npz`. It cross-checks recorded flag arrays/counts and original diagnostics, then attributes each flagged triangle's **three corners** proportionally to the saved dominant vertex-group label. It also computes 5 cm evaluated-coordinate hotspots and the persistence of triangle flags **within the same model and path**, where rest topology fingerprints are unchanged.

**Vertex-weight labels identify which skin regions to inspect. These are not proof of anatomical causation, physical attachments, or validated left/right mappings.**

### Shoulder press at sample 6 (75% through the saved motion)

| Model | Stretched triangles | Newly flagged vs sample 0 | Selected leading saved dominant-group labels |
|---|---:|---:|---|
| W8 | 3,509 | 3,072 | spine_03, shoulder_cap_r, shoulder_cap_l, scapula_r/l |
| V14 | 4,261 | 3,550 | spine_03, shoulder_cap_r, shoulder_cap_l, scapula_r/l |
| R120 | 9,171 | 7,337 | spine_03, shoulder_cap_r/l, upperarm_l/r |

The model-specific within-path counts are meaningful, but absolute counts **across differently tessellated meshes** are not valid rankings of anatomical quality.

At W8 sample 6: among 110 collapsed triangles, the most represented saved dominant labels were neck (25.333 triangle-corner equivalents), clavicle_r (19.333), shoulder_cap_r (15.667), shoulder_cap_l (14.667), and clavicle_l (7.333).

At V14 sample 6: collapse-label leaders were clavicle_r and neck (23 each), clavicle_l (15.333), shoulder_cap_r (13.333), and shoulder_cap_l (11).

At R120 sample 6: major collapse-label proxies include shoulder_cap_l (48.667), clavicle_r (44.333), upperarm_l (43), shoulder_cap_r (41), and upperarm_r (36).

The archived back-view press overlays show pronounced posterior shoulder/upper-back stretching. This evidence makes the scapular/clavicular/shoulder deformation field a high-value next inspection target; it **does not** prove a particular weight is erroneous or authorize changing skeleton joint positions.

### Squat near deepest pose (sample 7)

| Model | Collapse flags | Stretch flags | Prominent saved stretch-group labels |
|---|---:|---:|---|
| W8 | 34 | 885 | hip_crease_r/l, spine_01, pelvis |
| V14 | 211 | 1,238 | thigh_r/l, hip_crease_r, spine_01 |
| R120 | 244 | 3,363 | hip_crease_l/r, pelvis, thigh_r/l |

At W8 sample 7, the 1,593 saved intersection **pairs** show shin/thigh and cross-shin weighted regions, including 509 shin_l–thigh_l, 509 shin_r–thigh_r, and 198 shin_l–shin_r in the native collision-class summary. Those are collision-pair class labels, not necessarily separate unique triangle locations.

### Grip

All three diagnosis reports executed **263 trial configurations for runtime suffix l**, with the other suffix untested because the first side did not meet combined grip criteria. W8 and V14 each reached the pair-count limit at one trial, with hand-collapse result 24; R120 reached the limit at three trials (collapse 23, 23, 24). No accepted grip was found within this sampled finite grid. The runtime suffix is **not** independent evidence for anatomical left/right.

## Cloud automation / verification

Implementation: `scripts/cloud_body_analysis/localize_failures.py` with isolated synthetic regression tests in `scripts/cloud_body_analysis/tests/test_localize_failures.py`.

A dedicated fifth job, `localize-native-movement-failures`, was added to `.github/workflows/phone-blender-workbench.yml` at commit `e50af1477bf7674a1ca7382944bfcef89405ff93`. It installs only NumPy, fetches pinned diagnostic artifacts from the older successful run, checks the source hashes and recorded values, and uploads JSON/Markdown reports. It never opens or saves any `.blend`.

[Run 40019611125](https://github.com/anyangle1409-code/animation-software/actions/runs/40019611125) was **in progress at the time this document was authored**. Its passing status and resulting artifact must be checked before claiming the new cloud job is verified. Earlier W8/V14/R120 rest-audit and cross-model cloud runs have already passed.

## Safe next technical work

1. Confirm the fifth job and artifact SHA256. If it fails, repair **only** the isolated scripts/workflow after reviewing logs.
2. Read exact five-centimetre hotspots and triangle sets for press samples 0, 6 and 8. Compare per-model newly flagged vs already flagged triangles, respecting stable within-model triangle correspondence.
3. Prepare a reproducible read-only shoulder/clavicle/scapula pose/weight sensitivity **test plan**, with independent shoulder landmarks and anatomical handedness checks. Do not infer bone-attachment locations from labels.
4. Keep squat and grip diagnostics as separate unresolved work streams; do not weaken geometry/collision thresholds to force a pass.
5. Claude may independently research V14 archive mismatch on its own isolated branch. Do not modify Claude's work or the immutable reconstructions.

No `ORIGINAL_v1`, body model, production bridge, validated skeleton, PR124 muscle source, `PT_MODEL_VERSION 1.0`, release, merge or deployment was modified.
