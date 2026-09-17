# Phase 4 — forearm twist-distribution authorization

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting HEAD:** `c1b737fbbdeaa14d1c283032bab77f8b51306aa4`  
**Stage 2 is locked. Phase 3 has passed. Phase 5 has not started. Do not promote or merge.**

This file authorises the next Phase 4 implementation step after the root-cause pass proved that the push-up forearm collapse is caused by missing twist distribution in the retargeted deform-forearm chain, not by skin weights or the retained hand placement.

## Proven state entering this decision

The trustworthy push-up diagnostic now:

- renders the complete skinned surface rather than a skin-weight-filtered triangle subset;
- rasterises all 19,304 triangles;
- uses a forearm-focused camera, joint overlay and floor line;
- visibly shows the wrist at a steep planted-palm angle and the forearm collapsing into a narrow, flattened/faceted strap while the upper arm retains volume.

Placement was tested before weights, as required.

Forward floor-contact sweep:

- `z = 1.24` → about **92.10°** axis angle;
- `z = 1.30` → about **80.32°**;
- `z = 1.34` → about **73.89°**;
- `z = 1.42` → about **63.59°**.

The nominal 70–75° axis-angle band therefore needs roughly +95 to +120 mm of forward movement, but this conflicts with the authored `forearm_vertical` push-up rule: `z = 1.30` already gives about 64.3 mm elbow-to-wrist `dz` against a 60 mm cap.

The retained push-up floor contact is therefore:

- **`z = 1.295`**;
- measured axis angle about **81.18°**;
- all push-up technique rules clean;
- palm planted;
- left/right identical;
- Stage 1 and Stage 2 unaffected.

Do not continue chasing a sub-75° axis angle by moving the hands farther forward. The character carries about **14.62°** of hand-to-forearm offset in the bind pose, so the retained pose represents roughly **66.6° of wrist rotation from rest**. Treat the retained placement as the best technique-compatible result unless the twist fix itself produces new evidence requiring reconsideration.

## Root cause — proven

Measured long-axis twist on the character:

| bone | Push-up Top | Push-up Bottom |
|---|---:|---:|
| `upper_armL` | 53.7° | 69.8° |
| `upper_armL001` | 53.7° | 69.8° |
| `forearmL` | 31.7° | 9.1° |
| `forearmL001` | 31.7° | 9.1° |
| `handL` | 57.7° | 57.7° |

The helper bones carry exactly their parent's twist to the measured precision. They therefore distribute **no axial twist**.

At Push-up Bottom the distal forearm-to-hand change is about **48.6°**, and it is being concentrated at the wrist instead of being wound gradually through the deform forearm chain. This matches the visible flattened/creased strap.

The diagnosis is now:

- **not skin weights**;
- **not hand placement**;
- **not Stage 1 forearm lengthening**;
- **not the v5→v6 hand/wrist repair region**;
- **retargeting/driver twist distribution is the source-level defect**.

Do not reweight the forearm for this Phase 4 fix.

---

# Decision — distribute forearm axial twist in the retargeting layer

Implement the smallest shared retargeting change that allows the deform forearm twist helper to carry an appropriate fraction of the **relative axial twist between the proximal forearm and the final hand orientation**.

The goal is a gradual forearm wind, not a different hand pose.

## Hard constraints

The retained change must:

- preserve the proximal `DEF-forearm.*` / mapped forearm orientation except for the intended helper distribution;
- preserve the final `DEF-hand.*` world orientation/position to measurement tolerance;
- preserve elbow flexion;
- preserve wrist flexion/extension and deviation targets;
- redistribute **axial twist only** through the forearm helper chain;
- preserve the Stage 1 corrected forearm length and bind repair;
- preserve the locked cylindrical grip solver and grip contacts;
- preserve locked Stage 2 shoulder proportions and bind fix;
- keep left/right behaviour symmetric;
- make no skin-weight or topology change;
- make no new push-up placement change beyond the retained `z = 1.295`.

Do not interpolate general bone rotations into the helper. Decompose the relevant relative rotation and apply only the long-axis/twist component needed for the helper.

