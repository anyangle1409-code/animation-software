# Shoulder slope candidates — review

Body-shape candidates only. Nothing else moves: the skeleton, the skin weights,
the inverse bind matrices, the topology, the UVs and the vertex colours are all
byte-identical to promoted baseline v6, so arm length, retargeting, the exercise
definitions and the accepted motion cannot change — no bone moves and no vertex
changes which bone carries it. **None of these is promoted.**

Built on `HomeGymPT_Male_BASELINE_v6.glb` (`46180b57…410ed`), which is unchanged.
The candidates carry **no shorts mesh**, so the body is judged on its own and the
shoulder edit stays independently reviewable from the garment work.

| Candidate | Peak drop | SHA-256 |
|---|---|---|
| A — mild | 9.6 mm | `c84ba4535686bd63f556c8cc385c66237f134bbf8076e6cc1ee4464d667df64b` |
| B — medium (**preferred**) | 16.0 mm | `2704a83d9dc937bb654bf867c5ce82d74b61c9691c6bbc7a319dfeca37dd15ee` |
| C — strong | 23.9 mm | `641f1be5726c30d2dec946d5f3efc65639462c7a04af70e2d95cfa35cb3d594a` |

Drops are in studio millimetres on the 1.75 m figure.

## What was actually wrong

Measured band by band across the top of the left shoulder, from the neck outward,
the surface falls away by 49.5, 27.9, 18.0, **10.5**, 26.3 then 7.8 mm. That
near-flat step in the middle is the shelf: the line runs out level from the
trapezius and then drops off a cliff at the deltoid, instead of sloping the whole
way. Two things therefore had to change together — the outer end had to come
down, and the corner between trapezius and deltoid had to be rounded.

A first attempt lowered only the middle of the span, tapering back to zero at the
deltoid. It made matters worse in the outer half: the middle sank while the
deltoid cap stayed where it was, so the line came out *flatter* than before.
The shape now used is a ramp that reaches full depth around 55% of the way out
and holds it through the deltoid, applied only to surfaces that face upwards, so
the deltoid's outer silhouette is untouched and only its top line comes down.
A local relaxation of the same masked region then rounds the corner.

## What moved

882 of 10,839 vertices for candidate B, worst displacement 19.2 mm. The change is
confined to a box spanning the shoulder girdle: x ±0.309, y 1.467 to 1.769,
z −0.168 to 0.087 in model units — the trapezius, the clavicle shelf and the top
of the deltoid, nothing below the armpit and nothing past the upper arm.

Only `POSITION` and `NORMAL` differ from baseline v6. Normals are rebuilt where
the surface moved and one ring beyond it, so the new slope lights like a slope
rather than keeping the old shading.

**Symmetry.** Above 0.5 mm the change is exactly mirrored: 209 vertices a side,
worst paired difference 0.015 mm. Below that there is a tail of ten extra
right-side vertices moving less than half a millimetre, which follows the source
mesh's own small left/right asymmetry — the same asymmetry already recorded at
the wrist in `docs/CHARACTER_CANDIDATE_REPAIR.md`. It is far below anything
visible.

## Deformation

Whole-body edge strain, worst value across each exercise, baseline v6 → candidate B:

| Exercise | P95 | P99 | max |
|---|---|---|---|
| Bodyweight squat | 1.2398 → 1.2410 | 1.6254 → 1.6216 | 3.063 → 3.063 |
| Dumbbell curl | 1.2230 → 1.2197 | 1.4845 → 1.4891 | 2.247 → 2.247 |
| Shoulder press | 1.2357 → 1.2369 | 1.6822 → 1.6954 | 3.235 → 3.235 |
| Push-up | 1.2380 → 1.2391 | 1.6485 → 1.6572 | 2.458 → 2.458 |
| Pull-up | 1.3235 → 1.3254 | 1.8954 → 1.9065 | 4.283 → 4.283 |

Maximum stretch is identical in every exercise, P95 moves by at most 0.003 and
P99 by at most 0.013. The optional real-character diagnostic passes on the
candidate as it does on the baseline.

## Visual review

Neutral front, side and rear on matched cameras for all four; then candidate B
through curl peak (2.00 s), shoulder press (2.35 s), push-up bottom (1.58 s) and
the deepest squat (2.20 s), front and side, against baseline v6 on the same
frames.

- The trapezius-to-deltoid corner is visibly softer and the line from neck to
  shoulder tip descends continuously rather than stepping down.
- The deltoid keeps its outer silhouette and its volume; only its top comes down.
- Arms overhead in the shoulder press show no collapse or pinch at the junction,
  and the two sides stay identical.
- A is a small change and leaves much of the shelf; C is the same shape carried
  further and still reads as an athletic build rather than a dropped shoulder.
  **B is recommended** as the smallest that clearly resolves it.

## Known limits

- The judgement is a silhouette judgement, and the band-by-band height metric
  used to find the shelf is a crude proxy: it takes the highest vertex in each
  vertical slice, so it is noisy and it disagreed with the renders more than once
  during this work. The renders decided it; the numbers only located the shelf.
- The edit is bind-pose geometry, so it is carried through every pose by the
  existing weights. It has been checked in four poses, not all of them.
