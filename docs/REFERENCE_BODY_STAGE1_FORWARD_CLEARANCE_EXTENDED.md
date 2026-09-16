# Stage 1 — extended forward-clearance test (3.5° / 4.0° / 4.3°)

Executing the extended authorisation in
`docs/REFERENCE_BODY_STAGE1_FORWARD_CLEARANCE.md`. **Nothing retained. No asset
or source change. Stage 1 is not frozen. Stage 2 has not started.** Candidate
remains `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`).

Abduction held at 3° throughout. Only `startPose.upperarm_l/r.x` was varied.

## Clearance — Bottom and Return, identical at every value

| flexion | grip Δz | plate Δz | clearance L / R | inside L / R | region | axis Δ° | L/R mismatch |
|---|---|---|---|---|---|---|---|
| 0.0° (current) | 0.0 mm | 0.0 mm | −13.59 / −13.73 mm | 3 / 3 | upper thigh | 0.0 | 0.13 mm |
| 3.5° | 39.9 mm | 40.4 mm | −6.60 / −6.53 mm | 2 / 2 | upper thigh | 1.1 | 0.07 mm |
| 4.0° | 45.6 mm | 46.1 mm | −1.40 / −1.33 mm | 1 / 1 | upper thigh | 1.3 | 0.07 mm |
| **4.3°** | **49.0 mm** | **49.5 mm** | **+1.74 / +1.82 mm** | **0 / 0** | upper thigh | 1.4 | 0.07 mm |

Elbow world position moves only in z: 12 mm at 0°, 30 mm at 3.5°, 34 mm at 4.3°.

**The sweep is not monotonic across the full range.** 2.5° measured −3.87 mm
last round but 3.5° measures −6.60 mm — worse. The forward sweep samples the
thigh's surface relief exactly as the abduction sweep did; the apparent
"3.89 mm per degree" linearity over 0–2.5° was a smooth local patch, not a law.

So before trusting the 4.3° result I micro-tested the neighbourhood, which the
brief permits when the measurements justify it:

| flexion | clearance L / R | inside |
|---|---|---|
| 4.1° | −0.36 / −0.29 mm | 1 / 1 |
| 4.2° | +0.69 / +0.76 mm | 0 / 0 |
| 4.3° | +1.74 / +1.82 mm | 0 / 0 |
| 4.4° | +2.79 / +2.87 mm | 0 / 0 |

A clean ~1.05 mm per 0.1° gradient, so **4.3°'s positive clearance is real, not
perched on a bump**. 4.4° was measured only to confirm that gradient; it is above
the authorised ceiling and was not a retention candidate. 4.2° clears but at
0.69/0.76 mm is the "barely positive numerical result" the retention rule
excludes, which makes 4.3° the smallest acceptable authorised value.

Mid lift, Peak and Mid lower stay clear with zero vertices inside at every value
and improve: Mid lift 174.6 → 214.9 mm, Mid lower 200.1 → 211.2 mm at 4.3°. Peak
is unchanged to the last digit (189.41 mm) because `peakPose` was never touched.

`validateClip` over the complete 5.5 s loop, 83 frames: **zero violations and a
closed loop at 0°, 3.5°, 4.0°, 4.1°, 4.2° and 4.3°**, covering
`elbow_not_inward_l/r`, `elbow_under_shoulder_l/r` and `shoulder_quiet_l/r`.

## Visual

`11_forward_flexion_bottom.png` — Bottom pose, matched camera and crop, side and
front, at 0°, 3.5°, 4.0° and 4.3°. The side profiles are near
indistinguishable: the arm still hangs relaxed against the torso and there is no
forward reach. On the visual criterion alone, 4.3° passes.

## Why it was not retained

**The authorised mechanism cannot deliver a Bottom/Return-only change in this
exercise.** Applying 4.3° to the start pose and sampling the upper-arm flexion
channel through the rep gives:

| t | 0s | 0.5s | 1.0s | 1.5s | 2.0s | 3.3s | 5.0s | 5.5s |
|---|---|---|---|---|---|---|---|---|
| upperarm.x | 4.300° | 4.300° | 4.300° | 4.181° | 4.000° | 4.000° | 4.300° | 4.300° |

The channel is **flat across the whole rep**. The accepted curl's own character —
the upper arm held at exactly 0° through the first second while the elbow leads,
then drifting to 4° for the squeeze — disappears entirely, because this channel
is driven from the start pose with a 0.55 s delay, so the start value is held
right through the concentric.

That is caught by a committed assertion, `src/animation/animation.test.ts >
"lets the elbow lead while the upper arm stays quiet early in the curl"`, which
requires `upperarm.x` to be 0° at t = 1.0 s to six decimal places, under 4° at
1.5 s, and 4° at 3.3 s. With 4.3° applied it fails. The guardrails forbid
weakening tests, and this test *is* the accepted motion written down, so the
change cannot be retained as authorised.

Grip forward travel of 49 mm at Bottom therefore comes with 29.8 mm of forward
travel at Mid lift, which is the "new forward drift through the main lifting
phase" the blend requirement rules out.

## What this leaves

Three routes, none of which I can take without a decision:

1. **Add a dedicated keyframe** so `upperarm.x` returns to 0° by t ≈ 1.0 s.
   Bottom/Return would clear and the early-lift assertion would hold — but it
   introduces a 4.3° upper-arm sweep during the first second, which is new
   upper-arm motion in the phase the accepted curl deliberately keeps quiet, and
   is the opposite of the "smallest temporal window, no angular-velocity
   discontinuity" requirement.
2. **Accept the flattened channel.** Overall the upper arm moves *less*, not
   more — 4.3° → 4.0° → 4.3° instead of 0° → 4° → 0°. But it changes the
   accepted look and requires amending a committed test that encodes it, which
   is your call, not mine.
3. **Clear the contact somewhere other than the curl pose** — the remaining
   levers are the dumbbell's dimensions or the grip's orientation, both
   explicitly locked.

My own read: route 2 is the honest one if the flattened upper arm still looks
right to you, because it reduces upper-arm movement rather than adding it and
the rendered Bottom pose is visually unchanged. But it means consciously
retiring the "upper arm quiet at 0° early" property of the accepted curl, and
the test that guards it, and that is a motion-design decision.

## Guardrails

Forearm 14.86%, shoulder chain untouched, abduction 3°, elbow-flexion profile
(6° → 126°), 5.5 s timing, supination, clavicle, grip closure 85%, elbow
corrective 0%, `handleGripOffsets`, dumbbell rigidity, topology and weights all
unchanged. The dumbbell was never independently moved. No test or threshold was
weakened. Push-up untouched. Suite is back to 292 passed / 1 skipped / 1 failed
(the pre-existing `strainReview` timeout) with the source reverted.

## Status

**Stage 1 is not frozen. Stage 2 has not started.**
