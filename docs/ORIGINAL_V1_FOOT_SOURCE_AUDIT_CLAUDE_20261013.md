# ORIGINAL_v1 foot: source audit and toe-grounding candidate C2 (Claude, 13 Oct 2026)

Branch `claude/original-v1-foot-shape-20261013` (from `codex/claude-original-v1-handoff-20261013` @ `bd162c50`).
Parent model: `ORIGINAL_V1_WORK/anatomy/audit/HGPT_ANATOMICAL_AUDIT_r95_a003.blend`, SHA-256 `670a37bf…cbbe56` (verified before and after; never modified).
Status: **C2 is a review candidate, not accepted or promoted.** No skeleton, weights, rig or production file was changed.

## 1. Owner findings addressed (PR #81, comment 6120513138)

| Finding | Result |
|---|---|
| Toes point upwards / float | **Root cause found and corrected in candidate C2** (section 3) |
| Foot ~30.9 cm, looks long | **Confirmed long; cannot be shortened by a mesh edit. Needs an owner decision on the frozen skeleton** (section 2) |
| Foot shape/toe silhouette | Pads, tip rounding and floor contact improved; toe girth, spacing and nails are **still open** (section 5) |

## 2. Foot length: measured, not assumed

These are ANSUR II male standing values at 1.82 m: an OLS fit on stature, n = 4,082 (the public CSV in `ORIGINAL_V1_WORK/anatomy/sources/ansur2/`).

| Measure | ANSUR prediction at 1.82 m (± residual SD) | a003 model |
|---|---|---|
| Foot length | 279.9 ± 9.1 mm | **309.2 mm mesh** (+29.3 mm, about +3.2 SD) |
| Ball-of-foot length | 207.4 ± 7.8 mm | 229.2 mm heel to the MT1 distal station (+21.8) |
| Foot breadth | 104.1 ± 4.7 mm | 96.7 mm (−7.4) |
| Heel breadth | 73.7 ± 5.3 mm | not measured |
| Lateral malleolus height | 75.4 ± 5.0 mm | 70.0 mm (fibula station) |

The extra length sits in the skeleton, not the skin:
- The hallux distal-phalanx station is 304.2 mm from the heel skin, leaving only 5 mm of soft tissue beyond the bone tip.
- About 75% of the excess is between the heel and the MTP joint (+21.8 mm); the remaining +7.5 mm is between the MTP joint and the tip.
- The earlier committed `canonical_foot_proportion_audit_v1.json` found the a003 metatarsals plausible under stature-aware regressions. It left the toe-phalanx length and the "partition of excess length" unresolved, and that is still the case.

**Update (same day):** the owner said "continue with skeleton". Skeleton candidate C3 (279.9 mm, ball of foot 207.4 mm, heel provisionally 60 mm behind the ankle) is in `docs/ORIGINAL_V1_FOOT_SKELETON_C3_CLAUDE_20261013.md` and awaits sign-off.

**Owner decision required (originally asked):** should the frozen 206-bone forefoot and hindfoot chain be revised towards an ANSUR-consistent foot length of about 280 mm (±9 mm)?
- The skeleton-first rule forbids a mesh-only shortening: the bones would end up outside the skin.
- A revision would need new tarsal, metatarsal and phalanx stations, plus matching changes to the runtime `foot_*`/`toe_*` controls.
- The tarsus is currently BLOCKED in the readiness record.
- Evidence: `ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013/foot_source_proportion_audit.json`. Script: `scripts/audit_original_foot_source_proportions_blender.py`.

## 3. Why the toes point up

`build_toes()` in `scripts/original_v1_o2_body.py` lofts each toe as a straight tube whose ring centres sit 10–13.5 mm above the floor and caps it with a dome.

In the native model, the lowest toe skin is **8.3 mm above the floor** on every digit (both feet). The toes therefore read as raised, straight tubes even though the skeleton toe chains are almost level: they descend from 22 mm at the MTP joints to 14–18 mm at the distal-phalanx tips and run through the middle of each skin digit.

## 4. Candidates

### C1: rejected

C1 bent each digit down about a floor axis (7–13°).
- The verifier found the distal-phalanx tips of toes 2–5 **outside the skin** on both feet.
- Bending lowers the whole digit below its frozen bones, so C1 breaks the skeleton-first rule.
- Kept for reproducibility only (`--variant c1`, `c1_rejected_*.json`).

### C2: review candidate

`HGPT_ORIGINAL_V1_FOOT_SHAPE_C2_CLAUDE.blend`, SHA-256 `9d1571c3…c453a`.

