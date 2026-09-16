# Stage 1 — curl contact calibration attempt

Executing `docs/REFERENCE_BODY_STAGE1_NEXT.md`. **Stage 1 is not signed off and
Stage 2 has not started.** No asset changed, no source change retained, nothing
promoted or merged. The Stage 1 candidate is unchanged at
`f48d48e54553faa972683ce539b54d3b16ae58d1eda8e98b55d1a1725a35ebe9`.

## Correction to the Stage 1 report

The regression I reported — curl-bottom overlap doubling from −6.65 to
−13.85 mm — is **measurement-rule dependent, and under a consistent rule Stage 1
is the best of the three bodies.** The harness, like the viewer, stacks a
canonical-rig constant on top of the character's own grip frame; change which
constant and the ranking changes.

Closest approach at curl bottom, left / right:

| grip offset used | v7 | refmatch | Stage 1 |
|---|---|---|---|
| shipped renderer `{0, 0.045, 0}` | −5.86 / −5.81 | −6.65 / −6.60 | −13.85 / −13.99 |
| `anatomicalGripOffset` | −10.24 / −9.73 | −10.61 / −10.03 | **−9.91 / −9.87** |

Under the anatomical rule — the one the constraint pipeline has always used —
Stage 1 is the *least* overlapping and the most symmetric (0.04 mm left/right,
against v7's 0.51 mm).

## The contact cannot be cleared by calibration

The hand is already touching the leg. Closest hand-surface to leg-surface
distance at curl bottom:

| | v7 | refmatch | Stage 1 |
|---|---|---|---|
| hand-to-leg gap | 3.10 mm | 2.19 mm | **3.84 mm** |

**Stage 1 has the most clearance of the three.** A dumbbell held in that fist
has its inboard plate reaching 92.5 mm from the grip centre — the real geometry
from `src/equipment/geometry.ts`, a 15 mm bar 120 mm long and two 48 mm rubber
discs 35 mm thick centred 75 mm out. With the hand 2–4 mm off the thigh, that
plate is inside the leg for *any* grip centre that keeps the handle in the palm.

Clearing it needs the arm abducted a few degrees at the bottom of the curl. That
is a motion change, which this pass is not allowed to make, so **sign-off
criterion 5 cannot be met by equipment calibration and needs a decision.**

Across the full retained sequence the contact exists only at Bottom and Return,
which are the same pose; Mid lift, Peak and Mid lower clear by 157–235 mm with
no vertices inside, both sides.

## What was tried, and why it was reverted

Three code paths disagree about the grip offset:

| path | offset |
|---|---|
| `src/viewer/EquipmentView.tsx` (what is drawn) | `{0, 0.045, 0}` |
| `src/export/glb.ts` | `{0, 0.045, 0}` |
| `src/equipment/attach.ts` `resolveEquipment` (what the constraint pipeline solves) | `anatomicalGripOffset(side)` |

So the dumbbell that is drawn and the dumbbell the solver reasons about are
40 mm apart up the palm and 25 mm across. Unifying them on the documented
anatomical rule looked like the calibration this task wanted: it is rule-derived,
bilateral and deterministic, it improved curl bottom to −9.91 mm, and all 33
focused equipment/grip/export tests passed.

**It was reverted because it breaks the visible grip.** Rendered, the handle
sits outside the fist with the fingers behind the bar. The reason is arithmetic:

- The character carries its own `gripFrameOffsets` in scene extras —
  `l [0.015, 0.055, 0.012]`, mirrored — and `handMatrix` applies them, so its
  origin is already 58.3 mm from the hand bone.
- Measured on this character's own wrapping fingers (the centroid of vertices
  on the middle phalanges of all four fingers and the thumb), the handle centre
  sits a further **(±17.4, 54.2, 8.3) mm** in that frame.
- The shipped `{0, 0.045, 0}` lands about 9 mm short of that centroid — inside
  the fist, which is why the grip looks right.
- `anatomicalGripOffset` `{∓0.025, 0.085, 0}` lands about 31 mm past it, outside
  the fist, and its mirrored x has the opposite sign to this character's frame.

`anatomicalGripOffset` is authored against the canonical rig's hand. Stacked on
a character that already carries its own grip frame, it overshoots. The
divergence is a real defect, but unifying on either constant is wrong: the
correct value is per-character and derivable, as the measurement above shows.
Folding it into the character's embedded `gripFrameOffsets` and having the
renderer contribute nothing would change the contract for every character, which
is more than calibration and not something to do unasked.

## Sign-off criteria

| # | criterion | status |
|---|---|---|
| 1 | forearm remains 14.86% of figure height | met — asset untouched |
| 2 | upper arm and shoulder chain untouched | met |
| 3 | curl motion and timing unchanged | met — curl and press wrist angles bit-identical |
| 4 | grip closure 85%, elbow corrective 0% | met — neither touched |
| 5 | curl dumbbell/thigh contact cleared across the rep | **not met** — see above |
| 6 | grip/palm/thumb secure and natural | met under the shipped rule; the weak thumb opposition at 85% closure is the pre-existing documented item |
| 7 | no shoulder-press regression | met — no shared logic changed; press measures 291–473 mm clear with zero vertices inside at Rack, Mid, Overhead and Lower, perfectly symmetric |
| 8 | hand/wrist deformation no worse | met — unchanged from Stage 1 |
| 9 | typecheck, build and focused tests pass | met — typecheck and build clean, 33 focused equipment/grip/export tests pass, suite 292 passed / 1 skipped / 1 failed (the pre-existing `strainReview` timeout) |

Eight of nine. Stage 1 is held short of sign-off on criterion 5.

## What the decision is

Criterion 5 needs one of:

1. **Abduct the arm a few degrees at the curl bottom.** The anatomically real
   fix — lifters do it — but it is a change to accepted curl motion and needs
   explicit approval.
2. **Accept the residual.** ~10 mm of inboard plate inside the thigh at one pose
   of the rep, present in v7 today and slightly better in Stage 1 under a
   consistent rule.
3. **Calibrate the grip frame per character** and have the renderer stop adding
   a canonical constant. Derived value for this character is above. It fixes the
   drawn/solved divergence but does not clear the contact, because the hand is
   against the leg either way.

Option 2 is the only one available without new permission, and it leaves the
drawn/solved divergence in place. I would take option 1 for the contact and
option 3 separately for the divergence — but both need your say-so.

## Harness notes

`scratchpad/repair/overlap.test.mts` now measures through the viewer's own
placement path (`character.handMatrix` plus `handAttachmentMatrix` with grip and
socket rotations), selectable against the anatomical rule, over the retained
five-frame curl sequence and the four press frames. It reproduces the documented
v7 figure exactly: −5.86 mm left, −5.81 mm right, three thigh vertices inside.
`scratchpad/repair/gripframe.test.mts` derives the handle centre from the
character's own fingers.
