# W8 Row Pinned Edge Trajectory Implementation Plan

> Execute inline using superpowers:executing-plans, with one final fresh-context review.

Goal: track the four existing W8 edges across nine plain row poses without editing model files.
Spec: docs/HGPT_W8_ROW_ELBOW_CONTROL_EVIDENCE_20261031.md; elbow_edge_endpoint_audit.py TARGETS.
Architecture: a pure helper checks source/evaluated polygon correspondence, captures an evaluated neutral reference and endpoint/length/ratio samples. Existing row setup/post_pose callbacks collect separate JSON/Markdown in the existing artifact; original row-control output is unchanged.

Constraints: exact W8/r57 and four pairs/names; no blend save; corrective keys zero; explicit neutral reference; fixed topology; world metres and length millimetres. Four diagnostic edges are not a complete elbow region. Ratios are not tissue strain or safety; historical press ratios have a different reference. No anatomical side/ISB/ROM/muscle/acceptance claim.
Review focus: nested malformed records, numeric/ID types, nonfinite/extreme points, topology changes, degenerate neutral edges, zero posed edge, derived metric tampering and baseline labels.

### Task1 — tracked edge evidence
Files: new row_pinned_edges.py and test_row_pinned_edges.py; row_elbow_pose_state_probe.py capture/output; workflow focused test.
- [ ] Write tests for independent half/double lengths, rigid invariance, exact pairs/topology, degenerate/nonfinite reference, zero posed length and tampering. Observe RED missing module.
- [ ] Implement reference(vertices,faces,source_count,source_faces), snapshot(vertices,faces,reference,sample), report(reference,samples), validate_report(data), markdown(data).
- [ ] Integrate reference capture at benchmark setup and nine plain pose snapshots, guard source topology, output separate w8_row_pinned_edges.json/.md.
- [ ] Focused/full suites, compile/diff/workflow checks; fresh review and test-first Important/Critical corrections.
- [ ] Commit and verify all cloud jobs plus downloaded artifact CRC/SHA256, validator and exact Markdown replay.
- [ ] Save native method, machine record and execution-ledger result.
