# Imported character repair validation

The production path preserves the imported source skeleton, bind data, mesh, weights and proportions, then transfers the canonical anatomical pose onto that source rig. The current proven character remains `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5. A separate review copy adds only metadata that opts into the new directional outer-elbow corrective; it does not replace the proven candidate.

Proven v5 SHA-256: `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`  
Directional-elbow review SHA-256: `8e8df9e8adcf43e0e6473bf98efadb05a31075031f9124787429ec2aedca99e4`

## Current production changes

- Imported characters keep their authored skeleton, inverse binds, vertices and skin weights; the canonical rig is a driver rather than a replacement skin skeleton.
- Character-aware contact correction and calibrated hand frames keep equipment and floor/bar contacts aligned to imported proportions.
- The proven v5 candidate contains the verified bilateral finger/hand repair, wrist cuff transition, local hip repair and widened elbow weight transition.
- The retained elbow corrective remains flexion-driven and candidate-specific: up to 18 mm on the inner fold and 9 mm over the elbow point, including the source rig's numbered split forearm helpers. It is zero when the elbow is extended.
- Imported corrective targets preserve the source geometry's existing morph convention. An absolute-morph character stays absolute; a relative-morph character stays relative, so adding the elbow corrective cannot reinterpret pre-existing facial or body morph targets.
- The curl bottom uses relaxed clavicles, 3° upper-arm clearance and no forward shoulder flexion. Peak elbow flexion remains 126°; the range was not shortened to hide deformation.
- Curl coordination is now phase-local: elbow flexion begins first, while the upper arms wait until 55% of the concentric before completing only the authored 4° forward drift. On the eccentric they wait until 20% before settling. That secondary movement uses a fifth-order minimum-jerk curve so it joins the held pose with zero velocity and zero acceleration.

## Directional outer-elbow review candidate

The importer now supports an additional optional `elbowCorrective.outerSmooth` value. It is not a generic smoothing pass and is inactive for every character unless its own metadata enables it.

When enabled, the corrective measures the imported mesh's bind-pose one-ring curvature around the posterior elbow and moves only the outer elbow along the source surface normal towards the local surface average. The added bind-space displacement is capped at 8 mm and shares the existing measured elbow-flexion drive, so it remains zero at extension. No topology, skin weights, rig, inverse bind matrices, exercise range or equipment attachment changes are made.

The separate review GLB sets `outerSmooth: 1.0`; its geometry, skeleton, weights and existing grip calibration are otherwise byte-for-byte the same as proven v5.

Local production-geometry measurements on the review trial were favourable rather than a trade-off:

| Pose | Baseline P95 | Review P95 | Baseline P99 | Review P99 | Severe compression change |
|---|---:|---:|---:|---:|---:|
| Curl peak, 126° | 1.515× | 1.496× | 1.633× | 1.620× | 14 → 14 |
| Shoulder press racked, 100° | 1.393× | 1.388× | 1.557× | 1.535× | 11 → 11 |
| Push-up bottom approximation, 90° | 1.348× | 1.338× | 1.501× | 1.473× | 7 → 7 |
| Pull-up top approximation, 144° | 1.558× | 1.552× | 1.795× | 1.776× | 23 → 23 |

These cross-pose figures are local deformation checks, not a substitute for tomorrow's visual Studio review. The largest additional posed displacement at curl peak was about 6.9 mm.

A local elbow-subdivision experiment was also tested and rejected. It roughly halved median local edge length (about 25.6 mm to 13.2 mm) but increased local compression and did not improve the silhouette enough to justify changing topology. Do not use subdivision merely to hide the remaining elbow faceting, and do not amplify the retained radial corrective: that earlier experiment added bulk without repairing the silhouette.

## Verification

Current branch validation on Node 22 after the directional importer and morph-preservation changes:

- `npm run typecheck` — **passed**.
- `npm test` — **198 passed, 1 optional real-character diagnostic skipped** (17 test files passed).
- `npm run build` — **passed**, with only the existing >500 kB chunk-size advisory.
- Regression coverage verifies that directional smoothing is explicitly opt-in, no added bind-space offset can exceed the 8 mm safety cap, and pre-existing absolute/relative morph targets remain in their original convention unchanged.
- The proven v5 candidate remains unchanged and available for A/B comparison.

The optional external-asset diagnostic is skipped in ordinary CI because the real GLB is not committed. Proven v5 passed the production real-character diagnostic in the preceding retained validation. The new review candidate should be visually inspected in the Studio tomorrow before its metadata is promoted to the shared candidate.

## Current visual priorities

| Area | Current status | Next review |
|---|---|---|
| Bicep curl motion | **Improved / review** | Judge the new elbow-before-shoulder sequencing through the moving rep, especially the late 4° shoulder drift and eccentric settling. |
| Elbow silhouette | **Review candidate ready** | Compare proven v5 against the `OUTER_ELBOW` review copy at mid and full curl. Retain `outerSmooth` only if the visual contour is clearly better. |
| Grip / fingers | **Needs minor visual polish** | Equipment is rigidly attached and fingers are isolated; inspect the remaining small handle/skin intersections and angular knuckle folds rather than redistributing broad forearm weights. |
| Shoulders / axilla | **Needs minor visual polish** | Curl bottom is relaxed. Raised-arm shoulder/axilla work should remain a separate low-amplitude directional corrective; a prior broad radial inflation trial was rejected. |
| Squat hip/groin | **Needs minor fix** | Keep separate from the curl template; prior broad weight and generic forward-push trials were rejected. |

All comparison renders produced during this repair work are offline renders of the actual production-posed triangles. They are evidence for deformation and silhouette review, not literal captures of the live Studio viewport.
