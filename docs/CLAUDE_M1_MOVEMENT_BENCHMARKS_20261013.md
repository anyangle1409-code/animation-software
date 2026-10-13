# M1/M2: ORIGINAL_v1 integration benchmarks — squat, row, press, lunge, walk, trunk rotation, grip (Claude, 13 Oct 2026)

- **Branch:** `claude/movement-benchmarks-20261013`, stacked on draft PR #111 (`13cea5a5`).
- **Script:** `scripts/build_original_movement_benchmarks_blender.py`.
- **Test:** `scripts/blender_tests/test_original_movement_benchmarks.py` (7 native tests PASS).
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

**Tests:** 7 native tests pass (Blender 5.2.1), including walk-cycle closure and left/right phase symmetry, plus grip closure and mirror symmetry.

## Next

- **Collision- or volume-aware correctives:** for deep knee and elbow flexion (squat, lunge, row, grip).
- **Rest-pose hand clearance:** the hand-to-thigh proximity needs either a slightly abducted rest arm or contact handling; this is an owner-visible choice, not changed here.
- **Thumb opposition axis:** needed for grip benchmarks.
