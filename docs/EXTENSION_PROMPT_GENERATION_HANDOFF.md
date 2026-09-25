# Triceps / elbow-extension prompt-generation handoff

## Branch

`work/prompt-generation-extension-latest-20260925`

Layered on the refreshed generator chain:
latest source → hinge/RDL → bent-over row → pull-up → extension.

The live source branch is unchanged.

## Added here

Two existing `extensionFamily()` variants become prompt-generatable:

```
Create an overhead dumbbell triceps extension with 8 kg dumbbells and slow tempo.
Create a cable triceps pushdown with controlled tempo.
```

### Overhead dumbbell extension
- existing `extensionFamily({ position: 'overhead' })`;
- reference: `dumbbell_overhead_triceps_extension`;
- paired dumbbells;
- neutral palms-facing grip;
- default 8 kg per hand;
- standing support.

### Cable pushdown
- existing `extensionFamily({ position: 'pushdown' })`;
- reference: `cable_triceps_pushdown`;
- cable tower + straight bar + cable;
- pronated grip;
- standing support;
- cable-stack resistance is not yet a family parameter, so a requested stack
  weight is rejected rather than silently ignored.

## Generic generator improvement

`IntentImplement` now supports `cable`.
`interpretCommon()` handles cable equipment explicitly, and the Generate panel
labels it "Cable station · straight bar" instead of incorrectly calling it
bodyweight.

## Explicit refusals

- ambiguous "triceps extension" without overhead vs pushdown;
- skull crusher;
- kickback;
- rope pushdown;
- reverse/underhand pushdown;
- single-arm/unilateral extension;
- lying/supine extension;
- arbitrary angle input;
- cable stack load, until resistance becomes a real family parameter.

## Protection

No extension-family biomechanics changed.
No existing exercise definition changed.
No validation threshold changed.
No rig, grip, retargeting or production asset changed.

CI validates typecheck, focused generator tests, build and full suite.
