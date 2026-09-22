# Self-Sufficient Exercise Generation Plan

## Primary objective

The long-term goal is not simply to make it easier to add exercises manually.

The goal is to make HOME GYM PT capable of generating new exercises to a high standard from a short user command with minimal manual intervention.

Target interaction:

"Create a seated dumbbell shoulder press."

Target system behaviour:

Command → understand exercise → select movement family → select equipment → generate joint targets → solve body motion → solve grip/contact → apply anatomical rules → smooth motion → validate → compare against references → auto-correct → preview → approve/add.

The finished system should produce motion that is:
- human-like
- smooth
- anatomically plausible
- mechanically consistent
- equipment-aware
- collision-aware
- repeatable through the production retargeting path
- automatically checked before acceptance

Read this together with docs/HIGH_END_EXERCISE_ENGINE_ROADMAP.md.

The roadmap defines the architectural building blocks. This document defines the end-state workflow and the order needed to reach practical self-sufficiency.

---

# 1. Definition of self-sufficient

A conventional gym exercise should eventually require only a high-level command.

Example:

"Create an incline dumbbell curl at 45 degrees with controlled tempo."

The system should automatically determine, where possible:
- movement family
- required equipment
- stance or body support
- grip type
- primary joints
- joint ranges
- expected joint sequencing
- equipment trajectory
- contact points
- balance/support requirements
- tempo
- technique rules
- validation rules
- camera/review states

It should then generate the exercise, validate it, correct solvable problems, and present the result.

The user should not need to hand-author hundreds of lines of exercise data for normal cases.

---

# 2. What must remain protected

Do not sacrifice accepted production behaviour in pursuit of automation.

Preserve unless a measured regression proves change is necessary:
- production skeleton
- absolute retargeting path
- accepted character proportions
- accepted deformation/corrective work
- grip logic
- existing validated exercises
- production GLBs/assets
- existing exercise semantics and review states

Shared-system changes must be checked against the complete exercise library.

Escalation rule:
1. Fix the shared rig/system if the issue is global.
2. Fix the movement-family template if the issue is family-wide.
3. Fix the exercise definition if the issue is exercise-specific.
4. Use a narrow corrective only when the higher levels are inappropriate.

Never fix one exercise by silently damaging another.

---

# 3. Required end-state architecture

## A. Stable production rig

The full body must behave consistently across all exercise families.

Required areas:
- shoulder/clavicle/scapular chain
- elbow/forearm
- wrist/hand/fingers
- spine/pelvis
- hip
- knee
- ankle/foot

Before large-scale generation, shared rig edits must be protected by library-wide regression checks.

## B. Movement-family system

New exercises should inherit from movement families rather than start from empty data.

Core families:
- curl
- triceps extension
- vertical press
- horizontal press
- vertical pull
- horizontal pull
- squat
- hinge
- lunge
- shoulder raise
- fly
- carry
- calf movement
- core flexion
- rotation
- anti-rotation

A family template should define shared biomechanics and validation rules.

Example: a curl family can provide shared elbow-dominant flexion, torso stability, upper-arm trajectory, grip requirements, ROM expectations, equipment-path expectations, and smooth concentric/eccentric timing. Dumbbell curl, hammer curl, reverse curl, incline curl, preacher curl, cable curl and concentration curl should then override only what differs.

## C. Exercise intent parser

Convert a user command into a structured ExerciseIntent.

Example input:

"Create a standing alternating hammer curl with 12 kg dumbbells and controlled tempo."

Example interpreted intent:
- family: curl
- variant: hammer
- stance: standing
- equipment: paired dumbbells
- grip: neutral
- execution: alternating
- load: 12 kg
- tempo: controlled
- support: feet planted

Use sensible defaults when the request is clear. Ask the user only when a choice materially changes the exercise.

## D. Reusable biomechanical model

The generator must understand more than hard joint limits.

It should eventually support:
- anatomical joint limits
- preferred neutral ranges
- coupled joint behaviour
- shoulder/scapular contribution
- spine/pelvis coordination
- hip/knee/ankle coordination
- natural elbow paths
- wrist alignment
- balance and support
- expected ROM ranges
- movement-family-specific sequencing

The goal is plausible human motion, not merely legal bone rotations.

## E. Full-body solving

The solver should work from goals and constraints.

