# Imported character repair validation

The production path preserves the imported source skeleton, bind data, mesh, weights and proportions, then transfers the canonical anatomical pose onto that source rig. The current proven character remains `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` version 5. A separate review copy adds only metadata that opts into the new directional outer-elbow corrective; it does not replace the proven candidate.

Proven v5 SHA-256: `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`  
Directional-elbow review SHA-256: `8e8df9e8adcf43e0e6473bf98efadb05a31075031f9124787429ec2aedca99e4`  
Hand/wrist weight repair candidate SHA-256: `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed`

## Hand/wrist handover weight repair candidate — awaiting approval

`HomeGymPT_Male_HAND_WRIST_WEIGHT_CANDIDATE.glb`  
SHA-256: `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed`

Built from proven v5 by local skin-weight redistribution only. **Proven v5 was not
overwritten and still hashes to `dfb0fea6…`.** Neither GLB is committed; the candidate
is not promoted and the bundled/default character is unchanged.

### What the defect actually was

The fingertip "shards" at curl Peak and the wrist-to-palm facet at curl Bottom are one
defect, not two. In v5 the influence hands over from one bone to the next across a
*single* mesh edge: the steepest edge measured **1.000** at `DEF-hand.*` →
`DEF-f_middle.01.*` and `DEF-f_ring.01.*` (one end fully hand, the other fully finger,
with no transition at all) and **0.990** at `DEF-forearm.*.001` → `DEF-hand.*`. When the
joint bends, the two ends of that edge travel on different arcs and the triangle between
them folds shut.

Three candidate causes were ruled out by measurement rather than by eye:

