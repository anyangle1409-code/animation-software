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

| 1 Nov | **Press lockout chest ripples: candidate W5.** The guarded delta-mush patch of the lockout key smooths the skinning's wood-grain ripples on the pectorals and chest sides. Lockout roughness p95 0.076 → 0.059 mm (rest 0.066). Press peaks are unchanged over 49 frames: self-intersections 7, folds 8, edges over 35° 361. Pulldown is the same. Overhead extension: self-intersections 383 → 381, folds 67 = 67. Lateral raise, curl and squat are identical. Nine earlier variants were rejected for measured regressions (trajectories doc, W5). The armpit V-lines (pose creases) and the upper-arm ripples remain. | `press_lockout_w5_20261101/` |

| 1 Nov | **App candidate GLB v3: model W5, 9 clips (grip added).** 37.9 MB, 52 shared clip-morph components. **PT-App's preflight passes with no gaps.** three.js r170 matches Blender within 0.048 mm, and the LOD matches the full model within 0.035 mm (grip within 0.021 mm). PT-App candidate branch updated to v3 (commit `2d23cfd`): the opt-in test passes 3 of 3, and their 15 intake tests still pass. The phone playback page now serves v3. v2's binary leaves the working tree (history `37536ebb`). | `app_candidate_v3_20261101/` |

