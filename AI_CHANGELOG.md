# AI Change Log

This file records changes made by Codex and Claude. Each assistant must add an
entry whenever it changes code, tests, documentation, assets, exercise
definitions, or repository configuration.

## Unreleased

### Claude — 2026-09-16 — Stage 1: forearm proportion correction (candidate only, nothing promoted)

Stage 1 of `docs/REFERENCE_BODY_TWO_STAGE_DECISION.md`. Shoulder chain untouched — Stage 2 not started. Candidate `HomeGymPT_Male_FOREARM_CANDIDATE.glb` (`f48d48e5…5ebe9`) plus a dressed copy (`2d1434e8…70901`), built on the refmatch candidate; v7, v6 and proven v5 unchanged. Detail in the new `docs/REFERENCE_BODY_STAGE1_FOREARM.md`.

The forearm is lengthened along its own axis to the canonical rig's proportion, 10.93% → 14.86% of figure height (+79.2 mm model, +68.7 mm studio), both sides. The twist helper sits at 50.0% along and moves by its own share, so the forearm stretches uniformly instead of putting all the new length in the distal half. 2038 vertices moved, worst 79.2 mm, worst left/right difference 0.001 mm across 4178 mirrored pairs. **Skin weights unchanged** — `JOINTS_0`, `WEIGHTS_0`, `TEXCOORD_0`, `COLOR_0` and all 19304 triangles are bit-identical, bone names and joint count identical. Inverse binds rewritten for **42 of 160 joints**, exactly the moved chain; the first attempt recomputed all 160 and silently rewrote every untouched bone by the 1.29e-5 the file's node graph and stored inverse binds already differ by, which is invisible but is not "the forearm chain only".

**Contacts re-derived themselves from their own rules — nothing was nudged.** Push-up hands moved 0–8.8 mm and stayed on the floor, pull-up hands 0–1.2 mm and stayed on the bar, while free hands in curl, press and squat moved the full 68.7 mm. Bilateral mirror error 0.000 mm everywhere. Press rack rises 1.587 → 1.654 m and lockout 1.964 → 2.032 m.

Push-up true wrist extension 102.66° → **95.45°**, so the skeletal correction improves the documented hand-placement problem by 7.2° but does not solve it — 95° is still past a plausible wrist, and it stays an exercise-definition question. Curl and press wrist angles are bit-identical, which is the check that accepted motion was not rewritten to accommodate the new proportions. The v5→v6 hand/wrist handover repair sits in the stretched region and does not regress: max ring aspect 27.756173 → 27.756327. Strain P95 and P99 improve or hold in all five families; the only increase anywhere is push-up maximum stretch, +0.033, and pull-up over-3× improves 126 → 112.

**One regression, and it should be cleared before Stage 2:** the curl-bottom dumbbell/thigh overlap roughly doubles, −6.65 → −13.85 mm, because the longer forearm hangs the weight 69 mm further down a thigh that is no narrower there. Across the sampled frames the worst overlap actually improves slightly (15.59 → 13.99 mm) since the mid-lower frame gains 10.8 mm, but the bottom frame is worse than both the refmatch candidate and v7. It is contact calibration, not motion, and per the guardrails wants the dumbbell's placement rule re-derived rather than the weight nudged. Also worth recording: the harness that measures it was reading the grip rather than the leg, because `GLTFLoader` sanitises `DEF-hand.L` to `DEF-handL` and the pattern excluding the holding arm matched nothing — it returned an identical −14.58 mm for three different bodies, which is how it was caught. Fixed, and it now reproduces the documented v7 figure exactly (−5.86 / −5.81 mm, three thigh vertices).

Typecheck and build clean; suite 292 passed, 1 skipped, 1 failed — the pre-existing `strainReview` timeout.

### Claude — 2026-09-16 — rig review: measured skeletal proposal (investigation only, nothing implemented)

Investigation for `docs/REFERENCE_BODY_RIG_REVIEW.md`. No asset written, nothing implemented, promoted or merged. Proposal in the new `docs/REFERENCE_BODY_RIG_PROPOSAL.md`, with the current-vs-proposed joint overlay at `scratchpad/reference-fit/07_joints_current_vs_proposed.png`.

**Comparing the character against the canonical rig as well as the photograph splits the problem in two, and they want different decisions.** As a percentage of figure height: shoulder lateral offset is 9.71 on the canonical rig, 9.68 on the character, 10.64 on the reference; forearm length is 14.86 canonical, **10.93 character**, ~14.7 reference. The forearm is a defect — the character disagrees with the canonical rig, the reference and standard anthropometry (≈0.146H) by the same ~4% of height, so correcting it moves toward all three at once. The shoulder width is a style choice — the character and the canonical rig agree to within 0.03% of height, and only the reference is wider, so widening the character moves it *away* from the rig its animation is authored on unless that rig changes too.

Proposal per side: lateral shift of the whole arm chain 1.83% of height (37.0 mm model, 32.1 mm studio) and forearm lengthening 3.92% (79.2 mm / 68.7 mm); upper arm unchanged at 0.17% off. Projected shoulder span 31.34% against the reference's 31.34%, shoulder line 60.5° → 55.5° against 53.3° — **so the slope reaches the reference within about 2° with no further yoke sculpting**, because the line was too steep from a short run rather than a wrong angle. Neutral wrist 54.68% → 51.07% against 49.3%; the remaining 1.77% is left rather than lengthening past the canonical rig's own proportion.

The joints would *not* stay plausibly inside the current surface: the proposed shoulder lands at the outer edge of the deltoid and the proposed wrist inside the hand mesh, so the arm surface must translate and stretch with its bones and the inverse bind matrices be recomputed — weights and topology need not change. Downstream, the retarget path needs no code change (it writes orientations onto a preserved source skeleton) but every hand contact moves: curl, press, push-up and pull-up contacts and the dumbbell attachment all need recalibrating from their own rules rather than by hand, and the v5→v6 hand/wrist weight repair sits exactly in the stretched region and is the most likely regression. Recommendation: take the forearm correction, hold the shoulder widening for a separate decision that includes `src/rig/humanoid.ts`.

### Claude — 2026-09-16 — reference body match candidate (nothing promoted)

Front-reference fit of the production body against the supplied photograph, per `docs/REFERENCE_BODY_MATCH_HANDOFF.md`. One candidate, `HomeGymPT_Male_REFMATCH_CANDIDATE.glb` (`19f350ad…52f4c`) plus a dressed copy (`309e751d…8e7ff`); v7, v6 and proven v5 are untouched. Full detail and the evidence set in the new `docs/REFERENCE_BODY_MATCH.md`.

3127 of 10839 vertices moved, worst 30.6 mm. `JOINTS_0`, `WEIGHTS_0`, `TEXCOORD_0`, `COLOR_0` and all 19304 triangles are bit-identical to v7, the node graph is identical and the inverse bind matrices differ by exactly 0 — only `POSITION` and `NORMAL` changed, so the skeleton, retargeting, the exercise definitions, the accepted curl motion, the 0% elbow corrective and the 85% grip closure cannot have moved.

**The headline finding is that the biggest mismatch is skeletal and must not be sculpted away.** v7's shoulders are 3.45% of body height narrower than the reference's, and a silhouette-driven optimiser closes most of that with 30 mm of deltoid mass. Measuring the outer radius from each figure's *own* humerus axis shows why that is wrong: v7's arm is already the thicker of the two at every level. The span gap is where the arm attaches — the reference's humerus axis sits 10.64% of height from the midline, v7's at 8.23%, 2.41% per side. Matching it with geometry would need ~48 mm of radial mass per deltoid. Constraining the term to what the radii support costs 0.01 points of score, so the inflation was buying a number rather than a shape. Closing it properly means a wider clavicle and shoulder joint in the rig, which is a separate decision.

