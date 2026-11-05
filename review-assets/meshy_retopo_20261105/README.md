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

## Experiment 03h: lid-line head row and profile-built nose (5 Nov) — rejected

**Checkpoint, kept for the record:** `HGPT_Male_Retopo_03h_EXPERIMENT_EyeRows_NoseProfile_WIP_PROXY.blend`.

**Changes tried:**
- **Head loops** re-spaced to 1.682 / 1.694 / 1.706 m, so the eye rectangle spans 2 rows and its closing grid's middle row lies on the lid line.
- **Nose rows** placed along the traced side profile (base of the nose → underside → tip → bridge), with the side columns swept by rays from inside the nose root.

**Result:** (`audit_03h_experiment.json`)
- 4,394 quads, closed face, 1 component.
- **143 poor quads.**
- **The eyes got visibly worse:** the 24 mm-tall rectangle around a 7.5 mm opening turns the rings into spokes at the eye corners.
- **The nose still reads as a box.**

**Conclusion:**
- 03f remains the best face. The scripts at commit `999b04ec` reproduce 03f/03g; the current scripts reproduce 03h.
- Three rounds of procedural face construction have not reached production-quality eyes and nose.
- The method decision is with the owner.

## 03i: closed-eye lid loops and smoothed rings (5 Nov) — current best face

**Owner decision:** keep building the face procedurally; no template wrap. **Checkpoint:** `HGPT_Male_Retopo_03i_TorsoHead_FaceLidLoops_WIP_PROXY.blend` (`849c8fec…`), built from the 03d shell. The shell script's head loops are restored to the 03d values.

**What changed:**
- **Eyes, closed-eye lid topology:**
  - a lid-line chain of 8 vertices;
  - a lid-margin ring of 18 vertices: the inner and outer eye corners, plus 8 vertices on the upper lid and 8 on the lower lid, evenly spaced on the measured lids;
  - one quad spans each eye corner, so the lid line ends in a three-edge vertex;
  - upper and lower strips of quads close the eye along the lid line (no grid inside the opening);
  - 3 rings blend out to the grid rectangle.
- **Ring smoothing (eyes, nose, mouth):** the rings are smoothed in 2D (each vertex moves towards the average of its ring and radial neighbours; outlines fixed), blended 70/30 with the straight blend, and kept at least 1.2 mm apart. This removes the spokes and the box look.
- **Grid around the eyes:** grid vertices next to the eye rings may now relax (front-ray projection), which removes the crumples at the rectangle corners.
- **Nose:** 2 rings plus the profile-built fill.

**Measured (`audit_03i_face_lid_loops.json`):**
- 4,480 faces, 100 % quads, closed face, 1 component; 0 non-manifold, wire or loose elements.
- 20 three-edge and 16 five-edge vertices, at the rectangle corners and lid-line ends.
- **Shortest edge 1.17 mm.**
- Shape capture: median 0.22 mm, p95 2.7 mm.
- **Poor quads: 117** (03f 84, 03g 132, 03h 143); head / neck 81.
- **13 quads have a corner under 15°** (worst 4.1°), almost all in the nostril-sill strip under the nose (z 1647–1654 mm).

**Visual:**
- Round, concentric loops around both eyes, a rounded loop around the nose base and nostril wings, and round mouth loops, blending into the grid.
- **Still open:**
  - the nose tip and nostrils show through the cage (it is coarse: 3 columns per side); one subdivision captures the shape;
  - the nostril-sill strip has sharp quads;
  - the cage dips under the jaw edge below the chin in places;
  - ears are not built; hair is not on its own layer;
  - left-side asymmetry refinement;
  - re-verification against the real source.

## 03j: ears closed, first pass (5 Nov)

**Checkpoint:** `HGPT_Male_Retopo_03j_TorsoHead_FaceEars_WIP_PROXY.blend` (`8f0c2008…`), built from 03i by `scripts/retopology/build_task3_ears.py`.

**Method:** each ear opening (6 × 9 cells) is filled with:
- 3 concentric rings of 30 vertices (the helix band);
- a 6 × 9 grid filled from the four sides of the innermost ring (bowl and antihelix);
- projection onto the source by sideways rays from outside the head, then a light relax.

**Measured (`audit_03j_face_ears.json`):**
- 4,768 faces, 100 % quads, 1 component.
- **Open edges: only the pelvis (66) and the two arm sockets (128). The head is closed.**
- 28 three-edge and 24 five-edge vertices (the ear grid adds 8 corner poles per ear).
- Shape capture: median 0.23 mm, p95 3.0 mm.
- Poor quads: 156; head / neck 120, mostly thin ear-ring quads.

