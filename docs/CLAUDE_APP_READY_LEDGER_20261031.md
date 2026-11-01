# Home Gym PT: app-ready model ledger (Claude lane, from 31 Oct 2026)

**Branch:** `claude/r120-surface-candidate-20261023`.

**Status:**

- Candidates only.
- W8, V14, R120, ORIGINAL_v1, the validated skeleton, PT-App and `PT_MODEL_VERSION 1.0` are unchanged.
- Nothing has been merged or deployed.
- No `.blend` files are in git.

**Coordination:**

- Work's phone-cloud lane (PR #126, `work/phone-blender-workbench-20261023`) audits W8/V14/R120 read-only. It is not
  duplicated here.
- GPT's PT-App lane has a GLB structural preflight (PT-App draft PR #18, `scripts/check-glb-preview.mjs`). It is
  waiting for a real GLB with exact joint and morph names. This lane produces that GLB.

## The model being repaired

**C1** is the best existing candidate. It is not a restart. It consists of:

- the R120 surface;
- the R121 arm, elbow, hip and knee correctives (blend `W3`);
- the corrected scapula/clavicle press girdle (`V2_TRAJ_GIRDLE=candidate`, ISB frame);
- the upper-arm twist bones;
- the forearm crease reweight;
- the thorax-frame plane factor.

Its record is in `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md` (C1 section).

**"Before"** is the R120 surface with the original r57 press girdle and r57 drives (`V2_TRAJ_GIRDLE=r57 V2_TRAJ_R121=0`).
This is the model Work's phone reviews show.

## Completed

| When | What | Evidence |
|---|---|---|
| 31 Oct | **Real animation pipeline.** The harness renders every frame from fixed cameras, identical for every model and frame (`V2_TRAJ_ANIM`). Frames are composited (`anim_compose.py`) and encoded to H.264 by Blender's FFmpeg (`encode_mp4_blender.py`). Every video frame is a rendered pose. | scripts in `scripts/body_v2/` |
| 31 Oct | **Shoulder press, before vs C1.** 49 rendered frames per rep, 6 views. At the lockout the before model's shoulder tears: the humerus rolls into a tube under the shoulder skin and the skin crumples front and back. C1 keeps the shoulders coherent and smooth. | `review-assets/body_v2/visual_evidence/` (see its README) |
| 31 Oct | **Arm "balloon" diagnosis.** On C1 the upper-arm skin keeps its rest radius within about 5% through the whole press. Corrective keys add about 0 there. So the arm does not inflate during the movement. | `V2_TRAJ_KEY_DIAG` |
| 31 Oct | **App fidelity finding.** glTF/three.js play only 4 bone influences per vertex. 127,551 vertices have 5 to 10. Keeping the largest 4, as the exporter does, breaks the model: press lockout 7 → 791 self-intersections and 8 → 3062 folds; squat 0 → 1203 and 13 → 3600; up to 48 mm vertex error. | `V2_TRAJ_PRUNE4` |
| 31 Oct | **GLB export path.** The rig and body are exported with no helpers and no reference skeletons. All 141 shape keys go out as sparse morph targets, and each movement's bones and driven morph weights are baked per frame. Test export: 45.5 MB with one 9-frame clip. | `glb_bake_export.py` |

| 31 Oct | **Phone evidence published.** The press before/after (2 MP4s, 6 stills, per-frame metrics) is GitHub Actions artifact `claude-phone-evidence-41237436783` (run 41237436783, commit `8da657db`, 6.9 MB). | `review-assets/body_v2/visual_evidence/README.md` |
| 31 Oct | **App-safe binding fit, first pass.** The fit used 180 training poses (20 movements × 9 frames). Error is measured between the full binding and the fitted 4-influence binding, in linear blend skinning: the max is 2.7 to 10 mm and 99% of vertices are within 0.1 to 2.3 mm on every movement. The top-4 cut gave 48 mm. With lunge, pulldown and walk held out, the fit still matched them (p99 0.6 to 1.5 mm). Trunk rotation did not: held out it gave 71 mm, because no other movement twists the spine. So the final fit trains on all 20 movements (trunk rotation: max 13 mm, p99 1.9 mm). A dedicated range-of-motion sweep is needed before calling the binding reusable. | `fit_app_binding.py`; report in the scratch area |