What did change, each term set from a measurement: deltoid/upper arm −5 mm and forearm +7 mm radial (from the radii), thigh −5 mm and calf −6 mm (from the landmark table), a 26 mm shoulder-yoke drop, hips −5.5% and waist −8% lateral, and a +18% lower-ribcage flare — v7 holds 16.8% of height at the 68% band where the reference reaches 19.4%, which is the difference between a column and a V. Silhouette disagreement 17.10% → 15.86%; bands off by more than 1.5% of height, 29 of 49 → 23 of 49.

Method notes, because three of them changed the answer: 2912 vertices carry more than four influences so the CPU skinner has to normalise exactly as three.js does (without it, vertices land 678 mm out); the bind pose is a wide A-pose, so horizontal bands measure an arm's length rather than its width and reported the arm growing toward the wrist; and stance moves a silhouette outline exactly the way thickness does, so arm hang and leg abduction are fitted before any shape is judged — doing that made a strong apparent leg-shape error disappear entirely.

Strain is unchanged across all five exercise families (P95 within 0.009, P99 within 0.024, max within 0.025, over-3× counts identical bar a pull-up improvement from 146 to 126). Validated at ten poses against v7 on matched frames with no pinching, collapse or self-intersection. Typecheck and build clean; suite 292 passed, 1 skipped, 1 failed — the pre-existing `strainReview` timeout. The approved F3 garment transplants onto the candidate with the closest body-to-garment approach improving from 0.67 mm to 1.97 mm.

### Claude — 2026-09-16 — promote shoulder B as baseline v7 and F3 as the production shorts

Both approved candidates promoted, separately, on `chatgpt/absolute-retarget-imports`. Nothing merged.

| File | SHA-256 | Role |
|---|---|---|
| `HomeGymPT_Male_BASELINE_v7.glb` | `54222af34402281351b60d8bc2fb66f7e3fdf77d2c03eb869b5581d03adb16c4` | new baseline body — v6 + shoulder slope B |
| `HomeGymPT_Male_BASELINE_v7_SHORTS.glb` | `a5bec8fac0ce014d2ce96bcdb7b4cb846cfc65ee92ef5364f08ca0f7a2976f66` | new shipped default — that body + garment F3 |
| `HomeGymPT_Male_BASELINE_v6_SHORTS.glb` | `0761fb048510a80ce4aa8835f05a0007697086dcc60cd46a1ddb6e8ccc47b0d6` | retained fallback, untouched |
| `HomeGymPT_Male_BASELINE_v6.glb` | `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed` | retained fallback, untouched |
| `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` | `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f` | proven v5, retained fallback, untouched |

Promotion chain: proven v5 (hand/wrist handover weights) → v6 (promoted baseline) → v7 (shoulder slope B), with garment F3 over v7. `src/character/bundled.ts` now points at the v7 pair; the GLBs stay out of git behind `public/characters/.gitignore`.

**Verification, attribute by attribute.** The v7 body is bit-identical to the approved `SHOULDER_B.glb` in `POSITION`, `NORMAL`, `JOINTS_0`, `WEIGHTS_0`, `TEXCOORD_0`, `COLOR_0` and indices — only `asset.extras` gained the promotion chain. Against v6 it differs in `POSITION` and `NORMAL` alone, 884 vertices, worst 20.0 mm; `JOINTS_0`, `WEIGHTS_0`, `TEXCOORD_0`, `COLOR_0` and the indices are identical, the node graph is identical, and the inverse bind matrices differ by exactly 0. Curl motion, the 0% elbow corrective, the 85% grip closure, retargeting, the skeleton, the weights and the exercise definitions are therefore untouched. In the dressed file the body is bit-identical to v7 and the garment bit-identical to the approved F3.

**The two changes do not interact.** Rebuilding the garment over the v7 body produces a mesh bit-identical to rebuilding it over v6 — the shoulder edit provably has no effect on the shorts. It cannot: the lowest vertex the shoulder edit touches sits at y 1.467 and the garment's waistband tops out at y 1.177, a clear 289.3 mm. The containment figures measured for F3 against v6 therefore carry over unchanged.

**Unexpected difference, and what was done about it.** The garment builder no longer reproduces F3 bit for bit from the parameters recorded in F3's own `asset.extras`: 204 of 1410 vertices land elsewhere, worst 6.6 mm, all in the front panel the F candidates were iterating on. The two unrecorded knobs do not explain it — sweeping `SMOOTH` ∈ {8,12,16} × `OUTWARD` ∈ {40,70,100,140} never reaches zero and the recorded 12/70 is already closest — so `scratchpad/repair/shorts.mjs` itself changed after F3 was written, and the scratchpad is not under version control. Rather than ship a 6.6 mm variant the review never saw, the shipped garment is the approved F3 mesh transplanted onto the v7 body verbatim. Recorded in `docs/SHORTS_CANDIDATE_REVIEW.md` under *Reproducing F3*.

**Validation.** Typecheck clean. Test suite 292 passed, 1 skipped, 1 failed — the pre-existing `strainReview` 5-second timeout, which reproduces with all changes stashed and is environmental. Studio smoke test: both v7 sources register, the dressed one loads as the default, and the figure renders with the new shoulder line and the F3 shorts (`scratchpad/refine/shots/V7_default_front.png`). Re-running the containment and strain harnesses would have measured geometry already proved bit-identical, so they were not repeated.

### Claude — 2026-09-16 — review of shorts F3 and shoulder B (nothing promoted)

Independent visual review of the two candidates in the Studio, on the documented comparison poses. Both hold up; neither is promoted and no asset changed. Two findings, both recorded in the candidate docs.

**The shoulder-B push-up check was not evidenced.** `docs/SHOULDER_SLOPE_CANDIDATES.md` listed the push-up among the validated poses, but the crop used by the exercise capture script frames the upper body of a standing figure and the prone pose falls outside it — the saved images are floor. Re-captured on the full viewport: the pose is clean, the trapezius meets the deltoid in a rounded corner under load, and there is no pinch or collapse at the loaded shoulder. The recorded strain numbers never depended on those images and are unchanged.

**F3 does not touch the back of the garment.** Vertex for vertex against the promoted shorts, every garment vertex behind the hip centre line is bit-identical; all 416 that move are in front, between y 0.818 and 1.148, worst 20.2 mm. The rear deep-squat view confirmed before the garment was promoted therefore carries over to F3 without re-review.

### Claude — 2026-09-15 — front-crotch and shoulder-slope candidates (nothing promoted)

Two refinement tracks on promoted baseline v6, kept deliberately separate so each can be reviewed without the other: the shorts candidates carry an untouched v6 body, and the shoulder candidates carry no garment. Neither is promoted, no GLB is committed, and v5 still hashes to `dfb0fea6…`. Full detail in `docs/SHORTS_CANDIDATE_REVIEW.md` and the new `docs/SHOULDER_SLOPE_CANDIDATES.md`.

**Shorts front crotch.** Three candidates, F1/F2/F3, measured by how far the garment's front midline stands proud of a straight line from waistband to inseam: 8.26 mm promoted → 6.64 / 5.15 / **5.10** mm. The first three attempts made it *worse* (up to 11.73 mm): raising the panel's standoff inflates the shape rather than flattening it, because the clearance floor is enforced per vertex against that vertex's own skin and is therefore a scaled copy of the anatomy. The actual fault was that the inseam region was selected by height and midline distance alone, so it claimed the lower *front* as well as the part between the legs — and the inseam is deliberately tight at 3.5 mm, which shrink-wrapped precisely the area complained about. Gating the inseam on depth too, and letting the flattened panel reach further down, fixes it at the promoted standoff. **F3 is preferred**, and containment is why: flattening pushes the panel further off the body everywhere, so F1 and F2 introduce push-up breaches of −12.29 mm and −6.13 mm that the promoted garment does not have, while F3 matches it exactly at −2.33 mm.

**Shoulder slope.** Three candidates, A/B/C, at 9.6 / 16.0 / 23.9 mm peak drop. The shoulder falls away from the neck by 49.5, 27.9, 18.0, **10.5**, 26.3, 7.8 mm band by band — that near-flat step is the shelf that reads as square, the line running out level and then dropping off a cliff at the deltoid. A first attempt lowered only the middle of the span and tapered back to zero at the deltoid, which made the outer half flatter still; the shape now used is a ramp that reaches full depth around 55% out and holds through the deltoid, applied only to up-facing surfaces so the deltoid's outer silhouette is untouched, followed by a local relaxation to round the corner. **B is preferred** as the smallest that clearly resolves it.

