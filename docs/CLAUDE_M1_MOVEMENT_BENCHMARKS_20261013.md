# M1: ORIGINAL_v1 integration benchmarks — squat, bent-over row, shoulder press (Claude, 13 Oct 2026)

- **Branch:** `claude/movement-benchmarks-20261013`, stacked on draft PR #111 (`13cea5a5`).
- **Script:** `scripts/build_original_movement_benchmarks_blender.py`.
- **Test:** `scripts/blender_tests/test_original_movement_benchmarks.py` (5 native tests PASS).
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

## Next

- **Benchmark coverage:** lunge, walk-cycle keyframes, trunk rotation and grip (M2).
- **Collision- or volume-aware correctives:** for deep knee and elbow flexion.
