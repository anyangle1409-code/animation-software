# AI Change Log

This file records changes made by Codex and Claude. Each assistant must add an
entry whenever it changes code, tests, documentation, assets, exercise
definitions, or repository configuration.

## Unreleased


### ChatGPT — 2026-09-14 — joint timing, loop-range authoring, and completed shoulder biomechanics

Retained animation-workspace commit `d4340d2` adds a real review/authoring layer rather than another exercise-specific workaround. The timeline now supports custom **Set In / Set Out / Clear range** playback ranges with a visible overlay. Custom ranges are editor playback state only and never alter the exported clip; they normalise to the clip, preserve at least one frame, rescale with duration changes, reset on exercise changes, and are ignored when Loop is disabled. Playback math is isolated in `src/editor/playback.ts` and covered by dedicated tests. The Joint panel now exposes the existing phase-local bone timing system for the selected bone in the segment under the playhead: custom start delay, finish point, and optional easing override. These edits write to `Keyframe.jointTiming`, use normal undo/redo history, and preserve the existing deterministic animation pipeline. The implementation roadmap was updated to mark this animation-authoring foundation as present.

Validation for `d4340d2`: `npm run typecheck` passed; **225 tests passed / 1 optional real-character diagnostic skipped (226 total) across 23 files**; `npm run build` passed. The only build advisory remains the pre-existing Vite >500 kB chunk warning. No character asset, retarget algorithm, canonical rig, grip mapping, exercise goal or exported data format was replaced by this work.

Retained biomechanics commit `22cc1ee` resolves the isolated-action shoulder audit without weakening skin-containment rules. The medial deltoid now follows a lateral acromion-to-humerus route and uses a measured `taper: 0.84`, the largest tested visible-belly taper that stayed inside the existing containment allowance. Pectoralis keeps its previously proven visible chest-to-humerus line and gains a hidden proximal-humerus functional via point near `(0.02, 0.02, -0.02)`, making the trainer-level path shorten in both shoulder flexion (~6.6%) and adduction (~5.2%) without dragging the visible belly through the pull-up armpit. Latissimus likewise keeps its proven visible endpoints and gains a hidden proximal-humerus via point near `(0.04, 0.04, 0.04)`, producing shortening in isolated extension (~4.1%) and adduction (~4.9%). `src/muscles/functions.test.ts` now permanently checks all declared joint crossings plus elbow, wrist, knee, shoulder, scapular/trunk, hip and ankle functional actions.

Validation for `22cc1ee`: `npm run typecheck` passed; **218 tests passed / 1 optional diagnostic skipped (219 total) across 22 files**; production build passed. Rejected during that work: a high/anterior visible pectoral candidate that was mechanically correct but protruded roughly 35 mm during pull-up, and a changed visible lat insertion that missed the existing pull-up containment allowance by ~0.147 mm. The retained pattern is therefore deliberate: keep containment-safe rendered geometry and use hidden functional via points where joint-spanning length needs a more anatomical route. Functional path length remains a geometric motion diagnostic, not a force or EMG estimate.


### ChatGPT — 2026-09-14 — functional muscle paths and whole-body biomechanics gate

Audited the entire current muscle subsystem instead of limiting validation to the bicep curl. The audit confirmed **22 trainer-level muscle groups** and found a real engine defect: `forearm_flexors` and `forearm_extensors` declared that they act on the hands/wrists, but both endpoints were attached to the forearm bone. Their measured length change across every current exercise was effectively zero (floating-point noise around `2e-15`), so the overlay could highlight them but wrist motion could not make them contract or lengthen. The same audit exposed two straight-chord limitations worth fixing before scaling the library: the triceps path could shorten during elbow flexion instead of lengthening, and the quadriceps chord could cut across a deeply flexed knee instead of following the anterior/patellar route.

Validated feature commit `bbb6600a0e30b062925e763e592e192b70a8e0fc` adds optional anatomical `via` / wrap points to `MuscleDefinition`, constructs a full functional origin -> via point(s) -> insertion path, and drives `restLength`, stretch and bulge from that path while retaining the inexpensive fitted ellipsoid as the visible belly. Mirroring now includes via points and the containment fit includes every bone used by the path. This is intentionally an incremental biomechanics upgrade: curved functional paths are now correct enough to drive contraction, while the rendered overlay remains the existing inexpensive fitted form rather than becoming a general muscle-mesh simulator.

The forearm flexors/extensors now cross onto `hand_l`/`hand_r`, with a 0.72 belly taper so the visible mass remains primarily in the forearm while the functional tendon crosses the wrist. Triceps now has a posterior elbow via point (`upperarm_l`, approximately `[0.002, 0.292, -0.035]` before mirroring), and quadriceps has an anterior-knee via point (`thigh_l`, approximately `[0, 0.415, 0.05]`). A first 0.68 forearm taper trial was **rejected by the existing geometry invariant** because the visible belly ended about 2.4 mm too far from its functional insertion tolerance; no engine change was committed from that failed run. The 0.72 calibration was rerun through the complete gate rather than weakening the invariant.

Added permanent `src/muscles/functions.test.ts` coverage that requires every muscle group to physically span every joint listed in its `actsOn` metadata; verifies isolated elbow flexion shortens biceps while lengthening triceps; verifies wrist flexion/extension makes forearm flexors and extensors oppose one another; and verifies deep knee flexion lengthens quadriceps while shortening hamstrings. Existing all-exercise skin-containment, belly attachment, mirroring, biceps contraction, rig, retarget, equipment, export and movement-certification tests remain intact. Final Node 22 validation: `npm run typecheck` passed; `npm test` passed **211 tests with 1 optional real-character diagnostic skipped (212 total) across 21 files**; `npm run build` passed with only the pre-existing >500 kB Vite chunk advisory.

Added `docs/STUDIO_CAPABILITY_ROADMAP.md` to define the end target as a specialist **exercise-animation authoring studio with Blender-like control**, not a general Blender clone. Priorities are: biomechanical core, rig/pose controls, exercise timeline, hand/grip workspace, equipment/contact authoring, bounded corrective deformation, live diagnostics/approval, and template-driven scale. Sculpting, UV editing, texture painting, particles, compositing and arbitrary scene modelling remain deliberately out of scope. No exercise definition, retained bicep-curl motion, grip default, imported character asset, skin weights, retargeting algorithm, equipment attachment or candidate GLB was changed by this muscle-engine pass.

### ChatGPT — 2026-09-14 — selected-joint focus camera and curl realism guardrails

Added a diagnostic **Focus selected** camera mode for imported-character review. It follows the currently selected resolved joint during playback with a close 32° view and side-aware three-quarter offset, while reusing scratch vectors to avoid per-frame allocation. App-facing Recommended/full-body framing is unchanged. Validated feature commit `9126b7b`: TypeScript passed, **203 tests passed / 1 optional real-character diagnostic skipped** across 19 files, and the production build passed with only the existing Vite chunk-size advisory.

Hardened the bicep-curl validator without changing the accepted motion, model, rig, grip closure or equipment attachment. Added explicit anti-shrug clavicle limits, tightened upper-arm takeover to a 10° ceiling, required the dumbbell grip to remain supinated, constrained sideways wrist deviation to ±10°, and added the user-facing common error **Shrugging the shoulders**. New negative tests deliberately inject a shrug, 18° upper-arm takeover, lost supination and 20° wrist deviation and confirm each rule fires. Validated commit `d2b3a24`: TypeScript passed, **207 tests passed / 1 optional skipped** across 20 files, and the production build passed with only the existing chunk-size advisory.

Tomorrow review is now documented in `docs/BICEP_CURL_REVIEW_HANDOFF.md`. Use the proven v5 candidate first, then A/B the review-only `OUTER_ELBOW` candidate at curl mid/top with **Focus selected**. For grip, keep 85% as the baseline and compare 80/75/70/65% through the live production generator. Do not promote `outerSmooth` or a lower permanent grip closure from offline numbers alone; visual elbow silhouette, secure finger enclosure, thumb placement, palm loading, rigid dumbbell centring and bilateral symmetry are the acceptance gates. Temporary validation workflows/helpers were removed after the validated commits landed.

