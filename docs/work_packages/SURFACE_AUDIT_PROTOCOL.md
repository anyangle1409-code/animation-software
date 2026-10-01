# ORIGINAL v1 raw-snapshot surface audit

Prepared deterministic tooling. No actual candidate surface report has been
generated in this GPT stage because Blender snapshots are unavailable here.
This is evidence tooling, not a phase-completion or production-approval tool.

## Capture and execute

Check LIVE model branch/working tree and follow the preflight and change-audit
protocol. Use the candidate's own verified schema-2 snapshot and manifest.
Historical candidates may be inspected with their own identities; never relabel
their snapshots or bind them to a newer manifest. Both input/output files must
be inside the repository. Keep all existing evidence and use fresh output paths.

```bat
blender --background --factory-startup <verified candidate.blend> --python-exit-code 1 --python scripts/snapshot_original_v1_model_blender.py -- <fresh snapshot.json>
python scripts/audit_original_v1_surface.py <snapshot.json> --candidate-manifest <candidate.json> --json-out <fresh surface.json> --markdown-out <fresh surface.md>
```

The tool checks schema/rig/units/raw shape, finite coordinates and matching candidate
SHA. It records actual input/script file hashes, command, source git commit and UTC
timestamp. The snapshot/source bytes remain unchanged. It does not open/save a Blend,
move vertices, alter weights, assign normals, triangulate/remesh or change gates.
Snapshot metadata/hash binding cannot independently authenticate the author's source
history; preserve the real snapshot capture and operation records as well.

Exit 0 means a valid evidence report was written, even when it finds defects.
Exit 2 means invalid input, identity, precision, output collision or technical
failure. No report status is PASS: it is always EVIDENCE_ONLY, phase_complete=false
and production_approved=false. CLI output/Markdown are summaries; inspect JSON IDs.

## Measurements and interpretation

| Output | Meaning / coverage |
|---|---|
| Boundary / nonmanifold edges | One / more than two incident face uses, with exact vertices, faces and regions |
| Winding conflicts | Two incident faces traverse the shared edge in the same direction |
| Vertex links | Per-vertex incident-face neighbor link; disconnected/branched links expose pinch points even when every edge has two faces |
| Components | Edge-connected face shells, raw region counts, signed fan volume and conditional orientation hint |
| Repeated / duplicate faces | Repeated vertex indices; duplicate cycles up to rotation/reversal, preserving face order semantics |
| Degeneracy / nonplanarity | Exact zero area vectors, declared near-zero area, zero-area fan triangles and distance from the face's area-vector plane |
| Isolated / coincident vertices | Raw vertices unused by any face; distinct indices with exactly identical coordinates. Vertices present only in excluded faces are listed separately |
| Symmetry | This candidate's own unique reflected coordinate bins; vertex/face coverage, missing/ambiguous partners, mirrored winding mismatch and position error |

Repeated-index faces are explicitly excluded from incidence/link/component and
geometric calculations; they never disappear from defect/coverage reporting.
All analysed faces retain raw geometry metrics and region labels. Unknown mirror
coverage is not perfect symmetry. No nearest-surface matching or reference transfer
is used. Asymmetric triangulation or intentional authored asymmetry remains visible
for classification, never silently repaired.

Signed volume is only an orientation hint for closed, consistently wound shells
without identified invalid faces/vertex links. Negative volume is not automatically
rewritten. Positive volume does not prove an intersection-free outward surface:
nested cavities, overlapping components and actual anatomy need further evidence.
Polygon fan measurements are diagnostic; they do not prove Blender/exporter's
triangulation of concave/nonplanar n-gons.

Default diagnostic precision is area 1e-12 m², planarity 1e-6 m and mirror bins
1e-6 m. Optional flags `--area-epsilon-m2`, `--planarity-epsilon-m`, and
`--mirror-quantum-m` are recorded in the report. They are measurement controls,
not deformation tolerances, defect waivers or acceptance gates. Use identical
settings for comparisons; retain changed-setting evidence explicitly. Zero-area
faces remain separate even when near-zero precision is changed.

## Phase 6 use and unresolved work

Use raw findings as source evidence for manifold/degenerate/symmetry checks, with
coverage and any intentional classifications recorded. Do not infer completion
from an empty finding list. Joint-support loops require authored landmarks and
loaded views. Actual shading/custom/split normals, evaluated modifiers, clothing,
self-intersections, deformation and owner anatomy review are not inspected here.
Those checks remain unresolved and require their separate domain evidence.

Commit the actual snapshot/capture identity, candidate manifest, raw JSON/Markdown
and comparisons when execution occurs; update the Phase 6 packet/shared state only
after all phase requirements genuinely pass. Real review snapshots remain pending
and NON-BLOCKING; the numerical report is not a visual snapshot. Preserve defects,
rejections, partial evidence and protected frozen structures. No production approval.
