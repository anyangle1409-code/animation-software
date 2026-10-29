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

## Elbow: cause and candidate fix (T2)

**Cause**, measured on the rebuilt arm. These are rig and skinning properties, not muscle geometry.

- **Pivot:** the forearm pivot (`forearm_*` head) sits near mid-depth of the elbow cross-section, 40.6 mm from the
  posterior skin and 48.0 mm from the anterior skin.
- **Flexion axis:** exactly medio-lateral (rig X), with no carrying angle.
- **Skin weights:** a broad, symmetric linear blend from about −40 mm to +40 mm round the joint line (0.50/0.50 at the
  pivot).
- **Correctives:** the only elbow keys are the old-surface K1 keys at 90° and 110°.

With plain linear-blend skinning this gives, in `elbow_closeups_before.jpg`:

- 60–90°: acceptable;
- 120°: a sharp V-fold at the front crease and a pointed "beak" at the back;
- 140°: the forearm passes into the biceps (1641 intersecting pairs), so the arm reads as one flat slab from the front.

There is no contact between forearm and biceps.

**Candidate fix:** keys `R121_ELBOW_<s>_<deg>` at 45 / 90 / 120 / 140°, authored on the rebuilt surface. They are driven
by `r121_drives.elbow_flex_deg`, the angle between the posed upper-arm and forearm, with hats from 10°. The keys are in
arm-local space through the skinning, so the same keys act in the press rack or any other shoulder pose. To author each
pose:

1. **Hinge contact.** The plane through the flexion axis that bisects the elbow angle is where the inner forearm and
   biceps skin meet. Skin of either side that has crossed it, on the inner side of the angle, is flattened onto it, then
   spread over 4 rings. Flattened vertices per side: 103 / 1529 / 5206 / 7470 at the four angles; left and right agree
   to within 0.3 %.
2. **Unfold and de-crumple**, as for the arm keys.
3. **Rest-space conversion** through the measured deformation matrices; fit residual ≤ 0.001 mm.

Rejected on the way: a nearest-surface "inside" test. It flags crease skin next to the joint line as penetrating (4469
at 45°) and its iterations do not converge (about 14k at 140°).

**Results:**

| Measure | Before | With elbow keys |
|---|---|---|
| Curl, elbow folds over 90° | 147 | 4 |
| Curl, elbow crumple over 35° | 1032 | 373 |
| Curl, self-intersections | 1641 | 865 |
| Press rack (arm at 90°), elbow folds | 204 | 106 |
| Press rack, elbow crumple | 1506 | 1437 |

The remaining curl intersections are all forearm or hand against the front of the shoulder at 134–140°: real contact at
the top of a curl. The squat is unchanged, and every trajectory returns to neutral (0.0000 mm).

Still open:

- The contact face leaves a sharp slit in the side view at 120–140°.
- Compressed tissue does not bulge sideways, so there is no volume preservation yet.
- The key's reach up the biceps adds 61 folds inside the rest-space shoulder box at 140°.
- The press rack is only partly fixed; its keys were authored with the arm at the side.

Images: `elbow_closeups_before.jpg`, `elbow_closeups_elbow_keys.jpg`, `curl_elbow_keys.jpg`,
`press_corrected_girdle_elbow_keys.jpg`, `squat_all_keys.jpg`. Report: `report_TT_all8.json`.

## Shoulder system (T3): one girdle for every arm raise, on the ISB scapula frame

**ISB frame.** R41 and body_v2 carry ISB landmark empties (`LM_scapula_*__AA/TS/AI`). The ISB scapula frame built from
them (Wu et al. 2005: Zs from TS to AA, Xs normal to the AA–TS–AI plane pointing forward, Ys = Zs × Xs) gives a
scapular plane **18.5°** from the frontal plane, tipped 6° forward. That replaces the 35° assumption
(`V2_GIRDLE_FRAME=isb`). Upward rotation is about Xs, posterior tilt about Zs, and internal rotation about Ys.

**Internal-rotation sign fixed.** It was being chosen from the glenoid end, which lies almost on the AC pivot, so the
sign was unreliable and the inferior angle moved forward. It is now probed at the inferior angle, which moves backward,
as it should for internal rotation.

**Same girdle for every raise.** `apply_arm_pose(rig, elevation, plane)` applies the coupled girdle for any arm raise,
not only the press. The arm keys (sideways and forward families) are re-authored with it active
(`V2_R121_ARMKEY_GIRDLE=1`). Every arm raise therefore runs one shoulder mechanism.

**Press lockout:**

| | r57 girdle + keys | girdle (35° plane) + keys authored on it | **girdle (ISB) + keys authored on it** |
|---|---|---|---|
| folds over 90° | 869 | 156 | **136** |
| crumple over 35° | 5071 | 1251 | **1201** |
| shoulder folds over 90° | 778 | 143 | **119** |
| self-intersections | 3738 | 41 | **24** |

The press now starts from the standing carriage, humerothoracic 16° (`V2_TRAJ_PRESS_START`); 0° drove the arm through
the hip. Over the full press trajectory (I5), self-intersections are 0–2 everywhere except 24–25 at the lockout armpit.
Return to neutral is 0.0000 mm.

**Squat sole (I5).** 3,622 sole vertices carried shin weight, under the heel. The heel pad is bound to the calcaneus, so
`foot_sole_weights_candidate_blender.py` moves shin weight to the foot bone on the sole, fading back to the original
weights by 30 mm above the floor. About 4,040 vertices per foot change, symmetric left and right.

- Squat heel lift: **11.3 → 0.0 mm**.
- Sole slide: 19.3 → 17.4 mm. The remaining slide is not from shin weights; still to be investigated.

Images: `I5_press.jpg`, `I5_curl.jpg`, `I5_squat.jpg`. Reports: `report_TT_I5.json`,
`report_TT_I4_isb_girdle_keys.json`, `report_TT_G4_plane35_girdle_keys.json`.

## Joint centres (body_v2 R121p)

`joint_centre_audit_blender.py` compares each rig pivot with the ISB/clinical centre derived from skin prominences, which
needs no regression coefficients:

- knee = midpoint of the femoral epicondyles;
- ankle = midpoint of the malleoli;
- elbow = midpoint of the humeral epicondyles;
- wrist = midpoint of the styloids.

Results (pivot minus centre, mm; left and right within 1.4 mm):

| Joint | Lateral | Anterior | Up | Reading |
|---|---|---|---|---|
| knee | −7 | −6 | −1 | well placed |
| ankle | +1 | +1 | **+16** | pivot above the widest malleolar line; a plausible contributor to squat foot slide |
| elbow | −1 | **−17** | **+22** | above and behind the epicondyle line |
| wrist | −6 | −3 | +18 | above the styloid line |
| hip | n/a | n/a | n/a | rig thigh heads coincide with R41's `LM_hip_bone_*__HJC` |

The skin "widest point" can be pulled by muscle bulk, so the elbow and wrist offsets are indicative. **Not changed:**
moving a validated joint centre means re-skinning, and the rules forbid overwriting validated skeletal data. These are
candidates for an isolated skeleton-shift test.

Literature servers (NCBI/PMC) were not reachable from this sandbox, so regression-based hip joint centres (Harrington
2007, Bell 1990) were not applied: their coefficients could not be verified.

Report: `joint_centre_audit_R121p.json`.

## Squat knee contact (I6)

**Method:** the elbow's hinge-contact recipe applied to the knee. Thigh-side and shin-side skin within 18 cm of the
knee is flattened onto the plane bisecting the knee angle, on its inner side, behind the knee. Then unfold and
de-crumple, and take the keys back to rest space.

