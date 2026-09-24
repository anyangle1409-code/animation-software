# Revert points

A plain list of every change made on `chatgpt/absolute-retarget-imports` since the skeleton freeze, newest first, with what each one touched and how to undo it. Every commit here was also pushed to `claude/home-gym-pt-animation-txux66`. Nothing has been merged or promoted.

**Undoing one change** (keeps everything after it): `git revert <commit>`

**Going back to a point** (drops everything after it; do it on a new branch first): `git checkout -b rollback-<name> <commit>`

`AI_CHANGELOG.md` has the full measurements behind each entry.

## Safe points

| Point | Commit | State |
|---|---|---|
| After the push-up/pull-up templates | `PENDING` | 19 exercises, suite 664 / 1. Approved push-up and pull-up byte-identical. |
| After the Pallof press | `0c212be` | 19 exercises, suite 658 / 1. |
| After the calf raises | `e456c64` | 18 exercises, suite 639 / 1. |
| After the shoulder raises | `8ad49d4` | 16 exercises, suite 607 / 1. |
| After the cable pushdown | `a6b9154` | 14 exercises, suite 572 / 1. Cable equipment in. |
| After the split squat | `4f6b0a5` | 13 exercises, suite 551 / 1. |
| After the squat stance rework | `0349b4f` | 12 exercises, suite 533 / 1. Squat feet flat, knees tracking. |
| Before the squat stance rework | `70b5174` | 12 exercises, suite 533 passed / 1 skipped. Squat feet recorded as a known defect. |
| Before any new exercise families | `614033b` | 7 exercises, suite 426 / 1. Mirrored hand-roll fix in; skeleton frozen at `19ca602`. |
| Skeleton freeze | `19ca602` | 63-bone `hgpt_canonical_v3`. |

## Changes

| Commit | What | Changed behaviour of existing exercises? | Files |
|---|---|---|---|
| `PENDING` | Push-up and pull-up re-expressed as the horizontal-press and vertical-pull family templates | No — all nineteen byte-identical, including both approved exercises | new `families/horizontalPress*`, `families/verticalPull*`; `definitions/pushUp.ts`, `definitions/pullUp.ts` |
| `0c212be` | Anti-rotation family: cable Pallof press (first use of pose-level hand IK); cable tower mid pulley; two-hand grips on the cable handle | No — all eighteen byte-identical. The cable tower's drawn shape gained a mid pulley (the pushdown's tower shows it). | new `families/antiRotation*`, `definitions/pallofPress.ts`; `equipment/geometry.ts`, `equipment/library.ts`; library; mirror, press, feet and self-collision tests |
| `e456c64` | Calf family: standing and dumbbell calf raise; **`onBall` without an ankle now holds the knee** (engine) | No — all sixteen byte-identical, including the split squat | new `families/calf*`, `definitions/calfRaise.ts`, `definitions/dumbbellCalfRaise.ts`; `ik/solve.ts`, `ik/types.ts`, `constraints/locks.ts`, `constraints/types.ts`; library; squat/lunge/raise membership tests; feet and self-collision tests |
| `8ad49d4` | Shoulder-raise family: dumbbell lateral raise, dumbbell front raise; `'shoulders'` category | No — all fourteen byte-identical | new `families/raise*`, `definitions/lateralRaise.ts`, `definitions/frontRaise.ts`; `exercises/types.ts` (category); library; feet and self-collision tests |
| `a6b9154` | Cable triceps pushdown (extension family, `pushdown` position); cable tower, straight cable bar, stretching `cable` item (`attachment.mode: 'cable'`, `EquipmentTransform.scale`); **GLB export now keeps static equipment's rotation** | No — all thirteen byte-identical. Export only: the incline curl's bench now exports turned to face the lifter, as the studio shows it. | `equipment/types.ts`, `geometry.ts`, `library.ts`, `attach.ts`; `viewer/EquipmentView.tsx`; `export/clipBuilder.ts`, `export/glb.ts`; `editor/panels/EquipmentPanel.tsx`; `families/extension.ts`, new `definitions/cablePushdown.ts`; tests |
| `4f6b0a5` | Bodyweight split squat (lunge family); foot-on-its-ball contact; **toe joint limit 60° → 80°**; last-keyframe phase fix | No — all twelve byte-identical | new `families/lunge*`, `definitions/splitSquat.ts`; `ik/solve.ts`, `ik/types.ts`, `constraints/locks.ts`, `constraints/types.ts` (`onBall`); `rig/humanoid.ts` (toe limit); `animation/clip.ts`; `stance.ts`; tests |
| `0349b4f` | **Squat stance rework (approved, option A).** Feet pinned flat at 12°, knees aimed along the feet, shin rotation in the leg solver | **Yes — the squat only**: knees up to 64 mm further out, toes no longer through the floor. The other eleven are byte-identical. To undo just this: `git revert 0349b4f`. | `ik/solve.ts` (tibial rotation), `exercises/stance.ts` (`kneesOverToes`), `families/squat.ts`, `squat.test.ts`, `feet.test.ts` |
| `70b5174` | Overhead dumbbell triceps extension (elbow-extension family) | No — all byte-identical | new `families/extension*`, `definitions/overheadExtension.ts`; library, feet test, self-collision baseline |
| `1f9f09f` | Incline dumbbell curl; **incline bench geometry reshaped** (backrest hinge, 44 cm × 28 cm seat); per-pad support contact check | No — all byte-identical. The incline bench's drawn shape changed (no earlier exercise used it). | `families/curl.ts`, `equipment/geometry.ts`, `equipment/library.ts`, `constraints/collision.ts` (`equipmentPartDistances`), clearance test |
| `e6b5e81` | Seated dumbbell shoulder press; `supportsBody` equipment; `seatedStance`, `flatFootAim` | No — all byte-identical | `families/press.ts`, `stance.ts`, `equipment/types.ts`, clearance test |
| `8e24345` | Dumbbell bent-over row (horizontal-pull family) | No — all byte-identical | new `families/row*`, `definitions/bentOverRow.ts` |
| `4438bf2` | Whole-foot test for standing exercises; squat recorded as a known defect | No — test only | new `exercises/feet.test.ts` |
| `42eaa97` | Dumbbell Romanian deadlift (hinge family); root pivot, flat-foot locks, knee pole; heel rule shared | No — all byte-identical | `rig/pose.ts`, `animation/clip.ts`, `animation/generate.ts`, `constraints/locks.ts`, `constraints/types.ts`, `exercises/stance.ts`, `families/squat.ts` (heel rule moved, identical) |
| `614033b` | Mirrored-character hand-roll fix | Production character's hands (5.5° roll corrected) | `retargeting/retarget.ts`, `character/retargetSource.ts` |