**Limitations (first pass):**
- The ear is a relief seen from the side: the gap behind the ear (the undercut) is not modelled, so from behind it reads as a solid block.
- The helix rim still pokes through the cage in places.
- A dedicated ear mesh with the undercut remains a refinement item.

## 04a: arms to the wrist (5 Nov)

**Checkpoint:** `HGPT_Male_Retopo_04a_Arms_ToWrist_WIP_PROXY.blend` (`c530dad4…`), built from 03j by `scripts/retopology/build_task4_arms.py`. Read-only; 03j is unchanged.

**Method (designed loops, no auto-remesh):**
- **Measured arm axes.** The `LM_*` arm landmarks sit about 5 cm off the arm, so the axes are fitted to slice centroids of the source instead: upper arm z 1.18–1.33, forearm z 0.99–1.10; shoulder joint at z 1.42, elbow at the closest approach of the two lines, wrist at the narrowest slice.
- **Shoulder cap.** The 64-vertex socket loop is walked and mapped into the arm frame. 12 rings run from the socket to the arm, traced as meridians by fan rays from an origin inside the deltoid (offset 3.5 cm medially, 3 cm along the arm, checked inside by ray parity). The first 4 rings are tilted so the armpit side sits lower (the 105° / 170° raise needs those loops). A 4:2 all-quad transition halves 64 → 32 vertices early, avoiding thin quads.
- **Arm.** 32-vertex rings: every 2 cm on the upper arm and forearm, 6 rings over ±4 cm at the elbow with smoothly blended axes. The wrist ring is left open for the hand.
- **Guarded relax** (6 iterations): torso vertices fixed; no vertex may move more than 1 cm further from its arm axis or cross towards the body (x·side > 0.12).

**Measured (`build_04a_arms.json`, `audit_04a_arms.json`):**
- 6,848 faces, 100 % quads, 1 component, no non-manifold or wire edges.
- Open edges: pelvis (66) and the two 32-edge wrist rings, as planned. The sockets are closed.
- 92 three-edge and 96 five-edge vertices.
- Arm and cap fit to the source: median 0.6 mm, p95 2.4 mm. The 39 mm maximum is at the open wrist, where the hand is not built yet.
- Arm: 1,480 faces, 23 poor. Shoulder cap: 667 faces, 119 poor (aspect p95 4.07), concentrated in the armpit hollow.
- Minimum edge 1.17 mm; edge length p5 / p50 / p95 = 5.0 / 12.4 / 25.9 mm.

**Visual:**
- The deltoid is covered front, back and from the side, with loops following the cap.
- The elbow and forearm loops are even.

**Still open:**
- The armpit hollow seen from below has stretched, crowded quads where the cap meets the lats and pecs; it needs a hand-placed pass before the raised-arm tests.
- The left side uses the same procedure; the left-specific asymmetry check is not done yet.
- Hands and fingers are next.

## 04b: hands and fingers (5 Nov)

**Checkpoint:** `HGPT_Male_Retopo_04b_ArmsHands_WIP_PROXY.blend` (`1df4e6f9…`), built from 04a by `scripts/retopology/build_task4_hands.py`. Read-only; 04a is unchanged.

**What the source hand looks like:** relaxed, slightly cupped, thumb forward. **The Meshy surface fuses neighbouring fingers along their length** (a cut across the fingers gives one loop, not four), so fingers cannot be traced as separate tubes directly.