- Keys: `R121_KNEE_<s>_<pct>` at benchmark squat depths 50 / 75 / 100 %.
- Driven by `r121_drives.knee_flex_deg` (thigh against shin direction), with hats from 20°.
- Measured knee flexion at the three depths: 52 / 90 / 107°.
- Flattened vertices per side: 573 / 2066–2082 / 3149–3174 (left and right within 1 %).

**Deep-squat results:**

| Measure | Before (I5) | With knee keys (I6) |
|---|---|---|
| Knee self-intersections | 722 | **0** |
| Knee folds over 90° | 123 | **20** |
| Whole-body folds | 138 | 43 |
| Whole-body crumple | 941 | 659 |

The remaining squat intersections (115) are all in the armpit, from the arm carriage: the rest-pose issue below. The
arm movements are unchanged (keys at 0).

Images: `squat_knees_knee_contact_keys.jpg`. Report: `report_TT_I6_squat_knee_keys.json`.

## Rest-pose contact and the left-armpit flap (I7, I8)

**Rest contact** (`rest_contact_candidate_blender.py`). The rig's rest pose, with the arms hanging and no carriage, had
1929 self-intersecting pairs.

- **Method:** arm triangles intersecting body triangles push their vertices laterally and the body's medially, 0.4 mm
  per step, spread over 3 rings. This repeats until no pair remains (101 iterations), then the displacement is smoothed.
  The basis and every key move together.
- **Result:** 6911 vertices moved, at most 18.9 mm.

**Flap fix** (`local_flap_fix_candidate_blender.py`). The evaluated rest pose, with the r57 drives applied, still had 168
pairs. All were in a 4 mm patch at the back of the **left** armpit: shoulder-cap skin overlapping itself, an R120 stitch
pleat that R121's unfold had left on that side.

- **Method:** local plain Laplacian smoothing over those triangles plus 4 rings.
- **Result:** 168 → 103 → 0, at most 5 mm, 944 vertices.

**Self-intersections per frame (I8):**

| Movement | Frames |
|---|---|
| press | 0 0 0 0 2 0 0 25 22 25 0 0 2 0 0 0 0 |
| curl | 0 … 0 598 865 598 0 … 0 (forearm and hand against the shoulder at 134–140°) |
| squat | 0 0 0 37 192 0 … 0 192 37 0 0 0 |

At mid-squat the benchmark keeps the arms hanging, so the hands sweep through the rising thighs. That is a test-path
matter, not a skin defect. Before these passes the squat's neutral frame had 1929 pairs and its deep frames 115.

The standing look is preserved: the inner arm is slightly flatter where it meets the chest (`standing_before_after_I8.jpg`).

Images: `I8_press.jpg`, `I8_curl.jpg`, `I8_squat.jpg`. Report: `report_TT_I8.json`.

## Squat ground contact and arms (I8)

**Cause of the sole slide.** The remaining 17 mm was not skin. Both **foot bones** slide 16.4 mm medially at depth while
staying flat. The r57 benchmark squat is forward kinematics and plants only the **mean** of the two ankles (via the
root), so the symmetric inward drift cancels in the mean.

**Fix (test path).** `plant_feet()` in the trajectory test turns each thigh about the forward axis through its hip
until the ankle is back over its rest position (the knee tracks slightly outwards), then re-plants the feet flat. The
r57 benchmark is unchanged. Result: sole slide **17.4 → 0.0 mm**, heel lift 0.0 mm, lowest skin exactly on the floor.
This meets the contract's "feet planted, knees tracking over feet" (`hgpt.exercise.squat.bodyweight.v1`).

**Arms.** The contract does not specify an arm posture. The r57 path lets the arms hang, so the hands sweep through the
rising thighs (up to 228 pairs). `V2_TRAJ_SQUAT_ARMS=forward` raises the arms forward to horizontal with the descent,
the usual counterbalance cue, through the girdle.

**Thorax-relative girdle.** For the arms-forward squat the girdle was made thorax-relative: it is built in the rest
frame and carried by the current spine_03 pose. It now works with trunk lean. Press results are identical, since the
thorax is at rest in the press.

**Squat, arms forward, feet planted:** self-intersections 0 except up to 30 at the armpit at depth; folds 52; knee
folds 20. Return to neutral is 0.0000 mm.

Images: `I8_squat_arms_forward_planted.jpg`. Report: `report_TT_I8_squat_arms_forward_planted.json`.

## Curl top contact (I9)

**Cause.** The remaining curl intersections (865 at 140°) were the distal forearm and hand meeting the upper biceps and
the front of the shoulder, more than 16 cm from the elbow: outside the elbow keys' contact reach.

**Fix.** The elbow family was re-authored on I8 with a 26 cm reach. `V2_R121_ARMKEY_REPLACE=1` drops the family's old
keys and drive data first, so the old keys aren't active during authoring and names don't collide.

| Curl | Before | I9 |
|---|---|---|
| Self-intersections | up to 865 | **0 at every frame** |
| Folds over 90° | 64 | 7 |
| Edges stretched over 2× | 559 | 60 |

The press is unchanged.

**Tried, not adopted.** A volume-preserving bulge: flattened tissue pushed sideways along the hinge axis by 0.6 × its
flattening depth (`V2_R121_CONTACT_BULGE`). Little visible effect (`elbow140_flatten_vs_bulge.jpg`).

**Open.** At 120–140° the contact still reads as a flat face with a crease slit (`elbow_closeups_I9_reach26.jpg`).

## Hand-on-thigh contact made transient (I11): the current review set

The rest-contact pass had flattened the outer thighs where the hanging hands touched them, up to 18.9 mm on about 1,640
thigh vertices, and stored that in the **basis**. The dent therefore stayed when the hands moved away.

`hand_contact_to_key_blender.py` takes the part below 0.52 H (3,821 vertices) out of the basis and every key, and stores
it as keys `R121_REST_HANDCONTACT_<s>`, driven by the arm's elevation: 1 at the rest elevation (0.97°), 0 eight degrees
above it. The small inner-arm/chest flattening (≤ 5 mm) stays in the basis.

**Review set, I11** (`REVIEW_I11_press.jpg`, `REVIEW_I11_curl.jpg`, `REVIEW_I11_squat.jpg`, `REVIEW_I11_report.json`):

| Movement | Folds over 90° | Self-intersections per frame | Feet | Return to neutral |
|---|---|---|---|---|
| press | 137 | 0 0 0 0 2 0 0 25 22 25 0 0 2 0 0 0 0 | n/a | 0.0000 mm |
| curl | 7 | 0 at every frame | n/a | 0.0000 mm |
| squat (arms forward, feet planted) | 52 | 0 1 0 0 0 0 14 30 27 30 14 0 0 0 0 1 0 | slide 0.0 mm, lift 0.0 mm | 0.0000 mm |

With the r57 hanging arms the squat has up to 234 pairs at mid-depth, from the hands sweeping the thighs (path).

## Press rack: a combination corrective (I12)

**Cause.** At the rack (arm raised about 84° by the girdle, elbow 90°, humeral external rotation 21°), 115 folds
remained. 84 of them were on the proximal forearm (`forearm_tw0`) next to the elbow. Muting the arm keys there gives
986 folds, so the arm keys work; the remainder is the **combination** that neither family was authored for.

**Fix.** Key `R121_COMBO_<s>`, authored at the rack in the elbow and upper-arm region (within 18 cm of the elbow). It is
driven by `tri(elevation; 84°, ±45°) × tri(elbow; 90°, ±45°)` (`r121_drives`), so it acts in any movement that reaches
that joint combination.

