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

## Shoulder and armpit 0–170°: diagnosis, cause attribution and fixes (SH1)

**Scope:** the owner's request. Evaluate the shoulder and armpit through 0–170° from the front, back and side (plus a view under the armpit), and find the **cause** of each problem: topology, weights, joint placement, or missing corrective deformation. The current checkpoints are preserved: every step below is a new file.

**Tool:** `scripts/meshy/shoulder_diagnostics_blender.py`. It splits each side into six zones on the rest mesh: deltoid, front armpit fold (pectoral), back armpit fold (latissimus/teres), armpit floor, clavicle/trapezius and scapula. For each elevation it measures, per zone:
- self-intersections and folded faces;
- crease sharpness, and new edges sharper than 60°;
- edge stretch p95 and compression p5 (pinching);
- deltoid enclosed volume.

Two motions are tested:
- `lib`: the existing test motion. The clavicle lifts 25° at 170°, and the scapula rides on it.
- `rhythm`: an anatomical scapulohumeral rhythm. The clavicle elevates by 0.15 × the arm elevation and retracts by 0.10 ×; the scapula rotates upward by elevation/3.

A separate measurement records the tissue cover over the humeral head: the nearest skin to the joint, and the thickness along the top arc. All reports are in `shoulder_sh1/`.

### Findings and causes

| Problem (as seen) | Evidence | Cause | Action |
|---|---|---|---|
| Deltoid flattens and loses volume as the arm rises | The canonical shoulder joint sat only **16–27 mm under the skin** at the back and top, at rest; a real humeral head (≈24 mm radius) needs ~50 mm. Cover at 135°: 10 mm. The joint was **55 mm too far back and 20 mm too high** for this body; it was inherited from the earlier GLB fit, whose arms were posed differently. | **Joint placement** | **Fixed (06c).** The joint is moved to 50 mm under the lateral and upper deltoid of the source, centred front-to-back. The whole arm moves rigidly (no bone length change); the clavicle end follows, and the scapula moves 60 %. Deltoid cover at 90 / 135°: 11.9 / 10.0 → 31.5 / 31.1 mm; enclosed volume at 90°: 0.70 → 0.80. |
| Arm fit after the joint move | The two-bone arm fit used only the first of the two forearm bones, which folded the elbow. The narrowest forearm cut also lies proximal to the true wrist. | Fitting method (my error) | **Fixed.** Arms follow the measured centre lines: the upper arm meets the measured upper-arm axis at its canonical length, and the forearm runs parallel to the measured forearm axis. Right elbow 6 mm from the measured one, left 10 mm. Fingertips 3–22 mm. The left "wrist" residual of 50 mm is a bad left-wrist estimate: the left hand hangs differently, and its fingertips match within 12–22 mm. |
| Crease at the armpit apex (fin) | Cage folds of 136–170° at the apex, where the **source is smooth** (2–11°) | **Topology** (cap quads folded at the cap/socket junction) | **Fixed (05c)** with `repair_cage_folds.py`: unfold, then project along the normal, only where the cage folds more than 50° sharper than the source. Shoulder defect edges 17 → 4; no self-intersections. |
| Armpit floor flat and over-stretched | **892 source points inside the cage**, up to 44–49 mm: the axillary vault in the source's rest pose is a hollow that the 04a cap **bridged** | **Topology** | **Fixed (05c)** with `armpit_vault_fit.py`: armpit vertices carried into the vault along their normals, with a tangential relax. Shoulder coverage p95 / max: right 25.4 / 43.6 → **8.1 / 26.4 mm**, left 28.6 / 49.2 → **6.5 / 10.8 mm**. 0 self-intersections. Armpit stretch p95 at 90°: 3.30 → 2.49; at 170°: 4.97 → 3.79. |
| Crease along the front armpit fold at 90–105° | At rest the **source itself** turns 124–142° there: the skin is tucked into the fold in the arms-down pose | **Missing corrective deformation.** Linear skinning cannot unfold a tuck. | **Open.** Correctives at 90 / 135 / 170°. |
| Back armpit fold (latissimus/teres) stretched about 3.5× at 170° | Concentrated stretch in the back-fold zone | Weights plus the rest-pose tuck. A corrective is needed. | **Open.** |
| Trapezius bunches beside the neck at 135–170° | Clavicle/trapezius zone compression p5 0.68 | Joint motion (the clavicle rotates alone) plus weights | **Open**, tied to the next item. |
| **The scapula does not rotate upward** with the `lib` motion | The anatomical rhythm on bone-heat weights drags the whole upper back into a hump and a horizontal ridge (renders) | **Weights** (bone-heat spreads scapula/clavicle weight over the back) | Tried geometric anatomical girdle weights (`girdle_weights_blender.py`, candidate 06d): **worse**. At 170° with the rhythm, self-intersections rose (deltoid 9, clavicle/trapezius 18), sharp edges multiplied and deltoid volume fell to 0.27. **Rejected**; the result is kept in `girdle_weights_06d_REJECTED.json` and the 06d diagnostics. Scapular upward rotation needs a different mechanism (a sliding helper or corrective), not reweighting. |

### Current best state

- **Mesh:** `HGPT_Male_Retopo_05c_ShoulderArmpitFit_WIP_PROXY.blend` (`cc14d29c…`), from 05b: the fold repair plus the armpit vault fit. 0 rest self-intersections.
- **Rig:** `rig/HGPT_Male_Rig_06c_GHFit_ShoulderWeights_WIP_PROXY.blend` (`10d522d6…`). Bind (`8437c988…`, `GH_FIT=clearance`), then the same shoulder weight shaping as 06b.
- **`lib` motion, 45–170°, all six zones:** 0 self-intersections, folded faces ≤ 1 per zone. Deltoid cover 31–36 mm through 135°. Rest proportions unchanged (0° renders are identical).

**Comparison sheets** (rows: 06b baseline, 06c, 06c with the anatomical rhythm; columns: front, back, side, under the armpit) at 0 / 45 / 90 / 105 / 135 / 170°: `evidence/06c/shoulder_cmp_*.png`. These are working evidence; renders are not committed.

**The shoulder area is NOT declared complete.** Still open:
1. Correctives for the front-fold tuck, the back-fold stretch and the trapezius bunching.
2. An anatomical scapula motion that doesn't distort the back.
3. 4 remaining fold-defect edges at the armpit apex.
4. A 26 mm pocket left at the floor of the right armpit vault.

## SH2 (in progress): pocket fit, scapula glide, corrective attempts, skeleton check

