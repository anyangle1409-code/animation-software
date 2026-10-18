# Handoff: ORIGINAL_v1 shoulder / press deformation work (Claude → next assistant, 16 Oct 2026)

The owner asked for everything to be in the repo so another assistant can continue. This page is the starting point.

**Status:** everything here is a **review candidate — not accepted, not production, not clinically validated.**

**Branches:**
- **Work:** `claude/original-v1-consolidated-review-20261014`. Coordination happens on PR #26, which has a checkpoint comment per candidate.
- **Task ledger:** `docs/CLAUDE_MASTER_TASK_LEDGER_20261013.json` on `claude/master-execution-20261013`.

## Owner rules (keep them)

- Never change the frozen canonical bones or the V-series assets in production. All new work goes in a separately named candidate under `ORIGINAL_V1_WORK/anatomy/candidates/`.
- Keep genuine failures. Never weaken a test; document any test change.
- Do not merge to main and do not force-push.
- No secrets, no third-party assets.
- Never claim anything is clinically approved.
- `HGPT_SHOULDER_*` shape keys belong to another workstream ("Work"); leave them alone.
- The owner's reference photos stay **out** of the repo.

## Where it stands: R33 (latest)

- **Candidate:** `ORIGINAL_V1_WORK/anatomy/candidates/claude_review_r33_20261016/`
- **Doc:** `docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R33_20261016.md`
- **Test:** `scripts/blender_tests/test_original_review_candidate_r33.py` (3/3)
- **Owner's latest verdict (on R31):** "This is the closest to what I want apart from the highlighted sections. It's just the skin crumbling at this point really." R33 answers that. The owner has not yet reviewed R33.

**Recent candidates (newest first):**

| Candidate | What changed |
|---|---|
| R33 | Upper arm straight along its own bone at bent-elbow keys; elbow rounded (Taubin, scaled by bend); more back fill at 120/145°; fold clean-up threshold lowered per key. |
| R31 | Upper arm re-bound to the humerus, removing the false "joint" a third of the way down the upper arm. Owner: "The only joint will be the elbow." |
| R29 | Lockout 166° (owner-approved), arm in line with the back. |
| R26–R28 | Hook removed, rounded deltoid, straight arm column, fuller upper arm. |

Each has a `docs/CLAUDE_ORIGINAL_V1_REVIEW_CANDIDATE_R*_*.md` with measurements.

## Open problems (next steps, in order)

1. **Front armpit at 120–145°.**
   - The S7 bake misses its target by up to 23 mm on a small patch 2–3 cm in front of and below the shoulder joint. The likely cause is the bake's guard against skin passing through the body.
   - There is a sharp edge (132°) there at 130°.
   - Not visible from behind. Check it from the front.
   - Tools: `bakeerr_k.py` with `KEY=145.0`, and `foldsweep2.py` with `HTS=130`.
2. **Stretch.** R33's mid-press stretch (87–122) and lockout stretch (80) are above R31's (1–46 and 47). Visually fine so far.
3. **shoulder_press benchmark:** 2 crushed triangles (R31 0).
4. **Wait for owner feedback on R33** before larger changes. The owner reviews press frames from **behind** and in **three-quarter** view, and circles problems.

## How the shoulder correctives work

The correctives are shape keys driven by humerothoracic elevation (`scripts/original_v1_review_candidate_drives.py`, `drive_s1`).

**Families:**

| Family | Keys | Role |
|---|---|---|
| C1 | 4 | Arm–trunk contact (row) |
| S1 | 8 | Relax |
| S3 | 8 | Shape target |
| S5 | 12 | Baked delta-mush along the press (R15 recipe) |
| S7 | 8 | Press lockout shaping, Claude's (keys 120/145/156/166 × L/R) |
| HGPT_SHOULDER_* | 6 | Work's; do not touch |

**Settings and lineage:**
- **S7 fade-in:** S7 fades in from `rig["hgpt_s7_angles_start"]`, which is 95 in R31/R33.
- **Lockout:** the press lockout is the opt-in `scene["hgpt_press_lockout_ht"]` = 166, read in `original_v1_press_extension.install()`.
- **Lineage:** R18 → R18Wg5 (follow weights, `build_original_upperarm_follow_weights_blender.py`) → B5 (S5 rebuilt with `build_original_review_candidate_r15_blender.py`) → R31 / R33 (S7).
- **B5 base:** in the repo at `claude_review_r33_20261016/stages/B5_base.blend`. Its sha256 `4a694e80…` matches the recorded parent.

## Rebuilding / iterating on S7 (the main loop)

