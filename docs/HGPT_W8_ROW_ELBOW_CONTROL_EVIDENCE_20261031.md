# W8 row elbow-control evidence — 31 October 2026

## Verified native execution

Implementation `36872968457c49b06027d0c49491e9f5f0e3e6a1`, [run41189500502](https://github.com/anyangle1409-code/animation-software/actions/runs/41189500502), SUCCESS7/7. Cloud tests: report378/378; row12/12; other pose29/29+33/33+14/14+19/19+6/6+10/10; driver10/10+20/20+8/8. Before implementation, focused tests failed because the module was absent; they passed after implementation. A fresh-context review found no Critical/Important issue. Workflow parsing, compile and diff checks passed.

Artifact13038775565 independently downloaded, ZIP CRC-checked and SHA256 matched GitHub `ea7e2950fa936e2bfa8f51c1fdf78f9938b4495d403095678fad90429807ae2d`. JSON `eae29117f09652b4c17c84d555643ce4be70b1157daa8868bd4fbb63b904d5f2`; Markdown `1975bb3935cce0dc060455eab0d7df5150427838b27a0d36d8cb24a6b494a048`. The native JSON passes strict validation and regenerates its Markdown byte for byte. Machine record: `recovery_20261023/cloud_verification_20261031_run41189500502.json`.

## Control motion findings

This is the unchanged frozen bent-over-row benchmark, which couples shoulder and elbow motion. It is not an isolated elbow-flexion test.

| Sample | Elbow command degrees | Signed shoulder command degrees | Included control angle l/r degrees |
|---:|---:|---:|---:|
| 0 | 0 | 0 | 179.02601 / 179.02604 |
| 4 | 0 | 45 | 179.02602 / 179.02604 |
| 5 | 15.625 | 31.71875 | 164.87436 / 164.87437 |
| 6 | 50 | 2.5 | 130.51619 / 130.51621 |
| 7 | 84.375 | -26.71875 | 96.14559 / 96.14561 |
| 8 | 100 | -40 | 80.52222 / 80.52223 |

- Independent local forearm quaternion magnitude follows the elbow command with maximum discrepancy about0.00001256degrees.
- During samples0–4, with no commanded elbow bend, included-angle variation is below0.000009degrees despite shoulder movement.
- Included point-angle decrease over the path is about98.5038degrees. Maximum bilateral included-angle difference is about0.000027degrees.
- The initial included angle is not180degrees. The 100degree local command and98.5038degree included-angle change describe different quantities and are not interchangeable. Their difference alone does not prove an anatomical fault or justify changing the rig.

All points are authored bone-control heads, not verified anatomical joint centres. These unsigned included angles are not signed ISB joint coordinates or clinical ROM measurements. Suffixes l/r are not certified anatomical sides. No radius/ulna or natural-movement approval follows.

## Deformation remains unresolved

Existing whole-body flags are captured independently of control-angle interpretation. Sample0 has0collapsed,0stretched and2687intersecting face pairs; sample8 has31collapsed,1146stretched and1748intersecting pairs. The lower final intersection count does not establish acceptable geometry, nor can all final pairs be described as newly introduced. Flags are whole-body counts, not elbow-local failures, distinct affected vertices or anatomical tissue measurements.

The plain benchmark clears all corrective shape-key values, verified at every callback. It does not test driven corrective skin. The row ends flexed; return-to-neutral is untested. No visual or anatomical correction is claimed.

## Next evidence needed

Measure the same four already pinned W8 mesh edges from `scripts/phone_blender/elbow_edge_endpoint_audit.py` over this row path, with exact source/topology and endpoint-ID guards. Keep their historical shoulder-press names as provenance, not proof of anatomical location. They are four diagnostic edges, not a complete elbow region. Compare plain and driven corrective behavior only in separately labelled measurements; no guessed anatomical attachment or automatic approval.

No original model, rig, rest skeleton, weights, stored shape key, muscle ID/attachment, PT-App or PT_MODEL_VERSION1.0 changed. No merge or deploy.46 landmarks remain unbound;0/19 generic motions are approved.
