# c003: coupled upper-thorax and shoulder reconciliation to ANSUR (audit candidate, not canonical)

**Identity:** `r95_a003_shoulder_thorax_c003_ansur_coupled`
**Status:** `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`. `freeze_ready=false`; not promoted.
**Policy:** `SHOULDER_THORAX_ANSUR_COUPLED_C003`, recorded in `canonical_target_selection_v1.json` `owner_decisions`. For this audit candidate, the internally coherent ANSUR measurements govern over the inherited a003 notch height. The decision was made on the user's behalf from the audit evidence.

a003, c001, c002 and production are untouched; their hashes are test-enforced. ("c003" is an audit ID and is unrelated to the reserved `HGPT_CANONICAL_SKELETON_FIRST_c001`.)

## What moved, and why (all from a003, sha256 `11712ba3e105aa88…`)

| Element | Change | Basis |
|---|---|---|
| Sternum (rigid; length and inclination are a003's) | z −24.67 mm, y +14.66 mm (posterior). IJ 1519.2 → **1494.5** mm; PX 1316.1 → 1291.4 mm | z: ANSUR suprasternale at 1.82 m. y: solved as the least costal-cartilage deformation under pump-handle rib rotation; the sternum moves posteriorly as it descends. |
| Ribs 1–7 (both sides) | Pump-handle rotation 8.4–19.1° about the mediolateral axis through each rib head | Keep each costal cartilage (costochondral → sternocostal). Worst vector change 4.4 mm (rib 1); the rest ≤ 1.6 mm. |
| Ribs 8–10 | 8.6–9.7°, following the rib above through the interchondral joints | Change ≤ 0.22 mm |
| Ribs 11–12, spine, skull, hyoid, pelvis, legs | **unchanged** (identical to a003) | — |
| Clavicles and scapulae | Replaced: reconciled girdle on the new IJ with bony pitch 7.04°; SC at the Seth relation | Least joint departure from the Matsumura male standing means, with the ANSUR acromion (Lee LM25–LM27 border crossing of the clavicle-axis line) exactly at **1497.7** mm |
| Arms (humerus subtree) | Translated rigidly with GH: (∓25.5, −27.4, +8.8) mm | — |

In total, 85 bones and 172 markers moved; every one is listed in `candidate_record.json` (`moved_bones`, `moved_markers`).

**Before and after, left side (mm):**

| Point | a003 | c003 |
|---|---|---|
| SC | (25.0, −27.9, 1514.2) | (25.5, −22.7, 1501.3) |
| AC | (240.7, 25.6, 1497.5) | (169.2, 24.4, 1498.6) |
| GH | (218.9, 32.5, 1462.4) | (193.4, 5.1, 1471.2) |

| Measure | a003 | c003 |
|---|---|---|
| Clavicle chord | 222.9 mm | 151.3 mm |
| Bilateral AC distance | 481.4 mm | 338.4 mm |
| Bilateral GH distance | 437.8 mm | 386.9 mm |

## Acceptance checks (all PASS; `candidate.acceptance_checks`)

| Check | Result |
|---|---|
| ANSUR targets | IJ 1494.5 (error 0); acromion 1497.7 (error 0); within-subject acromion − IJ 3.2 mm vs 3.1 ± 13.9 (z 0.007) |
| SC closure | SC − IJ in the thorax frame equals the Seth relation exactly; clavicle head = SC marker |
| Angles (z vs Matsumura male) | Clavicle elevation **1.1° (z −1.72, low end)**, retraction 18.1° (z −0.81); scapula IR/UR/AT 30.3/8.0/7.6° (z 0.21/−0.41/−0.48); χ² 3.4. Screening line \|z\| ≤ 2. |
| Rib–sternum continuity | Costovertebral joints unchanged; cartilage and interchondral links as above |
| Cervical and axial continuity | All vertebrae, sacrum, coccyx, occipital and hyoid identical. ANSUR cervicale − new IJ = 80.7 mm, matching the living C7 − IJ relation (80.7 ± 11.4) |
| Unrelated bones | 121 bones identical to a003 |
| Stature | Max and min bone heights identical |
| Joint closure | SC, AC, GH and costovertebral endpoint-marker gaps all 0; arm bone lengths preserved |
| Collisions (stick axes) | No new axis intersections below 1 mm; the closest moved pairs are unchanged hand pairs |
| Bilateral mirror | Girdle and arm exact; ribs no worse than a003's inherited 0.04 mm asymmetry |

**Also passing:**
- **CP2:** verdicts identical to a003 (the inherited disc-gap FAIL and disc-clearance UNVERIFIED).
- **CP3 round trip:** PASS (5.9e-8 m bones, 2.0e-7 m markers).
- **Isolated movement suite** (`../../runs/isolated_bone_only_c003_shoulder_thorax_001/`): 135/135 integrity; 41/43 mirror (the same two side-specific hip pairs); shoulder-complex, scapulothoracic-rhythm and rib pump-handle tests PASS.

## Known defects and tensions (honest limits)

- **Clavicle elevation** of 1.1° is at the low end of the source (8 ± 4°).
- **Notch vertebral level:** the IJ now sits near the T3/T4 disc relative to the retained spine, one level below the supine CT finding T2–T3 (Razzouk 2023). This is consistent with the living C7–IJ relation, but standing vs supine is unverified.
- **Notch-to-spine depth** (IJ to T3 body) changes from 84.4 to 69.8 mm. No sourced comparator is committed.
- **The a003 sternum is long** (213 mm stick; REOPEN). PX moves down with it and is not corrected.
- **Rib rotations of 8–19°** are resting-geometry corrections of a003's straight-chord ribs; rib geometry remains BLOCKED.
- **The acromion mapping is bracketed:** using the lateral-line crossing instead puts the acromion at 1502.2 mm (+4.5).
- **Unchanged from a003:** the mesh is not refitted; SC/AC/GH marker frames keep a003 orientations; a003 arm lengths (and the short-forearm issue) are retained.
- **The vertical-only sternum alternative was rejected:** it gives 11–15 mm of cartilage mismatch and rib 7 crowding rib 8.

## Evidence

**`review/` (58 JPEGs, `manifest.json`):**
- `views_c003/`: 20 views (full body front/back/both sides/three-quarters; upper body front/back/overhead; both shoulders front/side/rear/overhead; both axillae).
- `poses_c003/`: 4 illustrative GH poses.
- `four_way/`: per-view a003 | c001 | c002 | c003 comparisons.
- `sheets/sheet_four_way_{body,shoulder_left,shoulder_right,overhead,poses}.jpg` and the `sheet_c003_*` sheets.

**Movement clips:** `../../runs/isolated_bone_only_c003_shoulder_thorax_001/clips/` holds a003-vs-c003 GIFs and keyframe sheets of solver-keyed scapular-plane elevation (both sides) and GH elevation, front and rear.

## Reproduce

```
python3 scripts/anatomy_fit/build_shoulder_candidate_c003.py --out <new>
python3.13 scripts/anatomy_fit/build_shoulder_candidate_blender.py --source-blend ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend --record <record> --out-blend <new>
python3 scripts/test_shoulder_thorax_c003.py      # 16 tests
```

| File | sha256 (first 16) |
|---|---|
| `candidate_record.json` | `3eb4fa1e2f7d815e` |
| `HGPT_ANATOMICAL_AUDIT_r95_a003_shoulder_thorax_c003_ansur_coupled.blend` | `3962215043cebbcf` |
