# Phase 1 — proximal handle-centre sweep: blocked by curl thigh clearance

Executing the follow-on sweep in `docs/REFERENCE_BODY_PHASE1_GRIP_SOLVER.md` from
`4a82e75`. The close-until-contact solver is kept unchanged. **Phase 1 is not
locked and Stage 2 has not been started.** Nothing promoted or merged.

## Direction

`handleGripOffsets` is expressed in the `handMatrix` frame. Probing the posed
hand in the handle's own frame put the palm centroid at (−29.5, −85.2, −18.0) mm
and the wrist at (−32.4, −109.2, −20.3) mm, so **−y is both proximal and deeper
into the palm** — the two directions the decision names are nearly the same one
here. The sweep ran in −y, with a −x arm to test "deeper" separately.

## Sweep

Solver re-run from scratch at each centre; contact from the repaired
finite-cylinder harness; curl Peak, left hand.

| shift (mm) | index MCP | fingers | palm | thumb | wrap |
|---|---|---|---|---|---|
| 0, 0 | 30.4° | −0.46 / 0 in | −1.14 | +3.80 | 240° |
| 0, −3 | 35.9° | −0.47 / 0 | −1.75 | +3.80 | 252° |
| 0, −6 | 44.2° | −0.32 / 0 | −1.67 | +2.95 | 264° |
| 0, −9 | 52.5° | −0.46 / 0 | −2.54 | +1.18 | 252° |
| 0, −12 | 60.8° | −0.38 / 0 | −3.53 | −0.19 | 261° |
| 0, −15 | 66.3° | −0.45 / 0 | −3.78 | **−7.82** | 285° |
| −5, −6 | 38.7° | −0.42 / 0 | **−6.69** | **−3.49** | 294° |
| −5, −9 | 47.0° | −0.44 / 0 | **−6.75** | **−6.42** | 312° |
| −5, −12 | 55.3° | −0.49 / 0 | **−8.33** | **−8.93** | 310° |

The −x arm is rejected outright: it sinks the handle 6–9 mm into the palm and
drives the thumb through it. Wrap is not used to choose — it is noisy here and,
as recorded earlier, only meaningful for a non-penetrating grip.

Along −y the MCPs free steadily and together (index 30.4 → 52.5 → 60.8), which is
the thing that was broken: at the embedded centre the handle sits against the
knuckle row, so the proximal phalanges reach it almost immediately and the
fingers cannot roll over it.

## Visual

Rendered as a three-quarter view with the bar as a real cylinder and lambert
shading from the triangle normals — `scratchpad/repair/shots/GRIP_q*_3q.png`. The
axial view used until now cannot settle this: a fingertip closing under the
handle is at the far end of the bar, clipped or occluded.

- **0 mm** — lower fingers wrap, but the index stands off the bar, as its 30.4°
  MCP says it must.
- **−6 mm** — better, but the lower fingers still stop at the handle's side.
- **−9 mm** — reads as a fist: all four curl around and the fingertips come under
  the bar.
- **−12 mm** — slightly more closed, no better in kind, and it spends the thumb's
  clearance down to −0.19 mm.

By the decision's selection rule the answer is **−9 mm**: the smallest shift that
reads as a true full fist while keeping the palm loaded, the thumb clear and no
digit penetrating.

## Why it cannot be taken

−9 mm breaks the curl's dumbbell-to-thigh clearance, which is on the decision's
own regression list and which Stage 1 cleared at some cost.

| shift | Bottom / Return clearance |
|---|---|
| 0 mm | **+1.74 / +1.82 mm**, 0 inside (Stage 1) |
| −3 mm | +0.70 / +0.78 mm, 0 inside |
| −5 mm | +0.09 / +0.17 mm, 0 inside |
| −6 mm | −0.18 / −0.10 mm, **1 inside** |
| −9 mm | −0.88 / −0.80 mm, **1 inside** |

The relationship is linear and the budget is tiny: **1 mm of proximal shift costs
about 0.29 mm of thigh clearance**, and Stage 1 left only 1.74 mm. The largest
shift that keeps the thigh clear is about −5 mm, with 0.09 mm of margin — which
is no margin — and −5 mm does not produce the fist the decision is asking for.

So the two written requirements are incompatible at this character's current
geometry:

- a convincing full-fist grip needs the handle about 9 mm proximal;
- the frozen curl keeps the plate off the thigh only while the handle stays
  within about 5 mm of where it is.

Both the curl motion (including the +4.3° rebase that bought that 1.74 mm) and
MCP placement are explicitly not mine to change here, so this is the report
rather than the lock.

## What was retained

Nothing new. `src/character/solvedGrip.ts` is unchanged at the validated 0 mm
solution from `899a9d9`: zero digits inside, palm loaded at −1.14 mm, thumb
opposing at +3.80 mm, wrap 240°. Thigh clearance re-measured back at
**+1.74 / +1.82 mm, nothing inside**. One unrelated fix is kept: a template
literal in `solvedGrip.test.ts` widened a bone name to `string` and failed
`tsc` — the tests passed, but the project typecheck did not.

## What would unblock it

One of these, each needing a decision that is not mine:

1. **Buy back thigh margin in the curl.** About 2.6 mm more clearance would fund
   the full −9 mm shift. The +4.3° rebase bought 1.74 mm, so the mechanism is
   known to work and the cost is a little more upper-arm flexion at the bottom.
2. **Move the handle along the bar axis or revisit MCP placement**, which the
   decision rules out without a new authorisation.
3. **Accept −5 mm**, which improves the grip short of a true fist and leaves the
   thigh at 0.09 mm — not recommended: it trades a visible margin for an
   invisible one, and still does not lock Phase 1.