Examples:
- hands remain on handles
- feet remain planted
- back stays against bench
- bar remains level
- elbow stays inside an allowed corridor
- knee tracks correctly
- torso remains inside a defined range
- equipment follows valid travel
- body avoids invalid penetration

The solver should resolve the body around these constraints instead of requiring every bone to be manually authored.

## F. Equipment intelligence

Equipment definitions should contain enough data for automatic exercise creation.

Dumbbell:
- handle axis
- grip region
- centre of mass
- collision primitive
- valid hand sockets

Barbell:
- main axis
- grip regions
- centre of mass
- plate/collar geometry
- symmetry rules

Bench:
- seat transform
- back-pad transform
- adjustable angle
- contact surfaces
- collision geometry

Cable machine:
- pulley location
- cable direction
- handle attachment
- travel limits
- cable constraints

Pull-up bar:
- bar axis
- grip region
- height/placement
- collision primitive

## G. Generic contact and collision system

Required contacts:
- hand ↔ dumbbell
- hand ↔ barbell
- hand ↔ cable handle
- hand ↔ pull-up bar
- foot ↔ floor/platform
- back ↔ bench
- chest ↔ pad
- elbow ↔ pad
- knee/thigh ↔ pad

Required collision checks:
- body ↔ body
- body ↔ equipment
- finger ↔ handle
- equipment ↔ equipment where relevant

A generated exercise should not pass validation while visibly penetrating itself or its equipment.

## H. Human-like motion system

The motion system must control:
- velocity
- acceleration
- deceleration
- easing
- joint sequencing
- phase timing
- natural settling
- controlled secondary motion
- left/right timing where appropriate
- concentric/eccentric differences
- loop continuity

Important principle: not every joint should move at the same normalized percentage at the same time.

Human-like movement requires coordinated delays and different timing curves.

## I. Structured reference library

Each important movement family should have reusable reference data:
- front view
- side view
- 3/4 view
- rear view
- Bottom/Mid/Peak/Return states
- joint-angle ranges
- anatomical landmark trajectories
- equipment trajectory
- hand orientation
- torso/pelvis orientation
- optional mocap trajectories later

The generator should compare its result against expected movement characteristics, not only hard joint limits.

## J. Automatic validation

Every generated exercise must pass standard QA.

Minimum checks should eventually include:
- technique-rule violations
- joint limits
- required ROM
- IK reachability
- grip/contact retention
- foot contact
- equipment drift
- equipment orientation
- body/body collision
- body/equipment collision
- finger/handle penetration
- symmetry where expected
- balance/support
- velocity discontinuities
- acceleration discontinuities
- loop closure
- skin/deformation thresholds
- reference trajectory deviation

Validation output should identify the exact exercise, frame/phase, rule, joint/contact and measured value.

## K. Automatic correction loop

This is the key to practical self-sufficiency.

Target process:

Generate → Validate → Diagnose → Adjust → Re-solve → Validate again → Repeat within safe limits.

Example:

SHOULDER PRESS

Initial validation:
- FAIL: wrist deviation +11°
- FAIL: right dumbbell drift 7.2 mm
- WARN: elbow path 18 mm outside preferred corridor

Auto-correction:
- rotate grip frame
- re-solve right arm
- adjust elbow target corridor

Second validation:
- PASS

Automatic correction must be constrained and auditable. It must never silently relax acceptance thresholds to achieve PASS.

---

# 4. Development order

## Phase 0 — Freeze the current foundation

Complete the current regression work first.

Requirements:
- existing exercise suite green
- shared-rig regression protection in place
- accepted curl/clavicle behaviour preserved unless measurement proves it wrong
- exact frozen SHA documented

Do not build generation layers on an unguarded rig foundation.

## Phase 1 — Remove manual duplication

Build reusable authoring primitives:
- pose mirroring
- technique-rule mirroring
- joint-target mirroring
- common stance/contact presets
- shared support rules
- common tempo profiles
- shared grip presets

Goal: a new exercise should no longer require manually duplicating left/right rules or repeated boilerplate.

## Phase 2 — Movement-family templates

Implement family inheritance using the existing ExerciseDefinition rather than replacing it.

Start with Curl.

Prove:
- dumbbell curl
- hammer curl
- reverse curl
- incline curl

Then expand to:
- press
- pull
- squat
- hinge
- lunge

Success criterion: variants become small override definitions instead of hundreds of copied lines.

## Phase 3 — Improve biomechanical intelligence

