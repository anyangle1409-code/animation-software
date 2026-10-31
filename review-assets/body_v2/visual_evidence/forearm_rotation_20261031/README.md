# Forearm rotation: before vs after (31 Oct 2026)

- **Before:** the R120 surface with the r57 drives.
- **After:** candidate C1 (forearm crease reweight, the wrist keys and the upper-arm twist bones).
- **Clip:** the r57 benchmark's pronation / supination with the elbows at 90°. There are 33 rendered frames, shown at
  16 fps.
- **Cameras:** fitted to the skeleton, identical for both models (whole body, both hands, and the left forearm from the
  side). The hands-front view in this clip is tight and cuts the hands at the frame edges; later clips use a wider one.

| Peak over the repetition | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 1894 | **0** |
| Folds over 90° (whole body) | 174 | 53 |
| Folds over 90° (elbows) | 131 | **5** |
| Return to neutral | 0.0 mm | 0.0 mm |

**Cause and fix:** the forearm-rotation rule turns the forearm's distal skin, but the elbow crease also carried part
of that weight. So the crease turned through the upper-arm skin, which is where the 1894 pairs come from. C1 moves that
weight onto the untwisted proximal twist bone near the elbow (`forearm_twist_candidate.py`).

**Files:** `forearm_rotation_before_after.mp4`, `STILLS_forearm_rotation_<view>.jpg`, `forearm_rotation_metrics.json`.
