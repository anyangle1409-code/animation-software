# Phase 3E — hip / pelvis / groin / deep flexion

Status: BLOCKED, not repaired. Review snapshots are NON-BLOCKING.
Entry: latest hash-verified experimental continuation candidate; earlier hand and
contact edits preserved. Diagnostics may start read-only while their reviews remain
pending. r29 lunge failures: pelvis max 7.559, torso min 0.120, torso max 7.200.
Squat is a control, not permission to hide lunge behind a five-exercise report.

Exact task: existing remaining diagnostics report lunge extreme edges, rest/posed
coordinates and current bone weights. Inspect the pelvis/upper-thigh/lower-torso
transition using `diagnostic_brief.md`/JSON and the raw edge rows. Listed IDs are
inspection targets, not an authorised edit mask or proof that weights are the cause.
Record an explicit bilateral vertex mask and allowed bone names before
editing a NEW candidate. Begin with local weight repair; supporting geometry only
if weight evidence proves necessary. Do not edit shoulders, arms/hands/feet, shorts,
frozen 63-bone rig/rest, lunge/squat definitions, R2 or thresholds.

Tests: `RUN_ORIGINAL_V1_REPAIR_CHECK.bat hip <new.blend> <unique label>`, then full
15-pose `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <new revision> <predecessor>`.
Compare R2, direct predecessor, r28 and r29. Target unchanged region max ≤5.0,
region min ≥0.15, volume 0.90–1.10, ≤200 intersection pairs, unchanged floor/contact
and all other development gates. No new material regressions; production targets
remain a separate later check. Re-test body before repairing garment deformation.

Renders: lunge front/side/3/4 and hip/groin close views, squat front/side/hip and
neutral pelvis; actual capture manifest, old/new pairs. No synthetic anatomical guide.
Acceptance: all three targeted failures gone with zero new predecessor regressions,
no remote region changes, normalized symmetric weights and independently authored
operation history. Reject a lower total hiding newly worsened squat, torso, contact,
hand or shoulder behaviour; preserve evidence and use previous valid parent.

Commit/push: new manifest and operation/solution evidence; permitted mask;
mesh/weight audits; full reports, every comparison, actual review snapshot;
O4/status/ledger/dashboard. Owner_review pending; continue safe reporting/QA prep.
Next: Phase 4 only with zero blockers, reconciled inherited severity regressions,
complete source-bound evidence and a separate development freeze record. Do not
silently change R2 or call the development freeze production approval.
