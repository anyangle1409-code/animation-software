# Revert points

A plain list of every change made on `chatgpt/absolute-retarget-imports` since the skeleton freeze, newest first, with what each one touched and how to undo it. Every commit here was also pushed to `claude/home-gym-pt-animation-txux66`. Nothing has been merged or promoted.

**Undoing one change** (keeps everything after it): `git revert <commit>`

**Going back to a point** (drops everything after it; do it on a new branch first): `git checkout -b rollback-<name> <commit>`

`AI_CHANGELOG.md` has the full measurements behind each entry.

## Safe points

| Point | Commit | State |
|---|---|---|
| After the split squat | `4f6b0a5` | 13 exercises, suite 551 / 1. |
| After the squat stance rework | `0349b4f` | 12 exercises, suite 533 / 1. Squat feet flat, knees tracking. |
| Before the squat stance rework | `70b5174` | 12 exercises, suite 533 passed / 1 skipped. Squat feet recorded as a known defect. |
| Before any new exercise families | `614033b` | 7 exercises, suite 426 / 1. Mirrored hand-roll fix in; skeleton frozen at `19ca602`. |
| Skeleton freeze | `19ca602` | 63-bone `hgpt_canonical_v3`. |

## Changes

| Commit | What | Changed behaviour of existing exercises? | Files |
|---|---|---|---|
| `4f6b0a5` | Bodyweight split squat (lunge family); foot-on-its-ball contact; **toe joint limit 60° → 80°**; last-keyframe phase fix | No — all twelve byte-identical | new `families/lunge*`, `definitions/splitSquat.ts`; `ik/solve.ts`, `ik/types.ts`, `constraints/locks.ts`, `constraints/types.ts` (`onBall`); `rig/humanoid.ts` (toe limit); `animation/clip.ts`; `stance.ts`; tests |
| `0349b4f` | **Squat stance rework (approved, option A).** Feet pinned flat at 12°, knees aimed along the feet, shin rotation in the leg solver | **Yes — the squat only**: knees up to 64 mm further out, toes no longer through the floor. The other eleven are byte-identical. To undo just this: `git revert 0349b4f`. | `ik/solve.ts` (tibial rotation), `exercises/stance.ts` (`kneesOverToes`), `families/squat.ts`, `squat.test.ts`, `feet.test.ts` |
| `70b5174` | Overhead dumbbell triceps extension (elbow-extension family) | No — all byte-identical | new `families/extension*`, `definitions/overheadExtension.ts`; library, feet test, self-collision baseline |
| `1f9f09f` | Incline dumbbell curl; **incline bench geometry reshaped** (backrest hinge, 44 cm × 28 cm seat); per-pad support contact check | No — all byte-identical. The incline bench's drawn shape changed (no earlier exercise used it). | `families/curl.ts`, `equipment/geometry.ts`, `equipment/library.ts`, `constraints/collision.ts` (`equipmentPartDistances`), clearance test |
| `e6b5e81` | Seated dumbbell shoulder press; `supportsBody` equipment; `seatedStance`, `flatFootAim` | No — all byte-identical | `families/press.ts`, `stance.ts`, `equipment/types.ts`, clearance test |
| `8e24345` | Dumbbell bent-over row (horizontal-pull family) | No — all byte-identical | new `families/row*`, `definitions/bentOverRow.ts` |
| `4438bf2` | Whole-foot test for standing exercises; squat recorded as a known defect | No — test only | new `exercises/feet.test.ts` |
| `42eaa97` | Dumbbell Romanian deadlift (hinge family); root pivot, flat-foot locks, knee pole; heel rule shared | No — all byte-identical | `rig/pose.ts`, `animation/clip.ts`, `animation/generate.ts`, `constraints/locks.ts`, `constraints/types.ts`, `exercises/stance.ts`, `families/squat.ts` (heel rule moved, identical) |
| `614033b` | Mirrored-character hand-roll fix | Production character's hands (5.5° roll corrected) | `retargeting/retarget.ts`, `character/retargetSource.ts` |
