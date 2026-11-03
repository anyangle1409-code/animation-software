# Older model vs current candidates: standing and shoulder press (3 Nov 2026)

**Models compared:**

| Column | Model | What it is |
|---|---|---|
| R41 | `R41_SOURCE.blend`, ORIGINAL_v1 | The older slim model: 21,600 vertices and the r57 shoulder keys S1–S5. R47 and R52 were built on it in Work's pipeline; R52 with S7 muted equals R41. R47's own blend is not available here, so R41 stands in for "the older model" |
| W5 | Body v2, published candidate | The muscular body (347,917 vertices), C1 correctives + the lockout chest-ripple fix |
| W11 | Body v2, current candidate | W5 + front-armpit fairing + pec thinning + upper-arm band key + fist contact keys |

**Rendering:**

- **Skeleton motion:** identical in every column, the C1 press path (`movement_trajectory_test_blender.py`, 17
  frames). The frames shown are:
  - 0, standing;
  - 4, the rack (90°, elbows at 90°);
  - 6, intermediate (125°);
  - 7, near lockout (149°);
  - 8, lockout (160°).
- **Cameras:** identical orthographic cameras, lighting, material and scale.
- **Angles:** front, side, back and three-quarter (front-right, 45°), whole body (`STILLS_press_<view>.jpg`) and
  shoulders (`STILLS_press_<view>_upper.jpg`).
- **Captions:** the per-frame skin self-intersections and folds over 90°.

**Read with care:** R41's shoulder keys were authored for the old r57 scapula and clavicle path. Under C1's corrected
girdle path they no longer fit. R41 collapses from the rack on: self-intersections 206 at the rack and 1,137 at
lockout. So these columns show R41's proportions, not its approved press appearance. A second R41 set, on its own r57
motion, is added separately.

## Proportions against the owner's reference image

The reference image is not stored in git. Widths are front-view silhouette widths, each a fraction of standing height
(top of head to sole). The reference is measured from its front view; skin was segmented and checked visually.

| Level | Reference | W11 | R41 | Note |
|---|---|---|---|---|
| Shoulder line starts widening (height) | 0.834 | 0.857 | 0.864 | **W11's shoulders rise about 4 cm higher** |
| Width at 0.80 (top of the shoulders) | 0.24–0.26 | **0.31–0.32** | 0.32 | Square, high upper trapezius and deltoid cap |
| Shoulders, outer maximum | 0.288 | **0.343** | 0.323 | The model's arms are at 16° (the reference's at about 8°). About 0.32 after correcting for that, so still about 11 % wide |
| Chest under the armpits | 0.18–0.19 | 0.194 | 0.17 | |
| Waist | 0.163 | 0.162 | 0.145 | Matches |
| Upper arm, mid | 0.060 | 0.062 | 0.055 | Matches |
| Forearm | 0.057 | 0.061 | 0.051 | |
| Thigh at 0.37 | 0.091 | **0.081** | 0.088 | **The lower thigh is about 11 % thin** |
| Knee | 0.060 | 0.063 | 0.058 | Matches |
| Calf | 0.075 | 0.074 | 0.067 | Matches |
| Ankle | 0.034 | 0.034 | 0.035 | Matches |
| Neck | 0.073 | 0.077 | 0.07 | |

**Not measurable from the reference:** the hips and upper thighs (shorts) and the feet (shoes).

**Uncertainty:** the reference is a single photograph. Expect a few per cent from perspective and pose.
