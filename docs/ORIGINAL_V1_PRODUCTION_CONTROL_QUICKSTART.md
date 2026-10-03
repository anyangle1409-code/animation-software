# ORIGINAL v1 shared GPT / Claude pickup

Work only on `claude/original-v1-blender-o2-20260929`. Before edits read LIVE branch
HEAD and preserve newer commits. This page is execution navigation; the master
plan is the authoritative roadmap and O4 handoff supplies the repair evidence.

Read in order:
1. `docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md`
2. `ORIGINAL_V1_HIGH_DETAIL_STATUS.json` / `docs/ORIGINAL_V1_DAILY_STATUS.md`
3. `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`
4. The work package selected by `scripts/select_original_v1_next_action.py`.

## Current exact laptop sequence

Always re-read live HEAD first. Then:

```bat
RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
RUN_ORIGINAL_V1_NEXT.bat
RUN_ORIGINAL_V1_EXECUTION_PLAN.bat
RUN_ORIGINAL_V1_AXILLA_PIT_PIPELINE.bat r55 r56
```

Use the next collision-free target revision if `r56` already exists locally.
Preflight/NEXT/orchestration are read-only; they must agree that the active action
is `RUN local axilla repair` before executing the pipeline. If generated status
has advanced, follow it instead of this embedded example.

The pipeline is fail-closed and preserves every completed child stage. It performs
the pre-edit pit declaration, one-dump numeric trial sweep, incremental apply and
full candidate validation/review. It never accepts the candidate, enters Phase 4,
changes a baseline or marks production approved.

After the local pipeline completes:

- inspect the new candidate's full comparison versus its active epoch baseline
  (currently P3B1) and versus r55;
- inspect the declared-face post-edit arc audit and real review renders;
- preserve a trade-off/rejected result rather than overwriting it;
- regenerate status/dashboard/ledger and record any evidence-backed continuation
  decision against the exact candidate SHA. Use the read-only verifier rather than
  hand-editing the decision blindly:
  `python scripts/verify_original_v1_continuation_decision.py --template --revision <candidate-rN> --parent r55 --disposition ORIGINAL_V1_WORK/candidates/repair_checks/axilla_<candidate-rN>/post_validation_disposition.json --json-out <fresh-decision-template.json>`;
  after real-render review, fill only the explicit visual disposition/reason/time fields
  and verify it with
  `python scripts/verify_original_v1_continuation_decision.py <decision.json> --json-out <fresh-receipt.json>`.
  A verified receipt only produces a proposed production-control fragment; it does not
  edit shared state, authorize Phase 4, promote a baseline or approve production;
- rerun NEXT/orchestration;
- only when production control selects `ENTER development freeze validation`,
  run `RUN_ORIGINAL_V1_PHASE4_PREFLIGHT.bat` and the Phase 4 work package.

The locked rig is rev2c / `rev2_forearm_twist_only`: 67 bones total, 66 deform,
with the historical 63-bone v4 structure plus four forearm-twist helpers. Do not
reopen that rig, P3 pose construction, thresholds or epoch baselines merely to
clear the remaining axilla defect.

## State and historical evidence

Production control recomputes full required coverage, grip and comparator results,
checks frozen input hashes, retains rejected candidates and refuses contradictory
or newer incomplete state. Foundation phases derive from the existing verified
R2/export status gates. Its 54/133 failures describe R2, not the 7-failure r29 state.
Earlier r20 has historical 14-pose coverage; it remains in the ledger but cannot
be selected as the latest complete 15-pose state. Intermediate r29a has geometry
metadata, not a completed full-evidence candidate. Missing metrics are null.

A future phase exit record is keyed by phase in phase_completion_records and
contains candidate_sha256 plus an evidence path/SHA reference. The exit report
must say PASS for that same candidate and document the master plan's exit checks.
Records are never inferred from a candidate's name or optimisation score. Phase 4
requires zero failures and resolved strict regressions. Phase 12 is deliberately
reserved for the separate final promotion workflow, never this generator.