**Method (designed loops, no auto-remesh):**
- **Hand frame** from the principal axes of the source hand beyond the wrist ring: L (to the fingertips), Wd (across the knuckles, thumb on the −Wd side) and N (dorsal).
- **Fingers from thickness ridges.** The hand's thickness (dorsal hit to palmar exit) is sampled across the hand every 1.5 mm. Each finger is a ridge; the grooves between ridges are the separating planes. Ridges are tracked from a reference cut with four clear ridges, then fitted as smooth centre lines. The web of each finger is where its groove fades.
- **Finger tubes** of 8 vertices (4 dorsal, 4 palmar). Loops are placed at 0 / 14 / 28 / 36 / 42 / 48 / 60 / 67 / 72 / 77 / 86 / 93 % from the web to the tip, which gives 3 loops at the PIP joint and 3 at the DIP joint. A 3-quad cap closes the fingertip, so there are no poles on the tip. Side vertices stop at 90 % of the distance to the groove plane (72 % at the web), so neighbouring fingers stay separate surfaces. The outer sides of the index and little fingers are capped at 1.25 × the inner spacing.
- **Palm:** 32-vertex rings from the arm's wrist ring to a knuckle ring made of the four finger base rings (16 dorsal + 16 palmar vertices), with one web quad between each pair of fingers. Each intermediate ring is a cut of the source by a plane that turns from the wrist-ring plane to perpendicular to the hand axis. Vertices are placed by arc length around the whole cut, blending the wrist ring's spacing into the knuckle ring's.
- **Thumb:**
  - An 8-edge opening is cut in the palm (a 2 × 2 block of quads, the middle vertex removed), on the palm rows spanning the thumb base up to the crotch. It is placed where its centre is nearest the thumb axis.
  - The thumb axis is measured from cuts perpendicular to it.
  - The thumb tube has 8 vertices with loops at the MCP and IP joints, two loops wrapping the thenar mound, and a 3-quad tip cap.
  - The opening's vertex order is matched to the first thumb loop (best cyclic shift and direction), so the thumb root is not twisted.
- Every hand vertex is tagged (`t4_part`: 1 palm, 10–13 fingers, 20 thumb root, 21 thumb) for the later weight pass.

**Measured (`audit_04b_hands.json`, `hand_metrics_04b.json`):**
- 8,380 faces, 100 % quads, 1 component, no non-manifold, wire or loose elements.
- **Open edges: only the pelvis (66).** Head, arms and hands are closed.
- 132 three-edge and 128 five-edge vertices.
- Source hand to cage: median 0.76 / 0.69 mm (right / left), p95 3.3 / 2.9 mm, max 7.9 / 7.7 mm (at the fused finger grooves, where the cage deliberately leaves a gap).
- Hand faces: 718 right, 814 left. Aspect p50 1.9 / 2.0, p95 4.4 / 4.0. Poor quads 53 / 51, mostly in the thumb root and at the finger webs.
- Longest hand edges are 40–46 mm, in the palm rows around the thumb opening.

**Still open (first pass):**
- The palm rows around the thumb opening are coarse; the thenar mound is covered by a few long quads.
- The thumb root has 2 very sharp quads (minimum angle under 2°).
- With 8 vertices around, fingers are smooth tubes: knuckle bumps and nails are left to the normal map from the real source.
- The fingers stop at 90 % of the groove; check that they do not stick together at the deformation tests.

## 05a: pelvis, legs and feet; the whole body is closed (5 Nov)

**Checkpoint:** `HGPT_Male_Retopo_05a_FullBody_Closed_WIP_PROXY.blend` (`9e49fa35…`), built from 04b by `scripts/retopology/build_task5_legs.py`. Read-only; 04b is unchanged.

**Method (designed loops, no auto-remesh):**
- **Hips.** Three horizontal loops below the pelvis opening (z 0.897 / 0.879 / 0.862). Each is a cut of the source, with the hands excluded, split at the midline. Each half has 33 edges at the opening's arc-length fractions, so the torso columns run on.
- **Crotch.** A 7-edge strip along the midline under the crotch, from the front midline vertex to the back midline vertex, traced by rays fanned in the midline plane. Both legs share it, so each leg's first ring is 33 + 7 = 40 edges.
- **Legs (each side measured on its own).** Joints are found from the cross-sections:
  - knee: the narrowest cut between thigh and calf, z 0.52;
  - ankle: the narrowest cut above the malleoli, z 0.15;
  - forefoot line: centroids of cuts across the foot.

  The centre line is the thigh line, a rounded knee corner, the shank line, a rounded ankle corner and the forefoot line. 40-vertex rings run perpendicular to it, with vertices placed by rays from the centre line. Ring spacing: thigh 2.5 cm, knee 1.75 cm, shank 2.5 cm, ankle and heel 0.9 cm (19 rings sweep round the heel), foot 1.8 cm.

  The ring frame is carried along the curve, so the front of the shin becomes the top of the foot. The first 4 rings blend from the crotch ring's vertex angles to even angles. Inner-thigh vertices never cross the midline; the source thighs nearly touch down to z 0.74.
- **Foot and toes.** The foot rings stop at the toe bases (74 % of heel-to-toe-tip length). The source toes touch each other, so they cannot be cut apart. Three concentric loops and a 14 × 6 grid, projected horizontally along the heel-to-toe-tip direction, cover the toes like a mitten. All quads.
- Every new vertex is tagged (`t5_part`: 1 hips, 2 crotch, 3 thigh, 4 knee, 5 shank, 6 ankle and heel, 7 foot, 8 toes) for the weight pass.

