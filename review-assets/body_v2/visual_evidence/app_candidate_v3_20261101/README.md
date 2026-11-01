# App integration candidate v3: `hgpt_body_v2_C1_W5_app_lod_v3.glb` (1 Nov 2026)

**Status: REVIEW CANDIDATE.** This is not a production asset.

- It is not merged into PT-App, and `PT_MODEL_VERSION 1.0` is unchanged.
- No approved screen, clip or model has been replaced.
- Adopting it needs the owner's approval.

It replaces v2 (`../app_candidate_v2_20261101/`) as the candidate. v2's binary is no longer in the working tree, to
keep the phone artifact small; it stays in git history at commit `37536ebb`.

## What changed from v2

- **The model is candidate W5.** That is C1 with the press-lockout chest ripples smoothed
  (`../press_lockout_w5_20261101/`). Only the lockout key changed; every other key, the skeleton and the skinning are
  C1's.
- **9 clips:** v2's eight plus `grip`. The grip uses the mesh-checked thumb and the coupled girdle
  (`../grip_20261031/`).
- **Morph targets:** 52 dense clip components (v2: 50). **Size:** 37.9 MB (v2: 36.5 MB).

## Checks (all in this folder)

| Check | Result |
|---|---|
| PT-App `scripts/check-glb-preview.mjs` (unchanged; source commit in `ptapp_check_glb_preview_source_commit.txt`) | **compatible, no gaps**: 81 nodes, 79 joints, 1 skin, 52 morph targets, 9 clips |
| three.js r170 playback in headless Chromium: load, play every frame of every clip, render | **plays**: 52,195 vertices, 52 morphs, 8 influences, 9 clips (`playback_report.json`, `THREEJS_<clip>.jpg`) |
| three.js playback vs the same LOD evaluated in Blender (CPU skinning readback) | **≤ 0.048 mm** at every checked frame |
| LOD vs the full 347,917-vertex model, at the LOD's own surface points | **≤ 0.035 mm** at every checked frame (first, middle and last of each clip) |

`fidelity_exact.json` gives these per clip and frame.

**On a real iPhone (owner's phone, 1 Nov 2026).** The phone playback page uses the same 8-influence patch. On iOS 18.7
(Apple GPU, WebGL2, 402×874 @3x, canvas 740×926 at pixel ratio 2):

- **all 9 clips at 56 fps median;**
- slowest 5% of frames 19 to 21 ms;
- no frame over 34 ms;
- download 3.0 s, model build 27 ms, first frame 512 ms;
- checksum verified on the device.

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
| `grip` | none (closed fist with the arms forward; a grip test) |

## What an engine must do

1. **Play 8 bone influences.**
   - Babylon.js does this natively.
   - three.js needs a vertex-shader patch for the second joint set, given in
     `scripts/body_v2/glb_playback/page.html` (`patchSkin8`).
   - three.js's `GLTFLoader` renormalises the first joint set to sum to 1 on load. The same file restores it.
2. **Allow signed morph weights.** The clip components use weights from −1 to 1.

## Limits, stated plainly

- **Timings:** the render timings in `playback_report.json` are from a software renderer (SwiftShader). The iPhone
  numbers above are from one recent iPhone; older devices are untested.
- **New exercises:** the clips are baked. A new exercise needs the full key set (141 correctives) and the drive rules.
  That runtime contract is an owner decision, not part of this file.
- **What the checks prove:** fidelity to the Blender candidate. The candidate's anatomy and movement are reviewed
  separately, in the before/after media in this artifact.

**Reproduce:**

1. Run `scripts/body_v2/movement_trajectory_test_blender.py` with:
   - the C1 environment (`docs/CLAUDE_APP_READY_LEDGER_20261031.md`);
   - `V2_TRAJ_LUNGE_ARMS=side`, `V2_TRAJ_BAKE_GLB=<out>.glb`, `V2_TRAJ_BAKE_LOD=0.15`, `V2_TRAJ_BAKE_FPS=16`,
     `V2_TRAJ_FRAMES=33` and `V2_TRAJ_SAVE_POS=1`;
   - `V2_TRAJ_GRIP_THUMB=<grip_thumb_solution.json from ../grip_20261031/>`;
   - the nine movements above, on the W5 blend.
2. Run `glb_playback/run_playback.mjs`.
3. Run `glb_playback/compare_playback.py --lodcheck`.