## Known validation boundaries

The cloud prepares/tests Python tooling and checks committed reports/GLBs. It
cannot validate the local Windows battery/process APIs, render Blender candidates,
inspect unavailable local .blend files, or run real animation integration here.
Blender-facing additions are capture/source metadata and read-only snapshot tools;
no rest pose, stress pose, candidate geometry/weights or threshold is changed.

Full milestone rear/anatomy views remain a later capture requirement; the existing
17-view repair set is a compact snapshot only. Earlier renders without capture
manifests remain historical; regenerate verified evidence into a fresh label rather
than relabelling them. The project requires zero third-party shipped runtime/assets;
existing stock Blender/Python authoring tools are development tools, not content.

## Full-evidence collection and interruption safety

The full runner uses report-only comparison mode while collecting each group.
A measured REGRESSION remains in the comparison JSON and blocks strict improvement;
it does not masquerade as a Blender/process failure. Direct targeted repair runs
retain strict comparator exit codes. The merger requires all six groups, including
neutral, with identical candidate and render-script identities and identical
metrics for overlapping poses. It records a source-bound evidence manifest and
stops on evaluator/queue/comparator execution errors. Existing outputs are protected.

If an interrupted run leaves a new candidate manifest without complete evidence,
status remains STOP across repeated ledger/dashboard generation. Preserve the local
blend, solution and partial evidence. Do not rerun the solver simply to clear an
output collision. A valid existing candidate can receive the missing evidence in
fresh group folders after its identity and inputs are verified. Never mix group
reports from different script versions or candidates.

2026-10-01 follow-up validation: 72 Python tests pass, including real subprocess
fixture runs proving a valid seven-failure / six-regression result remains recorded,
invalid metrics stop processing, and partial-candidate state remains deterministic.
Windows batch execution and actual Blender renders still require the laptop.

## Historical r29/r30 recovery reference

The material below documents earlier r29/r30 interruption/recovery and repository
preparation. It remains useful for understanding evidence lineage, but its embedded
`r29`, `r30`, `RUN_ORIGINAL_V1_R30.bat` and R2-only “current task” wording is
**historical**. It must never supersede live generated status, production control,
the orchestration selector or the current O4 handoff.

### Inspect an already-created candidate after an interruption

```bat
python scripts/inspect_original_v1_interrupted_run.py r30
```

This read-only utility verifies candidate bytes, parent manifest, solution bytes,
existing group sources, current render-script identity and complete pose membership.
It prints existing runner commands only for missing groups; it never reruns o22,
deletes files, changes status or claims SAFE TO START. Recheck live branch and
laptop environment first. Set BLENDER_EXE to the verified executable for neutral
capture. Reinspect after collecting missing groups. Once all groups verify, it
prints the full merger command. An unfinished group or existing full output stops
recovery instructions and preserves evidence for reconciliation.

After a verified fresh merge, complete the existing r30 runner steps 5–8: explicit
r28 comparison with --report-only; trial summary against r29 and r28; generated
candidate review; compact real-image collection; daily status generation. These
steps must use fresh output paths. Publish evidence and record non-blocking pending
owner review. Resume from the next-action selector, never from an optimiser score.

## Required evidence publishing from r30 onward

A full new candidate must include `full_<revision>_evidence_manifest.json` generated
by the full merger. Commit its six group `pose_test_report.json` files and six
`render_source_manifest.json` files, alongside the candidate manifest, merged
report and comparisons. Status generation verifies every hash, candidate/script
identity, exact group membership and overlapping pose metrics against the merged
report. A missing source receipt or altered source stops processing. Historical
pre-r30 results remain historical evidence; never fabricate retrospective receipts.

Full-resolution group PNGs may remain local under the existing storage policy.
The laptop collector verifies PNG bytes and publishes the real compact review set.
Cloud numeric receipt verification does not claim to inspect unavailable images.
Keep owner_review pending and continue safe work.