**Measured (`audit_05a_full_body.json`, `leg_metrics_05a.json`):**
- **Whole body: 13,148 vertices, 13,146 faces, 100 % quads, 1 component, 0 open edges, 0 non-manifold / wire / loose elements.**
- 140 three-edge, 128 five-edge and 2 six-edge vertices.

| Region | Source to cage median (mm) | p95 (mm) | Max (mm) |
|---|---|---|---|
| Thigh and knee | 0.49 | 2.0 | 7.5 |
| Shank | 0.23 | 0.93 | 2.0 |
| Hips and crotch | 1.7 | 10.4 | 18.3 |
| Ankle, foot and toes | 0.57 | 7.8 | 16.0 |

- The hips and crotch figures are high because of the shorts' hem step and the crotch seam bulge. The ankle, foot and toes figures are high because of the gaps between the toes.

| Region | Faces | Poor quads | Aspect p95 |
|---|---|---|---|
| Knee | 720 | 0 | 2.8 |
| Thigh | 720 | 33 | 3.9 |
| Ankle and heel | 1,520 | 32 | 2.8 |
| Shank | 880 | 126 | 5.2 |
| Foot | 320 | 77 | 6.9 |
| Toes | 408 | 140 | 19.8 |

- Shank quads are long: 2.5 cm ring spacing against about 7 mm around.

**Still open (first pass):**
- **Toes:** a mitten cap with crumpled quads at the tips. The toes need a dedicated pass, at least a separate big toe, with the toe-bend loop placed at the joint.
- **Crotch and groin:** they follow the **shorts** in the proxy, including the seam bulge and hem step. The body under the shorts is not in the source, so a proper groin and gluteal fold need the real source, or a separate clothing layer with the body sculpted beneath.
- **Shank:** ring spacing could be 2 cm for squarer quads.
- The inner thighs stop 3 mm short of the midline where the source thighs touch.

## 05b: rest-pose self-intersections removed (5 Nov)

**Checkpoint:** `HGPT_Male_Retopo_05b_FullBody_Untangled_WIP_PROXY.blend` (`48796bf6…`), made from 05a by `scripts/retopology/untangle_retopo.py`. The report names the trial file `try_05b_u.blend`; 05b is a byte copy of it. The topology is unchanged.

**Why:** before testing deformation, the rest mesh itself was checked for surfaces passing through each other. It had 676 intersecting triangle pairs:

| Region | Pairs |
|---|---|
| Ankle and heel | 212 (the bend rings cross over the front of the ankle) |
| Head | 190 (ears and face) |
| Toes | 152 |
| Palm and fingers | 72 |
| Hips | 24 |
| Torso and arms | 26 |

**Method:** for the intersecting faces' vertices plus a one-ring margin, move each vertex towards its neighbours' average, then back onto the source surface. A vertex is not snapped when the nearest surface is more than 3 mm away, which happens at fused fingers and toes. Repeat while the count falls.

**Result:** 676 → 330 → 188 → 36 → **0** in 4 rounds. 487 vertices moved more than 0.5 mm.
- The large moves (up to 53 mm) are all toe-cap vertices, pulled back from crumpled tips.
- Toes: aspect p95 19.8 → 8.6; fit to source p95 7.8 → 8.9 mm.
- Hands and legs: fit unchanged.

## 06a: canonical skeleton fitted and bound (Phase 2, first pass)

**File:** `rig/HGPT_Male_Rig_06a_Bind_WIP_PROXY.blend` (`7db29d99…`), made from 05b by `scripts/meshy/bind_retopo_blender.py`. The objects are named `MESHY_RIG` and `MESHY_BODY`, so the existing pose tests run unchanged.

**Skeleton:**
- The canonical rig (77 bones, from the earlier Meshy bind) is scaled **uniformly** to 1.82 m (× 0.9806), so its proportions are unchanged. Its trunk is aligned front-to-back with the retopology trunk (+3.4 mm).
- The earlier GLB bind could not be reused directly: the proxy body is posed differently, with surface gaps up to 49 mm.
- No bone length is changed. Limbs are aimed rigidly at joints measured on this mesh:
  - arms and legs as two-bone chains that end on the measured wrist or ankle, with the elbow or knee on the side of the measured one;
  - the hand is aimed along the measured hand axis and rolled to the knuckle line;
  - each finger and thumb is aimed at its tip, taken from the part tags;
  - the foot is aimed at the ball, and the toe at the toe tip.

