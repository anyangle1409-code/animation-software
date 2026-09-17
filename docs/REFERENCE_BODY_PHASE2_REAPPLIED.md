# Phase 2 — bind representation fixed, equivalence proven, Stage 2 re-applied

Phase 1 preserved exactly. Nothing promoted or merged. **One test fails**, named
in "The one open item" below; everything else in this document is measured and
passing.

| file | SHA-256 |
|---|---|
| `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb` | `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0` |

## Why the first candidate broke, and the fix

Two faults, one on top of the other.

**1. The bind representation was inconsistent.** `bindRetarget` takes each bone's
rest frame from its head to its *mapped child's* head, and its correction is
that frame measured against the bone's own stored bind orientation. Translating
`DEF-upper_arm.*` moves the **clavicle's tail** while leaving the clavicle's
stored orientation where it was, so the correction silently absorbs the angle
between them and the retargeted arm swings out. Stage 1's forearm tool used the
same mechanism safely only because it translated *along* a bone axis, which
leaves every direction unchanged; a lateral translation does not.

The fix: the arm chain translates rigidly and **the clavicle rotates by exactly
the angle its tail moved through** — a measured 10.147°, symmetric, with its
head held. Stored orientation and derived frame stay in step, so no correction
changes meaning. No arm length changes; the clavicle simply spans further.

**2. A matrix-order error hid behind it.** The script's helper multiplies arrays
row-major while glTF stores column-major, so `mul(A, B)` represents **B·A**. A
world-space transform therefore has to be applied as `mul(W, X)`, and a local as
`mul(W, invert(parentW))` — both of mine were reversed, and so were the first
attempt's. Verified against an independent reader: `mul(local, parentWorld)`
reproduces the published bone positions exactly.

The tool now **re-reads its own output** and checks achieved bone placement
against what was asked. Result: clavicle heads held at 0.00 mm, the whole arm
chain translated purely laterally by 38.82 mm model units on both sides,
**exact to 6.8e-13 mm.** The first attempt shipped a candidate whose arm was
28 cm out of place; that is now impossible to miss.

## Retarget equivalence

| check | result |
|---|---|
| import height and uniform scale vs Stage 1 | **identical** — 2.017579 m, 0.867376 (the broken candidate read 2.261510 / 0.773819, a 10.8% global error) |
| bones off the arm, driven from the same canonical poses across curl and press | **0.0000 mm of movement** |
| achieved bone placement vs intent | exact to 6.8e-13 mm |
| grip contact, Stage 2 candidate on the widened rig | **identical to locked Phase 1 to the digit**: fingers −0.46 / −0.36 / −0.22 / −0.11 mm, zero inside; thumb +1.18 mm; palm −2.54 mm; wrap 252° |
| curl Bottom/Return dumbbell-to-thigh | **+4.68 / +4.79 mm, zero inside** — better than Phase 1's +1.81 / +1.90, because the wider shoulder carries the weight further from the leg |

Equivalence is stated functionally rather than as a quaternion diff on purpose:
what matters is that the same canonical input produces the same character pose
plus the intended shift, and that Phase 1's grip and clearance survive. They do.

(One note on method: comparing the *Stage 1* candidate against the *Stage 2*
candidate under a single canonical rig leaves a ~5 mm arm residual, because
whichever rig the process loads, one of the two characters does not match it.
That residual is an artefact of the comparison, not of the candidate, which is
why the checks above pair each candidate with its own rig.)

## Re-applied Stage 2 work

All of it, from the recorded derivation — no value was re-derived.

- **Canonical rig**: `SHOULDER_WIDENING = 0.01924 × RIG_HEIGHT` = 33.67 mm per
  side over the clavicle tail and everything outboard. Nothing scaled.
