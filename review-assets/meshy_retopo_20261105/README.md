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