| Press | Before | With the combination key |
|---|---|---|
| Elbow folds over 90° | 90 | **20**; per frame 0 0 0 0 0 20 3 0 0 0 3 20 0 0 0 0 0 |
| Elbow crumple | 1445 | **268** |
| Whole-body crumple | 1673 | 1251 |

The curl and squat are unchanged: the key is off at their joint combinations. Report: `report_TT_I12_combo.json`.

## Open items (measured, next)

- **Elbow:** the curl is intersection-free (I9) and the press rack is fixed (I12). Still open: the flat contact face
  and slit at 120–140°.
- **Press lockout:** 6619 edges are still stretched more than 2× (armpit and lat skin), with residual armpit wrinkles.
- **Squat:** the knee contact, heel lift and sole slide are fixed; the arm path is above.
- **Rest-pose armpit and arm-hip intersections:** above.
- **Corrected girdle:**
  - the magnitudes are still the r57 project profile;
  - the 35° scapular plane is an assumption;
  - at lockout the inferior angle moves 107 mm anteriorly. Sliding round the chest wall is the right direction, but
    there is no thorax-contact check yet.
- **ISB landmarks:** still unbound (Work's gate). The axes here are thorax-frame constructions, not calibrated ISB
  segment frames.

## Tried, not adopted: tangential skin slide in the arm keys (J3)

**What was tried.** The arm (sideways and forward) keys were re-authored on I12 with an extra step, `V2_R121_ARMKEY_SLIDE=30`:
- 30 passes of Laplacian relaxation restricted to the surface tangent plane, on the upper body.
- The aim was to even out the skin stretch at lockout.
- The combination key was then rebuilt and the full trajectories re-run.

**Result (I12 → J3).**

| Measure | I12 | J3 |
|---|---|---|
| Press, folds over 90° | 137 | 124 |
| Press, shoulder crumple | 984 | 802 |
| Press, edges stretched over 2× | 7361 | 8297 |
| Press, edge-length p99 | 1.94 | 1.99 |
| Press, elbow folds | 20 | 65 |
| Press, self-intersections | 25 | 61 |
| Squat, self-intersections | 30 | 2 |

The slide made the skin smoother but more unevenly stretched: Laplacian smoothing evens out vertex positions, not edge
lengths. It is not adopted. I12 remains the current best.

The option stays in the script (default off). Report: `report_TT_J3_slide_not_adopted.json`.

## Elbow slit at 120–140°: soft lip tried, not adopted (K1 soft)

**What was tried.** `V2_R121_CONTACT_SOFT=0.012` draws skin within 12 mm of the hinge-contact face towards it, with a
falloff that meets the face tangentially. The aim was to roll the edges of the contact into a tight crease.

**Result.**
- The renders barely change (`elbow120_140_I12_vs_softlip.jpg`).
- Curl elbow folds rise from 4 to 17, and press elbow folds from 20 to 29.
- It is not adopted.

**What the comparison shows.** The visible flat triangle in the side view is the **upper arm's** flattened contact
face. It is left exposed because the biceps is wider along the hinge axis than the forearm that presses on it. Real
tissue is compressed only where the forearm touches.

**Next test.** `V2_R121_CONTACT_FOOTPRINT=<tol>` flattens each side only where the other side actually reaches the
contact plane. The run is in progress.

**Footprint, first run (K1, 4 mm slab).**

- **Renders.** At 120° the exposed flat triangle is mostly gone, and the biceps stays rounder
  (`elbow_I12_vs_footprint4mm.jpg`). 140° is little changed.
- **Curl metrics.** Elbow crumple falls from 377 to 308, but self-intersections rise from **0 to 968**. The footprint
  counted only forearm skin within 4 mm of the plane, so the unflattened biceps passed into the forearm's side walls.
- **Press.** Unchanged.
- **Verdict.** Not adopted as is. Report: `report_TT_K1_footprint4mm.json`.
- **Next.** Re-running with the footprint taken as the forearm's silhouette, from skin within a 30 mm slab
  (`V2_R121_CONTACT_FOOTPRINT_SLAB=0.030`).

**Footprint, adopted (K1, 30 mm slab).** The footprint is now the other side's skin within 30 mm of the contact plane,
so it is the forearm's silhouette, not just its nearest strip. Elbow keys were re-authored on I12 with
`V2_R121_CONTACT_FOOTPRINT=0.004 V2_R121_CONTACT_FOOTPRINT_SLAB=0.030` (45 / 90 / 120 / 140°, reach 26 cm).

| Curl | I12 | K1 |
|---|---|---|
| Self-intersections | 0 | 0 |
| Elbow crumple over 35° | 377 | **308** |
| Elbow folds over 90° | 4 | 4 |
| Edges stretched over 2× | 60 | 68 |

- Press: elbow crumple 268 → 263; everything else unchanged.
- Squat: unchanged.
- Every movement returns to neutral exactly.

Renders (`elbow120_140_I12_vs_K1_footprint30mm.jpg`): in the inner and front views the exposed flat face at 120–140°
is narrower. In the side view the crease is still a fairly sharp V. This is **partly fixed, not solved**: the remaining
crease is where the two contact faces meet the silhouette.

K1 is the current best candidate. Report: `report_TT_K1_footprint30mm.json`.

## Skeleton-shift test: elbow pivot (candidate copy, owner decision)

**Script.** `elbow_pivot_shift_candidate_blender.py`, run on a copy of the base R121p2, which has none of the new arm
keys. It moves only the forearm bone's head (disconnected from the upper arm) to the skin epicondyle midpoint. The rest
pose, mesh, weights and keys are unchanged.

**The shift.** Re-measured in world axes and mirror-averaged, it is 6.3 mm anterior and 9.6 mm up. That is smaller
than the joint audit's limb-frame figure; the left and right measurements were 11.7 and 7.5 mm up.

**Curl, before any elbow keys:**

| Measure | Pivot as built | Pivot shifted |
|---|---|---|
| Elbow folds over 90° | 147 | **111** |
| Elbow crumple over 35° | 1032 | **920** |
| All folds over 90° | 153 | 117 |
| Self-intersections | 1641 | 1559 |
| Edges stretched over 2× | 63 | 75 |
| Return to neutral | 0.0 mm | 0.0 mm |

- In `elbow_pivot_shift_R121p2.jpg` the elbow is slightly rounder at 60–90°. At 140° the result is still dominated by
  the missing contact handling.

**Verdict.** A moderate gain. This is the skin-landmark joint centre, so it supports moving the pivot. But it changes
the validated skeleton and the runtime rig's joint, so it is **not adopted: owner decision.**

If it is approved, the elbow, combination and press keys would be re-authored on the shifted rig. Reports:
`report_TT_EP0_pivot_as_built.json` and `report_TT_EP1_pivot_shifted.json`.

**Ankle (same script, `ankle`).** On a copy of R121p2, the foot bone's head was moved 16.4 mm down to the skin
malleolar midpoint. The shift is symmetric and matches the audit. Squat with the arms forward and the feet planted:

| Squat | Pivot as built | Pivot shifted |
|---|---|---|
| Sole slide | 11.1 mm | 8.8 mm |
| Heel lift | 11.4 mm | 10.6 mm |
| Self-intersections | 1282 | **1666** |

The new 333 intersections are foot against shin, at the front of the ankle: the lower pivot folds the dorsiflexed foot
into the shin.

The current candidate already has 0.0 mm sole slide and lift, through the sole weights and per-leg planting. The shift
therefore gains little and costs ankle-front contact that new keys would have to handle. **Not recommended.** It
stays recorded in case a future ankle corrective family is built.

Reports: `report_TT_AP0_ankle_as_built.json` and `report_TT_AP1_ankle_shifted.json`.

## Landmark staleness audit and re-binding proposal (read-only)

`landmark_staleness_audit_blender.py` checks each `LM_*` empty against the blend's own rest skin:

- *Skin landmarks* are stale if they are more than 4 mm from the skin.
- *Joint and bony landmarks* are stale if they lie outside the body (ray parity, 6 directions).

Run on the approved R41 copy (hash unchanged), **0 of 51** are stale. On body_v2 (K1), **20 of 51** are stale. The
landmarks were carried over unchanged when the surface was rebuilt and refitted.

| Landmark | Problem on body_v2 |
|---|---|
| Trochanterion | 35 mm inside the skin |
| Vertex | 30 mm inside the skin |
| IJ | 22 mm outside |
| Ulnar styloid | 18 mm outside |
| **Wrist centre (WJC)** | **18 mm outside the body, 66 mm from the rig's wrist pivot** |
| Chin | 16 mm outside |
| Lateral femoral epicondyle | 15 mm inside |
| Radial styloid | 12 mm inside |
| PX | 10 mm outside |
| ASIS | 5 mm inside |
| Medial malleolus | 4 mm inside |
| SC joints | about 3 mm outside |

**Re-binding proposal (JSON only; nothing applied).**

- Stale skin landmarks: the nearest skin point.
- EJC, WJC, KJC and AJC: the ISB skin midpoints from `joint_centre_audit_blender.py`. All of them are inside the body.
  - The re-bound WJC is 19 mm from the rig's wrist pivot (the stale one is 66 mm away).
  - Projecting R41's styloids to the nearest skin does not work: body_v2's wrist sits about 57 mm further forward, so
    both styloids land on the back of the wrist.
- HJC and GH: not proposed, because a skin proxy cannot give a deep joint centre.
  - HJC agrees with the rig (0 mm).
  - GH is 36 mm from the rig's shoulder pivot. It is inside the body, but it needs regression or imaging data before it
    can be resolved.

Applying the proposal would change landmark data in the candidate. That is left for review.

Files: `landmark_staleness_K1.json` and `landmark_staleness_R41_reference.json`.

## Press lockout: rough skin on the deltoids and upper back, cause found

`lockout_roughness_diag_blender.py` measures high-frequency roughness on the upper body at the press lockout (K1),
per vertex: |normal Laplacian − its neighbourhood mean|.

| State | p95 | p99 |
|---|---|---|
| Rest | 0.066 mm | 0.131 mm |
| Plain skinning, no corrective keys | 0.117 mm | 0.220 mm |
| Plus the legacy HGPT_S1 / S3 / S5 / S7 families | **0.268 mm** | **0.529 mm** |
| Plus the R121 keys (K1, what the review sheets show) | 0.125 mm | 0.212 mm |
| R121 keys without the legacy families | 0.238 mm | 0.499 mm |

Renders: `lockout_K1_vs_no_legacy_vs_lbs.jpg`.

- **Plain skinning:** the back is smooth, but the armpit and deltoid fold.
- **Legacy families:** they were transferred from the old surface and **inject the mottled texture**.
- **R121 keys:** they were authored *on top of* the legacy keys. They cancel the folds but carry the texture, so
  removing the legacy keys alone makes things worse.

**Cause.** The legacy shoulder families do not fit the rebuilt surface.

**Fix being tested.**

1. `neutralize_legacy_shoulder_keys_candidate_blender.py` zeroes the offsets of the S1 / S3 / S5 / S7 keys on a copy.
   The names and drives are kept, so this is reversible.
2. The R121 arm, forward-raise and combination families are re-authored on that clean base (L1 → L4).
3. The K1 elbow keys are kept.

**Result: L4 is adopted as the current best candidate.** L4 is K1 with the legacy S1 / S3 / S5 / S7 keys
neutralised, and the R121 arm, forward-raise and combination families re-authored on the clean base. The K1 elbow keys
are kept.

| | K1 | L4 |
|---|---|---|
| Lockout roughness p95 / p99 (rest: 0.066 / 0.131 mm) | 0.125 / 0.212 mm | **0.086 / 0.143 mm** |
| Press, folds over 90° | 137 | **13** |
| Press, shoulder crumple / folds | 984 / 120 | **326 / 13** |
| Press, elbow folds | 20 | **2** |
| Press, self-intersections | 25 | **10** |
| Press, edges collapsed under 0.5× | 9670 | **5384** |
| Press, edges stretched over 2× | 7361 | 9041 |
| Press, edge-length p99 | 1.94 | 2.04 |
| Press, asymmetry p95 | 2.88 mm | **1.40 mm** |
| Squat, self-intersections | 30 | **1** |
| Squat, edges stretched over 2× | 5524 | **4213** |
| Curl | – | unchanged |
| Return to neutral | exact | exact |

Renders: `lockout_K1_vs_L4_clean.jpg`.

- The upper back and deltoids are smooth now; the mottled texture is gone.
- What remains at the lockout:
  - more stretch at the armpit;
  - a rounded bulge at the back of the armpit in the side view. Plain skinning shows it too, so it comes from the
    binding, not from the keys.

Reports: `report_TT_L4_clean_shoulder.json`, `lockout_roughness_diag_L4.json` and
`r121_arm_correctives_combo_report_L4.json`. The arm and forward-raise authoring reports were lost when the
intermediate blends were cleaned up. The trajectory and roughness reports above are the evaluation.

## Posterior armpit at the lockout (L4): recorded, not changed

`lockout_posterior_axilla_L4.jpg` shows the side, back-three-quarter and back views at the lockout, with and without
corrective keys.

- **What it shows:** a rounded mass behind the armpit (latissimus / teres major), with a crease above it. It is
  identical with and without keys, so it comes from the skin weights, not the keys.
- **Anatomy:** a real overhead press also forms a convex posterior axillary fold there. Whether this one is too large
  is a judgement against reference photographs. It cannot be read off a metric, so nothing was changed.
- **Weights:** the region's weights are mixed — upperarm_r (0.49 mean), shoulder_cap_r, spine_02/03, muscle_lat_r and
  scapula_r.
- **If it is judged too big:** the next step would be a lat / teres helper weight, or a corrective on the posterior
  axillary fold at 120–160°.

## Asymmetry metric fixed; a small real asymmetry at the posterior armpit

**A measurement bug.** The trajectory test's maximum left/right asymmetry read about 800 mm while its p95 was about
1.3 mm. Wherever the arms or hands rest against the torso or thighs, the nearest mirror partner of a skin point can be
the *other* surface: for example a thigh vertex paired with the other hand's fingers, or torso skin paired with arm
skin.

A partner now counts only if:

- its dominant bone is the mirror of the vertex's own; and
- its rest normal is the mirror of the vertex's (the touching surfaces face opposite ways; this rejects 512 pairs).

Before this fix, every earlier `asymmetry_max_mm` value was meaningless; the p95 values were unaffected. On L4 with the
fix (`report_TT_L4_mirrorfix.json`):

| Movement | Max | p95 |
|---|---|---|
| Press | **40 mm** | 1.38 mm |
| Curl | 6 mm | 1.28 mm |
| Squat | 23 mm | 1.47 mm |

**The real asymmetry.** The press maximum is a patch of about 44 vertices at the posterior armpit (x ≈ ±0.174,
z ≈ 1.39). Its weights genuinely differ: one side carries about 0.19 upper-arm weight and the other none. With strict
pairing, only 28 pairs in the whole body differ by more than 0.2 (total-variation distance).

**A mistake on the way, rejected.** The first version of `symmetrize_weights_candidate_blender.py` paired by distance
only. It "found" 402 asymmetric pairs, which were almost all contact mispairs, and averaged torso skin with arm skin.
After re-authoring (M5 in the first run), every movement was wrecked:

- curl self-intersections 0 → 880;
- press self-intersections 10 → 4111.

It was not adopted. The script now uses the strict pairing. It changes 508 vertices by at most 0.24 weight, and the
pairs over 0.2 fall from 26 to 2. The arm, forward-raise, hip and combination families are being re-authored on that
base.

**Strict symmetrisation, re-authored (M5): not adopted.** The arm, forward-raise, hip and combination families were
re-authored on the strictly symmetrised weights. Changes from L4:

| | L4 | M5 |
|---|---|---|
| Press asymmetry max | 40 mm | 29 mm |
| Squat asymmetry max | 23 mm | 15 mm |
| Press shoulder folds over 90° | 13 | **183** |
| Press self-intersections | 10 | 22 |
| Curl shoulder folds over 90° | 1 | 19 |
| Lockout roughness p95 | 0.086 mm | 0.089 mm |

All other measures are unchanged, and every movement still returns to neutral.

The changed weights include the armpit patch that the rest-contact and corrective passes were tuned for. The trade is
worse, so L4 stays. Report: `report_TT_M5_symweights_not_adopted.json`.

**The armpit asymmetry stays open.** p95 is 1.4 mm, with a local maximum of 40 mm on a patch of about 44 vertices. The
safer next step is to symmetrise only that patch and re-check, rather than the whole body.

**Patch-only symmetrisation (P1): not adopted.** `V2_WSYM_BOX=0.16,0.19,0.03,0.09,1.35,1.42` changes 71 armpit vertices
by at most 0.08 weight. L4's keys were kept, without re-authoring.

| | L4 | P1 |
|---|---|---|
| Press asymmetry max | 40 mm | **40 mm** |
| Press folds over 90° | 13 | 112 |
| Press self-intersections | 10 | 24 |
| Squat folds over 90° | 40 | 103 |

The maximum does not move at all. A follow-up check found why:

- With **all shape keys off**, the lockout asymmetry maximum is the same 39.7 mm, so the keys are not the cause.
- The worst pair (vertices 297893 ↔ 112989) is 2.5 mm apart in rest-mirror space. That is outside the 2 mm pairing
  tolerance, so the patch fix never touched it: the rest mesh itself is slightly off-mirror there.

So it is a skinning asymmetry on a locally non-mirrored part of the mesh.

Even 0.08 weight changes in that patch disturb the folds the keys were tuned for. **L4 stays.** The armpit asymmetry
(p95 1.4 mm everywhere, a 40 mm local maximum) stays open. A fix would need a local re-mirroring of that patch's rest
shape and weights, with the keys re-authored afterwards.

**The armpit patch's off-mirror pair, measured.** Each vertex's mirror image was measured against the nearest *surface*
point, not the nearest vertex. On L4 that distance is p50 0.04 mm, p99 0.68 mm and max 9.5 mm, so the rest surface is
mirror-symmetric to well under 1 mm almost everywhere. In the posterior-armpit patch the maximum is 4.9 mm, where the
left-only flap fix moved vertices by up to 5 mm.

The 2.5 mm vertex-pair gap therefore comes from the two sides being **tessellated differently**, not from a different
shape. A proper fix would carry weights across by surface interpolation onto the mirrored triangle instead of nearest
vertex, and then re-author the armpit keys. That was not done, given how sensitive those folds proved.

**Closed for now.** p95 asymmetry is 1.4 mm; the armpit has a local 40 mm maximum at the full lockout.

## Generalisation: lateral and front raises (movements the keys were not authored for)

The trajectory test now has `lateral_raise` (plane 0°) and `front_raise` (plane 90°). Each runs straight-armed from the
16° standing carriage to 90° and back, through the coupled girdle. The R121 keys are driven by joint angles, so they
apply here without any exercise-specific authoring.

| L4 | Lateral raise, keys off → on | Front raise, keys off → on |
|---|---|---|
| Crumple over 35° | 524 → **295** | 1007 → **430** |
| Shoulder crumple | 274 → **140** | 779 → **275** |
| Folds over 90° | 17 → **4** | 52 → 47 |
| Self-intersections | 0 → 0 | 6 → **3** |
| Edges stretched over 2× | 1824 → 1970 | 2010 → 2277 |
| Asymmetry p95 / max | 1.3 / 27 mm | 1.3 / 20 mm |
| Return to neutral | exact | exact |

**One gap.** The front raise's remaining folds over 90° (about 40) are at its **start frame**: arms 16° forward of the
body, plane 90°. At 90° of elevation there are 0. The forward-raise keys start at 25° of elevation (`r121_drives.START`),
so a small forward carriage gets no correction.

**Next step.** A low forward key at about 16–20°, or an earlier start for the FLEX family.

Sheets: `REVIEW_L4_lateral_raise.jpg` and `REVIEW_L4_front_raise.jpg`. Reports: `report_TT_L4_raises.json` and
`report_TT_L4_raises_no_r121.json`.

**Low forward key: adopted as N2.** The FLEX family was re-authored on L4 with an extra key at 20°, which measures 11°
of humerothoracic elevation once posed with the girdle. The family now has its own start angle, rig property
`hgpt_r121_flex_start`. Existing blends without that property behave as before.

- **Start 10° (N1):** small gain only. The front raise's start frame still has 38 shoulder folds, because its measured
  elevation is below 10°.
- **Start 0° (N2):** front-raise start-frame shoulder folds 38 → **7**, and the squat (arms forward) shoulder folds
  38 → **7**. Press, curl and lateral raise are **unchanged**, and every movement returns to neutral exactly.

| N2 | Folds over 90° (peak) | Self-intersections | Asymmetry p95 / max |
|---|---|---|---|
| Press | 13 | 10 | 1.38 / 40 mm |
| Curl | 7 | 0 | 1.28 / 6 mm |
| Squat, arms forward | 20 | 0 | 1.47 / 23 mm |
| Lateral raise | 4 | 0 | 1.32 / 27 mm |
| Front raise | 7 | 0 | 1.31 / 20 mm |

**N2 is the current best candidate.** The script default for `V2_R121_FLEX_START` is now 0. Report:
`report_TT_N2_all_movements.json`.

## Generalisation, lower body: deadlift and lunge (N2)

The trajectory test now has `deadlift` and `lunge`, using the r57 benchmark poses.

| N2, keys off → on | Deadlift | Lunge |
|---|---|---|
| Crumple over 35° | 9149 → 2700 | 2462 → 1682 |
| Folds over 90° | 1867 → 399 | 339 → 278 |
| Hip folds over 90° | 1600 → 349 | 284 → 242 |
| Knee folds over 90° | 117 → 18 | 45 → 21 |
| Self-intersections (peak) | 4115 → 2052 | 824 → 180 |
| Return to neutral | exact | exact |

**Deadlift: where the peak comes from.** Hip flexion runs to **135°** (knee 103°), while the hip keys only cover the
squat range (55 / 93 / 110°).

- The movement is clean up to 114°.
- At 130–135° the abdomen and thighs interpenetrate (1755 hip-against-hip pairs).
- 135° is deeper than a conventional deadlift (about 80–110°) but within a full-depth squat, so a deeper hip key is
  worth adding (below).

**Deadlift: the start frames.** Their 300–400 hand-against-thigh intersections are a test-path artifact. The r57
deadlift hangs the arms vertically, closer in than the standing carriage, and they clear once the hinge begins.

**Deadlift: sole slide.** The 25 mm comes from the r57 deadlift path, which plants only the mean ankle. That is the
same issue the squat had, and it is fixed by the per-leg plant there, but the plant is not applied to the deadlift yet.

**Lunge.** It is asymmetric by design, and its root moves, so its asymmetry and sole numbers are not meaningful. Its
remaining intersections are hand-against-hip and leg, from the benchmark's abducted-arm pose.

**Next step.** A new authoring mode, `V2_R121_ARMKEY_MODE=hinge`, poses the benchmark deadlift and **appends** a key to
the hip family, named by its measured hip angle. The hip keys stay purely angle-driven. Running now, at about 135°.

Sheets: `REVIEW_N2_deadlift.jpg` and `REVIEW_N2_lunge.jpg`. Reports: `report_TT_N2_deadlift_lunge*.json`.

**Deep hip key, first attempt: rejected.** The key was authored at 135°, the deadlift bottom. Deadlift hip folds rose
from 349 to **1381** and self-intersections from 2052 to 3175. The other six movements were unchanged.

**Cause.** The key was authored as a residual on top of the hip family's 110° key, which was fully on beyond 110°
during authoring. Once the 135° key is appended, the 110° key fades out between 110° and 135°, so its correction
disappears at the bottom.

**Fix.** Hinge mode now folds what the earlier keys lose at the new angle into the new key, so the family reproduces
the authored pose exactly. Re-running.

**Deep hip key with the fold-in: adopted as H1.** The fold-in transfers the 110° key's full weight into the new 135° key.

| Deadlift | N2 | H1 |
|---|---|---|
| Crumple over 35° | 2700 | **745** |
| Folds over 90° | 399 | **72** |
| Hip folds over 90° | 349 | **28** |
| Edges stretched over 2× | 2784 | 2257 |
| Self-intersections | 2052 | 1827 |

Press, curl, squat, both raises and the lunge are identical to N2, and all seven movements return to neutral exactly.

**H1 is the current best candidate.** Report: `report_TT_H1_all7.json`.

**Still open.** At 130–135° there are 1530 hip-against-hip intersections: the abdomen and front of the thigh pass
through each other. That needs a contact step for the hip, like the knee and elbow hinge contact; relaxation alone
does not separate them.

**Hip contact in the deep hip key, 26 cm reach (H2): mixed, not adopted.** `V2_R121_HIP_CONTACT=1` flattens trunk and
thigh skin onto the plane bisecting the hip angle. About 7,600 vertices per side are flattened.

| Deadlift | H1 | H2 |
|---|---|---|
| Self-intersections | 1827 | **966** |
| Self-intersections at 130° | 668 | **177** |
| Folds over 90° | 72 | 160 |
| Hip folds | 28 | 111 |
| Edges collapsed under 0.5× | 10,438 | 14,353 |
| Edges stretched over 2× | 2257 | 3275 |

The other six movements are identical. The reach probably pulls in too much of the abdomen and thigh; retrying at
18 cm. Report: `report_TT_H2_hipcontact26.json`.

**Hip contact, 18 cm reach: worse, not adopted.** Deadlift self-intersections are 1646 (26 cm gave 966). Folds,
collapse and stretch rise as much as at 26 cm. Report: `report_TT_H2_hipcontact18.json`.

**Conclusion.** Bisector-plane contact does not give a clean win at 130–135° of hip flexion. That is beyond a
conventional deadlift (about 80–110°), and the movement is clean up to 114°. **H1 stays the current best.**

The abdomen–thigh interpenetration at the extreme is recorded as open. A better approach would be a contact surface
shaped like the abdomen (not a plane), or limiting the test path to realistic deadlift depth.

**Deadlift feet planted.** The test's deadlift now uses the same per-leg foot plant as the squat. On H1:

| Measure | Value |
|---|---|
| Sole slide / lift | **0.0 / 0.0 mm** (was 25 mm) |
| Folds over 90° | 68 |
| Hip folds | 19 |
| Knee folds | 18 |
| Self-intersections | 1861 (the extreme-depth abdomen–thigh contact above) |

Sheet: `REVIEW_H1_deadlift.jpg`. Report: `report_TT_H1_deadlift_planted.json`.

## Legacy leg keys: the same pattern as the shoulders

`leg_roughness_diag_blender.py` measures leg and hip roughness on H1: per vertex, |normal Laplacian − its neighbourhood
mean|, p95, over 0.30 < z < 1.15 m. The rest pose is 0.063 mm.

| Pose | Plain skinning | Legacy H1_BAKE / K1_KNEE only | All keys (H1) | R121 without legacy |
|---|---|---|---|---|
| Squat bottom | 0.116 mm | **0.187 mm** | 0.107 mm | 0.151 mm |
| Deadlift (114°) | 0.117 mm | **0.180 mm** | 0.098 mm | 0.135 mm |

The legacy hip and knee families were transferred from the old surface. They add about 60 % roughness, and the R121 hip
and knee keys, authored on top of them, cancel it. This is exactly the shoulder finding (L4).

**Running now (G-chain).**

1. Neutralise HGPT_H1_* and HGPT_K1_KNEE*.
2. Re-author the R121 hip family (squat 50 / 75 / 100), the knee family (with hinge contact) and the deep hinge key.
3. Re-run all seven movements and the leg roughness.

Report: `leg_roughness_diag_H1.json`.

**G3: legacy leg keys neutralised, hip / knee / deep-hip families re-authored.** Changes from H1:

| | H1 | G3 |
|---|---|---|
| Leg roughness p95, squat | 0.107 mm | **0.087 mm** |
| Leg roughness p95, deadlift | 0.098 mm | **0.085 mm** |
| Deadlift folds over 90° | 72 | **51** |
| Deadlift hip / knee folds | 28 / 18 | **8 / 0** |
| Deadlift self-intersections | 1827 | **1252** |
| Lunge folds over 90° | 278 | **61** |
| Lunge hip / knee folds | 242 / 21 | **43 / 0** |
| Squat knee folds | 20 | **13** |
| Squat edges stretched over 2× | 4213 | 7181 |
| Deadlift edges stretched over 2× | 2257 | 7215 |

Plain skinning gives 0.116 / 0.117 mm roughness, so G3 is now below it. The upper-body movements are unchanged.

**The extra stretch.** It is almost all on the buttocks and lower back (squat bottom: 869 → 3844 edges over 2×), where
skin really does stretch in a deep squat. The legacy H1_BAKE key had added slack there.

**A visible regression: a ridge across the lower back, at the top of the buttocks** (`legs_H1_vs_G3.jpg`,
`legs_squat_lbs_vs_H1nolegacy_vs_G3.jpg`). Measured as edge angles on the back of the waist at the squat bottom:

- Plain skinning has a real fold at z ≈ 1.08–1.10, with over 500 edges per 2 cm band past 21°.
- In H1, the legacy key cancelled it (about 0 edges).
- G3's relaxation leaves 61 edges past 21° at z 1.10; its squat-100 authoring report still shows 127 folds.

**Not adopted yet.** Re-running (G3b) with twice the relaxation rounds for the hip family (16 unfold, 12 de-crumple).
Reports: `report_TT_G3_legacy_legs_neutralised.json`, `leg_roughness_diag_G3.json`.

**G3b, twice the relaxation rounds: no effect.** The lower-back ridge is unchanged (54 edges past 21° at z 1.10, against
61 in G3), and every movement metric is within noise of G3. Report: `report_TT_G3b_more_rounds.json`.

**Why more rounds did not help.**

- The de-crumple step is HC smoothing, which is shape-preserving by design, so it keeps broad creases.
- The unfold step, a plain Laplacian, only acts on edges past 90°.
- The ridge's remaining edges are bent 21–71°, so neither step can remove them.
- (The "127 remaining folds" in the authoring report counts the whole body; 40 of them lie outside the hip region and
  never change.)

**Next try (G3c).** A new option, `V2_R121_ARMKEY_UNFOLD_DEG` (default 90, so behaviour is unchanged by default), lets
the unfold step also flatten creases. The hip family (squat and hinge) is being re-authored at 45°; the knee family is
unchanged.

**G3c, unfold threshold 45° on the hip family: partial, not adopted.**

- **Ridge:** the band maximum falls from 71° to 44°, but 57 edges past 21° remain at z 1.10, and the ridge is still
  visible (`legs_H1_G3_G3c.jpg`).
- **Not a mesh seam:** the ridge vertices lie on one rest edge loop at z = 1.102 with smooth rest angles (under 11°)
  and even density, so the ridge only forms in the pose.
- **Lunge:** worse than G3 (folds 61 → 127, hip folds 43 → 109). Deadlift crumple improves (717 → 517).

Report: `report_TT_G3c_unfold45.json`.

**Change of approach: smooth the legacy keys instead of zeroing them.** The legacy families carry two things:

- centimetre-scale corrections that still fit, such as the lower-back fold fix;
- millimetre-scale texture from the old surface, which is the roughness.

`smooth_legacy_keys_candidate_blender.py` low-pass filters each key's rest-space offset field (30 Laplacian rounds, about
16 mm characteristic length) and keeps the low-frequency correction. Running now (S-chain):

