# Stage 1 sign-off decision before Stage 2

**Branch:** `chatgpt/absolute-retarget-imports`  
**Current investigation head before this note:** `a896db2c9b166eb100be6a02d679e79a54155cf6`  
**Do not promote, merge, or start Stage 2 yet.**

This decision follows the curl-contact investigation at `a896db2`.

## What the latest investigation established

The Stage 1 forearm correction itself remains sound and should be kept:

- forearm proportion remains corrected to the canonical-rig target;
- shoulder chain is still untouched;
- accepted curl and press motion were not rewritten;
- grip closure remains **85%**;
- elbow corrective remains **0%**;
- hand/wrist deformation remains clean;
- strain/build/test state remains acceptable apart from the known pre-existing timeout;
- under the constraint pipeline's established grip rule, Stage 1 is actually the least-overlapping and most symmetric of v7, refmatch and Stage 1.

The remaining issue is not a simple Stage-1-regression calibration problem. Two separate defects are now visible:

1. **Grip-frame divergence:** renderer/exporter/constraint paths do not all resolve the dumbbell from the same character-specific grip frame.
2. **Real curl-bottom geometry contact:** even with a correct grip centre, the hand sits only a few millimetres from the thigh while the inboard dumbbell plate extends ~92.5 mm from the grip centre. The plate therefore penetrates the thigh at Bottom/Return unless the arm path provides some lateral clearance.

Do not confuse these two problems.

## Decision and required order

Proceed in this order only:

1. Fix the **grip-frame single source of truth** first.
2. Re-measure curl contact using that unified rule.
3. If plate/thigh contact remains at Bottom/Return, add the **minimum anatomically plausible curl-bottom arm abduction** required for clearance.
4. Revalidate Stage 1 completely.
5. Only after Stage 1 is signed off may Stage 2 shoulder widening begin.

Do not start Stage 2 while either grip-frame divergence or curl-bottom clearance is unresolved.

---

## Part A — fix grip-frame divergence first

The current paths disagree:

- viewer/exporter currently add a shipped literal such as `{0, 0.045, 0}`;
- `resolveEquipment` uses `anatomicalGripOffset`;
- the imported character already carries its own `gripFrameOffsets`.

The investigation proved that simply replacing the shipped literal with `anatomicalGripOffset` is wrong for this character: it rendered the handle outside the fist even though focused tests passed.

### Required behaviour

Make the character-specific grip frame the authoritative basis for equipment placement.

Do **not** stack a canonical-hand offset on top of a character-specific grip frame unless the offset is explicitly defined in that frame and validated against the wrapping fingers.

The renderer, exporter, diagnostics and constraint solver should agree on the same resolved grip transform for the same character and pose.

### Guardrails

Do not:

- use `anatomicalGripOffset` blindly for the imported character;
- retain two different grip-centre definitions that merely happen to look similar;
- move the dumbbell by eye until one frame looks correct;
- change the Stage 1 skeleton or forearm length;
- change grip closure from 85%;
- change elbow corrective from 0%;
- change accepted curl timing/elbow-flexion/supination/clavicle behaviour during this step.

### Validation for the unified grip rule

Prove with the real character that:

- handle centre sits naturally inside the closed fist;
- palm loading reads correctly;
- thumb and all four fingers wrap the handle plausibly;
- left/right result mirrors correctly;
- renderer, exporter and solved/diagnostic equipment transforms agree numerically to a negligible tolerance;
- shoulder press and other dumbbell exercises that share the rule do not regress.

Do not treat passing tests as sufficient if the rendered handle is visibly outside the fist.

---

## Part B — re-measure the curl after the grip fix

After the single-source grip transform is retained, re-measure the dumbbell against the thigh at:

- Bottom;
- Mid lift;
- Peak;
- Mid lower;
- Return.

Both sides.

Use real dumbbell geometry and the corrected thigh-contact harness. Record:

- closest plate-to-thigh distance;
- number of thigh vertices inside the plate, if any;
- handle/palm alignment;
- bilateral symmetry.