| 31 Oct | **4 influences are not enough; 8 are.** Even the fitted 4-influence binding breaks the press lockout (7 → 202 self-intersections, 8 → 1209 folds) and the squat (0 → 85, 13 → 864). On this fine mesh (3 to 5 mm edges), a 1 to 2 mm error that differs between neighbouring vertices creases the skin. Keeping the 8 largest weights stays within 0.38 mm of the full binding (only 519 vertices use 9 or 10). **App requirement: 8 bone influences (glTF JOINTS_0/1 + WEIGHTS_0/1).** Babylon.js plays this natively; three.js with the shader patch in `glb_playback/page.html`. | `V2_TRAJ_WEIGHTS4`, numpy top-8 check |
| 31 Oct | **Press lockout attribution.** At C1's lockout only the `R121_ARM_*_153` keys are active (S1/S3/S5/S7/SHOULDER/C1 off). The mass behind the arm in the side view is the posterior armpit fold, judged anatomical on 30 Oct and kept. The V on the upper chest follows the clavicles elevating, which is expected overhead. A chest relief-restore patch (W4) changed nothing visible and no metric, so it is **not adopted** (default-off option). | `V2_TRAJ_MUTE_KEYS`, `W4` |

| 31 Oct | **App integration candidate GLB** (`review-assets/body_v2/visual_evidence/app_candidate_20261031/`, 23.9 MB). It is the C1 app LOD: 52,195 vertices, 8 influences, 31 clip-morph components and press/curl/squat clips. **PT-App's own `check-glb-preview.mjs` passes it with no gaps.** It plays in three.js r170 within 0.047 mm of the Blender LOD, and the LOD is within 0.013 mm of the full model at every checked frame. Measured on the way: the full-resolution GLB (52.9 MB) cannot play on a phone, because three.js keeps all 140 morphs as one roughly 780 MB GPU texture, and PT-App rejects sparse accessors. | `app_lod.py`, `glb_playback/`, its README |

| 31 Oct | **Curl and squat before/after** (real animation, stills, per-frame metrics). Curl peak 1663 → 2 self-intersections, folds 200 → 17. Squat 1308 → 0, folds 1146 → 13, hips 555 → 0. **Latest phone artifact:** `claude-phone-evidence-41244308985` (run 41244308985, 27.4 MB): press, curl and squat media plus the app GLB. | `review-assets/body_v2/visual_evidence/` |

| 31 Oct | **PT-App reversible integration candidate:** branch `claude/body-v2-glb-candidate-20261031` in `anyangle1409-code/PT-App`. It is based on GPT's `chatgpt/model-glb-intake-gates-20261031` and modifies none of their files. It adds `model-candidates/body-v2-c1/CANDIDATE.json` (SHA-256, the exact 79 joint and 31 morph names, the engine requirements), a README and `tests/glb-candidate-body-v2-c1.test.mjs`. That test runs their unchanged `check-glb-preview.mjs` on the real GLB with the exact names: **3 of 3 pass**, and it skips without the file. Their 15 intake tests still pass. The binary is gitignored, and there is no PR. | PT-App commit `8dff242` |

| 31 Oct | **Bent-over row and push-up before/after** (real animation, stills, metrics; skeleton-fitted cameras). Row 1394 → 57 self-intersections and 272 → 34 folds. Push-up 2483 → 53 and 430 → 49. **Latest phone artifact:** `claude-phone-evidence-41251733616` (run 41251733616, 38.1 MB). It holds press, curl, squat, row and push-up, plus the app GLB. | `review-assets/body_v2/visual_evidence/` |

| 31 Oct | **Lunge (arms at the sides) and walking stride before/after.** Lunge 824 → 11 self-intersections and 327 → 38 folds (knees 50 → 2). Walk 182 → 0 and 31 → 6. No floor penetration. | `review-assets/body_v2/visual_evidence/` |

| 1 Nov | **Forearm rotation and grip before/after; all 7 priority movements are covered.** Forearm rotation 1894 → 0 self-intersections (elbow folds 131 → 5). Grip 2055 → 980: the elbow's 1048 pairs are gone. The 730 fist and palm pairs are the same in both models, and about 250 shoulder pairs come from the grip's girdle-free arm pose. Both grip models play the same skeleton-only thumb, because no mesh-checked placement exists on this surface. **Latest phone artifact:** `claude-phone-evidence-41260002901` (run 41260002901, 49.7 MB). It holds all nine movement sets plus the app GLB. | `review-assets/body_v2/visual_evidence/README.md` |