1. Smooth the H1_BAKE and K1_KNEE offset fields on H1.
2. Re-author the hip, knee and hinge families on top.
3. Re-run the ridge, leg roughness and all seven movements.

**S3: smoothed legacy leg keys, hip / knee / deep-hip re-authored. Best leg result so far.**

- **After smoothing alone:** the smoothed legacy keys give leg roughness 0.115 mm, the same as plain skinning, so the
  texture is gone. They still hold most of the lower-back fix: 27 edges past 21° at z 1.10, against 525 with plain
  skinning.

| | H1 | G3 (legacy zeroed) | S3 (legacy smoothed) |
|---|---|---|---|
| Lower-back ridge, edges past 21° at z 1.10 | about 1 | 61 | **0** |
| Leg roughness p95, squat / deadlift | 0.107 / 0.098 mm | 0.087 / 0.085 mm | **0.087 / 0.086 mm** |
| Squat folds over 90° | 20 | 13 | **10** |
| Squat stretched over 2× / collapsed | 4213 / 8314 | 7181 / 8510 | **4096 / 7702** |
| Deadlift folds over 90° (hip / knee) | 72 (28 / 18) | 51 (8 / 0) | 70 (21 / **31**) |
| Deadlift self-intersections | 1827 | 1252 | 1885 |
| Deadlift stretched over 2× | 2257 | 7215 | **1961** |
| Lunge folds over 90° (hip / knee) | 278 (242 / 21) | 61 (43 / 0) | 78 (32 / **33**) |
| Lunge stretched over 2× | 2140 | 2657 | **1895** |

