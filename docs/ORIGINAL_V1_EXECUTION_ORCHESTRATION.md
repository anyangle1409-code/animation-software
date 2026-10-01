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

At preparation time the expected state is:

- candidate: r29;
- phase/subphase: 3 / 3B;
- next action: `RUN r30`;
- command: `RUN_ORIGINAL_V1_R30.bat`.

The runner does not trust this prose. It re-reads generated state. If the existing
next-action selector no longer agrees with the r30 orchestration entry, it stops
rather than launching or recommending stale work.

## Critical path

The machine map carries the execution dependency chain:

1. 3B r30 hand/finger recovery;
2. 3C grip/thumb;
3. 3D wrist/push-up;
4. 3E lunge/hip;
5. Phase 4 development freeze;
6. Phase 5 high-detail anatomy;
7. Phase 6 topology/surface;
8. Phase 7 first-party clothing;
9. Phase 8 materials/presentation;
10. Phase 9 production deformation;
11. Phase 10 real runtime integration;
12. Phase 11 automated visual QA;
13. Phase 12 final freeze eligibility;
14. separate owner-authorised controlled release.

That list is an execution path, not a new numbering scheme. The production roadmap
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

For the current r30 node, examples include:

- full milestone capture/publication for a verified candidate;
- read-only diagnostics;
- status/handoff regeneration.

Those do not allow a failed r30 or incomplete Phase 3 to be bypassed.

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

## Current action remains unchanged

This orchestration package does not supersede or delay current Blender work.

The expected actual next model action remains:

```bat
RUN_ORIGINAL_V1_R30.bat
```

subject to live preflight and selector agreement.


## Phase 5 execution gap closure

When the orchestrator eventually selects `5_anatomy`, use the prepared regional
contract in `PHASE_5_ANATOMY_EXECUTION_PROTOCOL.md`. It converts the existing
5A-5G briefs into candidate-bound templates/receipts and forces each region to
inherit from the previous verified regional candidate. This reduces future Claude
session setup but does not alter the current r30 node.


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
