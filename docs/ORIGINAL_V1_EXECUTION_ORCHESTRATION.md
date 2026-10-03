# ORIGINAL v1 execution orchestration

This is the post-preparation execution map. It is **not Roadmap Phase 13** and it
does not add a new production phase.

Repository-side Stages 1–12 are now prepared. The purpose of this orchestration
layer is to stop Claude/GPT from having to reconstruct how those tools fit together
during laptop sessions.

Authoritative machine map:

`ORIGINAL_V1_EXECUTION_ORCHESTRATION.json`

Read-only selector/validator:

`scripts/original_v1_execution_orchestration.py`

Laptop wrapper:

```bat
RUN_ORIGINAL_V1_EXECUTION_PLAN.bat
```

Optional fresh JSON guidance output:

```bat
RUN_ORIGINAL_V1_EXECUTION_PLAN.bat ORIGINAL_V1_WORK\execution\current_plan.json
```

## What it does

The runner:

1. executes the normal model-session preflight;
2. verifies generated daily status is current;
3. checks that all Stage 1–12 prepared support artifacts still exist;
4. validates the declared critical-path graph;
5. reads the actual current candidate/phase/subphase/evidence-derived next action;
6. selects exactly one current execution node;
7. lists the prepared support stages relevant to that node;
8. lists safe parallel work, where explicitly declared;
9. prints guidance only.

It does **not**:

- launch Blender;
- run an optimiser;
- create a candidate;
- choose a subjective repair;
- record a phase COMPLETE;
- accept a review;
- alter R2;
- change the rig;
- change thresholds;
- promote a model;
- edit the runtime branch.

## Current expected node

The runner always re-reads generated state; this prose is only a checkpoint.
At the 2026-10-03 reconciled state the selected node is:

- node: `3A_axilla_local`;
- candidate: `r55`;
- phase/subphase: Phase 3 / pre-Phase-4 residual repair;
- next action: `RUN local axilla repair`;
- command: `RUN_ORIGINAL_V1_AXILLA_PIT_PIPELINE.bat r55 r56`.

Use the next collision-free target label if `r56` already exists locally. If the
selector has advanced, follow the generated state instead of this example.

## Critical path

The machine map retains the full historical execution graph so older evidence and
recovery remain explainable, but the current selector may enter the graph at the
node appropriate to live state. At the 2026-10-03 checkpoint it enters at
`3A_axilla_local`, after the earlier 3B/3C/3D/3E work has already been completed.

From the current node the forward path is:

1. residual local axilla repair and evidence reconciliation;
2. Phase 4 development freeze;
3. Phase 5 high-detail anatomy;
4. Phase 6 topology/surface;
5. Phase 7 first-party clothing;
6. Phase 8 materials/presentation;
7. Phase 9 production deformation;
8. Phase 10 real runtime integration;
9. Phase 11 automated visual QA;
10. Phase 12 final freeze eligibility;
11. separate owner-authorised controlled release.

Historical nodes such as `3B_r30` remain in the machine graph; their presence is
not permission to rerun them when live state has moved on. The production roadmap
still ends at Phase 12.

## Prepared support mapping

The orchestration file explicitly maps the earlier GPT preparation stages onto
the roadmap point where they become useful.

Examples:

- Phase 3C/3D/3E uses the source-bound diagnostic brief and local repair policy;
- Phase 6 uses the snapshot/surface-audit tooling;
- Phase 7 uses raw garment, static dressed and continuous dressed evidence;
- Phase 9 uses export, dressed-range and contact-source bridge tooling;
- Phase 10 uses runtime discovery and the real-engine evidence harness contract;
- Phase 11 uses deterministic first-party visual QA;
- Phase 12 uses the technical promotion and final-freeze verifier.

A prepared support stage never changes the entry/exit conditions of its roadmap
phase.

## Safe parallel work

The orchestration plan names only tasks that can proceed without obscuring the
critical path.