The Bottom and Return poses are the expected risk. Mid/Peak/Mid-lower should remain comfortably clear.

---

## Part C — if contact remains, allow the minimum real curl abduction

If the correctly rendered/solved dumbbell still intersects the thigh at Bottom/Return, permission is granted to alter the accepted curl **only in this narrowly defined way**:

- add the minimum anatomically plausible upper-arm abduction/lateral clearance required to remove the plate/thigh penetration;
- keep the change focused on Bottom/Return and blend smoothly into the already accepted trajectory;
- preserve the rest of the curl's accepted mechanics.

This is not permission for a curl redesign.

### Must remain unchanged unless the minimum-clearance calculation itself proves otherwise

- elbow flexion profile;
- timing and 5.5 s rep structure;
- forearm supination profile;
- accepted clavicle depression/behaviour;
- grip closure 85%;
- elbow corrective 0%;
- dumbbell rigidity/contact to the hand;
- bilateral symmetry;
- Stage 1 forearm proportion.

### Do not choose an arbitrary angle

Measure a small sweep of candidate abduction values and retain the **smallest** value that gives genuine geometric clearance while still looking natural.

Acceptance should be based on actual plate/thigh geometry, not merely a visual gap in one camera.

The retained motion should not show an obvious "chicken-wing" flare or make the curl look stylistically different from the accepted movement.

---

## Stage 1 final sign-off criteria

Stage 1 may be frozen only when all are true:

1. forearm remains at the corrected canonical-rig proportion;
2. shoulder chain remains untouched;
3. one authoritative character-aware grip-frame rule is used consistently by viewer/exporter/solver/diagnostics;
4. handle sits naturally inside the fist with correct palm/finger/thumb relationship;
5. Bottom and Return plate/thigh penetration is cleared, or reduced to a genuinely negligible non-visible/non-structural value using the minimum justified abduction;
6. Mid lift, Peak and Mid lower remain clear;
7. accepted curl mechanics other than the specifically authorised minimal bottom clearance are unchanged;
8. grip closure remains 85%, elbow corrective remains 0%;
9. shoulder press and shared equipment paths do not regress;
10. hand/wrist repair remains no worse than current Stage 1;
11. strain/diagnostic results remain acceptable;
12. typecheck/build/focused tests pass and the existing known timeout is the only suite failure;
13. Stage 2 has not started.

If criterion 5 cannot be met without an obviously unnatural arm flare, stop and report the minimum tested angle, residual contact and visual trade-off rather than forcing it.

---

## Push-up still remains deferred

Do not fix the remaining push-up wrist/hand-placement issue in this pass.

Stage 1 improved true wrist extension but did not solve it. Stage 2 shoulder widening will change shoulder-to-hand geometry again, so push-up placement must be re-measured and solved after Stage 2 rather than calibrated twice.

---

## After Stage 1 is signed off

Only then proceed to Stage 2 from `docs/REFERENCE_BODY_TWO_STAGE_DECISION.md`:

- widen canonical shoulder rig and source character together;
- do not fake shoulder width with deltoid inflation;
- re-derive contacts again from rules;
- revalidate curl, press, push-up, pull-up, squat, grip and deformation;
- then solve the remaining push-up hand-placement/wrist-extension issue against the final proportions.

Target sequence:

**forearm correction → character-aware grip single source of truth → minimum curl-bottom clearance correction if still required → Stage 1 sign-off → Stage 2 shoulder widening → full validation → push-up fix**

## Report before Stage 2

Return concisely with:

- branch HEAD;
- final Stage 1 candidate filename + SHA-256;
- exact grip-frame source-of-truth change;
- proof renderer/exporter/solver agree;
- handle-in-fist visual/measurement result;
- Bottom/Mid/Peak/Mid-lower/Return plate-thigh clearances for both sides;
- any retained abduction amount and how it was chosen;
- confirmation all other accepted curl mechanics remain unchanged;
- shoulder-press/shared-equipment cross-check;
- deformation/strain/typecheck/test/build result;
- explicit statement that Stage 2 has not started.

**Do not promote or merge.**
