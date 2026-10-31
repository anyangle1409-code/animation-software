# Push-up: before vs after (31 Oct 2026)

- **Before:** the R120 surface with the r57 drives and the benchmark's girdle-free push-up.
- **After:** candidate C1 with the coupled girdle on the push-up (`V2_TRAJ_PUSHUP_GIRDLE=1`) and the wrist keys.
- **Clip:** 49 rendered frames, top → bottom → top. Cameras are fitted to the skeleton and identical for both models.

| Peak over the repetition | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 2483 | **53** |
| Folds over 90° (whole body) | 430 | **49** |
| Folds over 90° (shoulders) | 119 | 46 |
| Folds over 90° (elbows) | 169 | **11** |
| Return to neutral | 0.03 mm | 0.24 mm |

**Still open on C1:** the forearm's own crease at full wrist extension, and the thumb base against the index
metacarpal (see the trajectories doc).

**Files:**

- `push_up_before_after_full.mp4` and `_close.mp4`;
- `STILLS_push_up_<view>.jpg`;
- `push_up_metrics.json`.
