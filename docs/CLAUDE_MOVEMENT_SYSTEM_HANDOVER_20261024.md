# Claude handover: anatomical movement system (24 Oct 2026)

All of this is candidate work on isolated branches. Nothing is merged or deployed, and nothing was written into:

- the approved original (R41), validated skeletal data, the r57 scripts, PT-App, or production assets;
- Work's branches (`work/phone-blender-workbench-20261023`, `work/experimental-anatomical-muscles-20261022`).

The permanent muscle IDs are used unchanged. Muscle highlighting is not implemented.

## Branches

| Branch | Contents |
|---|---|
| `claude/r120-surface-candidate-20261023` | Body v2 R121 surface, correctives, shoulder girdle, movement tests. Docs: `docs/R121_SURFACE_CANDIDATE_20261024.md`, `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md`, this file. |
| `claude/muscle-layer-native-20261024` | Based on Work's muscle experiment. Native R41 inventory, ISB landmark crosswalk and proposed anchors. Doc: `experiments/anatomical_muscles/CLAUDE_NATIVE_PASS_20261024.md`. |
| `claude/v14-recovery-investigation-20261023` / `claude/v14-deterministic-candidate-20261023` | The V14 vertex-count cause and the deterministic build (earlier). |

## What changed in the model's movement (measured, full out-and-back trajectories)

The test is `scripts/body_v2/movement_trajectory_test_blender.py`. Sheets: `trajectory_sheets.py`, written to
`review-assets/body_v2/movement_trajectories_20261024/`, sized for a phone.

| | Before (R121p, r57 girdle, no new keys) | Now (candidate **N2** = L4 + low forward key; review set `REVIEW_L4_*`) |
|---|---|---|
| Press: folds over 90° / self-intersections (peak) | 4666 / 4759 | **13 / 10** |
| Press lockout skin roughness, p95 (rest pose: 0.066 mm) | – (K1 had 0.125 mm, a mottled back) | **0.086 mm** |
| Curl: elbow folds over 90° / self-intersections | 147 / 1641 | 4 / 0 |
| Squat: self-intersections / heel lift | 1282 / 11.3 mm | **0 / 0.0 mm** |
| Lateral / front raise (not authored for): folds over 90° / self-intersections | – | **4 / 0** and **7 / 0** |
| Rest pose self-intersections | 1929 | 0 |
| Return to neutral, all movements | 0.0000 mm | 0.0000 mm |
| Left/right asymmetry p95 | ≤ 3 mm | ≤ 1.5 mm |

The candidate chain is:

1. R121p, the rebuilt surface.
2. Rest contact, the flap fix, and the hand contact made transient.
3. Sole weights.
4. Hip and knee keys (I-series).
5. K1 elbow keys (footprint contact).
6. **L4**: the legacy S1 / S3 / S5 / S7 shoulder keys neutralised, and the R121 arm, forward-raise and combination keys
   re-authored on the clean base.
7. **N2**: a low forward key (20°, measuring 11°) with the forward family's own start at 0°.

## Root causes established, each measured before anything was changed

1. **Press collapse.** On this rig, the r57 coupled girdle's scapular "upward rotation" and "posterior tilt" channels
   turn the scapula the wrong way: the glenoid moves down, and the inferior angle moves medially and off the ribs. Its
   clavicle roll is also carried rigidly into the scapula.

   *Fix:* `shoulder_girdle_candidate.py`. It uses the ISB scapula frame from the blend's own AA/TS/AI landmarks, pivots
   at the AC joint, and fixes each direction by checking landmark motion. One `apply_arm_pose` serves every arm raise.
   The r57 magnitudes are kept.
2. **Raised-arm crumple.** The rebuilt surface had no shoulder correctives of its own; the old ones were transferred.

   *Fix:* arm keys authored on the rebuilt surface with the girdle active, in sideways and forward families, blended by
   the plane of elevation.
3. **Elbow.**
   - The pivot sits at mid-depth.
   - The skin weights are a broad, symmetric 8 cm blend.
   - There is no forearm–biceps contact.

   *Fix:* elbow keys with hinge-contact flattening on the plane that bisects the elbow angle.
4. **Squat:**
   - *Hips:* hip keys.
   - *Knees:* hinge-contact knee keys.
   - *Heel lift:* sole skin was shin-weighted; it now follows the foot.
5. **Rest pose:** the arms interpenetrated the body.
   - *Fix:* a contact pass, plus the left-armpit flap removed.
   - The hand-on-thigh part is a transient key (driven by arm elevation), not a dent in the basis.

