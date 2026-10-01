# Phase 6–11 execution contract

PREPARED INSTRUCTIONS ONLY. All six phases remain NOT STARTED. Read the master
roadmap, generated status, O4 handoff and the specific package before execution.
This contract applies to all six packages; it does not change frozen gates.

## Entry, lineage and edit boundaries

Check LIVE model-branch HEAD and preserve newer work. Require the preceding
phase's actual exit evidence, a sufficiently stable development freeze and the
machine-selected continuation candidate. Verify the local Blend against its
manifest. r29's seven blockers prevent entering these phases now. Do not work
from main or transfer model-branch application code to the standalone branch.

Use a NEW candidate for each model change. Record parent SHA, explicit local
scope, independently authored operations and permitted IDs/regions/bones before
editing. Export raw schema-2 snapshots and audit changes through the existing
change-audit protocol. Topology/order changes require authored correspondence;
equal counts never prove index identity. No remote edits, legacy/third-party
content, frozen rig rest/hierarchy, R2, pose/frame or threshold changes.

Compare R2, direct parent and the immutable development-freeze candidate.
Retain r28/r29 controls for hand/contact changes. Report individual regressions;
STRICT IMPROVEMENT cannot hide a TRADE-OFF behind total scores. Reject invalid
lineage, protected edits, new blockers or unexplained material regressions.
Preserve rejected candidates, raw reports and images in the ledger/history.

## Available common commands

Replace placeholders with verified revisions and fresh repository-local paths.
These commands exist; do not add guessed flags. Check output collisions first.

```bat
RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat
python scripts/select_original_v1_next_action.py
python scripts/verify_original_v1_local_candidate.py <candidate.blend> <candidate.json>
blender --background --factory-startup <candidate.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <fresh snapshot.json>
python scripts/audit_original_v1_changes.py <before.json> <after.json> --policy <actual policy.json> --json-out <fresh audit.json>
RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <rN> <direct parent revision>
RUN_ORIGINAL_V1_MILESTONE_REVIEW.bat <rN>
python scripts/build_original_v1_daily_status.py --check
```

FULL_EVIDENCE is the existing 15-pose **bare-body stress** protocol. Its report-only
comparisons preserve regressions but are not acceptance. Milestone capture is
also bare-body. Neither supplies dressed, continuous-motion or real-engine proof.
Read the tooling-readiness table before claiming any later domain check passes.

For an already completed full report, recompute explicit profiles:

```bat
python scripts/evaluate_original_v1_deformation_report.py <full merged report.json> --grip-report <same full merged report.json> --profile development_blocker --require-group core_five --json-out <fresh development core.json>
python scripts/evaluate_original_v1_deformation_report.py <full merged report.json> --grip-report <same full merged report.json> --profile development_blocker --require-group extended --json-out <fresh development extended.json>
python scripts/evaluate_original_v1_deformation_report.py <full merged report.json> --grip-report <same full merged report.json> --profile development_blocker --require-group shoulder_rhythm_diagnostics --json-out <fresh development rhythm.json>
python scripts/evaluate_original_v1_deformation_report.py <full merged report.json> --grip-report <same full merged report.json> --profile production_target --require-group core_five --json-out <fresh production core.json>
python scripts/evaluate_original_v1_deformation_report.py <full merged report.json> --grip-report <same full merged report.json> --profile production_target --require-group extended --json-out <fresh production extended.json>
python scripts/evaluate_original_v1_deformation_report.py <full merged report.json> --grip-report <same full merged report.json> --profile production_target --require-group shoulder_rhythm_diagnostics --json-out <fresh production rhythm.json>
```

Verify the committed acceptance specification's required groups before execution.
The full source receipt/status check also requires the neutral control, completing
15-pose coverage. The evaluator accepts one required group per invocation; use all
three named groups, not a nonexistent combined-group alias.
Do not omit grip reports or required poses to obtain a pass. Phase packages may
require more coverage than these static stress poses; record missing coverage.
Evaluator exit 1 is a measured profile failure, exit 2 is invalid input/tool error.
Preserve failed reports and collect all required groups; never treat exit 1 as PASS
or use report-only to bypass the phase gate. Invalid input must be reconciled.

## Review, completion and publication

Produce actual neutral/anatomy/exercise images with exact candidate/source hashes
and matched camera, scale, lighting, pose and crop. Preserve mismatches explicitly.
REVIEW SNAPSHOTS ARE NON-BLOCKING BY DEFAULT. Publish images and their manifests,
mark owner_review pending, continue safe reversible work or independent tooling.
Owner acceptance is separate and mandatory for final Phase 12 promotion.

For Phase N create an INCOMPLETE template, execute every package/domain test and
then write a separate actual report with all required checks and exact references:

```bat
python scripts/verify_original_v1_phase_exit.py --phase <N> --template --json-out <fresh template.json>
python scripts/verify_original_v1_phase_exit.py <actual exit.json> --phase <N> --json-out <fresh receipt.json>
```

The verifier checks contracts/hashes/dependencies, not domain truth. Missing tools
or source evidence leave the check UNKNOWN/INCOMPLETE, never PASS. Register only
verified, genuinely executed reports in phase_completion_records. Archive stale
entries under phase_completion_history before revalidation on a new candidate;
preserve original freeze pins and reports, never relabel them. Follow
`docs/ORIGINAL_V1_PHASE_EXIT_EVIDENCE.md` for that procedure.

Commit/push manifests, operation records, masks/correspondence, raw audits,
complete source receipts, comparisons, actual review images, exit reports and
updated shared handoff/state/ledger/dashboard. Keep Blend binaries local under
the existing storage policy. Recheck LIVE HEAD before pushing. No package or
script may set production_approved; Phase 12 remains a separate workflow.