`.gitattributes` preserves ORIGINAL-v1 evidence/JSON and frozen rig-source bytes
across Git, including when core.autocrlf is true. Do not run `git add --renormalize`
or rewrite existing evidence to satisfy a mismatch. Inspect and preserve the exact
source bytes instead. This protects hashes without changing geometry or gates.

## Optional milestone visibility checkpoint

Use `RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat <verified candidate>` to capture the full
57-view bare model board when laptop power/time allows. This is optional alongside
Phase 3 repair and never blocks the next safe task. Read the visual review spec
for exact capture/publication paths and first-run Blender validation limitations.
For completed source captures, publication-only mode is available without rerender:
`python scripts/original_v1_milestone_review.py <revision>`. Publish actual images
and source JSON, regenerate daily status, record owner_review pending, continue.

## Later phase completion

Read `docs/ORIGINAL_V1_PHASE_EXIT_EVIDENCE.md` before recording Phase 4–11 COMPLETE.
Use INCOMPLETE templates, execute every named domain test, attach exact source
references, verify the actual report, then update phase_completion_records. A bare
PASS object is now refused. Phase 4 has an execution package and a metrics-only
independent replay utility. Neither makes any candidate freeze-eligible by itself; Phase 4 requires the current candidate to satisfy the live zero-blocker/strict-regression and evidence contracts. Review snapshots stay non-blocking.

For future Phase 12 preparation, create an INCOMPLETE packet with
`python scripts/verify_original_v1_production_promotion.py --template --json-out <fresh packet.json>`.
Read the promotion workflow before filling it: all gates and final owner acceptance
must identify the exact two bare/dressed exports. Templates never count as evidence
and the verifier never changes production approval.

## Phase 3 probe interpretation prepared for Claude

The existing remaining-diagnostics runner now also writes `diagnostic_brief.json`
and `diagnostic_brief.md` beside the raw probes. Read the brief first. It checks
exact source identities and agreement with the full rounded pose report, lists
pre/post-close grip measurements and local extreme-edge inspection IDs, and links
the repair packages. It neither diagnoses a cause nor authorises edits. Existing
probe files can be summarised without Blender using
`python scripts/build_original_v1_diagnostic_brief.py <latest revision>`; both
brief output paths must be unused. Preserve conflicting/partial evidence on STOP.

Stage 2 adds `python scripts/prepare_original_v1_repair_policy.py <3C|3D|3E>
--out-dir <fresh repository folder>` (one line). The prepared r29 examples live in
`ORIGINAL_V1_WORK/candidates/repair_preparation/r29_3C_stage2/` and corresponding
3D/3E folders. They are INCOMPLETE historical drafts, not permission to bypass the live production-control action. Generate
a new packet only for the actual machine-selected continuation candidate. Read its
README, preserve the original drafts and record a local intent before editing.

Stage 3 prepares Phase 6–11 packages under `docs/work_packages/`, with shared
`LATER_PHASE_EXECUTION_CONTRACT.md` and `LATER_PHASE_TOOLING_READINESS.md`.
Use them when those phases become eligible. Read the missing-tools column before
scheduling Blender work: bare stress renders do not prove dressed or continuous
motion, old export filenames must not overwrite history, and model-branch audits
do not prove a different runtime commit. All six phases remain NOT STARTED.

Stage 4 prepares `scripts/audit_original_v1_surface.py` for the raw schema-2
snapshot. Follow `docs/work_packages/SURFACE_AUDIT_PROTOCOL.md`; supply the exact
candidate manifest and fresh JSON/Markdown outputs. It lists surface defects and
coverage as EVIDENCE_ONLY. No candidate report or Phase 6 completion is claimed
until real snapshots and the remaining domain checks exist.

