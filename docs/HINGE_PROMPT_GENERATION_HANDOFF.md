# Hinge prompt-generation handoff

## Branch

`work/prompt-generation-hinge-20260925`

Created from source HEAD:

`8ec5247f9a5ef53dd023b3ebb7dd26339fac3060`

The live source branch was not modified.

## Goal

Certify the existing `hingeFamily()` for prompt generation without adding a
new exercise definition or changing the family biomechanics.

Supported draft request:

```
Create a dumbbell Romanian deadlift with 18 kg dumbbells and slow tempo.
```

Also intended to support:

- Romanian deadlift
- RDL
- dumbbell RDL
- dumbbell hip hinge

The adapter uses:

- `hingeFamily()`
- reference exercise `dumbbell_romanian_deadlift`
- paired dumbbells
- default 16 kg per hand
- configurable load
- existing family tempo or requested named/explicit tempo
- current family pronated hand orientation
- standing support

No correction lever was added. One should only be introduced after a measured
generated-hinge failure demonstrates a safe family parameter that resolves it.

## Explicit refusals

The adapter refuses rather than approximates:

- plain/conventional deadlift;
- sumo deadlift;
- stiff-leg deadlift;
- single-leg RDL;
- good morning;
- barbell RDL;
- kettlebell hinge;
- mixed grip;
- non-pronated grip;
- seated/incline support;
- arbitrary angle input.

## Files changed

- `src/generation/families.ts`
- `src/generation/intent.ts`
- `src/generation/parse.ts`
- `src/generation/parse.test.ts`
- `src/generation/generate.test.ts`

No family builder, exercise definition, rig, grip, retargeting or asset was
changed.

## Validation required on laptop

Run:

```
npm run typecheck
npm test -- src/generation/parse.test.ts src/generation/generate.test.ts
npm run build
```

If green, run:

```
npm test
```

With the production character asset available, confirm the RDL generation test
passes the full existing validation report first time. If it does not:

- do not weaken a gate;
- do not change `hingeFamily()` merely for the generator;
- report the exact failed check and measurement;
- add a lever only if an already-sound hinge-family parameter is demonstrated
  to resolve the measured failure.

## Protection target

- all existing 28 library clips remain byte-identical;
- no new standalone exercise definition;
- no production asset change;
- source branch remains untouched until this branch is independently validated.
