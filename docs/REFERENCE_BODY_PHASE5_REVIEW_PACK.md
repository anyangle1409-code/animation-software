# Reference body — final review pack

**Branch:** `chatgpt/absolute-retarget-imports` (mirrored to `claude/home-gym-pt-animation-txux66`)
**Nothing promoted. Nothing merged.**

This closes Phase 5 of `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`. Stage 1 was frozen on
entry; Stage 2, Phase 3 and Phase 4 are locked, and Phases 1–5 are complete.

The two items this pack originally carried forward as unresolved have since been accepted by
`docs/REFERENCE_BODY_FINAL_ACCEPTANCE_DECISION.md`, and the section below has been updated to
record that. Nothing has been promoted and nothing has been merged; promotion remains a
separate, explicit decision.

## Candidate assets

The assets are gitignored, so the hashes are the only record that travels with the branch.

| Role | File | SHA-256 |
|---|---|---|
| Final candidate body | `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb` | `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0` |
| Final dressed candidate | `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE_SHORTS.glb` | `841b01d6abb5649af8929f6b147b6aafbf95da4ecf13c2ea09f7f3e570306d72` |

The dressed candidate was rebuilt from the retained body with
`node scratchpad/reference-fit/dress.mjs`. Closest body-to-garment approach moved from
**0.67 mm** on the previous v7 pass to **1.97 mm** here — more clearance, and no
interpenetration anywhere.

`HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`) is retained only as the
frozen Stage 1 input the Stage 2 work was derived from. It is not a deliverable.

## Retained changes

### Phase 1 — reusable cylindrical power grip

- `src/character/solvedGrip.ts` (new) — character-scoped solved grip, keyed by
  `gripSolutionId` × grip family, with per-digit joint rows, a thumb opposition angle, the
  handle radius and a handle-centre offset. It is deliberately **not** in `GRIP_PROFILES`:
  those profiles are authored against the canonical rig, which has its own reach test, and
  putting solved angles there broke four canonical tests.
- `src/character/solvedGrip.test.ts` (new) — five guards, including that every solved angle
  lies inside the rig's joint limits (the substitution does not re-run `clampPose`) and that
  an unsolved family returns `null` rather than a fallback.
- `src/character/pose.ts` — `withSolvedGrip`, which returns a module-scratch pose and never
  mutates the shared one.
- `src/character/retargetSource.ts` — applies the solved handle centre inside `gripOffset`, so
  the renderer, the exporter and every diagnostic read one centre.
- `src/exercises/definitions/bicepCurl.ts` — the neutral rebase to 4.55° with a matching 8.55°
  peak, which is what funded the −9 mm handle move.

Retained result: zero digit penetration, palm loaded, 252° wrap, thigh clearance +4.68/+4.79 mm.

### Phase 2 — Stage 2 shoulder widening

- `src/rig/humanoid.ts` — `SHOULDER_WIDENING = 0.01924 * 1.75`, applied to the clavicle tail and
  to every arm-chain bone head and tail.
- `src/body/anatomical.ts` — `widenShoulders`, a graph-distance ramp at `HOPS = 2`. The shift is
  33.7 mm against a 7 mm median edge, so any mask that turns over inside one edge inverts the
  mesh; HOPS = 2 measures **better than unshifted** (worst 5.215 vs 5.308, tightest 0.1580 vs
  0.1324).
- `src/muscles/model.ts` — deltoid origins follow the clavicle; pec and lat insertions moved to
  4 mm lateral of the humerus shaft. Origins are the authored values.
- Contact rules re-derived only where they are genuinely shoulder-relative:
  `pushUp.ts`, `pullUp.ts`, `shoulderPress.ts`, `equipment/library.ts`, `body/body.test.ts`.

The bind/rest representation was repaired before any of this was trusted: translating
`DEF-upper_arm.*` moved the clavicle's tail, which defines `targetFrame`, while its stored
`restWorld` orientation stayed, so the correction absorbed ~13° and the arm landed 281 mm low.
The clavicle is now re-aimed by exactly the angle its tail moved (10.147°, head held).
Equivalence proven: off-arm bones 0.0000 mm, grip identical to the digit.

### Stage 2 containment — Decision 3

- `src/body/containment.ts` — three rings per clavicle, appended after `BODY_CHAINS` in
  `buildSections`. Containment-only by construction: `BODY_CHAINS` also feeds a rendered
  surface, so the bridge cannot live there. The clavicle frames are not reflections for this
  purpose, so the offset is flipped explicitly per side.

Nothing was widened, scaled or inflated and the 7 mm threshold is untouched, as required.
Latissimus went from 19.93 mm outside to under 4 mm; pectoralis 9.86 → 4.14 mm, better than its
pre-widening baseline.

### Phase 4 — forearm twist distribution

- `src/retargeting/retarget.ts` — `TwistHelper` / `FOREARM_TWIST_SHARE = 0.5`. `bindRetarget`
  recognises a deform twist helper; `applyRetarget` decomposes the relative rotation between the
  helper's driven parent and child and applies only the long-axis component, scaled by the
  share. The hand is driven afterwards against its updated parent, so its orientation is
  untouched.
- `src/exercises/definitions/pushUp.ts` — retained floor contact `z = 1.295`.

Only the forearm helper is wired. The upper arm shows the same copy-parent pattern, but nothing
measured requires changing it, so it was left alone per the written scope.

### Plumbing

`src/character/types.ts`, `src/animation/clip.ts`, `src/animation/generate.ts`,
`src/editor/strainReview.ts`, `src/viewer/CharacterFigure.tsx` — carry the grip context from the
exercise definition through to the pose. `StudioClip.hands` is optional so hand-authored test
clips still typecheck.

## Validation on the retained candidate

