# V3 candidate — bounded skin weights

This is a separate review candidate. The v1 and v2 files remain available. No production model, rig, exercise logic or asset reference was changed.

## Change and reason

V2 added midpoint vertices across the inherited body surface. Some midpoints combined more than four skin influences, while the application reads only four. At the neck/jaw blend the worst midpoint discarded 20.82% of the weight. V3 leaves an edge unsplit when its new midpoint would discard more than 5%. This uses the existing four-influence runtime and keeps the original vertices and their weights unchanged.

| Measure | V2 | V3 |
|---|---:|---:|
| Body triangles | 59,128 | 57,721 |
| Body vertices | 31,033 | 30,311 |
| Mean new-vertex discarded weight | 0.48% | 0.21% |
| Worst new-vertex discarded weight | 20.82% | 4.98% |
| Shoulder new vertices | 2,042 | 2,042 |
| Worst shoulder new-vertex loss | 3.87% | 3.87% |

The 5% threshold had a failing check against v2 before the builder was changed; it passes against v3. Details: `reports/weight_audit_v2.json`, `reports/weight_audit_v3.json`, and `reports/weight_audit_red.log`.

## Shoulder and motion

At curl Bottom, deltoid height remains 31.9 mm above the unchanged joint (target 25–35 mm). Apex z is -47.8 mm, posterior to the joint at -21.9 mm. The 160 bone matrices, original hand vertices, grip and equipment transforms match the frozen dressed reference at 26 sampled frames for each of the five exercises. Bare and dressed v3 bodies and solved grip match exactly at the supplied curl equivalence check.

Six focused tests passed. Finger wrap remains 343°. Renderer/exporter equipment agreement is 0.0000 mm at t=0,2,4; dumbbell Bottom clearance is +1.99/+2.15 mm with no reported intrusion. Existing push-up reach/flare findings remain. The unchanged application source suite was not rerun for this mesh-only change; its last run was 290 passed, 8 failed, 1 skipped. Logs: `reports/v3_tests.log`.

GLB inspection found 57,721 nondegenerate body triangles and zero edges shared by more than two faces. The v3 rig, animation and original binary prefix match the frozen source. Every original body attribute matches v2. The bare file differs only by disconnecting the shorts mesh node; the body and binary data are identical. All 400 reference files and the v2 deliverables were verified unchanged. See `reports/final_integrity_v3.json`.

## Visual review

`renders_v3/V3_ANATOMY_AND_EXERCISES.jpg` shows front, side, three-quarter, back and the five exercise peaks. `renders_v3/V3_OVERHEAD_BASELINE_COMPARISON.jpg` shows matched shoulder press and pull-up close-ups. The sharp overhead armpit fold also appears in the frozen reference at the same pose. V3 does not claim to repair that inherited defect; it needs deliberate local topology/weight/corrective work before production readiness.

The inherited face, hands, knees and some joint flow remain coarse despite the higher triangle count. No new skin textures were authored. The mesh is still an inherited triangulated surface refined for this candidate, not a complete new quad retopology. This is not a production-ready model.

## Files

- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v3.blend` — editable dressed candidate.
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v3.glb` — dressed runtime candidate.
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v3_BARE.glb` — matched bare candidate.

Use v3 only in the isolated review workflow. Do not merge or promote it to production.

