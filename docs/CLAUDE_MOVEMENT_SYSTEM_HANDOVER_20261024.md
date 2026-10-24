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

| | Before (R121p, r57 girdle, no new keys) | Now (candidate I5) |
|---|---|---|
| Press lockout: folds over 90° / self-intersections | 4666 / 4759 (peak) | 136 / 24 |
| Curl: elbow folds over 90° / self-intersections | 147 / 1641 | 4 / 865 (forearm meets the shoulder at 140°) |
| Squat: hip folds / heel lift | 586 / 11.3 mm | 0 / 0.0 mm |
| Return to neutral, all movements | 0.0000 mm | 0.0000 mm |
| Left/right asymmetry p95 | ≤ 3 mm | ≤ 3 mm |

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
4. **Squat hips:** hip keys. **Heel lift:** sole skin was shin-weighted; it now follows the foot.

All the keys are driven by joint angles (`scripts/body_v2/r121_drives.py`), not by exercise. Any movement that reaches
those angles uses them, which makes this a reusable movement system rather than a set of per-exercise fixes.

## Muscle layer (native pass)

- The pinned R41 copy is hash-verified. Work's inventory script was executed with Blender 5.2.1; this step had been
  BLOCKED.
- Anatomical left = +X = runtime `_r`, confirmed natively.
- Work's 46 ISB landmark requirements: **34 have native candidates** in R41; 12 are missing.
- Proposed origin and insertion anchors, with explicit textbook rules, for 20 left shoulder and arm muscles. They are
  **unreviewed**, so the validator still reports them as not ready.

## Blockers and next unblocked steps

**Owner decisions:**

- adopting the candidate drives and keys, which changes the runtime contract;
- replacing the r57 girdle directions;
- the reference build choice (V14 replay or deterministic).

**Blocked:**

- Anatomical review of the landmarks and anchors needs a human or anatomical reviewer.
- The NCBI/PMC literature servers are unreachable from this sandbox, so regression hip joint centres were not used.
- The body_v2 landmark empties are stale (R41 positions; body_v2's skeleton was refitted). They need re-binding before
  being used for positions; orientation use is fine.

**Next unblocked:**

1. **Rest-pose self-intersections** (1929: armpit 608, forearm–hip 420, hands 731). Resolve these as contact in the
   basis.
2. **Remaining sole slide** (17 mm) in the squat.
3. **Squat knee contact** (722 pairs at depth): hinge-contact keys for the knee, using the same method as the elbow.
4. **Skeleton-shift tests on a candidate copy:**
   - ankle pivot 16 mm above the malleolar line;
   - elbow pivot about 2 cm above and behind the epicondyle line.
5. **Elbow contact:** volume preservation, and the contact slit at 120–140°.
6. **Muscle layer:**
   - right side, derived independently rather than mirrored;
   - fans and digitations for the broad muscles;
   - wrap paths;
   - belly and tendon geometry on an experiment copy.
