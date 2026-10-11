# G4c — original exercise command → strictly typed INTENT ONLY
**11 October 2026 • Home Gym PT Chat software lane • no network, vendor runtime or pretrained model.**

The owner wants to type a command such as **dumbbell shoulder press** and have the first-party app generate a natural full-body exercise without depending on an external animation database. This step implements a narrow but production-traceable **natural language entry contract**, not yet exercise motion synthesis.

The module `src/exercise/firstPartyExerciseIntent.mjs` exposes two first-party, synchronous functions:

- `parseFirstPartyExerciseIntent(description)` returns a frozen typed descriptor containing movement ID, movement family, region (upper/lower/core), explicitly named equipment, laterality, posture and grip plus the biomechanics tests **that will be required**. It never invents joint locations, loads, contacts, animation frames, fatigue, range of motion or clinical approvals.
- `supportedFirstPartyExerciseIntentIds()` enumerates 26 intentionally bounded first-party movement intents. These include shoulder/bench pressing, push-ups, vertical pulls, rows, air/front/back/goblet squats, lunges, hinges/deadlifts, curls/extensions, raises, calf raises, plank and crunch. Synonyms are mapped deliberately, not by a web/third-party exercise library.

Example command **Dumbbell Shoulder Press** produces the movement ID `overhead_press`, source equipment `dumbbell`, upper body, vertical-press family, no assumed left/right hand and explicit future validation requirements: shoulder girdle, coordinated scapulohumeral motion, glenohumeral rotation, elbow/trunk and equipment contact. More complex descriptions such as **single-arm seated dumbbell shoulder press neutral grip** retain the user's source qualifier but do not invent missing joint/force data.

The parser **fails closed** if an unsupported or ambiguous movement is typed, an unknown qualifier is appended, a load such as 30 kg or repetition count would otherwise be silently ignored, more than one conflicting piece of equipment/grip/side/posture is present, or a side-specific arm is paired with a squat. The input is ASCII letters/hyphens/spaces only; no arbitrary unknown text is passed on to execution. Supported exercises can be extended only with new authored mapping and tests, not silent fallback to made-up keyframes.

A successful output explicitly contains false flags: realHumanPoseGenerated, contactAndLoadDynamicsVerified, clinicallyApprovedROM and productionAnimationReady. The final first-party biomechanics/constraint solver will consume this contract and either generate independently validated source-joint frames or explicitly reject unsupported combinations. Work owns anatomical 3D motion/deformation, and Chat owns this command/UI/engine integration. The command library's existence alone is **not** the app's long-term arbitrary-exercise capability.

Tests exercise 30+ language examples, contradictions, unknown inputs, source qualifier preservation, immutability and exercise-specific future biomechanical checks; CI reruns the inherited original GLB/pose source contract and unchanged animation studio typecheck/build without adding JS libraries.

**This is a separate PR stacked on G4b [PR #60](https://github.com/anyangle1409-code/animation-software/pull/60), not on colour-management PR #64.** Both are isolated first-party software lanes. Work's original skeleton, Blender file, c004 candidate, CT sources and PR #26 are untouched.
