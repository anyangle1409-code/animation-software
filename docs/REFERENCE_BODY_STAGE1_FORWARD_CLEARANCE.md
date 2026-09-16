# Stage 1 — authorised forward-clearance test before Stage 2

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting head:** `9535756a5b19821f17e7926ba3b92a53f315c530`  
**Do not promote, merge, freeze Stage 1, or start Stage 2 yet.**

Current candidate remains:

- `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
- SHA-256 `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`

The root-cause diagnostic in `docs/REFERENCE_BODY_STAGE1_CONTACT_DIAGNOSTIC.md` established the remaining Bottom/Return dumbbell contact is on the **front surface of the upper thigh**. The contact normal is approximately `+z` (forward). Shoulder abduction moves the arm mainly in `+x`, tangent to that surface, so the plate slides across the thigh instead of lifting away from it.

The prior non-monotonic abduction sweep is therefore understood and must not be used to choose a retained angle. The required escape direction is forward, not lateral.

## Authorisation

Permission is granted to test a **narrow, isolated shoulder-flexion correction at Curl Bottom/Return only**.

This is not permission to redesign the curl.

Keep the current curl abduction at **3°**. Do not use additional abduction as the clearance mechanism.

The next variable to test is the curl start/end shoulder-flexion channel (`startPose.upperarm_l/r.x` or the exact equivalent identified in the current exercise definition).

The diagnostic estimate is that about **14 mm** of forward grip translation is required to remove the current penetration, and about **20 mm** provides a sensible practical margin. Because the hand hangs roughly 0.55 m below the shoulder, approximately 2° of shoulder flexion is expected to produce about 19 mm of forward movement. That estimate is only a starting point; the retained value must come from real geometry.

## Minimal test sweep

Test, without retaining until measured:

- current baseline: 0° additional shoulder flexion;
- +1.0°;
- +1.5°;
- +2.0°;
- +2.5°.

If 2.5° still does not produce reliable positive clearance on both sides, stop and report before testing materially larger values. Do not continue increasing the angle blindly.

For every value, measure **both left and right** at:

- Bottom;
- Return.

Also re-check the already-clear frames:

- Mid lift;
- Peak;
- Mid lower.

Use the real Stage 1 character, character-specific `handleGripOffsets`, real dumbbell geometry and the corrected body-contact diagnostic.

## Required measurements

For each test value record at minimum:

- shoulder-flexion value;
- grip-centre forward (`z`) displacement versus the current Bottom pose;
- inboard plate forward displacement;
- closest plate-to-thigh signed distance, L/R;
- number of body/thigh vertices inside the plate, L/R;
- exact nearest body region;
- elbow world position;
- grip-centre world position;
- dumbbell orientation delta versus the current pose;
- bilateral mismatch.

The retained value, if any, is the **smallest tested shoulder-flexion change** that gives genuine positive plate/thigh clearance on both sides with a modest practical margin and no worse contact elsewhere in the rep.

Do not choose an angle because it looks good from one camera.

## Motion guardrails

All of the following must remain unchanged except for the specifically authorised minimal Bottom/Return shoulder-flexion clearance term:

- forearm proportion: **14.86% of figure height**;
- shoulder-chain bind geometry and Stage 2 shoulder width;
- curl abduction: **3°**;
- elbow-flexion profile, including the accepted 6° → 126° movement;
- 5.5 s timing / rep structure;
- forearm supination profile;
- accepted clavicle depression/behaviour;
- grip closure: **85%**;
- elbow corrective: **0%**;
- dumbbell rigidity relative to the hand;
- left/right symmetry;
- character-aware `handleGripOffsets` result;
- topology, weights and Stage 1 forearm bind correction.

Do not translate the dumbbell independently to create clearance.

## Blend requirement

If a shoulder-flexion value is retained, apply it only where needed around Bottom/Return and blend it smoothly into the already accepted trajectory.

Do not introduce a visible shoulder jerk or a new upper-arm motion through the main lifting phase.

The final curve must return exactly and symmetrically on the eccentric so Return matches Bottom.

Use the smallest temporal window that gives a natural transition, but do not create a discontinuity in angular velocity.

## Technique constraints to re-check

Explicitly re-run and report the existing technique checks that could be affected by forward shoulder flexion, including the exact current rule names for:

- `elbow_not_inward_*`;
- `elbow_under_shoulder_*`;
- any shoulder-quiet / shoulder-position envelope relevant to the curl.

The proposed ~2° change is expected to remain inside the existing `shoulder_quiet_*` range of approximately `[-5°, +10°]`, but this must be verified, not assumed.

Also verify:

- handle remains centred in the fist;
- finger/thumb grip remains natural;
- wrist angle does not materially regress;
- elbow silhouette remains natural at Bottom and through the transition;
- dumbbell does not create a new contact with the hip, pelvis or opposite body region;
- Mid lift, Peak and Mid lower remain comfortably clear.

## Acceptance rule

A retained forward-clearance correction is acceptable only if all are true:

1. Bottom and Return have genuine positive plate/thigh clearance on both sides;
2. a small practical margin remains rather than exactly zero clearance;
3. the retained angle is the smallest tested value meeting that condition;
4. no new collision appears at Mid lift, Peak or Mid lower;
5. `elbow_not_inward_*`, `elbow_under_shoulder_*` and shoulder-envelope checks still pass;
6. curl timing, elbow flexion, supination, clavicle behaviour, 85% grip and 0% corrective remain unchanged;
7. the change looks anatomically normal — no obvious forward shoulder reach or altered curl style;
8. bilateral symmetry remains negligible;
9. hand/wrist deformation remains no worse than current Stage 1;
10. focused tests pass without weakening thresholds.

If the smallest clearing value visibly changes the style of the curl or violates technique constraints, stop and report instead of forcing sign-off.

## After the clearance test

If the minimal forward-flexion correction satisfies the acceptance rule:

1. retain that one change;
2. re-run the full Stage 1 validation once;
3. update the Stage 1 documentation/change log;
4. freeze Stage 1 only if every previous sign-off criterion is now met.

Only **after Stage 1 is frozen** may Stage 2 shoulder widening begin.

Do not fix the remaining push-up wrist/hand-placement issue yet; that remains deferred until after Stage 2.

## Report before any Stage 2 work

Return concisely with:

- branch HEAD;
- exact shoulder-flexion values tested;
- clearance table for Bottom/Return, L/R;
- retained value, if any, and why it was the minimum;
- measured forward grip/plate displacement;
- confirmation Mid/Peak/Mid-lower remain clear;
- technique-rule results (`elbow_not_inward_*`, `elbow_under_shoulder_*`, shoulder envelope);
- confirmation all other accepted curl mechanics are unchanged;
- deformation/strain/focused-test result for the retained value;
- final Stage 1 candidate filename + SHA-256 if the asset changes;
- explicit statement whether Stage 1 is frozen;
- explicit statement that Stage 2 has not started.

**Do not promote or merge.**
