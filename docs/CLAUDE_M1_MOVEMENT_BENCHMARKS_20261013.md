# M1/M2: ORIGINAL_v1 integration benchmarks — squat, row, press, lunge, walk, trunk rotation, grip, single-leg stance, calf raise (Claude, 13 Oct 2026)

- **Branch:** `claude/movement-benchmarks-20261013`, stacked on draft PR #111 (`13cea5a5`).
- **Script:** `scripts/build_original_movement_benchmarks_blender.py`.
- **Test:** `scripts/blender_tests/test_original_movement_benchmarks.py` (11 native tests PASS).
- **Report:** `ORIGINAL_V1_WORK/anatomy/audit/claude_m1/movement_benchmarks_report.json`, with phone sheets beside it.
- **Scope:** the unchanged 17,946-vertex original male on the 67-joint rig; source blend `670a37bf…cbbe56`. This is diagnostic forward-kinematics movement evidence only. Nothing (motion, deformation, anatomy, GLB, clinical, production) is approved.

## Method

**Paths.** Each benchmark is a 9-frame smoothstep keyframe path.

**Joint ceiling.** Peak joint angles stay at or below the CDC/Soucie 2011 passive means for males aged 20–44, as recorded in `whole_body_movement_atlas.json`: hip flexion 130.4°, knee 137.7°, shoulder flexion 168.8°, elbow 144.6°, ankle dorsiflexion 12.7°.

**Rig conventions** (measured on the rig): hip flexion = thigh −X; knee flexion = shin +X; ankle dorsiflexion = foot −X; shoulder flexion = upper-arm −X; elbow flexion = forearm −X; trunk flexion = pelvis/spine +X.

**Feet.** Kept flat, with both ankle heads planted by translating the root. The lowest point is within 1 mm of the floor in every frame.

**Benchmarks.**
- **Squat:** pelvis tilted 25° forward, hips 110°, knees 110°, lumbar extension 10°.
- **Bent-over row:** 45° hip hinge with knees at 20°, then the pull: shoulders from 45° flexion to 40° extension, elbows to 100°, clavicle retraction 12° (PR110 semantics).
- **Shoulder press:** the reviewed PR110/PR111 coupled shoulder motion from 90° to 160° humerothoracic elevation, with the elbows extending from 90° to 0°.

**Metrics per frame:** whole-body collapse (< 0.1 area ratio), stretch (> 2), self-intersecting pairs grouped by dominant skin group, and exact closed-mesh volume change.

## Results

| Benchmark | Worst collapse | Worst stretch > 2 | Worst self-intersecting pairs | Volume Δ % | Dominant contact at end | Exceeds CDC passive mean |
|---|---|---|---|---|---|---|
| Squat | 26 | 56 | 371 | −4.3 … +0.2 | calf/thigh (72 per side), thigh/thigh (61) | ankle dorsiflexion 25° (+12.3) |
| Bent-over row | 2 | 0 | 156 | −3.0 … +0.5 | forearm twist/upper arm, elbow crease (44 per side) | ankle dorsiflexion 20° (+7.3) |
| Shoulder press | 48 | 438 | 462 | −5.0 … +1.5 | shoulder top: upper arm/upper arm (78), clavicle/upper arm (68) | — |

## Reading the results

