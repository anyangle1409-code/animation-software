# Stage 2 — locked

Executing Decision 3 of `docs/REFERENCE_BODY_PHASE2_AUTHORIZATION.md`. The
corrected bind/retarget fix and every already-validated Stage 2 value are
unchanged. Nothing promoted or merged.

| file | SHA-256 |
|---|---|
| `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb` | `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0` |

The candidate is byte-identical to the one the bind fix produced: the bridge is a
containment change only and touches no asset.

## First, a correction to the recorded residual

The decision was written against a residual of 7.84 mm for the pectoralis and
7.34 mm for the latissimus, and expected "under 1 mm beyond the existing
allowance". That understated it. `muscles.test` asserts inside its loop, so it
throws on the *first* failing muscle and never reaches the rest — 7.84 mm was
simply the first failure encountered, not the worst.

Surveying every muscle over every exercise instead:

| | before the widening | with Stage 2, before the bridge |
|---|---|---|
| latissimus | under 4 mm | **19.93 mm**, in the pull-up |
| pectoralis | 4.43 mm | **9.86 mm**, in the press |
| erector_mid | 5.71 mm | 5.71 mm (unchanged, inside) |

So the gap to close was about 16 mm, not 1 mm. The diagnosis in the decision
still holds exactly — it is a local coverage gap, both sides symmetric, opened
by the arm moving 33.7 mm outboard while the chest correctly stayed put — but
the bridge had to be sized for the real figure.

Also reverted: two muscle-origin nudges from the previous round (pectoralis
−0.045 → −0.065, latissimus −0.055 → −0.07). Measured against the survey they
were net-neutral — the pectoral improved by 0.22 mm and the latissimus worsened
by 2.23 mm — so the authored values are restored and the bridge does the work.

## The bridge

It lives in `src/body/containment.ts` and **only** there. `BODY_CHAINS` feeds
`buildProfileBodyGeometry`, which `character/builtin.ts` renders, so putting the
bridge in the profile table would have widened the visible chest. These sections
are consumed exclusively by `buildSections`, so they change where a belly is
allowed to be and nothing about what is drawn.

Three rings on each clavicle, over the outer half of the bone, offset to sit
over the measured points rather than enlarged concentrically:

| t | rx | rz | ox | oz |
|---|---|---|---|---|
| 0.50 | 30 | 30 | ∓26 | +4 |
| 0.80 | 50 | 46 | ∓50 | +6 |
| 1.00 | 55 | 52 | ∓60 | −6 |

Millimetres. Sized from measurement, not guessed: the pectoral's worst point sat
at clavicle-local t 0.800, x −34.7, z +26.2 mm, and the latissimus's at t 0.950,
x −82.8, z −23.8 — the latter 85 mm posterior to the upper arm's axis, which is
why the far ring carries front-to-back depth as well as outboard offset.
`sectionAt` caps the tube beyond the end rings, so the medial chest is untouched.

One thing worth recording: the two clavicle frames are **not** reflections of one
another for this purpose. The same negative `ox` on both fixed the left side and
left the right completely unchanged, so the offset is flipped explicitly per
side. Both sides now read identical figures.

## Result

| muscle | before bridge | after | allowance |
|---|---|---|---|
| latissimus (both) | 19.93 mm | **under 4 mm** | 7 mm |
| pectoralis (both) | 9.86 mm | **4.14 mm** | 7 mm |
| erector_mid (both) | 5.71 mm | 5.71 mm | 7 mm |

The pectoralis now sits *better* than its 4.43 mm pre-widening baseline, so this
is margin rather than a fragile pass. No belly was scaled, no chest or ribcage
widened, no waist touched, no deltoid mass added, and the 7 mm threshold is
untouched.

## Stage 2 lock conditions

| condition | result |
|---|---|
| pectoralis and latissimus inside the existing limit | met — 4.14 mm and under 4 mm against 7 mm |
| all four exercises validate cleanly | met — curl, press, push-up, pull-up all report no violations |
| matched character/rig bind equivalence intact | met — bones off the arm move 0.0000 mm; achieved bone placement exact to 6.8e-13 mm; import height and scale identical to Stage 1 |
| shoulder span and silhouette unchanged from the accepted result | met — the bridge touches no asset and no rendered surface; span stays at Δ −0.29% of figure height |
| Phase 1 grip and contact preserved | met — fingers −0.46 / −0.36 / −0.22 / −0.11 mm with zero inside, thumb +1.18, palm −2.54, wrap 252°, identical to the locked values; renderer vs exporter 0.0000 mm |
| Phase 1 curl mechanics preserved | met — Bottom/Return dumbbell-to-thigh **+4.68 / +4.79 mm**, zero inside, better than Phase 1's +1.81 / +1.90 |
| typecheck and build | met — both clean |
| full suite | met — **298 passed, 1 skipped, 0 failed** |
| no new structural regression | met |

**Stage 2 is locked.** Continuing to Phases 3–5.
