# R2 / early R3 offline review-QA scaffold status

## Branch

`work/internal-reference-engine-r2-scaffold-20260925`

Based on the core reference branch:

`work/internal-reference-engine-r0-r1-20260925`

The live source branch is untouched.

## Implemented

### Deterministic capture planning

- `src/reference/evidence.ts`
- `src/reference/capturePlan.ts`
- `src/reference/reviewCamera.ts`

A semantic review manifest can now be converted into renderer-ready capture
requests with:

- fixed dimensions;
- fixed DPR;
- neutral review backdrop marker;
- grid off;
- gizmos off;
- IK handles off;
- character view;
- deterministic camera intent.

Full-body views reuse the Studio camera presets.

The grip close-up no longer depends on the interactive Focus camera. It resolves
from the midpoint of `hand_l` and `hand_r` with an explicit camera offset and
FOV.

### Pure capture controller

- `src/reference/captureController.ts`

The controller:

1. snapshots user/editor viewport state;
2. applies each capture request in order;
3. waits for a deterministic settle barrier supplied by the browser bridge;
4. captures PNG bytes;
5. records evidence metadata;
6. restores the user's exact state in a `finally` block even if capture fails.

It has no React or WebGL dependency.

The only missing capture piece is the thin R3F/browser adapter that connects this
controller to the existing `Viewport.tsx` canvas.

### Solved-frame landmarks

- `src/reference/landmarks.ts`

Provides:

- exact canonical landmark positions at a clip time after IK/locks are resolved;
- normalized-time landmark trajectories.

This lets visual QA reason about the motion actually shown, rather than raw
authored poses.

### Body-size normalization

- `src/reference/normalize.ts`

Derives stable scales from the canonical rig:

- standing height;
- shoulder width;
- arm length;
- torso length.

Reference paths can therefore use body-relative units rather than pixels or one
character's absolute size.

### Trajectory comparison

- `src/reference/trajectory.ts`

Provides normalized landmark trajectories such as:

`hand relative to shoulder / arm length`

and candidate-vs-reference RMS/max deviation.

This is the foundation for detecting wrong paths over the whole repetition.

### Projected-landmark QA

- `src/reference/projection.ts`

Provides:

- deterministic 3D world -> normalized 2D image projection;
- resolution-independent landmark corridors;
- candidate/reference projected distance;
- explainable excess outside a corridor.

This is the first usable deterministic image-space QA layer and needs no vision
model.

## Tests prepared

- `capturePlan.test.ts`
- `captureController.test.ts`
- `reviewCamera.test.ts`
- `landmarks.test.ts`
- `normalize.test.ts`
- `trajectory.test.ts`
- `projection.test.ts`

These sit in addition to the R0/R1 reference tests inherited from the parent
branch.

## Deliberately not implemented here

- actual browser PNG extraction;
- reference mannequin rendering;
- silhouette-mask extraction;
- production gating;
- automatic correction from reference failures;
- local AI vision.

Those should follow only after this deterministic layer executes cleanly.

## Laptop validation

Run:

```
npm run typecheck
npm test -- \
  src/reference/evaluate.test.ts \
  src/reference/generation.test.ts \
  src/reference/reviewManifest.test.ts \
  src/reference/measure.test.ts \
  src/reference/capturePlan.test.ts \
  src/reference/captureController.test.ts \
  src/reference/reviewCamera.test.ts \
  src/reference/landmarks.test.ts \
  src/reference/normalize.test.ts \
  src/reference/trajectory.test.ts \
  src/reference/projection.test.ts
npm run build
```

If green, run `npm test`.

Do not merge into the live source branch until these checks are clean.

## Next implementation after validation

Only a thin browser bridge should be needed:

`ReviewCaptureBridge.tsx`

It should implement the `ReviewCaptureAdapter` interface using the existing
Studio store and R3F canvas.

Do not redesign semantic capture timing, camera policy, state restoration,
evidence metadata, normalization or projected-landmark QA; those pieces are
already isolated here.
