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

## Current best candidate: AX6 (H3 plus a press-lockout arm key)

**AX6 (30 Oct)** is H3 plus one appended sideways-family key, `R121_ARM_<s>_153`. It is authored at the press lockout
and faired at the posterior armpit corner. Details are in the trajectories doc's AX6 section.

- At the press lockout:
  - the pointed corner where the posterior fold meets the arm is gone;
  - folds 13 → 8, crumple 489 → 282, self-intersections 10 → 7.
- Every other movement is identical to H3. H3 is kept for rollback.
- Chain step 11 (on H3): `V2_R121_ARMKEY_MODE=abd V2_R121_ARMKEY_APPEND=1 V2_R121_ARMKEY_POSE=press
  V2_R121_ARMKEY_ANGLES=160 V2_R121_ARMKEY_FAIR_CENTRE=0.176,0.118,1.387 V2_R121_ARMKEY_FAIR_R=0.05`.

### H3 (T3 plus re-authored elbow keys and deep hip key), the base of AX6

The blend is not in git (no `.blend` files are committed). H3 is rebuilt from R121p by this chain; every step is a
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
9. **Elbow (E8c):**
   - elbow keys re-authored with `V2_R121_CONTACT_MODE=plane_restore` (`V2_R121_POSTGUARD_ROUNDS=3`);
   - the press-rack combination key re-authored on top of them.
   - The exact commands are at the end of the trajectories doc's section E.
10. **Deep hip key (H3):** the 135° key re-authored with the guarded-restore hip contact. The command is in the
    trajectories doc's H3 section.

**Reproducing.** Every step of the chain, and every test or diagnostic of it, runs with
`V2_GIRDLE_FRAME=isb V2_R121_ARMKEY_CRUMPLE=6 V2_R121_ARMKEY_CRUMPLE_DEG=21` exported. The trajectory test also needs
`V2_TRAJ_GIRDLE=candidate V2_TRAJ_SQUAT_ARMS=forward`.

- Without `V2_GIRDLE_FRAME=isb` the candidate girdle falls back to a 35° scapular plane. The press and raises then
  measure differently: lockout folds 50 instead of 13, stretched edges 8766 instead of 9041.
- The reports now record the frame (`girdle_frame`).

All keys are driven by joint angles (`scripts/body_v2/r121_drives.py`), not by exercise. Two movements were never used
for authoring (the lateral and front raises), and two more were only used for one deep key (the deadlift and lunge);
they test that the system generalises.

**H3, full out-and-back trajectories** (`scripts/body_v2/movement_trajectory_test_blender.py`; reports in
`review-assets/body_v2/movement_trajectories_20261024/`: `report_TT_E8c_all7.json`, plus `report_TT_H3_deadlift_squat_lunge.json`
for the rows the deep hip key touches).

- Against T3, three things changed:
  - the curl row (T3: 7 / 697 / 0 / 68 / 1.28 / 6 mm);
  - the deadlift row (T3: 70 / 771 / 1885 / 1961);
  - the press-rack elbow folds (2 → 6).
- T3's own report, `report_TT_T3_all7.json`, is kept for rollback.

| Movement | Folds over 90° | Crumple over 35° | Self-intersections | Edges stretched over 2× | Asymmetry p95 / max | Return to neutral |
|---|---|---|---|---|---|---|
| Press (16° → rack → 160° → back) | 13 | 489 | 10 | 9041 | 1.38 / 40 mm | 0.0 mm |
| Curl (0 → 140° → 0) | 9 | 832 | 0 | 96 | 1.29 / 10 mm | 0.0 mm |
| Squat (arms forward, feet planted) | 13 | 502 | 0 | 4096 | 1.42 / 23 mm | 0.0 mm |
| Lateral raise, 0 → 90° (not authored for) | 4 | 295 | 0 | 1970 | 1.32 / 27 mm | 0.0 mm |
| Front raise, 0 → 90° (not authored for) | 7 | 287 | 0 | 2277 | 1.31 / 20 mm | 0.0 mm |
| Deadlift (hip to 135°, feet planted) | 68 | 801 | 1011 | 1980 | 1.36 / 8 mm | 0.0 mm |
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
- `REVIEW_T3_squat.jpg`. The squat is unchanged in H3.
- **H3:** `REVIEW_H3_curl.jpg`, `REVIEW_H3_deadlift.jpg`, `REVIEW_H3_lunge.jpg` (arms at the sides).
- **Close-ups:**
  - `elbow120_140_T3_vs_E8.jpg` (the elbow fix);
  - `press_rack_T3_vs_E8c.jpg`;
  - `deadlift_bottom_E8c_vs_H3.jpg`.

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
   - **Flat faces at 120–140° (E8c).** A plane contact still cuts the wider biceps flat. Now the upper-arm skin the
     contact moved is restored wherever it stays clear of the forearm, checked triangle against triangle both after
     the contact and after the relaxation.
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
- **Knee keys with the guarded restore (K2):** mixed (squat knee crumple 281 → 304). The knee contact is mostly real
  calf-on-hamstring overlap.