The upper-body movements are unchanged, and every movement returns to neutral.

**The knee is the regression.** The smoothed K1_KNEE leaves knee folds of 31 (deadlift) and 33 (lunge); zeroed K1_KNEE
(G3) gave 0 in both.

**Running now (T-chain).** Smooth the legacy hip family, zero the legacy knee family, re-author all three.
Reports: `report_TT_S3_smoothed_legacy_legs.json`, `leg_roughness_diag_S3.json`.

**T3: legacy hip family smoothed, legacy knee family zeroed, hip / knee / deep-hip re-authored. Adopted as the current
best.**

| | H1 | S3 | **T3** |
|---|---|---|---|
| Lower-back ridge (edges past 21° at z 1.10) | about 1 | 0 | **0** |
| Leg roughness p95, squat / deadlift | 0.107 / 0.098 mm | 0.087 / 0.086 | **0.087 / 0.086 mm** |
| Squat folds over 90° | 20 | 10 | 13 |
| Squat collapsed under 0.5× | 8314 | 7702 | **7598** |
| Deadlift folds over 90° (hip / knee) | 72 (28 / 18) | 70 (21 / 31) | **70 (21 / 0)** |
| Deadlift stretched over 2× | 2257 | 1961 | **1961** |
| Deadlift self-intersections | 1827 | 1885 | 1885 |
| Lunge folds over 90° (hip / knee) | 278 (242 / 21) | 78 (32 / 33) | **50 (32 / 0)** |
| Lunge stretched over 2× | 2140 | 1895 | **1895** |