882 of 10,839 vertices move for B, confined to the shoulder girdle, and only `POSITION` and `NORMAL` differ from baseline v6 — weights, skeleton, inverse binds, topology, UVs and colours are byte-identical, so arm length, retargeting, the exercise definitions and the accepted motion cannot have moved. Above 0.5 mm the change is exactly mirrored, 209 vertices a side, worst paired difference 0.015 mm. Whole-body strain is unchanged: maximum stretch identical in all five exercise families, P95 within 0.003 and P99 within 0.013, and the real-character diagnostic passes.

A note on method, because it cost time twice: the band-by-band height metric used to find the shelf takes the highest vertex in each vertical slice, and it disagreed with the renders more than once. It was useful for locating the problem and useless for judging the fix.

### Claude — 2026-09-15 — promoted: baseline v6, and the shorts layer over it

Both candidates were visually approved and are now the production character. The curl motion, the elbow corrective (0%) and global grip closure (85%) were not reopened.

| Asset | SHA-256 | Role |
|---|---|---|
| `HomeGymPT_Male_BASELINE_v6.glb` | `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed` | baseline body — byte-identical to the approved hand/wrist candidate |
| `HomeGymPT_Male_BASELINE_v6_SHORTS.glb` | `0761fb048510a80ce4aa8835f05a0007697086dcc60cd46a1ddb6e8ccc47b0d6` | shipped default, garment over that body |
| `HomeGymPT_Male_HAND_REPAIR_CANDIDATE.glb` | `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f` | retained v5 fallback, untouched |

**A defect was found in the last confirmation and fixed before promoting.** The deepest squat from behind was the one view never explicitly reviewed, and it showed the waistband as a hard sawtooth — roughly eight triangle-sized teeth of bare skin biting into the garment across the lower back. It had been invisible until now because all four backdrops key the figure from the front, so every earlier rear capture had the seat in shadow; only the rim-lit `void` backdrop reaches a figure from behind.

The cause was not what it looked like. The waistband was not collapsing: the outer shell keeps 7.4–9.5 mm of standoff at every frame of the squat. It was the cut. A triangle is usable only when all three corners pass the region test, and the test demanded ≥90% of a vertex's weight on the hip and thigh bones — so a triangle straddling the waistband, whose third corner sits further up the back on a higher spine bone, was dropped whole. The clean line the clip would have cut came out as a row of missing triangles. The region test now excludes only the arms, which is the one thing that genuinely must be excluded, and keeps the torso surface continuous. Two smaller faults went with it: the rim closing the hem and waistband was wound from index-sorted edge keys, so half of it faced inwards and was culled, and the lining floor was raised from 0.45× to 0.7× of the local clearance. The garment is now 1,410 vertices and 2,824 triangles.

**How promotion works.** The registry already had `registerBundledCharacter` for this and nothing had ever used it. The binaries stay out of the repository — they are large, and the studio has to run for anyone who clones it without them — so they live in `public/characters/` behind a `*.glb` ignore, and a new `src/character/bundled.ts` probes for them at startup: the dressed body becomes the default, the bare body is registered alongside it so deformation can still be reviewed on skin, and finding neither leaves the built-in procedural character in place.

Two things about that were not obvious and are worth recording. The probe asks for one byte with a `Range` header rather than issuing a `HEAD`, because static file middleware does not reliably answer `HEAD` for files served out of a public directory — the first version reported both present assets as missing. And registering a source is not enough to select it: the character store captures the default source id when its module is first evaluated, which happens before any probe can finish, so `main.tsx` sets the choice explicitly once registration resolves. Six regression tests cover the probe's shape, the index.html-for-a-missing-path case, both present/absent combinations and a throwing fetch.

Validation: `npm run typecheck` and `npm run build` pass; the optional real-character diagnostic passes against both promoted assets; garment containment is unchanged by the fix. `npm test` is **292 passed, 1 skipped, 1 failed** — `src/editor/strainReview.test.ts` times out on vitest's 5-second default while building the built-in character. That failure reproduces with these changes stashed, so it is a slower container rather than a regression; the test has no explicit timeout and the repo has no convention for adding one, so it was left alone rather than quietly adjusted.

The push-up hand-placement finding is deliberately **not** part of this promotion and remains a future exercise-definition fix.

### Claude — 2026-09-15 — wrist angles re-measured, and a gym-shorts candidate (assets only, nothing promoted)

Three things, none of which changes the Studio, an exercise definition, the curl motion, grip closure or a corrective. No GLB is committed and neither character candidate is promoted.

**1. The reported push-up and pull-up wrist angles were the wrong measurement.** The earlier 115.4° and 102.6° figures were the *magnitude* of the relative quaternion between the hand and the forearm's split helper — one number covering flexion, deviation and forearm twist at once, which cannot be compared with a clinical range. Re-measuring it properly means splitting the relative rotation the way the body does it: a twist about the forearm's long axis first (pronation/supination, a radioulnar motion that is not wrist motion at all), then a swing, resolved onto the two anatomical wrist axes *after* the twist has been applied to them. The axes come from the character's own bind geometry — forearm long axis, palm normal from the metacarpal plane, and their cross product — and everything is reported as a change from bind so the A-pose offset cannot masquerade as movement. The decomposition closes exactly (extension and deviation recombine to the swing to 0.0000°) and is cross-checked against the plain world-space angle between the forearm's direction and the hand's.

Two earlier attempts at this got it wrong in instructive ways, both corrected: carrying world-space bind axes through the *posed* parent orientation reported a 95° sideways deviation that was really a pronation, and rotating the wrist axes by `change · swing⁻¹` rather than by the twist itself left the components failing to account for the swing.

| | push-up | pull-up |
|---|---|---|
| old reported figure | 115.4° | 102.6° |
| true wrist extension (+) / flexion (−) | **+102.7°** at the top, +74.8° at the bottom | **−34.1°** (flexion) |
| radial / ulnar deviation | 29–34° radial | 7.7° radial at the hang → 21.4° ulnar at the peak |
| forearm pronation | 61–91° | 79–101° |
| plain forearm-to-hand angle | 115.6° at the top, 90.2° at the bottom | 7.7°–32.9° |
| left/right mismatch | 0.0000° | 0.0000° |

**The pull-up figure was an artefact.** Almost all of the 102.6° is forearm pronation, which is exactly what an overhand bar grip requires and is within human range; true wrist angulation never exceeds 53°, and the forearm-to-hand angle you would see never exceeds 33°. Deviation peaks at 21.4° ulnar, well inside the usual 30–35°. No change is needed.

**The push-up figure was real, and understated the problem's nature.** The hand is flat on the floor (hand tilt 1.5° throughout, correct), but the forearm leans 64.9° from the floor at the top instead of standing near vertical, because the shoulder sits 218 mm horizontally ahead of the hand. Wrist extension is therefore 102.7° at the top and 74.8° at the bottom; typical active human extension is 70–80°. The bottom of the rep is fine, the top is roughly 20–30° past the limit, and the cause is hand placement rather than anything in the rig or the weighting. A fix would move the hand contact forward by about 20 cm so the forearm stands up — which is an exercise-definition change, so it is recorded here and **not made**.

**2. Hand/wrist weight repair candidate reviewed against proven v5** on identical frames and cameras at curl Peak, curl Bottom, shoulder press, push-up and pull-up. The fingertip shards and the wrist facet are gone, knuckle definition survives, and no cross-exercise pose is worse. No further weight edit was made: no regression was found. Still not promoted. Full detail and before/after measurements remain in `docs/CHARACTER_CANDIDATE_REPAIR.md`.