- **Typecheck** — clean.
- **Build** — clean (`built in 5.69s`).
- **Full suite** — **298 passed, 1 skipped, 0 failed.** This is the final validated code
  state. Documentation-only updates after it, including this one, did not re-run it.
- **Tracked tree** — clean at the Phase 5 commit.

Cross-exercise regression on the shared retarget change, all eleven required poses:

| Check | Result |
|---|---|
| Technique rules, four rule sets | clean |
| Curl / press grip vs locked Phase 1 | identical (fingers −0.46/−0.36/−0.22/−0.11 mm, thumb +1.18, palm −2.54, wrap 252°) |
| Curl thigh clearance | +4.68 / +4.79 mm, unchanged |
| Renderer vs exporter | 0.0000 mm |
| Body containment | inside 7 mm at all 11 poses; push-up Top improved 3.77 → 3.48 mm |
| Bilateral symmetry | identical |
| Skin weights / topology | untouched |

Push-up forearm twist at Bottom, across the authorised sweep:

| Helper share | Helper twist | Hand |
|---:|---:|---:|
| 0 (before) | 9.1° | 57.7° |
| 0.25 | 15.0° | 57.7° |
| **0.50 (retained)** | **21.0°** | **57.7°** |
| 0.75 | 26.9° | 57.7° |

The hand does not move at any fraction, which is the constraint that mattered. Measured girth
bins along the forearm's own axis: bind `55.2/56.7/50.3/43.3/33.5` mm against posed Bottom
`58.7/51.7/48.6/41.5/37.4/32.9` mm over 177 forearm vertices.

## Both carried-forward items — now accepted

Resolved by `docs/REFERENCE_BODY_FINAL_ACCEPTANCE_DECISION.md`. Neither is an open defect.

**1. Push-up wrist — accepted by rest-relative rotation (≈66.6°).** The acceptance criterion for
this character is wrist extension measured **against the character's own neutral hand-to-forearm
rest orientation**, not the raw forearm/hand world-axis angle. The asset carries a built-in
**14.62°** hand-to-forearm rest offset that a raw axis-angle target does not account for, so the
earlier 70–75° band stands as a diagnostic band rather than a criterion.

At the retained `z = 1.295` the raw axis angle is **81.18°**, which is **≈66.6° of actual
extension from rest** — anatomically plausible, palm planted, bilateral, and clean against every
authored push-up rule. The geometry also shows why the raw band could not be met: it needs the
hands near `z = 1.34`, while `z = 1.30` already exceeds the `forearm_vertical` rule's 60 mm
elbow-to-wrist `dz` cap. With a flat planted palm, extension *is* the forearm's angle from the
floor, so the raw target and the near-vertical-forearm requirement are geometrically
incompatible; the rest-relative reading is the correct measurement, not a concession.

Explicitly not done, per the decision: the hands were not moved forward to make the raw number
read 70–75°, `forearm_vertical` was not weakened, and weights, Stage 1 geometry, Stage 2
proportions and the retained 0.50 forearm twist-helper share are untouched.

**2. `strainReview` timeout — non-blocking historical evidence.** It intermittently exceeded the
5 s vitest timeout under full-suite load while passing in isolation. It did **not** reproduce on
the final validated run (298 / 1 / 0), so it is environmental and flaky rather than a product
defect, and it does not block acceptance. The code under test was not changed for it. If it
returns consistently under full-suite load while still passing in isolation, the permitted
response is a targeted per-test timeout adjustment, after confirming the test's own result is
unchanged.

## Corrections to my own earlier reporting

Recorded because the decision documents were written partly on the strength of these claims.

- I described the push-up forearm as a "flattened, faceted strap" from my own renders and the
  twist work was authorised on that basis. Measured girth does not support it: the posed forearm
  holds its bind girth within a few millimetres and the distal bins *grow*. There was no pinch or
  collapse — the look came from my render's flat shading and camera. The twist defect was real
  and is fixed on its own merits, but it was not repairing a collapse.
- I reported the push-up wrist at 43–51° by measuring canonical-rig bone axes. The character's
  decomposed wrist, accounting for the 14.62° bind offset, is 92.10° at the original placement.
- The first containment residual I reported understated the gap, because `muscles.test` asserts
  inside its loop and throws on the first failure. Surveying every muscle over every exercise
  found latissimus 19.93 mm, not 7.84 mm.
- A strain column in one harness read exactly 1.000 everywhere. three.js skins on the GPU, so
  `mesh.geometry` never moves; the column was removed and strain stays with `shoulder.test` and
  `strainReview`, which do CPU skinning.

## Diagnostics

`scratchpad/repair/` is gitignored and now holds 47 files, down from 34 MB of accumulated render
and text output to 436 KB. Retained are the harnesses on the permanent validation path:
`gripmetric`, `gripsolver`, `gripagree`, `gripview`, `overlap`, `phase2rules`, `phase3`,
`stage2_equivalence`, `p4view`, `p4twist`, `p4girth`, `technique`, `wrist4`, `measure`,
`contactdiag`, `flexsweep`, `clothing`, `waistband`, plus the `png.mjs` writer and the render
drivers they share. Removed as superseded: the `wrist`/`wrist2`/`wrist3` iterations,
`griptune` and `gripframe` (both superseded by `gripsolver`), and every stale `.txt`/`.png`
output. No retained harness imported a removed one.

## Status

Phases 1–5 are complete and locked on this branch. Both carried-forward items are accepted: the
push-up wrist on rest-relative rotation (≈66.6°), and the `strainReview` timeout as non-blocking
historical evidence. No executable code or asset changed during the acceptance close-out, and
both candidate hashes were re-verified as matching.

The branch is ready for a promotion decision. Nothing has been promoted and nothing has been
merged — replacing bundled assets, promoting, and merging each remain a separate explicit user
decision.