| 1 Nov | **App candidate GLB v2:** 8 clips (press, curl, squat, row, push-up, lunge, walk, forearm rotation), 36.5 MB, 50 shared clip-morph components. **PT-App's preflight passes with no gaps.** three.js r170 matches Blender within 0.047 mm, and the LOD matches the full model within 0.033 mm. The review camera now fits each clip, and the last frame is clamped. PT-App candidate branch updated to v2 (commit `ae477ee`); the opt-in test passes 3 of 3 and their 15 intake tests still pass. v1's binary leaves the working tree (history `80b91b02`). | `review-assets/body_v2/visual_evidence/app_candidate_v2_20261101/` |
| 1 Nov | **Walk fixed: the gait cycle plays forward and loops.** It had played forward and then backwards (out-and-back sampling of a whole cycle). Re-rendered: before 182 → C1 **0** self-intersections (knee against knee in both swing phases), folds 33 → 6. | `walk_stride_20261031/` |
| 1 Nov | **Grip fixed (test path):** the thumb search's baseline now includes the thumb's own MCP/IP flexion, so a mesh-checked placement exists (left hand within r57's limit of 5, mirrored to the right). C1 holds the arms with the coupled girdle (`V2_TRAJ_GRIP_GIRDLE=1`). Before 1480 → C1 **155** self-intersections (hand creases only; shoulders 250 → 0), folds 228 → 6. | `grip_20261031/` |
| 1 Nov | **Bent-over row, left shoulder (57 pairs vs 2), diagnosed:** strict mirror pairing (position, normal and dominant bone) shows the weights there are symmetric (mean difference 0.03) and the bone transforms are mirror-exact. With every shape key off, the left still has 45 pairs, so the keys are not the cause. The rest mesh differs by up to 3.6 mm between sides in that fold (posterior deltoid against the upper back, 120 to 146 mm behind the shoulder line). The row's retraction closes the fold, and the left side crosses where the right just touches. Close-up renders show no visible tear, only the same soft fold with fine crinkles on both sides. Low priority; a row-pose contact key is the fix if wanted. | `V2_TRAJ_DIAG_GROUPS`, `post_shoulder_l/r` views |
| 1 Nov | **Phone playback page (owner's device check):** a private claude.ai artifact plays GLB v2 on a phone with the 8-influence patch, checks its SHA-256, measures every clip's frame rate, and saves each run to a test log Claude can read back. Verified in headless Chromium; not yet run on an iPhone. | https://claude.ai/artifact/2kJqHzwh7RKy3i2pwbcgGU |

## In progress

- Nothing is running. The next items are below.

## Remaining (in order)

0. **Owner:** run the phone playback page on an iPhone (Run the test). Its results land in the artifact's test log.
1. **Hand:** the closed-fist creases (155 pairs, the same in both models: thumb MCP 19 per hand, ring knuckle against
   the palm 12 per hand). They need MCP-indexed knuckle correctives.

2. **C1 press lockout, still visible:**
   - crinkling under the clavicles (front close-up);
   - a lump behind the arm (side close-up).
3. **Bent-over row:** the left posterior-shoulder fold (57 pairs, diagnosed above; not visible in close-ups). Optional
   row-pose contact key. Push-up remains (forearm crease and thumb base).
4. **GLB, remaining:**
   - real iPhone playback and performance (page ready; needs the owner's phone);
   - PT-App shadow viewer integration (GPT lane; needs the 8-influence patch and signed morph weights);
   - a grip clip (now that the grip is clean apart from the fist creases);
   - the runtime drive contract for unbaked exercises (owner decision). GPT's read-only exercise-motion contract
     (`chatgpt/exercise-motion-contract-intake-20261031`) expects `ExerciseDefinition` packets with phases and tempo;
     the GLB's clips are review trajectories, not packets.

## Blocked / owner decisions

- **Adopting C1** changes the bind (twist bones, weights) and the runtime contract (drives). That is the owner's
  decision. AX6 stays the reference until then.
- **Production:** model release, PT-App integration and deployment all need owner approval.

## Resume point

0. Hips/groin, knees and feet were covered by the squat, lunge and walk before/after (hips 555 → 0, knees 129 → 13,
   lunge knees 50 → 2, walk knees 26 → 0); no further fault was visible in those frames.

1. Read this file, then `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md` (C1).
2. Blends are in the session scratch area and are not in git. They are rebuilt by the `chain_*.sh` recipes documented
   in the trajectories doc.
3. The harness environment for C1 is:

   ```
   V2_GIRDLE_FRAME=isb V2_TRAJ_GIRDLE=candidate V2_TRAJ_UA_TWIST=1 V2_TRAJ_FA_REWEIGHT=1 V2_R121_PF_FRAME=thorax
   V2_TRAJ_PUSHUP_GIRDLE=1 V2_TRAJ_GRIP_GIRDLE=1 V2_TRAJ_BENCH_CARRY=16 V2_TRAJ_SQUAT_ARMS=forward
   ```