C2 leaves each digit where its skeleton is. It expands only the skin **below the skeleton axis** downwards:
- The pad touches the floor under the middle of the distal phalanx.
- The pad rises to 3 mm under the phalanx tip.
- The expansion fades by 85% towards the skin tip, so the tip still curves up and stays rounded.
- The expansion profile is smoothstep in depth, so there is no crease at the axis and the pad is rounded rather than keeled.
- The weight ramps up from the web line, which keeps the sulcus behind the toes at 6–7 mm.

Scope of the edit:
- Mirrored exactly to the other foot.
- The same offset is added to every shape key.
- 834 vertices changed; the largest move is 9.1 mm, all of it vertical.

Script: `scripts/build_original_foot_shape_candidate_blender.py`. Report: `c2_build.json`.

## 5. Acceptance tests

Run with `scripts/verify_original_foot_shape_candidate_blender.py`; full output in `c2_verify.json`. **Verdict: PASS.**

| Check | Result |
|---|---|
| Topology, vertex groups, every weight, modifiers, object transform | identical |
| Both armatures (206 source, 67 runtime): heads, tails, parents, matrices | identical |
| Vertices moved outside the forefoot box (abs(x) > 20 mm, z < 70 mm, y < −188 mm) | 0 |
| Shape-key relative deltas (6 corrective keys) | unchanged (max change 0.0) |
| Left/right symmetry | 3e-8 m |
| Foot length / breadth | 309.2 / 96.7 mm (unchanged by design, see section 2) |
| Lowest toe skin above the floor | 8.3 → 0.03 mm, both feet |
| Lowest point of the body | unchanged (−0.0002 mm) |
| 76 forefoot skeleton stations (metatarsal and phalanx heads/tails, both feet) inside the skin | 76/76 (parent 76/76; C1 failed 8) |
| Rest triangle-area ratio, changed faces | 0.72–2.84 (the plantar pads are stretched up to 2.8×; a UV/texture-stretch concern for any skin texture, not a skinning one) |
| Posed checks (runtime `toe_*` ±30°, `foot_*` +20/−30° about the local X axis, both sides) | toe-region deformation ratios **identical** to the parent (weights unchanged) |
| Posed lowest point | equal to the parent in the toe −30° and foot −30° poses; 4.8 mm (toe +30°) and 6.3 mm (foot +20°) lower than the parent in the poses that already push the toes 29–76 mm through the floor with the leg held fixed |

The posed tests are forward-kinematics checks with the leg fixed. They do not include ground contact or IK, and they say nothing about walking realism.

## 6. Still open (not claimed)

1. **Foot length 309 mm**: owner decision, section 2.
2. **Toe girth and spacing**: the lesser toes are 9–11 mm wide at mid-length with 1.7–3.1 mm gaps and still look finger-like from the front. Widening them interacts with the gaps and needs a separate bounded pass.
3. **Nails**: the mesh has no nail geometry or separate material. Nail orientation cannot be assessed until nails are modelled.
4. **Articulation**: there is one runtime `toe_*` control per foot (all five toes move as a block), and there is no separate MTP or interphalangeal motion. A real walking toe-off needs at least MTP dorsiflexion of about 50–60° with deformation tests; this is not done.
5. **Foot breadth**: 7.4 mm narrower than ANSUR. Not changed here.

## 7. Review images (phone-sized)

Folder: `ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013/`.
- `review_sheets/*_before_after.jpg`: before above, C2 below, with measurements. Six views: lateral, medial, top, sole, front and three-quarter.
- `renders_before/` and `renders_c2/`: the individual views plus `views.json` (camera, scale and clip).

All views are Workbench orthographic renders of the real model (no painting or retouching), drawn with `scripts/render_original_foot_views_blender.py` and composed with `scripts/compose_original_foot_review_sheet.py`.

## Reproduce

Run from a directory that does not contain the scripts (bpy as a Python module):

```
python3.13 scripts/audit_original_foot_source_proportions_blender.py --blend <a003> --ansur ORIGINAL_V1_WORK/anatomy/sources/ansur2/ANSUR_II_MALE_Public.csv --out audit.json
python3.13 scripts/build_original_foot_shape_candidate_blender.py --blend <a003> --expect-sha 670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56 --out c2.blend --report c2_build.json
python3.13 scripts/verify_original_foot_shape_candidate_blender.py --parent <a003> --candidate c2.blend --out c2_verify.json
python3.13 scripts/render_original_foot_views_blender.py --blend c2.blend --body HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE --out renders_c2
python3 scripts/compose_original_foot_review_sheet.py --before renders_before --after renders_c2 --verify c2_verify.json --out review_sheets
```

Environment note: this run used Blender 5.2 as a Python module in a cloud container, not the owner's laptop. The starter-ZIP trial BLENDs were not reachable, so only the committed a003 model was used.