Add missing reusable rules:
- preferred neutral ranges
- coupled-joint rules
- shoulder/scapular coordination
- spine/pelvis coordination
- knee/hip tracking
- natural elbow path constraints
- required ROM rules

## Phase 4 — Upgrade equipment definitions

Add:
- axes
- grip regions
- centre of mass
- collision primitives
- adjustable geometry
- travel constraints
- contact surfaces

Keep definitions data-driven.

## Phase 5 — Generic collision/contact validation

Move collision logic out of scratch/diagnostic code and into production validation.

Start with:
1. hand/handle
2. dumbbell/body
3. arm/torso
4. foot/floor
5. bench/body
6. bar/body

## Phase 6 — Human-motion quality

Promote motion diagnostics into generation and validation.

Add measurable rules for:
- velocity continuity
- acceleration continuity
- natural phase easing
- joint sequencing
- secondary motion
- loop continuity

Bottom/Mid/Peak/Return remain semantic review points, not the only motion samples.

## Phase 7 — Structured reference system

Build reference records for validated movement families:
- expected ROM
- expected landmark corridors
- equipment paths
- body orientation limits
- joint sequencing expectations

Mocap can be added later; it is not required to begin.

## Phase 8 — ExerciseIntent and generator

Add the command-to-definition layer.

Target:

Natural-language request → ExerciseIntent → family template → variant overrides → equipment configuration → generated ExerciseDefinition.

Initially generate only certified movement families.

Do not allow unsupported biomechanics to be invented silently.

## Phase 9 — Solve, validate and auto-correct

Connect generation to the existing animation pipeline.

Target:

ExerciseIntent → generated definition → animation clip → QA → bounded automatic fixes → re-QA → final candidate.

Every automatic edit must be explainable and measurable.

## Phase 10 — Autonomous exercise creation workflow

Final workflow:
1. User enters an exercise command.
2. System interprets it.
3. System generates the exercise.
4. System solves motion/contact.
5. System runs QA.
6. System auto-corrects solvable failures.
7. System compares against reference rules.
8. System captures review views.
9. If fully certified, system presents the finished exercise.
10. If ambiguity or unresolved failure remains, it reports the exact issue requiring human decision.

---

# 5. Certification levels

## Experimental
- generator can create it
- human review required

## Validated
- family rules established
- regression suite exists
- references established
- normal variants can be generated reliably

## Auto-approved
- generated variants can pass the full validation/reference suite without manual editing
- human review is optional unless warnings exist

Do not claim full self-sufficiency for a family until it reaches validated or auto-approved status.

---

# 6. Representative proving set

Do not attempt hundreds of exercises first.

Prove the system across representative mechanics:
- dumbbell bicep curl
- hammer curl
- reverse curl
- incline curl
- bodyweight squat
- hinge/deadlift
- lunge
- dumbbell shoulder press
- push-up/bench-press pattern
- row
- pull-up
- triceps extension
- cable movement

Each new family must demonstrate that the same architecture works without bespoke engine code.

---

# 7. Success criteria

The project is functionally self-sufficient when:
1. A user can request a supported exercise in natural language.
2. The request becomes a structured intent.
3. The system selects the correct validated movement family.
4. A complete exercise definition is generated automatically.
5. Body/equipment/contact solving succeeds.
6. Motion is smooth and human-like under objective diagnostics.
7. Biomechanical and collision checks pass.
8. Reference movement checks pass.
9. Solvable errors are corrected automatically.
10. Existing exercises remain regression-safe.
11. The generated exercise can be added without manually authoring hundreds of lines.
12. Human intervention is limited to genuine ambiguity, unsupported equipment/movement, or final visual approval.

---

# 8. Rules for Claude / GPT / Work

When advancing this plan:
- inspect the current implementation before proposing replacements
- reuse existing generic systems wherever possible
- do not downgrade the current rich ExerciseDefinition schema
- prefer small reusable primitives over large rewrites
- make every shared change regression-safe
- use measured evidence, not visual assumption alone
- do not loosen validation thresholds merely to obtain PASS
- keep production assets untouched unless the approved task requires them
- do not add large numbers of exercises manually as a shortcut
- prioritise making the software capable of creating exercises itself

Central question for every major change:

"Does this make the system more capable of generating a new accurate, human-like exercise automatically without damaging existing exercises?"

If the answer is no, it is probably not the next priority.