### ChatGPT — 2026-09-14 — live grip-closure tuning and collision baseline

Added a live **Grip closure** control to the Exercise panel so the repaired imported character can be tuned through the exact deterministic production generator instead of recompiling guessed closure values. `StudioState.setGripClosure` clamps to 0..1, copies the exercise hand spec, regenerates the clip through `generateClip`, participates in normal undo/redo history, and leaves the authored dumbbell-curl default at **0.85**. The panel exposes a 0–100% range in 5% steps with an exact percentage readout. No exercise default, rig, imported-character mapping, equipment socket, candidate GLB, skin weights or retargeting rule was changed by this tooling pass.

Added `src/editor/store.test.ts` regression coverage for deterministic bilateral finger regeneration, clamping and undo back to the authored 85% value. Full validation before the feature commit was pushed: `npm run typecheck` passed; `npm test` passed **200 tests with 1 optional real-character diagnostic skipped** across 18 test files; `npm run build` passed with only the existing >500 kB Vite chunk advisory. The validated feature commit is `e2ebca5` (`feat: add live grip closure tuning`).

Also quantified the remaining small dumbbell/skin intersections using the saved production-posed repaired-hand evidence and the Studio's 15 mm-radius / 120 mm handle. The later v5 elbow and shoulder passes did not change hand geometry, grip calibration, closure or equipment attachment, so this is a useful baseline but **not a substitute for a fresh live v5 render**. At the authored 85% closure the strict cylinder test finds 103 hand/finger surface vertices per hand inside the handle, bilaterally symmetric and repeated in shoulder press: thumb 28 (max 13.18 mm), index 8 (6.91 mm), middle 3 (3.62 mm), ring 9 (8.90 mm), pinky 25 (12.53 mm), hand/palm 30 (14.57 mm). The concentration in palm/thumb/pinky means a whole-dumbbell translation is a poor first fix; it can help one side while worsening the other. A separate attempt to approximate lower closure by directly rotating source Rigify fingers was rejected because absolute anatomical retargeting made that approximation miss production digit positions by roughly 15–29 mm depending on reconstruction. Do not use that approximation to choose a permanent value.

Tomorrow review: load the proven v5 candidate and the separate `OUTER_ELBOW` review candidate, keep the curl at 85% first, then use the new live control to compare 80/75/70/65% at curl bottom/mid/top and shoulder-press start. Judge handle penetration, full finger enclosure, thumb placement, palm loading, equipment centring/rigidity and left/right symmetry. Only change the authored 85% value if the live imported-character A/B clearly improves the grip without making it look loose. The Library folder `/HomeGymPT Animation Review 2026-09-14` now also contains `Grip-Intersection-Diagnostic.md/.csv` plus the elbow candidate/evidence and curl motion profile.


### ChatGPT — 2026-09-14 — preserve imported morph conventions

Hardened the candidate-specific imported deformation path for future characters that already carry expressions or body-shape morphs. `importedElbowDeformation` previously set `geometry.morphTargetsRelative = true` whenever it appended the elbow corrective. Three.js uses one morph convention for the entire geometry, so that could reinterpret a source character's pre-existing absolute morph targets. The importer now leaves the source convention untouched: on relative geometries the elbow target remains a delta; on absolute geometries it writes base position plus the same corrective delta. The current male candidate's rendered result is unchanged; this is an importer-safety correction, not another elbow-shape change.

Added two regression cases alongside the directional elbow tests. They seed a character with a pre-existing absolute morph and with a pre-existing relative morph, append the corrective, and verify both the convention flag and the original morph data remain unchanged. The existing opt-in and 8 mm directional safety-cap tests remain. Final Node 22 validation: `npm run typecheck` passed; `npm test` passed **198 tests with 1 optional real-character diagnostic skipped** across 17 files; `npm run build` passed with only the existing >500 kB Vite chunk advisory. `docs/CHARACTER_CANDIDATE_REPAIR.md` now records this guardrail and the 198/1 result.


### ChatGPT — 2026-09-14 — directional outer-elbow review candidate

Continued the bicep-curl realism pass against the proven Library character `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5 (SHA-256 `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`). The proven v5 asset remains unchanged. Added an explicitly opt-in `elbowCorrective.outerSmooth` capability to `src/character/importedDeformation.ts`, plus focused regression coverage in `src/character/importedDeformation.test.ts`. The new path does not amplify the retained 18 mm / 9 mm radial elbow morph. Instead it measures the imported mesh's bind-pose one-ring curvature and settles only the posterior elbow along the source surface normal towards the local surface average. Added displacement is capped at 8 mm and shares the measured elbow-flexion drive, so it is zero at extension. The code supports both ordinary and interleaved Three.js geometry attributes. No topology, weights, inverse binds, canonical rig, retargeting algorithm, exercise range, grip or equipment attachment was changed.

Created a separate review GLB by adding only `outerSmooth: 1.0` to the existing candidate metadata: `HomeGymPT_Male_HAND_REPAIR_OUTER_ELBOW_CANDIDATE.glb`, SHA-256 `8e8df9e8adcf43e0e6473bf98efadb05a31075031f9124787429ec2aedca99e4`. It is review-only and must not replace v5 until visual approval. Local production-geometry checks moved in the correct direction across different arm poses: curl peak P95/P99 1.515x/1.633x -> 1.496x/1.620x; racked shoulder press 1.393x/1.557x -> 1.388x/1.535x; push-up-bottom approximation 1.348x/1.501x -> 1.338x/1.473x; pull-up-top approximation 1.558x/1.795x -> 1.552x/1.776x. Severe-compression counts did not increase in any of those checks. Maximum additional posed displacement at curl peak was about 6.9 mm. These are deformation measurements, not visual certification.

Also tested and rejected local elbow subdivision. It roughly halved median local edge length (~25.6 mm to ~13.2 mm) but increased local compression and did not improve the silhouette enough to justify changing topology. Do not pursue subdivision just to hide the remaining faceting. The earlier amplified radial shape remains rejected for the same reason: it added bulk without repairing the outer silhouette.

Full clean-state branch validation after the retained importer change: `npm run typecheck` passed; `npm test` passed **196 tests with 1 optional real-character diagnostic skipped** across 17 test files; `npm run build` passed with only the existing >500 kB Vite chunk advisory. Two new tests verify that outer smoothing is explicitly opt-in and that its additional bind-space offset cannot exceed 8 mm. `docs/CHARACTER_CANDIDATE_REPAIR.md` has been refreshed with the current v5/review hashes, measurements and tomorrow-review steps. Next: visually A/B the proven v5 and OUTER_ELBOW review candidate at curl mid/top in the live Studio. Keep the new metadata only if the silhouette improvement is clearly visible; otherwise leave v5 as the shared asset.


### ChatGPT — 2026-09-14 — minimum-jerk secondary motion for curl

Continued the software-level bicep-curl refinement without changing the character asset. Added a reusable `minimumJerk` easing kind using the fifth-order trajectory `10t^3 - 15t^4 + 6t^5`. Unlike the existing cosine `lift` curve, this reaches both zero velocity and zero acceleration at each endpoint, which is useful for secondary joints that begin moving part-way through a phase. The ordinary resistance-training `lift` curve remains the default for prime movement.

The dumbbell curl now uses `minimumJerk` only on the already-delayed upper-arm motion: the upper arms still wait until 55% of the concentric and 20% of the eccentric, but their small authored 4-degree shoulder drift now leaves and returns to the held pose without the acceleration step of the cosine curve. Elbow flexion/supination, start and peak poses, 126-degree peak flexion, 5.5-second repetition, grip, fingers, equipment attachment, clavicle depression, contact locks, canonical rig, retargeting, skin weights and the candidate GLB are unchanged. The retained Library candidate reviewed for this pass is `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5, SHA-256 `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`.