**3. Gym shorts as a separate clothing mesh.** `HomeGymPT_Male_SHORTS_CANDIDATE.glb`, SHA-256 `cdca3f3e3d05bf81181c2be8809ab2e62a03cdce33233082a245c4b275444dfa`, built on **proven v5** so the garment can be judged without the unapproved hand repair in the picture; `HomeGymPT_Male_SHORTS_ON_HAND_WRIST_DEMO.glb` (`d0405ba7ec5a138ce466cd59071c5b27af467815e5a16dcc05335f8cf4e584ce`) is the same garment over the hand/wrist candidate. 1,380 vertices, 2,764 triangles, influenced only by pelvis, thigh and lower-spine bones.

The garment is a shell lifted off the character's own surface and **inherits the skin weights of the body surface each vertex came from**. That is what makes a cloth solver unnecessary: linear blend skinning is linear, so a vertex at `body + offset` carrying the body's own weights lands at `skinned body + M·offset` in every pose, and the standoff is preserved by construction. The body mesh is byte-identical, 0 of 10,839 vertices changed influence, the inverse binds and the skin's joint list are unchanged, and of 162 nodes exactly one changed — the armature root gained the garment as a child. No new bone, no cloth simulation, no rebinding, no body edit to make the garment fit.

Containment was measured rather than eyeballed: for every covered skin vertex, the closest point on the garment's outer surface (point to triangle, since the garment's vertices are 15–25 mm apart and a thigh can push between two of them) and which side of the cloth that skin is on. Outside the squat the worst reading is 2–3 mm, always in the gluteal cleft or at the perineum where the garment's triangles are far larger than the crease they span; the deepest squat reaches −15 mm at the front of the pelvis. Neither is visible in any render, and both are recorded in `docs/SHORTS_CANDIDATE_REVIEW.md` as the first things to check in review rather than smoothed over.

Validation: `npm test` 287 passed + 1 optional skip across 36 files, `npm run typecheck` and `npm run build` pass, and the optional real-character diagnostic passes against both shorts assets. Proven v5 still hashes to `dfb0fea6…`.

### Claude — 2026-09-15 — hand/wrist handover weight repair candidate (asset only, not promoted)

Produced `HomeGymPT_Male_HAND_WRIST_WEIGHT_CANDIDATE.glb` (SHA-256 `46180b5741216f823e4f1e0030a06d65fff0f10bd1d7b132e4c36a0814a410ed`) from proven v5 by local skin-weight redistribution at two handover rings. Proven v5 is untouched and still hashes to `dfb0fea61e4053412f4213a5904dab1ed06b416003faf4ef0eb13c27e8d5702f`. No repository code changed; neither GLB is committed. The candidate is **not** promoted and the bundled/default character is unchanged.

**Diagnosis.** The fingertip "shards" at curl Peak and the wrist-to-palm facet at curl Bottom are the same defect: the influence hands over from one bone to the next across a *single* mesh edge. Measured on v5, the steepest edge in each handover was `DEF-hand.*`→`DEF-f_middle.01.*` and `DEF-hand.*`→`DEF-f_ring.01.*` at **1.000** — one end of the edge fully hand, the other fully finger — and `DEF-forearm.*.001`→`DEF-hand.*` at **0.990**. When the joint bends, the two ends travel on different arcs and the triangle between them folds shut: 22 of the 1,440 handover triangles retained under 25% of their bind area at curl Peak, the worst at 4.0%, and the shoulder press drove one wrist triangle to **0.35%** of its area at only 33.4° of wrist bend.

Character correctives are not involved: the four `homeGymPT_elbow*` targets move 106 and 72 vertices per side, all on `DEF-upper_arm*001`/`DEF-forearm*`/`DEF-forearm*001`, and touch no hand, palm, finger or wrist vertex. Nor is it handle intersection: of the 40 worst spike vertices, none lie inside the 15 mm handle cylinder. Nor is it bind topology: the hand contains no needle triangle (aspect > 20) in bind or posed.

**Repair.** For each of ten named bone pairs — the four MCP rings and the wrist ring, per side — the vertex's *pooled* weight on the two bones is held fixed and only the split between them is moved, so total skin weight stays exactly 1.0 by construction and no third bone is touched. An edge steeper than a gradient cap is relaxed by exactly the excess, iterated to convergence with a Jacobi sweep so the result does not depend on edge-visit order. Editing is confined to vertices on an over-steep edge or one mesh ring out; everything beyond that is pinned, so the change cannot creep up the forearm or along the fingers.

Caps of 0.55 / 0.45 / 0.40 / 0.35 / 0.28 were generated and reviewed on matched Studio stills. 0.55, 0.45 and 0.40 leave visible angular points at the ring and pinky fingertips; 0.28 over-smooths and degrades the push-up wrist (worst area retention 0.0495 → 0.0178). **0.35 is the smallest cap that removes the visible shards and the facet**, and is the candidate.

**What changed.** 314 of 10,839 vertices (2.90%). `POSITION`, `NORMAL`, `TEXCOORD_0/1`, `COLOR_0`, `JOINTS_1/2`, `WEIGHTS_1/2`, the index buffer, the node hierarchy, the skin definition and the inverse bind matrices are all byte-identical; only `JOINTS_0`/`WEIGHTS_0` differ. Worst |weight sum − 1| is 5.2 × 10⁻⁸; hand-area vertices still use at most 4 influences, sorted descending, matching the source's convention. Net weight moved per bone is identical left and right to four decimal places.

**Measured against v5** (production path, pinned 1,440-triangle handover set; aspect normalised so equilateral = 1):

| Pose | worst area retained | worst aspect | triangles < 25% |
|---|---|---|---|
| Curl Peak | 0.040 → **0.199** | 38.9 → **27.8** | 22 → **8** |
| Curl Bottom | 0.060 → **0.175** | 29.7 → **27.8** | 22 → **8** |
| Shoulder press | 0.0035 → **0.224** | 437.8 → **27.8** | 22 → **6** |
| Push-up 45% | 0.0495 → **0.0567** | 41.3 → **34.1** | 18 → 30 |
| Pull-up 45% | 0.0220 → 0.0220 | 108.6 → 108.6 | 36 → **16** |

Whole-rep edge strain improves on every exercise family: maximum stretch falls (curl 3.820 → 2.183, squat 3.677 → 2.109, press 3.677 → 2.867, push-up 3.848 → 2.274, pull-up 8.475 → 4.151) and P99 falls slightly, while P95 is unchanged to ±0.004. The cost is a small rise in mildly compressed edges (curl 117 → 119, push-up 51 → 63 below 0.5×) — the extreme collapse is spread rather than concentrated.

Grip is unaffected where it is rig-derived (reach use 0.9262, wrap 205.39°, within envelope — identical, because `measureGripFit` reads the canonical rig, not the skin) and marginally better where it is skin-derived (handle penetration 103 → 101 vertices per hand, deepest 14.57 → 14.05 mm). The dumbbell stays rigid and centred; the curl motion is untouched.

**Not fixed, and why.** The pull-up's worst triangle (`1227/4391/4397`, 2.2% area) has blends 0.466/0.427/0.288 — a gradient well inside the cap. It collapses from the rotation magnitude alone: the pull-up drives the wrist **102.6°** and the push-up **115.4°** from bind, beyond human wrist extension. That is a motion-side observation, recorded here rather than acted on; no exercise definition was changed.

Also recorded: v5's own wrist weighting is very slightly asymmetric at the edge level — 559 of 1,790 wrist edges differ between the hands by up to 0.019 in blend, although the vertex-value multiset mirrors exactly. That is why the repair band is 93 vertices on the left and 81 on the right. Above 1% of weight the change is exactly symmetric (143 vertices per side); the residue is six left-side vertices moving between 0.1% and 1%.

The palm gap and weak thumb opposition seen at 85% closure are unchanged by this repair, as intended; they remain a separate visual decision. The ~6 mm dumbbell/thigh overlap at the curl bottom is likewise unchanged and still documented rather than fixed.

**Validation.** `npm test` 287 passed + 1 optional skip across 36 files; `npm run typecheck` and `npm run build` pass. The optional real-character diagnostic was run against both GLBs and passes on each. Grip closure remains 85% and the elbow corrective remains 0%; neither was changed.

