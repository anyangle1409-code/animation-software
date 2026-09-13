# Candidate character: code repair and revalidation

**Partial repair completed. The candidate still fails visual acceptance in all five movements.**

Repository: `anyangle1409-code/animation-software`, branch `chatgpt/absolute-retarget-imports`.
Baseline: `641b43e9d6ceb642af241f99a6b40b729df05c35`. No merge performed.
Candidate: `HomeGymPT_Male_CC0_RUNTIME4_HIP_REFINED_CANDIDATE(1).glb`.
Original GLB SHA-256: `0eca49f54565c76e4262de389f7c9f57c42a8224d1576a868d0c7817ccd57585`.

## Implemented

- Preserve the source skeleton, hierarchy, inverse bind matrices, geometry and weights. No exercise definitions or candidate bytes changed; no destructive rebind.
- Reconnect six detached mapped branches through runtime attachment translations. Ninety-one detached Rigify face/chest/pelvis branches follow their anatomical parents.
- Respect the source's opposite left/right convention by reflecting rotations, without reflecting geometry.
- Use authored Rigify leaf-bone directions; exclude facial detail branches from parent shaft inference.
- Rotate pelvis placement with root rotation, apply scene transforms once, and restore source local positions on reset.
- Bake attachment translations and detail rotations into exported source animation tracks. Four new regression tests cover disconnected branches, root/display placement, opposite side conventions, reset, and exported playback.

## Verification

- Regular suite: **187 passed, 1 optional test skipped** (183 existing tests plus 4 new tests).
- Existing optional production diagnostic, explicitly enabled with this GLB: **1 passed**. Its original maximum-edge-strain threshold of 10 was unchanged.
- TypeScript checking and production build: **passed**. Vite retains its large-bundle warning.
- Fifteen diagnostic poses use the production preserved importer, `resolveFrame`, and `applyCharacterPose`. Sixty-one trajectory samples per movement check contact movement. These sample counts do not prove every frame free of self-intersection.
- Mapped anatomical frame error is below **0.030 degrees** across the fifteen posed captures, accounting for the source side convention. The skeleton follows the requested absolute pose instead of retaining its A-pose/open-hand rest. Correct skeleton orientation does **not** mean correct skin deformation or a closed mesh grip.
- Actual CPU-skinned triangles were rendered and visually inspected from two angles, including separate hand-region close-ups. **These are offline renders of production-posed geometry, not Animation Studio UI screenshots.** The available browser could not access the local Studio; live WebGL, lighting/material appearance and UI interaction remain unverified.

## Movement verdicts

| Movement | Verdict | Remaining defect |
|---|---|---|
| Dumbbell bicep curl | **FAIL** | Both wrists/palms split into stretched strips; all five digits on each hand fold or stretch across one another. Neither hand wraps the handle at bottom, mid-rep or top. Elbows pinch at contraction; shoulders remain bulky. |
| Bodyweight squat | **FAIL** | Both hands remain distorted. At the deepest pose, the upper/inner thighs and groin form a broad flattened wedge, and both knees pinch into angular folds. Feet drift during the repetition. |
| Dumbbell shoulder press | **FAIL** | Both wrists/palms and all fingers remain distorted throughout the press. At full overhead the handles are outside the fingers rather than enclosed by them. Armpits show sharp creases and uneven shoulder volume. |
| Push-up | **FAIL** | Both wrists/palms collapse and the fingers are not a coherent flat support surface at top or bottom. Hands do not hold their floor positions; the starting hand-bone target is about 63 mm off. Feet/toes are bent but floor contact is not certified. |
| Pull-up | **FAIL** | Both hands fail to wrap the bar at bottom and top; fingers and thumbs form stretched strips with wrist intersections. Hand-bone drift remains about 98 mm. Knees and ankle/foot transitions pinch in the tucked position. |

## Quantitative improvement

