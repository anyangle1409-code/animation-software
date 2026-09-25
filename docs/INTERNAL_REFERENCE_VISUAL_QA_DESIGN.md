# R3 deterministic visual QA — implementation design

R3 should compare locally generated candidate evidence to locally generated reference evidence without a cloud vision model.

## First checks

Use geometry and projected landmarks before image heuristics.

For every capture:

1. project canonical joint landmarks through the exact review camera;
2. normalize image coordinates by frame width/height;
3. compare candidate vs reference corridors;
4. compare equipment centre/axis;
5. calculate silhouette overlap/bounds where available.

Useful curl landmarks:

- shoulders;
- elbows;
- wrists/hands;
- upper torso;
- pelvis;
- dumbbell centres.

## Measurements

Store explainable values such as:

- elbow x/y screen offset relative to shoulder width;
- wrist height relative to torso height;
- hand-to-torso horizontal distance;
- left/right equipment height mismatch;
- candidate silhouette outside reference corridor;
- hand/equipment overlap;
- frame-to-frame projected trajectory deviation.

Every failure must name:

- capture/moment;
- view;
- landmark/equipment;
- measured value;
- allowed envelope;
- amount outside.

## Reference image source

Do not use photographs as runtime truth.

Generate a neutral reference pose/trajectory from the structured `ReferenceSpec`
and render it through the same camera/capture system.

The image is evidence. The underlying structured reference values remain the source of truth.

## Silhouette comparison

Start simple:

- alpha/body mask bounding box;
- left/right contour symmetry where expected;
- limb contour crossing torso where the reference says it should remain separate;
- equipment/body mask intersection.

Do not use raw pixel RMSE: different materials, lighting and character anatomy make it misleading.

## Deformation alarms

For production-character review, combine image evidence with mesh-space metrics:

- triangle stretch ratio;
- triangle area collapse;
- normal flips;
- self-intersection/contact checks already available;
- local left/right asymmetry.

A vision-only observation should never directly move the rig.

## Gate order

```
existing mechanical QA
  -> internal biomechanical reference QA
  -> deterministic projected-landmark QA
  -> silhouette/deformation QA
  -> bounded generator lever
  -> rerun every earlier gate
```

Local AI vision can be added later as an advisory detector, but it must not be required for the standalone system.