1. **Target shapes, one per key.** `scripts/build_original_skin_slide_targets_blender.py <base.blend> <outdir>` writes `targets.npz` keyed by `"120.0"`, etc.
   - It is driven entirely by environment variables. The exact R33 values are in `stages/r33_run.sh.txt`, and per key in `r33_key156_run.sh.txt` / `r33_key166_run.sh.txt`.
   - Those scripts use scratch paths: `$SP/b5/B5.blend` means `stages/B5_base.blend`, and `$SP/r33` means your output directory.
   - **R33 keys 156 and 166 were built in single-key runs and merged.** The ready-made merged targets are `stages/r33_targets.npz`.
   - Every step is commented in the code with the owner request or measurement behind it:
     - **Arm column:** `ELBOW_FAIR`, `ELBOW_MODE=tube`, `TUBE_*`, `TUBE_UPPER*`.
     - **Elbow rounding:** `ELBOW_ROUND`.
     - **Back fill:** `LAT_WEB`, `LAT_KEY_GAIN`.
     - **Clean-up:** `AUTO_UNCROSS`, `UNCROSS_FOLDS`, `UNCROSS_FOLDS_AT`, `UNCROSS_RMAX`.
     - **Slides:** `POST_RR`, `POST_SLIDE`, `FINAL_SLIDE`.
2. **Bake into S7 keys.** Use the S7 keys you built: `S7_START=95 S7_LOCKOUT_HT=166 S7_KEYS=120,145,156,166 S7_NAME=Rxx`, then:
   ```
   python scripts/build_original_review_candidate_r17_blender.py -- --bake --blend B5_base.blend --parent B5_base.blend --targets targets.npz --out Rxx.blend --report rxx_build.json
   ```
3. **Validate the 13 movement benchmarks.**
   ```
   scripts/validate_original_review_candidate_blender.py -- --candidate Rxx.blend --baseline ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --out rxx_validation.json --renders <dir> --name Rxx
   ```
4. **Test, doc, CI.** Add a test, copying the R33 test, plus a doc. Add the CI entry in `.github/workflows/original-review-candidate-r1.yml` (paths list and a run line).

**Running Blender:**
- The CI uses `blender --background --factory-startup --python-exit-code 1 --python <script>` with Blender 5.2.1.
- Claude ran the scripts with Blender 5.2.1 as a Python module (`bpy`) under Python 3.13.
- Scripts that take arguments use `-- --flag value`.

## Measurement / render tools (`scripts/claude_review_tools/`)

These were scratch tools.

**Before running them:**
- Most hard-code `sys.path` to `/home/user/p5/scripts`; edit that to your checkout.
- Some need env `SP` (a scratch directory holding `pil/` and `vid/` Python packages for PIL / imageio-ffmpeg). Adjust to your environment.
- Set `LOCK_HT=166` for the press tools on a base blend without the lockout property.

| Tool | Use |
|---|---|
| `skelanim.py <blend> <outdir>` | Press frames: back / side / three-quarter, skin and skeleton. Env: `STEPS=40`, `ONLY=24,28`, `SKINONLY=1`, `KEEP_S5=1`, `MUTE=HGPT_S7_` (turn a family off). |
| `skelvid.py <framesdir> <out.mp4>` | Video of those frames, with angle captions. |
| `cmpsheet.py <out.jpg> LABEL=framesdir ...` | Side-by-side crops. Env: `FR`, `CROP`, `VIEWS`. |
| `rendernpz2.py <base.blend> <outdir>` | Renders target shapes. Env: `ITEMS="tag=targets.npz:145.0,..."`, `HT`, `LOCK_HT`. |
| `foldsweep.py` / `foldsweep2.py <blend>` | Sharp new folds near the right arm root along the press; foldsweep2 prints the sharpest edges' positions. |
| `bakeerr_k.py <blend> <targets.npz>` | Bake error vs target at `KEY`. |
| `crushwhere.py`, `hookfind_k.py` | Crushed triangles / sharp edges in a target. |
| `follow.py` | How far upper-arm skin lags a rigid humerus. |
| `elbw.py` | Elbow weight hand-over profile. |
| `wdiff.py` | Weight diff between two blends. |
| `drops5.py` | Strip S5/S7 keys before an S5 rebuild. |
| `stripkeys.py` / `famoff.py` | Remove or toggle shoulder families. |
| `refview.py`, `rawrender.py`, `foldclose.py` | Reference-camera views, raw renders, fold close-ups. |

## Owner feedback history (shoulder press)

1. "The bicep should flow into the forearms without a big dip."
2. "This is the shape the model should be in" (reference photo, kept outside the repo).
3. "The outside of the arm is inline with the body itself."
4. "The back looks too bulky."
5. "It's too quickly it changes" (the arm-root crease should fade in gradually).
6. "The only joint will be the elbow."
7. "Just the skin crumbling at this point."
8. "The arms as it's raising up should be in a straight line … the bend at the elbow is too sharp and not subtle."

The press movement itself (lockout 166°) is approved as fine ("it doesn't need to be exact as long as the exercise is done").


## 17 October continuation: R42 contour study, not accepted

The owner confirmed the older reference's arm-to-body transition while retaining
newer arms/elbows. R42's native study and all results are documented in
`docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R42_20261017.md` and
`ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r42_study_20261017/`.
No R42 blend was saved. Marked stretch improves19→15, but six native area samples
fail and new contacts occur in two poses. All five profile/legacy contour/front
tests pass; every failure remains recorded. Native run39073116321.
Before a fourth fitting approach, discuss a strict area/contact feasibility stage
with the owner; keep the confirmed contour and newer arm/elbow fixed. A next
geometry candidate must be separately named R43. R41 remains the immutable model
baseline. Private reference photos are not in the repository.


