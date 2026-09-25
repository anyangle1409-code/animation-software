# Calf-raise prompt-generation handoff

## Branch

`work/prompt-generation-calf-latest-20260925`

Layered on the refreshed generator chain:
latest source → hinge/RDL → bent-over row → pull-up → triceps extension → shoulder raises → calf raises.

The live source branch is unchanged.

## Added here

Two existing `calfFamily()` variants become prompt-generatable:

```
Create a bodyweight calf raise with slow tempo.
Create a calf raise with 18 kg dumbbells.
```

### Bodyweight calf raise
- existing `calfFamily()` with no load;
- reference: `standing_calf_raise`;
- standing bilateral movement;
- no hand-held equipment.

### Dumbbell calf raise
- existing `calfFamily({ mass })`;
- reference: `dumbbell_calf_raise`;
- paired dumbbells;
- neutral grip;
- default 14 kg per hand;
- configurable load and existing tempo profiles.

## Explicit refusals

- seated calf raise;
- single-leg/unilateral calf raise;
- donkey calf raise;
- Smith/machine/barbell variants;
- deficit or step calf raise;
- contradictory bodyweight + dumbbell requests;
- hand-grip requests on the bodyweight version;
- arbitrary angle input.

## Protection

No calf-family biomechanics changed.
No exercise definition changed.
No validation threshold changed.
No rig, retargeting, grip or production asset changed.

CI validates typecheck, focused parser/generator tests, production build and full suite.
