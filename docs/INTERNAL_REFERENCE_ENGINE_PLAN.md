# HOME GYM PT — Internal Reference & Visual QA Engine

## Purpose

Make HOME GYM PT capable of judging its own generated exercise candidates without depending on YouTube, cloud vision services, or other third-party reference systems.

The reference system must be a separate verifier, not another copy of the generator. It should answer:

1. Is the generated motion biomechanically plausible?
2. Does it stay inside the expected movement-family envelope?
3. Does the equipment follow the expected path?
4. Are the contacts, timing and sequencing believable?
5. Does the rendered body visibly deform or interact incorrectly?
6. If something is wrong, which bounded family parameter is the safest correction lever?

The desired end-state is:

```
prompt
  -> ExerciseIntent
  -> family builder
  -> generated ExerciseDefinition
  -> clip
  -> existing mechanical QA
  -> INTERNAL REFERENCE QA
  -> review renders
  -> LOCAL VISUAL QA
  -> bounded correction
  -> repeat
  -> certified candidate / exact unresolved issue
```

No internet access is required at runtime.

---

## Design rule: the generator must not mark its own homework

The reference layer must be independent of the exercise-family implementation.

Bad design:

```
curlFamily() says shoulder = 4 deg
reference system asks curlFamily() what shoulder should be
candidate shoulder = 4 deg
PASS
```

Required design:

```
curlFamily() generates the candidate
reference/curl defines an independently approved shoulder/elbow/equipment envelope
evaluator samples the candidate against that envelope
```

Reference records are versioned, reviewable data. A family builder may change without silently changing what PASS means.

---

## Reference data model

Each supported movement family gets a local `ReferenceSpec`.

A reference should describe ranges and corridors, not one rigid pose.

Core sections:

### Identity
- reference id
- version
- movement family
- supported variants
- certification status
- body-size normalization convention

### Phase landmarks
Examples:
- start / stretch
- mid concentric
- peak / contraction
- mid eccentric
- return

Landmarks are represented as normalized cycle positions from 0.0 to 1.0.

### Joint envelopes
Examples:
- elbow flexion
- shoulder flexion / abduction
- forearm pronation/supination
- wrist deviation
- spine angle
- pelvis angle
- hip/knee/ankle angles

Each envelope may contain:
- preferred range
- hard acceptable range
- applicable phase/range of cycle
- optional timing corridor

### Landmark trajectories
Normalized paths for:
- shoulder
- elbow
- wrist/hand
- pelvis
- knee
- ankle
- head

Positions should be relative to stable body dimensions such as shoulder width, torso length, limb length or standing height, not raw pixels.

### Equipment trajectories
Examples:
- dumbbell centre
- bar axis
- handle path
- cable direction
- bench-contact region

### Contact expectations
Examples:
- feet planted
- hands fixed to bar
- back contacting bench
- body supported by pad

### Motion-quality envelopes
- phase duration ratios
- joint sequencing
- maximum velocity discontinuity
- maximum acceleration discontinuity
- allowed secondary motion
- symmetry/asymmetry expectations
- loop continuity

### Review cameras
Family-specific views to render automatically:
- front
- side
- 3/4
- rear where useful
- close-up targets such as hand/grip or shoulder

### Visual/deformation checks
These should initially be geometry-derived rather than AI-opinion based:
- self penetration
- equipment penetration
- grip gaps
- floor penetration
- silhouette discontinuities
- extreme local surface stretch/compression
- left/right deformation mismatch
- hand/finger contact shape
- elbow/shoulder/knee contour alarms

A local vision model can be added later, but it is not required for the first independent system.

---

## Offline reference images

HOME GYM PT can produce its own expected images.

The reference engine should create a neutral canonical reference pose/trajectory from the `ReferenceSpec`, then render it with a simple reference mannequin.

The candidate and reference are rendered with:
- identical camera
- identical framing
- identical body normalization
- identical phase
- identical equipment coordinate convention

The comparison is then based on:
- projected joint landmarks
- silhouette masks
- equipment centre/axis
- contact points
- key anatomical regions

This provides image-based checking without an external video.

The reference render is explanatory evidence. The authoritative measurements remain the structured reference values.

---

## Proposed source layout

Do not create all of this at once. This is the target structure.

```
src/reference/
  types.ts
  library.ts
  normalize.ts
  sample.ts
  evaluate.ts
  report.ts
  cameras.ts
  render.ts
  visual.ts

  specs/
    curl.ts
    overheadPress.ts
    squat.ts
    lunge.ts
    hinge.ts
    ...

src/reference/*.test.ts

docs/reference/
  README.md
  REFERENCE_SPEC_EXAMPLE.json
  certification/
```

The current generator remains in `src/generation/`. Reference code must not migrate into the generator.

---

## Implementation stages

### Stage R0 — Freeze the contract

Add only:
- `ReferenceSpec` types
- report/result types
- normalization conventions
- versioning rules
- no change to exercise mechanics

Success:
- typecheck/build/tests unchanged
- zero existing clip changes

