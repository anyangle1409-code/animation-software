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

## Asymmetry metric fixed; real weight asymmetry found

**A measurement bug.** The trajectory test's maximum left/right asymmetry read about 800 mm while its p95 was about
1.3 mm. Where the hanging hands touch the thighs at rest, a thigh vertex's mirror image lands on the other hand's
fingers, which produced 229 wrong partners.

A mirror partner now counts only if its dominant bone is the mirror of the vertex's own. Before this fix, every earlier
`asymmetry_max_mm` value was meaningless; the p95 values were unaffected. On L4 with the fix
(`report_TT_L4_mirrorfix.json`):

| Movement | Max | p95 |
|---|---|---|
| Press | **92 mm** | 1.39 mm |
| Curl | 11 mm | 1.29 mm |
| Squat | **57 mm** | 1.47 mm |

**The real asymmetry behind those maxima.** The press maximum is at the posterior armpit. Runtime-right vertices carry
about 0.37 upperarm_r; their left partners carry about 0.0 upperarm_l, with spine_03 instead.

A weight-symmetry check (total-variation distance between a vertex's weights and its mirror partner's) finds
**402 pairs over 0.2** on L4 and 518 on R121p. They lie mainly at the posterior armpit and the hip crease. The
asymmetry was inherited from the surface rebuild.

**Fix being tested.** `symmetrize_weights_candidate_blender.py` mirror-averages every pair over 0.05, in rounds,
because nearest partners are not always mutual.

- It changes 1192 vertices (735 at the shoulder / armpit, 289 at the hip / thigh).
- Pairs over 0.2 fall from 402 to **1**.

The arm, forward-raise, hip and combination families are then re-authored on that base (M1 → M5).
