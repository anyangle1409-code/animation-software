# High-End Exercise Engine Roadmap

## Purpose

This document defines the long-term direction for the HOME GYM PT animation software.

The goal is to evolve the current exercise-specific animation system into a reusable, high-end procedural exercise animation engine that can create large numbers of exercises accurately, consistently, and with minimal manual work.

This is a roadmap and architecture target only. Do not replace accepted production behaviour or make broad implementation changes just because they are described here.

---

## Core principle

Future exercises should be defined mainly by reusable movement rules, constraints, equipment definitions, and exercise data — not by bespoke animation code for every individual exercise.

Target workflow:

**Exercise description → movement template → biomechanical rules → IK/constraint solving → contact/equipment solving → animation → automated validation → visual review**

The accepted production character, skeleton, retargeting path, exercise behaviour, grip logic, assets, and existing validated work must be preserved unless a specific regression or approved migration requires change.

---

## 1. Production character and rig foundation

Before scaling the exercise library, establish one trusted production character/rig.

Requirements:

- Stable source skeleton and production retargeting path.
- Correct limb proportions.
- Reliable shoulder/clavicle/scapular behaviour.
- Reliable elbows, forearms, wrists, hands and fingers.
- Reliable hips, knees, ankles and spine.
- Reusable deformation/corrective system rather than exercise-specific mesh fixes.
- Dressed and bare character variants must share the same validated motion foundation.

The existing accepted work should be treated as the baseline, not rebuilt unnecessarily.

---

## 2. Biomechanical joint model

Create reusable anatomical rules for the full body.

Examples:

- Shoulder flexion/extension.
- Shoulder abduction/adduction.
- Internal/external rotation.
- Clavicle/scapular contribution.
- Elbow flexion/extension.
- Forearm pronation/supination.
- Wrist flexion/extension/deviation.
- Spine and pelvis motion.
- Hip flexion/extension/rotation.
- Knee flexion.
- Ankle movement.
- Joint limits and preferred neutral ranges.

The goal is for exercises to use the same underlying joint rules instead of inventing new behaviour per movement.

---

## 3. Generic IK and constraint system

Build a reusable full-body constraint/IK layer.

Typical constraints:

- Hand remains attached to equipment.
- Foot remains planted.
- Bar remains level.
- Back remains against bench.
- Elbow stays within an allowed path.
- Knee tracks within an allowed region.
- Pelvis/spine remain inside movement limits.
- Equipment maintains required orientation.
- Body parts avoid invalid penetration.

Exercise definitions should state constraints; the solver should determine the joint solution where possible.

---

## 4. Generic contact and grip system

Expand the current grip/contact work into a reusable contact framework.

Required contact types include:

- Hand ↔ dumbbell.
- Hand ↔ barbell.
- Hand ↔ cable handle.
- Hand ↔ pull-up bar.
- Feet ↔ floor/platform.
- Back ↔ bench.
- Chest ↔ pad.
- Elbows ↔ pad.
- Thighs/knees ↔ pads.
- Body ↔ equipment collision.

Grip/contact logic should be shared between exercises rather than recreated for each one.

---

## 5. Equipment definition system

Equipment should be reusable data-driven objects.

Each equipment definition should expose the information needed by the solver.

Examples:

### Dumbbell

- Handle axis.
- Grip region.
- Centre of mass.
- Collision geometry.
- Left/right grip frames.

### Barbell

- Bar axis.
- Grip regions.
- Plate geometry.
- Centre of mass.
- Symmetry/orientation rules.

### Cable machine

- Pulley position.
- Cable direction.
- Handle attachment.
- Travel limits.
- Cable length/constraint behaviour.

### Bench

- Back-pad transform.
- Seat transform.
- Adjustable angle.
- Contact surfaces.
- Collision geometry.

---

## 6. Data-driven exercise schema

Exercises should become definitions rather than large custom code paths.

Conceptual example:

```yaml
exercise: dumbbell_bicep_curl
family: curl
stance: standing

equipment:
  - dumbbell_left
  - dumbbell_right

grip:
  type: supinated

constraints:
  feet: planted
  torso: upright
  elbows: near_torso
  hands: locked_to_handles

motion:
  elbow_flexion: [5, 125]
  forearm: supinated

phases:
  - Bottom
  - Mid
  - Peak
  - Return

tempo: 2-1-2
```

The exact schema can evolve, but the principle is important: most future exercises should be authored through structured data and reusable systems.

---

## 7. Movement-family templates

Build reusable templates for major movement families.

Initial families:

- Squat.
- Hinge.
- Lunge.
- Horizontal push.
- Vertical push.
- Horizontal pull.
- Vertical pull.
- Curl.
- Triceps extension.
- Shoulder raise.
- Fly.
- Carry.
- Calf movement.
- Core flexion.
- Rotation.
- Anti-rotation.

