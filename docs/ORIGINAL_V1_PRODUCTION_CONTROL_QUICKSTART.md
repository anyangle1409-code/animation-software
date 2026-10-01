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

```bat
RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
RUN_ORIGINAL_V1_NEXT.bat
RUN_ORIGINAL_V1_EXECUTION_PLAN.bat
RUN_ORIGINAL_V1_R30.bat
```

Preflight/NEXT are read-only and print the task; NEXT does not silently launch
Blender. Run r30 only if preflight says SAFE TO START and selector says RUN r30.
If files already exist, inspect partial/new work; never delete it to obtain green.
Connect AC for the long solve/evidence run. Battery/runtime information may be
unknown; preflight never invents availability or completion time.

After r30 completes:
- Read full_r30 trial summary and R2/r29/r28 comparisons; trade-off is experimental.
- Run `RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat r30` read-only if r30 is the
  verified diagnostic candidate. If rejected, diagnose the previous valid candidate.
- Collect real review images using source manifests. Record owner_review pending;
  publish and continue safe work. Do not wait for routine visual approval.
- Commit/push candidate manifests, reports, comparison/solution evidence and
  review folders. Re-read live branch before publishing; no force push.
- Run `python scripts/build_original_v1_daily_status.py`, then `--check`.
  Update O4 handoff and the ledger/dashboard in the same checkpoint.
- Record chosen experimental continuation under
  `ORIGINAL_V1_PRODUCTION_CONTROL.json:continuation_decisions`, keyed by revision
  with candidate_sha256, reason, comparison evidence references and chosen parent.
  This records worker execution lineage, not owner acceptance or baseline promotion.
- Run selector again: wrist → grip/thumb → lunge. If frozen rig/pose change is
  needed, record the defect and continue independent safe diagnostics/doc tasks.

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
independent replay utility. Neither makes r29 freeze-eligible; its current seven
blockers and strict regressions remain visible. Review snapshots stay non-blocking.

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
3D/3E folders. They are INCOMPLETE drafts, not permission to bypass r30. Generate
a new packet for the actual continuation candidate after hand recovery. Read its
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
`RUN_ORIGINAL_V1_CANDIDATE_EXPORT.bat`. This does not supersede RUN r30 or
validate production/runtime motion. Actual laptop capture remains required.

Raw garment/body snapshot evidence is prepared in
`work_packages/GARMENT_RAW_EVIDENCE_PROTOCOL.md`. Existing snapshot command defaults
to the body; optional --garment captures the owned shorts. This does not measure
posed clothing clearance or supersede RUN r30.


Static evaluated clothing evidence is now prepared in
`work_packages/DRESSED_EVALUATED_EVIDENCE_PROTOCOL.md` and
`RUN_ORIGINAL_V1_DRESSED_EVIDENCE.bat`. It requires a same-candidate Stage 6
raw pair receipt and produces EVIDENCE_ONLY static clearance/intersection metrics
plus matched bare/dressed review pairs. It does not supersede RUN r30, classify
legitimate contact, prove continuous dressed motion or complete Phase 7.


Stage 8 sampled dressed range/contact tooling is prepared in
`work_packages/DRESSED_RANGE_CONTACT_PROTOCOL.md` and
`RUN_ORIGINAL_V1_DRESSED_RANGE.bat`. It requires a same-candidate verified Stage 7
static dressed evidence file. The default contact-classification template leaves
all real findings UNCLASSIFIED and cannot grant a PASS. The sampler deliberately
omits unsupported continuous push-up and moving-equipment paths rather than
inventing them. It does not supersede RUN r30 or prove runtime biomechanics.


Stage 9 first-party contact source bridging is prepared in
`work_packages/CONTACT_SOURCE_BRIDGE_PROTOCOL.md` and
`RUN_ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.bat`. It verifies current source semantics
and SHA-256 evidence for push-up floor locks, hand-driven curl dumbbells and the
fixed pull-up rack/socket contact model. It does not run the solver, does not add
Blender poses and does not declare this model branch to be the live runtime. Use
it later as a fail-closed comparison contract when Phase 10 discovers the actual
standalone runtime commit. It does not supersede RUN r30.


Stage 10 live-runtime discovery/harness preparation is available through
`work_packages/RUNTIME_DISCOVERY_HARNESS_PROTOCOL.md` and
`RUN_ORIGINAL_V1_RUNTIME_DISCOVERY.bat <separate-runtime-checkout> [fresh-output]`.
It rechecks the active standalone branch/remote HEAD, reruns the Stage 9 contact
semantic contract against that checkout, confirms actual canonical-v4 source state
and records SHA-256 source comparisons without editing the runtime. The prepared
runtime evidence JSON is an INCOMPLETE TEMPLATE only. The current discovered
runtime HEAD e3a7d915... is not green because focused skeleton parity fails at a
0.02 m root/root-tail delta; do not use it as integration proof. This does not
supersede RUN r30.


