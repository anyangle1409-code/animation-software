# Stage 1 — forearm proportion correction

Stage 1 of `docs/REFERENCE_BODY_TWO_STAGE_DECISION.md`. **Nothing promoted,
nothing merged, Stage 2 not started** — the shoulder chain is untouched.

| File | SHA-256 |
|---|---|
| `HomeGymPT_Male_FOREARM_CANDIDATE.glb` | `f48d48e54553faa972683ce539b54d3b16ae58d1eda8e98b55d1a1725a35ebe9` |
| `HomeGymPT_Male_FOREARM_CANDIDATE_SHORTS.glb` | `2d1434e8c42eaf3b3b18e2d8cb9ab0a91b542786be13fbee6ecbae9cac870901` |

Built on `HomeGymPT_Male_REFMATCH_CANDIDATE.glb` (`19f350ad…52f4c`), which is
unchanged, as are v7, v6 and proven v5.

## Skeletal and bind changes retained

The forearm is lengthened along its own axis to the canonical rig's proportion:
**10.93% → 14.86% of figure height, +79.2 mm model-space, +68.7 mm
studio-space**, identically on both sides. Upper arm and shoulder chain
untouched.

| Bone | change |
|---|---|
| `DEF-forearm.L/R` | none — its origin is the elbow |
| `DEF-forearm.L/R.001` | moved distally by 39.6 mm; the twist helper sits at 50.0% along, so moving it by its own share stretches the forearm uniformly instead of putting all the new length in the distal half |
| `DEF-hand.L/R` and all 20 palm/finger descendants each side | moved distally by the full 79.2 mm |

Local node matrices were rewritten parent-first from the new world transforms.
The node graph and the stored inverse binds were first checked to agree (worst
component 1.29e-5) — if the file's rest pose and its bind pose disagreed,
"move the bone" would mean two different things.

**Inverse binds: 42 of 160 joints rewritten** — exactly the moved chain
(forearm twist helper, hand, four fingers × 3, thumb × 3, four palms, per side).
The first attempt recomputed all 160 from the node graph, which silently
rewrote every untouched bone by that same 1.29e-5; that is invisible but it is
not "the forearm chain only", so it was restricted.

**Skin weights unchanged.** `JOINTS_0`, `WEIGHTS_0`, `TEXCOORD_0`, `COLOR_0`
and all 19304 triangles are bit-identical; bone names and joint count identical.
Only `POSITION`, `NORMAL`, the arm-chain node matrices and those 42 inverse
binds differ.

**Surface**: 2038 vertices moved, worst 79.2 mm. A uniform stretch between elbow
and wrist, rigid beyond the wrist, masked by each vertex's weight on that side's
forearm-and-hand chain so the elbow blends and nothing outside the arm can move.
Worst left/right difference across 4178 mirrored pairs: **0.001 mm**.

## Contact deltas

From the real-character diagnostic, hand world positions, refmatch → Stage 1:

| Exercise | hand movement | reading |
|---|---|---|
| Push-up | 0.0 – 8.8 mm | floor contact holds: the hand stays at y ≈ 0.026, z = 1.240 |
| Pull-up | 0.0 – 1.2 mm | bar contact holds: the hand stays at y ≈ 1.970 |
| Curl | 68.7 mm | free hand, moves the full arm extension |
| Shoulder press | 68.7 mm | free hand; rack and lockout both rise |
| Squat | 68.6 – 68.7 mm | free hand |

**Contacts re-derived themselves from their own rules — nothing was nudged.**
That is the significant result here: the locked contacts stayed locked while the
free ones moved by exactly the bone extension. Bilateral mirror error is
0.000 mm in every exercise at every sampled frame.

Shoulder press specifics: rack rises 1.587 → 1.654 m, overhead lockout
1.964 → 2.032 m, and the hands sit 8–18 mm wider.

## Updated push-up true wrist angles

| | refmatch | Stage 1 |
|---|---|---|
| push-up peak extension | 102.66° | **95.45°** |
| push-up deviation | 3.93° | −3.77° |
| pull-up peak angulation | 52.98° | 48.52° |
| curl peak angulation | 13.75° | 13.75° (unchanged) |
| press peak angulation | 11.01° | 11.01° (unchanged) |

Decomposition residual 0.0000° and left/right mismatch ≤0.0001° throughout.

**The skeletal correction is not the push-up solution.** It improves the true
wrist extension by 7.2°, but 95° is still past a plausible wrist, so the
documented hand-placement issue remains open and is still an exercise-definition
question. The handoff asked for this to be re-measured rather than assumed, and
the measurement says it is better, not fixed.

