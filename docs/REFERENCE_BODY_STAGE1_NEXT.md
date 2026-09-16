# Stage 1 — next decision before Stage 2

**Branch:** `chatgpt/absolute-retarget-imports`  
**Current Stage 1 head before this note:** `81a6e0259a1c92499046fba2de77c2d59f46b2e3`  
**Do not promote, merge, or start Stage 2 yet.**

Stage 1 itself is accepted in principle: the forearm proportion correction is sound, the hand/wrist repair does not regress, weights/topology remain unchanged, strain is flat or better, and the accepted curl/press motion was not rewritten. The one blocker before Stage 2 is the curl-bottom dumbbell/thigh contact.

## Immediate next task

Keep the Stage 1 forearm candidate and clear the curl-bottom dumbbell/thigh overlap **without changing the curl motion or the forearm correction**.

Re-derive the dumbbell placement / grip-centre rule for the corrected anatomy. Treat this as equipment/contact calibration, not an animation change.

### Hard guardrails

Do not:

- shorten/revert the corrected forearm;
- change the accepted curl joint motion, timing, or sequencing;
- change global grip closure from **85%**;
- change elbow corrective from **0%**;
- manually translate the dumbbell until one frame happens to look clear;
- alter weights, retargeting, or topology unless a new measured regression proves it necessary;
- start the shoulder-width Stage 2 in the same pass;
- fix the push-up hand-placement issue yet.

Any equipment/contact change must be derived from the existing anatomical/grip rules and remain bilateral and deterministic.

## Curl contact validation

After recalibrating placement, validate the same dumbbell through the full retained curl review sequence:

- Bottom — 0.00 s
- Mid lift — 1.00 s
- Peak — 2.00 s
- Mid lower — 4.00 s
- Return — 5.00 s

At each frame check both sides for:

- dumbbell/thigh clearance;
- handle centred naturally in the palm;
- thumb and all four fingers forming a secure wrap;
- palm loading/contact appearance;
- rigid dumbbell transform;
- bilateral symmetry;
- no wrist/elbow/shoulder compensation.

The goal is not merely to improve the −13.85/−13.99 mm bottom reading. The retained calibration should remove or reduce the contact to a genuinely negligible visual/geometry value **without creating a worse collision elsewhere in the rep**.

Use the corrected thigh-contact harness from `docs/REFERENCE_BODY_STAGE1_FOREARM.md`; do not use the old name-pattern version that accidentally measured the grip because `GLTFLoader` sanitises `DEF-hand.L` to `DEF-handL`.

## Cross-exercise check

If the changed placement rule is shared by the shoulder press or another dumbbell exercise, re-check those exercises before retaining it. In particular confirm:

- shoulder press rack position still reads naturally;
- overhead dumbbells remain centred and rigid;
- grip geometry remains inside the established envelope;
- no new body/equipment intersections appear.

Do not modify shoulder-press motion merely to preserve the old world-space dumbbell position.

## Stage 1 sign-off criteria

Stage 1 can be frozen as the baseline for Stage 2 only when all of the following are true:

1. corrected forearm proportion remains `14.86%` of figure height;
2. upper arm and shoulder chain remain untouched;
3. curl motion/timing remains unchanged;
4. grip closure remains 85% and elbow corrective remains 0%;
5. curl dumbbell/thigh contact is acceptably cleared across the entire rep, not just Bottom;
6. grip/palm/thumb appearance remains secure and natural;
7. no shoulder-press regression from shared equipment logic;
8. hand/wrist deformation remains no worse than the Stage 1 result;
9. typecheck/build and relevant focused tests pass; do not weaken thresholds.

Do not rerun expensive unrelated validation repeatedly while tuning. Use focused contact/grip checks during iteration, then run the full retained Stage 1 validation once for the final calibration.

## Push-up remains deferred

Stage 1 improved true top-position wrist extension from `102.66°` to `95.45°`, but this is still excessive. Do **not** fix it in this calibration pass.

Stage 2 will widen the shoulder chain and change shoulder-to-hand geometry again, so push-up hand placement should be solved **after Stage 2** against the final proportions. Re-measure it then rather than calibrating it twice.

## After Stage 1 contact is clean

Freeze the forearm + equipment/contact result as the Stage 1 baseline, then proceed to the already-approved Stage 2 direction in `docs/REFERENCE_BODY_TWO_STAGE_DECISION.md`:

- widen the canonical shoulder system and source character together;
- do not fake shoulder width with deltoid inflation;
- re-derive contacts from rules again after the shoulder change;
- fully revalidate curl, press, push-up, pull-up, squat, grip and deformation;
- only then address the remaining push-up hand-placement/wrist-extension issue.

Target sequence:

**forearm correction → curl equipment/contact calibration → Stage 1 sign-off → Stage 2 shoulder widening → full contact/deformation validation → push-up hand-placement fix**

## Report before Stage 2

Return concisely with:

- final Stage 1 candidate filename + SHA-256;
- exact equipment/grip calibration change retained;
- curl dumbbell/thigh clearance at Bottom, Mid lift, Peak, Mid lower and Return, both sides;
- confirmation curl motion is byte/numerically unchanged;
- grip/palm/thumb result;
- shoulder-press cross-check if shared logic changed;
- focused/full validation result;
- branch HEAD;
- explicit statement that Stage 2 has not yet started.

**Do not promote or merge.**
