# App integration candidate: `hgpt_body_v2_C1_app_lod.glb` (31 Oct 2026)

**Status: REVIEW CANDIDATE.** This is not a production asset.

- It is not merged into PT-App, and `PT_MODEL_VERSION 1.0` is unchanged.
- No approved screen, clip or model has been replaced.
- Adopting it needs the owner's approval.

## What it is

- **Model:** Body v2 candidate C1. This is the corrected press girdle, the R121 correctives, the upper-arm twist
  bones and the forearm reweight (`docs/R121_MOVEMENT_TRAJECTORIES_20261024.md`, C1).
- **Mesh:** an app LOD of 52,195 vertices and 104,370 triangles, decimated from 347,917 vertices. At rest it is at
  most 4.1 mm from the full surface (p99 0.11 mm).
- **Skeleton:** the 79-joint deform rig only. That is the 77-bone canonical rig plus the two upper-arm twist bones.
  Helper and display objects, reference skeletons and joint markers are left out.
- **Skinning:** **8 influences per vertex**, in two glTF joint sets (`JOINTS_0/1`, `WEIGHTS_0/1`).
  - With 4 influences the press lockout breaks: 7 → 202 self-intersections even with a fitted binding.
  - With 8 the result stays within 0.38 mm of the full binding.
- **Morph targets:** 31 dense "clip components" (`HGPT_CLIP_PC_nn`). They reproduce the corrective shape keys' effect
  at every baked frame within 0.013 mm.
- **Animations:** `press`, `curl` and `squat`, each 33 frames at 16 fps (2.0 s out and back). Each frame carries the
  bone transforms and the component weights.

## Checks (all in this folder)

| Check | Result |
|---|---|
| PT-App `scripts/check-glb-preview.mjs` (unchanged; source commit in `ptapp_check_glb_preview_source_commit.txt`) | **compatible, no gaps**: 81 nodes, 79 joints, 1 skin, 31 morph targets, 3 clips |
| three.js r170 playback in headless Chromium: load, play every frame of every clip, render | **plays**; `playback_report.json`, `THREEJS_<clip>.jpg` |
| three.js playback vs the same LOD evaluated in Blender (CPU skinning readback) | **≤ 0.047 mm** at every checked frame |
| LOD vs the full 347,917-vertex model, at the LOD's own surface points | **≤ 0.013 mm** at every checked frame (first / middle / last of each clip) |

`fidelity_exact.json` gives these per clip and frame.

## What an engine must do

1. **Play 8 bone influences.**
   - Babylon.js does this natively.
   - three.js needs a vertex-shader patch for the second joint set, given in
     `scripts/body_v2/glb_playback/page.html` (`patchSkin8`).
   - Note that three.js's `GLTFLoader` renormalises the first joint set to sum to 1 on load. The same file restores it.
2. **Allow signed morph weights.** The clip components use weights from −1 to 1.

## Limits, stated plainly

- **Timings:** the render timings in `playback_report.json` are from a software renderer (SwiftShader). They are not an
  iPhone measurement. Real device playback and performance checks have not been done.
- **New exercises:** the clips are baked. A new exercise needs the full key set (141 correctives) and the drive rules.
  That runtime contract is an owner decision, not part of this file.
- **What the checks prove:** they prove fidelity to the Blender candidate. The candidate's anatomy and movement are
  reviewed separately, in the before/after media in this artifact.

**Reproduce:** run `scripts/body_v2/movement_trajectory_test_blender.py` with `V2_TRAJ_BAKE_GLB`,
`V2_TRAJ_BAKE_LOD=0.15`, `V2_TRAJ_BAKE_FPS=16`, `V2_TRAJ_FRAMES=33` and `V2_TRAJ_SAVE_POS=1`. Then run
`glb_playback/run_playback.mjs` and `glb_playback/compare_playback.py --lodcheck`.
