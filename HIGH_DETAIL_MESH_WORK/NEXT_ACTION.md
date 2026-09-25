# Next action: V15 deep finger shaft/joint rebuild from V13e

## Prepared next attempt: V15f local ring/pinky reconstruction

After the 2026-09-25 V15a–e session, the next attempt is deliberately narrower.

Read:

- `V15_SESSION_2026-09-25.md`
- `V15F_LOCAL_PATCH_PLAN.md`

Start with:

`PREPARE_V15F_LOCAL_PATCH.bat`

This creates/opens a fresh V13e-derived `v15f_deep_hand_rebuild` candidate and
adds non-destructive ring/pinky high-dihedral hotspot groups/guides.

**Stage A is ring/pinky only.** Do not touch index/middle yet.

After the local ring/pinky reconstruction, run:

`AUDIT_V15F_STAGE_A.bat`

Proceed to index/middle only if Stage A passes the V13e no-regression gate for:
- general stable-ID/contact/topology invariants;
- total >100° folds;
- per-digit ring/pinky >100° folds;
- per-digit ring/pinky >35° sharp-length ratio.

Only after the complete hand passes the Blender audit should V15f enter the
normal export/frozen/current-source review pipeline.

## 2026-09-25 checkpoint: anatomical gate not cleared

V15a and V15b are preserved experimental candidates. V15b passed frozen motion/contact checks and the automated visual-change magnitude calibration, but its matched boards still show segmented finger shafts and its bind seam audit has 8 severe folds versus V13e's 4. V15e's added joint control geometry also increased sharpness. Do **not** accept/promote any V15 attempt or start grip refitting.

The next safe modelling action is a manually supervised local Blender patch reconstruction from the V13e source, using the prepared CORE/ANCHOR groups and the actual mesh surface. Rebuild the ring and pinky shaft/joint surfaces first, then index/middle; preserve all stable IDs and protected contacts. Recheck severe-fold counts before exporting. `V15_SESSION_2026-09-25.md` records the failed approaches and review paths. This is the handoff's genuine stop condition after multiple candidate-side approaches, so no validation threshold or frozen mechanics should be altered to make a trial pass.

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


## Resume after Work usage limit

When a GPT Work session resumes after the 5-hour limit, read:

`WORK_RESUME_AFTER_LIMIT.md`

It is the authoritative unattended V15f resume sequence and supersedes any older generic V15 "start all eight digits" instruction.


## V15f directional hotspot aid

The V15f hotspot preparation also classifies >35° sharp edges by direction
relative to the finger axis:

- **Cross-band >35°** — sharp edges running around/across the shaft. These are
  high-priority when they create the segmented "sausage-link" appearance.
- **Longitudinal >35°** — sharp edges running along the finger. These can indicate
  a side ridge/facet and should be inspected separately.

Both selections are available in the V15 Hand sidebar for V15f. The generated
`reports/prepare_v15f_hotspots.json` records directional counts and the
strongest edge locations.


## First topology proof

Before propagating a new topology strategy across ring/pinky, edit **ring_L only**
and run:

`AUDIT_V15F_RING_PROOF.bat`

This requires:
- general V15 invariants;
- no other finger's original positions changed;
- total >100° folds no worse than V13e;
- ring_L >35° and >50° sharp-length ratios no worse than V13e;
- ring_L >100° fold count no worse than V13e.

Only after this passes should the approach be tried on ring_R.

After each later digit use:

`AUDIT_V15F_DIGIT.bat ring_R`

`AUDIT_V15F_DIGIT.bat pinky_L`

`AUDIT_V15F_DIGIT.bat pinky_R`

The incremental gate also ensures fingers outside the approved sequence have not
moved.

At any interruption run:

`V15F_STATUS.bat`

to get the current artifact/gate state and next documented action.


## Prepared Stage B — index/middle

After Stage-A numeric **and visual** PASS, read:

`V15F_STAGE_B_PLAN.md`

Stage B is also incremental:

1. index_L
2. index_R
3. middle_L
4. middle_R

For each digit:
1. edit only that digit;
2. save/checkpoint;
3. run:
   `AUDIT_V15F_STAGE_B_DIGIT.bat <digit>`
4. the numeric PASS automatically generates a matched V13e/V15f visual board;
5. open it with:
   `OPEN_V15F_STAGE_B_VISUAL.bat <digit>`
6. record:
   `MARK_V15F_STAGE_B_VISUAL.bat <digit> pass|fail`

The Stage-B gate freezes the approved Stage-A ring/pinky surfaces by
per-digit SHA-256 surface fingerprint and prevents later Stage-B digits from
being touched early.

`V15F_STATUS.bat` drives this sequence automatically.


## One-command resume

For the next GPT Work session, the safest single entry point is:

`RESUME_V15F_WORK.bat`

It does **not** reset, clean or pull over local files. It:
- runs `CHECK_PREPARED_TOOLING.bat` logic;
- prints `V15F_STATUS`;
- creates V15f from V13e if it does not yet exist;
- otherwise refreshes the handoff, starts the local safe deterministic runner,
  and opens the existing V15f Blend with the V15 Hand sidebar.

The detailed documents remain authoritative if the status reports a blocked or
visual-decision state.


## Additional V15f shape-quality diagnostics

The shared Blender audit now also reports advisory per-digit bind-pose shape
signals:
- cross-section radius spread;
- transverse section axis ratio;
- longitudinal radius-profile jump;
- radius-profile second-difference.

These are intended to catch a finger that has fewer sharp edges but still has a
segmented/lumpy diameter profile. They are reported in
`shape_quality_priority` and surfaced in `V15F_LATEST_HANDOFF.md`.

They are **diagnostic only** until calibrated; do not turn them into hard
acceptance thresholds or override visual anatomy review solely from these values.
