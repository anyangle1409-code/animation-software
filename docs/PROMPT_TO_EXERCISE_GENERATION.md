# Prompt-to-exercise generation: the first vertical slice

2026-09-25. This implements phases 8–10 of `SELF_SUFFICIENT_EXERCISE_GENERATION_PLAN.md` for two certified families, curl and overhead press. A typed request becomes a validated candidate in the studio, ready for review.

```
"Create a standing hammer curl with 12 kg dumbbells and controlled tempo."
  → parsePrompt            ExerciseIntent { curl, neutral, standing, 12 kg, controlled }
  → curl adapter           CurlVariant    { grip: 'neutral', mass: 12, tempo, … }
  → curlFamily()           ExerciseDefinition      (the same builder the library uses)
  → generateClip()         StudioClip
  → validateCandidate()    13 checks — fails: dumbbells 17 mm inside the thighs
  → correction loop        upper arms 3° → 12° out; re-validated, confirmed at 13°
  → candidate              every check passes → opened in the studio, READY FOR REVIEW
```

Nothing generated is added to the library. A candidate lives in the session's **Generate** panel until it is discarded or the page reloads. Approving one records that a person has watched it. Promotion stays a deliberate code change: the panel shows the variant as the family call a definition file would contain.

## Where the plan stood before this

| Phase | State before this slice |
|---|---|
| 0 Freeze the foundation | Done: 63-bone skeleton frozen at `19ca602`, suite green, revert log kept. |
| 1 Remove duplication | Done: pose, rule, target, lock, stance and grip presets and mirroring. |
| 2 Family templates | Done, well past curl: 16 family builders, 28 exercises. |
| 3–6 Biomechanics, equipment, collision, motion | Partly done. Equipment geometry is data-driven; contact, grip and IK timing run in production code. The equipment and arm–trunk clearance measurements existed **only inside test files**. |
| 8 Intent and generator | Not started. |
| 9 Solve, validate, auto-correct | Not started: checks were spread over one review module and five test files, and there was no correction loop. |
| 10 Autonomous workflow | Not started: there was no prompt entry. |

## What was added — `src/generation/`

**`slots.ts`, `parse.ts`: request → `ExerciseIntent`.**
- Rule-based and deterministic: the same sentence always gives the same exercise, and every decision can be shown.
- It reads grip, support, bench angle, load (kg or lb), tempo (`controlled`, `slow`, `fast`, or `tempo 3-1-2-0`), execution and implement. Each value keeps the words it came from.
- Defaults are chosen and **written down as assumptions**.
- Generation stops with a question only when the answer would change the exercise:
  - a contradiction, such as "hammer … palms up" or two loads;
  - something no certified family does, such as alternating or single-arm work, a 30° incline, a seated curl, a barbell, preacher or Zottman curls, or a neutral-grip overhead press.
- Every other movement in the library is recognised and declined with its family named ("the lunge family … is not certified for generation yet"). It is never approximated.

**`families.ts`: one adapter per certified family, not per exercise.**
- An adapter holds no angles, poses or rules; those stay in the family builder. It holds:
  - the translation from intent to the builder's typed variant;
  - the library exercise to compare against;
  - the family's **levers**: parameters the correction loop may move, each bounded by what the family already documents, with the reason it is the right lever.