**Residuals (right / left):**

| Joint | Right (mm) | Left (mm) |
|---|---|---|
| Wrist | 1 | 31 |
| Ankle | 16 | 17 |
| Ball of the foot | 5 | 8 |
| Fingertips | 0–13 | 1–6 |
| Thumb tip | 0 | 14 |

- **Elbow:** the canonical elbow is 68 / 56 mm from the elbow first estimated on the mesh. That estimate came from the closest approach of two fitted lines. The skeleton render shows the canonical elbow inside the mesh's elbow region, so the canonical lengths are kept and the estimate is treated as unreliable.
- **Knee:** 29 / 19 mm from the measured cut, within the knee region.
- **Toe bone:** the canonical toe bone runs past the toe tips. It pivots at the ball, so it is harmless.

**Weights:**
- Bone-heat automatic weights, then clean-up rules driven by the builders' part tags:
  - fingers follow only their own chain, metacarpal and the hand;
  - thumb and palm are restricted the same way;
  - foot and toes follow only the leg-end bones;
  - no left/right bleed;
  - at most 4 influences, normalised.
- 1,185 vertices changed by the rules. 0 left unweighted. 64 deform groups.

**Rest-pose check:** 0 self-intersections.

### Phase 3 baseline: shoulder elevation sweep (`scripts/meshy/retopo_shoulder_sweep_blender.py`, `shoulder_sweep_06a.json`)

Both arms are raised in the scapular plane, elbows straight, the clavicle lifting in proportion (25° at 170°). Measured in the shoulder region; **no corrective shapes yet**.

| Raise | Self-intersections | Folded faces | Edge stretch p99 / max | Compression p1 |
|---|---|---|---|---|
| 0° | 0 | 5 | 1.00 / 1.00 | 1.00 |
| 45° | 0 | 4 | 1.29 / 1.47 | 0.88 |
| 90° | 2 | 4 | 2.31 / 3.13 | 0.72 |
| 105° | 2 | 4 | 2.62 / 3.63 | 0.68 |
| 135° | 1 | 3 | 3.21 / 4.49 | 0.60 |
| 170° | 35 | 6 | 3.69 / 5.16 | 0.46 |

**Seen in the renders:**
- 90–105°: a crease along the front armpit fold on the arm side.
- 135–170°: the side of the chest and the armpit skin are strongly stretched, and the rear deltoid notches in.

These are exactly the brief's priority areas. Next: shoulder weight shaping (smoothing and falloff between clavicle, scapula, upper arm and spine_03), then correctives at 90/135/170.

## 06b: shoulder weight shaping (Phase 3, step 1)

**File:** `rig/HGPT_Male_Rig_06b_ShoulderWeights_WIP_PROXY.blend` (`1ee7efc9…`), made from 06a by `scripts/meshy/shoulder_weight_shaping_blender.py` with 30 passes and a 0.20 m radius. The file is a copy of the trial `try_ws_30_0.20.blend`.

**Method:** around each shoulder joint, the weights of {clavicle, scapula, upper arm, spine_02, spine_03} are smoothed over the mesh graph. The smoothing fades out at the edge of the region. The upper arm beyond 16 cm from the joint is untouched, and each vertex's total for those bones is preserved. About 650 vertices changed per side.

**Sweep, 06a → 06b** (`shoulder_sweep_06b.json`; a wider variant, 80 passes / 0.24 m, is kept for reference in `*_variant_80_024.json`):

| Raise | Self-intersections | Folded faces | Stretch p99 |
|---|---|---|---|
| 45° | 0 → 3 | 4 → 3 | 1.29 → 1.29 |
| 90° | 2 → 0 | 4 → 2 | 2.31 → 2.35 |
| 105° | 2 → 0 | 4 → 1 | 2.62 → 2.72 |
| 135° | 1 → 0 | 3 → 0 | 3.21 → 3.27 |
| 170° | **35 → 1** | 6 → 0 | 3.69 → 3.78 |

**Visual (evidence `06b_shoulder_compare.png`):**
- The **rear-deltoid notch at 170° is gone**; the back of the shoulder is one smooth mass.
- The crease along the underside of the arm at 90–105° is slightly reduced but still present. It follows the seam between the shoulder cap and the torso in the 04a topology, so it needs a corrective or a local re-loop rather than more weight smoothing.
- The stretch p99 is set by about 30–75 edges of the armpit floor, about 14 cm below the joint, which stretch past 2×. Correctives and denser armpit loops are the next steps there.
