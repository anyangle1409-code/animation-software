# Claude handover: anatomical movement system (24–29 Oct 2026)

All of this is candidate work on isolated branches. Nothing is merged or deployed, and nothing was written into:

- the approved original (R41), validated skeletal data, the r57 scripts, PT-App, or production assets;
- Work's branches (`work/phone-blender-workbench-20261023`, `work/experimental-anatomical-muscles-20261022`).

The permanent muscle IDs are used unchanged. Muscle highlighting is not implemented. The full measurement log, with
every attempt (adopted or not) and its numbers, is `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md`. This file is the
summary.

## Branches

| Branch | Contents |
|---|---|
| `claude/r120-surface-candidate-20261023` | Body v2 R121 surface, corrective keys and drives, shoulder girdle, movement tests and audits. Docs: `docs/R121_SURFACE_CANDIDATE_20261024.md`, `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md`, this file. |
| `claude/muscle-layer-native-20261024` | Based on Work's muscle experiment. Native R41 inventory, ISB landmark crosswalk, proposed anchors for the upper and lower limbs, path-length checks against the exercise contract. Doc: `experiments/anatomical_muscles/CLAUDE_NATIVE_PASS_20261024.md`. |
| `claude/v14-recovery-investigation-20261023` / `claude/v14-deterministic-candidate-20261023` | The V14 vertex-count cause and the deterministic build (earlier). |

## Current best candidate: T3

The blend is not in git (no `.blend` files are committed). T3 is rebuilt from R121p by this chain; every step is a
script in `scripts/body_v2/` and is recorded in the trajectories doc.

1. **R121p**: the rebuilt surface.
2. **Rest pose:** contact pass, left-armpit flap fix, and the hand-on-thigh contact made a transient key. Then the
   sole weights.
3. **Hip and knee keys** (squat 50 / 75 / 100 %; the knee keys use hinge contact).
4. **Elbow keys** with mutual-footprint hinge contact (K1).
5. **Shoulder (L4):**
   - legacy S1 / S3 / S5 / S7 shoulder keys neutralised;
   - R121 arm (sideways), forward-raise and press-rack combination keys re-authored on the clean base, with the
     candidate girdle.
6. **Low forward key (N2):** 20° (measuring 11°), and the forward family starts at 0°.
7. **Deep hip key (H1):** 135°, authored in the deadlift (`hinge` mode), appended to the hip family with the fold-in.
8. **Legs (T3):**
   - legacy hip family (H1_BAKE) low-pass filtered;
   - legacy knee family (K1_KNEE) zeroed;
   - hip, knee and deep-hip families re-authored.

All keys are driven by joint angles (`scripts/body_v2/r121_drives.py`), not by exercise. Two movements were never used
for authoring (the lateral and front raises), and two more were only used for one deep key (the deadlift and lunge);
they test that the system generalises.

**T3, full out-and-back trajectories** (`scripts/body_v2/movement_trajectory_test_blender.py`;
report `review-assets/body_v2/movement_trajectories_20261024/report_TT_T3_all7.json`):

| Movement | Folds over 90° | Crumple over 35° | Self-intersections | Edges stretched over 2× | Asymmetry p95 / max | Return to neutral |
|---|---|---|---|---|---|---|
| Press (16° → rack → 160° → back) | 13 | 489 | 10 | 9041 | 1.38 / 40 mm | 0.0 mm |
| Curl (0 → 140° → 0) | 7 | 697 | 0 | 68 | 1.28 / 6 mm | 0.0 mm |
| Squat (arms forward, feet planted) | 13 | 502 | 0 | 4096 | 1.42 / 23 mm | 0.0 mm |
| Lateral raise, 0 → 90° (not authored for) | 4 | 295 | 0 | 1970 | 1.32 / 27 mm | 0.0 mm |
| Front raise, 0 → 90° (not authored for) | 7 | 287 | 0 | 2277 | 1.31 / 20 mm | 0.0 mm |
| Deadlift (hip to 135°, feet planted) | 70 | 771 | 1885 | 1961 | 1.34 / 8 mm | 0.0 mm |
| Lunge (benchmark pose, asymmetric by design) | 50 | 932 | 169 | 1895 | n/a | 0.0 mm |

**Other measures:**