### ChatGPT — 2026-09-14 — final Claude handoff audit

Audited branch `chatgpt/absolute-retarget-imports` at retained production head `4e34c043a04b81585aaae54e826b994cade0c6eb`. The tracked tree contains no temporary `.github` workflow, Python staging helper, scratch output or unfinished experiment file. Production diagnostic modules and their tests remain because they are validated Studio review controls. No Studio feature, character, deformation, grip or curl-motion code changed in this audit.

Refreshed `docs/BICEP_CURL_REVIEW_HANDOFF.md` with a **CLAUDE — START HERE TOMORROW** sequence, proven v5 asset identity, latest validation (287 passed + 1 optional skip across 36 files), retained controls, rejected experiments, exact elbow/grip comparison order and sign-off integrity requirements. Remaining visual work is explicitly limited to peak-flexion elbow surface/silhouette and hand/dumbbell grip/contact unless live review finds a genuine regression. Because this commit is documentation-only, validation was not rerun; it inherits the immediately preceding fully validated code state. Do not merge.

### ChatGPT — 2026-09-14 — align curl coaching wording with validated natural elbow drift

Updated the `elbow_drift` correction text from “pinned under the shoulders through the whole range” to “roughly under the shoulders; allow only a small natural drift near the top.” This is a wording-only change: the retained curl motion, technique thresholds and generated clip are unchanged. It removes a contradiction between the coaching copy and the validated 4° / ~21.55 mm late upper-arm/elbow contribution that is intentionally present to keep the curl lifelike rather than mechanically pinned.

The bicep-curl handoff was also refreshed to the deformation-aware approval checkpoint (287 passing tests + 1 optional skip across 36 files).

### ChatGPT — 2026-09-14 — bind visual sign-off to production deformation state

Closed an approval-integrity gap introduced by live export-aware character correctives. Visual sign-off previously matched only Studio document identity plus character source id, so changing a character-level elbow corrective after sign-off could leave the old approval looking current even though GLB export would now use a different deformation value.

Character state now carries a monotonic `deformationRevision`. Persistent corrective UI edits route through a revision-aware setter that increments only when the effective control value really changes; no-op/unknown writes do not advance it. Successful preserved/rebound imports and import mapping rebuilds also advance the revision because the stable `import` source id alone cannot distinguish different loaded character content. The temporary whole-rep corrective sweep still manipulates/restores the raw control directly, so a diagnostic scan that ends on the original value does not invalidate approval.

Visual sign-off records the current deformation revision and Review requires document identity + character source + deformation revision to match. Production approval is also suppressed and the sign-off button disabled while `Raw skinning` preview is active, because export always uses production correctives. Returning to Correctives on restores an otherwise-current sign-off only when no production value changed.

Regression coverage verifies revision changes only for effective control edits and that Studio sign-off records the character revision alongside its existing document-reference identity.

### ChatGPT — 2026-09-14 — fine grip closure and curl review frames

Grip review now has one-tap 65/70/75/80/85% fine closure presets in addition to the broader Loose/Training/Closed presets. Fine presets use the existing deterministic `setGripClosure` path and deliberately leave the playhead, wrist and equipment transform untouched, so thumb opposition, four-finger wrap and palm loading can be compared on the exact same pose.

Dumbbell Bicep Curl additionally exposes Bottom (0.00s), Mid lift (1.00s), Peak (2.00s), Mid lower (4.00s) and Return (5.00s) review buttons directly in the Grip workspace. This matches the retained review plan while keeping the authored 85% closure unchanged until a visual decision is made. No per-digit override, handle offset, wrist angle or exercise motion is changed automatically.

### ChatGPT — 2026-09-14 — same-frame corrective comparison presets

Added one-tap 0/25/50/75/100% presets to each character-level corrective tuning control. Unlike the existing strain-sweep review action, these presets change only corrective strength and deliberately leave the playhead untouched. This lets an author hold the curl on the exact same peak frame and tap through candidate strengths for a fair elbow-silhouette A/B before consulting strain metrics.

The existing whole-rep sweep remains separate and still restores the pre-scan value/pose; its `Review this value at worst P99` action can still move to each candidate's measured worst frame. No exercise pose, skin weights, authored default or automatic approval threshold is changed by the new presets.


### ChatGPT — 2026-09-14 — consolidated movement review summary

The Review workspace now brings the selected joint's existing movement diagnostics together beside the automated gates and human sign-off: maximum angular speed/acceleration, worst keyframe velocity discontinuity, resolved bilateral mirror mismatch, spatial joint drift and return error. Every measured problem point has a direct navigation action, and `Focus review joint` selects the joint and enters the close Focus camera.

For Dumbbell Bicep Curl, Review defaults to `forearm_l` when no joint is already selected, making the elbow review immediately useful without changing selection state until the author explicitly focuses it. Selecting another joint anywhere in the Studio takes over the Review summary. These movement signals remain descriptive navigation aids and do not silently add new automated approval thresholds.

Regression coverage now exercises the retained curl through the same summary ingredients and proves its forearm motion is finite, has an inspectable interior transition, remains bilaterally mirrored, moves the elbow through the small authored upper-arm contribution and returns the elbow to its starting relative position by the end of the rep.


### ChatGPT — 2026-09-14 — selected-joint spatial path diagnostics

Added a whole-rep spatial path diagnostic for the selected joint. It evaluates the canonical forward kinematics at the authored clip FPS, measures the selected bone head relative to its anatomical parent's head, and reports maximum 3D drift from the starting relative position, total relative path length, final return error and the exact worst timestamp. Root/world translation is removed by construction.

This is especially useful for the bicep-curl review: selecting `forearm_l` or `forearm_r` means the measured point is the elbow joint and the parent anchor is the upper-arm/shoulder joint. Pure elbow flexion therefore reads zero elbow drift, while upper-arm/shoulder contribution moves the elbow and becomes directly measurable in millimetres. The Joint workspace can jump straight to the maximum-drift frame. Values remain descriptive because many exercises intentionally translate joints.

Regression coverage proves a 90° forearm-flexion clip leaves the elbow point fixed, then adds a 10° upper-arm out-and-back path and verifies substantial measured drift, a midpoint worst frame, non-zero travelled path and essentially zero return error.


### ChatGPT — 2026-09-14 — resolved bilateral motion symmetry

Added a whole-rep bilateral motion diagnostic for paired joints. Rather than comparing raw left/right Euler values, it samples the final clip and mirrors each sampled pose through the canonical rig's existing `mirrorPose()` transform, which preserves flexion and flips the handed axial/abduction axes exactly as editor mirroring does. The actual opposite-side joint is then compared against that mirrored expectation using shortest-path angular deltas.

The Joint workspace now reports maximum and RMS mirror mismatch with the exact worst timestamp and a jump-to-frame action. This measures the resolved animation after timing/easing rather than merely checking that stored timing settings match. It remains descriptive because unilateral exercises may intentionally be asymmetric; for bilateral curls it provides a direct check that both arms actually follow the same mirrored path.

Regression coverage proves a synthetic forearm path containing flexion plus handed axial rotation reads essentially zero error when correctly mirrored, then detects an intentional 10° one-sided flexion change on the X axis at the final frame.


### ChatGPT — 2026-09-14 — selected-joint keyframe transition continuity

Extended selected-joint motion diagnostics with a phase-boundary continuity pass. For every interior keyframe, the Studio now samples one authored frame immediately before and after the boundary, computes shortest-path incoming/outgoing angular velocity per axis, and records the largest velocity jump. The Joint workspace shows the worst boundary, axis, timestamp and incoming/outgoing speeds with a direct jump-to-frame action.

This is intentionally descriptive rather than a universal pass/fail rule: a deliberate transition into a squeeze/hold can legitimately stop the joint. The purpose is to separate a keyframe/phase-boundary snap from a speed or acceleration peak occurring elsewhere in the movement, which is particularly useful when reviewing the curl elbow and late upper-arm contribution.