Stage 11 deterministic visual QA preparation is available through
`work_packages/VISUAL_QA_PROTOCOL.md` and `RUN_ORIGINAL_V1_VISUAL_QA.bat`.
Actual source images stay immutable; first-party PGM masks provide deterministic
crop/visibility/component/symmetry and matched silhouette measurements. Capture
setting differences are reported as CAPTURE_MISMATCH rather than model regression,
and unsupported checks remain UNKNOWN. The explicit reference inventory is empty
until real project-authored Phase 10-bound captures exist. Synthetic detector
fixtures are never model evidence. This does not supersede RUN r30.


Stage 12 final production-freeze preparation is available through
`work_packages/PHASE_12_PRODUCTION_FREEZE.md` and
`RUN_ORIGINAL_V1_FINAL_FREEZE_CHECK.bat`. The technical promotion verifier now
binds its receipt to the exact promotion packet SHA/candidate/runtime. The final
freeze verifier additionally rechecks Phase 4-11 exit reports, exact bare/dressed
assets, Phase 9 model commit, Phase 10/11 runtime commit and a separate explicit
`OWNER AUTHORISED PRODUCTION FREEZE` record. Even successful eligibility keeps
`production_approved=false`; actual release is a separate controlled runtime-side
operation. Current r29 cannot pass and this does not supersede RUN r30.


## Post-preparation orchestration

Stages 1-12 of GPT repository-side preparation are now mapped by
`ORIGINAL_V1_EXECUTION_ORCHESTRATION.json`. `RUN_ORIGINAL_V1_EXECUTION_PLAN.bat`
is read-only and should be rerun after each meaningful candidate/phase transition.
It validates the prepared support artifacts and prints one current critical-path
node plus relevant support/parallel-safe work. It never launches Blender or
advances a phase. This is execution navigation only; the roadmap still ends at
Phase 12. Current expected model action remains RUN r30.


### Phase 5 anatomy gap-closure tooling

Once Phase 4 is genuinely frozen, use
`docs/work_packages/PHASE_5_ANATOMY_EXECUTION_PROTOCOL.md` and
`RUN_ORIGINAL_V1_PHASE5_ANATOMY.bat`. The machine plan fixes the 5A→5G order,
permitted/protected scope, focused poses, required real views and evidence slots.
5B-5G require a verified predecessor-region receipt whose candidate is the direct
parent. Templates are INCOMPLETE only; actual Blender anatomy and real review
evidence are still required. Current work remains Phase 3/r30.


### Phase 6 advanced surface gap-closure tooling

After Phase 5 is actually complete, follow
`work_packages/PHASE_6_ADVANCED_SURFACE_PROTOCOL.md`. Populate the authored
`ORIGINAL_V1_PHASE6_JOINT_SUPPORT_PLAN.json` for the exact candidate, then use
`RUN_ORIGINAL_V1_PHASE6_SURFACE.bat <rN> <joint-support.json> <fresh-output-dir>`.
It runs raw surface audit, evaluated normal capture, exact BVH self-intersection
capture and joint-support contract verification without saving/repairing Blender.
Current r29/Phase 3 is not eligible.


### Phase 7 garment scene/provenance gap closure

After Phase 6 is complete, create the actual clean-room garment operation ledger
from `ORIGINAL_V1_PHASE7_GARMENT_AUTHORING_TEMPLATE.json`, then use
`RUN_ORIGINAL_V1_PHASE7_GARMENT_SCENE.bat <rN> <authoring-record.json> <raw-pair.json> <fresh-output-dir>`.
It captures modifier properties, shape keys/drivers, custom-normal state, groups,
attributes, libraries and material/image references and verifies the operation
chain. Dressed motion/contact evidence still comes from the existing Stage 7/8
tools. Current work remains Phase 3/r30.


### Phase 8 material/presentation gap closure

After Phase 7 completes, fill the actual owned numeric material record from
`ORIGINAL_V1_PHASE8_MATERIAL_PROVENANCE_TEMPLATE.json`, then run
`RUN_ORIGINAL_V1_PHASE8_PRESENTATION.bat <rN> <material-provenance.json> <fresh-output-dir>`.
Use `ORIGINAL_V1_PHASE8_PRESENTATION_CAPTURE_PLAN.json` for the required real
bare/dressed app-distance and close-up review renders. Image textures/HDRIs and
linked material resources are rejected by the prepared verifier. Readability is
still a real review, not an automated PASS. Current work remains Phase 3/r30.


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