Press, curl and both raises are unchanged, and all seven movements return to neutral exactly. The deadlift's 3 %
higher intersection count is all at the extreme 130–135° depth (the open abdomen–thigh contact).

**The lesson, which also applies to the shoulders.** Legacy keys transferred from the old surface should be
**low-pass filtered, not zeroed**: their centimetre-scale corrections still fit; only their millimetre texture does
not. The knee family is the exception, because the R121 knee hinge-contact keys replace it entirely.

Reports: `report_TT_T3_all7.json`, `leg_roughness_diag_T3.json`.

**Applying the lesson to the shoulders (U-chain, running).** L4 zeroed the legacy shoulder families, and press-lockout
stretch rose (edges over 2×: 7361 → 9041), just as zeroing raised the leg stretch.

`transplant_key_offsets_candidate_blender.py` brings the original S1 / S3 / S5 / S7 offsets back from R121p2. The
topology is the same, and the bases differ by at most 5 mm. The offsets are low-pass filtered (30 rounds), and then the
arm, forward-raise (with the 20° key) and combination families are re-authored on top.

**U3: smoothed legacy shoulder families under re-authored arm keys. Mixed, not adopted.**

The smoothed families alone have lockout roughness 0.128 mm (raw: 0.268 mm; plain skinning: 0.117 mm), so the texture is
gone. With the arm keys re-authored on top, lockout roughness is 0.088 mm (T3: 0.086 mm).

