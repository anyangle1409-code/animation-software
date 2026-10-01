# PHASE 6 — FINAL TOPOLOGY / SURFACE QUALITY

PREPARED ONLY; NOT STARTED. Apply LATER_PHASE_EXECUTION_CONTRACT.md and the
tooling-readiness table. Entry: Phase 5A–5G evidence and current-candidate exit
record, development freeze, verified local source and preserved anatomy reviews.

## Scope and exact work

Inspect the bare body's closed surface, components, edge/vertex manifoldness,
face winding/normals, duplicate/degenerate geometry, joint-support loops, creases
and symmetry coverage. Keep authored anatomical landmarks and exercise ranges.
Change only a measured local surface defect in a NEW candidate, with a pre-edit
mask. Prefer preserving IDs/faces. No broad remesh, automatic reference fitting,
V-series/third-party transfer, rig/rest or gate changes. A topology change must
record old/new faces/counts, affected regions and authored correspondence.

Advanced evaluated-surface tooling is also prepared in
`PHASE_6_ADVANCED_SURFACE_PROTOCOL.md`. It adds a one-command future capture path
for evaluated normals, exact non-adjacent BVH self-intersections and explicit
authored joint-support evidence. The joint-support template deliberately contains
no inferred vertex IDs; they must be authored from the final mesh. Even an
EVIDENCE_COMPLETE combined report is not Phase 6 completion.

The raw surface auditor is prepared: follow `SURFACE_AUDIT_PROTOCOL.md` and run
`python scripts/audit_original_v1_surface.py <snapshot.json> --candidate-manifest <candidate.json> --json-out <fresh surface.json> --markdown-out <fresh surface.md>`.
It reports defect IDs/regions, vertex links, components/boundaries, winding,
degeneracy and symmetry coverage/ambiguity with declared precision. It never
completes the phase. Actual shading normals are not captured. Joint-support review also needs
actual joint landmarks and posed views; topology statistics alone cannot pass it.
No unclassified manifold, winding or degenerate defect may be silently waived.

## Tests, renders and exit

Run raw surface and before/after change audits, then full bare stress evidence using the shared
commands. Compare R2, parent, development freeze and hand/contact anchors. Require
no new development blocker or material predecessor regression; preserve production
deficits until Phase 9. Unknown correspondence blocks numerical displacement/weight
claims; it does not permit a guessed mapping.

Render actual neutral front/rear/side/3/4, wire/surface close views for changed areas,
shoulder/elbow/wrist/hip/knee loops and corresponding loaded poses. Wire views
must be candidate renders, not generated diagrams. Publish matched parent/new
boards with hashes. Owner review pending is NON-BLOCKING; continue tooling/clothing
planning without destructive changes dependent on a rejected form.

Exit checks: `manifold_surface`, `normals`, `degenerate_faces`, `joint_support`,
`symmetry`, `topology_weight_audit`, `deformation_regression_checks`.
Attach raw domain evidence to each, verify the Phase 6 packet and register it only
after real checks pass. Commit source/child manifests, operations/mask/correspondence,
surface/change reports, comparisons and actual review evidence/shared state.
Reject unclassified defects, hidden changed regions, lost landmarks/joint support,
unknown mappings used as numerical proof or new regressions; preserve the candidate.
Next: Phase 7 independently authored clothing; Phase 6 completion is not approval.
