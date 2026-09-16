# Phase 1 — locked

Executing the final compatibility decision in
`docs/REFERENCE_BODY_PHASE1_GRIP_SOLVER.md` from `9c0855d`. Nothing promoted or
merged.

## Retained

| piece | value |
|---|---|
| curl neutral rebase | `startPose.upperarm_l/r.x = 4.55°`, `peakPose = 8.55°` |
| handle centre | −9 mm proximal, in `solvedGrip.handleCentre` |
| grip | close-until-contact solved digits, unchanged mechanism |
| thumb | `thumbOppositionX +16.47` (clamped to +14 at this closure), family-scoped |

Measured on `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`). The asset
is untouched: the handle correction lives with the solved angles, because the
two were solved together and neither is right without the other.

## The compatibility test

Only the three authorised rebases were tried, start and peak moved by the same
delta each time.

| rebase | Bottom / Return clearance | inside |
|---|---|---|
| 4.3° / 8.3° (frozen) | −0.88 / −0.80 mm | 1 |
| 4.5° / 8.5° | +1.27 / +1.36 mm | 0 |
| **4.55° / 8.55°** | **+1.81 / +1.90 mm** | **0** |
| 4.6° / 8.6° | +2.35 / +2.44 mm | 0 |

The rebase buys clearance far faster than the earlier linear estimate suggested
— about 10.7 mm per degree here, not the 0.29 mm per mm of handle shift that the
sweep implied — because it rotates the whole hanging forearm away from the thigh
rather than sliding the weight along it.

**4.55° is the retained value.** 4.5° clears genuinely but only to +1.27 mm,
short of the decision's preferred +1.5–2.0 mm band; 4.55° lands inside it at
+1.81/+1.90 and restores a slightly better margin than the frozen curl had
before the handle moved. 4.6° would be optimising past the smallest passing
value.

## Every measurement the decision asked for

| check | result |
|---|---|
| Bottom / Return thigh clearance, both sides | **+1.81 / +1.90 mm**, 0 vertices inside |
| Mid lift / Peak / Mid lower | clear by 190–230 mm, 0 inside |
| grip: index / middle / ring / pinky | −0.46 / −0.36 / −0.22 / −0.11 mm, **0 inside** |
| grip: thumb | **+1.18 mm**, 0 inside, opposing |
| grip: palm | **−2.54 mm**, loaded, 2 vertices |
| wrap | 252° |
| bilateral symmetry | identical to the digit, both hands, every figure |
| relative upper-arm drift | **exactly 4.000000°** at peak and late, 0.000000° at Bottom/Mid/Return |
| elbow flexion profile | 6 → 66 → 126 → 6°, unchanged |
| authored technique rules | **22 of 22 pass, no violations** — including `shoulder_quiet_l/r`, `elbow_not_inward_l/r`, `elbow_under_shoulder_l/r`, `no_swing`, `upper_arm_clear_l/r` |
| IK reachability / loop closure | nothing unreachable, loop closes |
| renderer vs exporter | **0.0000 mm** at t = 0, 2, 4, both sides |
| shoulder press grip | identical figures, no per-exercise tuning |
| typecheck / build | clean |
| full suite | 297 passed, 1 skipped, 1 failed — the pre-existing `strainReview` 5 s timeout |

Visual: `scratchpad/repair/shots/GRIP_LOCKED_3q.png`, a three-quarter view with
the bar as a real cylinder. All four digits curl around and under the handle,
the fingertips continue beneath it, the thumb opposes over the top and the
handle is visibly deep in the palm. It reads as a fist around an object.

The rebase is +0.25° on the frozen value. `no_swing` and `shoulder_quiet_*` pass
unchanged and a quarter of a degree of neutral flexion is below what the
silhouette can show, so the curl still reads as a strict natural curl with no
forward reach.

## Acceptance

All twelve criteria pass, including the two visual ones that were outstanding.
**Phase 1 is locked.** Stage 1 remains frozen apart from the authorised rebase,
which uses the same mechanism as the +4.3° it replaces. Continuing with Phase 2.
