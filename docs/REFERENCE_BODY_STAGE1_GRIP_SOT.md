# Stage 1 — grip single source of truth, and the curl-bottom clearance attempt

Executing `docs/REFERENCE_BODY_STAGE1_SIGNOFF_DECISION.md`. **Stage 2 has not
started.** Nothing promoted or merged.

| File | SHA-256 |
|---|---|
| `HomeGymPT_Male_STAGE1_CANDIDATE.glb` | `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb` |

Geometry, skeleton, weights, inverse binds and topology are identical to
`HomeGymPT_Male_FOREARM_CANDIDATE.glb` (`f48d48e5…5ebe9`). The only change is
one scene-extras entry, below.

## Part A — the grip frame

### What the character now carries

```
homeGymPT.handleGripOffsets = { l: [0.0174, 0.0542, 0.0083],
                                r: [-0.0174, 0.0542, 0.0083] }
```

The centre of a held cylindrical handle inside this character's **closed** fist,
expressed in the frame `handMatrix` returns. It was measured on the character
itself — the centroid of the vertices on the middle phalanges of all four
fingers and the thumb at 85% closure — and mirrored exactly.

It is deliberately separate from the `gripFrameOffsets` the character already
carried (`l [0.015, 0.055, 0.012]`). Those are **not** a handle centre: that
frame's origin is the palm contact point, and `RetargetContactResolver` uses it
as the arm's contact target for floor and bar locks. Moving it to the handle
centre would have shifted every push-up and pull-up contact by 54 mm. Two
distinct points, now named distinctly.

The measurement also explains the earlier failure. `handMatrix`'s origin sits
58.3 mm from the hand bone. The handle centre is a further 57 mm out through the
fist. The shipped literal `{0, 0.045, 0}` stopped ~9 mm short of it — inside the
fist, which is why it looked plausible — and `anatomicalGripOffset`
(`{∓0.025, 0.085, 0}`) overshot by ~31 mm, with its mirrored x on the opposite
sign to this character's frame. Neither is wrong as a canonical-rig constant;
both are wrong stacked on a character that carries its own grip frame.

### What changed in code

- `CharacterBuild` gains `gripOffset?(side)`.
- `retargetedCharacterSource` reads `handleGripOffsets` and exposes it.
- `src/viewer/EquipmentView.tsx` and `src/export/glb.ts` use
  `instance.gripOffset ?? character.gripOffset?.(side) ?? anatomicalGripOffset(side)`.
  Both `{0, 0.045, 0}` literals are gone.
- The exporter no longer rebuilds the grip frame from the scale and basis
  correction by hand. It takes `handMatrix` directly, which also applies the
  character's `gripFrameOffsets` — reconstructing only the first two left the
  exported item short of the palm by that offset.
- `twoHandGripOffsets` falls back per side rather than sharing one offset
  between both hands, so the mirrored palm axis is respected.

### Renderer, exporter, solver

Renderer and exporter now agree to **0.0000 mm** at t = 0, 2 and 4 s, both
sides (`scratchpad/repair/gripagree.test.mts`).

**The solver does not, and cannot be made to without a frame of lag.** I tried:
threading the character's hand frame into `resolveFrame` so a single resolved
transform served everything. It fails by 528 mm, because `resolveFrame` resolves
equipment *before* `applyCharacterPose` runs — the pipeline solves on the
canonical rig, and the character is posed from its result afterwards. That
ordering is why the renderer reads `handMatrix` at draw time in the first place.
The threading was backed out.

So the honest position is: **one offset definition**, used by the renderer and
the exporter in the character's frame, and by the solver on the canonical hand,
where the canonical constant is the correct value for the canonical rig it is
solving on. The solver's transform drives lock resolution, not drawing. Making
it character-aware needs the pipeline reordered so the character is posed before
equipment resolves, which is a larger change than this task authorises.

### Validation

Handle centre sits inside the closed fist, fingers wrapping over the bar, palm
loaded — `shots/GRIPFINAL_curlPeakHands.png`, against `GRIPSHIPPED` (old
literal) and `GRIPNEW` (canonical constant, handle outside the fist). Left and
right mirror exactly. 54 focused equipment, grip, export, exercise and animation
tests pass.

