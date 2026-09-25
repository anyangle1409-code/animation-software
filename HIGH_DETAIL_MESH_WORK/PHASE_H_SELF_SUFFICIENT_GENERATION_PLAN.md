# Phase H — self-sufficient prompt-to-exercise generation

## Gate

Dormant until the final character and movement system from Phase G is accepted.

Do not expand prompt certification against a temporary character state and then
assume those measurements transfer. Family certification must use the final
character/retarget/grip/deformation stack.

## End state

The user should be able to type a supported exercise request and have the studio:

1. parse it deterministically into an explicit `ExerciseIntent`;
2. choose the correct existing movement-family builder;
3. build a typed family variant;
4. generate the clip through the normal production pipeline;
5. validate it against the final character and equipment;
6. make bounded, explainable family-level corrections when a declared lever can
   resolve a measured failure;
7. automatically render the family review views;
8. return a review candidate with assumptions, corrections and every check;
9. refuse/ask rather than silently approximate something the family cannot build;
10. keep the candidate out of the permanent library until deliberately approved.

The goal is **self-sufficient generation**, not unconstrained motion invention.

## Current foundation

At the source state used to prepare this plan:

- 28 library exercises;
- 16 movement-family builders;
- 4 families certified for prompt generation:
  - curl;
  - overhead press;
  - squat;
  - lunge.
- 12 family builders remain to certify:
  - hinge;
  - row;
  - horizontal press;
  - supine;
  - raise;
  - extension;
  - calf;
  - carry;
  - vertical pull;
  - trunk flexion;
  - rotation;
  - anti-rotation.

The generator already has the correct architecture:
- deterministic parser;
- `ExerciseIntent`;
- one adapter per certified family;
- existing family builders as the source of motion;
- 13-check validation;
- bounded correction loop;
- session-only candidate;
- explicit refusal for uncertified/unsupported requests.

Do not replace this with a free-form LLM that writes angles directly.

## Family certification principle

A family becomes prompt-certified only by adding a thin adapter around the
existing family builder.

The adapter may contain:
- intent -> typed variant translation;
- family-specific prompt vocabulary;
- assumptions/defaults;
- the closest existing library reference for like-for-like body clearance;
- **measured** correction levers and bounded ranges;
- presentation metadata/source text.

It must not duplicate:
- exercise poses;
- joint angles;
- technique rules;
- equipment geometry;
- grip mechanics;
- IK;
- collision limits.

Those remain in the existing family/system modules.

## Certification order

This order minimizes new concepts and lets later families reuse earlier
generator evidence. It is a workflow order, not a quality ranking.

1. **hinge** — one dumbbell RDL reference; planted stance and body clearance are
   already shared with the certified lower-body infrastructure.
2. **row** — deliberately built on the hinge posture; certify after hinge so its
   torso/stance intent language is already settled.
3. **raise** — two dumbbell directions from one simple standing family.
4. **calf** — bodyweight/dumbbell variants; tests stance/contact and optional
   implement handling without a new support surface.
5. **horizontal press** — push-up; four contact points and floor hand profile.
6. **supine** — flat-bench press/fly; adds body support and two motions on the
   same bench setup.
7. **trunk flexion** — crunch/sit-up; floor support with no hand-held equipment.
8. **extension** — overhead dumbbell + cable pushdown; first mixed-implement
   family in the generator.
9. **vertical pull** — pull-up; fixed equipment grip locks and no floor contact.
10. **carry** — farmer's walk; locomotion/travel is a distinct generation case.
11. **anti-rotation** — Pallof press; two-hand cable handle and intentionally
    still trunk.
12. **rotation** — Russian twist + cable woodchop; mixed floor/cable setups and
    explicit trunk rotation make it the broadest remaining adapter.

If measurement shows a family is unexpectedly blocked, preserve its evidence
and continue with an independent family rather than weakening checks.

## Existing-library coverage target

Certifying the 12 remaining family builders covers the remaining 18 current
library exercises without writing 18 separate generators:

- hinge -> Romanian deadlift
- row -> bent-over row
- horizontal press -> push-up
- supine -> dumbbell bench press, dumbbell fly
- raise -> lateral raise, front raise
- extension -> overhead triceps extension, cable triceps pushdown
- calf -> standing calf raise, dumbbell calf raise
- carry -> farmer's walk
- vertical pull -> pull-up
- trunk flexion -> crunch, sit-up
- rotation -> Russian twist, cable woodchop
- anti-rotation -> Pallof press

The already-certified families cover:
- curl -> bicep, hammer, reverse and 45° incline curl
- overhead press -> standing/seated dumbbell press
- squat -> air squat
- lunge -> split, forward and reverse lunge