| | T3 | U3 |
|---|---|---|
| Press: edges stretched over 2× | 9041 | **4977** |
| Press: edge-length p99 | 2.04 | **1.78** |
| Press: self-intersections | 10 | **5** |
| Press: elbow folds | 2 | **0** |
| Press: folds over 90° | 13 | 20 |
| Press: edges collapsed under 0.5× | 5384 | 6320 |
| Press: asymmetry p95 | 1.38 mm | **2.46 mm** |
| Lateral raise: stretched over 2× | 1970 | 3846 |
| Front raise: stretched over 2× | 2277 | 3781 |

The legs and curl are unchanged.

**Verdict.** The legacy shoulder families help the press, the path they were originally tuned on (the r57 coupled
press). They hurt the raises that use the candidate girdle, and they nearly double the press asymmetry. That works
against a reusable, angle-driven system. **T3 stays.**

Press-lockout stretch at the armpit remains the shoulder's open item. A girdle-consistent stretch-relief step, not a
legacy transplant, is the better route.

Report: `report_TT_U3_smoothed_legacy_shoulder_not_adopted.json`.

**V3: stretch relief (tangential springs towards the rest edge lengths), rejected.** `V2_R121_ARMKEY_STRETCH=60` was
used on the arm and forward-raise families.

| | T3 | V3 |
|---|---|---|
| Press folds over 90° | 13 | **9207** |
| Press self-intersections | 10 | 4193 |
| Front raise folds over 90° | 7 | 5626 |
| Lateral raise folds over 90° | 4 | 3397 |
| Press lockout roughness p95 | 0.086 mm | 0.176 mm |
| Press stretched over 2× | 9041 | 8274 |
| Press collapsed under 0.5× | 5384 | 2235 |