Regression coverage proves a 90°/s linear hinge stopping at a middle keyframe is localised as a 90°/s X-axis jump at exactly 0.5 s, while two adjacent linear segments with the same velocity report essentially zero boundary discontinuity.


### ChatGPT — 2026-09-14 — whole-rep corrective candidate sweep

Added an on-demand deformation-control sweep on top of the export-aware elbow tuning. The Correctives workspace can now evaluate 0/25/50/75/100% outer-elbow smoothing through the existing production whole-rep strain path and reports the worst P99 and maximum-edge strain frame for every candidate value. Each result can be loaded directly at its worst P99 frame for close visual inspection.

The sweep is deliberately diagnostic rather than an optimiser: it never chooses or permanently changes a corrective value. A `finally` restoration returns both the source-level control and the mounted character to the pre-scan playhead pose even if a scan fails. Raw-skinning mode disables the sweep because candidate-strength comparisons would otherwise all be suppressed. The default per-mesh edge budget is lower than a single full review to keep the five-point comparison interactive while preserving identical samples across candidates.

Regression coverage uses a low-FPS/low-edge-budget character scan, proves the requested values are all visited, confirms finite worst-frame results, and verifies the exact pre-scan source value is restored afterwards.


### ChatGPT — 2026-09-14 — export-aware outer-elbow corrective tuning

Split the imported elbow's optional directional outer-smoothing from the retained radial volume corrective when a retargeted character is built for interactive authoring. The radial `homeGymPT_elbow_*` target is unchanged; a separate `homeGymPT_elbow_outer_*` target contains the full measured directional candidate and keeps the existing 8 mm bind-space displacement cap. Its authoring value is bounded to 0–100%, so the editor can never amplify that candidate beyond the measured cap.

The retargeted character source owns one shared outer-smoothing tuning object for its lifetime. Viewport builds and fresh GLB export builds from that source therefore read the same value rather than keeping a viewport-only override. The Correctives workspace exposes the control with an authored-value reset, while Raw skinning remains a separate non-destructive A/B bypass. Exercise data, source vertices, source skin weights and the preserved skeleton remain untouched.

Regression coverage starts from a v5-style authored value of 0%, proves the tunable outer target is available without changing the retained radial path, verifies the live deformation influence responds to the control, verifies the export deformation sampler bakes the same influence, and proves out-of-range edits clamp to the safe 0–100% interval.


### ChatGPT — 2026-09-14 — explicit bilateral joint-timing symmetry

Added `copyJointTimingToOpposite()` to the Studio store. It uses the canonical anatomical mirror bone, copies the selected segment's explicit delay/finish/easing to the opposite side in one normal undoable document edit, and copies **timing only**—pose rotations and IK remain untouched. If the selected side has no explicit joint timing, copying clears the opposite override so both sides use the same phase-default timing. Centre-line bones are a no-op.

The Joint workspace now compares the selected joint's effective delay/finish/easing with its left/right counterpart and displays `Timing matched` or `Timing differs`, plus a `Copy selected timing to opposite side` action when needed. This closes a real authoring gap: pose mirroring alone never guaranteed bilateral motion timing. Regression coverage verifies a custom left upper-arm timing copies exactly to the right and undo restores the prior right-side timing, and verifies copying a default-timed left hand clears a stale right-hand override.



### ChatGPT — 2026-09-14 — parent/child joint coordination diagnostics

Added `src/editor/coordinationDiagnostics.ts` to measure selected-joint versus anatomical-parent sequencing inside the current keyframe segment. It samples the actual generated clip at authored FPS, measures 3-axis shortest-path excursion from the segment start, identifies the first meaningful motion (5% of excursion with a 0.1° floor), records 95% finish timing, and reports parent-onset lag. A joint moving less than 0.25° is treated as near-isometric rather than being assigned a fake onset. There is deliberately no universal good/bad lag threshold because sequencing depends on the exercise.

The Joint workspace now shows selected/parent excursion and onset, parent onset lag, a direct `Select parent to tune timing` action, and `Jump to parent onset`. For the bicep curl this means selecting the forearm makes elbow flexion versus upper-arm/shoulder contribution directly inspectable, while the existing Segment timing controls remain the one place that changes delay/finish/easing. Regression coverage proves a synthetic upper-arm support motion with a 50% authored delay begins materially after an immediately moving forearm, and proves a truly stationary parent is reported as near-isometric.



### ChatGPT — 2026-09-14 — whole-rep deformation worst-point review

Added `src/editor/strainReview.ts`, an on-demand authoring scan that poses the active character through every authored clip frame using the same `resolveFrame()` + `applyCharacterPose()` production path, measures the existing bind-vs-posed edge-strain diagnostic, and records worst P95/P99/max strain plus severe compression/stretch-count timestamps per mesh. The scan respects the current Correctives-on/Raw-skinning viewport mode and always restores the character to the pre-scan playhead pose in a `finally` block. Its per-frame edge budget is bounded so this remains an interactive locator, not a force or finite-element model.

The Correctives workspace now exposes `Scan full rep` and shows the mode that was scanned, worst P99/max values and timestamps, severe-count worst points, and jump-to-frame controls. This gives elbow/shoulder corrective review a direct route to the frame where surface deformation is objectively worst before comparing the silhouette. Regression coverage builds the real built-in character, runs a deliberately low-FPS/low-edge-budget scan for CI cost, and verifies finite bounded worst-frame results.



### ChatGPT — 2026-09-14 — selected-joint motion-quality diagnostics

Added `src/editor/motionDiagnostics.ts`, which samples the selected joint at the clip's authored FPS and measures per-axis angular speed and angular acceleration using shortest-path angle deltas. Crossing the ±180° representation boundary therefore cannot create a false 358° snap. The diagnostic reports the worst speed and acceleration with responsible axis/timestamp and deliberately has no universal pass/fail threshold: these are animation-quality signals, not force or injury estimates.

The Joint workspace now exposes the whole-rep maxima, per-axis values, and `Jump to fastest frame` / `Jump to sharpest change` controls. This pairs with the existing Focus-selected camera and per-joint segment timing so elbow snapping, shoulder take-over or abrupt secondary timing can be located first and then tuned without changing unrelated joints. Regression coverage proves a synthetic linear 90°/s hinge reads 90°/s with effectively zero acceleration and verifies shortest-path handling across +179°/-179°.



### ChatGPT — 2026-09-14 — whole-rep grip worst-point review

Added `src/editor/gripReview.ts` to scan every authored animation frame at `clip.fps` through the same production `resolveFrame()` pipeline used by the viewport. For each single-hand equipment instance it records the worst contact-reach value and exact timestamp for thumb/index/middle/ring/pinky, plus the overall worst digit. The scan reuses the established `measureGripFit()` envelope and is diagnostic only: it never edits finger closure, equipment placement, wrist/arm pose or the accepted clip.

The Grip workspace now shows one jump button per digit with its whole-rep worst percentage and timestamp. Selecting it moves the playhead directly to the measured frame so localized thumb/pinky problems can be inspected without blind scrubbing. Regression coverage proves both retained curl dumbbells are scanned, worst points lie on authored frame times, re-measuring each recorded timestamp reproduces the stored digit value, and the overall value equals the maximum digit worst case.



### ChatGPT — 2026-09-14 — per-digit grip reach diagnostics

Extended the existing geometric grip diagnostic so every contact point is tagged with its owning digit and `GripFitMeasurement` now reports `digitReachUse` for thumb/index/middle/ring/pinky alongside the established overall `reachUse`. Each digit value is the maximum distance-to-handle-centre-line divided by that contact point's existing allowed reach. Overall `reachUse` remains exactly the maximum of those five digit values, so the established envelope and Review gate semantics do not change.

The Grip workspace now lists live per-digit percentages below each single-hand handle fit. Values at or above 100% are visually flagged and the UI explicitly says this means the authored **geometric contact-reach envelope** has been exceeded; it is not presented as literal mesh penetration, force, or injury risk. This pairs directly with the new per-digit closure sliders: an author can see which digit is the outlier and trim only that digit instead of translating the whole dumbbell or changing unrelated fingers. Regression coverage proves all five digit metrics exist throughout the retained curl/shoulder-press reps, remain inside the current accepted envelope, and that global reach is exactly the maximum digit reach.


