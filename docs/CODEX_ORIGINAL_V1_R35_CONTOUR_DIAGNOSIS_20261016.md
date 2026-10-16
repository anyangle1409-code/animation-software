# R35 arm-to-side contour diagnosis (16 October 2026)

**Status: diagnosis complete; no R35 model created. Owner approval requested before a broader S7 target rebuild.**

The owner's four locations are recorded in `CODEX_ORIGINAL_V1_R35_ARM_TO_SIDE_BRIEF_20261016.md`. The reference image stays outside the repository.

## What the saved model shows

The marked R34 press frame is at 135.625 degrees. A read-only Blender 5.2.1 probe evaluates the same file with S5 and S7 individually disabled. The S7 layer contributes the shelf/lobe at the junction. Disabling S7 also restores folds and upper-arm defects, so removing that family is not an acceptable correction.

The original R34 front-armpit regression checks do not cover this larger arm-to-side contour. R34 remains visually unaccepted.

## Bounded alternatives investigated and rejected

The posed surfaces were exported for numerical diagnosis. Local fairing, local attenuation of the S7 contribution, and attenuation followed by fairing were tried as scratch evaluated-surface probes. No blend or existing candidate was overwritten.

The rear silhouette becomes smoother in several trials, but the three-quarter junction does not improve enough. Stronger changes reintroduce folds. In combined trials the three-quarter profile-turn diagnostic became worse:

| Probe | Rear profile turn | Three-quarter profile turn | Maximum surface move |
|---|---:|---:|---:|
| R34 | 16.987 degrees | 53.426 degrees | 0 mm |
| 50% local attenuation | 13.891 | 52.505 | 12.399 mm |
| 60% attenuation + fairing | 11.447 | 56.172 | 16.692 mm |
| 80% attenuation + fairing | 9.243 | 58.692 | 21.554 mm |

The profile measure is a diagnostic of the projected curve over the local junction. It is not a substitute for owner visual review. These probe trials are **rejected**, not new review versions or clinically validated results.

## Proposed next scope

Replace the current local S7 target shape across the complete arm/axilla/side junction with a continuous transition. Preserve frozen bones, the basis mesh, weights, all non-S7 shape-key families, R34's front-armpit improvements and the approved press path. Test the contour from both rear and three-quarter at the marked frame and neighboring angles; rerun collision/collapse/stretch/volume and movement checks. Save any result as a separately named R35 candidate with its own doc, native Blender comparisons and press video.

This is a larger target-shape change than a small smoothing adjustment. The owner explicitly asked to be consulted before large changes, so no such rebuild has started.

Probe run: https://github.com/anyangle1409-code/animation-software/actions/runs/38946251822

Machine-readable findings: `docs/CODEX_ORIGINAL_V1_R35_CONTOUR_DIAGNOSIS_20261016.json`.

No test was weakened or deleted. No reference photo, secret, third-party asset, canonical skeleton change, merge or force-push was introduced.
