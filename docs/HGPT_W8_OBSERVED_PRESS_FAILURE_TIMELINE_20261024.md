# W8 shoulder-press observed failure timeline — native evidence, no repair
**24 October 2026. Read-only W8 reconstructed model, existing nine-frame native pose. No anatomical approval.**

## Provenance and cloud verification

- Isolated branch: `work/phone-blender-workbench-20261023`. Starting HEAD for this pass: `1d72499efaf76891fd41ba9229de085506df1b87`.
- Previously pending [seven-job run 40047715153](https://github.com/anyangle1409-code/animation-software/actions/runs/40047715153) is now **SUCCESS / all seven jobs completed**, at implementation commit `a001f60cbb9a43752cce93cf6576ed63e38dc8bf`. Native localization log: **150/150 tests PASS**, including 15 synthetic frame-math tests. Rest comparison: **5+12+12+15 tests PASS**. This verifies report infrastructure, **not** joint/skin correctness.
- Seven artifact ZIPs independently downloaded and SHA256-matched to GitHub's published digests: W8 `a1cf825082bce576dfafc3dce0d7dede9c9002c39eacd62a7e4cf017c8ab8ffb`; V14 `b018f84eca40023696bcf48c0848c8986f9c59d05427c2ac65f34854bc3b3feb`; R120 `41dd2860bc3facca995ef1b67ce63baac526463e39b5080bf88fb5fa042c8bba`; rest comparison `afd391c68a94702fbed3e469ea3b46d51d10bed9dabe67d0f68a204e85d8ba7f`; W8 actual pose `a76f589fbf277a86921f351e55ac12b0175492eb21f39f4b7aa37a341fe49837`; driver consistency `0ccfee8f9f1fc1f74656e5f768360b7ad38ceaf10673ceb773229e34476b66af`; native localization `2d502b488a29adaa38499d874591b76744bff5082c0adbae0360af9c0005934a`.
- W8 observed nine-frame pose JSON **member SHA256**: `7768c427cb13901faab42cce2c6299cfb179016230078b31889289940ede56bb`, from [artifact 12542086560](https://github.com/anyangle1409-code/animation-software/actions/runs/40047715153/artifacts/12542086560). Pinned reconstructed W8 .blend source SHA256: `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`; pinned r57 driver revision: `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- Earlier historical five-job [run 40029398965](https://github.com/anyangle1409-code/animation-software/actions/runs/40029398965) remains **FAILED overall** from the documented false-positive docstring/static read-only test. Its W8/V14/R120 native inspection and rest comparison passed; the four ZIPs and their rest-axis members were previously independently SHA256-verified. No reclassification of that failed run.
- The new timeline script was run **locally against the downloaded actual nine-frame JSON** and passed its provenance checks; **18/18 synthetic guards passed locally**. The new cloud workflow step and artifact must be checked separately before claiming CI verification.

## Actual observed nine-frame whole-body quality metrics

The pinned W8 in-memory shoulder press uses an authored humerothoracic target and a distinct **driver-measured** humerothoracic angle. Neither is independently calibrated ISB GH elevation or a clinical joint coordinate. The `l`/`r` suffixes are not certified anatomical sides. Counts are existing **whole-body** triangle flags and nonadjacent intersection pairs, not a per-shoulder tissue measurement.

| Frame | Measured driver angle, suffix l | Stretch flags | Collapse flags | Intersection pairs |
|---:|---:|---:|---:|---:|
| 0 | 87.680° | 1004 | 9 | 11 |
| 1 | 90.653° | 1006 | 2 | 11 |
| 2 | 98.491° | 809 | 3 | 7 |
| 3 | 109.564° | 954 | 38 | 163 |
| 4 | 122.232° | 2546 | 116 | 337 |
| 5 | 134.839° | 2723 | 102 | 83 |
| 6 | 145.726° | **3509** | 110 | 146 |
| 7 | 153.290° | 1437 | 116 | 245 |
| 8 | 156.103° | 1594 | **173** | **441** |

The largest adjacent **intersection-pair count** increase is frame 2→3 (7→163, +156); the largest adjacent **stretch-flag count** increase is frame 3→4 (954→2546, +1592). The highest stretch count is at frame 6, while the highest collapse and intersection counts occur at frame 8. Count differences do **not** identify newly failing triangle IDs, imply anatomical risk, or establish which shape key caused the change.

Actual helper evidence: cap helper present at all nine frames; axilla helper absent at all nine. Cap helper local delta (suffix l) grows from ~33.10° to ~49.43°, **not** a measured clavicle/scapula/glenohumeral anatomical rotation. Four populated shoulder-corrective families S1/S3/S5/S7 have verified math-consistent key values; a correct driver formula is not proof of a correct surface. The concurrent changes in S7 weights and surface metrics cannot establish causality. The fixed rest elbow taper proxy and shoulder/axilla tracked hotspot analyses remain separate evidence; no muscle anchor may be inferred.

## New reusable read-only diagnostics

- `scripts/cloud_body_analysis/pose_failure_timeline.py`: requires pinned model SHA256, frozen driver revision, all nine frames, consistent observed shape-key inventory, both suffixes, explicit no-save/no-approval provenance, finite metrics and internally consistent target/driver differences. Outputs `w8_press_deformation_timeline.json/.md`; retains per-frame key-family weights and helper presence, aggregate metric peaks and adjacent count jumps. No model writes or `bpy`.
- `scripts/cloud_body_analysis/tests/test_pose_failure_timeline.py`: 18 synthetic fail-closed guards. The existing `verify-actual-shoulder-driver-math` cloud job now runs the tests and reads **this run's** actual W8 pose artifact to publish the timeline alongside driver-consistency evidence; no extra model retrieval or native pose execution beyond the existing seven jobs.

Local reproduction, after obtaining the **exact pinned pose JSON** from the linked artifact:

```bash
python -m unittest discover -s scripts/cloud_body_analysis/tests -p test_pose_failure_timeline.py -v
python scripts/cloud_body_analysis/pose_failure_timeline.py \
  --actual /path/to/w8_shoulder_driver_pose_state.json --out /tmp/w8-press-timeline
```

## Next evidence gates and scientific sources

**Shoulder/clavicle/scapula:** independently bind thorax IJ/PX/C7/T8, scapular TS/AI/AA, clavicle SC/AC and reviewed humeral landmarks with verified sides and source-specific ISB segment definitions. Only then measure real coupled trajectories and isolate skin changes with controlled in-memory experiments. [Wu et al., ISB Part II (2005)](https://pubmed.ncbi.nlm.nih.gov/15844264/) defines reporting conventions; [2025 scapular kinematics review](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/) does not support a fixed universal scapulohumeral ratio.

**Elbow/forearm:** independently resolve humeral epicondyles and proximal/distal **radius versus ulna** frames before evaluating flexion and pronation. Rest PCA taper is a spread proxy, not a human circumference norm or muscle attachment.

**Hip/knee/ankle/foot:** separately calibrate pelvis/femur/tibia and multisegment foot with actual ground contact and skin continuity through squat; do not turn [CDC ROM population means and confidence intervals](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) into individual limits. See [Wu et al., ISB Part I (2002)](https://pubmed.ncbi.nlm.nih.gov/11934426/) and the [ISB foot standards portal](https://www.isbweb.org/activities/standards).

**Current gates:** 46/46 landmark checklist points unbound; 0/19 generic human joint-motion scenarios executed or approved; W8/V14/R120 are reconstructions, V14 archive two-vertex discrepancy and W8 archive mismatch unresolved; shoulder press/squat/grip acceptance FAILED/BLOCKED. No native skin repair, approved muscle origin/insertion/side, production update, ROM clamp, or highlighting. Permanent muscle IDs are retained; highlighting remains owner-DEFERRED.