That curl and press are bit-identical is the check that the accepted motion was
not rewritten to accommodate the new proportions.

## Updated curl dumbbell/thigh overlap

Closest approach, negative meaning the weight is inside the leg:

| | curl bottom (L / R) | mid-lower (L / R) |
|---|---|---|
| v7 | −5.86 / −5.81 mm | −15.26 / −15.30 mm |
| refmatch | −6.65 / −6.60 mm | −15.58 / −15.59 mm |
| **Stage 1** | **−13.85 / −13.99 mm** | **−4.82 / −4.68 mm** |

**This is the one regression.** At the bottom of the rep the overlap roughly
doubles, because the longer forearm hangs the dumbbell 69 mm further down the
thigh where the leg is no narrower and the plate meets it squarely. Across the
sampled frames the *worst* overlap actually improves slightly, 15.59 → 13.99 mm,
because the mid-lower frame improves by 10.8 mm — but the bottom frame is worse
than before and worse than v7.

It is a contact/equipment calibration problem, not a motion problem, and per the
guardrails it should be solved by re-deriving the dumbbell's placement rule
rather than by nudging the weight or editing the curl. **It should be resolved
before Stage 2**, so that a later shoulder change is not diagnosed against a
known-bad contact.

A note on how this was measured, because the first two readings were wrong.
`GLTFLoader` sanitises `DEF-hand.L` to `DEF-handL`, so the pattern excluding the
holding arm matched nothing, and "closest approach" came back as the grip itself
— identical to 0.01 mm for three different bodies, which is what gave it away.
With the pattern fixed and the real part geometry from `src/equipment/geometry.ts`
(a 15 mm bar of length 120 mm and two 48 mm rubber discs 35 mm thick, centred
75 mm out) rather than the bounding box, the harness reproduces the documented
v7 figure exactly: −5.86 mm left, −5.81 mm right, three thigh vertices inside.

## Hand/wrist deformation against v7

The v5 → v6 handover repair sits exactly in the stretched region, so it was the
most likely regression. Ring measurement through the production path, same
pinned ring set, 1440 ring triangles in all three:

| | max aspect | p99 aspect |
|---|---|---|
| v7 | 27.756173 | 5.870750 |
| refmatch | 27.756173 | 5.870750 |
| Stage 1 | 27.756327 | 5.870763 |

Worst offenders are the same rings (`wrist.L`/`wrist.R`, aspect 6.082, bind
aspect 1.795) at the same values. **The repair does not regress** — the change
is 1.5e-4 in the maximum.

## Strain and diagnostic

Worst per exercise, refmatch → Stage 1:

| Exercise | P95 | P99 | max | over 3× |
|---|---|---|---|---|
| Squat | 1.2377 → 1.2363 | 1.6251 → 1.6251 | 3.0871 → 3.0871 | 4 → 4 |
| Curl | 1.2105 → 1.2094 | 1.4855 → 1.4806 | 2.2226 → 2.2226 | 0 → 0 |
| Press | 1.2393 → 1.2387 | 1.6777 → 1.6777 | 3.2538 → 3.2538 | 10 → 10 |
| Push-up | 1.2364 → 1.2293 | 1.6626 → 1.6399 | 2.4771 → 2.5105 | 0 → 0 |
| Pull-up | 1.3271 → 1.3134 | 1.9305 → 1.9295 | 4.2862 → 4.2846 | 126 → **112** |

Every P95 and P99 improves or holds. The only increase anywhere is push-up
maximum stretch, +0.033, on a frame that has no over-3× vertices at all. No
threshold was altered.

## Garment

The moved vertices are all arm-weighted and sit laterally far outside the hips,
so the shorts are unaffected: the closest body-to-garment approach is 1.97 mm,
exactly as for the refmatch candidate. The deepest squat was re-run and the
body/garment path did not regress.

## Build gate

Typecheck clean, `vite build` clean, suite **292 passed / 1 skipped / 1 failed**
— the pre-existing `strainReview` 5-second timeout, unchanged and environmental.

## Would anything block Stage 2?

One item: **the curl-bottom dumbbell/thigh overlap.** It is not a deformation or
rig fault and it does not threaten the forearm correction itself, but it should
be re-derived before the shoulder widening, because Stage 2 moves the hands
again and a known-bad contact would confound attributing whatever changes next.

Nothing else. Weights, topology and the hand/wrist repair are intact; contacts
re-derive on their own; strain is flat or better; the accepted curl and press are
bit-identical.
