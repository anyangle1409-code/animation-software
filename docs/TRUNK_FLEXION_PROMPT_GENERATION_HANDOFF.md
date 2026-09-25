# Trunk-flexion prompt-generation handoff

## Branch

`work/prompt-generation-trunk-flexion-latest-20260925`

Layered on the refreshed generator chain through farmer's walk.
The live source branch is unchanged.

## Added here

Two existing `trunkFlexionFamily()` motions become prompt-generatable:

```
Create a crunch with controlled tempo.
Create a sit-up with slow tempo.
```

### Crunch
- existing `trunkFlexionFamily({ motion: 'crunch' })`;
- reference: `crunch`;
- bodyweight, lying on the floor;
- lower back/hips remain down while the upper trunk curls.

### Sit-up
- existing `trunkFlexionFamily({ motion: 'situp' })`;
- reference: `sit_up`;
- bodyweight, lying start with floor-planted feet;
- full trunk/hip rise to sitting.

## Generic intent improvement

`IntentSupport` now includes `lying`, and the slot reader recognises:
- lying;
- supine;
- on the floor;
- on the back.

This lets floor-supported exercises describe their actual support instead of
being forced into a standing/seated label.

## Explicit refusals

- reverse crunch;
- bicycle crunch;
- oblique/side crunch;
- V-up/jackknife;
- incline/decline versions;
- weighted/dumbbell/plate/cable versions;
- contradictory crunch + sit-up request;
- non-lying support;
- requested hand grip.

## Protection

No trunk-flexion biomechanics changed.
No exercise definition changed.
No validation threshold changed.
No rig, retargeting, grip or production asset changed.

CI validates typecheck, focused parser/generator tests, build and full suite.