Maximum posed edge length / authored rest edge length across bottom/start, halfway and peak poses. Uniform display scale is removed. A ratio of 1 is unchanged length; these are mesh-edge strains, not joint-angle errors. A lower maximum does not certify acceptable shape.

| Movement | Before | After |
|---|---:|---:|
| Dumbbell bicep curl | 16.24× | 7.22× |
| Bodyweight squat | 19.91× | 8.01× |
| Dumbbell shoulder press | 16.24× | 7.22× |
| Push-up | 27.54× | 9.87× |
| Pull-up | 26.63× | 8.20× |

Source hand-carried dumbbells retain their hand-bone-relative attachment transform to numerical precision (maximum matrix-element drift < 5×10⁻¹⁶ in the three captured poses). They are locked to the **bones**, but the damaged hand mesh does **not** close around their handles.

Contact drift is the maximum distance from the imported effector's own starting location over 61 samples, not distance to a mesh contact patch:

| Contact | Before | After | After: initial distance to canonical target, side-adjusted |
|---|---:|---:|---:|
| air_squat: foot_l | 560.0 mm | 79.4 mm | 20.6 mm |
| push_up: hand_l | 194.9 mm | 35.7 mm | 63.2 mm |
| pull_up: hand_l | 452.1 mm | 98.4 mm | 98.0 mm |

This remaining drift requires source-proportion-aware contact solving. The current changes repair hierarchy and root transforms; they do not implement that solver.

## Hands, independently

Both wrists/palms have collapsed webbing and exposed-looking gaps. Thumb regions become broad loops; index and middle regions project as folded tabs rather than wrapping the handle; ring and pinky regions stretch across neighboring digits. No digit on either hand receives a visual PASS.

The following edge ranges include edges with either endpoint dominated by that digit's source weights, across all fifteen captured poses. Regions overlap at boundaries; they are diagnostic associations, not exact anatomical segmentation.

| Digit | Left min–max | Right min–max | Verdict |
|---|---:|---:|---|
| Thumb | 0.25–9.87× | 0.25–9.87× | FAIL |
| Index | 0.10–7.78× | 0.10–7.78× | FAIL |
| Middle | 0.14–5.16× | 0.14–5.17× | FAIL |
| Ring | 0.08–9.87× | 0.08–9.87× | FAIL |
| Pinky | 0.18–8.20× | 0.18–8.19× | FAIL |

## Body-region inspection

The large detached face/chest/pelvis sheets have been removed. Shoulders and armpits remain bulky or sharply creased under elevation. Elbows show compressed folds at flexion; forearms retain a continuous main shaft but break down at the wrist connection. Palms, all fingers and both thumbs fail the grip inspection. The deep squat shows flattened inner/upper-thigh and groin surfaces plus angular knee collapse. Ankles/feet remain connected in standing and squat captures, but foot drift and tucked-leg pinching prevent contact/shape certification. The inspection did not include an exhaustive triangle-intersection proof.

## Residual asset evidence and next work

At the authored GLB scale, both wrist pivots are approximately **117 mm** from their nearest influenced vertex (weight > 0.05); both first index-finger pivots are approximately **175 mm** away. Wrist pivots are about **193 mm** from their weighted surface centroids. These measurements use the asset's rest-pose skinned vertices, before exercising it. They strongly indicate a rig-to-surface alignment problem, not just an open-hand rest-pose offset.

A reliable hand repair needs a separate corrected asset: align the wrist and each finger/thumb joint to the actual surface, regenerate consistent bind matrices, inspect and correct cross-digit weights, and verify each digit independently under flexion. Original candidate bytes must remain preserved. Deep hip/knee deformation also needs isolated rig/weight inspection. After the asset is sound, add source-proportion-aware floor/bar constraints and calibrate grip sockets against the actual closed palm. Automatically guessing pivots from mixed weight centroids is not a reliable substitute.

This code change is a tested foundation, **not a finished character repair**. Do not promote this candidate based on the automated pass alone.