- **Elbow mutual-penetration contact (E1):** no plane, but at 140° it threw forearm skin into the chest (6193
  intersections).
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
- **Infraspinatus** (and the new subscapularis) shorten in the press under a humeral-head wrap and any external
  rotation from 0 to 60°. This is consistent with their elevation moment arms (Otis et al. 1994), so the contract's
  "near-isometric" is the questionable entry.
  - Teres minor (new) becomes near-isometric from about 40° of external rotation.
  - Teres minor and subscapularis anchors were added on 29 Oct (unreviewed).
- **Trapezius lower** lengthens 36–56 % under every girdle model tried, including a scapulothoracic-glide model with
  thorax contact. A rigid AC-pinned scapula cannot stay on the ribs at physiological clavicle angles.
  - This traces to the known a003/R41 transverse scapula defect: AA→TS is 227 mm against 113 ± 6.6 mm in male CT, and
    the AC breadth is 481 mm.
  - The skeleton tracker already records it as a confirmed rebuild defect.
  - The re-check belongs on the corrected girdle (c003/c004).
- **Gluteus medius** is a fan: its fibres change by −24 / −6 / +15 %, with a mean of −4.9 %.

**Defect fixed:** the serratus origin rule had placed it inside the thorax.

**MG1, first muscle geometry (30 Oct)**, on new experiment copies of R41 (never the source):

- Upper-arm belly and tendon envelopes: biceps long and short heads, brachialis, triceps long, lateral and medial
  heads.
- Both sides built independently, in Work's `HGPT_EXPERIMENT_MUSCLES` / `_TENDONS` collections, tagged with permanent
  IDs.
- Sized from this body's own humerus-to-skin space by an upper-arm cross-section rule. Results: 0 outside the skin,
  0 inside the bone radius, 0 muscle–muscle overlaps, source hash unchanged.
- The tendons follow the anatomical chain in elbow flexion.
- Literature volumes could not be fetched (the hosts are unreachable from the sandbox), so the reviewed
  `rest_volume_m3` stays null.
- Sheet: `experiments/anatomical_muscles/native_20261024/mg1/MG1_left_arm_sheet.jpg`.

**MG2, length response (30 Oct):**

- Work's kernel `belly_axes` with activation 0, so positioning only.
- Stored as per-angle rest-space shape keys: each section keeps its deep surface and its outer surface bulges.
- Through the curl the biceps shortens to 0.60 and thickens ×1.29 at 140°. Volume is held to 0.9994–1.0001 for every
  muscle at every angle.
- Still open:
  - deep-under-superficial layering (brachialis growing under the biceps; needs a layered or contact response, with
    the skin response);
  - the triceps medial head, which lengthens past the elbow instead of wrapping (needs a path-following sweep);
  - skin crossings under flexion (the skin does not bulge yet).
- Sheet: `native_20261024/mg2/MG2_left_curl_sheet.jpg`.
- **MG3 (layered response):** superficial bellies ride their deep neighbours' new surface. 0 muscle–muscle overlaps at
  every curl angle, both sides. The brachialis lifts the biceps up to 19 mm at 140°.
- **MG4 (deltoid, three heads, both sides):**
  - built as cylindrical sections along the shaft (inside the band MG1 reserves for it) plus a GH-spherical cap over the
    head;
  - 0 outside the skin or bone, 0 overlaps;
  - volumes 121 / 91 / 60 cm³ (anterior / middle / posterior);
  - sheet: `native_20261024/mg4/MG4_left_shoulder_sheet.jpg`.