Added regression coverage for the minimum-jerk curve itself, including near-zero endpoint velocity and acceleration. Full branch validation on Node 22 passed: `npm run typecheck`; `npm test` with **194 passed and 1 optional real-character diagnostic skipped**; and `npm run build`, with only the existing >500 kB chunk warning. No asset was modified. The next elbow work should remain topology-aware; do not amplify the retained radial elbow corrective, because that experiment was already rejected for adding bulk without fixing the angular silhouette.


### ChatGPT — 2026-09-14 — phase-local joint timing; natural curl shoulder sequencing

Reviewed the animation generator itself rather than changing the character asset. The generator previously exposed only phase-level easing, so every joint moved on the same normalized clock between the authored start and peak poses. Added optional `MovementPhase.jointTiming` with per-bone `delay`, `finish`, and easing. `generateClip` carries that timing onto the outgoing phase keyframe and `sampleClip` remaps only explicitly timed bones; all other joints keep the existing resistance-training easing. No intermediate stop-start keyframes are inserted.

The dumbbell curl is the first validation use. Both upper arms now remain at the relaxed bottom position until 55% of the concentric while elbow flexion begins immediately, then complete only the already-authored 4° forward drift near the top. On the eccentric, the elbows begin opening first and the upper arms wait until 20% of the phase before settling back. Start and peak poses, the 5.5 s repetition tempo, 126° peak elbow flexion, clavicle depression, supinated grip, finger closure, equipment attachment, contact locks, canonical rig, imported-character retargeting, skin weights and candidate GLB are unchanged.

Regression coverage now explicitly checks elbow-before-shoulder sequencing in addition to the existing loop, grip, equipment rigidity, contact, symmetry and technique validation. Branch validation on Node 22: `npm run typecheck` passed; `npm test` passed **193 tests with 1 optional real-character diagnostic skipped**; `npm run build` passed with only the pre-existing >500 kB chunk warning. No character asset was changed by this software pass.


### Codex — 2026-09-14 — correction to wrist diagnosis; morph-aware strain test

**This supersedes the earlier claim that the candidate has no mixed wrist weights.** The imported source names are `DEF-forearmL`, `DEF-forearmL001`, and `DEF-handL` (mirrored on the right). The trial's `matchingBones` recognized the base name and dotted suffixes only, so it silently omitted the split forearm helper. Counting that exact helper reveals 313 vertices per side with both hand and forearm weights; 167 per side satisfy the trial's radius, pair-weight and blend gates. The zero-displacement experiment therefore did not establish a topology limitation.

The real-character test also measured only `applyBoneTransform`, omitting all pose morphs. It now uses `SkinnedMesh.getVertexPosition`, which includes morphing before skinning. Two always-on regression tests verify relative and absolute morph targets, including returning to zero influence. Full suite: **192 passed, 1 optional skipped**. With the real candidate supplied, the diagnostic's three tests pass. Build/typecheck passes; existing bundle-size warning remains. Passing the catastrophic strain ceiling is not visual certification.

Removed the uncommitted rejected shoulder/wrist prototypes from the local production modules, returning those two modules to their current remote contents. No model, weights, exercise, retargeting or active corrective changes are included in this checkpoint. Candidate SHA remains `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`.

Next: account explicitly for sanitized split-helper names when constructing a new isolated wrist trial. Do not silently change the shared elbow matcher without a separate comparison, because that would expand the existing elbow correction's affected region. Drive wrist bend relative to its forearm, not from the hand's world orientation (which also changes when the torso/shoulder moves). Validate activation, affected vertices, morph-aware strain, floor contacts and close-up rendered grip before retaining a shape. The prior images were offline renders of production-posed triangles, not live Studio screenshots; that visual acceptance step is still outstanding.

**Corrected wrist trial — 2026-09-14 (rejected).** A local wrist-relative morph was then run with the split helper included: it selected 167 blended vertices per side, stayed exactly zero in curl and shoulder press, moved 334 vertices at push-up peak (maximum 2.75 mm) and 334 at pull-up peak (maximum 0.92 mm). It did not reduce any global strain count and the close-up read as a small outward puff rather than a lifelike wrist transition. It is not in the candidate; the candidate has again been restored to SHA-256 `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`. Do not retain or re-enable the local prototype. A successful wrist shape needs a directional flexion/extension profile built from the actual palm/forearm surface directions.

**Verification note — 2026-09-14.** After cleanup, the ordinary suite produced 191 passing tests plus one timeout in the pre-existing heavy neck weight-normalization test at Vitest's default 5 s budget. Running that test alone with the repository's established 30 s allowance passes all 12 neck tests (the slow assertion completed in 2.776 s); build/typecheck passes. Treat this as timing contention in the full parallel run, not a regression from an active character change. No candidate or production-code prototype was retained after this note.

**Rejected deep-squat hip-weight trial — 2026-09-14.** The squat reaches 101.27° hip flexion and has 85 mixed vertices per hip inside 150 mm of the joint. A stronger local same-side hip blend (8 iterations at 0.80, versus the retained 4 at 0.55) softened parts of the seam but did not repair the deep groin collapse. It raised the deepest-squat maximum edge ratio from 3.68× to 4.04×; P99 improved only 1.647 to 1.643 and compressed-edge count fell 141 to 136. This is not a usable trade. The candidate was restored to SHA-256 `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`. The next hip attempt must be a deep-flexion directional pose shape, not heavier weight averaging.

**Rejected deep-flexion directional hip trial — 2026-09-14.** Implemented a local, deep-squat-only anterior hip morph gated from 1.10 to 1.70 radians of relative hip flexion (maximum 8 mm, 150 mm radius), then posed and rendered the actual candidate. The deep-squat front and side renders were pixel-identical to the active baseline and all reported strain metrics were unchanged (maximum 3.68×, P99 1.647, 106 edges above 2×). It therefore either did not select a meaningful surface region in the imported topology or was too small to affect it; in either case it is not an improvement. The trial code and metadata were removed and the candidate was restored to SHA-256 `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`. Typecheck passes. Do not revive this exact forward-push target; the next attempt needs to identify visible groin seam vertices from the posed mesh before sculpting a shape.

**Rejected athletic-stance squat motion trial — 2026-09-14.** Compared a temporary wider, more toe-out stance (0.48 m / 16°) with 94° hip flexion, 106° knee flexion and 22° ankle motion against the retained 0.42 m / 12° deep squat. The alternate render looked marginally less forced but did not resolve the groin fold, while peak compression worsened slightly (144 edges below half rest length, vs. 141). Stretch metrics improved only trivially (P99 1.643 vs. 1.647; 103 vs. 106 edges above 2×). It would also make the requested deepest squat shallower. The exercise definition was restored exactly; no motion change is retained. Typecheck passes.

**Rejected amplified elbow-shape trial — 2026-09-14.** Compared a larger version of the retained elbow morph (24 mm inner / 12 mm outer, versus 18 mm / 9 mm) at the actual curl peak. Curl bottom remained unchanged, as intended, but the close render added bulk without removing the angular elbow silhouette. The curl peak strain metrics also did not improve (maximum 3.75×, P99 1.498, 30 edges above 2×). The asset has been restored to its proven SHA-256 `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`; do not simply scale the existing radial elbow shape further. A future improvement must be a topology-aware directional shape or a denser candidate elbow mesh.