- Rest pose: 0 self-intersections.
- Skin roughness p95 (rest 0.066 mm):
  - press lockout 0.086 mm;
  - squat bottom 0.087 mm;
  - deadlift 0.086 mm.

**Before any of this** (R121p, r57 girdle, no new keys):

- press folds over 90° 4666, self-intersections 4759;
- curl self-intersections 1641;
- squat self-intersections 1282, heel lift 11 mm;
- rest pose 1929 self-intersections.

**Phone review sheets:**

- `REVIEW_L4_press.jpg`, `REVIEW_L4_curl.jpg`, `REVIEW_L4_lateral_raise.jpg`, `REVIEW_L4_front_raise.jpg`. The arm
  and shoulder keys behind these sheets are the same as T3's, except the front raise's start.
- `REVIEW_T3_squat.jpg`, `REVIEW_T3_deadlift.jpg`, `REVIEW_T3_lunge.jpg`.

## Root causes established (each measured before anything was changed)

1. **Press collapse.** The r57 coupled girdle's "upward rotation" and "posterior tilt" turn the scapula the wrong way
   on this rig.
   - *Fix:* `shoulder_girdle_candidate.py`. It uses the ISB scapula frame from the blend's own landmarks and pivots at
     the AC joint. Each rotation sign is fixed by a landmark probe. One `apply_arm_pose` serves every arm raise.
2. **Raised-arm crumple.** The rebuilt surface had no correctives of its own.
   - *Fix:* angle-driven arm and forward-raise keys, blended by the plane of elevation.
3. **Elbow.**
   - *Causes:* a mid-depth pivot, a broad symmetric weight blend, and no forearm–biceps contact.
   - *Fix:* hinge-contact elbow keys. Mutual-footprint contact stops the wider biceps being cut flat beyond the
     forearm.
4. **Squat.**
   - *Fix:* hip keys, hinge-contact knee keys, and sole skin bound to the foot (not the shin).
   - The sole slide was the test path's mean-ankle plant; the test now plants each leg.
5. **Rest pose.** The arms interpenetrated the body.
   - *Fix:* a contact pass, with the hand-on-thigh part made transient.
6. **Press rack.** Fixed with a combination corrective (arm about 84° and elbow 90°).
7. **Rough skin at the press lockout.** The legacy shoulder keys, transferred from the old surface, carry its texture
   (roughness p95 0.117 → 0.268 mm). The R121 keys authored on top of them cancelled the folds but kept the texture.
   - *Fix:* neutralise them and re-author on the clean base (L4).
8. **Rough legs and a lower-back fold.** The legacy hip and knee keys carry the same texture (squat 0.116 → 0.187 mm),
   but the hip family also fixes a real skinning fold across the lower back at the squat bottom.
   - *Fix:* low-pass filter the hip family, zero the knee family, re-author (T3).
9. **Front-raise start folds.** The forward family started at 25° of elevation.
   - *Fix:* a 20° key, with the family's own start at 0° (N2).
10. **Deadlift deep hip.** The hip keys stopped at 110°.
    - *Fix:* a 135° key appended to the family. The earlier keys' lost weight is folded into it, so the family
      reproduces the authored pose (H1).

## Lessons that apply beyond this model

- **Transferred legacy correctives:** low-pass filter them rather than zero them. Their centimetre-scale correction
  often still fits; their millimetre texture does not. One exception: a family that a new contact family replaces
  entirely (the knee).
- **Appending a key to a family changes the hats of the keys before it.** Fold their lost weight into the new key.
- **Mirror partners for symmetry checks** must share a mirrored dominant bone and a mirrored rest normal. Where limbs
  rest against the body, the nearest-point partner is the wrong surface.
  - One weight "fix" based on distance-only pairing wrecked every movement; it was caught and rejected.
- **mathutils is single precision.** Finite-difference solvers need steps of about 0.01°, or the Jacobian is zero.
- **Benchmark test paths contain artifacts:** mean-ankle planting, arms hung through the thighs, and a 135° "deadlift".
  Separate them from model faults before fixing anything.

## Tried and not adopted (all measured; details in the trajectories doc)

