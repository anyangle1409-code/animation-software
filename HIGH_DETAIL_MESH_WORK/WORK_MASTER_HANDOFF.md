# HOME GYM PT — Work Master Handoff

This is the **single current handoff file for ChatGPT Work**.

Read this file first, then run `RESUME_WORK.bat`.

## 1. Exact current state

### Source / canonical rig
- Repository: `anyangle1409-code/animation-software`
- Frozen canonical skeleton commit: `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- Current runtime / retarget source commit: `614033b256d869230ea273522620467401b0bc71`
- Skeleton ID: `hgpt_canonical_v3`
- Canonical bones: **63**
- Hierarchy status: **STRUCTURALLY FROZEN**
- Current source branches at the runtime commit:
  - `chatgpt/absolute-retarget-imports`
  - `claude/home-gym-pt-animation-txux66`
- Current source validation: **426 passed / 1 skipped / 52 files**
- Typecheck: clean
- Build: clean

### Mesh / Blender workspace
- Work branch: `codex-high-detail-candidate-v6-knee-review-20260922`
- Reviewed geometry baseline: **V6 knee seam**
- New review candidate awaiting acceptance: **V7 knee retopology**; see `REVIEW_V7_KNEE_RETOPOLOGY.md`
- V6 asset creation commit: `b2203cfccd30d6835473ef2e1dee37965da22d02`
- Baseline files:
  - `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb`
  - `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb`
  - `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend`
- V6 body: 33,089 vertices / 62,961 triangles
- V6 remains the geometry source and must not be overwritten.

## 2. What is finished and must not be reopened

The following source-side structure is settled:

- 63-bone canonical hierarchy
- pelvis / spine / neck / head
- clavicles
- scapulae
- shoulders / upper arms
- elbows / forearms
- wrists / hands
- hips / knees / ankles / toes
- all finger chains
- four metacarpals per hand
- thumb base / CMC behaviour through `thumb_01`
- forearm twist helper distribution at the character layer
- mirrored-character hand-roll retarget fix

Do **not** add, remove, rename or re-parent canonical bones.

The freeze is protected by `src/rig/frozen.test.ts`.

## 3. Important current runtime behaviour

### Scapula
- scapula bones exist
- scapular rhythm is **OFF**
- final scapula deform weights are **not painted yet**

### Palm / thumb
- palm/metacarpal structure exists
- thumb opposition/twist capability exists
- palm cupping and thumb twist are **not yet driven by exercise motion**
- the current production character's exported palm bones are badly placed and unweighted, so they are not yet suitable for visible palm cupping

### Mirrored hand roll
Fixed at runtime commit `614033b`.

Before the fix, the production mirrored hand was about 5.5° off.
After the fix:
- curls: ~0.72° residual
- shoulder press / squat: 0.00°
- mirrored synthetic hand now matches same-side behaviour

Existing embedded grip offsets are automatically carried from the old hand frame into the corrected frame.

### Grip warning
The curl grip's widest finger-wrap gap changed from **36° to 66°** after the hand frame was corrected.

Do **not** undo the retarget fix.

Refit/re-solve the curl grip later against the final improved hand geometry.

## 4. What Work has access to

Work has access to the latest source definitions and all 63 canonical bones through the repo.

`RESUME_WORK.bat` prepares an isolated `validation_63` source tree from runtime commit:

`614033b256d869230ea273522620467401b0bc71`

This includes the frozen v3 skeleton and the mirrored-hand retarget fix.

Important distinction:

The current V6 GLB is **not yet a newly rebound 63-bone production asset**. It still carries its existing character rig and weights.

That is intentional.

Work should improve the geometry first. Final asset binding/weighting comes afterwards.

## 5. Work to do now — in order

### Phase A — knee retopology
Do this first.

Goal:
- replace the still-open medial-knee strips with connected anatomical loops
- remove the pointed medial-knee overhang
- improve patella / tendon / medial-knee shape
- keep knee flexion clean in squat poses
- preserve left/right symmetry
- preserve all existing accepted exercise mechanics

Do not fake the fix with pose offsets.

### Phase B — hand geometry
After the knee candidate is reviewed.

Improve:
- finger shape
- finger joint definition
- thumb base / web
- palm shape
- wrist transition
- believable closed-fist/grip silhouette

Preserve:
- push-up floor-contact guard
- existing hand proportions unless measured evidence supports a correction
- frozen canonical hierarchy

Do not finalise grip tuning until the geometry is stable.

### Phase C — grip refit
After final hand geometry.

Re-solve/review:
- curl dumbbell grip
- press dumbbell grip
- pull-up grip where relevant

The corrected hand frame is now the reference.

The old 36° wrap-gap target must not be restored blindly; solve against actual contact, penetration, wrap and visual fist quality.

### Phase D — skin/material refinement
Improve appearance without changing rig behaviour.

### Phase E — shoulder / back / chest / armpit topology
Prepare the final mesh around the frozen scapula structure.

Do not enable scapular rhythm yet.

### Phase F — final character binding and weights
Only after geometry is accepted.

The final character asset should then:
- preserve the frozen 63-bone canonical structure
- correctly use/represent palm/metacarpal deformation where required
- correctly introduce/use scapula deform influence
- preserve the character-specific forearm twist helper behaviour
- prove neutral/rest equivalence before any new motion is enabled

Then paint/tune:
- shoulder
- scapula / upper back
- chest / armpit
- hand / palm
- wrist / forearm

### Phase G — movement activation
Only after the final weighting pass is proven.

Then source-side work can:
- enable/tune palm cupping
- enable/tune thumb opposition/twist
- enable/tune scapular rhythm
- refine solver behaviour where required

## 6. Laptop workflow

From `HIGH_DETAIL_MESH_WORK`:

```text
RESUME_WORK.bat
START_CANDIDATE.bat <version>
```

After Blender editing/export:

```text
FINISH_CANDIDATE.bat <version> <task>
```

Task must be one of:
- `knee`
- `hand`
- `material`
- `shoulder`

The finish workflow validates against the current v3 runtime source, runs guards, exercise comparison, task-specific checks, renders review views, and writes checkpoint metadata.

## 7. Hard rules

Do not:
- overwrite V6
- alter the frozen canonical hierarchy
- change accepted exercise mechanics to hide a mesh problem
- loosen validation thresholds just to pass
- promote or merge without explicit approval
- enable scapular rhythm during mesh-only work
- enable palm/thumb exercise motion before final binding/weights
- change production asset references during candidate work
- treat the mannequin hand-shape mismatch as a reason to change the canonical skeleton

## 8. Stop conditions

Stop and report instead of improvising if:
- a mesh fix requires changing accepted exercise mechanics
- a guard must be loosened to make the candidate pass
- knee work changes unrelated areas
- hand geometry unexpectedly changes floor contact
- a candidate requires a new canonical bone
- scapular rhythm is required just to make static mesh geometry look acceptable
- unexplained rig, skin, material, animation or retarget changes appear

## 9. What to report back

For each completed candidate, report only what matters:
- candidate version
- exact Blender / bare GLB / dressed GLB filenames
- hashes
- exact geometry changes
- tests / guards
- key visual review findings
- remaining defects
- whether it is safe to continue to the next phase

Do not promote automatically.

## 10. Immediate next action

Phase A has a first validated V7 knee candidate. V6 remains the read-only accepted baseline until review. Inspect `REVIEW_V7_KNEE_RETOPOLOGY.md` and `renders_v7_knee_retopology/V7_KNEE_V6_COMPARISON.jpg`. The pointed squat flap is substantially reduced, but a small medial notch and simplified patellar dome remain. Decide whether the knee needs another candidate pass before treating V7 as the next geometry baseline.

Stop for this knee review before moving into the hand geometry pass. Do not promote V7 automatically.
