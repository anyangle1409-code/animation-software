# ORIGINAL_v1 foot C4 — provisional development candidate (Claude, 14 Oct 2026)

**Status:** PROVISIONAL DEVELOPMENT CANDIDATE, not accepted. The frozen a003 is unchanged.

**Basis:** the owner's 14 Oct instruction to continue with the 280 mm C3W skeleton/mesh as a provisional candidate. C4 keeps C3W's skeleton (C3, 279.9 mm) and **replaces C3W's mesh stage**, because that stage has a defect found today (below).

**Files:**
- Builder: `scripts/build_original_foot_c4_candidate_blender.py`.
- Native tests: `scripts/blender_tests/test_original_foot_c4_candidate.py` (8 pass locally, including an exactly identical rebuild from C3).
- CI: `.github/workflows/original-foot-c4.yml`.
- Blend and report: `ORIGINAL_V1_WORK/anatomy/candidates/claude_foot_20261013/c4/` (`HGPT_ORIGINAL_V1_FOOT_C4_CLAUDE.blend`, SHA-256 `b1ecd3e5…05aa`; parent C3 `7545be4a…21f9`).

## Defects found in my earlier candidates (corrected here)

1. **C3W crumpled the little toes.** Its ball-breadth stage scaled x about each slice's foot centre, with a weight fading along y. Because the metatarsal-head line is oblique, each lesser toe got a different sideways shift at its root than at its tip. The shear crumpled toes 4–5 (visible in `breadth/sheets_c3w/*`). It also moved toes 1 and 5 off their unchanged phalanx stations. My C3W check counted self-intersecting pairs, which stayed 0, so it did not catch this. **C3W should not be used.**
2. **"Narrow heel, 58–61 mm" is withdrawn.** That figure was a vertex extent below 40 mm height on a sparsely sampled heel. True plane sections (edge intersections) give **75–81 mm** at 20–30 mm behind the ankle joint and **82.9 mm** at the widest point posterior to the malleoli. Against ANSUR II at 1.82 m (73.7 ± 5.3 mm) that is not narrow (up to +1.75 SD), and the exact value depends on the landmark. The heel is **not changed**.
3. **Ball breadth by true sections is 96.7 mm on C3,** not the 94.6 mm vertex extent reported before. The −1.6 SD deficit to ANSUR (104.1 ± 4.7 mm) is still real, so C4 widens it.

## What C4 changes (mesh-only)

Only x moves; y and z never change. Topology, weights, rigs and the 206-bone master are untouched beyond C3's foot re-partition. Every shape key gets the same delta, and the result is mirrored exactly.

- **Toes, relational fit (no invented toe sizes):**
  - The five toe tubes are found from the mesh itself: the connected components of the forefoot skin anterior to y = −170 mm, grown back to the webs geodesically over mesh edges. Labels cannot jump a gap, unlike nearest-axis assignment, which misassigned skin in Work's toe trial.
  - On C3 the lesser toes are 9–12 mm wide but 20–23 mm tall, with 2.7–2.8 mm minimum gaps (hallux–toe 2: 0.7 mm).
  - Each toe's edges move apart **slice by slice, from true sections on a 0.5 mm grid**. The move is half the *local* gap minus 0.6 mm, using a ±3 mm window minimum so it never over-closes. It holds past a shorter neighbour's tip and fades in over 8 mm from the web. Within a slice the map is affine in x, so there is no shear along a toe.
  - **Result:** mean widths 26.0 / 14.8 / 11.1 / 8.2 / 7.9 → **26.5 / 16.1 / 13.5 / 10.2 / 9.3 mm**; minimum gaps along every toe **0.67 / 0.71 / 0.74 / 1.0 mm**.
- **Ball breadth to ANSUR:** only the skin medial of the first and lateral of the fifth metatarsal-head stations moves outward (3.9 mm each side), solved on true sections: **96.7 → 104.1 mm**. Toe tubes are excluded, so the toes stay on their stations.

## Checks (builder, then re-measured by the native tests)

