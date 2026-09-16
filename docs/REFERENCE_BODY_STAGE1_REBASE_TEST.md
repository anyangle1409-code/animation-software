# Stage 1 — upper-arm neutral rebase test

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting head:** `b2a82eacaaa7031a0df12b592bed125eadb03b86`  
**Do not promote, merge, freeze Stage 1, or start Stage 2 yet.**

Current candidate remains:

- `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
- SHA-256 `c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`

The extended forward-clearance test in `docs/REFERENCE_BODY_STAGE1_FORWARD_CLEARANCE_EXTENDED.md` proved that **4.3° of forward upper-arm flexion clears the Bottom/Return dumbbell-to-upper-thigh contact** with +1.74 / +1.82 mm clearance, zero vertices inside, negligible bilateral mismatch, and no visible forward reach in the matched renders.

It was not retained because changing only `startPose.upperarm_l/r.x` flattens the authored upper-arm channel across the rep. The accepted curl currently means:

- neutral upper arm early while the elbow leads;
- then about **+4° relative late upper-arm drift** for the squeeze;
- then return to the same neutral baseline.

The existing test encodes that behaviour using absolute zero because the current neutral baseline happens to be 0°. The behavioural intent is the **relative motion**, not the numeric value zero itself.

## Decision

Test a **neutral-baseline rebase** of the existing upper-arm flexion curve by **+4.3°**, preserving the existing relative motion exactly.

This is **not** the flattened 4.3° → 4.0° → 4.3° route, and it is **not** a new keyframe that sweeps the arm back to 0° during the first second.

The test should preserve the accepted curve shape and timing while shifting the whole upper-arm-x curve forward by +4.3°:

| Behaviour | current | rebased test target |
|---|---:|---:|
| early neutral / elbow-lead phase | 0° relative baseline | 4.3° absolute |
| late upper-arm drift | +4° relative | about 8.3° absolute |
| return | 0° relative baseline | 4.3° absolute |

The intended invariant is therefore:

`rebased_upperarm_x(t) = current_upperarm_x(t) + 4.3°`

for the accepted curl upper-arm flexion channel, without changing any other channel.

## Why this is the authorised test

This keeps the accepted motion character intact:

- the upper arm remains **quiet relative to its own start baseline** during the early elbow-led phase;
- the same delayed late drift still occurs;
- the same relative amplitude remains approximately 4°;
- the same timing/easing remains intact;
- the loop returns exactly to the new 4.3° neutral baseline;
- Bottom/Return retain the forward translation that previously gave real plate/thigh clearance.

Do not treat the old absolute 0° value as an anatomical requirement if the same behavioural invariant can be preserved around the corrected neutral pose.

## Test-first requirement

Do **not** retain the rebase immediately.

First implement it as a focused test candidate and prove all of the following.

### 1. Relative-motion preservation

Sample the old accepted curl and the rebased candidate over the full 5.5 s rep.

For `upperarm_l/r.x`, verify the candidate differs from the current accepted curve by approximately **+4.3° at every sampled time** to numerical tolerance.

Also explicitly record at minimum:

- 0.0 s;
- 0.5 s;
- 1.0 s;
- 1.5 s;
- 2.0 s;
- 3.3 s;
- 5.0 s;
- 5.5 s.

The relative late drift and return must remain unchanged.

### 2. Update the behavioural test without weakening it

The existing assertion in `src/animation/animation.test.ts` is named:

`lets the elbow lead while the upper arm stays quiet early in the curl`

Its current absolute checks are tied to the old neutral value:

- upper arm = 0° at 1.0 s;
- late upper arm > 0° and < 4° at 1.5 s;
- early-down upper arm = 4° at 3.3 s.

If the rebase is retained, update this test so it protects the **same behaviour relative to the start-pose baseline** rather than hard-coding zero.

The replacement test should still prove, at minimum:

- elbow flexion at 1.0 s is still >50°;
- upper-arm flexion at 1.0 s is equal/negligibly different from the start baseline on both sides;
- at 1.5 s the upper arm has begun its delayed drift but is still less than the full ~4° relative drift above baseline;
- at 3.3 s the upper arm is about **baseline + 4°**;
- the final Return matches the start baseline exactly.

This is an intentional test generalisation around a new neutral pose, **not permission to weaken the elbow-lead/quiet-upper-arm behaviour**.

If the relative behaviour does not remain equivalent, stop and revert.

### 3. Clearance validation

Re-measure the real Stage 1 character with real dumbbell geometry and `handleGripOffsets` at:

- Bottom;
- Mid lift;
- Peak;
- Mid lower;
- Return.

Both sides.

Require:

- Bottom and Return retain genuine positive plate/thigh clearance;
- no vertices inside the inboard plate;
- Mid lift, Peak and Mid lower remain comfortably clear;
- no new hip/pelvis/groin/body contact appears;
- bilateral mismatch remains negligible.

Do not assume the previous +1.74/+1.82 mm survives the full curve rebase; re-measure it.

### 4. Technique and motion invariants

All of these must remain unchanged except for the +4.3° neutral rebase of upper-arm flexion:

- forearm proportion = **14.86% of figure height**;
- shoulder bind chain / Stage 2 width untouched;
- abduction = **3°**;
- elbow flexion profile = accepted 6° → 126° profile;
- 5.5 s timing and phase structure;
- supination profile;
- clavicle depression/behaviour;
- grip closure = **85%**;
- elbow corrective = **0%**;
- `handleGripOffsets`;
- dumbbell rigidity relative to the hand;
- bilateral symmetry;
- topology, skin weights and Stage 1 forearm bind correction.

Run the existing full technique validation and explicitly confirm:

- `elbow_not_inward_l/r`;
- `elbow_under_shoulder_l/r`;
- `shoulder_quiet_l/r`;
- loop closure.

The projected late absolute value is about **8.3°**, which is still inside the current shoulder-quiet envelope of approximately `[-5°, +10°]`; verify rather than assume.

### 5. Visual acceptance

Produce matched-camera comparisons of **current accepted curve vs rebased curve** at least at:

- Bottom;
- Mid lift;
- Peak;
- Return.

Use side and front where useful.

The rebased version must still read as a normal strict dumbbell curl:

- no visible forward reach;
- no shoulder swing;
- no obvious upper-arm drift during the elbow-led opening phase;
- no changed curl style;
- elbow silhouette natural throughout.

If the ~8.3° late absolute position looks visibly too far forward or otherwise changes the accepted style, stop and do not retain the rebase even if numerical constraints pass.

## Retention rule

Retain the +4.3° neutral rebase only if **all** of these are true:

1. Bottom/Return clear on both sides with a practical positive margin and zero inside;
2. the candidate upper-arm-x curve is the accepted curve plus +4.3° to numerical tolerance;
3. early elbow-led behaviour is preserved relative to the new baseline;
4. the late relative drift remains ~4° with the same timing/easing;
5. loop/Return closes exactly to the new baseline;
6. all existing technique constraints pass;
7. the updated test protects the same behavioural invariant rather than weakening it;
8. the visual comparison still reads as the same strict curl;
9. no contact/deformation/grip regression appears;
10. focused tests, typecheck and build pass without weakened thresholds.

If any condition fails, revert the rebase and report the exact blocker. Do not try a different baseline angle or add extra keyframes in the same pass.

## If retained

If the test passes and the +4.3° rebase is retained:

1. run the complete Stage 1 validation once;
2. update `AI_CHANGELOG.md` and the Stage 1 handoff with the retained motion/test change;
3. report final Bottom/Mid/Peak/Mid-lower/Return clearances, relative upper-arm motion measurements, technique results, deformation/strain, typecheck/test/build, candidate filename/SHA and branch HEAD;
4. **freeze Stage 1 only if every Stage 1 sign-off criterion now passes**.

Only after Stage 1 is frozen may Stage 2 begin.

Do not fix the push-up wrist/hand-placement issue yet.

## Stop point

This authorisation is for **one focused hypothesis only**:

**rebase the existing accepted upper-arm flexion curve by +4.3° while preserving its relative motion exactly.**

Do not test route 1, the flattened route 2, new equipment dimensions, new grip orientation, Stage 2 shoulder widening, or the push-up fix in the same pass.

**Do not promote or merge.**
