# Grip (closed fist): before vs after (31 Oct / 1 Nov 2026)

- **Before:** the R120 surface with the r57 drives.
- **After:** candidate C1.
- **Clip:** the r57 benchmark grip. The arms are held at 45° shoulder flexion with the elbows at 90°, the fingers close
  to a fist (MCP 80°, PIP 90°, DIP 60°) and open again. There are 33 rendered frames, shown at 16 fps.
- **Cameras:** fitted to the skeleton, identical for both models (whole body, both hands, and the left hand from the
  side).

## The thumb (same for both models)

r57's mesh-checked thumb search finds no placement on this surface, even with its thumb/finger contact limit raised
from 5 to 80. The thumb's own MCP and IP flexion already collapses a few crease faces in every candidate, and closing
the fist collapses 20 to 23 palm-knuckle faces per hand.

Both models therefore play r57's **skeleton-only** solution: the closest thumb tip with bony clearance
(`grip_thumb_solution.json`). Its skin contacts are measured below, not hidden.

| Peak over the repetition | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 2055 (elbow 1048, hand 730, shoulder 277) | **980** (hand 730, shoulder 250) |
| Folds over 90° (whole body) | 228 | **75** |
| Folds over 90° (elbows) | 125 | **5** |
| Return to neutral | 0.0 mm | 0.0 mm |

## What remains, and why

- **Hand, 730 pairs, the same in both models:** the closed fist presses the fingers into the palm skin. This is
  geometry the r57 grip angles create on this hand mesh, and no corrective in either model covers it. A knuckle and
  palm corrective (MCP-indexed keys) is the next hand task.
- **Shoulder, about 250 pairs, already present at the first frame:** the r57 grip poses the arms forward 45° with no
  shoulder-girdle motion, but the shoulder keys were authored with the coupled girdle. This is the same test-path
  issue the push-up had, and that one was fixed with `V2_TRAJ_PUSHUP_GIRDLE`. It is not a grip fault.

**Files:** `grip_before_after.mp4`, `STILLS_grip_<view>.jpg`, `grip_metrics.json`, `grip_thumb_solution.json`.
