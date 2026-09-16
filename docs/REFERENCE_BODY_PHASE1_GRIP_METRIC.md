# Phase 1 — grip harness repaired, and what the corrected metric says

Diagnostic repair only. **No grip profile was tuned or retained**, and the
reason is in "The blocker" below. Stage 1 stays frozen; Stage 2 not started.
Nothing promoted or merged.

Measured on `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`), curl
Peak, left hand unless stated.

## The four faults, and the fixes

**1. Vertex classification.** The old harness took each vertex's single
highest-weighted bone and discarded any vertex whose best bone held under 0.5.
A finger vertex normally splits about 0.45/0.40 across two phalanges, so those
vertices were either thrown away or — when the palm happened to hold the
plurality — counted as palm. That is the entire dominant-bone vs summed-weight
disagreement, and it is why the palm looked like the binding constraint.
Vertices are now assigned to the group holding the largest **summed** weight,
which is how the vertex actually moves.

**2. Finite-handle contact.** Distance was measured to an *infinite* cylinder,
and anything outside an axial slab was `continue`d. A vertex just past the end
of the bar was recorded as absent rather than as clear. It is now the signed
distance to the real **capped** cylinder, so nothing is discarded and a vertex
beyond the cap reads as the positive distance it is.

**3. Axial slab.** The half-length was an environment variable — ±40 mm in one
harness and ±60 mm in another, which is precisely why the two disagreed. It is
no longer a filter at all: the cap is the bar's real half-length, 60 mm, read
from `src/equipment/geometry.ts` (`bar(0.015, 0.12)`, discs at ±0.075 on z, so
the bar axis is local z — checked, not assumed).

**4. Sweep integrity.** A profile sweep had returned byte-identical numbers.
Every profile now reports the canonical joint angle it produced *and* a checksum
of the posed hand vertices, and the run flags `SWEEP-DEAD` if either fails to
move between profiles. Six profiles now give six distinct checksums and a
monotonic response. The original fault was a clip generated before the profile
mutation; the clip is now regenerated after every mutation.

## Proof the harness is correct

- Six profiles, six distinct vertex checksums, no `SWEEP-DEAD` rows.
- The metric responds monotonically to profile depth, and the response is
  traceable to a moved mesh rather than to a changed constant.
- The metric is pose-invariant across curl Bottom/Mid/Peak, as a rigidly held
  handle must be, while the checksums differ — the hand is in a different place
  each time but the grip geometry is not.
- Renders are drawn from the same posed vertices, through the same transform,
  and the render's highlighted set is **75 vertices against the metric's 75**.
- Left and right agree to the digit on every figure below.

## Rendered evidence

`scratchpad/repair/shots/GRIP_{shipped,flat}_{solid,slice}.png`. The solid view
looks down the bar axis at the back half of the hand, with the bar as a white
outline; the slice is a cross-section of the bar's mid plane against its true
circle. Penetrating vertices are red, contact vertices amber.

The shipped image settles it: **the bar's circle is entirely filled with hand
surface.** The fist closes solid, straight through the bar's volume. The slice
shows red vertices inside the circle with green middle-phalanx vertices just
outside it. Metric and picture agree.

## The corrected numbers, which invert the previous finding

At the frozen grip centre, curl Peak, closure 0.85 (mm; "in" = vertices inside):

| profile | finger | palm | thumb | wrap |
|---|---|---|---|---|
| shipped `[78,95,60]` | **−11.48 / 53 in** | −0.59 / 1 in | −10.43 / 21 in | 339° |
| `[66,81,51]` | −9.75 / 36 | −0.75 / 1 | −11.11 / 18 | 338° |
| `[43,52,33]` | −6.83 / 13 | −1.05 / 1 | −8.75 / 24 | 285° |
| `[31,38,24]` | −4.29 / 2 | −1.20 / 1 | −9.83 / 27 | 275° |
| `[20,24,15]` | +1.87 / 0 | −1.32 / 1 | −11.35 / 24 | 265° |
| flat `[0,0,0]` | +3.82 / 0 | −1.50 / 1 | −13.92 / 30 | 290° |

