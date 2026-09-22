# V6 medial-knee seam review candidate

V6 is a separate test asset derived from V5. It aligns two nearly coincident open boundary strips on each inner knee. It does not change the frozen shoulder or other bones, hierarchy, skin weights, animations, exercise definitions, grip/equipment logic, production references or `bundled.ts`.

## Measured change

At the squat peak each knee had two 15-vertex boundary paths, 28 boundary edges in the sampled region and a maximum 0.58 mm geometric gap. Paired vertices have identical joint sets, weights and normals. V6 gives each pair the same rest position and normal; the largest individual rest move is 0.335 mm. The gap is 0 mm on both knees in all 20 saved candidate pose snapshots across the five exercises. Body topology remains 33,089 vertices and 62,961 triangles; UV seams and face indices remain separate. This is geometric alignment, **not topological welding**.

Six focused checks pass: shoulder sagittal target; bare/dressed equivalence; grip/343° wrap; renderer/exporter agreement; dumbbell/shorts clearance; and 26 frames per exercise for curl, squat, shoulder press, push-up and pull-up. Original hand positions, all 160 bone matrices and equipment transforms match the frozen dressed model throughout. V6 has zero degenerate body triangles and no edges shared by more than two faces. All 400 pinned source files and V5 deliverables remain hash-identical. `reports/final_integrity_v6_knee_seam.json`, `reports/knee_seam_v5.json`, `reports/knee_seam_audit_v6.json` and the test logs contain the checks.

`renders_v6_knee_seam/V6_KNEE_SEAM_COMPARISON.jpg` shows matched knee close-ups; the visible difference at this scale is small. The pointed medial knee overhang remains. Three broader candidate-side smoothing/contour trials did not remove it cleanly and were rejected locally. A real production knee pass requires connected anatomical joint loops and deliberate patella/tendon shape work, followed by the same motion checks. V6 is a review checkpoint, not a production-ready knee or finished skin mesh.