**Retained split-helper elbow corrective — 2026-09-14.** The imported Rigify arm has numbered split helpers (for example `DEF-forearmL001`) that form the visible flexed-elbow surface. The existing optional elbow morph had intentionally omitted these helpers, so its radial correction could not fully reach the sharp hinge. `importedElbowDeformation` now has an opt-in `includeSplitHelpers` matcher; only this candidate enables it. The candidate’s same conservative 18 mm inner / 9 mm outer shape now includes the split upper-arm/forearm surface at flexion. Curl bottom remains exactly unchanged, curl peak renders with a visibly softer elbow transition, and pull-up top remains stable. Full suite: **192 passed, 1 optional skipped**; production build passes with the existing chunk-size warning; the real-character diagnostic passes. The retained candidate is SHA-256 `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f` and its shared asset was advanced to version 5. The morph is still source-skeleton/absolute-retarget safe and exports through the standard deformation sampler.

**Retained relaxed curl-bottom shoulders — 2026-09-14.** The high-looking curl-bottom shoulders were primarily a clavicle presentation issue, not a reason to push the upper arms outward or alter the character mesh. The curl now applies a symmetric 5° clavicle depression (left +Z / right −Z) at both start and peak. The actual render shows a more relaxed shoulder line with the arms beside the torso; dumbbell attachment remains numerically rigid (4.44e−16 matrix drift). Curl peak P99 edge strain improves from 1.502 to 1.490 and compression reduces from 143 to 141 edges below half rest length. Full suite: **192 passed, 1 optional skipped**; production build and real-character diagnostic pass. No asset, weights, importer or retargeting algorithm change was needed.

### Codex — 2026-09-13 — imported character: elbow corrective and handover

This entry is the current cross-assistant handover for the candidate male character. Continue from branch `chatgpt/absolute-retarget-imports`; do not merge it. The active candidate remains external to the repository: `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` (SHA-256 `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`). Its supplied source file remains untouched.

**What is now in the production path.** The preserved-source-skeleton absolute-retarget path remains mandatory. The import still keeps the character's vertices, source hierarchy, inverse binds and skin weights; no destructive canonical rebind is used. Curl rest and peak upper-arm rotations were reduced so the shoulders sit naturally at the bottom of the curl. The candidate received symmetric forearm/elbow blend-weight repair, wrist-cuff settling and localized hip smoothing. It also contains opt-in `homeGymPT.elbowCorrective` metadata, interpreted by `src/character/importedDeformation.ts`: a conservative, symmetric pose-driven morph activates only with elbow flexion (maximum 18 mm inside and 9 mm outside), and is baked into exported GLBs through the same sampler as the viewport.

**Validated current state.** `npm test`: 190 passed, 1 optional skipped. `npm run build`: passed (only the pre-existing bundle-size warning). The real-character optional diagnostic passes. An exported curl GLB has the source mesh's `morphTargetInfluences` track with a peak influence of 0.99999946. Prior contact measurements remain within millimetres: pull-up hand grip maximum 1.036 mm; push-up hand surface approximately -0.05 to +6.01 mm from the floor; squat foot approximately -2.30 to +0.001 mm. All ten fingers remain isolated from the opposite hand and forearm.

**Visual work still needed — do these as targeted pose correctives, not broad smoothing or rebinding.**

1. **Shoulder/armpit:** the curl bottom is improved, but overhead press/pull-up still need a low-amplitude, candidate-specific shoulder-cap/axilla corrective. A prior broad shoulder-weight pass increased local strain; do not repeat it. Keep the corrective zero around rest and curl-bottom.
2. **Elbow:** the new correction removes the worst hinge-like collapse but cannot fully change the low-density elbow silhouette. Visually inspect curl mid/top and pull-up top before adjusting its deliberately small limits.
3. **Wrist, palm and grip:** hand placement and equipment attachment are stable, but the wrist-to-palm transition and knuckle contour need a local pose shape. Do not redistribute broad forearm weights. Confirm each finger and thumb still wraps the handle after any change.
4. **Hips/groin, knees and feet:** deep squat still needs a candidate-specific groin/hip shape and restrained knee treatment; localized hip smoothing alone is not enough. Preserve floor contacts and never introduce general knee smoothing.

**Guardrails.** Do not change the model, exercise definitions, canonical rig, weights, or retargeting algorithm unless a new measured defect requires it. Preserve the absolute anatomical pose, source skeleton, hand sockets and equipment lock. Run a focused rendered inspection after each corrective and run the full automated suite only for a retained change. Update this file with measurements and exact asset hash whenever a new candidate is produced.

**Continuation review — 2026-09-13.** Re-inspected the latest elbow-corrective render. It improves bend volume without altering curl-bottom shoulders. The residual angular elbow contour is topology-limited; do not amplify this corrective blindly. The next retained visual change should be a measured, raised-arm-only shoulder/axilla shape or a wrist/palm shape, with before/after renders and contact checks.

**Fresh production evidence — 2026-09-14.** Regenerated all six requested key poses from the current candidate with the corrective applied before skinning: curl bottom/top, deepest squat, press overhead, push-up bottom and pull-up top. The focused real-GLB production diagnostic passes; the full suite remains 190 passed / 1 optional skipped and the production build succeeds. This confirms the current import has 52 required mapped bones, 160 source bones and 10,839 vertices. Keep the correction as-is: full-mesh maximum edge ratios are still dominated by original hand/wrist and pull-up topology (pull-up reaches 8.47× during the cycle), not a reason to increase the elbow morph.

**Rejected experiment — 2026-09-14.** Tested a raised-arm-only shoulder-cap/axilla morph (zero at curl bottom; 566 local vertices; maximum press displacement 3.31 mm). It produced too little visible improvement and increased press compression slightly (105 to 111 edges below half rest length). It is not in the candidate: the active asset has been restored to SHA-256 `706c4aa1951628e8f210daf1b082d34f43881cf75c8e9523e3e23b513318c9cd`. Do not repeat this radial inflation approach; the remaining shoulder defect needs a pose-specific directional shape, not a spherical push.

**Rejected wrist test — 2026-09-14.** Tested a loaded wrist-cuff shape gated by hand rotation. It moved zero vertices in every representative pose because this asset has no forearm/hand mixed-weight ring for the correction to govern. The candidate was immediately restored to the same SHA above. A wrist improvement requires a topology-aware shape based on the actual rigid ownership boundary, not a conventional blend-ring morph.


### ChatGPT — 2026-09-12 — whole-body imported-character movement certification

Added a whole-body retarget regression suite that deliberately authors the source character in a non-canonical rest pose, then checks five representative exercise families across five points in each clip. The suite covers squat (torso, hips, knees, ankles), bicep curl (upper arm, elbow, wrist, fingers), shoulder press, push-up, and pull-up. It compares anatomical segment directions rather than raw bone quaternions so different source-bone roll remains valid. The purpose is to prove the absolute-pose importer is general, not a bicep-curl special case.

The real candidate GLB remains outside the repository. Its skin-weight audit is therefore separate from this code regression suite. A temporary branch-only GitHub Actions workflow runs tests, typecheck and the production build for this certification work.

### ChatGPT — 2026-09-12 — absolute imported-character pose transfer

Imported characters now take the canonical resolved pose as an absolute anatomical target instead of adding canonical deltas to the asset rest pose. This brings A/T-posed arms into the exercise pose and lets authored-open hands reproduce the canonical grip while preserving the source skeleton, bone lengths, weights and passive helper/twist bones.

The retargeter evaluates canonical world bone frames, aligns them to the imported character facing direction, converts them through each source bone authored-to-anatomical basis correction, and writes the resulting local rotations through the source hierarchy. Regression coverage includes a deliberately T-posed character and an authored-open hand; the grip assertion checks finger segment directions because authored bone roll can differ even when the anatomical segment is correct.

### Claude — 2026-09-12 — imported characters are preserved, not rebuilt

The rig is a *driver*, not a skin skeleton. The import path now says so.

Rebinding rebuilt an imported surface onto the 53 canonical bones by
re-placing every vertex through a blend of per-bone transforms. Measured
against the file's own rest pose on a 160-bone Rigify character, that moved
**37.8% of edges beyond ±20%, 21.7% beyond ±50%, 5.8% past double, worst
33.2×** — before a single frame was played. It was the cause of the faceted
torso and clawed hands, not the asset.

