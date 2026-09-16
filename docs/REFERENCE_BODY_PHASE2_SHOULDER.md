# Phase 2 — Stage 2 shoulder widening: measured and derived; canonical half blocked

Phase 1 is locked (`docs/REFERENCE_BODY_PHASE1_LOCKED.md`). Nothing promoted or
merged. The repository is green: 298 passed, 1 skipped, 0 failed.

## The measurement, re-verified

The decision says not to reuse a stale transform, and it was right to. Re-running
the locked front overlay on the current Stage 1 candidate gives different numbers
from the old rig proposal, which measured a different row.

| landmark | reference | Stage 1 | Δ |
|---|---|---|---|
| head | 10.35 | 9.92 | −0.43 |
| neck | 7.26 | 7.26 | 0.00 |
| **shoulders** | **29.69** | **25.52** | **−4.17** |
| hip | 21.50 | 22.29 | +0.79 |
| waist | 15.82 | 15.46 | −0.36 |
| thigh | 11.21 | 11.07 | −0.14 |
| knee | 5.75 | 5.82 | +0.07 |
| calf | 7.26 | 7.76 | +0.50 |

Percentages of sole-to-crown height. Everything except the shoulders is inside
0.8%, so the shoulder is the one real gap — which is what the earlier
investigation concluded, at a different magnitude.

(The ankle row reads +3.16 and is not a body finding: the reference's feet are
cropped dark, so its ankle width measures near zero. It was excluded from the
earlier rounds for the same reason.)

## The derived transform

The whole arm chain translates laterally outward from `DEF-upper_arm.*`. Nothing
is scaled: upper-arm and forearm lengths are untouched, and the clavicle simply
spans further, which is what a wider shoulder is. **No mass is added anywhere** —
widening by inflating the deltoid is what the decision rules out.

The response had to be measured rather than assumed, because the deltoid seam is
shared with the torso and a vertex's share of the shift is its weight on the arm:

| shift per side | shoulders | Δ vs reference |
|---|---|---|
| 2.090% of height (36.6 mm studio) | 30.05 | **+0.36** |
| **1.924% of height (33.7 mm studio)** | **29.69** | **0.00** |

The span gains 1.083× the total applied shift — slightly *more* than one for one,
not less as the old proposal expected. **1.924% per side lands the shoulder span
exactly on the reference**, and the shoulder landmark's *height* mismatch also
falls from +2.6% to +0.4%, which is independent corroboration: the landmark is
now found where the reference finds it.

## The character candidate

| file | SHA-256 |
|---|---|
| `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb` | `173ef5dfe6c5985306274d4cee75d64e95708fcaac1824c1fb62bf487f509f4d` |

Built by `scratchpad/reference-fit/stage2_shoulder.mjs` from the Stage 1
candidate. v5, v6, v7 and every earlier candidate are untouched.

- 3086 vertex moves, worst 38.8 mm in model units;
- inverse binds rewritten for **48 of 160 joints** — only the moved chain;
- weights, joint indices, UVs, vertex colours, indices and topology unchanged;
- normals rebuilt over the moved set and one ring beyond it.

**Symmetry, honestly:** worst left/right difference 0.712 mm over 4175 mirrored
pairs. That is not my edit being asymmetric — the edit mirrors by construction,
and the residual scales exactly with the shift (0.712/0.774 = 0.920 against
1.924/2.090 = 0.921). The cause is the asset's own skin weights: the arm weight
mask differs by up to 0.0183 at mirrored pairs (mean 0.00004), which at a 33.7 mm
shift is 0.618 mm of the 0.712 mm seen, the rest being the 0.25 mm pairing
bucket. The constraint is to preserve weights unless a correction is objectively
required, so the asymmetry is followed faithfully rather than papered over.

## The canonical half, and why it is not applied

The decision requires the canonical rig and the character to widen **together**.
I implemented that as one constant, `SHOULDER_WIDENING = 0.01924 × RIG_HEIGHT`,
applied to the clavicle tail and every bone outboard of it, mirroring through the
existing machinery. It typechecks and it widens the rig correctly.

It also breaks nine tests, and only some of them are re-derivable.

**Re-derived successfully.** `hand_width` on the press, and the width envelopes
on push-up and pull-up, are absolute spans whose own labels state a
shoulder-relative intent ("Hands are shoulder-width or slightly wider", "Grip
stays just wider than the shoulders"). Shifting both bounds and the authored
`hands.width` by the added span, 67.3 mm, preserves that intent exactly. The
shoulder press then validates clean.

**Not re-derivable without a decision.**

1. **Pull-up.** Its hands are not placed by `hands.width` at all — they are locked
   to the rack's fixed `pullup_l`/`pullup_r` sockets. So widening the authored
   width moved the envelope without moving the hands, and `full_hang_l/r` still
   fail: a grip now narrower than the shoulders forces elbow flexion at the dead
   hang. Fixing it properly means the pull-up grip position has to *track shoulder
   width* rather than being a fixed property of the rack. That is a design change
   to the equipment model, not a re-derived contact rule.
2. **Push-up.** `body_line` fails for the same class of reason: the floor hand
   placement is fixed, so wider shoulders change the torso height at the same
   elbow angle and head/hips/ankles leave one line.
3. **The procedural body and muscle overlay.** `body.test`, `ecorche.test`,
   `shoulder.test`, `muscles.test` and `functions.test` all fail: the procedural
   body silhouette and the muscle bellies are built from the rig and need widening
   in step, or a belly leaves the skin.

Rather than rush those — a hurried contact re-derivation on push-up and pull-up
is exactly how subtle breakage gets in — the canonical widening and the three
exercise edits are **backed out**. The tree is green and the derivation is
recorded above, so applying it later is a matter of executing, not re-deriving.

## What is needed to finish Phase 2

1. A decision on whether the pull-up grip and push-up hand placements may become
   shoulder-width-derived rather than fixed. Without it the canonical rig cannot
   widen, and without the canonical rig widening the character and the rig
   disagree about where the shoulder is, which is worse than either.
2. Widening the procedural body geometry and muscle belly fits by the same
   constant, so the overlay stays inside the skin.

Phases 3–5 are not started: Phase 3 is the full validation pass over Stage 1 +
grip + Stage 2, and Stage 2 is not in place.
