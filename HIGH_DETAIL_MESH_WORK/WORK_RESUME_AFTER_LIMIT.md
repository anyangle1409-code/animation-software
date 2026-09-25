# Work resume after 5-hour limit — V15f

## Purpose

This is the resume point for the next GPT Work session after the 2026-09-25
5-hour usage limit.

Do not restart the investigation. The previous Work session already completed
V15a–e experiments and established the next direction.

## Repository / branch

Repository:

`anyangle1409-code/animation-software`

Use only:

`work/v15-deep-hand-rebuild-prep-20260925`

Do not modify or merge:

`chatgpt/absolute-retarget-imports`

At resume:
1. run `git status`;
2. preserve any local/untracked Blender/generated files;
3. run `git fetch origin`;
4. confirm the current branch;
5. if the working tree is clean and the local branch is behind its remote,
   fast-forward only;
6. never reset/clean away local files just to match the remote.

Read, in order:

1. `V15_SESSION_2026-09-25.md`
2. `CURRENT_STATE.md`
3. `NEXT_ACTION.md`
4. `V15F_LOCAL_PATCH_PLAN.md`
5. `WORK_MASTER_HANDOFF.md`

## What the previous Work session proved

No V15 candidate is accepted.

- V15a: rejected; aggressive radial reconstruction caused pinching and large fold regression.
- V15b: best completed trial, technically strong but visually not acceptable.
  Index/middle sharpness improved, while ring/pinky remained the main problem.
- V15c: stable-ID failure; diagnostic only, never export.
- V15d: incomplete one-digit topology operation; diagnostic only.
- V15e: 1,165 added PIP/DIP control vertices, but sharp/fold metrics worsened.

Therefore V15f must **not** repeat whole-hand radial smoothing or indiscriminate
joint subdivision.

The remaining current blocker is local ring/pinky surface topology.

## V15f strategy

Start V15f fresh from **V13e**.

Do not build it from V15b or V15e.

V15f Stage A is deliberately incremental:

1. ring_L proof;
2. ring_R;
3. pinky_L;
4. pinky_R;
5. full ring/pinky Stage-A gate;
6. only then inspect index/middle.

The purpose is to prove the topology strategy on the smallest possible surface
before spending usage propagating it.

## Resume/status command

At any interruption or uncertain resume point, run:

`V15F_STATUS.bat`

It reports the current V15f artifacts/gates and the next documented action.

## First commands

From `HIGH_DETAIL_MESH_WORK` run:

`CHECK_PREPARED_TOOLING.bat`

Then:

`PREPARE_V15F_LOCAL_PATCH.bat`

This creates/opens:

`HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v15f_deep_hand_rebuild.blend`

fresh from V13e and adds non-destructive ring/pinky hotspot groups and guides.

No geometry is changed by the preparation.

## Blender sidebar

The **V15 Hand** sidebar now contains a V15f ring/pinky proof section.

It can select:
- Ring / Pinky
- Left / Right
- >35°
- >50°
- >75°
- >100°
- PIP hot
- DIP hot

It can also toggle `V15F_HOTSPOT_GUIDES`.

Start with **Ring Left** only.

Use the normal V15 CORE / ANCHOR / PIP / DIP groups to define the allowed
editing envelope.

## Ring-left proof

Do not apply a whole-core radial projection.

Do not globally subdivide the finger.

Do not delete original tracked vertices.

Inspect the real ring-left surface around the highest-dihedral guides and rebuild
only the local face/edge flow needed to remove accidental planar bands/folds
while preserving anatomical volume.

Prefer:
- longitudinal/circumferential edge flow;
- minimal new local control vertices;
- retained knuckle volume;
- fixed anchor transition;
- no movement outside the documented digit scope.

After the first ring-left topology attempt:

1. save a checkpoint with the V15 Hand sidebar;
2. save the current V15f Blend;
3. run:

`AUDIT_V15F_RING_PROOF.bat`

Equivalent incremental command:

`AUDIT_V15F_DIGIT.bat ring_L`

### If ring-left proof FAILS

Do not propagate the topology to the other fingers.

Stay on ring_L only.

Read:
- `reports/v15f_ring_l_proof_gate.json`
- `reports/audit_v15f_deep_hand_rebuild_blender.json`

Repair the local edge flow/volume and rerun the proof.

If the basic approach is clearly wrong, preserve/checkpoint it and try another
local topology strategy rather than smoothing harder.

### If ring-left proof PASSES

Save another checkpoint.

Then reconstruct ring_R using the same **principle**, not blind coordinate
copying if the mirrored source surface differs.

Run:

`AUDIT_V15F_DIGIT.bat ring_R`

Only continue if it passes.

Then:

`AUDIT_V15F_DIGIT.bat pinky_L`

and:

`AUDIT_V15F_DIGIT.bat pinky_R`

after their respective edits.

## Stage-A gate

When all four ring/pinky digits have individually passed, run:

`AUDIT_V15F_STAGE_A.bat`

Do not touch index/middle until Stage A passes.

The Stage-A gate requires:
- general V15 stable-ID/contact/topology invariants;
- total >100° digit folds no worse than V13e;
- ring/pinky per-digit >100° fold counts no worse than V13e;
- ring/pinky >35° sharp-length ratios no worse than V13e.

These are no-regression gates, not final visual acceptance.

## Stage B

Only after Stage A passes:

1. checkpoint the successful ring/pinky state;
2. visually inspect index/middle;
3. rebuild only remaining visible local problem patches;
4. do not blindly rerun V15b whole-core radial reconstruction;
5. run the full Blender audit again.

V15b proved index/middle can improve under conservative changes, but the new
V15f topology should be driven by direct surface inspection rather than another
whole-digit script.

## Full V15f validation

Only after the whole-hand Blender audit is clean run:

`RUN_V15_POST_EDIT_ALL.bat v15f_deep_hand_rebuild`

Then:

`OPEN_V15_REVIEW.bat v15f_deep_hand_rebuild`

Do not start Phase C unless V15f is technically clean **and** explicitly
visually accepted.

## Frozen rules

Preserve:
- V8 body/knee baseline;
- V13e hand source;
- all original stable IDs;
- all 682 protected push-up contacts and their skin rows;
- non-digit positions/weights;
- `hgpt_canonical_v3`;
- existing rig;
- exercise mechanics;
- grip behaviour;
- equipment transforms;
- retargeting;
- production references.

Never loosen a gate to make V15f pass.

Never change mechanics to compensate for mesh anatomy.

## Unattended continuation

The user may not be available to watch the laptop.

Continue from one documented step to the next without asking for routine
permission or waiting for "continue".

Do not stop merely because:
- one digit is finished;
- an audit generated a report;
- a local objective defect needs repair;
- another checkpoint is appropriate;
- a technically failed local attempt can be safely revised.

When a digit gate fails:
1. read the report;
2. keep the edit local to that digit;
3. repair/retry;
4. do not propagate a failing approach.

When a digit gate passes:
1. checkpoint;
2. continue to the next documented digit.

If Stage A passes:
- checkpoint;
- proceed to Stage B.

If the final V15f pipeline produces an obviously failed candidate:
- preserve it;
- do not promote it;
- write the state to the repo;
- continue any safe non-destructive work that does not cross an acceptance gate.

Do not automatically:
- promote geometry;
- start grip refit before hand acceptance;
- merge the source branch;
- change production references;
- loosen thresholds;
- delete previous attempts.

## Only stop for the user when necessary

Stop only when:
- ChatGPT/OS requires a confirmation only the user can provide;
- credentials/access are missing;
- local execution is unavailable;
- usage is exhausted;
- continuing would violate a frozen rule;
- the only remaining dependency is a genuinely subjective final visual
  acceptance;
- no other safe independent work remains.

If forced to stop, update a repo handoff with:
- branch and HEAD;
- current V15f checkpoint;
- last digit completed;
- last audit result;
- generated reports;
- exact next command.

## Usage priority

Spend Work/Blender usage on:
- direct topology inspection;
- local mesh reconstruction;
- unavoidable visual judgement.

Use the prepared scripts for:
- selection/hotspots;
- invariants;
- fold/sharpness gates;
- export;
- frozen validation;
- latest-source integration;
- review boards/reports.

Do not spend a new Work session recreating tooling that already exists.


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


## V15f-specific recovery

For ring/pinky proof, scope, sharpness or severe-fold failures, read:

`V15F_FAILURE_RECOVERY.md`

Use the older `V15_FAILURE_RECOVERY.md` for export/frozen/current-source pipeline failures.


## Automatic interruption handoff

The ring-left proof, per-digit gates and Stage-A gate automatically refresh:

`V15F_LATEST_HANDOFF.md`

It records:
- branch/HEAD;
- candidate/checkpoint state;
- which incremental gates pass/fail;
- latest Blender invariant/fold state;
- per-digit original movement;
- Stage-A failures;
- next action from `V15F_STATUS.bat`.

If a later Work session is interrupted, read this file before reconstructing
state manually.

You can refresh it at any time with:

`WRITE_V15F_HANDOFF.bat`


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