`retargetedCharacterSource` replaces it for imports. The file's vertices,
inverse bind matrices, weights and bone hierarchy are untouched; the canonical
rig's joint angles are transferred onto the mapped source bones each frame,
through the change of basis `bindRetarget` already worked out. The same
measurement now reads **0.00% at every threshold, worst 1.00×**. The only
change made to a character is a uniform scale on its root so a model of any
height stands at the rig's scale — and because `applyRetarget` already scales
root motion by the model's height, the two cancel and a step is a step.

Three optional members on `CharacterBuild` carry it, so nothing else in the
app had to learn about retargeting:

- `driver` — how a character that kept its own skeleton is posed.
  `applyCharacterPose` branches on it and is otherwise unchanged.
- `handMatrix` — the character's own hand, restated in the canonical hand's
  basis, so the rig's grip offsets apply unchanged. A preserved import has its
  own proportions, so its hands are not the rig's hands; equipment follows
  this instead. The export additionally cancels the root scale, so a dumbbell
  parented to an imported hand stays a real dumbbell.
- `sampler` — the animation on the character's own bones. `bakeClip` gained
  `boneTracks`, off for such a character, because the canonical bone tracks
  would name bones the exported file has no nodes for.

Bones the rig does not drive — twist bones, helpers, a whole face rig, 108 of
160 on the test character — stay in the source hierarchy at rest and ride
their parents, which is what they were authored to do. They are not "unmapped
weight" to be redistributed, and the orphaned-vertex concept does not exist on
this path.

Imports default to preserving. Rebinding stays selectable, labelled a
diagnostic: it is still the only way to see a character on the studio's own
proportions. The old retargeting side channel (`CharacterView`, the store's
`binding`) is gone — an import is now an ordinary registered source, which is
precisely what makes equipment and export work on it.

Six regression tests (`imported.test.ts`) run on a Rigify-shaped fixture
round-tripped through a real GLB, so no asset enters the repository: rest
geometry identical vertex for vertex; the angle arriving at the character's
elbow is the angle the rig holds; twist bones keep their authored local
transform through the rep and travel with the arm; helper bones count as
undriven rather than unweighted; the grip frame is the hand's own to within a
micrometre at four points in the rep; and the exported GLB carries the
imported mesh and skeleton, parents the dumbbell to the character's own hand
bone, and plays back to within a millimetre of the viewport.

The built-in character is untouched and remains the default. 177 tests pass.

### Claude — 2026-09-11 — importing a Rigify character, and imports with holes in them

Two importer changes, found by putting a real Rigify-rigged GLB through the new
character layer. Both are general; neither is specific to that file.

**Rigify deform names.** `DEF-upper_arm.L`, `DEF-spine.003` and the rest matched
nothing, so a Rigify export arrived with 30 of 53 bones mapped and every one of
them a finger. Its spine is numbered rather than named — `DEF-spine` is the
pelvis and `DEF-spine.006` the head — so the synonyms now carry the whole set.
The test file maps 52 of 53; only our own synthetic `root` is left, which has
no counterpart in any character.

**Vertices the rig cannot use.** The rebind already handed an unmapped bone's
weight to its nearest mapped ancestor. Two cases defeat that: a face rig
parented to the armature rather than to the head, so walking up reaches
nothing; and `neutral_bone`, the placeholder Blender's exporter gives vertices
that belong to no vertex group at all. Both used to be pinned to the pelvis,
which dragged whole limbs across the hips as long shards. Each such vertex now
binds rigidly to the bone nearest it at bind time, so it rides the part of the
body it sits on.

That is a graceful failure, not a repair, and it is reported as one: the count
comes back in `RebindReport.orphaned` and the character panel says the vertices
carried no usable weight — a gap in the file's own weighting, not in the
import. On the file that prompted this, 1,922 of 10,839 vertices (17.7%) are
unweighted, symmetric at 961 a side, all outboard of the elbow: both forearms
and both hands. Rigid binding keeps them attached to the right limb; it cannot
make them deform, and the arms still shred through a curl. The fix belongs in
the asset.

Four character tests were given an explicit 30 s timeout. Building the built-in
surface runs every repair pass over 14k vertices, which is seconds rather than
milliseconds, and it was tripping vitest's 5 s default on a slower machine. No
assertion changed.

### Claude — 2026-09-10 — the character layer, made replaceable

The visible character was welded to the animation. `buildSkinnedRig` imported
one mesh builder, the viewport imported another, the exporter hardcoded the
first, and the surface was bound to the rig by *bone index* — so no externally
authored mesh could be dropped in without editing all three. This separates the
three layers the studio actually has:

1. **Rig** (`src/rig`) — bones, limits, poses. Unchanged, and knows nothing
   about surfaces.
2. **Skinning/deformation** (`src/character`, new) — how a surface attaches to
   those bones, plus whatever per-character corrections it needs.
3. **Visible mesh** — supplied by a `CharacterSource` and replaceable without
   touching either layer above.

**The interface.** A `CharacterSource` has an id, a label, a declared set of
capabilities and an async `build(rig)`. Every source ends at
`assembleCharacter`, which binds its surfaces to a freshly built canonical bone
hierarchy, so the studio and the exporter cannot drift apart: both ask the
registry for a source and pose what comes back through `applyCharacterPose`.

**Registered characters.** `builtin` is the existing anatomical surface, still
the default. `procedural` is the original tube-and-blob mannequin, kept as a
diagnostic model — cheap, obviously synthetic, and with trivially predictable
weights, which is what you want when the question is whether a deformation
problem is in the rig or in the mesh. `registerBundledCharacter(...)` is the
one call that will put a higher-quality GLB in front of the animation; nothing
is registered yet, because there is no asset yet.

**Rebinding by bone name.** `rebindToCanonical` takes an imported skinned mesh
and re-places every vertex through `q = Σ wᵢ · (Cⱼ · S · Bᵢ⁻¹) · p` — out of
each source bone's bind frame, through a uniform height scale, into the
canonical bone's rest frame — then rewrites the skin indices to our bone order.
Bones our rig does not carry (twist bones, helpers) hand their weight to the
nearest mapped ancestor. UVs and materials survive untouched, which is the
point: a textured, mapped, higher-quality mesh keeps everything that makes it
higher quality. Two honest limits, both documented at the function: proportions
follow the rig rather than the model, and custom normals, tangents and morph
targets are authored against the old bind pose, so they are dropped and the
normals recomputed.

**Deformation stacks are per character.** The elbow corrective and the armpit
morph correctives are authored against particular vertices of the built-in
mesh, so they now live in that character's own stack and are handed to nobody
else — asserted by test. The exporter no longer knows what a shoulder
corrective is: it asks the active character's stack for a sampler and bakes
whatever tracks come back.

**Capability, not assumption.** The anatomy view asks
`capabilities.anatomy` before mounting the écorché variant; a textured import
says no and gets the plain surface rather than a mis-mapped one.

**Imports keep both routes.** Rebinding onto the studio rig is the default and
produces an ordinary registered character — equipment, grip and export all work
on it unchanged. Retargeting the model's own skeleton is retained beside it for
a character whose proportions must be preserved. The panel gained a character
picker and a bind-mode picker and nothing else; the larger character-management
UI is deliberately not built.

Untouched: the canonical skeleton, joint limits, IK, contacts and grip,
equipment sockets, exercise definitions, the biceps-curl motion, animation
validation and timing.

Verified: the built-in character still builds, binds and animates; a GLB loaded
through the new source architecture rebinds onto the canonical rig and is
driven by the same curl; the dumbbell is exported as a child of `hand_r` for an
imported character as for the built-in one; posed bone rotations match the
baked clip's tracks at four points through the rep; and swapping characters
live in the viewport keeps the dumbbells in the hands. 168 of 169 tests pass —
the one failure is the unfinished head pass from the previous round, recorded
below, not a regression from this work.

