# P007 — Unconstrained rigid sternum rotation + translation fit (9 October 2026)

**Status: FIRST-PARTY NUMERIC DIAGNOSTIC / NOT AN ANATOMICAL POSE OR CANDIDATE.**

The user's Home Gym PT male (1.82 m) skeleton is still 0 READY / 9 PARTIAL / 3 BLOCKED; this investigation does not change any canonical bone, source-of-truth coordinate, anatomy decision or production mesh.

## Problem inherited from P004–P006

- The isolated, source-attributed but previously rejected P003 spine-only disc repartition shifted ribs away from their articular levels by up to ~40 mm.
- P004 restores the **relative 3D rib-head/vertebra position** by moving each rib with its thoracic reference. P005 follows the unchanged clavicle→arm/hand hierarchy when the sternum moves.
- The full 3D sternocostal corridor audit shows **six of 14** recorded rib-tail/sterna-marker vectors change by >5 mm under the existing median rib-shift sternum translation. Max **9.446 mm**.
- P006 analytically proves **every pure sternum translation** leaves at least **7.230 mm** maximum relative-vector mismatch for that particular frozen set of rib displacements. A least-squares *translation* achieves **7.828 mm** maximum mismatch.
- All 5-mm bounds here are diagnostic engineering change-detectors, **not medically supported cartilage tolerances**.

## New question and independent implementation

Could a **rigid rotation plus translation** of the existing sternum control and its 14 sternal markers reduce the relative-vector mismatch?

`scripts/anatomy_fit/p007_sternum_rigid_fit_audit.py` implements a standalone first-party, pure-Python **proper rigid-body least-squares point-set fit** (Horn unit quaternion method, symmetric Jacobi eigensolver). It maps each original sternocostal marker control position to the same marker position displaced by that rib's actual c004→P004 rigid-tail displacement.

This fits in 6 DOF without introducing or installing a new anatomical target, editing bones, installing cartilage physics or changing the spine. It **minimises sum of squared 3D errors**, not maximum error. No physiological movement bounds are enforced; it is not proof that the model can really rotate this much.

This diagnostic first verifies P006's premises that rib motion and sternum/marker motion in P004/P005 are genuinely rigid **pure translations**; it refuses manipulated marker ownership or non-rigid rib changes.

## Verified results, GitHub CI run 37922684079

| Diagnostic | Result |
|---|---:|
| Input sternal-marker/rib-tail control corridors | 14 |
| P004/P005 median-translation worst change | 9.446 mm |
| Best pure translation (least squares), worst | 7.828 mm |
| Any pure translation best-possible lower bound | 7.230 mm |
| Unconstrained **rotation + translation** least-squares fit, worst | **5.926 mm** |
| Rotation + translation root-mean-square residual | **3.713 mm** |
| Best-fit geometric rotation angle | **3.958°** |
| Markers still exceeding 5-mm engineering guard | **2 of 14** (rib 1 left/right) |
| Anatomical motion or posture validated | **NO** |

The rotation is primarily about the model's X axis (sagittal plane); the numerical best-fit world translation matrix is saved by the report, but its absolute world translation components must **NOT** be interpreted as a clinically appropriate sternal-body target or applied to the production character.

### Interpretation

The rigid fit improves the mathematical correspondence markedly, with the ribs 2–7 now below the 5-mm **engineering change threshold**. Ribs 1 left/right still exceed it by ~0.926 mm. **This does NOT prove no 6-DOF rigid-body solution exists** that satisfies every guard: the current optimizer minimizes RMS, not the worst-case residual, and no physiological range constraints are applied.

Even a mathematically perfect rigid fit would not demonstrate real costal-cartilage anatomy, thoracic shape, SC/AC/GH continuity, patellar/finger interactions, body surfaces or realistic exercise movement.

### Needed next

1. Obtain and validate 3D costosternal cartilage insertion landmarks, per-rib curved geometry, manubriosternal relationship, sternoclavicular anatomical constraints and patient/cohort posture. Preserve the existing source-to-coordinate definitions and avoid arbitrary scaling.
2. Distinguish rib *articular surface contact*, rib orientation/costochondral flexibility, sternum orientation, and scapulothoracic gliding from the existing two-point rib controls.
3. A separate unconstrained **minimax** rigid-fit probe could check whether any six-degree-of-freedom transform satisfies all 14 numeric review guards, but that would still be no anatomical acceptance.
4. Re-run complete coupled muscle/skeletal movement and original full regression suite only on a source-compatible candidate. Continue explicit documentation of literature and frame gaps.

### Run again

```bash
python3 -m unittest discover -s scripts -p 'test_p007_sternum_rigid_fit_audit.py' -v

python3 scripts/anatomy_fit/replay_p004_coupled_thorax.py --out /tmp/diagnostic_p004.json
python3 scripts/anatomy_fit/replay_p005_shoulder_chain.py --p004 /tmp/diagnostic_p004.json --out /tmp/diagnostic_p005.json
python3 scripts/anatomy_fit/p007_sternum_rigid_fit_audit.py \
  --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
  --proposal /tmp/diagnostic_p005.json
```

CI independently ran all **108 focused tests** in this draft branch: 13 trunk preflight + 14 P004 + 17 P005 + 15 neutral arm/thigh + 17 rib 3D + 17 P006 + 15 P007; all passed. The previous full-suite 9 inherited production-control failures are NOT silently treated as fixed.

No C005, canonical promotion, merge, production files or Claude work altered.