- **Squat and row contacts are expected tissue contact** (calf on thigh, elbow crease), not tearing. They still interpenetrate, because there is no collision or volume preservation: a contact-aware corrective or collision layer is needed for deep flexion.
- **Ankle dorsiflexion:** a flat-foot parallel squat needs about 25° here. The CDC 12.7° value is a passive non-weight-bearing mean, so this is recorded, not hidden. A weight-bearing ankle ROM source is needed before judging it.
- **The press reproduces the known shoulder-top LBS buckle** (W2/#112). It is the worst benchmark and depends on the W4 weight refit or a contract decision.

## M2: lunge, walk stride, trunk rotation and grip

The same script, metrics and floor rule apply, so M1 numbers are unchanged (re-run byte-identical in `worst` and volume range). Phone sheets are `lunge_`, `walk_stride_`, `trunk_rotation_` and `grip_phone_sheet.jpg` in `ORIGINAL_V1_WORK/anatomy/audit/claude_m1/`.

**Paths.**
- **Lunge:** front hip and knee to 90°, rear hip to 10° extension and rear knee to 90°. The body is grounded by a vertical root shift, so the lowest point is on the floor.
- **Walk stride:** 5 key poses (contact, loading, mid-stance, push-off, and the mirrored contact), with hips 25° flexion / 10° extension, knees up to 60°, ankle up to 10° and counter-swinging arms (shoulder 15°, elbow 15°). The second half is the first half with the sides swapped.
- **Trunk rotation:** 15° axial rotation each at spine_01/02/03 and the neck (45° total).
- **Grip:** arms held forward (shoulder flexion 45°, elbow 90°), then MCP 80°, PIP 90° and DIP 60°, with thumb CMC/MCP/IP 30/40/40°.

| Benchmark | Worst collapse | Worst stretch > 2 | Worst self-intersecting pairs | Volume Δ % | Dominant contact | Exceeds CDC passive mean |
|---|---|---|---|---|---|---|
| Lunge | 0 | 57 | 84 | −1.8 … +0.1 | early: front thigh into the hanging thumb; end: calf/thigh (42 per side) | — |
| Walk stride | 0 | 0 | 64 | −0.2 … +0.1 | thumb against the thigh on the forward-swinging arm's side (both sides, mirrored phases) | — |
| Trunk rotation | 0 | 7 | 84 | −0.6 … 0.0 | thumb against the thigh (right); 4 spine_02/upper-arm pairs at 45° | — |
| Grip | 0 | 44 | 150 | −0.04 … +0.01 | elbow crease, forearm_tw0/upper arm (51 per side), present from frame 0 because of the 90° elbow | — |

**Reading the results.**
- **Hand-to-thigh proximity at rest:** the A-pose hand hangs almost on the thigh. Any hip flexion, stride or trunk rotation drives the thumb into the thigh. This is a rest-pose setup artifact, not a deformation fault, but a runtime without collisions will show it.
- **Elbow crease at 90°:** the same class as the row and the M1 knee contact. It needs the collision- or volume-aware corrective listed below.
- **Grip closure:** the mean fingertip-to-wrist distance falls from 184 to 61 mm on both hands.
- **Thumb opposition is not achieved:** rotating the thumb chain about local Z curls it, but it stays out to the side of the fist. A thumb opposition axis is needed before a grip can be judged; this is recorded, not tuned.

**Rig finding (left/right digit axes) and the fix it forced.**
- The rig's local digit axes are **not mirror images**: local +Z flexes the `_r` fingers toward the palm but **extends** the `_l` fingers.
- The first M2 run assumed "finger flexion = local +Z" for both sides. The `_l` hand therefore curled backwards, and the fingertip-to-wrist metric could not tell the difference: a backward curl also brings the tips near the wrist.
- **Fix:** the benchmark now measures, at rest, the sign of each digit bone's local-Z rotation that moves its tip toward the palm (palms face the body, the convention in `scripts/audit_original_v1_joint_kinematics_blender.py`).
- **New metric** `digit_tip_mirror_error_mm`: the largest distance between a left digit-joint tip and the x-mirror of its right counterpart.
  - Fixed signs: 0.0002 mm.
  - The old single sign: 164.5 mm.
  - Native test: below 0.5 mm in every frame.
- With the fix, the grip's worst collapse fell from 5 to 0 and its worst pairs from 213 to 150; the left thumb-base/index-metacarpal intersection disappeared.
- The repo's existing finger audits (`audit_original_v1_skeleton_motion_blender.py`) already derive hinge axes per side from geometry, so this was a benchmark bug only. Any new consumer that assumes mirrored digit axes would hit it.

**Tests:** see below (8 native tests after the M2 follow-ups).

## M2 follow-ups: single-leg stance and calf raise (ankle/toe)

The seven earlier benchmarks are unchanged in every metric.
- **Determinism fix:** a face's contact class used to break ties among three different vertex groups by Python's hash-randomised string-set order, so per-class counts (never totals) varied between runs (e.g. 137 vs 133 in one press frame).
- Ties now break by name, and the classes are sorted by (count, name). Two consecutive runs now produce identical reports.
- The class counts quoted above (squat 72/61, row 44, press 78/68) are unchanged. Phone sheets: `single_leg_stance_phone_sheet.jpg` and `calf_raise_phone_sheet.jpg`.

- **Single-leg stance:** the right leg lifts to hip 90° and knee 90°. The left stance leg, pelvis and root stay at rest, so the stance foot does not move. No weight shift or pelvic drop is modelled.
- **Calf raise:** both ankles plantarflex 35° (CDC passive mean 54.6°). The MTP joints extend by the same 35°, which keeps the toes flat: the toe bones' world rotation equals rest (0.0°). The body is grounded on the toe pads; the floor contact goes from 14 foot + 9 toe vertices per side at rest to 52 toe vertices per side. The atlas has no CDC value for MTP extension.

| Benchmark | Worst collapse | Worst stretch > 2 | Worst self-intersecting pairs | Volume Δ % | Dominant contact | Exceeds CDC passive mean |
|---|---|---|---|---|---|---|
| Single-leg stance | 0 | 53 | 60 | −1.6 … +0.1 | early: lifted thigh into the hanging thumb; end: calf/thigh of the lifted leg (42) | — |
| Calf raise | 0 | 0 | 0 | −0.2 … 0.0 | none | — |

- **Ankle-joint head rise:** 92 mm at 35°, increasing monotonically.
- **Calf raise is the first benchmark with no deformation defect:** at 35° plantarflexion with 35° MTP extension, the ankle and forefoot skin does not collapse, stretch or self-intersect. This covers the toe-off range that F6 swept on the foot alone, now on the whole grounded body.

**Tests:** 8 native tests pass (Blender 5.2.1):
- walk-cycle closure and left/right phase symmetry;
- grip closure and mirror symmetry;
- calf-raise heel rise, monotone and within the CDC plantarflexion mean;
- plus the M1 floor, CDC and finiteness checks across all nine benchmarks.

## H1 natural arm carriage and H2 thumb opposition (14 Oct)

**H1: hand-to-thigh contact.**
- **Cause:** with the arms hanging straight (0° abduction) the hand rests almost on the thigh, so any hip flexion, stride or trunk rotation drives the thumb into it.
- **Fix:** both upper arms carry a constant **4° shoulder abduction** (`ARM_ABDUCTION_DEG`; upper-arm local −Z for `_r`, +Z for `_l`) in the walk, lunge, trunk rotation and single-leg stance.
- **Choice of value:** 0 / 4 / 6 / 8° were measured, and 4° is the smallest that clears every hand–thigh contact. It is an authored natural carriage, not a sourced value.

| Benchmark | Worst pairs (0° → 4°) | Remaining |
|---|---|---|
| Walk stride | 64 → **0** | — |
| Trunk rotation | 84 → **0** | — |
| Single-leg stance | 60 → 42 | calf/thigh only |
| Lunge | 84 → 84 | calf/thigh only; thumb contact gone |

The other five benchmarks are unchanged frame by frame.
- **New native test:** `test_no_hand_thigh_contact_with_arm_carriage`. It fails with the carriage at 0°, which was checked.
- **Updated test:** the first frame of the three carriage benchmarks is now "standing with carriage": 0 pairs and |volume| < 0.5%. The exact-rest check is kept for squat, row and calf raise.

**H2: thumb opposition in the grip** (`THUMB_OPPOSITION`, `_solve_thumb`).
- **No sourced thumb CMC opposition axis exists here, so the thumb pose is solved:**
  - with the fingers fully flexed, the thumb base (CMC) Euler rotation is searched on a 15° grid, total ≤ 60°;
  - MCP and IP are flexed 40° about their measured palmar axes;
  - **every candidate is checked on the evaluated mesh**, and the closest thumb-tip placement to the flexed index/middle middle phalanges with ≤ 5 thumb/finger skin intersections **and 0 collapsed hand faces** wins;
  - each side is solved independently, because the digit axes aren't mirrored. The solutions mirror exactly (CMC −15 / ±30 / ∓30°), with a digit mirror error of 0.0 mm.
- **Result:** the thumb now lies over the top of the fist along the index finger, instead of sticking out sideways.
- **Grip metrics:** worst collapse 0 → 0, stretch > 2 44 → 4, pairs 150 → 150 (all the 90° elbow crease).
- **Still not a full wrap:** the thumb tip ends 60.7 mm from the index/middle middle phalanges. Closer placements (30–54 mm) all drive 126–316 thumb pairs into the fingers or palm, or collapse faces. Skinning has no contact model for the thenar pad, so these were rejected and recorded rather than shipped.

## P4 families: forearm rotation and wrist circuit (14 Oct)

**Targets:** the *active* means in `whole_body_movement_atlas.json`:
- pronation 68.8 ± 12.5° and supination 82.4 ± 14.2° (biplane 2D–3D registration, 20 limbs);
- wrist flexion 73.6 ± 4.5°, extension 68.0 ± 4.3°, radial deviation 18.6 ± 1.7° and ulnar deviation 31.3 ± 3.3° (goniometry, 120 wrists, adults 18–40).

Both start from the standard goniometric position: elbow flexed 90°, forearm neutral (thumb up).

**Rig facts measured for this:**
- **Forearm twist must be applied about the bone's own axis before flexion (Euler YXZ).** With XYZ, the "twist" swings the flexed forearm sideways.
- **Forearm local +Y pronates `_r` and supinates `_l`:** mirrored.
- **The twist bones follow the rig rule** (`forearm_tw0` keeps 0%, `forearm_tw1` keeps 50% of the twist).
- **Wrist flexion is the hand's local Z** with the measured palmar sign per side. Local +X is ulnar deviation on both sides.

| Benchmark | Worst collapse | Worst stretch > 2 | Worst pairs | Notes |
|---|---|---|---|---|
| Forearm rotation (neutral → 68.8° pronation → 82.4° supination) | 0 | 0 | 124 (all the 90° elbow crease) | Minimum forearm cross-section radius 0.90 of rest: **no candy-wrapper** |
| Wrist circuit (flexion, extension, radial, ulnar) | 0 | 16 (full flexion) | 136 (elbow crease + wrist at full flexion) | The **dorsal wrist skin pinches into a crease at full extension**: recorded, not hidden |

- **Direction check (close-up renders in the phone sheets):** pronation turns the palm down with the thumb rolling medially; supination turns the palm up. Extension bends the hand dorsally; ulnar deviation drops the little-finger side.
- **Tests:** 11 native tests. The two new ones require the peaks to equal the atlas means, no collapse, and a forearm slice radius above 0.85.

## Next

- **Collision- or volume-aware correctives:** for deep knee and elbow flexion (squat, lunge, row, grip).
- **Rest-pose hand clearance:** the hand-to-thigh proximity needs either a slightly abducted rest arm or contact handling; this is an owner-visible choice, not changed here.
- **Thumb opposition axis:** needed for grip benchmarks.