- **MG5 (armpit-fold muscles, both sides, 30 Oct):** pectoralis major (clavicular and sternocostal heads),
  latissimus dorsi and teres major (`build_axillary_fold_envelopes_blender.py`, muscle branch 7fbb9cab).
  - Built as fan sheets: from authored origin lines, through via points found on the front and back armpit folds,
    to the humeral insertion lines, with each muscle's twist. They are cast onto the trunk skin from the thorax axis.
  - Layered: teres major under the latissimus, the pectoral heads under the anterior deltoid, the sternocostal head
    under the clavicular.
  - 0 outside the skin, 0 shallower than the layer, 0 overlaps.
  - Volumes 220 / 23 / 22 / 193 cm³ (latissimus / teres major / clavicular / sternocostal).
  - The latissimus and teres bellies end at the triceps long head; tendons run on to the humerus.
  - Rest pose only. R41 has no rib-cage surface, so the depth floor is the authored thickness.
  - Sheets: `native_20261024/mg5/MG5_left_axilla_sheet.jpg` and `MG5_right_axilla_sheet.jpg`.
  - Revised (muscle branch 67578e5c). The teres major and clavicular origins now cross their fibres; before, the
    sheets crossed themselves.
    - 0 outside the skin, 0 too shallow, 0 overlaps.
    - 5 self-crossing face pairs remain at the clavicular head's edge.
    - Volumes 219 / 53 / 50 / 185 cm³.
- **MG6a (read-only press check of the bound proxies):** R41's anatomical chain is posed natively through the press
  (coupled girdle).
  - Overlaps between envelopes: 6 at the start, 169 at the rack, 314 at the lockout, mostly between the deltoid heads.
  - The middle deltoid falls to 0.22 of its volume at the lockout.
  - The fans stretch up to 15.5×.
  - The bound proxies need a per-pose rebuild for elevation. Its skin has to come from a posed body, which R41's guide
    skeleton does not drive.
- **MG7 (leg muscles for the squat, both sides, 30 Oct; muscle branch fa650288):** quadriceps (rectus femoris and the
  three vasti), biceps femoris long, semitendinosus, semimembranosus, adductor magnus (hamstring part), medial
  gastrocnemius and soleus (`build_leg_muscle_envelopes_blender.py`).
  - MG1's compartment method on a femoral-shaft line and on KJC → AJC.
  - 0 outside the skin, 0 shallower than the layer, 0 inside the bone proxy, 0 self-crossings, 0 overlaps.
  - Squat check (native leg posing): 0 overlaps to knee 78°. At 102° the hamstrings meet the medial gastrocnemius
    behind the knee (92 face pairs), which needs a contact response.
- **MG8 (glutes, both sides, 30 Oct; muscle branch 466940bc):** gluteus maximus and medius, built by the MG5 fan
  builder in a new gluteal mode.
  - 0 outside the skin, 0 shallower than the layer, 0 self-crossings, 0 overlaps.
  - Volumes 345 / 144 cm³.
  - Squat: the glutes add no overlaps. The maximus keeps its volume (1.02); its edges stretch up to 2.1× at hip 100°.
  - **All 12 squat-contract muscles now have proxies.**
  - The builder's inside test is now a three-ray majority. A single ray gave false positives. MG5 moved at most
    0.9 mm with unchanged checks, and its reports were refreshed.
- **MG9a (bone-driven positioning through the press, 30 Oct; muscle branch 233f5d22): partial, not adopted.**
  - Rotation-blended Poisson deformation of each proxy sheet:
    - bone-fixed fibre ends; per-station rotations slerped by the authored humerus weight;
    - the along-fibre rest shape fades as fibres pull taut;
    - head, cuff, MG1 and thorax obstacles act on the deep surface; volume-preserving thickness;
    - the three deltoid heads are solved as one sheet; rest round trip 0.0001 mm.
  - **Through the rack (90°):**
    - deltoid volume 0.96 / 1.41 / 1.07, against MG6a's blended 0.56 / 0.41;
    - fans stretch about half as much (sternocostal pectoral 4.1× against 9.0×);
    - overlaps rise, 257 against 169, mostly a new latissimus / teres major contact.
  - **Above 120°** the deltoid folds: the glenohumeral joint turns about 107°, more than the cap's own angular span, so
    the sheet must unwrap. Six schemes were measured and none holds. Details and next steps are in the pass doc.
  - **Teres major / latissimus fibres reach 2.0× / 1.6×** at the lockout. This needs re-checking on the corrected
    girdle; R41's scapula is about twice as wide as the CT reference.
