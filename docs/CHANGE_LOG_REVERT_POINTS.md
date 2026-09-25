# Revert points

A plain list of every change made on `chatgpt/absolute-retarget-imports` since the skeleton freeze, newest first, with what each one touched and how to undo it. Every commit here was also pushed to `claude/home-gym-pt-animation-txux66`. Nothing has been merged or promoted.

**Undoing one change** (keeps everything after it): `git revert <commit>`

**Going back to a point** (drops everything after it; do it on a new branch first): `git checkout -b rollback-<name> <commit>`

`AI_CHANGELOG.md` has the full measurements behind each entry.

## Safe points

| Point | Commit | State |
|---|---|---|
| After the reverse lunge | `d3cb716` | 28 exercises, suite 844 / 1. |
| After the farmer's walk | `7c5e6be` | 27 exercises, suite 825 / 1. **Plan steps 1–7 complete.** |
| After the crunch and sit-up | `99d1796` | 26 exercises, suite 806 / 1. Plan step 6 (core flexion) complete. |
| After the forward lunge | `38ae9d0` | 24 exercises, suite 771 / 1. Plan step 5 (stepping lunge) complete. |
| After the cable woodchop | `8d52bbf` | 23 exercises, suite 745 / 1. Plan step 4 (rotation) complete. |
| After reflecting equipment for mirrored characters | `92194bc` | 22 exercises, suite 727 / 1. Character view and GLB export place world equipment on the character's side. |
| After the Russian twist | `9539e25` | 22 exercises, suite 722 / 1. |
| After the bench work | `c5aaedf` | 21 exercises, suite 704 / 1. |
| After the push-up/pull-up templates | `7525ff6` | 19 exercises, suite 664 / 1. Approved push-up and pull-up byte-identical. |
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
| `PENDING` | Mesh coordination report: the full 28-exercise library measured against the production character, accepted V8 and hand candidate V13e; report scripts; importer-diagnostic overflow fixed | No — no runtime or asset change. One test harness fix (`realCharacterDiagnostic.test.ts` computed a maximum by spreading one argument per edge, which overflowed on V13e). | new `docs/MESH_COORDINATION_REPORT.md`, `scripts/mesh-coordination-report.{sh,py}`; `retargeting/realCharacterDiagnostic.test.ts` |
| `d3cb716` | Reverse lunge. **Engine:** a leg's pose-IK target may name the ball of the foot and stand on it (`PoseIKTarget.onBall`), solved as an `onBall` lock is. `lungeFamily`'s `step` option becomes `'forward' \| 'back'`. | No — all twenty-seven byte-identical (no existing target sets `onBall`). The carry export test gained a 60 s timeout (two whole exports; it timed out at 5 s under load). | `exercises/types.ts`, `animation/clip.ts`, `animation/generate.ts`, `animation/pipeline.ts`; `families/lunge*`, new `definitions/reverseLunge.ts`, `definitions/forwardLunge.ts`; library; mirror, feet, squat, carry and self-collision tests |
| `7c5e6be` | Carry family: farmer's walk, walking in place. **Engine:** `ExerciseDefinition.travel` (in-place walking speed, exported as root-node extras); a stepping foot's contact lift measured from its goal's lowest point (heel or ball) | No. Twenty-five clips byte-identical; the forward lunge's contact records differ by one lift value, 7×10⁻¹⁸ m (the same height computed another way). All twenty-six exports byte-identical. | new `families/carry*`, `definitions/farmersWalk.ts`; `exercises/types.ts`, `animation/pipeline.ts`, `export/glb.ts`; library; mirror, ikTiming and self-collision tests |
| `99d1796` | Trunk-flexion family: crunch and sit-up, lying on the floor | No — all twenty-four byte-identical. No engine, rig or equipment change. | new `families/trunkFlexion*`, `definitions/crunch.ts`, `definitions/sitUp.ts`; library; hinge (pivot membership), feet and self-collision tests |
| `38ae9d0` | Forward lunge (the first stepping foot). **Engine:** per-phase timing and lift for pose-IK targets (`MovementPhase.ikTiming`); a pose-IK aim's `forward` survives blending; a leg driven by pose IK reports a lifted floor contact to characters. | No — all twenty-three byte-identical, clips and exports (no existing exercise sets `ikTiming`, aims a pose target, or drives a leg by pose IK). The standing-feet flatness check now skips a foot no lock holds (every existing standing exercise locks both). | `exercises/types.ts`, `animation/clip.ts`, `animation/generate.ts`, `animation/pipeline.ts`, `constraints/types.ts`, `character/retargetContact.ts`; `families/lunge*`, new `definitions/forwardLunge.ts`, new `animation/ikTiming.test.ts`; library; feet, squat, mirror and self-collision tests |
| `4ff2eec` | **Engine (display/export):** a foot standing on its ball reports its ankle, not its ball, as its contact, so a character stands where the rig does | Poses: no, all twenty-three byte-identical. Contact records and the character's feet: yes, for the standing and dumbbell calf raises (both feet were drawn 14 cm forward) and the split squat (back foot 7.5 cm); their GLB exports change with them. The other nineteen exports byte-identical. | `animation/pipeline.ts`; `families/calf.test.ts` |
| `8d52bbf` | Rotation family: cable woodchop (standing, high to low) | No — all twenty-two byte-identical. No engine, rig or equipment change. | `families/rotation*`, new `definitions/cableWoodchop.ts`; library; mirror, feet and self-collision tests |
| `92194bc` | **Engine (display/export):** equipment the rig places in world space is reflected into a mirrored character's world — Character view, GLB export and the production clearance gate | Clip data: no, all twenty-two byte-identical. Exported GLBs: twenty byte-identical, including the approved push-up and pull-up; the Pallof press's tower, handle and cable move to the character's side; the pushdown's bar is written as its (identical) mirror image. Skeleton view unchanged. | new `equipment/mirror*`; `character/types.ts`, `character/retargetSource.ts`, `viewer/EquipmentView.tsx`, `export/glb.ts`, `exercises/equipmentClearance.test.ts` |
| `9539e25` | Rotation family: Russian twist, seated on the floor. Longer timeouts on three whole-library tests. | No — all twenty-one byte-identical. No engine, rig or equipment change; the timeout change alters no assertion. | new `families/rotation*`, `definitions/russianTwist.ts`; library; mirror (asymmetric list and its honesty check), anti-rotation, feet and self-collision tests; `rig/palm.test.ts`, `rig/scapula.test.ts`, `muscles/muscles.test.ts` (timeouts) |
| `c5aaedf` | Supine family: dumbbell bench press and dumbbell fly, lying on the flat bench | No — all nineteen byte-identical. No engine or equipment change. | new `families/supine*`, `definitions/dumbbellBenchPress.ts`, `definitions/dumbbellFly.ts`; library; press, feet and self-collision tests |
| `7525ff6` | Push-up and pull-up re-expressed as the horizontal-press and vertical-pull family templates | No — all nineteen byte-identical, including both approved exercises | new `families/horizontalPress*`, `families/verticalPull*`; `definitions/pushUp.ts`, `definitions/pullUp.ts` |
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
