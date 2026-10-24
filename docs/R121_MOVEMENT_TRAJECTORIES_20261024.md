# R121 movement trajectories: press, curl, squat (24 Oct 2026)

Branch: `claude/r120-surface-candidate-20261023`. This is candidate work only. The original model, the validated skeleton,
the r57 scripts, Work's branch (`work/phone-blender-workbench-20261023`) and PT-App are not changed. Nothing is merged.

Work's branch measures the reconstructed **W8** surface read-only: edge-ratio timelines and key-family muting at fixed
press poses. This document covers the **rebuilt R120/R121 candidate** with full out-and-back trajectories. Its numbers are
not comparable one-to-one with Work's W8 numbers: different mesh, different metrics.

## Test

`scripts/body_v2/movement_trajectory_test_blender.py` is read-only and saves nothing to the blend. Each trajectory has
17 frames and starts and ends at neutral.

| Movement | Path |
|---|---|
| press | neutral → rack (humerothoracic target 90°, elbow 90°) → lockout (160°, elbow 0) → rack → neutral. Shoulder from the r57 coupled path (`apply_corrected_pose`), or from the corrected girdle (`V2_TRAJ_GIRDLE=candidate`, below). |
| curl | elbow 0 → 140° → 0, with arms at the standing carriage (16°). |
| squat | the r57 benchmark squat, depth 0 → 1 → 0. |

The r57 drives always run. The R121 candidate keys (arm, flex and hip families) run unless `V2_TRAJ_R121=0`.

Per frame the test records (hands and feet excluded):

- edges whose two faces differ by more than 35° ("crumple") or 90° ("fold"), whole body and per region (rest-space
  shoulder, elbow, hip and knee boxes);
- posed/rest edge-length ratio: p1 and p99, collapse (< 0.5×) and stretch (> 2×) counts;
- non-adjacent self-intersecting triangle pairs (BVH overlap), by region pair;
- left/right asymmetry: mirror-partner distance, p95 and max;
- lowest skin height against the rest floor, and sole slide and lift;
- return to neutral: last frame against first frame.

`scripts/body_v2/trajectory_sheets.py` makes the phone sheets. Each sheet has four sampled frames as rows and front /
side / back as columns, labelled with the numbers.

The edge ratios are geometric descriptors, not tissue strain. The rest-space boxes are not anatomical regions.

## Root cause found: the press girdle directions

At lockout, the r57 coupled path tore the rebuilt shoulder: the upper arm rolled into a tube under the shoulder skin
(`review-assets/body_v2/movement_trajectories_20261024/press_lockout_r57_vs_corrected_girdle.jpg`). To find out why, I
moved the humerus to the same direction but without clavicle or scapula motion. The shoulder then deforms acceptably, so
the girdle is the cause.

Next I applied each girdle channel alone at +30° on this rig and measured the landmarks: AC = clavicle tail, glenoid end =
scapula head, inferior end = scapula tail (about the inferior angle: 183 mm below the AC joint, 138 mm from the midline).

| Channel (r57 bone-local Euler) | Measured motion | Anatomical sense (ISB Part II, Wu et al. 2005) | Verdict |
|---|---|---|---|
| clavicle elevation (X) | AC up 90 mm | AC rises | correct |
| clavicle retraction (Z) | AC back 85 mm | AC moves posteriorly | correct |
| clavicle posterior rotation (Y) | AC fixed; scapula swings rigidly with the clavicle, inferior end 64 mm posterior and 56 mm up | the AC joint absorbs the roll; the scapula stays on the thorax | wrong mechanism |
| scapula upward rotation (Z) | glenoid **down** 20 mm, inferior end **medial** 36 mm | glenoid turns up, inferior angle swings laterally | **inverted** |
| scapula posterior tilt (X) | inferior end **posterior** 37 mm (off the ribs) | inferior angle moves anteriorly, onto the ribs | **inverted** |
| scapula internal rotation (Y) | glenoid forward 12 mm | glenoid faces more anteriorly | plausible |

At the r57 lockout (upward rotation 42°, tilt 17°, clavicle roll 28°) the scapula therefore turns down and lifts off the
thorax while the humerus is forced to 160°. The skin weighted to the scapula, which is the shoulder top (10k vertices), is
dragged the wrong way. This agrees with Work's observation that the W8 press fails worst between frames 3 and 8. Work's
notes also record that the side and frame conventions are uncertified.

