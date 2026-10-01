# Phase 3D — wrist / push-up

Status: REFINEMENT; coarse development clear, strict severity regression remains.
Review snapshots are NON-BLOCKING. Entry: hash-verified experimental continuation
candidate from 3B. Read r29/R2/r28 comparisons and remaining diagnostics.
Defect: pushup_bottom hand maximum ratio R2 1.915 → r29 2.032 exceeds the committed
0.1 comparison tolerance. r28 is 2.067; r29 self-intersections 150 versus r28 144.

Exact task: existing remaining diagnostic locates worst pushup_bottom/hand/max
edges, vertex IDs, mirror edge, rest/posed midpoint and bone weights. Record a
separate edit mask; `diagnostic_brief.md`/JSON lists measured inspection IDs only.
Agreement with the complete rounded pose report is required before the brief is
written; a discrepancy stops the runner and must be reconciled without relabelling.
Define a wrist-only bilateral permitted mask from those IDs before a new candidate edit.
Change only local forearm/hand transition weights unless evidence requires a local
geometry experiment. Preserve finger/PIP improvements and unrelated shoulders/body.
No rest/hierarchy, push-up pose, floor, threshold or equipment edits. No broad hand
re-solve merely to improve one edge; no legacy/third-party data.

Tests: `RUN_ORIGINAL_V1_REPAIR_CHECK.bat pushup <new.blend> <unique label>` and hand
subset; then `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <new revision> <predecessor>`.
Compare R2, direct parent, r28 and r29 with embedded grip evidence. Target the
reported severity defect using unchanged tolerances; do not claim clearance just
because max <5.0. Preserve floor position, palm contact, curl_peak clearance,
finger minima and bilateral grip. Mesh/weight audits must show no distant edits.

Renders: pushup_bottom side, 3/4, palm/wrist close views, both sides; curl/handle
control close-ups. Use actual hash-bound capture manifests and old/new boards.
Acceptance: targeted R2 wrist regression disappears without new predecessor
regressions or blockers; full contact and provenance checks remain intact.
Reject new failure/contact loss, broad unrelated edits, symmetry/normalisation
failure or hiding severity behind aggregate counts. Preserve rejected evidence.

Commit/push: source/child manifests, solution/edit log, mask and weight/mesh audits,
full reports and comparisons, review images/manifests, O4/status/ledger/dashboard.
Owner_review pending does not stop grip/lunge diagnostic work. Next: 3C then 3E,
or safe independent diagnostics if grip requires a frozen-structure decision.
