# Phase 3C — equipment grip / thumb

Status: BLOCKED; four development failures. Review snapshots are NON-BLOCKING.
Entry: hash-verified continuation candidate after 3B; use r29 read-only if r30 is
incomplete/rejected. R2, r28, r29 and local predecessor remain comparison anchors.
Current evidence: curl_handle and pullup_bar each have 5.93 mm penetration on both
sides; prior solves show weight-independence. Do not repeat blind weight solves.

Exact diagnosis: run `RUN_ORIGINAL_V1_REMAINING_DIAGNOSTICS.bat <revision>` once
into a new output folder. Read grip_penetration.json for pre/post-close depth,
deepest vertex IDs/regions/weights and handle centre/axis/radius. Verify source SHA.
Separate thumb IP rest conflict, handle frame, closing pose and local geometry.
Evidence may identify a frozen rig/pose defect; document it, do not silently repair
the rig or handle frame. Continue wrist/lunge/read-only tasks if that decision is blocked.

Permitted repair: a NEW experimental candidate with minimal independently authored
thumb/web local geometry, if diagnostics demonstrate a mesh defect and it can be
repaired without changing frozen rig/poses. Record permitted vertex mask before
editing, mesh/weight audit and bilateral symmetry. No whole-hand remesh, external
reference fitting, handle radius/tolerance changes, rig rest edits or copied weights.

Tests: focused `RUN_ORIGINAL_V1_REPAIR_CHECK.bat hand <new.blend> <unique label>`;
then `RUN_ORIGINAL_V1_FULL_EVIDENCE.bat <new revision> <predecessor>` and additional
r28/r29 comparisons using existing comparator with embedded grip reports. Compare
R2, execution parent, r28 and r29. Development penetration ≤2 mm on all four checks;
production remains ≤1 mm, with unchanged contact-count gate. No contact loss,
finger collapse, new curl_peak failure or wrist/overhead regression. No overall score.

Renders: both thumbs/webs and handle views before/after closing in curl_handle and
pullup_bar; actual camera/source SHA manifest; matched previous/new boards.
Acceptance: remove targeted failures and introduce zero material regressions versus
predecessor; keep inherited R2 differences separately visible. Reject invalid
provenance, frozen-frame edits, lost contact, higher blockers or material worsening.

Commit/push: candidate operation log and manifest, local edit mask, mesh/weight
audits, grip probes, full pose reports/comparisons, real review images, updated
handoff/status/ledger/dashboard. Owner_review pending; continue safe work.
Next: remaining wrist/lunge packages. Grip metadata for runtime is authored only
after measured ORIGINAL-v1 contact passes; do not reuse legacy or generic fallback rows.
