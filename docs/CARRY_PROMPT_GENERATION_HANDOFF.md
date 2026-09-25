# Farmer's-walk prompt-generation handoff

## Branch

`work/prompt-generation-carry-latest-20260925`

Layered on the refreshed generator chain:
latest source → hinge/RDL → bent-over row → pull-up → triceps extension → shoulder raises → calf raises → farmer's walk.

The live source branch is unchanged.

## Added here

The existing `carryFamily()` becomes prompt-generatable:

```
Create a farmer's walk with 28 kg dumbbells.
```

The adapter:
- calls existing `carryFamily()` unchanged;
- uses `farmers_walk` as the library/reference exercise;
- uses paired dumbbells and neutral grip;
- defaults to 24 kg per hand;
- accepts configurable load;
- uses semantic intent support `walking`;
- preserves the family's travel metadata and two-step walking-in-place loop.

## Important tempo rule

The carry family currently gives each step an explicit fixed 0.6 s phase duration.
Changing `ExerciseDefinition.tempo` does not genuinely change that cadence.

Therefore a requested tempo is rejected rather than silently pretending it was
applied. Cadence should only become prompt-configurable after the family exposes
a real step-duration/cadence parameter.

## Explicit refusals

- suitcase/unilateral carry;
- overhead carry;
- front-rack carry;
- bear-hug carry;
- trap-bar/barbell/kettlebell carry;
- single-arm carry;
- non-neutral grip;
- non-walking support;
- requested tempo/cadence until the family owns that parameter;
- arbitrary angle input.

## Protection

No carry biomechanics changed.
No exercise definition changed.
No validation threshold changed.
No rig, retargeting, grip or production asset changed.

CI validates typecheck, focused parser/generator tests, production build and full suite.
