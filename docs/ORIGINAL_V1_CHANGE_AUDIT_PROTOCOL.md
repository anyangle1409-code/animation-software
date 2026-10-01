# ORIGINAL v1 model / weight change audit

These tools collect evidence, never approval. Standard Python computes reports;
Blender is needed only for the read-only snapshot exporter. It records raw weights,
not renormalized values that could hide errors. No nearest-surface correspondence.

1. Verify local parent and child hashes against committed manifests.
2. Export each without saving the Blend:
   `blender --background --factory-startup <candidate.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <new snapshot.json>`.
3. Commit an edit policy containing `allowed_regions`, explicit `allowed_vertex_ids`,
   `allowed_bones`, `index_correspondence_confirmed`, `max_influences` (normally 4),
   and `normalization_tolerance` (normally 1e-6). Confirm index correspondence from
   actual operation history, not equal vertex count. Empty permission lists allow
   no edit. Policy must reference candidate hashes in the operation log.
4. Run `python scripts/audit_original_v1_changes.py <before.json> <after.json> --policy <policy.json> --json-out <new audit.json>`.
5. Inspect moved vertices, max/mean displacement, affected regions, symmetry change,
   vertex/face counts, topology/correspondence, distant edits; changed weight rows,
   affected bones, max delta, raw normalisation, influence counts, cross-side weights,
   symmetry and unexpected regions/bones. Preserve all flagged evidence.
6. If topology changed, displacement/weight deltas are explicitly unavailable until
   a separate authored correspondence is established. Do not assume indices still
   match. Current utility deliberately refuses such numerical comparison rather
   than inventing mappings. Use counts/health evidence and a reviewed mapping tool.
7. Re-run full deformation/contact/provenance tests; absence of distant changes
   alone does not approve shape quality. Keep previous and rejected audit records.

Known scope: snapshots audit body geometry/weights, not clothing/material quality,
whole scene provenance, pose mechanics or actual runtime animation. Mirror pairing
uses this character's own exact quantized coordinate twins; missing/ambiguous twin
coverage is reported and must not be called perfect symmetry.

## Snapshot schema 2 identity checks

The exporter now records both mesh/rig world matrices, all 63 rest bones including
parent, head, tail, full rest matrix (roll/orientation) and deformation flag, and
scene unit scale. This uses the candidate's own rig; it imports no reference mesh
or rig. Non-deform group names omitted from weight rows are listed separately.

Before comparing, the auditor requires schema 2, hgpt_canonical_v4_original, metre
units (scene scale 1, matching the foundation initializer), matching coordinate
frames and identical rig-rest/deformation identity. A transform or rig mismatch
returns STOP rather than misleading local vertex deltas. Preserve old schema-1
snapshots; export new schema-2 files to fresh paths rather than rewriting history.
Actual Blender export of these additional fields remains a laptop validation task.

The edit policy must contain `before_candidate_sha256` and `candidate_sha256`
matching the exact snapshot sources. Allowed IDs must be unique valid integers;
allowed bones/regions must exist. Normalization tolerance and influence count must
be finite/valid. The output records its policy limits explicitly. Region membership
is checked in both parent and child, so relabelling a distant vertex cannot mask
an edit. Changes to region labels remain separately visible. These checks protect
evidence comparability; an audit report is never model/production approval.

Example policy shape (fill hashes and IDs from the verified operation history):

```json
{
  "before_candidate_sha256": "EXACT_PARENT_SHA256",
  "candidate_sha256": "EXACT_CHILD_SHA256",
  "allowed_regions": ["hand"],
  "allowed_vertex_ids": [],
  "allowed_bones": ["hand_l", "hand_r"],
  "index_correspondence_confirmed": true,
  "change_epsilon": 1e-8,
  "normalization_tolerance": 1e-6,
  "max_influences": 4
}
```

This illustrative hand mask does not authorize a complete hand edit or infer that
vertex IDs correspond. Use each work package's permitted region and actual authored
edit mask. Empty IDs permit no change. Placeholder hashes deliberately fail.

## Phase 3 repair preparation drafts

Use `python scripts/prepare_original_v1_repair_policy.py 3D --out-dir <fresh repository folder>`
(or 3C / 3E) to prepare an edit-intent draft, audit-policy draft, inspection context
and execution README for the latest complete candidate. It reuses the existing
auditor and diagnostic brief validation; it does not add modelling or approval tools.

The parent hash is pinned. Child hash is null, correspondence is false, and all
permission lists remain empty. Raw probes, when available, are source-checked and
their IDs remain inspection references only. A missing pair is AWAITING_PROBES;
a partial, stale or contradictory pair is STOP. Missing data never invents a mask.
The preparation manifest binds source files and original draft bytes.

Preserve the generated drafts. Before editing, copy the intent to a fresh record
and record exact local IDs/regions/bones, defect evidence, operation and symmetry
plan. After making a NEW candidate, bind actual child identity and operation history
in a new linked record, export snapshots and create the completed policy using the
same pre-edit scope. Never retrospectively broaden a mask to hide distant edits.
Regenerate for a newer continuation candidate instead of relabelling old drafts.
