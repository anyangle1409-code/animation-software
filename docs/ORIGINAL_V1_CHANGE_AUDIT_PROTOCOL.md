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