## Scope

Start with the **forearm twist helper**, because that is the chain with proven visible failure and the measured distal twist step.

Do not change upper-arm helper behaviour merely because it also currently follows its parent. Only extend the shared mechanism to another helper if objective evidence shows that helper has the same anatomical twist-distribution role and the change is required for correct deformation.

The implementation may be reusable/generic internally, but the retained behavioural change must remain evidence-driven rather than blanket-applied to every connected helper.

## Fraction sweep — measure, do not assume 50/50

Do not hard-code an arbitrary half-twist without evidence.

Test a small focused set of forearm-helper twist fractions, initially:

- **0.25**;
- **0.50**;
- **0.75**;

where the fraction means the helper absorbs that fraction of the relevant forearm→hand relative axial twist while the final hand result remains unchanged.

For each candidate, report at Push-up Top and Bottom:

- forearm and helper long-axis twist;
- helper→hand residual twist step;
- final hand transform delta versus baseline;
- wrist extension/rotation-from-rest result;
- palm/floor contact;
- full forearm silhouette from the trustworthy render;
- wrist→forearm and elbow→forearm transition;
- any pinching, flattening, corkscrew or volume loss;
- bilateral agreement.

Choose the **smallest/most conservative distribution that produces a smooth anatomical forearm wind and removes the visible collapse**. Do not optimise a numeric twist fraction in isolation; the complete silhouette is the final arbiter.

If none of 0.25 / 0.50 / 0.75 is satisfactory, refine only around the best measured interval rather than launching a broad search.

---

# Shared-retarget regression validation

Because this fix touches shared retargeting machinery, do not declare Phase 4 complete from the push-up alone.

After selecting one retained twist distribution, validate at minimum:

### Push-up

- Top and Bottom;
- retained `z = 1.295` floor contact;
- planted palms;
- technique rules clean;
- natural forearm volume;
- no flattening, faceting, pinch or corkscrew;
- smooth wrist→forearm and elbow→forearm transitions.

### Locked Stage 1 / Phase 1

- curl Bottom / Mid / Peak / Return;
- full-fist grip contact numbers remain effectively unchanged;
- dumbbell lock remains correct;
- curl Bottom/Return thigh clearance remains clean;
- renderer/exporter agreement remains intact.

### Locked Stage 2 / Phase 3

- shoulder press Bottom / Overhead, including grip;
- pull-up Bottom / Top, including bar grip;
- deepest squat;
- neutral/standing or equivalent non-arm-stressed pose;
- shoulder-width/body-containment results remain unchanged;
- no new forearm/hand deformation in any exercise.

Confirm the final hand pose is not drifting merely because twist has been redistributed upstream.

Use focused tests/renders while selecting the fraction. Run typecheck/build and the full suite once on the retained candidate.

## Phase 4 pass condition

Phase 4 may be locked when all of the following are true:

1. the retained `z = 1.295` push-up placement remains technique-clean and palms remain planted;
2. wrist rotation from the character's bind/rest state is anatomically plausible without forcing the hand beyond the `forearm_vertical` rule;
3. the forearm helper carries a real, measured share of the axial twist rather than copying its parent rigidly;
4. the final hand orientation/position remains effectively unchanged;
5. Push-up Top and Bottom show natural forearm volume with no flattened strap, crease, pinch or corkscrew;
6. wrist→forearm and elbow→forearm transitions are smooth;
7. bilateral symmetry remains clean;
8. no skin-weight change was needed;
9. locked Stage 1/Phase 1 curl and grip remain clean;
10. locked Stage 2 shoulder/body/contact results remain clean;
11. press and pull-up grips remain correct;
12. focused tests, typecheck/build and the final full suite show no new regression.

If a twist-distribution solution cannot satisfy both the push-up silhouette and the locked cross-exercise behaviour while preserving the final hand transform, stop and report the measured conflict. Do not compensate with reweighting or exercise-specific counter-rotations without a new decision.

## After Phase 4

If the above passes, lock Phase 4 and continue automatically to **Phase 5 — final cleanup and review pack** in `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`.

Keep usage low. Do not promote or merge.