## Latest continuation — 18 October: R43 rejected; R44 area-bound repair

R43 finished as a rejected unsaved study, with native comparison images and two
press videos committed at21255f8b914f8fd0c98239742d741bd9c13a25bd. No R43 blend
was saved. See docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R43_20261017.md. It passes
13 benchmarks and adds no contacts, but loses the owner-confirmed junction and
fails area severity at two full-press samples. Motion/crease checks alone are
not visual approval. Artifact12120445839, run39079213916 preserve all failures.

The R43 optimizer applied the parent-relative area severity ceiling only to
already-stretched faces, disagreeing with the unchanged native checker. R44
fixes that mismatch, with a regression test seen failing before the fix and
passing afterwards. Its finer smooth fitting controls use exactly the same
editable material mask, verified by a new hash-based domain test. No older test,
R43 evidence, skeleton, protected arm/elbow geometry or HGPT_SHOULDER key changes.
See docs/CODEX_ORIGINAL_V1_R44_PLAN_20261018.md and workflow
.github/workflows/original-review-r44.yml. Save a separately named R44 model
only after native gates; retain and render a failed study otherwise. Owner
visual approval remains pending.


## Latest continuation — 18 October: R44 rejected; R45 material-distance correction

R44 native evidence is committed at961de0f578b3bfe2fc81064011e2e7bb874666e9.
Run39112671734/artifact12131744259 preserve its before/after images, two press
videos, logs and measurements. All83 native area/contact/motion/crease checks
and13 benchmarks pass. The approved-junction test still fails. Its pre-save
harness also hit a missing legacy temporary directory; no R44 model was saved.
The later rendered owner-profile test ran and failed independently. The R44
study remains immutable and rejected, with owner approval pending.

R45 diagnoses the spatial field's use of straight-line distance across skin
folds. It uses distance along rest-mesh edges for compact weights and boundary
fading, in exactly the same free/frozen material domain. A folded-surface
regression reproduces the old cross-surface control coupling and passes with
the corrected distance. New domain/preservation tests and all prior model
acceptance thresholds remain mandatory. The separately named R45 pre-save
harness creates its own staging directory and runs the unchanged prior tests.
See docs/CODEX_ORIGINAL_V1_R45_PLAN_20261018.md and workflow
.github/workflows/original-review-r45.yml. R45 starts with R44's retained body
increment; native evaluation and safety comparison still use immutable R41.
No skeleton, protected arm/elbow source coordinate,166, anchor, Basis, weight,
topology, HGPT_SHOULDER, non-S7 key or V-production asset changes are authorized.
A new model may be saved only after all fixed native/shape gates; retain any
failed study and report it honestly. Numerical checks are not owner approval.


## R45 result and R46 bounded continuation — 2026-10-18

R45 completed on run39115485844 and evidence commit a88afeb96a6c8429003a67478d8f84369cf2447c. It is rejected, with no saved model: all83 native responses and13 benchmarks passed, but the unchanged R42 owner-junction test still fails six measurements. Motion excess0.445976mm and posterior-crease excess1.797725deg. Its30-minute fitter limit interrupted ongoing progress after five accepted steps. The pre-save staging error from R44 is fixed; R45 reached the actual pre-save profile test and correctly refused saving.

Native artifact12132988179 SHA2564fa00d6fe12dc0a107d83f7b33aca9053e388611972bdd0d122b464900e2d0d1. Local images/video reviewed. See docs/CODEX_ORIGINAL_V1_REVIEW_CANDIDATE_R45_20261018.md.

R46 is a continuation from the exact retained R45 state, with150minutes maximum fitting and180minutes total. No fitting algorithm, skin domain, anatomical policy, test assertion or acceptance threshold changes. New named folder/test/workflow; normal source/evidence commits only. See docs/CODEX_ORIGINAL_V1_R46_CONTINUATION_PLAN_20261018.md. Source preparation/control tests are not model acceptance. Continue to inspect native outputs before claiming completion.


## R46 rejected; R47 scope investigation — 18 October

R46 evidence commit5c9fb322d7e29cf0916ccef05f78296f13f6cd18. No model saved; owner-junction shape still fails despite all83 native checks and13 benchmarks passing. The owner re-supplied the older whole-body reference and rejected this outline.

Read docs/CODEX_ORIGINAL_V1_R47_SHAPE_SCOPE_AUDIT_20261018.md before another fit. A reproducible read-only certificate finds12 upper-outline samples with exactly zero response to every permitted coordinate: that portion of arm-root skin was locked. The R42 outward-fill target also disagrees with the narrower whole-outline relationship in the supplied reference. A private, approximate2D outline overlay was prepared; no reference photo or trace is in the repo.

No R47 geometry exists. Broader shoulder-side/proximal-arm/upper-flank skin edits await the owner's required confirmation on the concrete overlay. Preserve newer elbow/distal-arm detail and all canonical/protected assets. Existing R42 test stays unchanged as historical evidence; resolve its conflicting target interpretation explicitly, with full-outline requirements and all safety checks retained, before accepting any next candidate. Do not launch another long continuation unchanged.