6. **Press rack:** a combination corrective (arm about 84° and elbow 90°): press elbow folds 90 → 20.
8. **Rough skin at the press lockout (L4, current best).** The legacy S1 / S3 / S5 / S7 shoulder keys transferred from
   the old surface injected the texture. Neutralising them and re-authoring the R121 arm families on the clean base
   gives:
   - lockout roughness p95 0.125 → 0.086 mm;
   - press folds 137 → 13;
   - press self-intersections 25 → 10;
   - squat self-intersections 30 → 1.
7. **Elbow at 120–140° (K1):** the upper arm was flattened wider than the forearm that presses on it.
   Mutual-footprint contact narrows the exposed flat face, and curl elbow crumple falls from 377 to 308 with 0
   intersections. The side-view crease is only partly fixed.

All the keys are driven by joint angles (`scripts/body_v2/r121_drives.py`), not by exercise. Any movement that reaches
those angles uses them, which makes this a reusable movement system rather than a set of per-exercise fixes.

## Muscle layer (native pass)

- The pinned R41 copy is hash-verified. Work's inventory script was executed with Blender 5.2.1; this step had been
  BLOCKED.
- Anatomical left = +X = runtime `_r`, confirmed natively.
- Work's 46 ISB landmark requirements: **34 have native candidates** in R41; 12 are missing.
- Proposed origin and insertion anchors, with explicit textbook rules, for 20 left shoulder and arm muscles. They are
  **unreviewed**, so the validator still reports them as not ready.
- **Path-length direction check against Work's exercise contract** (`path_length_direction_check_blender.py`):
  - The script poses R41's anatomical chain natively. That chain has no constraints to the runtime rig.
  - **Curl: 12 of 12 match** (biceps, brachialis and brachioradialis shorten; triceps long lengthens).
  - **Press: 10 match, with 3 muscles flagged** (each fails in both phases):
    - *Triceps long* lengthens 5 %, because 125° of shoulder elevation outweighs the elbow extension. This is a contract
      question for Work or the owner; the contract is not edited.
    - *Trapezius lower* needs scapulothoracic gliding before it can be judged.
    - *Infraspinatus* needs a wrap and humeral rotation.
  - The check also found a defect in the serratus origin: it was a rib-chord point inside the thorax. The rule was
    fixed on both sides, and serratus now shortens in the press, as the contract says.
- **Legs:** proposed anchors for the 12 squat muscles on both sides (unreviewed, mirror-exact), and a squat
  path-length check.
  - Result: **10 match, 12 contract "variable", 2 mismatches** (gluteus medius in the descent and the ascent).
  - Gluteus maximus only lengthens once it wraps behind the hip; as a straight line it runs through the joint.
  - Gluteus medius is a fan: its anterior fibres shorten by 20 % while its posterior fibres lengthen by 9 %. It needs
    a fibre fan before the contract's "near-isometric" can be checked.

## Blockers and next unblocked steps

**Owner decisions:**

- adopting the candidate drives and keys, which changes the runtime contract;
- replacing the r57 girdle directions;
- the reference build choice (V14 replay or deterministic);
- moving the elbow pivot about 6 mm forward and 10 mm up, to the skin epicondyle midpoint. The test on a copy gives
  curl elbow folds 147 → 111 before keys (`R121_MOVEMENT_TRAJECTORIES` doc, skeleton-shift test). It changes the
  validated skeleton.

**Blocked:**

- Anatomical review of the landmarks and anchors needs a human or anatomical reviewer.
- The NCBI/PMC literature servers are unreachable from this sandbox, so regression hip joint centres were not used.
- The body_v2 landmark empties are stale: 20 of 51 fail on K1, against 0 of 51 on R41
  (`landmark_staleness_audit_blender.py`).
  - A re-binding proposal exists as JSON (skin landmarks to the nearest skin; EJC, WJC, KJC and AJC to the ISB skin
    midpoints). It awaits review before being applied.
  - GH (36 mm from the rig pivot) needs regression or imaging data.

**Next unblocked:**

1. **Elbow at 120–140°:** the flat contact face and slit. (The curl top contact itself is fixed in I9.)

   (Done since the first version of this handover: the squat's 17 mm sole slide was the r57 path planting only the
   mean ankle. A per-leg plant in the test now gives 0.0 mm. Arms forward is available, through the thorax-relative
   girdle.)
4. **Skeleton-shift tests on a candidate copy: done.**
   - *Elbow:* a moderate gain (owner decision, above).
   - *Ankle:* not recommended. Sole slide improves only slightly, and 333 new foot–shin intersections appear.
5. **Elbow contact:** volume preservation, and the contact slit at 120–140°.
6. **Muscle layer:**
   - fibre fans for gluteus medius, trapezius, latissimus, pectoralis and serratus;
   - scapulothoracic gliding, needed for the trapezius lower verdict;
   - fans and digitations for the broad muscles;
   - wrap paths;
   - belly and tendon geometry on an experiment copy.
