# Next action: V15 deep finger shaft/joint rebuild from V13e

V8 remains the accepted body/knee baseline. **V13e is the hand geometry starting point. V14e is experimental/rejected and must not become the geometry baseline.**

The V14e result proves that adding thousands of local vertices plus constrained smoothing is not enough. The next pass must rebuild the **actual finger shaft, knuckle/joint and problematic unwelded/local patch surface topology** on index, middle, ring and little fingers on both hands.

Read:
- `V15_DEEP_HAND_REBUILD_PLAN.md`
- `V15_WORK_HANDOFF.md`

## First action

From `HIGH_DETAIL_MESH_WORK`, run:

`START_V15_HAND.bat`

That is the authoritative start path. It first runs the fail-fast V15 preflight
(branch/baseline hashes, protected contacts, Python helper syntax, required
tools), creates the V15a diagnostic Blend from V13e if needed, and opens it in
Blender with the **V15 Hand** helper sidebar loaded.

Optional static check before opening Blender:

`CHECK_PREPARED_TOOLING.bat`

Expected first-attempt Blend:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend`

The preparation step changes no vertex positions. It creates diagnostic groups
for protected push-up contacts, patch boundaries, sharp folds, safe rebuild
core and per-digit ownership.

## Geometry task

Work from V13e only.

Replace or redirect the interior shaft/joint surface topology that causes the broad segmented silhouette. Preserve every original V8-source vertex record and its `v8_source_id`; rebuild faces/edge flow and add vertices rather than deleting original source vertices. Preserve exact anchor/contact positions and skin rows. Interpolate UVs and normalised deform weights onto new vertices. Use rounded longitudinal flow and gradual joint transitions rather than another subdivision/smoothing-only pass.

Keep:
- all **682 protected original push-up contacts** exact;
- non-hand body unchanged;
- frozen 63-bone `hgpt_canonical_v3`;
- exercise/equipment/grip/retarget behaviour unchanged;
- production references unchanged;
- palm/thumb exercise motion and scapular rhythm off.

## Visual gate

Generate matched V13e/V15:
- open palm/back/web;
- closed fist palm/back/side;
- curl;
- push-up;
- pull-up.

Do not accept V15 because it passes guards or contains more topology. It must visibly reduce the inherited broad faceting/segmentation while preserving push-up contact.

No grip refit until this gate is passed.

## Validation lane A — frozen comparison

Pinned runtime:

`614033b256d869230ea273522620467401b0bc71`

Keep this pin unchanged for reproducibility.

Require the established protected-contact, retarget, seam, bare/dressed and exercise comparison gates.

## Validation lane B — latest source integration

Current integration target at handoff creation:

`chatgpt/absolute-retarget-imports @ 47187360b5d631d438a6b33b284ad06732e244cb`

State at that HEAD:
- 28 exercises
- recorded suite 868 passed / 1 skipped

Use a disposable source checkout. **Do not merge the source branch into the mesh branch.**

Run every current gate that swaps `REAL_CHARACTER_GLB`, plus the mesh coordination report, against V15.

Known V8/V13e body-shape measurements — arm/chest baselines, incline-curl thigh graze, near-limit bench compression — are not hand blockers and must not be “fixed” inside V15.

## Stop conditions

Stop and report rather than compensate if:
- any protected push-up contact or skin row changes;
- a fix requires changing a grip, exercise, equipment transform, retargeting or guard;
- non-hand geometry changes;
- new nonmanifold/open-edge defects appear;
- bare/dressed posed equivalence breaks;
- visual improvement is again marginal.

Only a visibly improved and technically passing candidate may become the geometry source for Phase C grip fitting.


## After the Blender edit

Save the V15a Blend and run:

`RUN_V15_POST_EDIT_ALL.bat`

That single command handles invariant audit, GLB packing, bare variant, frozen validation, direct V13e/V15 visual boards and disposable latest-source integration validation.


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
