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

## Index (31 Oct 2026)

| Folder | What |
|---|---|
| `press_20261031/` | Shoulder press, before vs C1. Peak self-intersections 4934 → **7**, folds 4666 → **8**. |
| `curl_20261031/` | Biceps curl to 140°, before vs C1. Self-intersections 1663 → **2**, folds 200 → **17** (elbow 194 → 14). |
| `squat_20261031/` | Squat, before vs C1. Self-intersections 1308 → **0**, folds 1146 → **13**: hips 555 → **0**, knees 129 → 13. |
| `bent_over_row_20261031/` | Bent-over row, before vs C1. Self-intersections 1394 → **57**, folds 272 → **34** (elbow 162 → 11). |
| `push_up_20261031/` | Push-up, before vs C1. Self-intersections 2483 → **53**, folds 430 → **49** (elbow 169 → 11). |
| `lunge_20261031/` | Lunge (arms at the sides), before vs C1. Self-intersections 824 → **11**, folds 327 → **38** (knees 50 → 2). |
| `walk_stride_20261031/` | Walking stride (one gait cycle, played forward and looping; re-rendered 1 Nov), before vs C1. Self-intersections 182 → **0**, folds 33 → **6** (knees 26 → 0). |
| `forearm_rotation_20261031/` | Forearm rotation, before vs C1. Self-intersections 1894 → **0**, elbow folds 131 → **5**. |
| `grip_20261031/` | Grip (closed fist; re-rendered 1 Nov with a mesh-checked thumb and, for C1, the coupled girdle), before vs C1. Self-intersections 1480 → **155** (hand creases only), folds 228 → **6**. |
| `press_lockout_w5_20261101/` | Press lockout chest ripples, C1 vs candidate W5 (guarded delta mush on the lockout key). Lockout roughness p95 0.076 → **0.059 mm**; peak self-intersections and folds unchanged (7 / 8). |
| `app_candidate_v3_20261101/` | **The app integration candidate GLB, v3** (1 Nov): model W5 (C1 + smoothed lockout chest), 9 clips (v2's eight + grip). PT-App's preflight passes with no gaps; three.js within 0.048 mm of Blender; see its README. |
| `app_candidate_v2_20261101/` | v2 (C1, 8 clips), superseded by v3. README and checks kept; binary in git history (commit `37536ebb`). |
| `app_candidate_20261031/` | v1 (3 clips), superseded by v2. Its README and checks are kept; the binary is in git history (commit `80b91b02`). |

**Before** is the R120 surface with the r57 drives: the original r57 shoulder path for the press, and no R121
correctives. **After** is candidate C1. Both run through the same harness and the same fixed cameras. Every clip
returns to neutral exactly (0.0 mm). The curl and squat use the same path for both models: arms at the standing
carriage for the curl, arms forward for the squat.

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

- **Crinkling across the upper chest and a sharp V-ridge from the sternum to the shoulders** (front close-up).
  - It is identical with every shape key off, so it comes from the skinning.
  - A chest relief-restore patch to the lockout key is being built.
- **The armpit skin** has 9011 edges stretched more than 2× at lockout.

The rounded mass behind the arm in the side close-up is not on that list. It is the posterior armpit fold
(latissimus and teres major). It was judged anatomical against the owner's reference photos on 30 Oct and is kept;
only its pointed corner was an artifact, and that was fixed in AX6.

**Reproduce:** run `scripts/body_v2/movement_trajectory_test_blender.py` with `V2_TRAJ_ANIM=1 V2_TRAJ_FRAMES=49`, then
`anim_compose.py` and `encode_mp4_blender.py`. The environments are in `press_metrics.json`.