- **Mesh 05d** `HGPT_Male_Retopo_05d_ArmpitPocket_WIP_PROXY.blend` (`de8c60a5…`): 05c plus `armpit_pocket_fit.py`.
  - Shoulder fit p95 / max: right 8.1 / 26.4 → 4.5 / 9.0 mm; left 6.5 / 10.8 → 4.8 / 10.1 mm.
  - 0 self-intersections; 4 fold-defect edges remain.
  - A second fold-repair pass was **rejected**: it reduced the defects 4 → 3 but worsened the fit (left max 24 mm).
- **Rig 06e:** 05d bound and shaped as 06c (`e6bd6be7…` bind, `18d00939…` weights).
- **Rig 06f** `HGPT_Male_Rig_06f_ScapulaGlide_WIP_PROXY.blend` (`e6b498a2…`): 06e plus a **scapula glide helper** (`add_scapula_glide_blender.py`).
  - A separate deforming bone per side, driven by arm elevation (ROTATION_DIFF against a reference bone), rotating 0.6 × elevation/3 and lifting 15 mm at 170°.
  - It takes weight only from the spine share, over the shoulder blade, never on the arm or the armpit walls.
  - Visible upward rotation of the shoulder-blade relief, no hump, zone metrics unchanged.
  - A first version whose region reached the posterior armpit wall caused front-fold collisions and was narrowed.
- **Corrective shapes:** edge-length solve (`build_shoulder_correctives_blender.py`), all variants **rejected** (reports `correctives_*_REJECTED.json`):
  - raw solve: shards at 170°;
  - smoothed displacement: correction washed out;
  - uniform scale-back: keys shrunk to 5–13 %;
  - smoothed local scale-back: fins and serrations.
  - The 90° key improves the metrics (deltoid 0.80 → 0.90, back-fold stretch 2.59 → 2.23) but replaces the crease with serrations.
- **Skeleton check (06f):** all bone lengths are canonical except the clavicles (−6.0 / −1.3 mm, from the joint move) and the non-deforming muscle guide lines.
  - The shoulder joint is 49 mm under the lateral and upper deltoid, centred front-to-back.
  - The joint's position relative to the acromioclavicular joint is canonical.
  - The test motion is within the `src/rig/humanoid.ts` limits: abduction ≤ 180°, clavicle elevation 25° at its limit, elbow 5° of flexion.
- **Owner's observation (the "flying squirrel" web, 105°):** confirmed by measurement and **identified as a weights cause**. Upper-arm weight reaches down the side of the trunk to **253–273 mm below the shoulder joint**: 134–156 trunk vertices more than 120 mm below it in 06a–06f, and 06b's smoothing added about 90 more trunk vertices with arm weight. In a real raised arm the trunk skin below the axillary folds stays with the ribcage. This also explains the armpit-floor and back-fold stretch numbers the corrective attempts were fighting.
  - Next: limit upper-arm influence on the trunk to the axillary fold region.
- **Continuous sweep (preliminary, 06f; `sweep_animation_06f_PRELIMINARY.json`):** the summary flags up to 126 intersecting pairs within 0.25 m of the shoulders at some frames, elbow included angle down to 148°, and wrist deviation up to 23°. These are **not yet investigated**; they may be test-rig effects (the hands and forearms near the head at 170°) and must be checked before any sign-off.

## AX2: the armpit "batwing" — root cause and anatomical correction (rig 06g)

**The owner's finding:** at 90–105° a triangular sheet of skin runs from the upper arm down the side of the ribcage. **Investigated before any further correctives** (`batwing_probe.py` measurements, recorded below).

| Question | Measurement (06f, right side) | Verdict |
|---|---|---|
| Excess surface area at rest? | The cage follows the source over the side chest and armpit (shoulder fit p95 4.5 mm, max 9 mm after 05d) | **No.** The sheet is created by deformation, not by extra rest geometry. |
| Does the arm's topology reach too far down the trunk? | The seam between the torso and the 04a shoulder cap runs down to **178 mm** below the shoulder joint; 247 cap vertices lie on the chest wall medial of the arm root | **Yes**, a contributing topology cause. The axillary folds leave the chest wall about 100–130 mm below the joint. |
| Do weights pull the chest wall up with the arm? | Upper-arm weight on the trunk: mean 0.19–0.20 at 60–180 mm below the joint (max 0.69), 0.06 down to 300 mm. **Scapula weight 0.42–0.53 on the lateral chest wall** (serratus region), 0.33 down to 300 mm. | **Yes, the main cause.** |
| Effect | At 105°, chest-wall skin 140–180 mm below the joint moves **80 mm** on average (max 163); 180–300 mm below moves 42 mm | The batwing |

**Correction (06g, `axillary_fold_weights_blender.py`)**, rig `HGPT_Male_Rig_06g_AxillaryContour_WIP_PROXY.blend` (`62600bac…`), from 06f:
- **Anatomical axillary contour in the weights.** The anterior fold (lower border of pectoralis major) leaves the chest wall 110 mm below the joint. The apex of the hollow is 90 mm below; the posterior fold (latissimus dorsi plus teres major) is 130 mm below.
- On the trunk side of the arm root and below that line (30 mm fade), skin no longer follows the upper arm. Lateral chest-wall skin in front of the posterior axillary line no longer follows the scapula either.
- The removed weight goes to the vertex's own spine bones.
- Untouched: the arm, the deltoid, the two folds, the upper pectoral and latissimus, and the back over the shoulder blade. Deltoid cover and volume are unchanged (cover 30.6 / 22.4 mm at 90 / 135°; volume ratio 0.80 at 90°).
- No smoothing and no corrective shapes.

**Result:**

| Trunk skin below the joint | 06f motion at 90° / 105° | 06g motion at 90° / 105° |
|---|---|---|
| 100–140 mm (fold ends) | 49 / 58 mm | 38 / 46 mm |
| 140–180 mm | 67 / 80 mm | 38 / 44 mm |
| 180–300 mm (ribcage) | 36 / 42 mm | **11 / 13 mm** |

- Upper-arm weight at 180–300 mm below the joint: 0.06 → 0.00.
- **Visual (front / back / underside sheets at 0 / 45 / 90 / 105 / 135 / 170°):**
  - the ribcage stays vertical under the arm instead of flaring out into a sheet;
  - the lower border of the pectoral reads as the front fold;
  - the latissimus flares less;
  - a hollow forms under the arm.
- The stretch now concentrates in the hollow and the back fold (p95 3.8–4.3 at 90–105°), where real skin unfolds.

