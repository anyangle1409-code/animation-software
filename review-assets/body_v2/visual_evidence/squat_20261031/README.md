# Squat: before vs after (31 Oct 2026)

- **Before:** the R120 surface with the r57 drives and no R121 correctives.
- **After:** candidate C1 (R121 hip and knee keys, including the deep hip key authored in the deadlift; the
  hands-at-rest contact key).
- **Clip:** the r57 benchmark squat, with the arms forward for both models. There are 49 rendered frames per repetition.
  Cameras are fixed, with a floor at the rest sole height.

| Peak over the repetition | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 1308 | **0** |
| Folds over 90° (whole body) | 1146 | **13** |
| Folds over 90° (hips) | 555 | **0** |
| Folds over 90° (knees) | 129 | 13 |
| Edges stretched over 2× | 5835 | 4096 |
| Return to neutral | 0.0 mm | 0.0 mm |

**Before at neutral:** 124 self-intersections, the hands pressing into the thighs. C1 has 0.

**Files:**

- `squat_before_after_full.mp4`: real Blender animation, front / side / back.
- `STILLS_squat_<view>.jpg`: neutral, intermediate, maximum and return.
- `squat_metrics.json`: every frame, including floor contact and sole slide.
