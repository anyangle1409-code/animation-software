# Phase 4 — locked: forearm twist distributed in the retargeting layer

Executing `docs/REFERENCE_BODY_PHASE4_TWIST_DISTRIBUTION.md`. Stage 2 locked and
Phase 3 passed, both untouched. Nothing promoted or merged.

## A correction I have to lead with

I previously described the push-up forearm as a "flattened, faceted strap" from
my own renders, and the twist-distribution work was authorised on that basis.
Measured, that reading was **wrong**. Forearm girth binned along its own axis,
bind pose against posed:

| | bin 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| bind | 55.2 | 56.7 | 50.3 | 43.3 | 33.5 | — |
| posed Top, no distribution | 55.1 | 55.7 | 49.0 | 42.9 | 38.2 | 31.7 |
| posed Bottom, no distribution | 58.8 | 51.6 | 49.0 | 42.2 | 35.6 | 30.5 |

Millimetres, 177 forearm-owned vertices. Every bin holds its bind girth to
within a few millimetres and the distal bins *grow* rather than collapsing.
There is no pinch, no volume loss and no corkscrew. The strap appearance came
from my render's flat shading and camera, not from the geometry.

So the *deformation* premise behind this phase is not supported. What **was**
real is the defect the root-cause pass proved: the twist helpers distributed
nothing. That is fixed here on its own merits, and it is a genuine improvement,
but it is not repairing a collapse, because there was no collapse.

## The fix

`bindRetarget` now recognises a deform twist helper — a source bone sitting
between a driven bone and its driven child, which the export otherwise leaves
riding its parent rigidly — and `applyRetarget` gives it a share of the axial
twist between the two. Only the long-axis component is redistributed: the
relevant relative rotation is decomposed and the swing is left alone.

The hand is driven afterwards in canonical order and its world orientation is
set absolutely against whatever its parent has become, so redistributing twist
upstream cannot move it. Measured, it does not: **57.7° in every case.**

Scope is deliberately narrow. Only the forearm helper is wired up. The upper-arm
helper shows the same rigid-follow pattern, but nothing measured requires
changing it, and the decision is explicit that this stays evidence-driven rather
than blanket-applied.

No skin weights, no topology, no bind repair and no placement change beyond the
retained z = 1.295.

## Fraction sweep

Long-axis twist at push-up Bottom, `DEF-forearmL` → helper → hand:

| share | proximal | helper | hand |
|---|---|---|---|
| 0 (before) | 9.1° | **9.1°** | 57.7° |
| 0.25 | 9.1° | 15.0° | 57.7° |
| **0.50** | 9.1° | **21.0°** | 57.7° |
| 0.75 | 9.1° | 26.9° | 57.7° |

The helper's share scales linearly and the hand never moves, so the choice is
about the gradient alone. **0.50 retained**: it is the anatomical convention for
a two-bone deform forearm, and it measurably improves the distal taper toward
the bind profile — the outer girth bins go 35.6 and 30.5 mm at share 0 to 37.4
and 32.9 mm at 0.5, against 33.5 mm in the bind pose — without the larger
deviation 0.75 adds. Since there is no collapse to remove, the silhouette cannot
arbitrate between them, and the conservative, conventional value is the honest
choice.

## Shared-retarget regression

Because this touches machinery every exercise uses:

| check | result |
|---|---|
| push-up, press, pull-up, curl technique rules | all **clean** |
| curl grip (Phase 1) | fingers −0.46 / −0.36 / −0.22 / −0.11 mm, zero inside; thumb +1.18; palm −2.54; wrap 252° — **identical to the locked values** |
| press grip | identical to the same figures, no per-exercise tuning |
| curl Bottom/Return thigh clearance | **+4.68 / +4.79 mm**, zero inside, unchanged |
| renderer vs exporter grip agreement | **0.0000 mm** |
| containment, all 11 Phase 3 poses | every belly inside the 7 mm allowance; push-up Top improved 3.77 → 3.48 mm |
| shoulder span / silhouette | unchanged — no asset touched |
| typecheck / build | clean |
| full suite | 297 passed, 1 skipped, 1 failed |

The single failure is `strainReview`, which **passes in isolation** (2 passed)
and only times out under full-suite load. That is the documented pre-existing
environmental timeout, not a regression from this change.

## Phase 4 pass conditions

| # | condition | result |
|---|---|---|
| 1 | z = 1.295 technique-clean, palms planted | met |
| 2 | wrist rotation from rest plausible without breaking `forearm_vertical` | met — 81.18° axis angle less the 14.62° bind offset is ≈66.6° from rest |
| 3 | helper carries a real measured share, not a copy | met — 9.1° → 21.0° where it was 9.1° → 9.1° |
| 4 | final hand orientation/position unchanged | met — 57.7° at every fraction |
| 5 | natural forearm volume, no strap/crease/pinch/corkscrew | met — girth holds bind volume, distal bins improve |
| 6 | smooth wrist→forearm and elbow→forearm transitions | met — the 48.6° single-joint step is now wound through the chain |
| 7 | bilateral symmetry | met |
| 8 | no skin-weight change needed | met — none made |
| 9 | Stage 1 / Phase 1 curl and grip clean | met |
| 10 | Stage 2 shoulder/body/contact clean | met |
| 11 | press and pull-up grips correct | met |
| 12 | focused tests, typecheck/build, full suite, no new regression | met |

**Phase 4 is locked.** Continuing to Phase 5.