- **Not the character correctives.** The four `homeGymPT_elbow*` targets move 106 and 72
  vertices per side, all dominated by `DEF-upper_arm*001` / `DEF-forearm*` /
  `DEF-forearm*001`. Not one hand, palm, finger or wrist vertex is touched, so Correctives
  on versus Raw skinning cannot change either defect. (The naive test reports the whole
  mesh because this asset's morph convention is absolute, not relative; the footprint above
  is measured against each target's own base position.)
- **Not handle intersection.** Of the 40 worst spike vertices, none lie inside the 15 mm
  handle cylinder.
- **Not bind topology.** The hand contains no needle triangle (aspect > 20) either in bind
  or posed.

### The repair

For each of ten named bone pairs — the four MCP rings and the wrist ring, per side — the
vertex's **pooled** weight on the two bones is held fixed and only the split between them
moves. Total skin weight therefore stays exactly 1.0 by construction and no third bone is
affected. An edge steeper than a gradient cap is relaxed by exactly its excess, iterated to
convergence with a Jacobi sweep so the outcome does not depend on the order edges happen to
be visited — which is what keeps the two hands identical, their vertices being numbered
differently. Editing is confined to vertices lying on an over-steep edge or one mesh ring
out from one; everything beyond is pinned, so the change cannot creep up the forearm or out
along the fingers.

Caps of 0.55 / 0.45 / 0.40 / 0.35 / 0.28 were generated and reviewed on matched Studio
stills. 0.55, 0.45 and 0.40 leave visible angular points at the ring and pinky fingertips.
0.28 over-smooths: the push-up wrist degrades from 0.0495 to 0.0178 worst area retention.
**0.35 is the smallest cap that removes the visible shards and the facet**, so it is the
candidate. The ~40% retained-area figure was treated as a review target, not a goal: the
chosen cap reaches 0.199 at curl Peak, and was selected on the stills rather than on that
number.

### What changed, and what did not

314 of 10,839 vertices, 2.90%. Byte-identical between v5 and the candidate: `POSITION`,
`NORMAL`, `TEXCOORD_0`, `TEXCOORD_1`, `COLOR_0`, `JOINTS_1`, `JOINTS_2`, `WEIGHTS_1`,
`WEIGHTS_2`, the index buffer, the node hierarchy, the skin definition and the inverse bind
matrices. Only `JOINTS_0` and `WEIGHTS_0` differ. Worst |weight sum − 1| is 5.2 × 10⁻⁸.
Hand-area vertices still carry at most 4 influences, sorted descending, which is the
source's own convention — and the one that matters, because three.js reads only
`JOINTS_0`/`WEIGHTS_0` and renormalises them.

Because the repair changes weights only, the bind pose is unchanged by construction: at
bind every bone matrix is identity relative to its inverse bind, so the skinned result is
independent of the weights. A pinned bind-geometry checksum confirms it, and a full-figure
render diff finds changes confined to the two hands and wrists (0.055% of pixels, the
remainder being single-pixel anti-aliasing noise along silhouettes).

### Measured against v5

Production path, pinned 1,440-triangle handover set, aspect normalised so an equilateral
triangle scores 1:

| Pose | worst area retained | worst aspect | triangles < 25% | triangles < 40% |
|---|---|---|---|---|
| Curl Peak 2.00s | 0.040 → **0.199** | 38.9 → **27.8** | 22 → **8** | 46 → **32** |
| Curl Bottom 0.00s | 0.060 → **0.175** | 29.7 → **27.8** | 22 → **8** | 46 → **32** |
| Shoulder press | 0.0035 → **0.224** | 437.8 → **27.8** | 22 → **6** | 46 → **32** |
| Push-up 45% | 0.0495 → **0.0567** | 41.3 → **34.1** | 18 → 30 | 52 → 64 |
| Pull-up 45% | 0.0220 → 0.0220 | 108.6 → 108.6 | 36 → **16** | 85 → **83** |

Whole-rep edge strain, all five exercise families:

| Exercise | max stretch | P99 | P95 |
|---|---|---|---|
| Bicep curl | 3.820 → **2.183** | 1.4503 → 1.4461 | 1.1978 → 1.1985 |
| Air squat | 3.677 → **2.109** | 1.3996 → 1.3978 | 1.1716 → 1.1727 |
| Shoulder press | 3.677 → **2.867** | 1.7094 → 1.6822 | 1.2320 → 1.2318 |
| Push-up | 3.848 → **2.274** | 1.6516 → 1.6485 | 1.2396 → 1.2380 |
| Pull-up | 8.475 → **4.151** | 1.9430 → 1.8954 | 1.2833 → 1.2822 |

Edges stretched beyond 2× fall everywhere (curl 22 → 12, press 128 → 114, pull-up 94 → 64).
The cost is a small rise in mildly compressed edges (curl 117 → 119, push-up 51 → 63 below
0.5×): the extreme collapse is spread rather than concentrated.

Grip, curl, all five review frames:

| Measure | v5 | candidate |
|---|---|---|
| Reach use | 0.9262 | 0.9262 |
| Wrap coverage | 205.39° | 205.39° |
| Within envelope | yes | yes |
| Handle penetration, per hand | 103 vertices | 101 vertices |
| Deepest penetration | 14.57 mm | 14.05 mm |

Reach and wrap are identical because `measureGripFit` reads the canonical rig, not the
skin; a weight repair cannot move them. The handle figures are skin-derived and improve
marginally. The dumbbell remains rigid and centred, and the curl motion is untouched.

### Residuals recorded, not hidden

- **The pull-up's worst triangle is not a weighting problem.** Triangle `1227/4391/4397`
  retains 2.2% of its area, unchanged at every cap, and its blends are 0.466 / 0.427 /
  0.288 — a gradient well inside the cap. It collapses from rotation magnitude alone.

  **Correction (2026-09-15).** The 102.6° and 115.4° figures quoted here originally were
  the magnitude of the relative quaternion between hand and forearm helper — flexion,
  deviation and forearm twist added together — and are not wrist extension angles. Measured
  anatomically, the **pull-up's is an artefact**: almost all of it is forearm pronation
  (79–101°, normal for an overhand grip), true wrist angulation never exceeds 53°, and the
  visible forearm-to-hand angle never exceeds 33°. What collapses that triangle is the
  pronation concentrated at the hand bone, not a wrist bend. The **push-up's is real**:
  102.7° of true extension at the top of the rep, 74.8° at the bottom, against a typical
  human limit of 70–80°, caused by the shoulder sitting 218 mm ahead of the hand so the
  forearm leans 25° off vertical. Both remain motion-side observations; no exercise
  definition was changed and none should be on the strength of this repair. See
  `AI_CHANGELOG.md` for the full decomposition.
- **v5's own wrist weighting is marginally asymmetric.** 559 of 1,790 wrist edges differ
  between the hands by up to 0.019 in blend, although the multiset of vertex values mirrors
  exactly and the topology matches (726 vertices, 1,790 edges, mean valence 5.156 per side).
  That is why the repair band is 93 vertices on the left and 81 on the right. Above 1% of
  weight the change is exactly symmetric — 143 vertices per side, net weight moved per bone
  identical to four decimal places — and the residue is six left-side vertices moving
  between 0.1% and 1%, which is below any visible threshold.
- **Palm gap and thumb opposition are unchanged**, as intended. They remain a separate
  visual decision after this deformation fix is accepted.
- **The ~6 mm dumbbell/thigh overlap at the curl bottom is unchanged** and remains
  documented rather than fixed. Closest approach −5.86 mm (left) and −5.81 mm (right), three
  thigh vertices inside a plate per side. It is a true 3D intersection, not screen-space
  occlusion.

### Validation for this candidate

- `npm test` — **287 passed, 1 optional real-character diagnostic skipped, 36 files.**
- `npm run typecheck` — passed. `npm run build` — passed, existing >500 kB chunk advisory only.
- Optional real-character diagnostic run against **both** GLBs; passes on each.
- Grip closure remains **85%** and the elbow corrective remains **0%**. Neither changed.

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

## Live grip review tooling

The Studio now exposes the exercise's **Grip closure** in the Exercise panel. It is a normal undoable exercise edit and regenerates through the production clip generator; the authored curl default remains 85%. Use this instead of editing finger bones or source-rig rotations by hand when reviewing the remaining handle/skin intersections.

Baseline production evidence at 85% finds 103 surface vertices per hand inside the 15 mm-radius dumbbell handle, concentrated in hand/palm (30), thumb (28) and pinky (25), with far less overlap at the middle finger (3). This pattern repeats in the shoulder press, so do not move the whole dumbbell as the first response. Tomorrow, visually compare 85/80/75/70/65% using the actual imported candidate and keep the lowest-overlap value only if all digits still form a secure, natural wrap and the thumb/palm remain convincing. These saved collision counts are a diagnostic baseline, not live-v5 visual certification.

