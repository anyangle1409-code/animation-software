# PHASE 4 — DEVELOPMENT DEFORMATION FREEZE

PREPARED ONLY. Execute only when evidence-led production control selects
`ENTER development freeze validation` for the machine-selected latest complete
experimental candidate. Never hard-code an old revision or baseline: use the current
candidate and its active stress-pose epoch baseline from generated status. Historical
R2/P2B1/P3B1 pins remain immutable history, but the active comparison baseline is the
one selected for the current candidate. DEVELOPMENT CLEAR is not production approval.

## Entry and permitted scope

Read live branch HEAD, master plan, machine status, daily dashboard and O4 handoff.
First run `RUN_ORIGINAL_V1_PHASE4_PREFLIGHT.bat`; it is read-only and fails closed
unless the current candidate, active epoch baseline, continuation lineage, complete
full-evidence receipt and local candidate bytes all agree. Require zero development
failures, no unresolved strict regressions, all Phase 3
subphases clear, complete predecessor/source evidence and reconciled continuation
lineage. If selector does not say ENTER development freeze validation, continue its
Phase 3 task. Pending routine owner review never blocks safe evidence collection.

This package collects and pins evidence. No geometry, weights, topology, rig/rest
pose, exercise pose, tolerance or R2 modification is permitted. No production
content is copied from V-series or third-party sources. A real frozen-structure
defect requires scoped evidence; continue independent safe work while unresolved.

## Exact execution sequence

Replace `<rN>` with the machine-selected candidate; use fresh output paths.

1. Run `RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat`, then
   `python scripts/select_original_v1_next_action.py`. Check clean/live state and
   local candidate bytes. Connect AC where practical; unknown power is not proof
   of availability. Preserve all existing partial/new work.
2. Read the full development report and every active-epoch-baseline/direct-parent/
   frozen-predecessor comparison. Historical baseline evidence remains preserved; do
   not substitute R2 for the current epoch baseline. Recompute with
   `python scripts/build_original_v1_daily_status.py --check`.
   Zero failures cannot hide individual severity regressions or trade-offs.
3. Repeat all 15 existing poses in a separate Blender invocation:
   `python scripts/verify_original_v1_replay.py <rN> --capture --json-out ORIGINAL_V1_WORK/candidates/repair_checks/development_freeze_<rN>/numeric_replay_verification.json`.
   This reuses the existing pose script in metrics-only mode, emits no preview,
   never saves the Blend and never reruns an optimiser. It refuses source/version,
   coverage or numeric differences. Existing replay folders are preserved.
4. If a completed replay exists and only verification was interrupted, run the same
   command without `--capture`, with a fresh receipt path. Do not relabel the primary
   run as a replay. The matching capture arguments/source hashes are checked.
5. Collect schema-2 raw mesh/weight snapshots and the candidate's real creation
   audits per `docs/ORIGINAL_V1_CHANGE_AUDIT_PROTOCOL.md`. Verify permitted edit IDs,
   parent/child SHA, unchanged rig rest and frames, normalization, influence counts,
   cross-side weights, symmetry and distant changes. Resolve material discrepancies;
   retain all health flags and raw evidence. Do not normalize/rewrite data to clear flags.
6. Publish a real compact repair snapshot or optional full milestone set. Read
   `docs/ORIGINAL_V1_VISUAL_REVIEW_SPEC.md`. Mark owner_review pending/NON-BLOCKING,
   record candidate SHA and source JSON, commit/push imagery and continue.
7. Pin a NEW development-freeze record. Record candidate revision/SHA, exact
   candidate manifest and metrics references, active epoch-baseline identity plus
   historical baseline lineage, frozen rig/gate/pose input hashes, replay and audit
   references, protected scopes and
   permitted next work. This record pins a comparison candidate; it does not replace
   R2 or promote production. Keep every prior freeze/rejection in history.
8. Prepare the phase exit packet:
   `python scripts/verify_original_v1_phase_exit.py --phase 4 --template --json-out ORIGINAL_V1_WORK/candidates/repair_checks/development_freeze_<rN>/phase_4_exit_TEMPLATE.json`.
   The template is INCOMPLETE. After executing the checks, create a separate actual
   exit packet with exact command/commit/time and source references for each check.
   Never turn unexecuted placeholders into PASS assertions.
9. Verify the actual packet:
   `python scripts/verify_original_v1_phase_exit.py <actual packet.json> --phase 4 --json-out <fresh verification receipt.json>`.
   This checks contract/source integrity and existing phase dependencies; it does
   not judge anatomy or replace domain tests. All actual checks must pass.
10. Only then register the candidate-bound actual exit report in
    `ORIGINAL_V1_PRODUCTION_CONTROL.json:phase_completion_records["4"]`, using its
    exact path/hash. Regenerate status/dashboard/ledger; run `--check`. Commit/push
    the complete checkpoint and update O4 handoff before executing Phase 5.

## Required acceptance evidence

Seven explicit exit checks: development_zero_failures; no_unresolved_regressions;
replay_matches_primary; frozen_rig_baseline_gates; source_lineage_verified;
published_review_snapshot; freeze_record_pinned. Every check needs verified source
references, not only a boolean. Preserve the source report/source manifest and replay
receipt; no numeric replay images are expected. Owner acceptance is not required
for this development checkpoint; final production acceptance remains separate.

A PASS contract cannot prove an unexecuted check. Compare actual replay metrics and
read all domain/audit outputs. Reject the freeze if any blocker, unresolved material
regression, conflicting lineage, changed frozen input, non-identical replay or missing
source remains. Preserve the candidate as EXPERIMENTAL and continue the appropriate
local repair/diagnostic work. Do not weaken a gate or silently promote a trade-off.

## After freeze

Prepare/execute Phase 5 region packages in order only with a sufficiently stable
recorded foundation. Later candidates must compare against the applicable active epoch baseline, the immutable
recorded development-freeze candidate and their direct parent, plus local audits. Historical
baseline pins remain preserved and are never rewritten.
A changed candidate invalidates an old candidate-bound exit report: revalidate the
current revision and write a new report while preserving the original freeze pin.
Never rewrite a pinned freeze candidate to follow anatomy experiments. Review
snapshots remain NON-BLOCKING; continue safe regions/diagnostics while review is pending.

When old active records prevent status generation after a new candidate, archive
their exact references under phase_completion_history before clearing the active
entries for revalidation. Keep the original freeze pin and every old report. This
allows new experimental evidence to be tested without pretending old gates apply.