Optional source-bound candidate export evidence: follow
`work_packages/CANDIDATE_EXPORT_PROTOCOL.md` and
`RUN_ORIGINAL_V1_CANDIDATE_EXPORT.bat`. This does not supersede the live production-control/orchestration action or
validate production/runtime motion. Actual laptop capture remains required.

Raw garment/body snapshot evidence is prepared in
`work_packages/GARMENT_RAW_EVIDENCE_PROTOCOL.md`. Existing snapshot command defaults
to the body; optional --garment captures the owned shorts. This does not measure
posed clothing clearance or supersede the live production-control next action.


Static evaluated clothing evidence is now prepared in
`work_packages/DRESSED_EVALUATED_EVIDENCE_PROTOCOL.md` and
`RUN_ORIGINAL_V1_DRESSED_EVIDENCE.bat`. It requires a same-candidate Stage 6
raw pair receipt and produces EVIDENCE_ONLY static clearance/intersection metrics
plus matched bare/dressed review pairs. It does not supersede the live production-control/orchestration action, classify
legitimate contact, prove continuous dressed motion or complete Phase 7.


Stage 8 sampled dressed range/contact tooling is prepared in
`work_packages/DRESSED_RANGE_CONTACT_PROTOCOL.md` and
`RUN_ORIGINAL_V1_DRESSED_RANGE.bat`. It requires a same-candidate verified Stage 7
static dressed evidence file. The default contact-classification template leaves
all real findings UNCLASSIFIED and cannot grant a PASS. The sampler deliberately
omits unsupported continuous push-up and moving-equipment paths rather than
inventing them. It does not supersede the live production-control/orchestration action or prove runtime biomechanics.


Stage 9 first-party contact source bridging is prepared in
`work_packages/CONTACT_SOURCE_BRIDGE_PROTOCOL.md` and
`RUN_ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.bat`. It verifies current source semantics
and SHA-256 evidence for push-up floor locks, hand-driven curl dumbbells and the
fixed pull-up rack/socket contact model. It does not run the solver, does not add
Blender poses and does not declare this model branch to be the live runtime. Use
it later as a fail-closed comparison contract when Phase 10 discovers the actual
standalone runtime commit. It does not supersede the live production-control next action.


Stage 10 live-runtime discovery/harness preparation is available through
`work_packages/RUNTIME_DISCOVERY_HARNESS_PROTOCOL.md` and
`RUN_ORIGINAL_V1_RUNTIME_DISCOVERY.bat <separate-runtime-checkout> [fresh-output]`.
It rechecks the active standalone branch/remote HEAD, reruns the Stage 9 contact
semantic contract against that checkout, confirms actual canonical-v4 source state
and records SHA-256 source comparisons without editing the runtime. The prepared
runtime evidence JSON is an INCOMPLETE TEMPLATE only. The current discovered
runtime HEAD e3a7d915... is not green because focused skeleton parity fails at a
0.02 m root/root-tail delta; do not use it as integration proof. This does not
supersede the live production-control next action.


Stage 11 deterministic visual QA preparation is available through
`work_packages/VISUAL_QA_PROTOCOL.md` and `RUN_ORIGINAL_V1_VISUAL_QA.bat`.
Actual source images stay immutable; first-party PGM masks provide deterministic
crop/visibility/component/symmetry and matched silhouette measurements. Capture
setting differences are reported as CAPTURE_MISMATCH rather than model regression,
and unsupported checks remain UNKNOWN. The explicit reference inventory is empty
until real project-authored Phase 10-bound captures exist. Synthetic detector
fixtures are never model evidence. This does not supersede the live production-control next action.


Stage 12 final production-freeze preparation is available through
`work_packages/PHASE_12_PRODUCTION_FREEZE.md` and
`RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat`. The technical promotion verifier now
binds its receipt to the exact promotion packet SHA/candidate/runtime. The final
freeze verifier additionally rechecks Phase 4-11 exit reports, exact bare/dressed
assets, Phase 9 model commit, Phase 10/11 runtime commit and a separate explicit
`OWNER AUTHORISED PRODUCTION FREEZE` record. Even successful eligibility keeps
`production_approved=false`; actual release is a separate controlled runtime-side
operation. No current candidate can bypass its required phase prerequisites; this does not supersede the live production-control next action.