**Continuous sweep, rest → 170° → rest, 61 frames** (`shoulder_sweep_animation_blender.py`, MP4 and GIF in the evidence folder; `sweep_animation_06b/06f/06g.json`):
- The first run reported 126 intersections, a 148° elbow, a 23° wrist and 163 mm/° jumps. All of these were **test artifacts**: frame 0 was left unposed while frame 1 straightened the arm and re-aimed the hand. The sweep now starts from the measured rest elevation, keeps the rest elbow bend and the rest wrist orientation.
- Corrected figures: intersections ≤ 4 (06g) / 3 (06f) / 1 (06b); identical going up and coming down; largest frame-to-frame jump 5.8 mm per degree (smooth). The elbow and wrist stay at their rest angles.

**Regression found (not hidden):** with the arm brought **closer to the body than the rest pose**, the inner upper arm now presses into the latissimus. 06f hid this because the chest wall moved away with the arm.
- Intersecting pairs at 17.5° (rest) / 12° / 8° / 5° from vertical: 0 / 0 / 34 / 258, all upper arm against latissimus or scapula skin.
- Standard poses: stand (8°) 0 → 17, curl (5°) 216 → 347; press and squat unchanged.
- This is real contact on a body with this much latissimus. It needs an adduction contact or compression corrective, driven only below the rest elevation: the next item.

**Still open:**
1. The adduction contact above.
2. The torso/arm topology seam is still 178 mm below the joint, so the cap loops on the chest wall don't follow the fold contours; a fairly sharp crease shows on the inner arm at the hollow wall at 135°. A local re-loop along the fold contours is the topology fix.
3. Front/back fold sharpness at full elevation.
4. The scapula glide's visual effect is subtle.

Nothing has been sent to production or marked approved.

## AX3: arms-down contact, axillary ring gradient, vault-loop trial (rigs 06h, 06i)

All changes are made from **06g** (`62600bac…`, preserved, read-only). New versions:
- `HGPT_Male_Rig_06h_AdductionContact_WIP_PROXY.blend` (`f42a428c…`)
- `HGPT_Male_Rig_06i_AxillaryRingRelax_WIP_PROXY.blend` (`27cd2c43…`), the **current candidate**

Both are read-only. The numbers are in `axilla_ax3/`. Renders, MP4 and GIF are in the local evidence folder only (no Meshy-derived renders in git).

### 1. Arms-down contact (06h, `build_adduction_contact_blender.py`)

**Cause:** since 06g the chest wall stays with the ribcage. An arm brought closer to the body than its rest angle (17.5° from vertical) therefore meets the latissimus. This is real tissue contact, so it is corrected as contact.

**Method:**
- Collision-driven mutual flattening at 4° from vertical. Only truly intersecting, facing, non-adjacent triangle pairs are moved, each side by half the depth.
- Solve and smooth-the-correction-field rounds alternate.
- The posed displacement is inverse-skinned into one shape key per side (`CONTACT_ADD_R/L`).
- A driver on the arm's elevation keeps the key at **exactly 0 above 14.5°**, so the raised range cannot change. It ramps to 1 at 4° and is held there below.

| Shoulder-region pairs | 17.5° | 12° | 8° | 5° | curl start (5°, elbow 40) | 45° | 90° | 135° | 170° |
|---|---|---|---|---|---|---|---|---|---|
| 06g | 0 | 0 | 17 | 129 | 281 | 1 | 0 | 0 | 2 |
| **06h / 06i** | 0 | 0 | **0** | **0** | 150 | 1 | 0 | 0 | 2 |

**Standard poses** (`pose_report_*.json`): stand 17 → **0**; curl 347 → 216; press_bottom 107 → 107; press_mid 0; press_top 1 → 2 (hip/groin band).
- The remaining curl and press_bottom pairs are all **forearm against biceps at the elbow fold**: 202 and 107 pairs. Arm-to-trunk pairs are 0.
- This elbow contact is unchanged at the rest elevation and is an **open elbow item, not a shoulder one**.

**Renders** (stand 8° and 5°; front, back, underside, back-side): identical in shape to 06g, with no dents or notches.

**Rejected versions:**
- **v1** split the mesh into arm and trunk by dominant bone. Next to the part border, where both are one surface, it found false contacts and tore notches into the front axillary fold.
- **v2** excluded the border. It was clean, but the real contacts lie 3–10 edges apart across that border, so it removed almost nothing (17 pairs left at 8°).
- **v3** was collision-driven with a border mask. Again it removed almost nothing.

### 2. The inner-arm crease at 135° and the low seam (06i, `axillary_ring_relax_blender.py`)

**Investigation:**
- **Topology placement is not the cause.** The trunk-side cap rings lie on the source (mean 0.1–2.3 mm). Rings 1–2 already reach 81–90 mm below the joint, matching the source's armpit dome (78–98 mm below it).
  - The rings run up the chest wall of the narrow arm/chest gap to the vault top, then down the inner arm. So no ring can be slid onto the fold contour without leaving the source surface (`relay_axillary_loops.py`: "no ring reaches the contour").
- **The cause is a weight step across too few rows.** Ring 0 (the torso rim) is trunk-weighted, and by ring 2 the skin is mostly arm.
  - At 135° the rungs between rings 0–1 / 1–2 / 2–3 stretch **×7.6 / ×10.5 / ×6.0**, while ring 5 and up stretch ×2 or less.
  - One or two rows take the whole raise: that is the crease. The "seam sits too low" impression comes from this step showing as a line at the bottom of the vault.

**Fix:** the weights of the trunk-facing cap vertices in rings 1–4 are relaxed (Laplace) between fixed boundaries:
- ring 0, the torso rim, so the **chest wall keeps its weights**;
- ring 5;
- the deltoid side.

No smoothing of the surface and no corrective shape.

| | 06h | 06i |
|---|---|---|
| Rung stretch at 135°, rings 0-1 … 4-5 (max) | ×7.6 / 10.5 / 6.0 / 4.9 / 3.2 | ×4.3 / 6.2 / 5.2 / 5.9 / 6.1 |
| New sharp edges, armpit zone, 45 / 90 / 105 / 135 / 170° | 5 / 4 / 5 / 7 / 8 | 0 / 1 / 1 / 1 / 4 |
| Back-fold stretch p95 at 135 / 170° | 4.99 / 5.43 | 4.27 / 4.71 |
| Scapula zone stretch p95 at 135 / 170° | 5.02 / 5.44 | 3.45 / 3.85 |
| Deltoid volume ratio at 90 / 135° | 0.80 / 0.56 | 0.80 / 0.56 (unchanged) |
| Trunk band 180–300 mm below the joint at 105° (batwing check) | 13 mm | 13 mm (unchanged) |
| Continuous sweep 0→170→0: max pairs / folded / jump | 4 / 6 / 5.8 mm per ° | **3 / 3** / 5.8 mm per ° |