- **Shoulder-relative contact rules**: press and push-up width envelopes,
  pull-up grip and the rack's `pullup_l/r` sockets (±0.24 → ±0.274, on a 1.3 m
  bar with uprights at ±0.62), and the pull-up hang height (−0.055 → −0.0631,
  the measured 8.1 mm the longer clavicle lifts the shoulder). Push-up's
  `body_line` tolerance carries the widening because its sagittal deviation is
  0.0000 at every frame — the whole 0.0669 is the constant lateral fact that a
  shoulder is wider than a hip, so the sagittal margin stays at 26.8 mm,
  exactly what it was. **All four exercises validate clean.**
- **Procedural surface**: the baked anatomical body carries the widening through
  a 2-hop graph-distance ramp, held at 1 where the arm owns the surface. The
  shoulder's worst and tightest edge strains come out **better than leaving it
  unshifted** (5.215 vs 5.308, 0.1580 vs 0.1324). Torso not widened.
- **Muscle anchors**: three deltoid origins follow the clavicle's moved lateral
  end (without which `deltoid_medial` lengthens in its own abduction again);
  pectoralis and latissimus insertions brought onto the humerus shaft; both
  origins moved laterally by 15–20 mm, less than the widening, along attachments
  that are broad sheets in life. No thickness, bulge, flatten or spread changed.
- **Deltoid-to-deltoid envelope** in `body.test` carries the widening; the rig
  now measures 500 mm against a reference of about 520 mm.

### Reference overlay, on the corrected candidate

| landmark | reference | Stage 2 | Δ |
|---|---|---|---|
| **shoulders** | 29.69 | **29.40** | **−0.29** |
| neck | 7.26 | 7.26 | 0.00 |
| head | 10.35 | 9.92 | −0.43 |
| hip | 21.50 | 22.29 | +0.79 |

From −4.17% to −0.29% of figure height — about 5 mm on a 520 mm span, inside
every other landmark's error, so effectively on target. It is not the exact 0.00
the earlier run reported: that figure came from the *broken* candidate, whose
clavicle had not been re-aimed, so the silhouette it measured was not a pose the
rig can actually produce.

## The one open item

`muscle overlay > keeps every belly inside the skin in every other exercise too`
fails: `pectoralis_l` reaches **7.84 mm** outside the containment skin in the
push-up, against a 7 mm allowance. The latissimus sits just behind it at 7.34 mm.

Diagnosed rather than left vague. Both bellies exit nearest **`spine_03`** — the
chest's lateral edge, at x ≈ −0.17 to −0.20 — into the band the widened arm
vacated between a chest that must not widen and a deltoid section that moved
outward with the humerus. It is a gap in the *containment proxy* surface, not
added mass.

Every lever the decision permits was tried and measured:

| lever | result |
|---|---|
| insertions onto the humerus shaft | fixed the press case and the latissimus; press went from 9.86 mm to clear |
| origins moved laterally | 9.86 → 7.84 mm; past −0.085 the latissimus breaks elsewhere |
| `taper` on either sheet | migrates the violation between poses and muscles rather than reducing it — 0.92 → 7.7 mm, 0.84 → 10.3 mm, 0.78 → moves to the squat; on the latissimus it makes it *worse* |
| `flatten` | no effect on the probed depth at all |
| explicit `outward` | moves it under 0.3 mm |
| an extra interpolated clavicle profile ring | changes the figure by **zero digits** — the nearest section is the chest, not the clavicle |

What is left would be either widening the chest, scaling a belly down, or
opening the containment skin's armpit coverage. The first two the decision
forbids; the third is a judgement about a proxy surface that runs close to "do
not inflate deltoid mass to fake shoulder width", so it is put to you rather
than taken unilaterally. The residual is 0.84 mm on a 7 mm allowance.

## Status

Suite: **297 passed, 1 skipped, 1 failed** (the item above). Typecheck clean.
Phase 1 grip, curl motion and thigh clearance all preserved or improved.
Phases 3–5 not started, since Stage 2 acceptance requires no unresolved
regression and this one is unresolved.