## Post-preparation orchestration

Stages 1-12 of GPT repository-side preparation are now mapped by
`ORIGINAL_V1_EXECUTION_ORCHESTRATION.json`. `RUN_ORIGINAL_V1_EXECUTION_PLAN.bat`
is read-only and should be rerun after each meaningful candidate/phase transition.
It validates the prepared support artifacts and prints one current critical-path
node plus relevant support/parallel-safe work. It never launches Blender or
advances a phase. This is execution navigation only; the roadmap still ends at
Phase 12. Current expected model action is determined by live production control; at the 2026-10-03 checkpoint it is the r55 local axilla pipeline.


### Phase 5 anatomy gap-closure tooling

Once Phase 4 is genuinely frozen, use
`docs/work_packages/PHASE_5_ANATOMY_EXECUTION_PROTOCOL.md` and
`RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat`. The machine plan fixes the 5A→5G order,
permitted/protected scope, focused poses, required real views and evidence slots.
5B-5G require a verified predecessor-region receipt whose candidate is the direct
parent. Templates are INCOMPLETE only; actual Blender anatomy and real review
evidence are still required. Current work remains Phase 3 until live production control advances it; at the 2026-10-03 checkpoint this is the r55 local axilla repair.


### Phase 6 advanced surface gap-closure tooling

After Phase 5 is actually complete, follow
`work_packages/PHASE_6_ADVANCED_SURFACE_PROTOCOL.md`. Populate the authored
`ORIGINAL_V1_PHASE6_JOINT_SUPPORT_PLAN.json` for the exact candidate, then use
`RUN_ORIGINAL_V1_PHASE6_SURFACE.bat <rN> <joint-support.json> <fresh-output-dir>`.
It runs raw surface audit, evaluated normal capture, exact BVH self-intersection
capture and joint-support contract verification without saving/repairing Blender.
Phase 4/5 eligibility is derived from the current candidate and live completion records; historical r29 is not an execution target.


### Phase 7 garment scene/provenance gap closure

After Phase 6 is complete, create the actual clean-room garment operation ledger
from `ORIGINAL_V1_PHASE7_GARMENT_AUTHORING_TEMPLATE.json`, then use
`RUN_ORIGINAL_V1_PHASE7_GARMENT_SCENE.bat <rN> <authoring-record.json> <raw-pair.json> <fresh-output-dir>`.
It captures modifier properties, shape keys/drivers, custom-normal state, groups,
attributes, libraries and material/image references and verifies the operation
chain. Dressed motion/contact evidence still comes from the existing Stage 7/8
tools. Current work remains Phase 3 until live production control advances it; at the 2026-10-03 checkpoint this is the r55 local axilla repair.


### Phase 8 material/presentation gap closure

After Phase 7 completes, fill the actual owned numeric material record from
`ORIGINAL_V1_PHASE8_MATERIAL_PROVENANCE_TEMPLATE.json`, then run
`RUN_ORIGINAL_V1_PHASE8_PRESENTATION.bat <rN> <material-provenance.json> <fresh-output-dir>`.
Use `ORIGINAL_V1_PHASE8_PRESENTATION_CAPTURE_PLAN.json` for the required real
bare/dressed app-distance and close-up review renders. Image textures/HDRIs and
linked material resources are rejected by the prepared verifier. Readability is
still a real review, not an automated PASS. Current work remains Phase 3 until live production control advances it; at the 2026-10-03 checkpoint this is the r55 local axilla repair.


### First-party visual-QA mask capture