**Cross-sections (sagittal, 30 mm medial of the joint):** 06g shows a spike (a flap folding out at the front fold) at 90, 135 and 170°. **It is gone in 06i.** The coronal slice through the apex at 170° shows a Z-fold in 06g and a smooth line in 06i.

**Not adopted:**
- **`insert_vault_loops_blender.py`** adds three new rings across the vault (+256 vertices per side). It passes every guard: 0 n-gons, 0 rest intersections, drivers kept, ≤ 4 influences.
  - But extra rows do not lower the strain: a quad stretched ×6 splits into two quads stretched ×6.
  - The corner-pattern quads of the 64→48 ring transition crumple into small shards on the front vault at 135–170°.
- **`arm_tube_weights_blender.py`** (inner-arm ownership): no visible gain, and armpit stretch rose.
- **`axillary_floor_gradient_blender.py`**: reached the chest wall and brought the batwing back (140–180 mm band up to 192 mm).

### 3. Anatomical check (no photographic references available in this session; criteria from standard surface anatomy)

| Region | Expected | 06i | Verdict |
|---|---|---|---|
| Pectoral edge (anterior fold) | Lower border of pectoralis major forms one continuous fold from the chest to the arm. Taut at 90–135°, flattening at full elevation; no skin folding over it. | Front-fold zone: 0 intersections and 0 new sharp edges at 45–170°; stretch p95 1.2–2.2 (low). The flap spike at the fold edge is removed. A softer kink remains in the front coronal slice at about 105 mm below the joint at 90–135°. | Plausible; slightly angular at 90–135° |
| Latissimus / teres major (posterior fold) | Lower than the front fold at rest. Becomes a firm ridge running up the arm at 90–170°, visible from the back. | Contour 130 mm (back) vs 110 mm (front). Ridge visible in the back renders at 105–170°. Stretch p95 4.3–4.7 at 135–170°: real skin slides over the latissimus here, which linear skinning cannot do. | Plausible shape; strain high |
| Ribcage | Stays put; only spine and girdle motion moves the side of the chest. No lift with the arm. | 180–300 mm band moves 13 mm at 105° (06c-era batwing: 42 mm). Upper-arm weight there is 0.00. | Plausible |
| Armpit hollow | A dome between the folds, deepest around 90°, shallow but still concave at 135–170°. | Hollow present at 0–105°. At 135–170° the coronal apex slice is almost straight (flat), not concave. | **Deviation**: the fossa is too flat at full elevation |

### Status and open items

1. Elbow-fold contact in the curl and the press bottom: forearm against biceps, 216 and 107 pairs. A separate elbow corrective is needed.
2. Flat axillary fossa at 135–170°. A small slightly-concave fossa shape on the trunk side, driven above 120°, is the candidate fix (a shape key, on top of correct weights).
3. Posterior-fold strain ×4–5 at 135–170° (skin sliding not modelled).
4. Slight angularity of the anterior fold at 90–135°.

**Nothing is marked complete; 06i is the current candidate for the owner's visual review.**

## MD1 / ST: muscle definition restored (07a → 07b) and the standing-model review

**Checkpoints, all read-only:**
- 06j `HGPT_Male_Rig_06j_ElbowContact_WIP_PROXY` (`3b16e5cf…`): elbow contact keys, anatomical hinge posing.
- 07a `…_07a_DefinitionRestore` (`2146a8f7…`): superseded by 07b.
- **07b `…_07b_DefinitionRestore_FoldRelief` (`5592268…`): latest verified checkpoint.**

Earlier checkpoints are unchanged. Deformation development is paused at the owner's request.

**Why the body looked like a mannequin** (`muscle_relief_audit_blender.py`, renders under identical lighting):
- Muscle volume was intact.
- The 20–25 mm quads stepped over the source's roughly 10 mm separations between muscles.
- Flat-shading facets had passed for definition.

**The restore** (`densify_project_blender.py`):
- One subdivision level everywhere except the hands; each new vertex is placed onto the approved source.
- A symmetry guard and a posed fold guard decide what is not imported.
- Abdominal groove depth: 43 % → 76 % of the source (15 mm scale), 60 % → 82 % (30 mm scale).
- Chest, arms and back relief correlate 0.92–0.99 with the source.
- 48,086 vertices.

**07b deformation verification** (anatomical elbow hinge):

| Check | Result |
|---|---|
| Stand / curl / press bottom / press middle / press top | 0 / 0 / 0 / 0 / 0 pairs |
| Squat | Known hip, groin and knee contact, unchanged |
| Arms-down and curl contact | 0 |
| Shoulder sweep 0→170→0 | Max 4 intersections, 5 folded faces, 5.76 mm/°, symmetric up and down |
| Chest lift at 105° | 13 mm, unchanged |

**Proportions vs the approved source** (`proportion_compare_blender.py`, shared rest pose, tape-measure girths at the same planes; `standing_07b/proportions_07b.json`):

| Measurement | Difference |
|---|---|
| Height | −0.4 mm |
| Shoulder breadth | −1.8 mm |
| Hip breadth | −3.8 mm |
| Chest girth | −1.7 mm |
| Waist girth (at 1080 mm) | +3.2 mm |
| Hip girth | −1.5 mm |
| Thigh girth | −3 / −6 mm |
| Calf girth | −0.8 mm |
| Neck girth | −4 mm |
| Upper-arm girth | **−6 mm (−1.6 %)** |
| Forearm girth | −3.5 mm (−1 %) |

Deviation from the source: |dev| mean 0.06 mm. 410 vertices are more than 2 mm off: the shorts region, the hands and the toes.

