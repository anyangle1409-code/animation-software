# Walking stride: before vs after (31 Oct 2026; re-rendered 1 Nov)

- **Before:** the R120 surface with the r57 drives.
- **After:** candidate C1.
- **Clip:** the r57 benchmark stride, which is one whole gait cycle:
  - right heel strike → left swing → left heel strike → right swing → right heel strike;
  - both models use a 16° arm carriage;
  - 49 rendered frames, shown twice at 20 fps;
  - cameras fitted to the skeleton, identical for both models.

  The walk is on the spot, as on a treadmill: the pelvis does not travel forward.

**Fixed on 1 Nov:** the first version played the cycle forward and then the same cycle backwards, so the second half
was a backward walk. The clip now plays the cycle once, forward. Its last frame is its first, so it loops. The harness
option is `V2_TRAJ_WALK_CYCLE=forward` (the default); `=outback` reproduces the old clip.

| Peak over the cycle | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 182 (knee against knee, in both swing phases) | **0** |
| Folds over 90° (whole body) | 33 | **6** |
| Folds over 90° (knees) | 26 | **0** |
| Lowest skin above the rest floor | 1.45 mm | 1.45 mm |
| Loop (last frame vs first) | 0.0 mm | 0.0 mm |

**Stills:** right heel strike, left swing, left heel strike and right swing (frames 1, 13, 25 and 37 of 49). A gait
has no single "maximum", so the four phases replace the usual neutral / intermediate / maximum / return.

**Files:** `walk_stride_before_after.mp4`, `STILLS_walk_stride_<view>.jpg`, `walk_stride_metrics.json`.