| 1 Nov | **Real iPhone playback measured (owner's phone).** GLB v3 on iOS 18.7 (Apple GPU, WebGL2, 402×874 @3x, canvas 740×926 at pixel ratio 2), in the phone playback page. **All 9 clips at 56 fps median**, slowest 5% of frames 19 to 21 ms, **no frame over 34 ms**. Download 3.0 s, model build 27 ms, first frame 512 ms. 8 influences active; checksum matches. | phone playback page, test log |

**Latest phone artifact (1 Nov):** `claude-phone-evidence-41303518619` (run 41303518619, commit `be3b46eb`, 61.6 MB): all
nine movement sets, the press lockout C1 vs W5 comparison, and app GLB v3.

## 3 Nov 2026 (owner brief: full anatomical model improvement)

**Runner check:**

- The repository is public, so standard GitHub-hosted runners are free and do not use the included minutes.
- `claude-body-v2-checks` run 41635410746 succeeded on `ubuntu-latest` (runner `GitHub Actions 1000006835`, hosted
  pool) in 16 s.
- `claude-visual-evidence` runs since then have all succeeded. Nothing is blocked.
- PT-App was not pushed this session, so that no workflows start in the private repository.

**Completed and verified:**

| Item | Evidence |
|---|---|
| **W11** = W5 + W7 front-armpit fairing + W8f pec thinning + W6d elbow-gated upper-arm band key + W9 fist contact keys. Against W5: overhead extension folds 67 → 59 and self-intersections 381 → 365; grip 155 → 56; press edges over 35° 318 → 309; 9 movements identical. **Worse:** collapsed edges about +300 (the faired armpit fold) | `shoulder_w11_20261103/` (press, pulldown, overhead extension, upper arm from behind, grip videos) |
| Comparison set: R41 (older slim) / W5 / W11, standing + press rack / intermediate / near lockout / lockout, front / side / back / three-quarter, identical skeleton motion and cameras | `comparison_r41_w5_w11_20261103/` |
| Silhouette proportions against the owner's reference (not stored). Waist, upper arm, knee, calf and ankle match. **Shoulders are high and square** (the line starts about 4 cm higher, 0.31 vs 0.25 of height wide at 0.80); the lower thigh is about 11 % thin | comparison README |
| Anatomical defect list | `docs/ANATOMICAL_DEFECT_LIST_20261103.md` |
| CI on the free runner: byte-compile + the drive-rule unit test (37 checks) | `.github/workflows/claude-body-v2-checks.yml` |
| W12a: armpit-hollow fairing (4.5 cm at (0.21, −0.015, 1.39)) in the 153 key. Overhead extension folds 59 → 51, self-intersections 365 → 338; the hollow is visibly smoother. **Worse:** collapsed edges +10 / +40 | ROUGH and REG W12_a45 (scratch) |

**Accepted later on 3 Nov:**

- **W12c** = W12a + the W5 mush and W7 fairing at the 120 / 150 press poses, in gated keys `R121_ARMBAND120/150_<s>`
  (elbow fade 50–70°, forward-raise fade at plane factor 0.3–0.6).
  - Better: overhead extension folds 59 → 51 vs W11; the intermediate-press pec ripples and front-armpit notch are
    visibly reduced.
  - Unchanged: the lateral raise, curl and squat are identical.
  - Worse: collapsed edges +11 / +40.
  - Evidence: `press_w12c_20261103/`.
- **Shoulder rest reshape (S1, S1b, S1c, S1d): none accepted.**
  - What it achieves: it does lower and slim the shoulders toward the reference. S1c brought the silhouette at 0.836
    of height from 0.240 to 0.199.
  - Why it is not accepted: every variant raises folds somewhere (S1c press +1, overhead +4, squat +4; S1d overhead
    +7). S1b's tangential relaxation broke the keys entirely (press folds 8 → 317).
  - Cause: the shoulder correctives are per-vertex offsets authored on the old shape.
  - Next: reshape, then re-patch the affected keys on the new shape.

**Failed and rejected today (all kept in the record):**

| Variant | What happened |
|---|---|
| W12b (the same patch, ungated, in the 120 / 150 keys) | Overhead extension folds 59 → 73, collapsed +195; squat collapsed +86. **Visually it is a large improvement at 125°**: the pec ripples are gone and the notch is softened. That is why W12c exists |
| S1 (shoulder reshape 16 / 14 mm) | The silhouette moved halfway to the reference (0.836 level 0.240 → 0.199), but the deltoid cap's relief packed into crinkles and a crease appeared where the trapezius lowering stopped |
| R41 renders as the "older approved" press look | R41_SOURCE lacks the R47 / R52 dense press correctives. It collapses on either girdle path (up to 1,710 crossings). The approved older look is in `review-assets/shoulder_r59/` (R52 at the R47 marked pose) |

### Male and female characters (owner requirement, 3 Nov)

- **Design:** `docs/CHARACTER_ARCHITECTURE_MALE_FEMALE_20261103.md`.
  - Shared between the two models: canonical bone names, exercise definitions in joint angles, corrective drive rules,
    the test harness and its thresholds.
  - Per character: skeleton fit, weights, corrective keys, landmark and region profile, references, results, approval.
- **Scaffolding:**
  - `review-assets/body_v2/characters/` holds the manifest plus a profile and approval record per character.
  - `scripts/body_v2/character_profile.py` validates them: owner approval is required before any approved or
    production-ready state, a character cannot be a scaled copy of another, and bone names must be canonical.
  - Its unit test (28 checks) runs on the free-runner check workflow.
- **Status:**
  - Male: `candidate` (W12c), **not approved**.
  - Female: `not_started`. Her work starts after the male appearance approval unless the owner says otherwise.
  - Neither is production-ready.
- **Not done yet (incremental):**
  - 36 hard-coded male object names remain in older scripts. They move to the profile when each script is next touched;
    the default profile is the male, so behaviour is unchanged.
  - Body-relative resolution of the absolute-metre exercise fields (hand and foot widths, IK targets) is designed, not
    built.

## In progress

- App GLB v4 from W12c is being baked (playback, fidelity and PT-App preflight run locally; no PT-App push).
- The W12c press close-up video is being rendered.

## Remaining (in order)

1. **Hand:** the closed-fist creases (155 pairs, the same in both models: thumb MCP 19 per hand, ring knuckle against
   the palm 12 per hand). They need MCP-indexed knuckle correctives.

2. **C1 press lockout, still visible** (the chest ripples are fixed in candidate W5; what is left):
   - the V-lines from the sternum to the armpits (pose creases; the W5 guard leaves them alone on purpose);
   - fine ripples on the upper arms (W5 leaves the arm skin alone; including it raised overhead-extension folds);
   - the lump behind the arm (side close-up), judged anatomical on 30 Oct.
3. **Bent-over row:** the left posterior-shoulder fold (57 pairs, diagnosed above; not visible in close-ups). Optional
   row-pose contact key. Push-up remains (forearm crease and thumb base).
4. **GLB, remaining:**
   - real iPhone playback: done for GLB v3 (56 fps on every clip); older iPhones untested;
   - PT-App shadow viewer integration (GPT lane; needs the 8-influence patch and signed morph weights);
   - the runtime drive contract for unbaked exercises (owner decision). GPT's read-only exercise-motion contract
     (`chatgpt/exercise-motion-contract-intake-20261031`) expects `ExerciseDefinition` packets with phases and tempo;
     the GLB's clips are review trajectories, not packets.

## Blocked / owner decisions

- **Shoulder joint spacing (skeleton, frozen):** the GH centres are 0.236 of stature apart, against a typical
  0.21–0.22. After the mesh fix the outer shoulder width is still about 5 % over the reference unless the joints move
  about 2 cm each side.
- **Head and face:** the model is a mannequin. A face, ears and hair are a separate package.

- **Adopting C1** changes the bind (twist bones, weights) and the runtime contract (drives). That is the owner's
  decision. AX6 stays the reference until then.
- **Production:** model release, PT-App integration and deployment all need owner approval.

## Resume point

0. Hips/groin, knees and feet were covered by the squat, lunge and walk before/after (hips 555 → 0, knees 129 → 13,
   lunge knees 50 → 2, walk knees 26 → 0); no further fault was visible in those frames.

1. Read this file, then `docs/R121_MOVEMENT_TRAJECTORIES_20261024.md` (C1).
2. Blends are in the session scratch area and are not in git. They are rebuilt by the `chain_*.sh` recipes documented
   in the trajectories doc.
3. The current best candidate is **W11** (blend `W11`, recipe in the trajectories doc, section W11). The published
   app GLB (v3) is still W5.
   - **Best candidate as of 3 Nov:** W12c = W11 + W12a + the gated 120 / 150 keys.
   - **Recipes:** `run_w12.sh a45 0.045 0.21,-0.015,1.39` then `run_w12c.sh`.
   - **Shoulder reshape:** the tool is `scripts/body_v2/rest_reshape_shoulders_blender.py`. The settings tried are
     recorded above; it needs the key re-patch next.
   The harness environment for C1 / W5 is:

   ```
   V2_GIRDLE_FRAME=isb V2_TRAJ_GIRDLE=candidate V2_TRAJ_UA_TWIST=1 V2_TRAJ_FA_REWEIGHT=1 V2_R121_PF_FRAME=thorax
   V2_TRAJ_PUSHUP_GIRDLE=1 V2_TRAJ_GRIP_GIRDLE=1 V2_TRAJ_BENCH_CARRY=16 V2_TRAJ_SQUAT_ARMS=forward
   ```