**Candidate fix:** `scripts/body_v2/shoulder_girdle_candidate.py`. The r57 magnitudes (`pose_profile`) are unchanged;
only the directions and mechanism change.

- **Clavicle:** the r57 elevation and retraction channels as they were. The axial roll stays on the clavicle and is not
  passed to the scapula.
- **Scapula:** carried with the AC joint, turned about the AC joint in the thorax frame by:
  - posterior tilt, about the in-plane medio-lateral axis;
  - upward rotation, about the scapular-plane normal;
  - internal rotation, about the vertical axis.

  The scapular plane is taken 35° anterior to the frontal plane, because the rig's three scapula points are nearly
  collinear. Each direction is fixed by checking the landmark motion:
  - upward rotation: inferior angle lateral +75 mm per 30°, glenoid up;
  - posterior tilt: inferior angle anterior;
  - internal rotation: glenoid anterior.
- **Humerus:** the r57 target direction and axial rotation, applied after the girdle, as `apply_corrected_pose` does.

## Results

Peak values over each 17-frame trajectory; the curl and squat use the R121 candidate keys.

| | press, r57 girdle, no R121 keys | press, r57 girdle + keys | press, corrected girdle, no keys | **press, corrected girdle + keys** | curl (keys) | squat (keys) |
|---|---|---|---|---|---|---|
| folds over 90° | 4666 | 869 | 2898 | **296** | 153 | 138 |
| crumple over 35° | 20452 | 5071 | 16317 | **2121** | 1337 | 941 |
| shoulder folds over 90° | 3884 | 778 | 2471 | **236** | 4 | 41 |
| edges stretched over 2× | 16915 | 16323 | 9059 | **7108** | 63 | 1134 |
| p99 edge ratio | 2.48 | 2.46 | 2.04 | **1.93** | 1.17 | 1.60 |
| self-intersections (at lockout or depth) | 4759 | 3738 | 2841* | **149** at lockout | 1641 (elbow at 140°) | 1119 (knee at depth) |
| asymmetry p95 | 2.8 mm | 3.0 mm | 2.7 mm | 2.9 mm | 1.3 mm | 1.4 mm |
| return to neutral | 0.0000 mm | 0.0000 mm | 0.0000 mm | 0.0000 mm | 0.0000 mm | 0.0000 mm |

\* The peak of 2841 is at the press's own start pose, not at lockout. The press starts at humerothoracic 0° with the arm
pointing straight down in the 40° plane, which drives the forearm into the hip (925 pairs) and the hands into the thighs.
This is a test-path artifact.

The rest pose itself has 1929 self-intersecting pairs:

- arm into torso skin in the armpit: 608;
- forearm into hip: 420;
- hands into thighs or hips: 731.

This is a property of the rebuilt body in the rig's rest pose, with the arms close to the body. The standing review renders
use 16° carriage, which hides it.

Images (phone sheets) are in `review-assets/body_v2/movement_trajectories_20261024/`:

- `press_r57_girdle.jpg` and `press_corrected_girdle.jpg`;
- `press_lockout_r57_vs_corrected_girdle.jpg`;
- `curl.jpg` and `squat.jpg`;
- the per-frame JSON reports `report_*.json`.

## Open items (measured, next)

- **Elbow crease** at 90° (press rack) and in the curl: up to 206 folds. The curl at 140° has 1641 self-intersection
  pairs; the forearm sinks into the biceps where real tissue is in contact. That is task T2.
- **Press lockout:** 6619 edges are still stretched more than 2× (armpit and lat skin), with residual armpit wrinkles.
- **Squat:**
  - the back of the knee interpenetrates (722 pairs at depth);
  - sole skin slides 19 mm and lifts 11 mm (shin-weighted heel and ankle skin).
- **Rest-pose armpit and arm-hip intersections:** above.
- **Corrected girdle:**
  - the magnitudes are still the r57 project profile;
  - the 35° scapular plane is an assumption;
  - at lockout the inferior angle moves 107 mm anteriorly. Sliding round the chest wall is the right direction, but
    there is no thorax-contact check yet.
- **ISB landmarks:** still unbound (Work's gate). The axes here are thorax-frame constructions, not calibrated ISB
  segment frames.