The previous report had this backwards. It is the **fingers** that penetrate,
by 11.48 mm over 53 vertices, and the **palm** that barely touches at −0.59 mm
over a single vertex — which is exactly the firm contact a loaded grip should
show. The old "4.61 mm over 2 vertices" finger figure was the misclassification;
the old "palm is closure-invariant, so closure cannot help" conclusion followed
from it and is withdrawn.

## The thumb: a real fix, found and not retained

`thumbOppositionX` is written to `thumb_01.x` with **no per-side sign flip**,
unlike flexion on z. The shipped `−14` rotates the thumb *into* the bar.

| oppX | thumb | finger | wrap |
|---|---|---|---|
| −14 (shipped) | −10.43 / 21 in | −11.48 / 53 | 339° |
| 0 | −6.15 / 6 in | −11.48 / 53 | 339° |
| **+14** | **+2.54 / 0 in** | −11.48 / 53 | 339° |

`+14` clears the thumb completely with wrap unchanged and no effect on the
fingers or palm, and it is **identical on both hands**, so the missing sign flip
is not the problem — the sign itself is. (`+30` and `+45` return the same figure
because the rig limits that axis to ±14°, which is a useful confirmation that
the clamp is live.)

This is not retained. `thumbOppositionX` is shared by every grip profile —
`bar`, `handle` and `rope` all carry `−14` — so flipping it moves the thumb on
pull-up, press and row as well. That is a cross-exercise change and it belongs
in the Phase 3 validation pass, not in a diagnostic phase, and it does not on
its own complete Phase 1.

## The blocker

**No grip profile produces a full-fist wrap on a 30 mm bar without penetrating
this hand, and no handle placement does either.**

- **Profile.** 120 per-joint profiles searched (MCP 25–65, PIP 25–75, DIP
  10–40, thumb corrected to +14). Four came back clean. All four are
  `[25, 25, *]` — a barely-flexed hand — and all four wrap only ≈160°. The DIP
  term does not move any contact figure at that depth, because the distal
  phalanges never reach the bar. The best wrap available anywhere in the grid,
  336°, costs 10.52 mm of finger penetration.
- **Placement.** With the full-fist profile and the corrected thumb, 522 of 6561
  bar centres over a ±40 mm grid clear the fingers and thumb — but **none** of
  them keep the palm loaded. The bar can only avoid the fingers by leaving the
  hand.

So the two Phase 1 acceptance criteria — a full-fist cylindrical wrap, and a
handle that does not pass through the hand — cannot both be met by tuning a
profile. That is the documented stop condition, and it is why nothing was
retained.

One caveat on my own metric, stated rather than buried: **wrap is only
meaningful for a non-penetrating configuration.** A solid fist trivially scores
high, because every direction around the bar has hand surface near it. The 339°
in the shipped row is not evidence of a good grip.

## What would actually fix it

The root cause is that `applyGrip` is a **static angle table scaled by a single
closure scalar**. It closes each digit to a fixed fraction of a fixed pose,
which produces a fist, not a grip — the fingers keep closing after they reach
the bar. A cylindrical grip needs the digits to **close until they contact the
cylinder and stop**, per joint, per digit, which is a solver rule rather than a
table and is genuinely reusable across bar diameters.

That is a change to the animation pipeline, well beyond "tune a profile", so it
needs authorising before anyone starts it. The alternatives are to accept a
reduced-wrap cupped grip at ≈160°, or to revisit the finger bone lengths and MCP
placement in the character's hand, which is rig and mesh work.

## Status

Phase 1 is **not** locked. Stage 2 not started. The harnesses live at
`scratchpad/repair/grip{metric,view,tune}.test.mts`.