### ChatGPT — 2026-09-14 — per-digit deterministic grip closure

Added optional `HandSpec.digitClosure` overrides for `thumb`, `index`, `middle`, `ring` and `pinky`. Each value is an absolute 0..1 closure for that digit; unspecified digits continue to use the existing global `hands.closure`. `applyGrip()` now chooses the digit-specific value before applying the active equipment-aware grip profile, including the thumb opposition proxy. The field is absent by default, so the accepted 85% dumbbell curl remains numerically identical until an author explicitly trims a digit.

The Grip workspace now contains a collapsed `Fine-tune individual digits` section with five deterministic sliders and one-shot reset. `setGripDigitClosure()` and `clearGripDigitClosures()` regenerate through normal undo/redo history; setting a digit back to the global closure removes the redundant override rather than persisting noise. Regression coverage proves a pinky-only trim leaves index closure at the accepted baseline, thumb trim drives both thumb-base opposition and thumb wrap, and store edits/reset/undo behave correctly. This is the intended next tool for thumb/pinky intersection cleanup before considering any whole-dumbbell translation.


### ChatGPT — 2026-09-14 — two-hand equipment review gate

Extended the conservative Review workspace with a separate `Two-hand equipment fit` gate. Every `attachment.mode === 'hands'` instance is now measured at the same sampled production frames used for the rest of review. The gate uses `measureTwoHandFit()` and blocks Ready-for-visual-review when either left/right grip socket exceeds the existing 5 mm bilateral envelope. Failure detail reports worst socket error and worst absolute spacing mismatch; exercises with no two-hand equipment mark this gate not applicable and remain unaffected.

The grip review loop now resolves a single production frame when either supported dumbbell or two-hand checks are needed, avoiding a second solver pass for the same sample. Regression coverage appends a synthetic rigid barbell to the push-up only inside the test because its hand joints are world-locked throughout the rep. The synthetic bar deliberately uses the hand origins as its grip targets, avoiding normal in-palm offsets whose world position changes as the wrist rotates. Default 80 cm sockets correctly block automated approval; the test then measures the actual locked-hand separation, calibrates only the bar grip sockets with `withTwoHandGripWidth()`, regenerates, and proves the full review returns green. Earlier curl and in-palm fixtures were deliberately rejected because the new gate correctly detected their changing bilateral grip-point spacing. No accepted exercise definition or animation was changed.


### ChatGPT — 2026-09-14 — rigid two-hand socket calibration

Replaced the placeholder `hands` attachment (which merely drew equipment along the line between both hands) with a rigid socket-fit solver. Two-hand equipment now uses its actual authored `leftSocket`/`rightSocket` positions, maps their midpoint and axis onto the two hand-local grip targets, and never non-uniformly scales the item. Any difference between hand separation and socket separation remains a measurable symmetric residual rather than being hidden by wrist/elbow/shoulder compensation. Optional left/right grip offsets and a scalar `gripRoll` are now part of the two-hand attachment data.

Added `withTwoHandGripWidth()` for per-exercise contact-width authoring: it moves only the two grip socket positions symmetrically along their existing local axis and can reset those positions back to immutable library defaults without erasing unrelated socket-rotation overrides. The Grip workspace reports left/right socket error, hand separation and socket separation, and exposes undoable grip-width plus bar-roll controls. Preserved-source imported characters use the same `twoHandAttachmentMatrix()` from their live left/right hand matrices, so their preview no longer falls back to canonical two-hand placement.

Regression coverage uses a synthetic barbell rather than changing any accepted exercise definition. It proves the raw 80 cm barbell sockets expose their real spacing residual, calibrated socket width lands both contacts within numerical tolerance with a rigid determinant of 1, roll changes orientation without moving either grip contact, and arbitrary imported-character hand matrices use the same solver.


### ChatGPT — 2026-09-14 — hand-local grip orientation calibration

Extended one-hand equipment attachments with optional `gripRotation` Euler degrees. Production placement is now `hand frame × calibrated grip transform × inverse equipment socket transform`, so the equipment socket remains pinned to the exact same hand-local grip centre while the handle can rotate inside the palm. The full socket transform includes socket orientation as well as position, improving future non-zero-angle handles while preserving the current zero-rotation dumbbell baseline. The preserved-source-skeleton `EquipmentView` uses the same transform through the extended `handAttachmentMatrix`, so imported-character preview and export/runtime placement agree.

The Grip workspace now exposes exact X/Y/Z orientation degrees per one-hand equipment instance plus independent `Reset orientation`; centre calibration and orientation reset do not erase each other. `setEquipmentGripRotation` regenerates through normal document history and is undoable. Regressions verify a rotated dumbbell keeps its socket/grip centre exactly fixed in world space, undo restores the original document, and resetting orientation leaves a custom grip centre intact. This calibration changes equipment placement only; it never twists the wrist, elbow, shoulder or finger animation to compensate.


### ChatGPT — 2026-09-14 — equipment-aware deterministic grip profiles

Replaced the one-size-fits-all finger generator with explicit deterministic profiles for `dumbbell`, `bar`, `handle`, `rope`, `floor` and `none`. The **dumbbell profile exactly preserves the previous production values** (`[78,95,60]` finger flexion, `[-22,60,60]` thumb Z and -14° thumb-base X at closure 1), so the accepted bicep-curl hand shape does not silently change. Bar/pull-up, neutral handle and rope profiles now have distinct finger/distal-thumb closure values; thumb-base opposition stays at the canonical rig's real -14° limit rather than asking the joint for impossible extra travel; the floor profile is intentionally near-open, matching a planted palm rather than a cylindrical wrap.

`HandSpec.grip` remains the semantic equipment grip. A new optional `gripPreset` is only a generated hand-shape override, allowing authoring experiments without falsely changing exercise/equipment metadata. The Grip workspace exposes this as a profile selector and `setGripPreset` regenerates deterministically through normal undo/redo history. Regressions preserve the exact dumbbell baseline, prove bar/handle/rope generate distinct shapes, keep push-up fingers effectively open at its 5% closure, and verify the override is undoable while semantic grip remains unchanged.


### ChatGPT — 2026-09-14 — conservative review and approval workspace

Added a dedicated Review workspace that aggregates the checks the Studio can measure honestly before an exercise is considered ready for human sign-off. `src/editor/review.ts` runs the exercise technique validator, loop closure, unreachable IK scan, explicit lock/contact diagnostics across the clip and the established single-hand dumbbell grip envelope where applicable. Technique **errors** block; technique warnings are surfaced but do not masquerade as fatal errors. Contacts block on unresolved, limited, over-extended or >5 mm error samples. The grip gate is explicitly scoped to the cylindrical dumbbell case the existing geometry diagnostic supports; unsupported equipment is reported as not applicable rather than falsely certified.

Automated success now means only **READY FOR VISUAL REVIEW**. `APPROVED` requires a separate human visual sign-off for natural motion, silhouette, grip/contact appearance and equipment stability. That sign-off is transient and bound to both the exact `StudioDocument` object and active character source id, so any document edit or character swap invalidates it automatically; undoing exactly back to the reviewed document can restore it. Regression coverage proves the retained dumbbell curl clears the measurable gates, an impossible world-space arm lock blocks both contact/IK readiness, and visual sign-off follows exact document identity.


### ChatGPT — 2026-09-14 — live surface-strain diagnostics

Extended the Correctives workspace with an objective surface-deformation readout. `src/character/meshStrain.ts` samples posed `SkinnedMesh.getVertexPosition` edge lengths against the same edges in bind geometry, so normal rigid character/world movement cancels out while non-rigid skinning/morph distortion remains measurable. The panel refreshes at 5 Hz and reports P95, P99 and maximum absolute edge strain, counts of sampled edges compressed by >20% or stretched by >20%, and the sample count per mesh. The sampling budget is bounded per mesh so diagnostics do not require scanning every dense-mesh edge every rendered frame.

