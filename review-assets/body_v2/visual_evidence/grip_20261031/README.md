# Grip (closed fist): before vs after (31 Oct; re-rendered 1 Nov 2026)

- **Before:** the R120 surface with the r57 drives.
- **After:** candidate C1.
- **Clip:** the r57 benchmark grip. The arms are held at 45° shoulder flexion with the elbows at 90°. The fingers close
  to a fist (MCP 80°, PIP 90°, DIP 60°) and open again. 33 rendered frames, shown at 16 fps.
- **Cameras:** fitted to the skeleton, identical for both models (whole body, both hands, and the left hand from the
  side).

## What changed on 1 Nov

1. **The thumb is mesh-checked now (same for both models).**
   - The r57 thumb search had never found a placement on this surface. Its baseline was measured before the thumb's
     own MCP and IP flexion, so those few crease faces counted against every candidate.
   - With that fixed, the search finds a left-hand placement within r57's own limit of 5 thumb-finger pairs. The right
     hand uses its mirror image (`grip_thumb_solution.json`).
   - Before, both models played a skeleton-only thumb.
2. **C1 holds the arms with the coupled shoulder girdle** (`V2_TRAJ_GRIP_GIRDLE=1`), as its shoulder keys were
   authored. The push-up uses the same option. The before model keeps the r57 pose.

| Peak over the repetition | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 1480 (elbow 1048, shoulder 277, hand 155) | **155** (hand only) |
| Folds over 90° (whole body) | 228 | **6** |
| Folds over 90° (elbows) | 125 | **5** |
| Folds over 90° (shoulders) | 101 | **1** |
| Return to neutral | 0.0 mm | 0.0 mm |

The 31 Oct version of C1 had 980 self-intersections (730 in the hands, 250 at the shoulders).

## What remains

**Hand, 155 pairs at the closed fist, the same in both models.** Thumb MCP crease 19 per hand, ring-finger knuckle
against the palm 12 per hand, and smaller knuckle creases. These are the creases of a tightly closed fist on this hand
mesh. MCP-indexed knuckle correctives are the next hand task.

**Files:** `grip_before_after.mp4`, `STILLS_grip_<view>.jpg` (open hand, closing, fist, open again), `grip_metrics.json`,
`grip_thumb_solution.json`.