- Grip knowledge the library's hammer and reverse curls wrote per exercise (muscle emphasis, the "rolling to supination" error) is keyed by grip here, so any curl with that grip gets it.
- **Curl:**
  - supinated, neutral or pronated grip; standing or the 45° incline;
  - levers: elbow bend at the bottom, from 16° up to 30° (the family's own clearance lever), and upper-arm abduction, up to 15°.
- **Overhead press:**
  - pronated grip, standing or seated;
  - no lever yet; one will be added when a measured failure shows which parameter resolves it;
  - a neutral grip is refused with the reason recorded in `press.test.ts`: it needs forearm supination at the joint's limit, which is a modelling gap.

**`validate.ts`: one report, the library's own checks at the library's own limits.**

| Check | Source | Limit |
|---|---|---|
| Technique rules, loop closure, IK reachability, locked contacts, dumbbell grip envelope, two-hand fit | `editor/review.ts` `reviewExercise`, at 20 samples/s | the exercise's own rules; 5 mm contact error |
| Joint limits | as `exercises.test.ts` | every rotation inside its bone's limit, locked axes still |
| Lock stillness | as `exercises.test.ts` | 5 mm |
| Feet flat and square | as `feet.test.ts` | toe height 1 mm, direction 0.25° |
| Duration, rule and muscle references | as `exercises.test.ts` | exact |
| Equipment clears the body | `constraints/bodyClearance.ts` (moved out of `equipmentClearance.test.ts`, which now calls it) | 2 mm off legs and trunk; a pad reached within 3 mm and pressed ≤ 15 mm |
| Arms clear the trunk | `constraints/bodyClearance.ts` (moved out of `selfCollision.test.ts`) | within 1 mm of the reference library exercise, measured live on the same character |

- The two body checks need a character. Without one they are reported as **not run**, and the candidate is **unverified**, never passed.
- The arm–trunk check is the only one that needs a reference. The library holds each exercise to its own recorded separation, because real arms rest on real chests. A candidate is held to its nearest library exercise, measured on the same character, so the comparison is like for like whichever body is loaded.

**`generate.ts`: the pipeline and the bounded correction loop.**
- When a check fails, the loop walks a lever that can resolve it one step at a time. The lever resolving the most failures goes first, so one change is preferred to two.
- A lever stops when a step breaks a check that was passing.
- A value is accepted only if the checks it fixed still pass **one step further on**. Clearance can be a ridge: the reverse curl measured 0.79, 2.39, 4.21, 5.70, 0.47 and −4.76 mm across 4–6.5° of abduction.
- There are at most 3 rounds and a budget of 40 validations. After the loop the full report runs again.
- The loop can only write variant fields, through a lever, inside its bound. It never sees a limit, so it cannot loosen one.
- Every attempt is recorded with what it measured.
- The pipeline is a generator: tests and tools run it straight through, and the UI yields between measurements to show progress.

**UI.**
- A **Generate** tab (right panel) has a prompt box, example requests, live progress and the candidate's report:
  - what the request was understood as, and the defaults it assumed;
  - the corrections, with every attempt;
  - all checks, and the generated source;
  - Preview, Approve (only when every check passed) and Discard buttons.
- The candidate opens in the studio like any exercise, and the toolbar lists it as "Candidate: …".
- In the app, the body checks measure the bundled dressed V8 body, built separately so measuring never disturbs the viewport. The tests use the production character.

## Measured

On the production character (`HomeGymPT_Male_CORNER_FINAL_SHORTS.glb`):

| Request | Result | Validations | Time |
|---|---|---|---|
| Create a standing hammer curl with 12 kg dumbbells and controlled tempo. | **Passed after one correction.** The family defaults put the neutral-grip dumbbells **17.07 mm inside the thighs** (37 vertices), with the arms 3.88 mm from the chest against the library hammer curl's 5.02 mm. The loop moved the upper arms from 3° to **12°** out. Result: dumbbells 14.47 mm clear, arms 5.02 mm from the chest, confirmed at 13°. The library's hammer curl was hand-tuned to the same 12°. | 12 | 46 s |
| Create an incline dumbbell curl at 45 degrees with 8 kg dumbbells. | **Passed first time**, on the 45° incline bench, with the arms hanging behind the body. | 1 | 10 s |
| Create a seated dumbbell shoulder press with 10 kg dumbbells and controlled tempo. | **Passed first time**, seated on the flat bench. Built by the same pipeline with no press-specific generator code. | 1 | 30 s |
| Create a standing dumbbell shoulder press with 14 kg dumbbells. | Passed first time. | 1 | 30 s |
| Create an alternating hammer curl with 12 kg dumbbells. | **Needs a decision:** only two-arm work is certified. Nothing built. | 0 | — |

- In the app, on the bundled V8 body, the hammer curl's arms already clear the chest. Only the dumbbell clearance fails, so the loop resolves it with the elbow lever: 16° → 25° at the bottom, 5.27 mm clear, confirmed at 26°. Both corrections pass every check; which lever is used follows from what fails on the body measured.
- `a standing dumbbell curl with 10 kg dumbbells` generates a definition identical in every motion field to the library's `bicepCurl` (tested). The family is the source, and the library exercise is one of its outputs.

## Protected

- No family builder, exercise definition, rig, retargeting, grip or asset file changed.
- All 28 library clips are byte-identical.
- The equipment-clearance and self-collision tests print identical measurements (121 lines) after moving their measuring code into `constraints/bodyClearance.ts`, with the same limits.
- `store.loadExercise` now calls the new `loadDefinition`, which does what it always did.
- `src/test/setup.ts` yields one macrotask before each test. `selfCollision.test.ts` never returned to the event loop in its 190 s run, which made vitest's worker report a timeout and `npm test` exit 1 with every test passing.

## Next

1. **Certify another family** by writing its adapter: squat, lunge or hinge. The pipeline, checks, loop and UI are shared.
2. **Adjustable incline bench.** A 30° or 60° incline is refused today because the bench is built at 45°. Make its back angle a parameter of the equipment and of the curl's `INCLINE`, then certify the angles that pass.
3. **Levers for the press.** Add one when a certified press intent first fails a check.
4. **Move grip knowledge into the curl family.** Muscle emphasis and the grip error would then live in one place with the forearm rotation; the library's hammer and reverse curls would stop repeating it.
5. **Review views.** Capture the family's camera views automatically with each candidate (plan phase 10, step 8).