| Check | Result |
|---|---|
| Foot self-intersecting pairs | 0 → **0** |
| Reversed triangles | **0** |
| Foot area ratio range | 0.87–2.09 |
| Bone stations inside the skin | all |
| Mirror symmetry | exact (0.0 m) |
| Lowest point, foot length | unchanged (0.0 mm, 279.9 mm) |
| Ball breadth (sections) | 104.1 mm |
| Heel breadth (sections) | 82.9 mm, unchanged |

**Posed sweep** (`c4/foot_posed_sweep_c4.json`; foot −30…+20°, toes −50…+30°): 0 collapse, 0 stretch > 2 and 0 self-intersection on a003, C3W and C4. The minimum area ratio at +30° toe is 0.687 for C4, against 0.530 for C3W.

## Visual evidence (phone sheets)

- `c4/sheets_c3w_vs_c4/`: six foot views; the crumpled little toes are gone.
- `c4/sheets_a003_vs_c4/`: six foot views against the frozen original.
- `c4/fullbody_a003_vs_c4/`: front, rear, both sides and both three-quarter views. Only the feet differ; height is 1.82 m.

## Still open (not claimed)

- **Toe cross-sections are still tall** (lesser toes about 20 mm high for 10–13 mm wide). No sourced toe height or breadth was retrievable here: the 3D-scan studies that hold them were behind blocked full text. So no height change was made.
- **Nails:** absent.
- **Individual toe articulation:** still the 67-joint single toe control. Work's 95-control trial keeps its own failing gate; individual toes remain a runtime-contract question for Work (F5).
- **The ANSUR heel landmark wording** was not retrievable; the section definition used is disclosed.

## C5 = C4 + plantar heel contact (same day)

**Defect, inherited from the frozen a003.** In neutral standing, no heel skin behind the ankle-joint centre (AJC) is within 2 mm of the floor.
- On true sections, the plantar contour is lowest 10 mm in front of the AJC (1.2 mm) and rises behind it. C4 measures 6.6 / 9.9 / 13.2 / 19.3 / 27.9 mm at +10 / +20 / +30 / +40 / +50 mm; a003 is worse (26.7 mm at +30).
- The standing foot therefore rocks on its midfoot and forefoot.
- A standing foot bears weight on the heel under the calcaneal tuberosity and on the first and fifth metatarsal heads (the plantar tripod). That is the qualitative reference used; no numeric heel-pad target.

**Change.** `scripts/build_original_foot_heel_contact_blender.py` moves z only, mesh-only, mirrored, and updates every shape key.
- Target sole: on the floor from 10 mm in front of the AJC, then a 35 mm round-off up to the heel back.
- Each section is lowered rigidly to that target, with a vertical fade (full to 15 mm above the sole, zero at 60 mm). The heel pad thickens and the calcaneus stays inside. A 12 mm blend in front of the flat start avoids a midfoot step, and nothing goes below the floor.
- **Variants measured on side renders:**
  - R = 22 mm left a boxy heel corner;
  - R = 45 mm left the pad 2–4 mm off the floor at +20/+30 mm;
  - R = 35 mm was chosen.

**Result.** `c5/HGPT_ORIGINAL_V1_FOOT_C5_CLAUDE.blend`, parent C4.
- Profile at +10 / +20 / +30 / +40 / +50 mm: **0.2 / 0.6 / 1.1 / 5.7 / 14.2 mm**.
- Heel contact vertices (within 2 mm): 0 → 6. Metatarsal-head (11), toe (41) and lateral-midfoot (3) contacts are unchanged.
- 0 self-intersections, 0 flipped faces, area ratios 0.63–1.85, exact mirror, every station inside the skin.
- Posed sweep (`c5/foot_posed_sweep_c5.json`): 0 collapse, stretch or intersection. The minimum area ratio at +20° foot is 0.79 (C4: 0.88).
- Native tests: `scripts/blender_tests/test_original_foot_c5_heel_contact.py`, 5 pass, also in the C4 workflow.

**Evidence:**
- `c5/sheets_a003_vs_c5/` and `c5/sheets_c4_vs_c5/`: six foot views each;
- `c5/fullbody_a003_vs_c5/`: six full-body views.

**Still open:**
- The heel back stays faceted: the a003 heel is low-poly, and no topology change was made.
- The 2 "arch" contact vertices are the inherited medial midfoot skin. A real arch is off the floor, but no arch-height source was used, so it is left as is.