`work_packages/VISUAL_QA_MASK_CAPTURE_PROTOCOL.md` documents the project-owned
z-buffer PGM mask path. Future Blender capture scripts can generate source-bound
subject/body/garment/hand/foot/equipment masks immediately after a real render,
without third-party image libraries or an external vision model. Final Phase 11
runtime masks must still be emitted/bound by the exact Phase 10 runtime frame.


### End every laptop session deterministically

After saving the numbered Blend, generating available evidence, updating the O4
handoff/status, committing and pushing, run `RUN_ORIGINAL_V1_SESSION_CLOSE.bat`.
Read `work_packages/SESSION_CLOSE_PROTOCOL.md`. `READY_TO_END_SESSION` means the
branch is clean/synced and handoff/status are current. `PARTIAL_WORK_PRESERVED`
means an incomplete candidate is explicitly recorded with a matching local Blend
and manifest. Any other result prints exact closing actions. The checker never
commits, pushes, fetches, deletes or saves Blender files.


### End-of-session handoff safety

Before ending a Claude/Blender laptop session, run
`RUN_ORIGINAL_V1_SESSION_CLOSE.bat`. It verifies local/remote branch state,
working-tree cleanliness, generated status, O4 handoff coverage and incomplete
candidate/Blend identity. It reports `READY_TO_END_SESSION`,
`PARTIAL_WORK_PRESERVED` or `NEEDS_ATTENTION_BEFORE_ENDING`. It never commits,
pushes, fetches, deletes or saves Blender files. See
`work_packages/SESSION_CLOSE_PROTOCOL.md`.


### Phone-friendly progress summary

Run `RUN_ORIGINAL_V1_PROGRESS.bat` for a concise read-only status derived from the
same production-control state and execution-orchestration map. It shows current
candidate/phase, blocker counts, exact next action, next major milestone, completed
and remaining roadmap phases, Phase 3/5 subphase states and the 12/12 prepared
support-tooling count. It deliberately does not invent a model-completion
percentage because roadmap phases have unequal real Blender workload.


### Claude laptop acceleration

Use `RUN_ORIGINAL_V1_CLAUDE_START.bat` at the start of a laptop session. It runs
preflight, next-action selection, execution-plan validation and prints the compact
live Claude brief without launching Blender. For completed candidates use
`RUN_ORIGINAL_V1_CANDIDATE_CLOSE.bat <rN>`, `RUN_ORIGINAL_V1_REVIEW_PACKAGE.bat <rN>`
and/or `RUN_ORIGINAL_V1_CANDIDATE_HANDOFF.bat <rN>`. Check laptop-only Blend
identity with `RUN_ORIGINAL_V1_BLEND_INVENTORY.bat`; an optional local recovery
copy can be made with `RUN_ORIGINAL_V1_LOCAL_BACKUP.bat <fresh-directory-outside-repo>`.
End with `RUN_ORIGINAL_V1_CLAUDE_END.bat [rN]`. Full rules are in
`work_packages/LAPTOP_ACCELERATION_PROTOCOL.md`. None of these wrappers advances a
roadmap phase or infers acceptance.


### Phase 7 bare/dressed equivalence

After the actual Phase 7 garment exists, run
`RUN_ORIGINAL_V1_PHASE7_EQUIVALENCE.bat <rN> <fresh-output-dir>`. It reuses all
15 frozen stress poses and requires the full underlying body/rig/body metrics to
remain identical when only garment visibility changes. The body dressed-mask is
inactive in both comparison states. This is evidence-only and does not classify
garment contact or complete Phase 7.


### Blender smoke gate

`RUN_ORIGINAL_V1_CLAUDE_START.bat` now includes `RUN_ORIGINAL_V1_BLENDER_SMOKE.bat`.
It opens the current complete candidate read-only in background Blender and checks
candidate identity, the canonical 63-bone v4 rig/body, evaluated mesh APIs and
linked-library state before Claude starts the selected modelling command. It never
saves the Blend.