### Stage R1 — Curl reference evaluator

Start with curl because prompt generation already exists and the family has strong measured behaviour.

Reference checks should cover:
- elbow ROM
- upper-arm corridor
- shoulder movement
- forearm orientation by grip
- wrist neutrality
- torso stability
- dumbbell path
- left/right symmetry
- timing/phase structure

Test:
- accepted library curl variants pass
- deliberately perturbed candidate fails with named measurements

Do not derive the expected values by calling `curlFamily()`.

### Stage R2 — Automatic review capture

For every generated candidate:
- render the full repetition
- capture family review cameras
- capture semantic phases
- write a review manifest with time, phase and camera metadata

Initial output:
- front/side/3-quarter stills
- optional short loop video from local renderer

No visual AI required yet.

### Stage R3 — Deterministic visual QA

Compare candidate vs reference render using local geometry/image measurements:
- 2D normalized joint offsets
- silhouette bounds
- equipment path projection
- body/equipment overlap
- contact alignment
- symmetric contour checks

Produce an explainable report:
```
FAIL shoulder trajectory
candidate peak: +0.084 torso lengths
reference max: +0.050
excess: +0.034
```

### Stage R4 — Connect to bounded correction

Reference failures may nominate correction categories, but only existing declared family levers may modify a candidate.

The reference engine never changes:
- acceptance thresholds
- rig
- production assets
- exercise library definitions

Flow:
```
reference FAIL
 -> diagnosis
 -> generator asks family adapter for compatible lever
 -> bounded attempt
 -> full mechanical QA
 -> reference QA
 -> accept/reject
```

### Stage R5 — Expand to current prompt-certified families

After curl:
1. overhead press
2. squat
3. lunge
4. hinge once prompt-certified
5. row
6. vertical pull
7. remaining families

A family is "reference certified" only when:
- its accepted library examples pass
- known bad perturbations fail
- reports name the actual measurement
- reference records were independently reviewed

### Stage R6 — Reference mannequin renderer

Generate an independent idealized reference motion from `ReferenceSpec`.

Purpose:
- give the reviewer something visible to compare against
- create reference stills without external images
- support automated silhouette/path comparison

This mannequin is not a production character and must not be used to hide production-mesh deformation failures.

### Stage R7 — Local visual-anatomy reviewer

Only after deterministic checks are mature.

Possible local-only options:
- bundled lightweight pose/silhouette model
- local feature comparison
- locally executed vision model if later practical

Its output is advisory until a numerical/geometric check confirms the issue.

Required rule:

`visual observation -> measurable confirmation -> bounded correction`

Never allow free-form visual feedback to move bones directly.

### Stage R8 — Reference auto-certification loop

Final workflow:

```
Generate
 -> mechanical QA
 -> reference QA
 -> render QA
 -> diagnose
 -> bounded correction
 -> repeat
 -> CERTIFIED / HUMAN DECISION REQUIRED
```

The user should only be asked when:
- the prompt is genuinely ambiguous
- the requested movement/equipment is unsupported
- two legitimate techniques cannot be distinguished from the request
- a failure has no approved correction lever
- visual quality is uncertain beyond objective checks

---

## Relationship to third-party material

Third-party video can remain optional development material, never a runtime dependency.

It may be used manually during development to help set or audit a reference envelope. Once an envelope is approved, HOME GYM PT stores only its own structured reference values and provenance notes.

Production behaviour must not require:
- YouTube
- an external API
- a cloud vision model
- an internet connection

---

## Mesh QA integration

The same reference infrastructure can later review character candidates.

Example hand review pack:
- open palm/front
- back of hand
- thumb-index web
- closed fist
- dumbbell curl grip
- push-up hand
- pull-up grip

Checks:
- protected contacts unchanged
- joint/finger landmarks align
- silhouette is smoother than prior accepted checkpoint
- no new holes/folds/intersections
- grip/contact geometry remains valid

Mesh acceptance remains separate from exercise-motion acceptance.

---

## Guardrails

1. Preserve the frozen 63-bone canonical hierarchy.
2. Never relax a validation threshold to obtain PASS.
3. Never silently approximate an unsupported exercise.
4. Never change production GLBs as part of reference work.
5. Existing library clips must remain byte-identical unless an explicitly approved exercise change is the task.
6. Reference specifications are versioned separately from family builders.
7. A generated candidate must pass existing mechanical QA before reference QA can certify it.
8. A reference failure may suggest a lever; it cannot edit arbitrary bones.
9. Runtime operation must work without network access.
10. All reference decisions must be explainable in measurements.

---

## Definition of done

The Internal Reference Engine is successful when a supported prompt can:

1. generate an exercise;
2. pass mechanical/contact/collision QA;
3. compare itself against a local independent biomechanical reference;
4. render its own review views;
5. detect meaningful trajectory/pose/deformation differences;
6. make safe bounded corrections;
7. repeat validation;
8. certify the result without external media or human inspection in normal cases.

Human review becomes an exception, not a standard step.