### Claude — 2026-09-09 — shoulder junction folds, and the armpit

Two defects, both the source's, both on the shared surface so the Character
view, the Anatomy view and the GLB export get the same repair.

**The fins.** A row of vertices at y ≈ 1.40, from 20 mm to 100 mm either side of
the midline, alternated in and out of the surface by 11 to 20 mm — a zig-zag
along the top of the trapezius that read as a pale fin from behind. Everything
else in that region deviates from its own neighbourhood by about 1.5 mm, which
is what curvature looks like at this vertex spacing, so the fold is noise an
order of magnitude above the anatomy. `smoothShoulderFins` measures each vertex
against the mean of its neighbours along its normal and removes only the part of
that deviation above 4 mm, so a real ridge is inside the threshold and untouched:
a clamp on outliers, not a smoothing pass. 48 vertices move, by at most 15.8 mm,
and the worst deviation falls from 19.5 mm to 5.6 mm.

- Self-intersecting non-adjacent triangle pairs around the shoulders fall from
  188 to 146: 46 of the fold's own pairs removed and 4 created.
- The four that remain cannot be removed from this side. The fin is a doubled
  sheet, and the leaf underneath has to travel out through the leaf above it to
  reach the surface they should share. Every guard tried against that — halving
  the corners of a crossing triangle, dropping them outright, dropping only the
  corner moving towards the other sheet — cascaded through the fold and took the
  whole repair back to nothing. Resolving them means moving the leaf above too,
  which is the outer shoulder.

**The armpit.** The source hands the axilla a scrambled binding: adjacent
vertices on the same sheet of skin, 40 mm from the humerus axis and 200 mm below
the shoulder joint, are bound one to the upper arm outright and the next to the
second spine segment outright. Raising the arm swings one and leaves the other,
so a 15 mm edge reaches 130 mm.

`correctArmpitWeights` recovers the two sheets by majority over each vertex's own
ring, counts rows out from the fold where they meet, and grades the arm's share
across five rows either side. Two influences per vertex throughout, and the
majority owner of every vertex is preserved — the ribcage stays the ribcage —
so the body's own proportion tests measure the same chest and shoulder width
afterwards. 772 vertices are regraded and the worst step in the arm's share
across an edge falls from 0.69 to 0.16.

That is as far as weights can go, and the reason is arithmetic rather than
tuning. An edge carries (difference in the arm's share) × (how far its ends
swing). At 100° of abduction the axilla swings about 180 mm, so a 12 mm edge
holds 2× only if the share changes by less than 0.07 across it — fifteen rows
from arm to torso. The surface has about six rows to give, and widening the band
past them drags the chest up with the arm. Every graded weighting tried, from a
six-row blend to an edge-by-edge relaxation against a per-edge ceiling, lands
between 4× and 12×.

**So the binding keeps the crease and a corrective takes the tearing.**
`buildArmpitCorrectives` skins the surface at eighteen sampled shoulder poses per
side, repairs each one directly — over-stretched edges pulled together,
over-squashed ones pushed apart, inside the shoulder's field and nowhere else —
and carries the repair back through the skinning matrices into bind space, where
it becomes a morph target. Eleven samples are textbook lifts and seven are taken
from the exercise clips themselves, because the exercises twist the shoulder as
they raise it — the pull-up by more than 40° — and an earlier version driven by
abduction and forward-lift angles alone made the pull-up *worse*, 5.3× to 8.4×,
by applying shapes built for a shoulder that was not there. The shapes are
blended by how close the shoulder is to each sample, normalised so they never
sum to more than one correction.

They are ordinary glTF morph targets with an ordinary weights track: `bakeClip`
samples the influences from the same pose the bones come from, using the same
function the viewport uses, so the exported animation deforms exactly as the
studio does. The exported file grows from 1.0 MB to 7.0 MB, because glTF stores
each morph target as a full-length vertex array and three's exporter does not
emit the sparse form these would compress to.

Worst stretch and squash across the shoulder and armpit, excluding the elbow,
for the source binding and for this one:

| | source | repaired |
| --- | --- | --- |
| one arm abducted, 30–130° | 6.23 / 0.56 | 1.80 / 0.54 |
| one arm forward, 45–120° | 5.69 / 0.36 | 1.51 / 0.54 |
| both arms, 30–165° | 7.81 / 0.09 | 3.87 / 0.12 |
| dumbbell curl | 1.55 / 0.63 | 1.55 / 0.63 |
| shoulder press | 7.33 / 0.09 | 3.39 / 0.22 |
| push-up | 4.56 / 0.47 | 3.37 / 0.48 |
| pull-up | 8.68 / 0.10 | 4.31 / 0.20 |

**Against the limits declared for this round — 2.0× stretch, 0.35× compression —
one arm at a time meets them through the whole range the exercises use, and the
curl meets them. Both arms together, one arm past 130°, and the loaded press,
push-up and pull-up do not.** They are between two and three times better than
the binding they replace and they are not yet right. The tests hold the measured
values as ceilings so none of it can be given back quietly.

Triangle orientation and area in the posed shoulder, against the same poses on
the source: inverted triangles 62 against 50 at 60° of abduction, 372 against
364 at 100°, 680 against 674 at 150°, 847 against 788 at 150° of forward lift —
the folding at extreme angles is the character's own and this work adds a little
to it. Self-intersecting pairs in the same region go the other way, and by much
more: 14 against 46 at 60°, 10 against 46 at 100°, 13 against 46 at 150°, 260
against 386 at 150° forward.

Bind positions: 76 vertices move in total across every shared repair now in
place, by at most 29.9 mm, all of them on the back of the neck and the top of the
shoulders. The full-body silhouette is unchanged — same shoulder width, same
chest, same waist — and the repository's own proportion tests check it.

Verification: 158 tests pass — the repository's own 122 unmodified, plus 36 for
the anatomy build, of which 9 are new for the shoulder: the folds flattened, the
armpit regraded without moving a single vertex's owner, two influences per vertex
everywhere, nothing moving until an arm lifts, one arm inside the declared limits
through its range, the improvement over the source, no exercise made worse by the
correctives, the correctives present in the exported GLB with a weights track
that actually rises, and the anatomy view carrying the same shapes.
`npm run typecheck` and `npm run build` are clean.

### Claude — 2026-09-09 — head-to-neck weights and the nape ledge, shared by every consumer

The character's generator binds by a single rule near the top of the body —
`if (part !== 'body' || sourcePoint.y > 1.50) influences = [{ sourceName: 'head', weight: 1 }]`
— so everything above 1.50 m in the source becomes head:1.00 with no blend. On
the finished mesh that leaves 3,868 vertices bound wholly to the head, reaching
down to y = 1.397, and only seven vertices in the whole body carrying both head
and neck weight. The neck bone runs from 1.420 to 1.520 and drives almost none
of the surface over it, so the neck does not deform: it is rigid with the skull,
and the transition to the chest happens as a step at the edge of the head's
region rather than along the neck.

The same rule also decides which conversion transform each source vertex is
carried through, and the head's transform does not land where the spine's does.
So the seam is a ledge in the surface as well as a cliff in the weights: down the
midline the back of the neck sits at z = -35 mm from y = 1.39 to 1.41 and then
steps back to -69 mm across a single 13 mm row, and the nape overhangs a recess.

Both repairs now live in `src/body/neck.ts` and run from
`buildAnatomicalBodyGeometry` — the one place the decoded surface is built — so
the studio's Character view, the Anatomy view and the GLB exporter all get the
same corrected mesh without any of them asking for it. The earlier Anatomy-only
copies of both are gone.

