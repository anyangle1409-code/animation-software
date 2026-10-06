# r97: shoulder foundation candidate (weights-only, NOT accepted)

| | |
|---|---|
| Candidate | `HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r97.blend` |
| SHA-256 | `8b2fbe50781dfcf9123178615efc926945847959ed2b897def920f0b3c48962f` |
| Parent | r95 (BARE GLB `c4b8e388…7c85`), rebuilt as `repair_preparation/r97_shoulder_foundation_declared/r95_reconstructed.blend` |
| Scope | Declared before edit (`r97_declared_before_edit.json` + amendment). Spine_02/03, clavicles, scapulae, upper arms, glenohumeral helpers only. |
| Status | **BLOCKED** by the shoulder acceptance evaluator. Production approval stays false. Awaiting GPT validation. |

## What changed (causal order)

1. **Skeleton mechanics.** In rev2c the scapula pivots at the scapula head, so the glenohumeral joint slid 9.3 cm medially during elevation. Its pivot is now at the acromioclavicular joint, and the joint moves 1.1 cm medially and rises 5 cm. Two non-exported helper pairs are added: `glenohumeral_half_{l,r}`, which carry half the swing plus the full twist, and `glenohumeral_ref_{l,r}`. Vertices across the glenohumeral junction blend to the half-swing helper rather than across the full joint angle, which removes linear-blend chord collapse. Transition-zone shrink across the matrix improves from 0.16 to 0.90.
2. **Topology.** Unchanged. Vertices, faces and rest positions are identical to r95.
3. **Weights.** The declared-bone weights are re-solved as a cotangent-harmonic field with anatomical Dirichlet anchors:
   - rib wall to the spine;
   - skin over the scapular body to a partial scapula weight;
   - clavicle ridge;
   - upper trapezius slope;
   - spinal midline at the neck base, held to the spine only;
   - acromion cap.

   The solution is mirrored left to right and capped at four influences. The neck-boundary band has its declared-bone share re-solved, while its neck and head weights are restored exactly. Weights on non-declared bones are bit-identical to r95 (`r97_scope_audit.json`).
4. **Correctives.** None fitted. r95's six keys are kept at value 0 with their drivers removed, so all evidence is weights-only.

## Results against r95 (weights-only, 56-pose matrix)

| Metric | r95 | r97 |
|---|---|---|
| Protected-zone self-intersection pairs (sum) | 1931 | 1536 |
| Minimum edge ratio | 0.031 | 0.078 |
| p1 edge ratio | 0.292 | 0.482 |
| p99 edge ratio | 3.25 | 3.16 |
| Maximum edge ratio | 4.09 | 4.45 |
| Minimum transition-zone shrink | 0.16 | 0.90 |

The repository pose test comparison is in `repair_checks/r97_pose_test_weights_only/r95_vs_r97_pose_test_comparison.md`.
- **Improved:**
  - press_top self-intersections: 58 → 4;
  - press_top_rhythm: 72 → 0;
  - overhead compressed edges: about 35% fewer.
- **Regressed:**
  - squat_bottom: 82 → 99;
  - pullup_top: 92 → 110;
  - pullup_hang: 0 → 8;
  - overhead stretched edges: up;
  - overhead volume: up 4–7%.

## Known failures (expected GPT FAIL)

- **SH-V02.** Overhead (150–170°) there is a thin axillary membrane between the arm and the chest wall, with a crease. r95's pointed pectoral flap is gone, but the membrane remains.
- **SH-V01.** The rear deltoid dents at flexion 150–170°, press_top and pullup_hang.
- **SH-V05.** Back creases lateral to the scapula at 150° and above. r95's rear back-sheet is gone.
- **SH-M03.** Protected-zone self-intersections are not zero: 27 of 56 poses.
- **SH-M09.** The squat and pull-up regressions above.

Three or more weight-only trials moved these defects rather than removing them. The next causal layer is **support topology and the bind-pose shape of the axillary fold**: extra edge loops across the anterior and posterior folds, and a less adducted rest fold. Further weight tuning is not the next step.