For the current local-axilla node, examples include:

- full milestone capture/publication for a verified candidate;
- read-only diagnostics;
- status/handoff regeneration.

Those do not allow an unresolved local repair or incomplete Phase 3 to be bypassed.

Owner review snapshots remain non-blocking by default. An owner rejection,
protected frozen-structure change or contradictory lineage evidence still blocks
the affected work exactly as defined by the master plan.

## Transition rules

After each meaningful execution:

1. preserve the candidate/evidence already created;
2. re-read remote HEAD before writing;
3. commit/push actual evidence and handoff updates;
4. regenerate status/dashboard;
5. re-run `RUN_ORIGINAL_V1_EXECUTION_PLAN.bat`;
6. follow the newly selected node only after its entry conditions are true.

Never manually advance the orchestration plan merely because a run finished. Phase
state and exit evidence control progression.

## Runtime boundary

The model orchestration map references the runtime discovery package but does not
make this branch a runtime integration target.

Phase 10 still requires:

- separate authoritative runtime checkout;
- exact live runtime HEAD;
- exact-SHA green standalone/browser gates;
- Phase 9 final model/asset evidence;
- real solver/contact/export execution.

No wholesale branch merge is permitted.

## Final release boundary

The final node is not "production approved". Phase 12 tooling can only establish:

`ALL_FREEZE_PREREQUISITES_SATISFIED`

with `production_approved=false`.

The production activation itself remains a separate, explicit, owner-authorised
runtime-side release followed by exact-SHA release verification.

## Current action

This orchestration package does not supersede live production control. At the
2026-10-03 checkpoint the expected actual model action is:

```bat
RUN_ORIGINAL_V1_AXILLA_PIT_PIPELINE.bat r55 r56
```

subject to live preflight/selector agreement and a collision-free target label.
A completed pipeline still produces an EXPERIMENTAL candidate plus evidence; it
does not automatically enter Phase 4.

## Phase 5 execution gap closure

When the orchestrator eventually selects `5_anatomy`, use the prepared regional
contract in `PHASE_5_ANATOMY_EXECUTION_PROTOCOL.md`. It converts the existing
5A-5G briefs into candidate-bound templates/receipts and forces each region to
inherit from the previous verified regional candidate. This reduces future Claude session setup but does not alter the current local-axilla node or Phase 4 entry requirements.


## Session-close gate

At the end of each laptop session run `RUN_ORIGINAL_V1_SESSION_CLOSE.bat` after
the intended save/evidence/handoff/commit/push steps. The read-only checker reports
`READY_TO_END_SESSION`, `PARTIAL_WORK_PRESERVED`, or exact blockers/actions. This
prevents a future Claude pickup from discovering unpushed commits, stale status,
an undocumented partial candidate or a local Blend/manifest identity mismatch.


## Session close

At the end of every laptop execution session, use
`RUN_ORIGINAL_V1_SESSION_CLOSE.bat` after saving/evidence/handoff/commit/push.
It confirms the handoff is unambiguous or that partial work is explicitly
preserved. It is read-only and does not make pending routine owner review a
session-close blocker.


## Concise progress view

For phone/status checks, `RUN_ORIGINAL_V1_PROGRESS.bat` prints a compact projection
of the same evidence-derived state. It separates actual roadmap completion from
prepared infrastructure and does not estimate a synthetic percentage.


## Laptop acceleration layer

`work_packages/LAPTOP_ACCELERATION_PROTOCOL.md` consolidates the read-only start,
candidate closure/review/handoff, local Blend inventory/recovery and end-session
commands. The preferred start is `RUN_ORIGINAL_V1_CLAUDE_START.bat`; the preferred
end summary is `RUN_ORIGINAL_V1_CLAUDE_END.bat [rN]`. Local recovery backup is
optional and requires a fresh destination outside the repository. These commands
reduce context/evidence overhead only; they do not launch or approve Blender work.
