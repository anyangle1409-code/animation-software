# Meshy male mesh: rig-fit investigation (4 November 2026)

**Status:** an experimental investigation. It is **not accepted**, not production, and nothing is merged. The production model, its rig and the PT-App are unchanged.

Work is on branch `claude/home-gym-pt-animation-txux66`, a separate branch. The earlier MPFB branch is preserved, and the remote branch's extra commit was merged in without rewriting history.

## Source asset (kept unchanged)

`Meshy_AI_male_fitness_mannequi_1104161525_generate.glb`:

- 5,536,916 bytes;
- SHA-256 `9a033de91403300ac6d6ae000a19fa3356cbd706c1715f3d40eee1004e3fa85d`.

The file is **not committed**, because the repository is public and the licence is not yet verified. It is kept read-only in the session's scratch area. Every adaptation below was made on a copy.

**Verified on import** (`inspect_report.json`):

- 1 mesh, 115,330 vertices, 230,672 triangles;
- no UVs, no armature;
- stature 1.820 m, facing −y once imported (Z-up);
- **watertight**: 0 boundary edges, 0 non-manifold edges, 1 connected component;
- median edge length 3.8 mm;
- the pose is an **A-pose**: arms 31.9° from vertical, hands open, feet apart.

## Fit to the canonical skeleton (`bind_report.json`, `landmarks.json`)

The rules for the fit:

- The mesh copy was scaled uniformly to the canonical stature, 1.856 m (×1.0198).
- A **copy** of the canonical rig (`MESHY_RIG`) was posed into the mesh's A-pose by rigid rotations only. **No bone length or joint definition was changed.** That pose was then used as the copy's bind (rest) pose.
- Helper bones were not weighted: shoulder_cap, muscle_*, hip_crease and forearm_tw0. They are driven by the production R121 drives. root was not weighted either.
- Weights are Blender bone-heat automatic weights. All 115,330 vertices received weights.

| Joint | Canonical vs this mesh |
|---|---|
| Knee | 24–32 mm from the mesh's knee centre |
| Ankle | 23 mm |
| Wrist | 23–24 mm; the canonical forearm is about 2 cm longer than the mesh's |
| Crotch height | mesh 0.774 m vs W12c 0.790 m: hip region compatible |
| **Shoulder (GH) spacing** | canonical 438 mm; the mesh's shoulders are visibly narrower (width at 1.47 m: 0.565 m incl. deltoids). The canonical GH sits a few cm lateral of the mesh's natural joint. This is the same mismatch found with the MPFB bodies. **A skeleton revision would need owner approval; none was made.** |

## Deformation tests (`pose_report.json`)

**Method:** linear blend skinning only. There are no corrective shapes yet. Intersections are counted on the full 230k-triangle mesh, as non-adjacent triangle pairs.

| Pose | Self-intersections (pairs) | Where | Edge stretch p99 / max | Volume change |
|---|---|---|---|---|
| Stand (arms down 8°) | 1,052 | upper arm into the latissimus / armpit | 1.08 / 2.2 | −1.1 % |
| Press bottom (55° elevation, elbow 70°) | 327 | armpit | 1.56 / 6.8 | +2.2 % |
| Press mid (105°, elbow 115°) | 112 | shoulder top | 2.25 / 14.5 | +6.0 % |
| Press top (170°, elbow 175°, clavicle +25°) | 323 | rear deltoid / trapezius fold | 2.88 / 21.0 | +7.6 % |
| Curl (elbow 140° flexion) | 1,646 | forearm against the biceps (expected contact, needs a contact corrective) | 1.32 / 2.8 | −1.8 % |
| Squat (hip 100°, knee 110°, trunk lean 35°) | 1,735 | armpit 955, groin / hip crease 497, back of knee 283 | 1.96 / 17.1 | −7.4 % |

**Visual findings** (the renders were sent in the conversation, not committed):

- **Good:** standing, press bottom and curl look clean.
- **Press mid and top fail** without correctives:
  - the skin crumples on top of the shoulder at mid;
  - a deep fold at the rear deltoid / trapezius at the top (back view);
  - the shoulder mass pushes into the side of the neck (side view).
- **Squat:** groin and back-of-knee collapse typical of skinning alone; the hip-crease volume is lost (−7.4 %).

## Mobile performance (`lod_report.json`)

| Level | Triangles | Vertices | Surface deviation p95 / max | Skinned GLB size |
|---|---|---|---|---|
| Full | 230,672 | 115,330 | — | — |
| LOD 60k | 60,000 | 29,994 | 0.14 / 0.63 mm | 1.70 MB |
| LOD 40k | 40,000 | 19,994 | 0.20 / 1.27 mm | 1.14 MB |
| LOD 25k | 25,000 | 12,494 | 0.30 / 1.10 mm | 0.72 MB |

- The full mesh is too heavy for mobile skinning. A 25k–40k-triangle level keeps the shape to within about 1 mm.
- The bone-heat weights have up to 11 influences per vertex (21,767 vertices have more than 4). A 4-influence limit and renormalisation are required for glTF / mobile.
- No device frame-time test was possible in this environment.

## Acceptance gates

| Gate | Result |
|---|---|
| **Commercial licence** | **Open / not verified.** Meshy's terms depend on the account plan used to generate the asset. They must be checked against Meshy's current terms for that account before any use in the app. |
| **Runtime independence** | **Pass by construction.** The output is a static GLB baked into our own skinned asset; no Meshy service or runtime is needed by the app. |
| Visual approval | Pending, by the owner. |
| Deformation | **Fails** at press mid / top and squat without correctives; the measured failures are above. |
| Mobile | Feasible only at a 25k–40k-triangle level with a 4-influence limit. |

## What would make it production-capable

1. Retopology into an animation mesh with edge loops at the shoulder, elbow, hip and knee. Alternatively, a deformation cage driving the dense mesh.
2. Corrective shapes for the shoulder (press mid / top) and the squat (groin, back of knee), rebuilt like the earlier R121 families.
3. Helper-bone weights (shoulder_cap, muscle_*, hip_crease) and the 4-influence limit.
4. An owner decision on the shoulder-joint (GH) spacing: whether to revise the skeleton.
