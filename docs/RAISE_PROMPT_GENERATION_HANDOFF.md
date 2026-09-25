# Shoulder-raise prompt-generation handoff

## Branch

`work/prompt-generation-raise-latest-20260925`

Layered on the refreshed generator chain:
latest source → hinge/RDL → bent-over row → pull-up → triceps extension → raises.

The live source branch is unchanged.

## Added here

Two existing `raiseFamily()` variants become prompt-generatable:

```
Create a lateral raise with 7 kg dumbbells and controlled tempo.
Create a front raise with 5 kg dumbbells.
```

### Lateral raise
- existing `raiseFamily({ direction: 'lateral' })`;
- reference: `dumbbell_lateral_raise`;
- paired dumbbells;
- neutral hanging grip;
- standing support.

### Front raise
- existing `raiseFamily({ direction: 'front' })`;
- reference: `dumbbell_front_raise`;
- paired dumbbells;
- pronated palms-down grip;
- standing support.

Both accept configurable dumbbell load and existing tempo profiles.

## Explicit refusals

- single-arm/unilateral/alternating raises;
- cable, machine or band raises;
- plate front raise;
- rear-delt/reverse-fly/bent-over variants;
- seated/incline raises;
- grip changes that contradict the family;
- a request naming both lateral and front raise.

## Protection

No raise-family biomechanics changed.
No exercise definition changed.
No validation limit changed.
No rig, retargeting, grip or production asset changed.

CI validates typecheck, parser/generator tests, production build and full suite.
