# Prompt family certification matrix

Source snapshot used to prepare this matrix:
- live source branch: `chatgpt/absolute-retarget-imports`
- 28 library exercises
- 16 family builders
- 4 prompt-certified families

Update the **measured status** in this file as families are certified. Do not mark
a family certified solely because an adapter compiles.

| Order | Family | Current library exercises | Current prompt state | Main new certification concern |
|---:|---|---|---|---|
| — | curl | bicep curl; hammer curl; reverse curl; 45° incline curl | CERTIFIED | Existing elbow-bottom/abduction levers; only 45° incline certified |
| — | overhead press | standing; seated dumbbell shoulder press | CERTIFIED | Pronated only; no lever until a measured failure needs one |
| — | squat | air squat | CERTIFIED | Bodyweight only |
| — | lunge | split squat; forward lunge; reverse lunge | CERTIFIED | Bodyweight only; step direction |
| 1 | hinge | Romanian deadlift | NOT CERTIFIED | Hinge depth/stance intent; dumbbell/body clearance |
| 2 | row | bent-over row | NOT CERTIFIED | Reuses hinge posture; neutral dumbbell grip |
| 3 | raise | lateral raise; front raise | NOT CERTIFIED | Direction intent; shoulder-height/clearance |
| 4 | calf | standing calf raise; dumbbell calf raise | NOT CERTIFIED | Optional implement/load while preserving foot contact |
| 5 | horizontal press | push-up | NOT CERTIFIED | Four fixed contacts; floor hand/grip semantics |
| 6 | supine | dumbbell bench press; dumbbell fly | NOT CERTIFIED | Motion selector; flat-bench support/compression |
| 7 | trunk flexion | crunch; sit-up | NOT CERTIFIED | Floor support; motion selector; no hand-held implement |
| 8 | extension | overhead triceps extension; cable pushdown | NOT CERTIFIED | Mixed dumbbell/cable equipment; two-hand bar |
| 9 | vertical pull | pull-up | NOT CERTIFIED | Fixed rack sockets; equipment hand locks; no floor |
| 10 | carry | farmer's walk | NOT CERTIFIED | Travel/locomotion timing rather than a stationary rep |
| 11 | anti-rotation | Pallof press | NOT CERTIFIED | Cable side; two-hand handle; intentional trunk stillness |
| 12 | rotation | Russian twist; cable woodchop | NOT CERTIFIED | Mixed seated/cable setup; trunk-turn direction/range |

## Per-family evidence columns

For each family add a dated evidence section containing:

- source HEAD;
- final character hash;
- adapter commit;
- canonical prompts tested;
- refusal prompts tested;
- existing library variants reproduced;
- first-pass failures;
- correction levers added, if any;
- validation count for each prompt;
- current full-suite result;
- automatic review render locations;
- status: `CERTIFIED`, `BLOCKED`, or `IN REVIEW`.

A `BLOCKED` family should say exactly which missing equipment, biomechanical
capability or family parameter prevents certification.
