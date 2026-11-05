# Meshy male manual retopology: Task 3 continuation on the geometry proxy (5 November 2026)

**Status: WIP. Task 3 is NOT complete and NOT approved.** The face loop system, a left-side refinement after applying the mirror, and re-verification against the real source are still outstanding. Nothing is merged; production and PT-App are untouched.

## Inputs, verified in this session

| File | SHA-256 | Result |
|---|---|---|
| `HGPT_Meshy_Claude_START_HERE.zip` | `ebbc0c71…` | Extracted; the WIP checkpoint is inside. |
| `HGPT_Male_Retopo_03_TorsoHead_WIP.blend` (owner's checkpoint) | `d5de4b71…6cd6c6` | Matches the manifest. Opens in Blender 5.2.1 (saved in 4.3.34). **Unchanged; read-only.** |
| Geometry proxy, two parts | parts `9d1ede81…` / `4404e2e5…`; LZMA `689ecab1…`; raw `37ed0bfa…`; NPZ `1f811b0b…` | Every checksum passes. 169,017 vertices and 338,034 triangles; one watertight component. Bounds match `source_audit.json` exactly. |
| Original source `HGPT_Meshy_Male_Pro_1.82m_Clean_Unrigged.blend` (`b4151843…`) | — | **Still missing:** the five part ZIPs were not received. The proxy has no UVs, textures or materials. **Every result below must be re-checked against the real source before approval.** |

The geometry, `.blend` files and renders are **not** in git (licence and public repo). Only scripts and numeric reports are committed.

## Checkpoints (new files only)

1. **`HGPT_Male_Retopo_03b_TorsoHead_WIP_PROXY.blend`** (`2bb16dc4…`)
   - Made by the owner's `use_meshtarget_geometry_proxy.py`.
   - The scaffold's two Shrinkwrap modifiers now target the proxy.
   - **Projection verified:** median 1.0 mm (the modifier offset), p95 3.7 mm. Unprojected, the median is 15 mm.
2. **`HGPT_Male_Retopo_03c_TorsoHeadShell_WIP_PROXY.blend`** (`fe2ffe30…`)
   - Adds the new object `HGPT_Male_Task3_Shell` in `BODY_PRODUCTION`.
   - The scaffold object `HGPT_Male_Body_WIP` is kept unchanged.

## Method: designed loop layout, no auto-remesh

`scripts/retopology/build_task3_shell.py` is the design record. Every loop is placed explicitly from measured anatomy:

- **Torso:** horizontal loops every 2.5 cm, from 0.915 m (above the gluteal cleft; the pelvis is Task 5) up to the armpit.
- **Arm socket:**
  - loops every 1.2 cm from the armpit to the acromion;
  - on each loop, the socket edge is found where the surface meets the arm root (x = 0.19 m);
  - the outline is smoothed and kept at least as wide as the arm contact;
  - result: the front edge follows the deltopectoral line, the back edge the posterior deltoid border; no shell vertex lies on the arm.
- **Trapezius band:** 8 loops spaced evenly along the surface from the acromion loop to the neck. They are traced by a fan of rays from inside the upper chest, because this body's trapezius top is nearly flat: x 0.19 → 0.09 m within 2 cm of height.
- **Neck:** 5 loops up to a **jaw / skull-base loop**:
  - at the front it follows the jaw border measured on the source (1.578 m at the chin → 1.602 m at the jaw angle);
  - it rises behind the ear to the base of the skull;
  - the submental area and the jaw underside belong to the neck.
- **Head:** loops up to the brow; cranium loops around the head centre; the crown is closed by a **Coons-patch quad grid** (17 × 16), with no fan and no ladder.
- **Planned openings, kept as clean quad boundaries:**
  - arm socket: 64 edges per side;
  - face: jaw line to brow; this is where the scaffold's eye / mouth loop system goes;
  - ear base: 22 edges per side;
  - pelvis: 66 edges.
- **Clean-up:** an on-surface relax (8 iterations); the opening edges and midline vertices stay fixed.
- **Modifiers:** Mirror, then a nearest-surface Shrinkwrap, as in the owner's scaffold.

## Measured result (`audit_03c_task3_shell.json`)

**Topology (mirrored mesh):**
- 3,548 faces, **100 % quads**;
- 1 component; 0 wire edges, 0 loose vertices, 0 non-manifold edges;
- interior valence: 3,394 vertices with 4 edges and 4 with 3 (the crown-grid corners);
- open edges are **only** the planned openings.

**Edge length:** p5 7.3 mm, median 13.6 mm, p95 26.2 mm.

**Shape capture** (source to cage, away from the openings):
- raw cage: median 1.3 mm;
- after one subdivision with projection: **median 0.24 mm, p95 2.9 mm**.

**Quad shape** (poor = aspect > 4, or a corner < 30° or > 150°):

| Region | Faces | Poor | Worst corner |
|---|---|---|---|
| Torso | 1,090 | 16 | 20.5° |
| Socket band | 808 | 12 | 22.9° |
| Trapezius band | 606 | 20 | 16.8° |
| Head / neck | 680 | 24 | 16.6° |
| Crown | 364 | 2 | 48.8° |

## Findings

- **The source is not mirror-symmetric.**
  - The head's centre is 4–5.5 mm towards −x, and the head is wider on −x.
  - A plain mirrored copy lies 6.4 mm (median) inside the left side of the head.
  - With the Shrinkwrap after the Mirror, the left side lands on the surface. It is still slightly worse than the right: 53 poor quads against 38, a worst corner of 9°, and a shortest edge of 1.1 mm.
- **This WIP stage was rebuilt, not just extended.** The scaffold's loop plan (openings, eye / mouth / ear guide rings, an open pelvis) was followed. The scaffold's coarse cage (faces of about 5 cm) and its upper-back gaps were rebuilt at production density in a new object; the scaffold itself is preserved.

## Outstanding (Task 3 is not complete)

1. **Face loop system:** eye rings, mouth rings, nasolabial and nose loops, bridged into the face opening. Build it from the scaffold's `FLOW_EYE_*`, `FLOW_MOUTH_*`, `FLOW_NOSE` and `FLOW_JAW` guides.
2. **Ear:** a separate ear mesh, or a closed ear-base cap.
3. **Left side:** apply the mirror, then relax and inspect the left side on its own.
4. **Review against the 105° and 170° shoulder poses:** this needs the arm (Task 4) and the rig.
5. **Re-verify** everything against the real source once the five part ZIPs arrive.

## Update: face loop system (03d → 03f, 5 Nov)

**New checkpoints** (new files; nothing earlier is overwritten):

| Checkpoint | SHA-256 | What it adds |
|---|---|---|
| `HGPT_Male_Retopo_03d_TorsoHeadShell_DenseHead_WIP_PROXY.blend` | `06d52e04…` | The shell with ~8 mm head loops; face opening widened to the cheekbone (54.5°) and the forehead loop (~1.743 m); every vertex tagged with its loop and column (`t3_row`, `t3_col`). |
| `HGPT_Male_Retopo_03e_TorsoHead_FaceLayout_WIP_PROXY.blend` | `3f5376c6…` | The face layout, first version. |
| `HGPT_Male_Retopo_03f_TorsoHead_FaceLayout_Relaxed_WIP_PROXY.blend` | `e24d800d…` | **Current.** The face layout plus a head-wide on-surface relax. |

### Finding: the face is not centred on the body's midline
Measured on the proxy, the face midline runs from x −4 mm at the chin to −8.5 mm at the nasal bridge:
- nose tip at x −6.5 mm;
- inner eye corners at +3 and −20 mm;
- mouth corners at +20 and −35 mm.

So the shell's Mirror + Shrinkwrap is **applied** in a full-body object, `HGPT_Male_Task3_Body`. The face is then built across the whole face, around its own measured midline. The scaffold's eye and mouth guide rings were not used for positions: they sit at the temple (eye ring centre x ≈ 60 mm) and about 3 cm behind the lips. Their loop plan was kept.

### Face design (`scripts/retopology/build_task3_face.py`)
- **Half-face grid:** each half-face is a grid between the shell's face-opening boundary (jaw loop, forehead loop, cheekbone column) and a designed midline chain (chin, lips, philtrum, nose, glabella, forehead). The chain follows the measured midline.
- **Eyes:** a 6 × 3-cell rectangle per eye is replaced by 3 concentric rings, ending on the measured eyelid opening:
  - inner corner (3, 1693) mm, outer corner (35, 1695) mm;
  - upper lid (16, 1698.5) mm, lower lid (19, 1691) mm;
  - left eye mirrored about the face midline.

  The rings map to the lids by distance along the outline, and the opening is closed by a grid (the sculpt's lids).
- **Mouth:** a half-rectangle on each side of the midline is replaced by 3 half-rings ending on the lip border:
  - corners (20, 1628.5) and (−35, 1628.5) mm;
  - upper border 1637 mm, lower border 1617 mm.

  The lips are closed by a grid whose middle row is the lip line (1627.5 mm).
- **Symmetry:** the topology is identical on both sides (the left side reuses the right side's rectangle indices).

### Measured result (`audit_03f_face_layout.json`)
- **Openings:** only the pelvis, both arm sockets and both ears; the face is closed.
- **Topology:** 4,454 faces, 100 % quads, 1 component; 0 non-manifold, wire or loose elements.
- **Poles:** 16 three-edge and 12 five-edge vertices, at the corners of the eye and mouth rectangles and the crown grid.
- **Shape capture** after one subdivision and projection: median 0.23 mm, p95 2.7 mm.
- **Poor quads:** 84 of 4,454 (1.9 %): crown 0, trapezius 9, socket 10, torso 17, head/neck 48.
- **Sharp corners:** 9 quads have a corner under 15° (worst 6.1°), all at the eye and mouth corners, mostly on the asymmetric left side.

### Still open (Task 3 not complete)
1. **Nose:** loops around the nostrils and the nose tip. At the current density the tip and wings poke through.
2. **Eye corners:** a cleaner closing grid, with its middle row on the lid line; the left-eye outline measured on the left eye itself rather than mirrored.
3. **Ears:** separate ear meshes, or caps over the ear openings.
4. **Hair:** a separate layer (the sculpted front hair tuft currently pokes through the scalp cage).
5. **Re-verification** against the real source (the five part ZIPs are still missing).

## Update: nose loops and left-eye outline (03g, 5 Nov) — mixed result

**Checkpoint:** `HGPT_Male_Retopo_03g_TorsoHead_FaceNose_WIP_PROXY.blend` (`8173ad55…`), a new file. 03f is kept for comparison.

**What changed:**
- **Mouth and nose share one builder.** For each, a half-rectangle at the midline is replaced by half-rings down to the measured outline, closed by a grid.
- **Nose outline, relative to the face midline:**
  - top of the nasal bridge at z 1670 mm;
  - top of the nostril wing at (12, 1666) mm;
  - widest point of the wing at (17.5, 1655) mm;
  - base of the wing at (15, 1649) mm;
  - base of the nose (subnasale) at z 1645.5 mm.
- **Left eye** measured on its own: inner corner (−20, 1692.5), outer corner (−50, 1695.5), upper lid (−34, 1699), lower lid (−36, 1691) mm.
- **Rings:** the eye, nose and mouth rings are now held fixed by the relax passes (relaxing collapsed neighbouring rings into the nose–lip and eye-corner creases). The relax inside the face projects along the front direction. Eye rings are evenly spaced.

**Measured (`audit_03g_face_nose.json`):**
- 4,464 faces, 100 % quads, closed face, 1 component.
- 20 three-edge and 16 five-edge vertices, all at rectangle corners.
- **Shortest edge 1.5 mm** (03f: 0.6 mm; the trial without fixed rings: 0.1 mm).
- Shape capture: median 0.22 mm, p95 2.7 mm.
- **Poor quads: 132**, of which head / neck 96. This is up from 84 in 03f, because the fixed ring quads are thinner.
- The worst corner (2.3°) is in the nostril-sill strip under the nose.

**Visual verdict:**
- **03g is not yet better than 03f.**
- The nose half-rectangle reads as a box, and the nose tip still pokes through the cage.
- The eye-closing grid and the inner rings crinkle inside the 7.5 mm eye opening.
- Under the chin, the cage dips below the surface in places.
- **The eye and nose regions are not production quality in either checkpoint.**

**What it needs:**
- Eyes: one quad loop per lid (upper and lower lid rings meeting at the eye corners) instead of a closing grid, plus a higher ring count (24 or more).
- Nose: a nose patch with loops around the nostril wings, built from the nose's own side profile (it projects 12 mm in front of the lip) rather than front-projected cells.
- Re-checking both against the real source.