Regression coverage proves a rigidly moved one-bone mesh reports zero strain and a known relative morph stretch is detected at the expected 50% maximum. These values are diagnostic geometry signals, not injury/force estimates. They are intended to be read alongside the viewport-only Correctives on / Raw skinning A/B switch when deciding whether a joint corrective actually improves deformation rather than merely changing silhouette.


### ChatGPT — 2026-09-14 — corrective-deformation inspection workspace

Added a dedicated Correctives workspace for judging mesh-specific joint deformation without modifying the accepted animation. `src/character/correctiveDiagnostics.ts` discovers Studio-authored `homeGymPT_*` morphs on the active character and reports their live morph influence, affected vertex count, authored maximum displacement and current influence-scaled maximum displacement. Measurement respects the geometry's existing relative/absolute morph convention.

Added a viewport-only **Correctives on / Raw skinning** A/B switch. Normal `applyCharacterPose` and the character's deformation stack still run first; when Raw skinning is selected the viewport then zeros only `homeGymPT_*` influences. The Studio document, source geometry, deformation sampler and export path are not changed, and unrelated morphs such as facial expressions remain untouched. This provides a safe way to judge whether elbow/shoulder correctives genuinely improve the moving silhouette before promoting or tuning them. Regression coverage checks relative and absolute displacement measurement plus selective suppression.


### ChatGPT — 2026-09-14 — per-instance equipment socket authoring

Added direct socket-level authoring for **static equipment**. Equipment instances can now carry local `socketOverrides` without mutating `EQUIPMENT_LIBRARY`; `equipmentSocketForInstance` resolves the effective socket and the production attachment/contact resolver uses that effective value. Selecting a static socket in the Equipment workspace moves the existing Studio transform gizmo onto the socket. Translate/Rotate edits are converted back into equipment-local position/rotation, regenerate the deterministic clip, and participate in normal undo/redo history. Exact local position/rotation inputs and `Reset socket` are available alongside the gizmo.

The scope is deliberately guarded: hand- and two-hand-driven equipment reject socket authoring so handle placement continues to have one owner, the Grip/attachment workspace. This prevents competing edits between a moving hand socket and grip-centre calibration. Regressions verify that moving the pull-up rack's left grip socket changes the real production contact target, undo restores the original socket, reset removes the per-instance override, and a dumbbell socket edit creates no document/history change.


### ChatGPT — 2026-09-14 — static equipment transform authoring

Added a dedicated Equipment workspace for selecting exercise equipment, inspecting its declared sockets and authoring **static** world transforms. Static objects such as the pull-up rack can now be translated/rotated either through exact numeric controls (position in centimetres, rotation in degrees) or through the Studio's existing Translate / Rotate gizmo. `setEquipmentTransform` edits the exercise definition, regenerates the deterministic clip and participates in normal undo/redo history, so moving a rack also moves the equipment sockets that contact locks resolve against.

Hand- and two-hand-driven objects are deliberately protected: a world-transform edit is ignored without creating an undo step because their final transform belongs to the attachment/grip solver and would otherwise be overwritten on the next frame. The Equipment panel directs those cases back to the Grip workspace instead. Regressions verify a static rack transform reaches both the exercise definition and generated clip and is restored by undo, while a dumbbell hand attachment cannot be misleadingly world-transformed. The roadmap now records static equipment transform authoring as implemented; direct socket-selection/gizmo authoring remains a later refinement.


### ChatGPT — 2026-09-14 — live contact and reachability workspace

Added a dedicated Contacts tab that inspects floor, world and equipment locks at the current playhead using the **same `resolveFrame` production pipeline and analytical IK result used by the viewport**. Each lock now has a live target position, final hand/foot effector position, world-space error in millimetres, solver `reached` state and explicit physical over-extension state. Equipment locks also show the equipment/socket pair they resolve through. This is diagnostic-only: it does not add a second solver, hidden correction, safety score or movement change.

`src/constraints/contactDiagnostics.ts` is the pure inspection layer. Regression coverage verifies the bicep-curl floor contacts, pull-up rack socket contacts and a deliberately impossible world-space arm target; the impossible target must surface as `overextended` rather than being silently presented as a valid contact. Lock enable/disable remains the existing undoable clip edit. The Studio roadmap now records the contact-inspection foundation as implemented; equipment move/rotate authoring remains the next separate step.


### ChatGPT — 2026-09-14 — hand-local grip-centre calibration

Extended the Grip workspace with per-instance handle-centre calibration. Each hand-attached dumbbell now exposes X/Y/Z in hand-local millimetres. Editing writes `attachment.gripOffset` through the normal Studio document history, regenerates the deterministic clip, and therefore updates both the rendered equipment position and live grip-fit diagnostics immediately. `Reset anatomical centre` removes the override and returns to `anatomicalGripOffset(side)` rather than baking a duplicate default value.

The calibration is deliberately equipment-only: it does not change wrist, elbow, shoulder or finger animation automatically. This makes it suitable for fixing the visual case where a handle sits too deep/shallow in the hand without corrupting an accepted curl motion. Regressions verify custom offsets are undoable, actually drive the resolved dumbbell to the requested hand-local point, and reset back to the implicit anatomical default. The capability roadmap now records grip-centre calibration as implemented.


### ChatGPT — 2026-09-14 — measurable hand/grip workspace

Added a dedicated Grip tab for the curl/hand-authoring workflow. It keeps the existing deterministic finger generator and existing 30-joint fine-hand editing rather than introducing a second hand rig. The panel exposes an exact closure slider plus Loose 70%, Training 85%, and Closed 100% quick presets; all use the existing `setGripClosure` document edit, regenerate deterministically and remain undoable.

Added `src/equipment/gripDiagnostics.ts`, which measures each hand-held cylindrical handle against the same geometric concepts already enforced by the grip regression: maximum finger/thumb reach use and angular enclosure around the handle. The UI reports contact reach used, wrap coverage, largest open gap, and an explicit `Within envelope` / `Review fit` authoring status. This is intentionally described as animation-fit geometry, not a force or injury-safety score. New regressions confirm the preset set includes the curl's authored 85% default and that both the dumbbell curl and shoulder press remain inside the measurable envelope across 13 samples per repetition. The capability roadmap now records the Grip workspace as implemented.


### ChatGPT — 2026-09-14 — non-destructive A/B pose comparison

Added transient Reference A / Candidate B pose snapshots to the Studio. `comparison` state lives outside `StudioDocument`, so capturing, clearing and viewing snapshots do **not** mutate the accepted clip, do not create undo-history entries and do not affect export. The new Compare panel renders both snapshots side by side as deterministic front-view projections of the canonical core skeleton and, when a joint is selected, shows exact X/Y/Z angles for A and B plus the signed delta. This is intended for judging shoulder/elbow/body-position refinements before deciding whether a clip edit should be kept.

`src/editor/comparison.ts` owns the pure front-view projection helper, with tests keeping all projected endpoints inside the normalised viewport and confirming that the curl peak visibly differs from the start at the forearm. Store regressions verify A/B capture leaves the document/history untouched and that loading another exercise clears stale snapshots. The capability roadmap now records non-destructive A/B pose comparison as implemented.


### ChatGPT — 2026-09-14 — semantic pose-marker authoring

Added semantic pose landmarks directly to `Keyframe` as `marker?: 'start' | 'transition' | 'peak' | 'return'`. Generated exercise clips now classify their deterministic boundaries as Start, first arrival at Peak, intermediate Transition boundaries, and final Return. Markers are metadata only: they do not change pose interpolation, IK, joint timing, contacts, equipment or export motion. The Timeline renders the landmarks as labelled keyframes and exposes an editable Marker selector for the keyframe under the playhead. Marker edits use the existing document history, so undo/redo works normally and clearing a marker leaves the underlying pose untouched.

The bicep-curl template now generates `[start, peak, transition, transition, return]` across its existing five keyframes. Regression coverage checks deterministic marker generation, undoable marker editing and marker clearing without pose mutation. The Studio capability roadmap now records pose markers as implemented.


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