## Part B — curl clearance under the unified rule

Closest plate-to-thigh distance, left / right, real dumbbell geometry:

| Frame | distance | thigh vertices inside |
|---|---|---|
| Bottom | **−13.59 / −13.73 mm** | 3 / 3 |
| Mid lift | +174.56 / +174.62 mm | 0 |
| Peak | +189.41 / +189.41 mm | 0 |
| Mid lower | +200.07 / +200.13 mm | 0 |
| Return | **−13.59 / −13.73 mm** | 3 / 3 |

Bilateral difference 0.14 mm. Mid, Peak and Mid-lower are comfortably clear, as
expected. Bottom and Return — the same pose — still contact.

## Part C — abduction sweep, and why I stopped

Swept the curl-bottom upper-arm abduction, modifying only `startPose.upperarm_*`
z and leaving everything else alone. The authored technique rule
`upper_arm_clear_*` permits up to 20°, so none of these violate it.

| abduction | plate clearance L / R | hand-to-leg gap |
|---|---|---|
| 3° (current) | −13.59 / −13.73 mm | 3.84 mm |
| 5° | −16.16 / −16.27 mm | 3.63 mm |
| 6° | −16.61 / −16.45 mm | 2.10 mm |
| 7° | **−5.36 / −5.19 mm** | 3.78 mm |
| 8° | −13.17 / −12.79 mm | 2.51 mm |
| 9° | −13.00 / −13.56 mm | 3.40 mm |
| 11° | −12.96 / −13.29 mm | 7.60 mm |

**No value clears, and the relationship is not monotonic**, which means I cannot
name "the smallest value that gives genuine geometric clearance" — the premise
of the instruction does not hold here. The hand-to-leg gap tells the story:
abducting the shoulder from 3° to 9° does not move the hand away from the thigh
at all (3.84 → 3.40 mm). The abduction is being absorbed somewhere between the
shoulder and the hand, so the weight is rotating in place rather than
translating clear, and the plate contact wanders with the handle's orientation
instead of improving with the angle.

The best residual found is −5.4 mm at 7°, which is better than the current
−13.6 mm — but I have not established *why* 7° is special, and retaining a
motion change I cannot explain, on a hunch that it will hold for other
characters and poses, is exactly the "move it until one frame looks correct"
the guardrails forbid. The decision document also says to stop and report rather
than force it, so no abduction change is retained and the curl is untouched.

What I did not get to the bottom of, and would look at next: whether the closest
contact at Bottom is on the thigh proper or on the hip/pelvis above it, which
would explain why abducting the arm does not help; and what absorbs the
abduction between shoulder and hand.

## Sign-off criteria

| # | criterion | status |
|---|---|---|
| 1 | forearm at corrected canonical proportion | met — geometry untouched |
| 2 | shoulder chain untouched | met |
| 3 | one authoritative character-aware grip rule across viewer/exporter/solver/diagnostics | **partial** — one definition; renderer and exporter agree to 0.0000 mm; the solver stays in canonical space for the ordering reason above |
| 4 | handle inside the fist, palm/finger/thumb correct | met |
| 5 | Bottom/Return penetration cleared | **not met** — −13.6 mm; sweep did not yield a clearing angle |
| 6 | Mid lift, Peak, Mid lower clear | met — 175–200 mm, nothing inside |
| 7 | accepted curl mechanics unchanged | met — no motion change retained |
| 8 | grip closure 85%, elbow corrective 0% | met |
| 9 | shoulder press and shared paths do not regress | met — Rack/Mid/Overhead/Lower clear by 299–466 mm, zero inside, exactly symmetric |
| 10 | hand/wrist repair no worse | met — geometry identical to Stage 1 |
| 11 | strain/diagnostic acceptable | met — geometry identical to Stage 1 |
| 12 | typecheck, build, focused tests pass; only the known timeout fails | met — 292 passed, 1 skipped, 1 failed (`strainReview`) |
| 13 | Stage 2 not started | met |

Eleven met, one partial, one not met. **Stage 1 is not frozen.**

## Push-up

Untouched, as instructed.