Stretch and collapse improve, but sliding vertices within the surface without a fold guard flips triangles wherever the
skin is compressed. It is not adopted; the option stays off by default.

A usable version would need an inversion guard: reject or halve any step that flips a face. That was not pursued here.
Report: `report_TT_V3_stretch_relief_rejected.json`.

## S1: press-lockout stretch (29 Oct 2026)

### Where the stretch is and what causes it

`scripts/body_v2/lockout_stretch_diag_blender.py` (read-only) measures the press lockout (candidate girdle, 160°,
elbows straight) in three configurations:

| Lockout | Over 2× | Over 1.5× | Under 0.5× | Max ratio |
|---|---|---|---|---|
| All keys (T3) | 8766 | 27,935 | 5691 | 68.9 |
| Without R121 keys | 8548 | 27,347 | 5113 | 68.9 |
| Plain skinning (no corrective keys) | 10,736 | 30,399 | 3471 | 55.8 |

- **The stretch comes from the skinning, not the keys.**
  - The upper-arm and shoulder-cap bones drag the skin of the side chest, lat and lower scapula up with the arm.
  - The R121 keys add only about 200 stretched edges.
  - The legacy (non-shoulder) families move some of it from the upper arm onto spine_03 and the back.
- **Location, all keys:**
  - stretched: deltoid cap 3699, back side / lat 2871, axilla floor 992, side chest 837;
  - compressed: deltoid cap 4187, mostly at shoulder_cap and clavicle (skin bunching over the acromion).
- **Size.** Stretched edges are short at rest (median 1.95 mm against 2.82 mm for all edges). Posed they measure
  5.5 mm median and 9.9 mm at p95.
- **The fix has to be a skin slide.** Real skin draws the area the opening axilla needs from a wide surround.

Renders: `lockout_stretch_diag_T3.jpg` (heat maps: red = an adjacent edge at 2× or more, blue = 0.5× or less; top row
all keys, bottom row plain skinning).

### V4: posed-space slide with rest mean-value weights (not adopted)

**Script:** `skin_slide_mvc_prototype_blender.py`, read-only.

**Method:**

- Each vertex's rest 1-ring gives positive mean-value weights (Floater). These reproduce the rest vertex exactly in its
  tangent plane, so the rest pose is a fixed point (checked: 0.004 mm).
- The posed shoulder region (0.30 m around each GH joint) is re-solved so each vertex sits, in its posed tangent plane,
  at the same weighted barycentre. There are 2 tangential unknowns per vertex, solved with a sparse direct solve, then
  projected back onto the posed surface.

**What it took to get a fixed point:**

- A first formulation (full 3D Laplacian keeping only its normal part) did not hold the surface. Rest drifted 94 mm.
- Even with exact weights, 18 rest rings with a reflex angle (and 2 degenerate hand–thigh vertices) leave residuals.
  A Laplacian solve spreads a point residual over centimetres, so those vertices are pinned.

**Results at the lockout:**

| | T3 | 3 rounds, full step | 6 rounds, full step | 4 rounds, half step, crease contact pinned |
|---|---|---|---|---|
| Over 2× | 8747 | 4606 | 4727 | 4442 |
| Under 0.5× | 5652 | 3769 | 5666 | 3355 |
| Folds over 90° | 50 | 61 | 166 | 82 |
| Self-intersections | 27 | 108 | 664 | 195 |

- The stretch spreads smoothly (heat maps) and the shaded shape is unchanged.
- The linearised steps do not converge: each round moves 10–35 mm whatever the damping. Every extra round adds
  self-intersections at the axilla and the posterior arm fold. Both sheets of the crease slide along each other.
- Pinning skin that has another sheet within 10 mm along its normal (240 vertices plus 3 rings) helps the first round
  (41 intersections) but not the later ones.
- A per-triangle inversion guard (revert flipped triangles' vertices) made things worse: 1349 intersections and 775
  folds. Partial reverts leave the slide field discontinuous, and folds already in the posed mesh trigger reverts every
  round.

**Verdict:** not adopted. Projection onto the posed surface lets vertices cross creases. The r57 surface-walking slide
(`original_v1_skin_slide.py`, R24) is built to avoid exactly that: vertices walk across triangle edges, and every step is
guarded. That is tried next (V5).

### V5: surface-walking slide (not adopted)

**r57 walker as is.** A run on the lockout (region 0.16–0.26 m around the GH joints, about 80k vertices, 60 iterations)
was stopped. The sequential walker costs about 390 µs per vertex step (about 35 min per pose). A benchmark also showed
its step is wrong for this mesh.

**`scripts/body_v2/skin_slide_walk_vec.py`** is the same algorithm vectorised. Free vertices are split into colour
classes (no two share a triangle), so each class walks and is guarded at once and the guards stay exact. It was checked
against r57 on a 3 mm test grid (36 cm square, with a compressed blob):

| 20 iterations | r57 | vectorised |
|---|---|---|
| Time | 68 s | 1.4 s |
| Energy (start 651) | 5649 | 5546 |
| Largest distance off the surface | 0.014 mm | 0.014 mm |

**Step size.** In both versions the energy *rises*, from 651 to about 5600. r57 moves every vertex a fixed 1.5 mm,
whatever its gradient, which jitters on a ~3 mm mesh; R24 ran on the coarser old mesh. Alternatives, measured as energy
after 150 iterations:

| Step | Energy |
|---|---|
| η = 0.3 | 1153 |
| Gradient-proportional | about 5700 |
| η = 0.1 | 633 |
| Diagonally preconditioned (α = 1) | 580 |

The stable steps are local, so the relief spreads like diffusion. Moving it across a 30 cm region would take on the
order of 10⁴ iterations.

**V4's global field carried out by the guarded walker** (`V2_SLIDE_METHOD=mvcwalk`):

| | T3 | 4 rounds, half step | 8 rounds, full step |
|---|---|---|---|
| Over 2× | 8747 | 8040 | 7745 |
| Folds over 90° | 50 | 93 | 160 |
| Crumple over 35° | 661 | n/a | 2069 |
| Self-intersections | 27 | 23 | 28 |

- No vertex crosses a crease any more: the intersections stay at T3's level.
- But the guard rejects 10k–44k vertex steps per round, mostly next to the triangles already crushed at the deltoid
  cap. The vertices next to them move without them, which fragments the field: stretch falls only 11 %, folds triple.

### Conclusion for S1

- The press-lockout stretch is a property of the skinning, not a defect of the corrective keys.
- The skin shape is right either way. Every tangential method above leaves the shaded surface unchanged. The stretch
  would show only once a skin texture or normal map is applied (texels about 2× larger under the arm).
- Two robust routes, both larger pieces of work:
  1. **A parameter-domain slide.** Relax in a 2D chart of the shoulder region (a UV island, or the rest surface with
     the arm hanging), then evaluate on the posed surface. That is how production skin-slide deformers avoid both crease
     crossing and guard fragmentation.
  2. **Wider skin weights.** Spread the upper-arm influence over the lat and side chest. This changes the bind, so every
     arm key would need re-authoring.
- **T3 stays.** The authoring hook added while testing (`V2_R121_ARMKEY_WALK`) was removed again, untested in authoring.