**Visual defects found in the standing review** (not corrected; awaiting the owner's review):
1. **Upper-back midline:** a narrow dark slit along the thoracic spine, at rest and standing. The source has a broad, smooth groove instead.
2. **Sternum and neck base:**
   - the midline sternal line is sharper and slightly notched compared with the source;
   - small crinkle lines at the neck/trapezius junction and under the jaw.
3. **Pelvis:** the source wears modelled shorts, so the genital and gluteal anatomy under them has no source reference. The current shape is improvised and crude, with a fold and flap on the left. Flatter patches in flat shading mark where the shorts surface was too far away to snap to. This needs a decision: anatomical underwear/shorts or a nude anatomical form.
4. **Head and face:** visibly softer than the source (eyelids, lips, the hair sculpt). The face was retopologised at lower density and isn't densified.
5. **Hands:**
   - not densified, so there's a resolution step at the wrist in flat shading (not visible when smooth);
   - 0.8 mm mean inside the source (up to 2.6 mm);
   - in the standing pose the palms face forward and the fingers splay, because the pose doesn't rotate the forearm inward. This is a pose-setup issue.
6. **Feet:** toes slightly softer and up to 2.4 mm inside the source.
7. **Arms:** about 1.6 % slimmer than the source at mid-upper-arm and 1 % at the forearm.

## SC1: standing-model cleanup pass (07b → 07c), presented for approval

**Checkpoint:** `HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend` (`e9448c68…`), read-only. 07b and every earlier checkpoint are unchanged. Scripts: `standing_cleanup_blender.py`, plus `densify_project_blender.py … face`. Every rest-pose edit is also applied to all corrective shape keys.

**Changes:**
1. **Upper-back midline.**
   - Correction: the earlier report said 07b was 2–6 mm deeper than the source. It was not. The approved source itself has a spinal crease only 1–2 mm wide and about 8 mm deep; a coarse probe had missed its floor.
   - The crease is now a broad, rounded groove (about 4 mm deep over ±5 mm): a deliberate departure from the source artefact. The back muscles beside it are unchanged.
2. **Sternum, neck and jaw.** The sternum line is softened, with a few small notches left at the top, as in the source. The neck/trapezius crinkles and the jaw line are reduced by targeted volume-preserving smoothing.
3. **Pelvis: neutral nude base form.** The source wears modelled shorts, so there is no anatomical reference under them.
   - Made symmetric from the cleaner side.
   - A simple smooth genital mass, without detail.
   - The left-side "flap" was a deep crease where the genital mass met the inner thigh. It is filled into a smooth junction (vertices up to 47 mm).
   - The hip-side lines from the shorts seams are softened.
   - Fitted shorts can go on top later.
4. **Arms: unchanged.** The surface lies 0.04–0.16 mm from the source. The 1.6 % girth gap is the convex-hull tape riding over the source's raised veins, not missing volume.
5. **Hands and feet:** brought out to the source where they sat inside it (122 hand and 15 foot vertices), except where fingers or toes would cross.
6. **Face:** a second subdivision level on the face only. Brows, eyes, lids and lips are crisper. 56,677 vertices in total.

**07c verification** (anatomical elbow hinge):

| Check | Result |
|---|---|
| Stand / curl / press bottom / mid / top | 0 / 0 / 0 / 0 / 0 pairs |
| Squat | 745 pairs (07b: 757), known hip/knee contact |
| Arms-down and curl contact | 0 |
| Raised range | 3 pairs at most |
| Sweep 0→170→0 | Max 6 intersections, 5 folded faces, 5.76 mm/°, symmetric |
| Chest lift at 105° | 13 mm, unchanged |

Proportions against the source: everything is within 1.2 %, height −0.4 mm.

**Known remaining items (not corrected):**
- The hands are at the original resolution (a wrist density step in flat shading only).
- The standing presentation pose shows the palms forward, because the pose does not rotate the forearm inward.
- Small marks remain at the nostril base, the front hairline and the top of the right shoulder.
- The thighs around the filled groin crease are up to about 4.5 mm off the source.
- More "new sharp edges" are counted in the back-fold zone in the diagnostics (2 → 10). There are no intersections there.

## F00 — Female source baseline (6 Nov, read-only, before any work)

The male standing model 07c was approved by the owner on 6 Nov and is locked (see `review-assets/body_v2/characters/hgpt_male_v2/APPROVAL.md`, which also lists the non-blocking polish items). Female work starts from her own source. Nothing from the male mesh or topology is reused.

**Source, verified against the supplied SHA-256 checksums** (neither file is in git; licensed Meshy source):

| File | Bytes | SHA-256 |
|---|---|---|
| `HGPT_Meshy_Female_Pro_1.68m_Clean_Unrigged.glb` | 32,370,660 | `de8ab078f2510c18bf3b05e82d3840583138f3c3feb6407fda7f24cfd6bf885b` |
| `HGPT_Meshy_Female_Pro_1.68m_Clean_Unrigged.blend` (rejoined from two parts with the supplied script) | 61,311,365 | `4b53bebe89ca28fb84a1458fcb34da5d4ca78bda0c03f50d2bf39d8e468fc782` |

**Geometry.** One mesh, `Mesh_0`, 514,566 triangles. The `.blend` mesh is welded: 257,175 vertices, watertight (0 boundary edges), one component. The GLB holds the same positions split at 800 UV islands (283,437 vertices). The figure is 1.680 m tall, feet at z = 0, facing −y (the male's convention). A-pose with the arms about 22° from vertical. Textures are 4096²/2048²/4096². No rig, shape keys or vertex groups. The sports bra and shorts are fused into the body surface. Ponytail. Barefoot.

**Measurements vs the owner's Option 4 guide** (`female_f00/female_source_measurements.json`, made by `scripts/meshy/female_source_baseline_blender.py`). Girths use the tape-measure method, the convex hull of the trunk's own section. The bust is measured with the arms excluded and the bra included.

| Measure | Source | Guide |
|---|---|---|
| Height | 1.680 m | ≈ 1.68 m |
| Bust (z 1.196) | 94.6 cm | 84–92 cm |
| Waist (z 1.045) | 63.4 cm | 64–72 cm |
| Hips (z 0.82) | 99.5 cm | 90–98 cm |
| Leg length, trochanter level to floor | 47.3 % | 47–50 % |
| Shoulder breadth across the deltoid caps | 42.7 cm | 37–40 cm* |
| Shoulder : hip width (37.9 cm) | 1.13 | 0.95–1.00* |

\* The guide's shoulder width is probably biacromial, measured bone to bone. A breadth across the deltoid caps on the skin is normally 3–5 cm wider, so these two rows are not like for like. They will be re-measured on the fitted skeleton (acromion landmarks).

**Observations.** Bust and hips are slightly over the guide, partly because of the fused clothing. The waist is just under it. Muscle definition is softer than on the reference sheet.

An earlier run of this script was wrong in four places, all now fixed:
- the bust included the arms;
- a ponytail sliver gave a 0.3 cm waist;
- the shoulder breadth included the A-pose arms;
- crotch height was used in place of hip height.

## F01a — Female head / neck / torso shell (6 Nov, work in progress)

The owner chose to **keep the fitted athletic wear**: the sports bra and shorts are part of her body form, as supplied.

The builder is `scripts/retopology/female/build_f_shell.py`. It follows the same loop convention as the male, so the two characters share topology conventions, but it is built on her own surface. Every height and border is measured on her source, and nothing comes from the male mesh or from scaling. The convention:
- half body plus a Mirror modifier;
- horizontal torso loops;
- socket, face, ear and pelvis openings;
- meridian bands;
- a Coons cap on the crown.

Her own values:

| Feature | Value |
|---|---|
| Pelvis opening | 0.960 m, above her gluteal cleft |
| Armpit | 1.21 m |
| Socket loops | 1.212–1.336 m, every 7.75 mm |
| Arm-root line | x = 0.152 m |
| Trapezius / neck base | 1.336–1.372 m |
| Jaw border | 1.420 m at the chin, rising to 1.468 m at 80°; read from radius profiles taken from a fixed neck axis |
| Occiput | 1.478 m |
| Head loops | 1.488–1.552 m, every 8 mm |
| Head centre | (0, −0.019, 1.53) |
| Ear | 1.475–1.535 m, 88–124°; the jaw loop is its lower edge |

Female-specific handling:
- **Body axis:** taken from the large section loop that crosses the midline and holds the front-most point. This ignores the ponytail and the thin centre-front fin of the bra.
- **Placement rays:** use her surface without the ponytail and take the outermost layer within 15 mm. The fused bra and shorts lie over the skin inside the source, so the first hit would otherwise be the hidden skin.
- **Snapping and projection:** nearest-surface queries also drop covered faces (fabric lying over skin within 6 mm).
- **Crown:** the cap is built without the ponytail tie, giving a smooth scalp dome under it. The ponytail will get its own mesh.

Result:
- 1,527 vertices per half, all quads, 51 rows × 34 columns.
- Edge length p5 / median / p95: 6.1 / 10.6 / 27.4 mm. The shortest edge is 2.8 mm, in the throat where the face columns converge, as on the male.
- Report: `female_f01a/shell_report.json`. The checkpoint file is read-only and not in git.

Still to do, in order:
- the face loop system and ears;
- the arms from her sockets, and the hands;
- the pelvis, legs and feet;
- the ponytail as its own mesh;
- densify / projection, including the strip under the bra band's lip;
- skeleton fit;
- the standing review.

## F04a — Female full-body cage (6 Nov, work in progress)

All six steps run on her own source. Each builder is a female script in `scripts/retopology/female/` that follows the male loop conventions, with every landmark measured on her:

| Step | Script | What is hers |
|---|---|---|
| F01b shell | `build_f_shell.py` | three meridian rows between her steeply slanting jaw and the head loops (1.496 m upward); 7 under-chin rows; 18 socket loops, giving a 64-vertex socket and 32-vertex arm rings |
| F02a face | `build_f_face.py` | landmarks below; midline rows placed from her landmarks; mouth and nose rows chosen near the midline |
| F02b ears | `build_f_ears.py` | same method as the male, on her ear opening |
| F03a arms | `build_f_arms.py` | arm selection x > 0.155 m; upper arm fitted at 1.12–1.22, forearm at 0.92–1.01; shoulder joint at z 1.30; wrist search 0.84–0.93; elbow placed by proportion (below) |
| F03b hands | `build_f_hands.py` | same method, on her hands |
| F04a legs | `build_f_legs.py` | crotch ≈ 0.79 m (the shorts' inseam hem is lower, ≈ 0.70 m); hip loops 0.938–0.806 m; knee search 0.38–0.54, ankle 0.09–0.20 |

**Face landmarks (F02a):**
- Midline at x = −0.5 mm: her face is symmetric, unlike the male's.
- Nose and mouth read from a curvature map of a 0.5 mm front depth map:
  - alae at ±16.5 mm, alar groove top at z 1.490, subnasale 1.4725, nose tip 1.485;
  - lip line 1.453, mouth corners at ±23.5 mm, upper vermilion 1.4605, lower 1.441.
- **Eyes:** her eye region is a smooth hollow with no lid crease in the geometry, so the closed-lid line follows her painted eyes. On the +x side: inner corner 14 mm, outer 44 mm, z 1.5105–1.5205. The −x side is mirrored.

**Elbow (F03a):** her A-pose arm is almost straight, so the male's line-intersection method put the elbow only 0.19 m below the shoulder joint. The elbow is placed instead at 0.56 of the shoulder-joint-to-wrist length, along her measured centroid path. This gives z ≈ 1.03, which matches the surface narrowing at 1.02.

**Projection target:** her source without the hanging ponytail. Fabric-covered skin is left out only where the layer above faces the same way, as fused fabric does; the arm–torso and thigh gaps keep both surfaces. Forward rays at bra height follow the bra's centre panel.

**Result:** 12,330 quads, 0 non-quads, 0 boundary edges; closed from head to toes.
- Checkpoint `HGPT_Female_Retopo_F04a_Legs_WIP.blend` (`2d1f2488e176…`), read-only, not in git.
- Reports: `female_f04a/`.

**Next:**
- crossing / untangle check;
- densify / projection: the nose tip, the under-chin band and the bra-band lip still cut under the surface;
- the ponytail mesh;
- the skeleton fitted to her proportions;
- the standing review.

## F09b — Female standing model completion (6 Nov): candidate for the owner's visual approval

**Status: CANDIDATE, not approved.** Male 07c is untouched. Nothing was merged into production.

**Candidate:** `HGPT_Female_F09b_TexFix_WIP.blend` (read-only, SHA-256 `bf67fc71928b49d89380680f2e5dcde966848378dd9d60a84d81c30fef33883e`). It lives in the session workspace `hgpt_ws/female/retopo/`, because licensed geometry and `.blend` files are never committed.

**Chain:** every step was written to a new file, and earlier checkpoints are locked:

F04a → F03d hands → F04d legs → F05c untangle → F06a densify → F06b untangle → F06c fit-out → F06d untangle → F06e hands outside → F06f untangle → F07a clothing → F07b ponytail → F08a skeleton → F08b bind and stand pose → F08c hems → F09a bake → F09b texture fix.

Reports for each step are in `female_f09a/`.

### Geometry and topology
- **Body:** 50,090 vertices and 50,088 quads, with 0 non-quads and 0 boundary edges (closed).
  - Self-intersecting face pairs: 754, almost all in the hands (palm 672, fingers 82).
- **Deviation of the visible clothed surface from her source:**
  - head, hands and feet: p95 0 mm;
  - back hair: p95 0.42 mm;
  - trunk and limbs: p95 0.6 mm, p99 2.4 mm.
  - Coverage from her source to the new surface: p95 3.7 mm (`source_comparison.json`).
- **Nose, chin and bra band:** the parts that sat under the surface (F04a) were fitted out in F06c–F06f.
- **Separate, removable garments:**
  - bra: 1,917 faces;
  - shorts: 1,826 faces.
  - Both have Solidify 1.2 mm, hems straightened along her surface, and a 0.6 mm lift.
- **Ponytail:** a separate mesh of 3,547 vertices and 6,236 faces (a decimated copy of her source hair).
- **Textures:** baked from her source albedo, then cleaned up in F09b:
  - 119,704 fabric-coloured texels repainted on uncovered skin;
  - black ponytail texels filled;
  - skin-coloured hem bands on the garments set to the fabric colour.

### Proportions vs source (clothed; tape-measure sections at the same heights)

| Measure | New | Source |
|---|---|---|
| Height | 1.680 m | 1.680 m |
| Bust | 94.9 cm | 94.7 cm |
| Underbust | 72.8 cm | 72.9 cm |
| Waist | 63.5 cm | 63.4 cm |
| Hips | 99.3 cm | 99.5 cm |
| Thigh | 54.5 cm | 54.6 cm |
| Calf | 35.0 cm | 35.0 cm |
| Upper arm | 30.5 cm | 30.6 cm |
| Deltoid breadth | 45.3 cm | 45.3 cm |

Hip width differs by −1.1 %. Without the garments, the body measures bust 93.6 cm and hips 97.6 cm.

### Clothing assumptions (no evidence in the source)
- The source has its garments fused to the skin, so it gives no evidence of the body underneath.
- Under the garments, the body is the garment shape inset by 3 mm, with light Taubin smoothing.
- The breasts keep the supported bra shape.
- No nipples, genital or other anatomical detail was invented.

### Skeleton
- Fitted to her own measured joints, not scaled from the male.
- 67 bones (64 deform), with canonical names, hierarchy and roll (`canonical_rig_conventions.json`).
- **Joint positions:**

  | Joint | Position (m) |
  |---|---|
  | Shoulder (GH) | (±0.167, 0.011, 1.32) |
  | Elbow | z 1.030 |
  | Wrist | z 0.847 |
  | Hip | (±0.091, −0.031, 0.855) |
  | Knee | z 0.4325 |
  | Ankle | z 0.0925 |

- **Segment lengths:** upper arm 320.8 mm, forearm 221.4 mm, thigh 429.7 mm, shin 342.6 mm.
- **Limb bones vs the soft-tissue centre line:** 2–4°. The thigh is 6.6–8°, which is expected from the medial femoral head.
- **Bind:** 0 unweighted vertices, at most 4 influences.
- **Natural standing pose:** arms 10° from vertical and 6° forward, elbows bent 12°.
- No exercise animation and no shoulder-deformation work.

### Remaining defects (visible in the sheets; not hidden by shading)
1. **Body under the garments:**
   - raised ridges where the strap and band edges were (front shoulders, upper back);
   - staircase steps at the old garment boundary in the wireframe;
   - a front-chest crease.
2. **Hands:**
   - thumb-web chord faces (up to 17 mm from the source);
   - a dark crease line on the back of each hand;
   - self-intersections in the palms and between fingers;
   - the `thumb_01_l` joint sits marginally outside the body.
3. **Front-armpit chord faces** (up to 15 mm from the source).
4. **Toes:** joined, not individually separated.
5. **Ponytail:**
   - made of decimated triangles, with a streaky, glossy look and dark folds;
   - a loose strand shard beside the face in the side view.
6. **Bra:** the front band shows a light patch of baked texture at centre front.
7. **Rig:** the male helper and corrective bones are deferred.

Review sheets are kept in the session scratchpad (`sheets_F09b/`):

- `01` natural stand (texture and clay);
- `02` source vs new, same cameras;
- `03` Option 4 reference vs new;
- `04` close-ups;
- `05` body without clothing;
- `06` topology wireframes.

## F10 – F11a — Female standing corrections (6 Nov): candidate for the owner's visual approval

**Status: CANDIDATE, not approved.**
- No exercise animation and no shoulder-deformation development has started.
- Male 07c is untouched.
- Every step is saved as a new, read-only file in the session workspace `hgpt_ws/female/retopo/`. Licensed geometry is never committed.

### Checkpoints

| Checkpoint | Scope | Script |
|---|---|---|
| F10a | Bra rebuilt symmetrically from its complete left half, both front straps and the over-shoulder strap segments added, flap into the armpit removed | `fix_bra_f_blender.py` |
| `HGPT_Female_F10b_BodyRepair_WIP.blend` (`b9b81dec…`) | Armpits repaired, hands repaired, body under the garments rebuilt | `repair_body_f_blender.py` |
| `HGPT_Female_F10c_Finish_WIP.blend` (`cab739f9…`) | Toes, textures, ponytail, garment weights re-transferred from the skin | `finish_f10c_blender.py` |
| `HGPT_Female_F10d_Rig_WIP.blend` (`e1266807…`) | Rig contract check: 63/63 canonical bones; bone roll aligned to the male in the parent frame (`metacarpal_index_r` was flipped by 173°); left thumb joint moved inside the hand | `rig_contract_f_blender.py` |
| `HGPT_Female_F10e_BreastRig_WIP.blend` (`b1ea217c…`) | Her own breast weights and the `breast_l` / `breast_r` helpers (see `docs/FEMALE_CHEST_BRA_MOVEMENT_REQUIREMENTS_20261106.md`) | `breast_rig_f_blender.py` |
| **`HGPT_Female_F11a_ChestGroin_WIP.blend` (`eafbc941…`) — the candidate** | Chest and groin rebuild, garment fit | `chest_groin_f_blender.py` |

### F11a changes

- **Chest:** two breast forms with a soft sternal valley, replacing the merged shelf.
  - The midline is eased back towards a sternum line, at most 30 mm, with a cosine fall-off over 55 mm.
  - The pinched notch at the top of the sternum is filled, and the upper poles are smoothed.
  - The bra's centre front is eased towards the sternum while the cups stay full.
- **Groin:**
  - The crumpled crotch tab is replaced by a smooth saddle (biharmonic membrane), and webbing below her source's crotch line is lifted.
  - The inner-thigh and glute-to-thigh junctions are smoothed, with a conservative 3 mm mons. No genital detail is modelled.
- **Clothing fit:**
  - 15 mm bands either side of every garment hem are smoothed, which removes the inset staircase lines.
  - Skin clearance under the fabric ramps from 0 at the hem to 1.4 mm.
  - The shorts are lightly smoothed (the stepped waistband is gone) and their crotch is refitted.
  - Skin through the fabric: shorts 2, bra 0 vertices at rest; shorts 2, bra 3 in the standing pose.
  - Shorts off the skin: p95 4.1 mm, max 4.9 mm.
  - Bra off the skin: p95 9.9 mm, max 21.8 mm, where the sports bra spans the cleavage.
  - A lofted shorts gusset was tried and rejected. Her source's inner thighs touch below the crotch, as the body now does.

### Measurements

- **Body topology:** 50,090 vertices, all quads, closed. 52 self-intersecting face pairs (all hands, at the thumb collars), against 233 in F09b.
- **Proportions against her source:** within ±0.2%, except hip width (−0.8%).

### Remaining

- **Thumbs:** the thumb bases still pinch where they meet the hand. This needs a thumb re-topology.
- **Upper back:** a faint Y mark under the ponytail.
- **Chest:** a faint line on the upper chest along the old bra neckline. The sternal valley is conservative.
- **Groin:** soft lines where the inner thighs meet.
- **Bra straps:** small knots where the strap segments join on the shoulders.
- **Ponytail:** still decimated triangles.

Review sheets are in the session scratchpad, `sheets_F11a/`.

## F12 — Female chest and shorts corrections (6 Nov): candidate F12d for the owner's review

The owner withheld approval of F11a for two areas: the breasts still read as one mass (especially clothed), and the
shorts had a pointed protrusion at the crotch. **Nothing here is approved, no V1 checkpoint was made, F11a and
every earlier checkpoint and Male 07c are untouched, and exercise animation remains paused.**

**Causes (geometry inspected, body and garments separately).**
* *Chest:* the body already had two breast forms with a ~30 mm sternal valley (sections at z 1.20). The bra followed
  her source's fused fabric: a near-flat shelf across both breasts, with the cleavage hidden behind it. The F11a bra
  dipped only ~13 mm at the centre, so the clothed chest read as one mass.
* *Shorts:* the protrusion was in the garment, not the body. The F07a–F11a shorts were cut from the body by
  albedo and ended at the crotch in two flaps, a slit, a pointed front tab and a thin spike underneath.

**What changed (scripts in `scripts/retopology/female/`; checkpoints are local only, read-only).**

| Checkpoint | Script | Change |
|---|---|---|
| F12a `…F12a_ChestShorts_WIP` (`ab44efb0…`) | `rebuild_shorts_f_blender.py`, `bra_cups_f_blender.py` | Shorts rebuilt from body faces: waistband from the old top hem, leg-opening planes fitted to the clean old hems, no tab, slit or spike. Bra front eased onto the body's sternal valley (gore 3.5 mm over the sternum, smoothstep out to the unchanged outer cups), so it reads as two supported cups. Skin texels just outside the hems cleaned. |
| F12b, F12c | `gusset_shorts_f_blender.py` (earlier states) | Superseded intermediates, never reviewed, deleted for disk space. Their shorts weights were wrong (below). |
| **F12d `…F12d_ChestShorts_WIP` (`89df9517…`)** | `gusset_shorts_f_blender.py` | Crotch gusset plus a full rebuild of the shorts weights. |

The F12d gusset is a regular quad grid joined to the F12a front and back crotch hems:
* it is laid by rays from inside the pelvis and relaxed as a collision-constrained membrane, so it spans the
  inguinal creases instead of following them;
* each vertex keeps its x position, tapering to 55 % of the hem width under the crotch;
* it sits ≥ 3 mm over the skin, and the rest of the shorts ≥ 1.8 mm;
* the shorts' weights come from the nearest skin point (top 4 influences, normalised).

Defects found in F12a during validation and fixed in F12d (both are documented in the F12a script):
1. its leg openings were raised to the *source's* crotch line, so it had **no crotch panel** (bare skin from y −0.06
   to +0.06);
2. swapping the shorts' mesh datablock lost the vertex-group names, so the **weights pointed at missing groups**.
   This was invisible at rest, but the shorts lifted 30–67 mm off the skin at 45–90° hip flexion.

Four attempts to re-cut the shorts down to the body's crotch line were rejected. They gave a hanging flap, a string
or folded hems, because the crotch underside is only ~2 cm wide between the creases.

**Validation (F12d; `female_f12/*.json`).**

Standing pose:
* 0 skin vertices outside the shorts (F11a: 1).
* Shorts off the skin: p50 3.6, p95 4.4, max 12.0 mm; 4 vertices over 10 mm.
* Shorts: 1 part, 0 non-manifold edges.
* Body: unchanged from F11a (50,090 vertices, all quads, closed, 52 self-intersecting pairs, all in the hands).
* Proportions within ±0.3 % of the source, clothed.

Limited hip-flexion check (`scripts/meshy/female/hip_flexion_clearance_f_blender.py`; structural only, no pelvis tilt, no correctives):

| Pose | Skin outside shorts | Shorts off skin p95 / max (mm) | Groin self-intersections |
|---|---|---|---|
| standing | 0 (F11a 1) | 4.4 / 12.0 | 0 |
| hip 45 / knee 60 | 0 (F11a 1) | 4.1 / 11.9 | 0 |
| hip 90 / knee 90 | 12 (F11a 23) | 3.8 / 10.9 | 0 |

Limited arm-elevation check (`chest_bra_elevation_test_f_blender.py`, glenohumeral only):
* Unchanged from F10e: breast core stretch 1.00 at all elevations; centroid shift 2.6 / 2.1 / 6.4 / 9.8 / 11.4 mm at
  0 / 45 / 90 / 135 / 170°.
* Skin outside the bra: 81 / 2 / 27 / 29 / 20 (F10e: 76 / 5 / 29 / 34 / 24).
* The bra cups now span part of the sternal valley: 70 cup vertices are more than 6 mm off the skin (max 9.3 mm;
  F10e: 1).

**Remaining (not hidden).**
* Small corner tips where the gusset edges meet the leg openings, visible in the front and back views.
* The shorts waistband keeps the source's raised elastic band, with small steps.
* The bra has 3 parts and 1 non-manifold edge.
* Elsewhere: the thumb bases and hand self-intersections, the strap knots at the shoulders, and the ponytail's
  triangles.

**Review sheets** (renders are local only) are produced by `review_chest_shorts_f_blender.py`,
`chest_sections_f_blender.py` + `chest_sections_draw.py` and `make_f12_sheets.py`:
1. chest with and without the bra (front, 3/4, side, sternum);
2. shorts (front, back, side, from below);
3. shorts and body separately;
4. clearance diagnostic;
5. chest sections;
6. hip-flexion check;
7. arm-elevation check.

Sheets 1–5 compare F11a with F12d.
