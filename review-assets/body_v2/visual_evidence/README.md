# Visual evidence for phone review (Claude lane)

These are real Blender renders of the Body v2 model:

- Every video frame is a separately posed and rendered body. There are no slides and no interpolation.
- The cameras are fixed and orthographic, identical for both models and for every frame.
- The numbers under each row are measured on that exact frame: skin self-intersections (skin passing through skin),
  folds (edges creased past 90°), and shoulder folds.

The media are published as a GitHub Actions artifact by `.github/workflows/claude-visual-evidence.yml`
(artifact `claude-phone-evidence-<run id>`). Download it on the phone, unzip it in Files, and tap an MP4.

**Status:** these are candidates, not approved models. W8, V14, R120, ORIGINAL_v1, PT-App and `PT_MODEL_VERSION 1.0`
are unchanged.

## press_20261031: shoulder press, before vs after

- **Before:** the R120 surface with the original r57 shoulder path and drives. This is the model in the existing phone
  reviews.
- **After:** candidate C1:
  - the corrected scapula/clavicle press path (ISB frame);
  - the R121 arm, elbow, hip and knee correctives;
  - the upper-arm twist bones and forearm crease reweight.

  Its record is in `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md` (C1).
- **Clip:** 49 rendered frames per repetition (neutral → rack → lockout → rack → neutral), at 20 fps, shown twice.

| Peak over the repetition | Before | After (C1) |
|---|---|---|
| Skin self-intersections | 4934 | **7** |
| Folds over 90° (whole body) | 4666 | **8** |
| Folds over 90° (shoulders) | 3884 | **8** |
| Edges stretched over 2× | 17422 | 9011 |
| Return to neutral (max vertex offset) | 0.0 mm | 0.0 mm |

**Files:**

- `press_before_after_full.mp4`: full body, front / side / back.
- `press_before_after_close.mp4`: the shoulders close up, front / back / side.
- `STILLS_press_<view>.jpg`: neutral, rack (intermediate), lockout (maximum) and return to neutral, before and after.
- `press_metrics.json`: every number, per frame, for both models.

**What the before model does:** at lockout the shoulder tears. The upper arm rolls into a tube under the shoulder
skin, and the skin crumples front and back.

**What C1 does:** it keeps the shoulders coherent and smooth.

**Still visible on C1, and next to fix:**

- crinkling under the collarbones (front close-up);
- a lump behind the arm (side close-up);
- 9011 armpit edges stretched more than 2× at lockout.

**Reproduce:** run `scripts/body_v2/movement_trajectory_test_blender.py` with `V2_TRAJ_ANIM=1 V2_TRAJ_FRAMES=49`, then
`anim_compose.py` and `encode_mp4_blender.py`. The environments are in `press_metrics.json`.
