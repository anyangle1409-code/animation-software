# Hinge + row prompt-generation handoff

## Branch

`work/prompt-generation-hinge-row-20260925`

This branch is layered on top of:

`work/prompt-generation-hinge-20260925`

so hinge can be validated independently first.

The live source branch is unchanged.

## Additional family on this branch

**Bent-over row**

Supported draft request:

```
Create a dumbbell bent-over row with 16 kg dumbbells and controlled tempo.
```

The adapter:

- uses existing `rowFamily()` unchanged;
- uses `dumbbell_bent_over_row` as the reference exercise;
- uses paired dumbbells;
- defaults to 14 kg per hand;
- accepts configurable load and tempo;
- uses the row family's neutral palms-facing grip;
- uses the existing fixed bent-over posture;
- adds no correction lever.

It deliberately requires the words **bent-over** rather than treating a bare
"row" as this exercise. That prevents silent substitution of one-arm, cable,
chest-supported, upright or other row styles.

## Explicit refusals

- bare/ambiguous "row";
- upright row;
- chest-supported row;
- one-arm/unilateral row;
- renegade row;
- seated/cable row;
- barbell or T-bar row;
- non-neutral grip;
- arbitrary torso-angle input.

## Validation order

First validate the hinge-only branch.

Then on this branch run:

```
npm run typecheck
npm test -- src/generation/parse.test.ts src/generation/generate.test.ts
npm run build
npm test
```

With the production character available, both the generated RDL and generated
bent-over row are expected to run the same full existing validation report as
their library references.

If either fails:

- do not weaken a validation gate;
- do not modify the family merely for generation;
- report exact check + measurement;
- add a family lever only when a measured failure demonstrates the correct safe
  parameter.

## Protection target

- no new exercise definition files;
- existing family builders unchanged;
- existing library clips byte-identical;
- rig, grip, retargeting and production assets unchanged.