- **A chain, not a blend.** Spine to neck over the lower half of the head-bound
  block, neck to head over the upper, each a straight ramp in height. Two
  influences per vertex, never three, and the partner switch is a level surface
  at 1.45 m so head weight is never adjacent to spine weight. 1,347 vertices
  rewritten, 1,213 of them previously head:1.00.
- **The block is taken whole, never cut off by radius.** Every version with a
  radial taper inside it put head weight against spine weight out at the edge
  and tore the surface open; pulled in to 85 mm it measures worse too, taking
  rotation from 1.29× to 1.59×.
- **The neck's sideways reach is trimmed** beyond 65 mm — its own surface at the
  base — fading to nothing by 145 mm. The source gave the neck bone a share of
  twelve vertices on the top of each shoulder, out to 170 mm on the deltoid; a
  head turn stretched an 8.6 mm edge there to 2.15× and squashed its mirror to
  0.31×. On the shoulder the freed share goes to the collarbone rather than the
  arm, so lifting the arm behaves exactly as it did before, to within float
  noise.
- **Positions and colours are untouched.** This changes which bones drive the
  neck, not where the neck is, and a test compares every position and colour
  component against the source build.

Deformation across every edge the repair touches, measured against the same
edges on the source binding (stretch / squash):

| pose | repaired | source |
| --- | --- | --- |
| flexion 20° | 1.158 / 0.732 | 2.937 / 0.839 |
| extension 20° | 1.266 / 0.839 | 2.748 / 0.249 |
| rotation 25°, either way | 1.294 / 0.828 | 2.213 / 0.310 |
| flexion 15° with 20° turn | 1.218 / 0.743 | 2.779 / 0.188 |

The limits — no more than 1.30× stretch, no less than 0.60× compression — were
fixed before the weighting was tuned, and the weighting was changed until it met
them rather than the other way round. Maximum influences per vertex: 2. Largest
step in the head's share across an edge: 1.00 before, 0.43 after — and the
largest one left is a 32 mm edge inside the throat, which is the ramp's own
gradient rather than a boundary. The largest step between any two bones is 0.94,
between the collarbone and the top of the spine on the shoulder: two bones that
hold still together, so it is a step in the weights and nothing in the skin.

`correctNeckLedge` closes the ledge, on the shared mesh, before anything reads
it — the weight repair included, because it finds the seam from the source's own
head binding. The seam and the step are measured from the mesh itself in 2.5 mm
bands with a 13 mm window, every band keyed on |x| so the result is mirrored by
construction, and each row under the seam slides back towards the nape's depth:
most at the seam, less further down, nothing at all 55 mm below it or 85 mm out
to the side. The ledge becomes a slope from the nape into the upper trapezius.

- **40 vertices move, by at most 29.9 mm**, all of them on the back of the neck.
  The step being closed is 34.2 mm and the row directly under the seam has to
  reach the nape, so that is the floor for closing it without moving the head
  block — which carries the face, the jaw, the ears and the hairline, and is
  untouched. Spreading the ramp further would move more rows, not fewer
  millimetres.
- **Depth only.** No vertex moves sideways or vertically, and none moves
  forwards. The trapezius ridge is a lateral form, so sliding the surface back in
  depth cannot flatten it — which is what an earlier smoothing pass over the same
  region did, and why this one is not a smoothing pass.
- **Nothing new folds.** No triangle in the mesh turns over or is pinched below a
  quarter of its area, and a Möller-Trumbore pass over the 768 triangles round
  the neck finds 70 intersecting non-adjacent pairs against the source's 74: the
  correction removes four and adds none. The remaining 70 are the source's own
  shoulder fold, untouched here.
- The largest gap between neighbouring rows down the midline falls from 34.2 mm
  to 9.6 mm, which is the spacing the rest of the neck already has.

The Anatomy view's private levelling pass is deleted: it was a second correction
for the same defect applied to one mode only. Anatomy now inherits the corrected
base and sculpts relief on top of it, and a guard over the whole écorché surface
damps any displacement — from any stage — that would leave a triangle facing
against the character's own. Of its 27,460 triangles, 0 do.

**Unresolved when this landed, and taken up in the round above.** Raising the arm
tore the armpit: 5.20× stretch at 60°, 8.03× at 100°, and 0.12× compression at
45° of forward flexion, on edges where the thorax meets the upper arm. Those
numbers were the character's own — the source mesh measured identically, before
any of this work — and nothing in this entry changed them. The shoulder round
above brings them down by two to three times and does not finish the job; the
figure is not ready for exercise production while any of it stands.

Verification: 150 tests pass — the repository's own 122 unmodified, plus 28 for
the anatomy build, of which 13 cover this junction: two influences summing to
one, head share handed over by position, left/right symmetry, deformation limits
under neutral, flexion, extension, both rotations and a combined pose, the arm
left as the source had it, colours unchanged and movement confined to the back of
the neck in depth alone, the ledge closed into a slope and mirrored, no triangle
turned over or pinched anywhere in the mesh, Character and Anatomy sharing one
corrected base, and both the corrected weights and the corrected positions read
back out of a decoded GLB export. `npm run typecheck` and `npm run build` are
clean.

### Claude — 2026-09-09 — Anatomy view: sculpted arm and elbow deformation

Adds a fifth view mode, `Anatomy`, beside Skeleton / Muscles / Combined /
Character. It renders the same skinned body as a greyscale écorché on a black
stage. Nothing in this entry changes the Character view, the muscle overlay, the
exercise definitions, the rig, the IK, the grip, the animation timing or the GLB
export; the anatomy geometry is built separately and the character's own surface
is asserted bit-identical before and after.

- **Muscle relief from the existing model.** Each belly in `muscles/model.ts` is
  read as a continuous 0–1 field over the bind-pose surface and used to displace
  it along its own normals, so a muscle is form rather than colour. Nine fields:
  three deltoid heads, biceps, triceps, forearm flexors and extensors, plus a
  brachialis and a brachioradialis that exist in `body/ecorche.ts` as shape only
  — no group id, no activation row, never a belly in the overlay. Peak relief is
  13.0 mm and the mean is 4.1 mm over 1,062 vertices.
- **Arm surface settling.** The source mesh carries a horizontal band across the
  upper arm, visible in Character mode too, which made the relief read as bulges
  stacked on a segmented tube. A few weight-limited Laplacian passes over the arm
  region remove it. Mesh seams are welded for the purpose so a split vertex ring
  does not shade like an edge.
- **Elbow skin blend.** The character hands the humerus over to the forearm
  across roughly 40 mm on one side of the joint and 20 mm on the other, which
  deforms like a hinge between two tubes. Anatomy mode redistributes that pair's
  share on a smooth ramp, symmetric and ±50 mm.
- **Elbow pose corrective.** A bind-space offset scaled by elbow flexion, driven
  by `4·s·(1−s)` on the forearm's weight share — strongest where blend skinning
  actually collapses. Exactly zero at extension, so the clip still loops;
  symmetric left to right; bounded at 25 mm.
- **Activation colour is built and held at zero.** `ECORCHE_GREYSCALE` keeps the
  view in grey while the anatomy is being judged. The per-group field, the
  shader hook and the border threshold all still work.
- **Local refinement is written and switched off.** `body/refine.ts` does
  red-green subdivision of a named region with interpolated skin weights. A
  triangle-by-triangle audit showed most high-flexion surface contact is the
  upper arm meeting the forearm rather than elbow-ring density, so it is not used
  here. The note at the top of `body/elbow.ts` records what was measured and why
  the remaining contact was accepted.

