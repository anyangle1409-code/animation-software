# Rib 3D articulation audit — independent cross-check for P003 / P004 / P005

**Status: ENGINEERING DIAGNOSTIC ONLY. No anatomical target, new bone candidate or production acceptance.**

The preceding trunk preflight checked rib-head attachment **height**, but a displaced rib can accidentally pass that check even when its head moves forward, backward or laterally relative to the spine. This independent code closes that diagnostic blind spot without treating a straight control as real bony articulation.

## Source of truth and anatomical semantics

- Baseline: unchanged c004.
- P003: rejected spine-only disc repartition.
- P004: isolated rib-by-rib 3D translations based on the existing c004→P003 level displacement, plus an **unsourced heuristic** sternum shift.
- P005: the same ribs/sternum, with a full rigid clavicle/shoulder/arm hierarchy follow-through.
- **12 pairs of costovertebral joints (24)** have valid markers.
- **10 pairs of costotransverse joints (20)** have valid markers. The 11th and 12th ribs are floating ribs and **do not have costotransverse markers in the 427-complex inventory**. The validator deliberately never fabricates such markers.
- The first **7 pairs of ribs (14)** have a `sternocostal` marker carried by the sternum. Ribs 8–10 use costal margins rather than a direct equivalent; 11–12 have no direct sternal cartilage attachment.

## What is measured

`scripts/anatomy_fit/rib_3d_coupling_audit.py` independently derives these from bone control endpoints and recorded joint marker centres:

1. Each rib head's **full 3D relative vector** to the matching thoracic vertebral level (body centre or disc midpoint per existing project convention).
2. The relative 3D vector of each costovertebral or costotransverse joint marker to its rib head, ensuring a marker does not stay behind when the rib moves.
3. The recorded `sternocostal` marker minus each rib's *straight-control tail* for the first seven pairs. This is a rib-to-sternum **proxy corridor**, NOT anatomical costal cartilage geometry.
4. Rib control segment length changes.

All quantities are compared against the immutable c004 baseline; the 5 mm general-vector and 1 mm segment-length change detectors are **engineering diagnostic limits**, not physiological tolerances. These guards reject large relative changes for review and do not certify the baseline itself.

It is possible and expected that P004/P005 improve rib-head alignment while still failing the sternocostal-vector guard: one rigid sternum translation may not preserve the 14 separate costal-cartilage endpoints when the thoracic spine changes its curve.

## Tests and reproduction

```bash
python3 -m unittest discover -s scripts -p 'test_rib_3d_coupling_audit.py' -v
python3 scripts/anatomy_fit/replay_p004_coupled_thorax.py --out /tmp/hgpt_p004_3d.json
python3 scripts/anatomy_fit/replay_p005_shoulder_chain.py --p004 /tmp/hgpt_p004_3d.json --out /tmp/hgpt_p005_3d.json
python3 scripts/anatomy_fit/rib_3d_coupling_audit.py \
  --baseline ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json \
  --proposal /tmp/hgpt_p005_3d.json
```

The tests include a deliberate 20 mm depth-only displacement invisible to a height-only test, intentionally stranded costotransverse markers, misplaced sternal markers, rib length changes, malformed coordinates, and the real P003/P004/P005 geometric records.

Results always contain `contact_surfaces_verified: false`, `costal_cartilage_modelled: false`, and `canonical_promotion_allowed: false`.

## Limitations / next tasks

Mechanical rib control correspondence cannot solve anatomical rib curvature, costal cartilage variability, the true SC/AC/GH joint shapes, per-level vertebral wedging, thoracic AP depth, nor loaded exercise trajectories. No operation changes the source of truth or any approved asset.

The experiment must remain draft-only until the region's independently sourced geometry and 3D contact surfaces are validated. Preserve a003/c001–c004, P001, rejected P003, and Claude's branch. Current canonical readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED**.
