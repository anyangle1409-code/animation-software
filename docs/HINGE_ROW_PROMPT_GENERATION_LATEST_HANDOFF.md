# Refreshed hinge + row prompt-generation handoff

## Branch

`work/prompt-generation-hinge-row-latest-20260925`

This branch is layered on the refreshed hinge/RDL branch, which itself is based
on source HEAD:

`47187360b5d631d438a6b33b284ad06732e244cb`

It therefore includes Claude's adjustable incline-bench work rather than the
older 8ec5247 snapshot.

The live source branch is unchanged.

## Added here

**Bent-over row prompt generation**

Supported request:

```
Create a dumbbell bent-over row with 16 kg dumbbells and controlled tempo.
```

The adapter:
- calls existing `rowFamily()` unchanged;
- uses `dumbbell_bent_over_row` as its library/reference exercise;
- uses paired dumbbells;
- defaults to 14 kg per hand;
- accepts configurable load and existing tempo profiles;
- uses the family's neutral palms-facing grip;
- uses the family's existing fixed bent-over posture;
- has no correction lever unless a measured failure later proves one necessary.

## Explicit refusals

The generator refuses rather than approximates:
- an ambiguous bare "row";
- upright row;
- chest-supported row;
- one-arm/unilateral row;
- renegade row;
- seated/cable row;
- barbell/T-bar row;
- non-neutral grip;
- arbitrary torso-angle input.

## Protection rules

No new exercise definition file was added.
No row-family biomechanics were changed.
No validation threshold was loosened.
Rig, retargeting, grip and production assets are untouched.

## Validation

The branch owns a GitHub CI workflow so Claude does not need to spend usage
discovering compile/test problems.

Required gates:
1. `npm run typecheck`
2. focused parser/generator tests
3. `npm run build`
4. complete `npm test`

If production-character generation fails, report the exact mechanical check and
measurement. Do not alter `rowFamily()` or a threshold simply to force PASS.
