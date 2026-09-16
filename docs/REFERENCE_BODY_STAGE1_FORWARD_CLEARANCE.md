# Stage 1 — authorised forward-clearance test before Stage 2

**Branch:** `chatgpt/absolute-retarget-imports`  
**Current head before this note:** `7bbf12a75a78b8890c693c41bfe6d3bc02bc9f3e`  
**Do not promote, merge, freeze Stage 1, or start Stage 2 yet.**

Current candidate remains:

- `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
- SHA-256 `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`

The root-cause diagnostic established that the remaining Bottom/Return dumbbell contact is on the **front surface of the upper thigh**. The contact normal is primarily forward (`+z`). Shoulder abduction moves the arm mainly laterally (`+x`), tangent to that surface, so it slides the plate across the thigh instead of lifting it away.

The first authorised shoulder-flexion sweep has now confirmed the diagnosis. Nothing from that sweep was retained.

## Evidence from the completed 0–2.5° sweep

Curl abduction remained fixed at **3°**. Only `startPose.upperarm_l/r.x` was varied.

Bottom and Return are identical at every tested value:

| forward shoulder flexion | grip Δz | clearance L / R | vertices inside L / R |
|---:|---:|---:|---:|
| 0.0° | 0.0 mm | -13.59 / -13.73 mm | 3 / 3 |
| 1.0° | 11.4 mm | -9.69 / -9.72 mm | 2 / 2 |
| 1.5° | 17.2 mm | -7.45 / -7.32 mm | 3 / 3 |
| 2.0° | 22.9 mm | -5.66 / -5.53 mm | 3 / 3 |
| 2.5° | 28.6 mm | -3.87 / -3.79 mm | 2 / 2 |

The result is monotonic: approximately **3.89 mm of clearance improvement per degree** over the tested range. The dumbbell axis changes by only about **0.8°** at 2.5°, so this is a translation effect rather than an equipment-orientation workaround.

Mid lift, Peak and Mid lower remain clear at every tested value with zero vertices inside. `validateClip` across the full rep reported zero violations and a closed loop for all tested values, including the existing `elbow_not_inward_*`, `elbow_under_shoulder_*` and `shoulder_quiet_*` checks.

The earlier 14–20 mm forward-travel estimate was optimistic because the thigh's front surface is oblique. The measured conversion is only about **0.34 mm of clearance per millimetre of forward grip travel**.

Extrapolation from the measured sweep indicates roughly:

- **3.5°** for approximately zero clearance;
- **4.0°** for approximately a 2 mm positive margin;
- **4.3°** for approximately a 3 mm margin.

These are predictions only. The retained value must come from real geometry and visual review.

---

## Extended authorisation

Permission is now granted to test exactly these additional Bottom/Return forward-flexion values:

- **3.5°**;
- **4.0°**;
- **4.3°**.

Keep curl abduction fixed at **3°** throughout.

This is still a focused test, not blanket permission to redesign the curl.

### Test all three, but retain only if justified

For each value, measure both sides at Bottom and Return using the real Stage 1 character, character-specific `handleGripOffsets`, real dumbbell geometry and the corrected body-contact diagnostic.

Also verify Mid lift, Peak and Mid lower remain clear.

Record at minimum:

- actual plate-to-upper-thigh signed clearance, L/R;
- number of body vertices inside the inboard plate, L/R;
- forward grip-centre displacement versus the current 0° start pose;
- dumbbell-axis/orientation delta versus the current pose;
- elbow world position;
- bilateral mismatch;
- technique-rule result across the complete 5.5 s loop.

## Visual comparison is mandatory

Produce matched Bottom-pose renders for:

- the current retained curl start pose;
- 3.5°;
- 4.0°;
- 4.3° if it is needed numerically.

Use the same camera/crop/character/equipment so the only visible motion difference is the authorised shoulder-flexion term.

The purpose is to verify that the arm still reads as a natural relaxed dumbbell-curl start rather than a visible forward reach.

Do not select a value from clearance numbers alone.

---

## Retention rule

The retained value must be the **smallest tested angle** that satisfies all of these:

1. genuine positive plate/thigh clearance on both sides at Bottom and Return;
2. preferably at least about **2 mm practical margin**, rather than a barely positive numerical result;
3. zero new collision at Mid lift, Peak or Mid lower;
4. natural-looking relaxed curl start/end pose with no obvious forward reaching;
5. `elbow_not_inward_*`, `elbow_under_shoulder_*` and `shoulder_quiet_*` all still pass through the complete rep;
6. bilateral behaviour remains effectively mirrored;
7. dumbbell remains rigid and correctly seated in the fist;
8. no material wrist/elbow/shoulder deformation regression.

### Expected decision logic

- If **3.5°** unexpectedly gives a stable practical margin on both sides and looks natural, it may be retained because it is the smaller value.
- If 3.5° is approximately zero/too marginal and **4.0°** gives about 2 mm or more on both sides **and looks natural**, retain **4.0°**.
- Use **4.3° only if 4.0° does not produce a reliable practical margin** and 4.3° still looks anatomically natural.
- If 4.0° clears numerically but already reads as an obvious forward reach, **stop instead of forcing 4.3°**.
- If 4.3° still does not meet clearance + visual acceptance, stop and report; do not continue climbing beyond 4.3° without a new decision.

Do not interpolate and retain an untested value unless the measured results explicitly justify a smaller follow-up micro-test first.

---

## Motion guardrails

All of the following remain locked except for the specifically authorised minimal Bottom/Return shoulder-flexion term:

- forearm proportion: **14.86% of figure height**;
- canonical/source shoulder width and Stage 2 shoulder work;
- curl abduction: **3°**;
- elbow-flexion profile, including accepted **6° → 126°** movement;
- 5.5 s rep timing and phase structure;
- forearm supination profile;
- accepted clavicle depression/behaviour;
- grip closure: **85%**;
- elbow corrective: **0%**;
- character-aware `handleGripOffsets`;
- dumbbell rigidity relative to the hand;
- topology and weights;
- Stage 1 forearm bind correction;
- left/right symmetry.

Do not independently translate or rotate the dumbbell to manufacture clearance.

## Blend requirement if a value is retained

The authorised flexion belongs at Bottom/Return only and must blend smoothly into the already accepted trajectory.

- no visible shoulder jerk;
- no discontinuity in angular velocity;
- no new forward drift through the main lifting phase;
- eccentric path must mirror cleanly so Return matches Bottom;
- Peak remains the existing accepted Peak unless objective evidence demands otherwise.

Use the smallest temporal window that looks and measures natural.

---

## Stage 1 sign-off after a successful retained value

If one of the authorised values satisfies the clearance and visual criteria:

1. retain that single minimal motion change;
2. re-run the full Stage 1 validation once;
3. confirm the forearm correction, grip source-of-truth work and hand/wrist repair remain intact;
4. confirm shoulder press/shared dumbbell behaviour remains clean;
5. update the Stage 1 documentation and `AI_CHANGELOG.md` with the retained result;
6. freeze Stage 1 only if all prior Stage 1 sign-off criteria are now met.

Do **not** promote or merge as part of this task.

Stage 2 may begin only after Stage 1 is explicitly frozen and reported clean.

The push-up wrist/hand-placement issue remains deferred until after Stage 2 because shoulder widening will change shoulder-to-hand geometry again.

---

## Report before Stage 2

Return concisely with:

- branch HEAD;
- 3.5° / 4.0° / 4.3° clearance results, L/R;
- inside-vertex counts;
- measured grip forward travel;
- visual verdict for each materially relevant candidate;
- exact retained value, if any, and why it is the minimum acceptable value;
- confirmation Mid lift / Peak / Mid lower remain clear;
- `elbow_not_inward_*`, `elbow_under_shoulder_*`, `shoulder_quiet_*` results;
- confirmation elbow flexion, supination, clavicle behaviour, timing, 85% grip, 0% corrective and 3° abduction remain unchanged;
- hand/wrist deformation and strain result;
- typecheck/test/build result;
- final Stage 1 candidate filename + SHA-256 if changed;
- explicit statement whether Stage 1 is frozen;
- explicit statement that Stage 2 has not started.

**Do not promote or merge.**