Variants should inherit from a family template and override only what differs.

Example:

**Curl template**

→ dumbbell curl  
→ hammer curl  
→ reverse curl  
→ cable curl  
→ preacher curl  
→ incline curl  
→ concentration curl

---

## 8. Exercise Builder

Long-term goal: create an Exercise Builder where a new movement can be assembled from reusable components.

Example flow:

**Movement family → equipment → stance → grip → joints/ROM → contacts → tempo → validation**

Example:

**Curl → Dumbbells → Standing → Neutral grip → Elbow 10–120° → Hand lock + planted feet → 2-1-2**

This should generate the starting exercise automatically.

---

## 9. Automatic validation

Every exercise should eventually run through automated QA.

Checks should include:

- Joint-limit violations.
- Body/body collision.
- Body/equipment collision.
- Finger/handle penetration.
- Lost grip/contact.
- Foot sliding.
- Equipment drift.
- Bar orientation.
- Excessive torso movement.
- Elbow/knee trajectory.
- Required ROM.
- Symmetry where expected.
- Sudden velocity/rotation discontinuities.
- Skin/deformation thresholds.

Target output example:

```text
HAMMER CURL

Biomechanics: PASS
Joint limits: PASS
Grip/equipment lock: PASS
Collisions: PASS
Skin deformation: PASS
Foot lock: PASS

Warnings:
Shoulder elevation exceeds preferred target by 3.1°.
```

Warnings should be actionable enough for GPT/Claude/Work to investigate automatically.

---

## 10. Reference and motion-quality system

Create a structured reference library for important movement families.

Useful reference data:

- Front view.
- Side view.
- 3/4 view.
- Rear view.
- Bottom/Mid/Peak/Return reference states.
- Expected joint-angle ranges.
- Equipment position/orientation.
- Hand orientation.
- Anatomical landmarks.
- Optional mocap/reference trajectories later.

The reference system should help distinguish objective regressions from style preferences.

---

## 11. AI-assisted exercise generation

Once the reusable architecture exists, the desired workflow is:

1. User requests an exercise.
2. AI selects the movement-family template.
3. AI selects/creates equipment definitions.
4. AI creates the exercise definition.
5. IK/constraints generate the initial motion.
6. Contact and equipment solvers resolve interaction.
7. Automated validation runs.
8. AI reviews warnings and corrects them.
9. App captures Bottom/Mid/Peak/Return and useful camera views.
10. Regression checks run.
11. User performs final visual approval only when needed.

Long-term objective: AI should do as much of the creation, validation, correction and documentation process as safely possible without requiring repeated user input.

---

## Recommended implementation order

### Stage 1 — Finish/freeze production character foundation
Do not scale the exercise library until the important anatomical and deformation issues are controlled.

### Stage 2 — Generic biomechanical joint model
Define joint limits, preferred ranges and shared anatomical rules.

### Stage 3 — Generic IK/constraint engine
Hands, feet, elbows, body posture and equipment should be constrained through reusable systems.

### Stage 4 — Generic grip/contact framework
Generalise current grip work into reusable body/equipment contact.

### Stage 5 — Equipment definitions
Move equipment behaviour into reusable data.

### Stage 6 — Exercise schema
Make exercises primarily data-driven.

### Stage 7 — Movement-family templates
Create reusable parent templates and variants.

### Stage 8 — Automated biomechanics/collision validation
Make exercise generation measurable and testable.

### Stage 9 — Reference/mocap comparison
Add objective motion-quality comparison.

### Stage 10 — AI Exercise Builder
Allow AI to generate and refine exercises from high-level descriptions.

---

## Representative validation set

Do not start by adding hundreds of exercises.

First prove the architecture across a small but difficult set covering different mechanics, for example:

- Dumbbell bicep curl.
- Hammer curl.
- Bodyweight squat.
- Hinge/deadlift pattern.
- Lunge.
- Dumbbell shoulder press.
- Push-up or bench-press pattern.
- Row.
- Pull-up.
- Triceps extension.
- Cable movement.

If these can share the same generic architecture without exercise-specific hacks, scaling the library becomes much safer.

---

## Non-negotiable engineering rule

Avoid fixing a single exercise in a way that damages another.

Prefer:

1. Correct the shared rig/system if the defect is global.
2. Correct the movement-family template if the defect is family-wide.
3. Correct the exercise definition if the defect is exercise-specific.
4. Use a narrowly scoped corrective only when the previous levels are inappropriate.

All changes must protect previously accepted exercises through regression testing.

---

## Current intent

This document is the long-term architectural target.

Before implementing any stage, inspect the current repository and existing accepted/frozen work, then propose the smallest safe next step.

Do **not** begin a large refactor automatically.

Preserve accepted production behaviour and only change what is required for the current approved stage.
