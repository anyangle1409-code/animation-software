# App integration candidate v2: `hgpt_body_v2_C1_app_lod_v2.glb` (1 Nov 2026)

**Status: REVIEW CANDIDATE.** This is not a production asset.

- It is not merged into PT-App, and `PT_MODEL_VERSION 1.0` is unchanged.
- No approved screen, clip or model has been replaced.
- Adopting it needs the owner's approval.

It replaces v1 (`../app_candidate_20261031/`, three clips) as the candidate. v1's binary is no longer in the working
tree, to keep the phone artifact small; it stays in git history at commit `80b91b02`.

## What changed from v1

- **8 clips instead of 3:** `press`, `curl`, `squat`, `bent_over_row`, `push_up`, `lunge`, `walk_stride` and
  `forearm_rotation`. Each is 33 frames at 16 fps (2.0 s).
- **The walk loops forward.** The stride is one whole gait cycle, played once forwards. Its first and last frames are
  the same heel strike, so it loops. In earlier runs it went forward and then backwards.
- **Morph targets:** 50 dense clip components (`HGPT_CLIP_PC_nn`), shared by all clips. v1 had 31.
- **Size:** 36.5 MB (v1: 23.9 MB).

Unchanged from v1:

- the model (Body v2 candidate C1);
- the 52,195-vertex app LOD;
- the 79-joint deform skeleton;
- 8 bone influences per vertex;
- signed morph weights.

## Checks (all in this folder)

| Check | Result |
|---|---|
| PT-App `scripts/check-glb-preview.mjs` (unchanged; source commit in `ptapp_check_glb_preview_source_commit.txt`) | **compatible, no gaps**: 81 nodes, 79 joints, 1 skin, 50 morph targets, 8 clips |
| three.js r170 playback in headless Chromium: load, play every frame of every clip, render | **plays**: 52,195 vertices, 50 morphs, 8 influences, 8 clips (`playback_report.json`, `THREEJS_<clip>.jpg`) |
| three.js playback vs the same LOD evaluated in Blender (CPU skinning readback) | **≤ 0.047 mm** at every checked frame |
| LOD vs the full 347,917-vertex model, at the LOD's own surface points | **≤ 0.033 mm** at every checked frame (first, middle and last of each clip) |

`fidelity_exact.json` gives these per clip and frame.

**Review camera:** the three.js sheets now fit the camera to each clip's skinned bounds. In the first v2 sheets the
fixed standing framing cut off the push-up and the bent-over row.

## Clip names and the app's exercise contract

The clip names are the movement-benchmark names. They satisfy the id pattern in GPT's read-only intake gate
(`scripts/check-exercise-motion-packet.mjs` on PT-App branch `chatgpt/exercise-motion-contract-intake-20261031`).

They are **review clips, not exercise definitions**. Each is a 2-second out-and-back benchmark trajectory, not an
`ExerciseDefinition` with phases and tempo. No exercise packet is claimed for them. The closest definitions in
`src/exercises/definitions/` are:

| GLB clip | Closest definition `clipName` |
|---|---|
| `press` | `shoulder_press`, `seated_dumbbell_shoulder_press` |
| `curl` | `bicep_curl` |
| `squat` | `air_squat` |
| `bent_over_row` | `dumbbell_bent_over_row` |
| `push_up` | `push_up` |
| `lunge` | `forward_lunge`, `split_squat` (the stance is formed in place, without a step) |
| `walk_stride` | none (unloaded gait cycle; `farmers_walk` adds the load) |
| `forearm_rotation` | none (pronation and supination test) |

## What an engine must do

1. **Play 8 bone influences.**
   - Babylon.js does this natively.
   - three.js needs a vertex-shader patch for the second joint set, given in
     `scripts/body_v2/glb_playback/page.html` (`patchSkin8`).
   - three.js's `GLTFLoader` renormalises the first joint set to sum to 1 on load. The same file restores it.
2. **Allow signed morph weights.** The clip components use weights from −1 to 1.

## Limits, stated plainly

- **Timings:** the render timings in `playback_report.json` are from a software renderer (SwiftShader). They are not an
  iPhone measurement. Real device playback and performance checks have not been done.
- **New exercises:** the clips are baked. A new exercise needs the full key set (141 correctives) and the drive rules.
  That runtime contract is an owner decision, not part of this file.
- **What the checks prove:** fidelity to the Blender candidate. The candidate's anatomy and movement are reviewed
  separately, in the before/after media in this artifact.

**Reproduce:**

1. Run `scripts/body_v2/movement_trajectory_test_blender.py` with:
   - the C1 environment (`docs/CLAUDE_APP_READY_LEDGER_20261031.md`);
   - `V2_TRAJ_LUNGE_ARMS=side`, `V2_TRAJ_BAKE_GLB=<out>.glb`, `V2_TRAJ_BAKE_LOD=0.15`, `V2_TRAJ_BAKE_FPS=16`,
     `V2_TRAJ_FRAMES=33` and `V2_TRAJ_SAVE_POS=1`;
   - the eight movements above.
2. Run `glb_playback/run_playback.mjs`.
3. Run `glb_playback/compare_playback.py --lodcheck`.
