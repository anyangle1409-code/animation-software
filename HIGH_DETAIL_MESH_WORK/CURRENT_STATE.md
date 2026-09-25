## Master roadmap / Work usage

Authoritative high-level roadmap:
- `AUTONOMOUS_STUDIO_MASTER_PLAN.md`

Blender/Work-only task map:
- `BLENDER_ONLY_REMAINING.md`

Use direct Blender Work only for interactive topology, source-rig/bone placement that needs 3D judgement, weight painting/deformation tuning, and final visual inspection that cannot be resolved from generated boards. Deterministic code, GLB transforms, validation, reports, prompt certification and source work should stay outside Blender where possible.

# Current source of truth

This file is the authoritative entry point for the high-detail mesh review workspace.

## Current status

- Accepted body/knee geometry baseline: **V8**
- Current hand review baseline: **V13e fingertip retopology**
- **V14e is an unaccepted experimental checkpoint**. Its added finger-body loops and constrained smoothing passed technical guards but did not visibly fix the broad segmented finger silhouette.
- Next candidate: **V15 deep hand rebuild**, starting from V13e, using `V15_DEEP_HAND_REBUILD_PLAN.md` and `V15_WORK_HANDOFF.md`.
- Grip refit has **not** started and must remain held until hand geometry is visually accepted.

The canonical hierarchy is frozen at **63 bones**:
- structural freeze: `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- skeleton ID: `hgpt_canonical_v3`

## Validation sources — keep separate

Two validation lanes are required.

### A. Frozen historical comparison pin

`614033b256d869230ea273522620467401b0bc71`

Use this unchanged for reproducible mesh comparisons and the established hand guards. It includes the mirrored-hand-roll runtime fix.

### B. Current source integration target

At the time this handoff was prepared:

- branch: `chatgpt/absolute-retarget-imports`
- HEAD: `47187360b5d631d438a6b33b284ad06732e244cb`
- library: **28 exercises**
- recorded suite: **868 passed / 1 skipped**

The source branch has advanced well beyond the frozen comparison pin. Current-source validation must be done in a **disposable checkout**. Do not merge the source branch into the mesh candidate branch.

The current source contains the broader collision/contact/equipment gates and the mesh coordination report. Re-run those against any candidate that is being considered for acceptance.

## Geometry assets

Accepted body/knee checkpoint:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend`

Current hand review source:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v13e_fingertip_retopology.blend`

Rejected/experimental comparison only:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v14e_finger_body_trial.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v14e_finger_body_trial_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v14e_finger_body_trial.blend`

Preserve all earlier candidates. Use `CANDIDATE_BASELINE_MANIFEST.json` for machine-readable hashes/state.

## Current mesh coordination facts

The current-source coordination report shows V8 and V13e are identical on body measurements, as expected for a hand-only change.

Known body-shape items that **do not block the hand rebuild**:
- arm-to-chest baseline differences on the fuller high-detail body;
- incline curl dumbbell/thigh graze of about 0.8 mm;
- bench support compression close to the existing limit.

A hand-only V15 candidate must not materially change those body measurements.

## Instruction precedence

1. `CURRENT_STATE.md`
2. `NEXT_ACTION.md`
3. `V15_DEEP_HAND_REBUILD_PLAN.md`
4. `V15_WORK_HANDOFF.md`
5. `RIG_63_FREEZE.md`
6. latest candidate review notes
7. older handoff/reproduction notes as historical evidence only

Any older note that calls V10/V11 the immediate next action is superseded.

## Ready work

Work may continue autonomously on:
- V15 index/middle/ring/little finger shaft and joint **geometry rebuild from V13e**;
- candidate-only topology diagnostics;
- matched hand review renders;
- frozen and latest-source integration validation.

## Still held

- grip refit;
- production promotion;
- scapular rhythm;
- palm/thumb exercise-motion activation;
- final scapula deform weighting;
- changes to accepted exercise mechanics to accommodate a mesh.

## V15 fast path

Run:

`scripts/prepare_v15_deep_hand_blender.py`

It creates:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend`

with diagnostic vertex groups and **zero intended geometry displacement**.

Then perform only the local finger shaft/joint rebuild described in `V15_DEEP_HAND_REBUILD_PLAN.md`.

## Hard rules

Do not:
- build V15 from V14e;
- overwrite V8, V13e or V14e;
- move any of the 682 protected original push-up contacts or alter their skin rows;
- modify the frozen hierarchy;
- change exercise mechanics, grips, equipment, contacts or retargeting to make a mesh pass;
- loosen guards;
- enable scapular rhythm or palm/thumb exercise motion;
- change production asset references during candidate work;
- promote automatically.

A candidate passes only if it is **both technically clean and visibly better than V13e**.


## V15 prepared execution environment

Preparation branch:

`work/v15-deep-hand-rebuild-prep-20260925`

The branch now contains a fail-fast, versioned V15 execution environment:
- exact baseline/hash preflight;
- V13e diagnostic candidate creation;
- per-digit Blender guide/selection groups and helper sidebar;
- stable-ID invariant checking;
- export-only UV/weight repair and triangulation;
- stable-ID GLB packing;
- frozen comparison validation;
- direct V13e matched visual review;
- rejected-V14e image and geometry calibration;
- latest-source disposable integration validation;
- candidate iteration/preservation manager;
- failure recovery guide;
- review dashboard/difference maps;
- dormant Phase C grip-refit plan.

No V15 geometry has been created or accepted by these preparation commits. The
remaining irreducible current-phase work is the actual Blender shaft/joint
surface rebuild plus the visual anatomy decision.


## End-goal continuation

After character/rig/motion phases are accepted, continue with:
- `PHASE_H_SELF_SUFFICIENT_GENERATION_PLAN.md`
- `PROMPT_FAMILY_CERTIFICATION_MANIFEST.json`
- `START_PROMPT_FAMILY_CERTIFICATION.bat <family>`
- `AUDIT_PROMPT_GENERATION_COVERAGE.bat`

Final integrated release proof:
- `FINAL_SYSTEM_ACCEPTANCE_PLAN.md`
- `RUN_FINAL_SYSTEM_ACCEPTANCE.bat final_character.glb`