- **Skin slide** (Laplacian): smoother, but more stretch.
- **Stretch relief** (tangential springs): thousands of fold-overs.
- **Elbow soft lip.**
- **Elbow footprint at 4 mm** (until the 30 mm slab was used).
- **Whole-body and patch weight symmetrisation:** the armpit asymmetry is skinning on a differently tessellated patch.
- **Hip contact at the deadlift's extreme depth** (26 cm and 18 cm).
- **More relaxation rounds, and a 45° unfold, for the lower-back fold.**
- **Smoothed legacy shoulder keys:** better press, worse raises and symmetry.
- **Ankle pivot shift.**
- **Skin slide for the lockout stretch** (S1, 29 Oct):
  - posed-space mean-value tangential solve with projection (does not converge; crease sheets interpenetrate);
  - r57 surface walking (its 1.5 mm step jitters on this ~3 mm mesh; stable steps are diffusion-slow);
  - the solved field carried out by guarded walking (no new intersections, but folds triple for −11 % stretch).

## Muscle layer (native pass, branch `claude/muscle-layer-native-20261024`)

**Native setup:**

- The pinned R41 copy is hash-verified and unchanged throughout.
- Anatomical left = +X = runtime `_r`.
- 34 of Work's 46 ISB landmark requirements have native candidates.

**Proposed anchors** (unreviewed, so the validator keeps them "not ready"):

- 20 shoulder and arm muscles, both sides;
- 12 squat muscles, both sides;
- an optional `fibres` list for fan muscles (gluteus medius done).

**Path-length direction checks** against Work's exercise contract, on R41's own anatomical chain posed natively:

| Exercise | Result |
|---|---|
| Curl | 12 of 12 match |
| Press | 10 match; 3 muscles flagged in both phases |
| Squat | 10 match, 12 contract "variable", gluteus medius flagged |

The flagged muscles:

- **Triceps long** lengthens in the press. This is a contract question.
- **Infraspinatus** needs a wrap and humeral rotation.
- **Trapezius lower** lengthens 36–56 % under every girdle model tried, including a scapulothoracic-glide model with
  thorax contact. A rigid AC-pinned scapula cannot stay on the ribs at physiological clavicle angles.
- **Gluteus medius** is a fan: its fibres change by −24 / −6 / +15 %, with a mean of −4.9 %.

**Defect fixed:** the serratus origin rule had placed it inside the thorax.

## Decisions for the owner

- Adopting the candidate drives and keys (this changes the runtime contract), and replacing the r57 girdle directions.
- The reference build choice: V14 replay or deterministic.
- **Elbow pivot:** move it about 6 mm forward and 10 mm up, to the skin epicondyle midpoint.
  - On a copy, before keys: curl elbow folds 147 → 111.
  - It changes the validated skeleton.
- **Landmark re-binding.**
  - 20 of 51 body_v2 landmarks are stale (0 of 51 on R41).
  - A JSON proposal exists (`landmark_staleness_K1.json`).
- **Muscle contract entries:** triceps long (press), trapezius lower (press), gluteus medius (squat). Each needs
  either a "variable" entry or functional heads, which would need new permanent IDs.

## Blocked

- **Anatomical review** of the landmarks and anchors needs a human reviewer.
- **NCBI / PMC** are unreachable from this sandbox, so regression joint centres (hip, GH) were not used.

## Open, unblocked (in rough priority)

1. **Press-lockout armpit stretch:** 9041 edges over 2×.
   - It is the skinning's: there are 10,736 with no corrective keys (`lockout_stretch_diag_blender.py`).
   - The shaded shape is right; it matters once a skin texture is used.
   - Three slide methods were measured and not adopted (above).
   - Next step: a parameter-domain (2D chart) slide, or wider upper-arm weights over the lat and side chest. The weights
     change the bind, so that needs owner approval, and every arm key would need re-authoring.
2. **Elbow side crease at 120–140°:** partly fixed.
3. **Deadlift abdomen–thigh contact at 130–135°.** It is clean to 114°. Needs a non-planar contact surface, or a test
   path at realistic deadlift depth.
4. **Posterior armpit fold at the lockout:** comes from the skin weights, and part of it is anatomical. Needs a
   judgement against reference photos.
5. **Lunge:** the benchmark's abducted arms touch the legs. This is a test-path artifact.
6. **Muscle layer:**
   - a scapulothoracic model with translation;
   - fibre fans for trapezius, latissimus, pectoralis and serratus;
   - wrap paths;
   - belly and tendon geometry on an experiment copy.