- **Muscle layer, next:**
  - a contact response behind the knee; the squat length response (MG2 / MG3's method);
  - the deltoid above 120°: a construction that changes curvature (a pose-aware rebuild by MG4's rules in a moving
    frame, or a volumetric simulation). MG9a's bone-driven positioning covers the press to the rack;
  - a per-pose latissimus / teres major separation pass;
  - the posterior-fold skin driven by the MG5 latissimus / teres volumes (the system-level route for open item 4);
  - rotator cuff and scapular muscles, which need a scapula surface (R41 has landmarks only);
  - skin response;
  - reviewer sign-off on the anchors.

## Decisions for the owner

- Adopting the candidate drives and keys (this changes the runtime contract), and replacing the r57 girdle directions.
- The reference build choice: V14 replay or deterministic.
- **Elbow pivot:** move it about 6 mm forward and 10 mm up, to the skin epicondyle midpoint.
  - On a copy, before keys: curl elbow folds 147 → 111.
  - It changes the validated skeleton.
- **Landmark re-binding.**
  - 20 of 51 body_v2 landmarks are stale (0 of 51 on R41).
  - A JSON proposal exists (`landmark_staleness_K1.json`).
- **Shoulder-girdle width** (a003/R41: AC breadth 481 mm, scapular spine about twice the CT length). Adopting the
  corrected c003/c004 girdle is the owner's call on validated skeletal data. The trapezius-lower verdict, and the
  serratus verdict's dependence on the girdle model, wait on it.
- **Posterior armpit corner at the lockout.** AX6 implements the sculpted posterior-fold key, authored at the press
  lockout. Keep it, or prefer a latissimus / teres major helper (re-binding) or muscle-driven skin later. The fold mass
  itself is judged anatomical.
- **Muscle contract entries:** triceps long (press), trapezius lower (press), infraspinatus and subscapularis
  (press), gluteus medius (squat). Each needs
  either a "variable" entry or functional heads, which would need new permanent IDs.

## Blocked

- **Anatomical review** of the landmarks and anchors needs a human reviewer.
- **NCBI / PMC** are unreachable from this sandbox, so regression joint centres (hip, GH) were not used.

## Open, unblocked (in rough priority)

1. **Press-lockout armpit stretch:** 9041 edges over 2×.
   - It is the skinning's: there are 11,421 with no corrective keys (`lockout_stretch_diag_blender.py`).
   - The shaded shape is right; it matters once a skin texture is used.
   - Three slide methods were measured and not adopted (above).
   - Next step: a parameter-domain (2D chart) slide, or wider upper-arm weights over the lat and side chest. The weights
     change the bind, so that needs owner approval, and every arm key would need re-authoring.
2. **Elbow at 140°.** Some flattening remains near the upper biceps, where the guards return skin to the plane contact
   (E8c fixed 120°).
3. **Deadlift abdomen–thigh contact at 135°.**
   - H3 cut it from 1885 to 1011 intersections (25 at the ~120° frame).
   - The rest lies outside the contact reach or in the groin.
   - 135° is past a conventional deadlift's depth.
4. **Posterior armpit fold at the lockout: judged, then fixed in AX6 (30 Oct).** The corner is gone with a
   press-lockout key (option 2 below). Options 1 and 3 remain for the owner. The judgement against the owner's
   reference photos:
   - the fold mass (latissimus and teres major) is anatomical and stays;
   - the pointed corner where it meets the arm is a skinning artifact (+6.3 mm at the 1.5 cm scale, +1.9 mm at rest).
     It is minor at phone scale.
   - Pose-ridge relief patched into the arm keys (AX1, AX2), and applied directly at the press, does not remove it. It
     needs a change of form: a latissimus / teres major helper (re-binding), a sculpted posterior-fold key, or
     muscle-driven skin. That is an owner decision.
   - Details are in the trajectories doc's last section. `axilla_fold_diag_blender.py` measures it.
5. **Lunge.** The benchmark's hanging hands meet the rising front thigh, a test-path artifact. With
   `V2_TRAJ_LUNGE_ARMS=side` (arms at 22°) the lunge has 11 intersections (front groin) and 35 folds.
6. **Muscle layer:**
   - a scapulothoracic model with translation;
   - fibre fans for trapezius and serratus (latissimus, pectoralis and teres major are built as MG5);
   - wrap paths;
   - belly and tendon geometry on an experiment copy.
