# Authoritative entry point

Before doing substantial work, read:

- `AUTONOMOUS_STUDIO_MASTER_PLAN.md` — full execution order from current V15 hand work through the self-sufficient prompt generator.
- `BLENDER_ONLY_REMAINING.md` — tasks that genuinely require direct Blender/Work control; keep deterministic/source work outside Blender where possible.
- `CURRENT_STATE.md` — current frozen baselines and immediate status.
- `NEXT_ACTION.md` — current phase action.

The master roadmap does not override phase gates; it tells you when each prepared tool becomes active.

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


## V15 automation index

The surrounding V15 workflow is now prepared. Work should spend its usage on
the actual finger-surface modelling and visual judgement, not setup.

### Before Blender
- `V15_PREFLIGHT.bat` — verifies branch safety, exact V8/V13e hashes, 682
  protected contacts, helper-script syntax, Python/Node/Git and Blender.
- Preflight is also run automatically by every `START_V15_HAND.bat`.

### Start / continue modelling
- `START_V15_HAND.bat` — first/default attempt (`v15a_deep_hand_rebuild`).
- `START_V15_HAND.bat v15b_deep_hand_rebuild` — explicit preserved version.
- `START_NEXT_V15.bat` — automatically chooses the next unused V15 letter.
- `LIST_V15_ATTEMPTS.bat` — lists preserved attempts and available validation state.

Blender opens with a **V15 Hand** sidebar containing:
- protected-contact selection;
- per-digit CORE / ANCHOR / SHARP / PIP / DIP / DISTAL selection;
- isolate/reveal;
- guide visibility toggle;
- numbered non-destructive checkpoint-copy button.

### After saving the edited Blend
Run only:

`RUN_V15_POST_EDIT_ALL.bat <version>`

It performs:
1. invariant/stable-ID Blender audit;
2. export-only repair of genuinely new vertex UV/weights;
3. export-only triangulation;
4. stable-ID dressed GLB packing;
5. bare variant;
6. frozen `614033b` validation;
7. V13e/V15 matched hand renders;
8. V14e-calibrated visual-change analysis;
9. V13e/V14e/V15 per-digit faceting diagnostics;
10. seam/fold audit;
11. disposable latest-source full-suite/integration validation;
12. consolidated Markdown report;
13. local HTML dashboard with difference maps.

### Review
- `OPEN_V15_REVIEW.bat <version>` — opens the dashboard.
- `V15_POST_EDIT_REPORT_<version>.md` — concise machine-generated result.
- `V15_FAILURE_RECOVERY.md` — exact recovery action for each failing stage.

### After visual acceptance only
Read:
- `PHASE_C_GRIP_REFIT_PLAN.md`
- `PHASE_C_WORK_HANDOFF.md`

Do not activate Phase C before the hand anatomy is visually accepted.


## Prepared later-phase tools

These are dormant until their phase gates are met:

### Phase D — appearance
- `PHASE_D_SKIN_MATERIAL_PLAN.md`
- `MAKE_PHASE_D_SKIN_SWEEP.bat <candidate_version>`

### Phase E — shoulder topology
- `PHASE_E_SHOULDER_TOPOLOGY_PLAN.md`

### Phase F — final source-rig weights / retarget intake
- `PHASE_F_FINAL_BINDING_PLAN.md`
- `AUDIT_PHASE_F_SOURCE_RIG.bat reference.glb candidate.glb`
- `VALIDATE_PHASE_F_RUNTIME.bat reference.glb candidate.glb label`

### Phase G — motion activation
- `PHASE_G_MOVEMENT_ACTIVATION_PLAN.md`

Do not jump ahead simply because these tools exist. Each plan states its entry gate.


## End-goal continuation

After character/rig/motion phases are accepted, continue with:
- `PHASE_H_SELF_SUFFICIENT_GENERATION_PLAN.md`
- `PROMPT_FAMILY_CERTIFICATION_MANIFEST.json`
- `START_PROMPT_FAMILY_CERTIFICATION.bat <family>`
- `AUDIT_PROMPT_GENERATION_COVERAGE.bat`

Final integrated release proof:
- `FINAL_SYSTEM_ACCEPTANCE_PLAN.md`
- `RUN_FINAL_SYSTEM_ACCEPTANCE.bat final_character.glb`


## Prepared-tooling self-check

At any phase, before spending substantial Work/Blender usage, run:

`CHECK_PREPARED_TOOLING.bat`

It statically compiles every Python helper and verifies the authoritative roadmap/phase/launcher files plus the 16-family / 28-exercise certification manifest. It does not require Blender, Node modules or network access and does not modify candidates.