## Certification protocol — every family

### 1. Prove the builder

Before parser work:
- identify every current library exercise produced by the family;
- reconstruct each reference through the family call;
- prove the generated definition/clip is identical in every intended motion
  field to the library reference;
- record deliberate metadata differences separately if any.

If the library reference cannot be reproduced by its own family, repair that
family architecture first; do not hide the discrepancy in the generator adapter.

### 2. Define intent vocabulary

Add only words that map to actual typed family parameters.

For every prompt slot:
- accepted values;
- synonyms;
- default and written assumption;
- contradictions;
- unsupported named variants with a concrete reason.

If a phrase would require a parameter the family does not have, refuse it.

### 3. Define equipment semantics

The parser must never silently discard named equipment or load.

For each family state:
- allowed implement(s);
- support surface;
- optional/required load;
- handedness/execution;
- equipment angle/side/direction if applicable.

Mixed-implement families must explicitly route the intent to the correct setup.

### 4. First-pass validation

Build canonical prompts for every existing variant and run the full generator
validation against the **final character**.

No correction lever is added in advance merely because one seems useful.

### 5. Derive correction levers only from failures

If a valid family intent fails:
- identify the measured failing checks;
- locate a parameter the family itself already exposes, or a clearly
  family-level parameter that can be added without changing the meaning;
- sweep it within a bounded anatomical/equipment range;
- require that fixing one check does not break previously passing checks;
- require one step beyond the accepted value to confirm it is not a narrow
  measurement ridge.

If no legitimate family lever resolves the failure, the variant is not certified.

Never give the correction loop a validation threshold.

### 6. Negative/refusal tests

For each family maintain prompts for:
- contradictory instructions;
- unsupported equipment;
- unsupported unilateral/alternating execution;
- unsupported grip;
- unsupported support/angle;
- named variants the family cannot build;
- requests naming two movement families at once.

Expected result is an explicit issue/question, not a nearest approximation.

### 7. Automatic visual review pack

Generation currently validates numerically but the project plan still lists
automatic family camera capture as unfinished.

Before calling a new family autonomous, make the generator produce review views
from the family/exercise camera metadata automatically for every passing
candidate.

At minimum:
- the family-defined coaching camera;
- front;
- side;
- three-quarter;
- relevant contact/equipment close-up.

The candidate result should point to those views.

### 8. Final-character no-regression proof

For certification:
- full source suite green first;
- existing library clips unchanged unless a separately reviewed family fix was
  made;
- existing certified prompt families produce the same results;
- new family reference prompts pass all checks;
- current production/final character body collision and equipment clearance
  measured;
- exported candidate playback agrees with studio;
- any grip family used by the movement is already certified for the final hand.

### 9. Session-only candidate remains the default

Passing generation is not automatic library promotion.

Approval should mean:
- a person reviewed the candidate;
- the exact intent/variant/check report is retained.

Permanent library promotion remains an explicit code/content operation with a
revert point.

## Self-review without third-party video

Keep the software independent.

The system already knows:
- canonical joint limits;
- family pose definitions;
- technique rules;
- contact locks;
- equipment geometry;
- collision envelopes;
- grip envelopes;
- family camera views;
- reference library variants.

Use those as the primary self-review sources.

Add derived visual/geometry diagnostics from the software's own model:
- silhouette continuity;
- limb/trunk segment alignment;
- contact/support separation;
- left/right symmetry;
- path smoothness/jerk;
- joint-angle and angular-velocity curves;
- equipment trajectory smoothness;
- loop continuity.

Do not make internet/YouTube retrieval a requirement for candidate generation.

External reference media can remain an optional human research input for adding
a genuinely new family, not a runtime dependency.

## New-family creation is a separate level

Once all existing 16 families are prompt-certified, the next autonomy step is
not "let the model invent arbitrary poses."

For a genuinely new exercise:
1. classify it against existing biomechanics/equipment;
2. reuse existing stance/grip/contact/equipment primitives;
3. create a typed family or extend an existing one;
4. author explicit technique rules;
5. add deterministic validation;
6. certify reference variants;
7. only then expose it to prompt generation.

This keeps the studio explainable and testable as coverage grows.

## Final Phase H acceptance

Phase H is complete when:
- all 16 current family builders are either prompt-certified or carry an explicit
  documented blocker;
- every current library exercise is reachable from a canonical prompt through
  its family where supported;
- unsupported prompts are refused rather than approximated;
- passing generated candidates receive automatic review renders;
- the final character is used by all character-dependent validation;
- the correction loop contains only bounded family-declared levers;
- a regression corpus proves old prompts stay deterministic as new families are
  added;
- nothing auto-promotes without review.
