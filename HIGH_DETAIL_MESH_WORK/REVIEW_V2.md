# V2 — posterior shoulder balance and bare equivalence

Review candidate only. No production promotion. V1 preserved byte-for-byte.

## Findings
Claude's posterior-selection concern was tested using identical original vertices selected from the frozen baseline, holding ownership and region membership fixed. This establishes real sculpt displacement without any added-vertex sampling bias. It does not measure a physical volume centroid.

| Fixed original-vertex region | V1 mean sagittal displacement | V2 |
|---|---:|---:|
| Cap (25 vertices) | -32.315 mm | -10.727 mm |
| Upper shaft (105) | -8.458 mm | -2.574 mm |
| Lower shaft (105) | +0.067 mm | +0.067 mm |

The change was real localized cap reshaping, not a displaced skeleton or whole arm, and not solely a vertex-density artifact. V2 reduces the posterior sculpt coefficient from 0.040 m to 0.012 m. Vertical uplift, rig and original weights are unchanged.

## Measured targets
Deltoid height 31.9 mm (target 25–35). Apex sagittal z -47.8 mm, versus V1 -69.5 mm; still posterior to joint z -21.9 mm. Joint (214.9, 1412.1, -21.9) mm and humerus tilt 3.22 degrees unchanged. The supplied cap-band mean offset falls from 36.1 mm in our V1 run to 19.5 mm. Maxima also depend on sample selection and should not be described as sampling-independent; fixed correspondence complements the supplied measurement.

## Files
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v2.glb: dressed candidate.
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v2_BARE.glb: identical body and rig, garment mesh attachment removed. Orphan garment data remains in the binary intentionally; it is not rendered.
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v2.blend: editable dressed candidate.
- renders_v2/V1_V2_SHOULDER_COMPARISON.jpg and EXERCISE_REVIEW.jpg; individual full-size views in the same folder locally.

## Checks
Six focused tests passed cleanly in 33.27 seconds: supplied sagittal, bare/dressed equivalence, grip metrics, renderer/exporter agreement, dumbbell clearance and expanded five-exercise comparison. First run had a test-runner result-reporting timeout despite completed assertions; per-vertex finite checks were changed to direct throws preserving the same failure condition, and the complete focused run repeated successfully without concurrent rendering. Both logs retained.

Bare/dressed: identical solved grip, 0.0000 mm posed hand/body difference over 31,033 vertices at curl Bottom. Renderer/exporter: 0.0000 mm at t=0,2,4 both sides. Dumbbell Bottom clearance +1.99/+2.15 mm, no vertices inside. Grip-wrap metrics remain 343 degrees; see log.

Five exercises at 26 samples each: all 160 bone matrices, original hand vertices and equipment transforms exactly match frozen; all vertices finite and loops close. This is denser discrete sampling, not exhaustive continuous-motion or collision certification. Existing push-up reach/flare findings remain unchanged. Existing full source suite was not repeated because no application source changed.

400 reference files, copied production source and V1 binaries verified unchanged. Candidate rig/skin/animation metadata and original binary prefix match frozen. See reports/final_integrity_v2.json.

## Still open
New-vertex influence truncation (max 20.82%), detailed joint-loop refinement, hand/knee anatomy and skin textures remain from V1. Overhead armpits require closer deformation work; these still renders show no obvious new gross discontinuity but do not establish production quality. No new corrective drivers or production mechanics were added. Body remains 59,128 triangles.

## Claude review
Start with this document and compare the V1/V2 images. Reproduce sagittal and equivalence checks with GLB/ASSETS/DRESSED pointing to V2 and BARE to V2_BARE. Review posterior balance visually in-app under matched conditions. Do not merge, promote or modify frozen production assets or rig positions.