The user approved each stage from rendered previews before this checkpoint, and
approved the elbow result explicitly. Verification: 137 tests pass — the
repository's own 122 unmodified, plus 15 for the anatomy build — and
`npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-09 — skin, eyes and clothing-seam preview

- Replaced the grey teaching surface with a warm natural skin palette while
  preserving the existing red/orange active-muscle overlay.
- Rebuilt the eyes as visible sclera with separate brown irises and pupils,
  slightly compressed vertically and positioned inside the existing sockets.
  The eye surfaces remain part of the same head-skinned draw call.
- Replaced interpolated vertex-colour clothing boundaries with geometric cuts
  through triangles at the waist and mid-thigh. The resulting waistband and
  hems are straight, share the body's skin binding and remain poseable without
  grey fringes or saw-tooth triangle edges.
- Preserved the approved head, shoulders, torso, legs, feet, grip, dumbbells and
  bicep-curl motion. The generated mesh is 13,952 vertices and 27,460 triangles.

The user approved the full-body and detail validation renders before commit.
Verification: 122 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — approved shoulder and head refinement

- Rounded and narrowed the raised, squared-off deltoid caps and introduced a
  natural neck-to-shoulder slope without moving the underlying shoulder joints.
- Shortened the elongated head profile and added restrained width through the
  cranium and temples while keeping the crown aligned to the 1.75 m rig.
- Preserved the approved torso, legs, feet, curl motion, dumbbell placement and
  two-handed grip from the preceding correction.

The user approved the rest, mid-curl and top-curl validation render before this
change was committed. Verification: 122 tests pass; `npm run typecheck` and
`npm run build` are clean.

### Codex — 2026-09-08 — `codex/anatomical-reference-character`

Purpose: correct the withdrawn anatomical character using the supplied curl
reference as a visual gate, without changing Claude's muscle-overlay system or
the accepted lower-body proportions.

- **Correct bind conversion.** Rebuilt the MakeHuman surface in the canonical
  rig's actual rest pose. The source spine is now mapped waist-to-neck instead
  of backwards; upper-arm, forearm, thigh and shin twist segments are fitted
  proportionally; palms use wrist-to-knuckle length; every finger segment maps
  joint-to-joint. Tiny cross-side source weights are removed before collapsing
  to the app's two-influence skin.
- **Reference-shaped body.** Applies the adult-male and muscular CC0 targets,
  then sculpts a lean chest-to-waist V taper. The accepted legs and feet remain
  anatomically shaped and the sole is fitted to the app's floor. The source's
  helper hair strips are deliberately excluded; they are rig guides, not hair.
  The result is 13,524 vertices and 27,036 triangles, split across six generated
  modules so no GitHub blob approaches the earlier transfer limit.
- **Face and clothing.** Keeps the anatomical head, nose, lips, ears and eye
  geometry, uses a neutral anatomical-grey teaching surface and fitted dark
  shorts, and remains one skinned draw call shared by viewport and GLB export.
- **Grip and motion.** Retains the smaller round dumbbells, corrected anatomical
  grip position and 126-degree curl. Rest, mid-curl and top-curl renders include
  the real equipment transforms and show the handle inside each closed hand.
- **Regression coverage.** The contracted-curl export test now measures every
  posed triangle edge, directly rejecting torn shoulders, metre-long strips and
  exploded finger fans. Body tests cover two-weight normalization, human bounds,
  male taper, clothing, eyes and the increased anatomical-mesh budget.
- **Provenance.** Restored `THIRD_PARTY_ASSETS.md` and added a reproducible
  generator for the exact CC0 sources and rest-pose conversion.

Verification: 122 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — `codex/anatomical-reference-character`

Purpose: improve the dumbbell curl while recording and withdrawing an
unsuccessful imported-character experiment.

- **Retained:** replaced the oversized hex dumbbell ends with smaller round
  plates and reduced peak elbow flexion/shoulder travel so the weights do not
  crowd the chest. The existing grip placement and mirrored finger closure are
  unchanged.
- **Rejected and removed:** an attempted MakeHuman-to-canonical remap passed
  static mesh and bone tests but failed in the real posed preview. Its bind pose
  was incompatible with the canonical skeleton, causing torn shoulders and
  torso sections and fingers to explode away from both hands. The body also did
  not match the requested athletic male reference. All generated mesh data,
  surface-highlighting changes and third-party asset files from that attempt
  have been removed; the last known-good profile character is restored.
- **Regression coverage:** added a contracted-curl skin test which transforms
  every vertex and rejects detached or exploded geometry. This covers the visual
  failure that the earlier bone-only tests missed.

Verification: 122 tests pass, including the new fully posed skin check;
`npm run typecheck` and `npm run build` are clean.

### Claude Opus 5 — 2026-09-08 — `claude/home-gym-pt-animation-txux66`

Purpose: make the studio's character read as a person rather than a mannequin,
and make the muscle overlay usable as exercise instruction.

Preserved Codex's `067e90db` grip work unchanged: `anatomicalGripOffset` is
still what places a one-hand attachment, and its two animation tests still run.

- **Character.** Re-authored the body profiles as an athletic adult male:
  V-taper from a 0.39 m chest to a 0.27 m waist, deltoid caps, biceps and
  triceps mass, a forearm flare into a narrow wrist, patella at the knee, and a
  calf. Added a face — eyeballs with irises and lids, brow, nose, lips, jaw
  corners, ears — and a close-cropped hair shell.
- **Clothing.** Surface colour is now a vertex attribute on the same single
  mesh, so skin, dark fitted shorts, waistband, eyes, lips and hair cost one
  draw call between them. The shorts run from the hip to mid-thigh, leaving
  every joint the exercises work bare.
- **Muscle overlay.** Each belly is now built on an anatomical frame — length
  along the muscle, width across the body, depth through the skin — instead of
  spreading along an arbitrary axis. Bellies taper into tendon at both ends and
  are fitted against the body at runtime, so none of them break the skin during
  the curl and none exceed 7 mm in any other exercise. Re-placed all 21 muscle
  definitions against the new surface.
- **Highlighting.** Primary muscles are now a clear red, secondary a softer
  orange, stabilisers close to flesh tone and untargeted muscles almost
  invisible. For the curl this leaves both biceps as the obvious highlight, with
  the forearm flexors and front deltoids behind them.
- **Grip.** The thumb now extends at the knuckle and folds over, laying it along
  the handle instead of sweeping it past the palm. This rig has no
  carpometacarpal joint, so the thumb cannot oppose across the palm; along the
  bar is as close to a wrap as its joint limits allow.
- **Backdrop.** A studio/light backdrop toggle, so app-facing captures come out
  on a clean light stage instead of the editor's dark one.
- **Tests.** New `body/body.test.ts` cases for the male silhouette, the shorts'
  coverage and the eyes; a new `muscles/muscles.test.ts` covering containment,
  attachment, left/right mirroring, the biceps through the curl and the
  activation palette; a new `equipment/grip.test.ts` checking each handle stays
  wrapped by the fingers and thumb and rigid in the hand throughout both
  dumbbell exercises.

Verification: 121 tests pass; `npm run typecheck` and `npm run build` are clean.

### Codex — 2026-09-08 — `codex/fix-dumbbell-grip-position`

Purpose: keep dumbbell handles visibly enclosed by the fingers throughout
hand-held exercises.

- Moved the default one-hand equipment grip from inside the palm to the centre
  of the curled-finger loop, with mirrored left/right palm-facing offsets.
- Applied the anatomical default to the bicep curl and dumbbell shoulder press.
- Expanded animation tests to check both hands throughout the full repetition
  and detect a handle positioned inside the palm.

Verification: 81 local tests passed on the compatible Codex checkout;
`npm run typecheck` and `npm run build` completed successfully.

## Baseline history

### Claude Opus 5 — 2026-09-08 — commit `e6ef05b4`

Added the anatomical skinned body, corrected mirrored finger flexion, and added
the dumbbell shoulder press and pull-up. Reported 101 passing tests.

### Claude Opus 5 — 2026-09-08 — commit `287f72c6`

Created the initial Home Gym PT Animation Studio, including its canonical rig,
IK, equipment, exercise definitions, editor, retargeting and exporters.

### Repository owner — 2026-09-07 — commit `df07dced`

Created the repository with the initial commit.
