# Stage 1 — forward-clearance sweep result

Executing `docs/REFERENCE_BODY_STAGE1_FORWARD_CLEARANCE.md`. **Nothing retained,
no asset or source change, Stage 1 is not frozen and Stage 2 has not started.**
Candidate remains `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`).

Abduction held at 3°. The only variable swept was `startPose.upperarm_l/r.x`,
the curl start/end shoulder-flexion channel, which is the Bottom and Return pose
by definition; the existing keyframe easing carries the blend into the accepted
trajectory.

## Bottom and Return

Identical at every value — the same pose — so one table serves both.

| flexion | Δz grip | Δz inboard plate | clearance L / R | vertices inside L / R | region | L/R mismatch | axis Δ° |
|---|---|---|---|---|---|---|---|
| 0.0° (current) | 0.0 mm | 0.0 mm | −13.59 / −13.73 mm | 3 / 3 | upper thigh | 0.13 mm | 0.0 |
| 1.0° | 11.4 mm | 11.6 mm | −9.69 / −9.72 mm | 2 / 2 | upper thigh | 0.04 mm | 0.3 |
| 1.5° | 17.2 mm | 17.3 mm | −7.45 / −7.32 mm | 3 / 3 | upper thigh | 0.14 mm | 0.5 |
| 2.0° | 22.9 mm | 23.1 mm | −5.66 / −5.53 mm | 3 / 3 | upper thigh | 0.14 mm | 0.6 |
| 2.5° | 28.6 mm | 28.9 mm | **−3.87 / −3.79 mm** | 2 / 2 | upper thigh | 0.08 mm | 0.8 |

**Monotonic, unlike the abduction sweep.** That is the root-cause diagnosis
confirming itself: forward travel is along the contact normal, lateral travel was
tangent to it. Clearance improves by a near-constant **3.89 mm per degree**
(3.90, 4.09, 3.97, 3.89 mm/° across the four steps), and the dumbbell barely
rotates — 0.8° of axis change at the largest value, so this is translation, not
a reorientation.

**No tested value clears**, so per the brief I stopped rather than continuing to
larger angles.

## Mid lift, Peak, Mid lower

All remain clear with zero vertices inside at every tested value, and all improve
slightly:

| frame | 0.0° | 1.0° | 1.5° | 2.0° | 2.5° |
|---|---|---|---|---|---|
| Mid lift | 174.56 mm | 183.96 | 188.65 | (clear) | (clear) |
| Peak | 189.41 mm | 189.41 | 189.41 | 189.41 | 189.41 |
| Mid lower | 200.07 mm | 202.65 | 203.94 | (clear) | (clear) |

Peak is unchanged to the last digit because `peakPose` was not touched — the
change lives only at the start/end pose, which is what "Bottom/Return only" is
supposed to mean.

## Technique rules

`validateClip` run over the whole rep at 15 samples/second, 83 frames, for every
tested value:

| flexion | violations | loop closed |
|---|---|---|
| 0.0° | none | yes |
| 1.0° | none | yes |
| 1.5° | none | yes |
| 2.0° | none | yes |
| 2.5° | none | yes |

That covers `elbow_not_inward_l/r`, `elbow_under_shoulder_l/r` and
`shoulder_quiet_l/r` — they are entries in `bicepCurl.technique` and would be
reported here if breached. The shoulder-quiet envelope is `upperarm.x ∈ [−5°,
+10°]`, so 2.5° sits comfortably inside it. **The constraint side is clear the
whole way; it is the geometry that has not cleared.**

## How much would be needed

The relationship is linear enough to extrapolate honestly:

- **~3.5°** for zero clearance (13.59 ÷ 3.89);
- **~4.0°** for a 2 mm practical margin;
- **~4.3°** for 3 mm.

That is about **40 mm** of forward grip travel for zero and **46 mm** for a 2 mm
margin.

This is more than the diagnostic's 14 mm estimate, and the sweep shows why that
estimate was optimistic: it assumed the contact normal was exactly +z. Measured,
only about **0.34 mm of clearance is gained per millimetre of forward travel**
(9.72 mm of clearance for 28.6 mm of travel), because the thigh's front surface
is oblique rather than facing straight forward. The direction was right; the
conversion rate was not.

## Retained

**Nothing.** 2.5° does not give positive clearance on either side, and the brief
is explicit that larger values are not to be tried without reporting first. 4° is
a 60% increase on the largest authorised value, so it needs approval rather than
an assumption.

For what it is worth, 4° would still be inside the authored shoulder envelope,
and the style cost looks small — at 2.5° the elbow moves from z 12 mm to 25 mm
and the grip 28.6 mm forward, which is a slight forward hang rather than a reach.
At 4° that would be roughly 46 mm at the grip. Whether that still reads as the
accepted curl is a judgement for you, and it should be looked at rather than
assumed from numbers.

## Guardrails

Forearm 14.86%, shoulder chain untouched, abduction 3°, elbow-flexion and
supination profiles untouched, 5.5 s timing untouched, clavicle untouched, grip
closure 85%, elbow corrective 0%, dumbbell never translated independently,
`handleGripOffsets` unchanged, topology and weights unchanged, push-up untouched.
Bilateral mismatch stayed ≤ 0.14 mm throughout. The sweep harness is
`scratchpad/repair/flexsweep.test.mts`, outside the tracked tree.

## Status

**Stage 1 is not frozen. Stage 2 has not started.**
