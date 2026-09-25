# HOME GYM PT — Work Master Handoff

This file is intentionally short. The previous V10/V11 instructions are superseded.

Read in this order:

1. `CURRENT_STATE.md`
2. `NEXT_ACTION.md`
3. `V15_DEEP_HAND_REBUILD_PLAN.md`
4. `V15_WORK_HANDOFF.md`

## Current task

Create the next hand candidate as a **deep local finger shaft/joint topology rebuild from V13e**.

- V8 = accepted body/knee geometry baseline
- V13e = hand geometry starting point
- V14e = preserved experimental/rejected visual checkpoint
- no grip refit yet
- no production promotion

## Fixed rig/runtime facts

- frozen hierarchy: `hgpt_canonical_v3`, 63 bones
- structural freeze: `19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`
- frozen historical comparison pin: `614033b256d869230ea273522620467401b0bc71`
- latest source integration target at handoff creation:
  `chatgpt/absolute-retarget-imports @ 47187360b5d631d438a6b33b284ad06732e244cb`
- current source state recorded there: 28 exercises, 868 passed / 1 skipped

Keep frozen comparison and latest-source integration testing separate. Do not merge source into the mesh branch.

## First Blender action

Run:

`HIGH_DETAIL_MESH_WORK/scripts/prepare_v15_deep_hand_blender.py`

It creates:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend`

with diagnostic selection groups and no intended geometry displacement.

## Hard rules

Do not:
- build V15 from V14e;
- move the 682 protected original push-up contacts or alter their skin rows;
- alter the frozen hierarchy;
- change exercise mechanics, grips, equipment, retargeting, contacts or production references to make a mesh pass;
- loosen guards;
- enable scapular rhythm or palm/thumb exercise motion;
- promote automatically.

The candidate advances only if it is **visibly better than V13e** and passes both frozen and current-source validation.

See `V15_WORK_HANDOFF.md` for the exact Blender execution order, candidate naming, review views and stop conditions.


## Execution shortcut

After the V15a Blender mesh edit is saved, run:

`RUN_V15_POST_EDIT_ALL.bat`

Do not manually reproduce the export/validation steps. The command is intentionally fail-fast and does not promote or merge anything.


### Export housekeeping is automated

Work does not need to manually triangulate the editable V15 Blend or hand-author missing new-vertex UV/weight data before export. `RUN_V15_POST_EDIT_ALL.bat` creates a temporary export copy, repairs only genuinely new V15 vertices from V13e, triangulates that temporary copy, packs the GLB, and deletes the temporary copy.


## Two-command Work flow

From `HIGH_DETAIL_MESH_WORK`:

**Start / open the prepared Blender candidate**

`START_V15_HAND.bat`

This creates the V15a diagnostic Blend from V13e if it does not exist, then opens it in Blender with the body selected and the V15 guide groups/markers ready.

After the actual finger geometry edit is saved:

**Run everything after the edit**

`RUN_V15_POST_EDIT_ALL.bat`

That handles export preparation, GLB packing, bare variant, frozen validation, V13e/V15 matched renders, seam/fold checks, visual-change metrics, latest-source integration and the consolidated report.

Those are the only two workflow commands Work should need around the actual Blender modelling.


## If anything fails

Read `V15_FAILURE_RECOVERY.md` and repair the **first failing stage**. Do not
loosen a guard or change exercise/grip/runtime behaviour to make a hand mesh pass.


## Candidate iteration / preservation

Use `LIST_V15_ATTEMPTS.bat` to see every preserved V15 attempt and its available
validation state.

Repair the **current** candidate when the failure is local and objective:
- a stray vertex;
- missing UV/weight on new geometry;
- a seam/topology defect;
- a protected/contact leak that can be restored without changing the intended
  shaft/joint design.

Preserve the current candidate and start a **new** attempt when:
- the visual-change gate does not materially exceed rejected V14e;
- the basic shaft/joint strategy is visibly wrong;
- fixing it would require undoing most of the rebuild;
- the candidate is technically clean but visually rejected.

Start the next unused version with:

`START_NEXT_V15.bat`

For an explicit version:

`START_V15_HAND.bat v15b_deep_hand_rebuild`

After saving that candidate:

`RUN_V15_POST_EDIT_ALL.bat v15b_deep_hand_rebuild`

Never rename or overwrite an earlier attempt to reuse its letter.
