# P006 — Mathematical limit of sternum-only translation (9 October 2026)

**Status: independent engineering feasibility analysis, NOT a skeleton correction or anatomical target.**

## Proven input and reproduction

- Baseline: immutable c004 reference with 206 bones / 427 joint markers.
- Experiment: P004 translates each rib according to its vertebral reference-level change; P005 translates both complete clavicle→hand/arm control subtrees by the sternum movement to close relative SC/AC/GH control vectors.
- The first 7 pairs of ribs have 14 sternocostal markers in the control model. The audit uses their original rib-tail and sternocostal marker coordinates. Their true curved bone and costal cartilage surfaces are not yet available.
- Script: `scripts/anatomy_fit/p006_sternocostal_translation_feasibility.py` and 17 unit/mutation tests. It is a **read-only calculation**; no new P006 JSON skeleton is created.

## Derivation

For an individual rib i, let `d_i` denote the 3D translation of the rigid rib control segment between c004 and P004. Let `s` be the sternum body's single 3D translation. Since P004's markers move rigidly with the sternum, the rib-tail-to-sternal-control-vector changes by `s - d_i`. The code checks that the rib endpoints and marker movements actually meet these hypotheses before using the equation.

- The **least-squares optimum** over all 14 control corridors is the arithmetic mean of the 14 rib shifts: `s_LS = sum(d_i) / 14`.
- For any translation s, the triangle inequality yields `||d_a-d_b|| <= ||d_a-s|| + ||s-d_b||`. Therefore the largest remaining corridor mismatch for **any single translation** must be **at least** `max_(a,b)(||d_a-d_b||)/2`. This is a mathematically necessary lower bound, not a simulated anatomical constraint.

This cannot rule out a solution with realistic sternum **rotation**, rib-specific rotations, flexible costal cartilage, altered thoracic shape, or source-bound re-registration of landmarks. Likewise, a 5 mm vector-difference trigger is a software engineering change guard, NOT a clinical rib/sterna contact threshold.

## Verified GitHub CI results

GitHub Actions `37922260342`, P004/P005/c004 record replays:

| Numeric diagnostic | Result |
|---|---:|
| Number of rib–sternum control corridors | 14 |
| Existing heuristic sternum translation in model XYZ mm | (0, +5.388, −14.442) |
| Least-squares optimum translation mm | (0, +4.893, −16.328) |
| Difference in these translations | 1.951 mm |
| Largest absolute rib–sternum relative control-vector change under P004/P005 | 9.446 mm |
| Largest relative change under least-squares translation | 7.828 mm |
| Unavoidable best-possible maximum mismatch **lower bound** for any pure translation | 7.230 mm |
| Maximum pairwise difference between rib translations | 14.460 mm (ribs 2 and 7 on the left; mirrored right) |
| Engineering marker-vector change review threshold | 5 mm |
| Pure translation can meet all 14 guards | **NO** |

The P004/P005 rib/vertebral head and costovertebral/costotransverse markers still have zero engineering 3D-vector regressions. A separate 3D audit (`rib_3d_coupling_audit.py`) finds **6 of 14** rib–sternum proxy control vectors changed by more than 5 mm: first ribs ~9.446 mm, second ribs ~9.238 mm, seventh ribs ~6.160 mm on each side. The previous short endpoint-to-marker **distance length** summary had shown only a 3.6605 mm maximum; this proves why checking the full vector was necessary.

**All six focused test groups pass (13 + 14 + 17 + 15 + 17 + 17 = 93).** Code and CI do NOT evaluate whether any of those differences is within real cartilage physiological capacity.

## Findings and next highest-value actions

1. **Reject unqualified "just move the sternum" fixes.** P006 proves no pure translation can satisfy every pre-existing control-vector invariant at the 5 mm engineering review level.
2. Evaluate **rigid sternum rotation + translation** separately, with explicit rigid shape and marker ownership tests, to determine whether a six-degree-of-freedom sternum *control transform* better fits the new rib-level kinematics. Even if it does, it is not anatomical acceptance.
3. Model rib/costal-cartilage flexibility in a source-compatible movement system only when endpoints/surfaces are validated; do not deform ribs arbitrarily to make the lines connect.
4. Resolve source-compatible S1 depth, sternum-to-spine sagittal dimensions, per-level thoracic wedges and SC/AC/GH anatomically located articular surfaces. Check whole-body motion and realistic muscle/skin later.

### Reproduce

```bash
python3 -m unittest discover -s scripts -p 'test_rib_3d_coupling_audit.py' -v
python3 -m unittest discover -s scripts -p 'test_p006_sternocostal_translation_feasibility.py' -v
python3 scripts/anatomy_fit/replay_p004_coupled_thorax.py --out /tmp/p004_for_p006.json
python3 scripts/anatomy_fit/replay_p005_shoulder_chain.py --p004 /tmp/p004_for_p006.json --out /tmp/p005_for_p006.json
python3 scripts/anatomy_fit/p006_sternocostal_translation_feasibility.py \
  --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
  --proposal /tmp/p005_for_p006.json
```

Canonical promotion prohibited. Readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED**. Preserve Claude's `f3f725f4`, a003/c001–c004, P001, rejected P003, original model and all other agents' work.
