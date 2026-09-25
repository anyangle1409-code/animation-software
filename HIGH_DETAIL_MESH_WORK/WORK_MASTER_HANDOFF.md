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

# Authoritative entry point

Before doing substantial work, read:

- `AUTONOMOUS_STUDIO_MASTER_PLAN.md` — full execution order from current V15 hand work through the self-sufficient prompt generator.
- `BLENDER_ONLY_REMAINING.md` — tasks that genuinely require direct Blender/Work control; keep deterministic/source work outside Blender where possible.
- `CURRENT_STATE.md` — current frozen baselines and immediate status.
- `NEXT_ACTION.md` — current phase action.

The master roadmap does not override phase gates; it tells you when each prepared tool becomes active.

# HOME GYM PT — Work Master Handoff

## Latest checkpoint — 2026-09-25

Read `V15_SESSION_2026-09-25.md` before executing the V15 plan below. The prepared V15a and later trial attempts have been run. V15b is a preserved, technically validated comparison trial, but **no V15 geometry is accepted**: the matched visuals still show segmentation and the severe-fold seam metric worsens. V13e remains the hand source and V8 the body/knee baseline. Grip refitting and production promotion remain blocked by the hand-anatomy visual gate. Continue with a new V13e-derived candidate only after addressing the fold/shaft topology locally; do not overwrite V15a–V15e.

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

From `HIGH_DETAIL_MESH_WORK`, run:

`START_V15_HAND.bat`

This is the authoritative launcher. It runs preflight first, creates
`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15a_deep_hand_rebuild.blend` from V13e
if needed, then opens Blender with diagnostic selection groups and the V15 Hand
sidebar. The preparation has no intended geometry displacement.

Optional static tooling check first:

`CHECK_PREPARED_TOOLING.bat`

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


## Prepared Phase C candidate evaluator

The numeric/regression evaluation path is already prepared.

Start from:

`PHASE_C_GRIP_CANDIDATE_TEMPLATE.json`

Copy it to a new candidate JSON and edit only:
- `thumbOppositionX`;
- `handleCentre`;
- per-digit MCP/PIP/DIP rows.

Then run:

`EVALUATE_PHASE_C_GRIP.bat accepted_hand.glb candidate.json <label>`

The runner:
- fetches the newest source branch into a disposable worktree;
- preserves the shipped `homeGymPTMale` row;
- injects the candidate under its own temporary solution ID;
- tags a **copy** of the accepted hand GLB to select that ID;
- proves the metadata selected the candidate row;
- checks the row against joint limits across every current dumbbell exercise closure;
- runs the existing shipped-path skinned-cylinder grip harness on both hands in curl/press;
- requires no digit/thumb penetration beyond the existing 0.5 mm contact tolerance;
- reports palm loading separately rather than treating intended palm contact as a failure;
- requires at least the existing 190° wrap diagnostic floor;
- compares mirrored-hand, equipment-clearance and self-collision tests baseline vs candidate;
- optionally requires the full normal source suite;
- writes `reports/phase_c_grip_<label>/phase_c_grip_evaluation.json`;
- removes the disposable worktree;
- never promotes or overwrites the production grip row.

A numeric PASS still requires the matched high-zoom visual grip boards described
above before acceptance.


## Prepared Phase C seed generation

Before hand-editing a candidate row, generate coarse solver-derived seeds from
the accepted hand:

`GENERATE_PHASE_C_GRIP_SEEDS.bat accepted_hand.glb <label>`

Default absolute handle-centre Y sweep (relative to the embedded centre):
- 0 mm
- -3 mm
- -6 mm
- -9 mm
- -12 mm

This range is grounded in the project's existing 0/-6/-9/-12 mm evidence. It is
a coarse search, not an acceptance preference.

For each centre the runner:
- fetches the latest source in a disposable worktree;
- reads the **current** shipped `homeGymPTMale` centre rather than assuming -9 mm;
- runs the existing close-until-contact skinned solver on the accepted hand;
- converts the solved curl-closure angles back to closure=1 `SolvedGrip` maxima;
- verifies the same row on the mirrored right hand;
- records per-digit/thumb/palm contact and wrap;
- writes a standalone candidate JSON.

Then run the stronger certification on shortlisted JSON files:

`EVALUATE_PHASE_C_GRIP.bat accepted_hand.glb candidate.json <label>`

Seed generation never promotes a row and does not replace visual review.


## Phase C visual review is also automated

A successful/complete candidate evaluation generates:
- baseline solid/contact overlay;
- candidate solid/contact overlay;
- baseline/candidate handle cross-sections;
- baseline/candidate three-quarter grip views;
- `phase_c_grip_review.html` with the numeric summary and matched images.

Open it with:

`OPEN_PHASE_C_GRIP_REVIEW.bat <label>`

The images come from `review-assets/harnesses/gripview.test.mts`, using the same
posed skinned vertices and handle transform as the grip metric.

The dashboard still requires an explicit visual anatomy verdict. It does not
auto-promote the candidate.


## Resume after Work usage limit

When a GPT Work session resumes after the 5-hour limit, read:

`WORK_RESUME_AFTER_LIMIT.md`

It is the authoritative unattended V15f resume sequence and supersedes any older generic V15 "start all eight digits" instruction.


## V15f-specific recovery

For ring/pinky proof, scope, sharpness or severe-fold failures, read:

`V15F_FAILURE_RECOVERY.md`

Use the older `V15_FAILURE_RECOVERY.md` for export/frozen/current-source pipeline failures.


## Local safe deterministic runner

`PREPARE_V15F_LOCAL_PATCH.bat` now requests a detached local safe runner as
well as opening Blender.

Manual controls:

`START_V15F_SAFE_RUNNER.bat`

`STOP_V15F_SAFE_RUNNER.bat`

The runner has a strict whitelist. It may automatically:
- run the correct saved-digit audit after a new V15f Blend save;
- run Stage-A numeric validation when all four Stage-A digit proofs are complete;
- generate missing matched visual boards;
- run Stage-B per-digit deterministic validation/render steps;
- run the final `RUN_V15_POST_EDIT_ALL.bat v15f_deep_hand_rebuild` once every
  required numeric + explicit visual gate has passed;
- refresh `V15F_LATEST_HANDOFF.md`.

It may **not**:
- edit Blender geometry;
- mark a visual PASS/FAIL;
- promote a mesh/grip;
- merge source;
- alter production references;
- loosen a threshold;
- cross an unresolved visual gate.

This means deterministic laptop work can continue after a save even if GPT Work
usage is exhausted immediately afterward. Whether the detached local process
survives the host Work session ending depends on the local environment, so do
not treat it as a guaranteed replacement for GPT Work itself.

The runner exits when only the final V15 review remains, when its 8-hour local
lifetime expires, or when the stop flag is requested.
