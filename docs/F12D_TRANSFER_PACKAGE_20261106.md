# Home Gym PT — Female F12d handover to ChatGPT Work (6 Nov 2026)

**Status: F12d is a WIP candidate. The owner has NOT approved it. Do not mark Female V1 approved.** Male 07c is
the approved standing base and is not part of this package. Do not change it.

## 1. What is in this transfer (8 ZIP files, each < 24 MB)

| File | Contents |
|---|---|
| `HGPT_F12d_START_HERE.zip` | this guide, `MANIFEST.json`, `reassemble_f12d.py`, `verify_f12d_blender.py`, the Blender open-check result, F10–F12 reports, review sheets, the modelling / test scripts, docs |
| `HGPT_F12d_blend_part01of07.zip` … `part07of07.zip` | the actual checkpoint `HGPT_Female_F12d_ChestShorts_WIP.blend`, split byte-for-byte into 7 chunks (one chunk per ZIP; no re-encoding, no downsampling) |

**The checkpoint:**

| Field | Value |
|---|---|
| File | `HGPT_Female_F12d_ChestShorts_WIP.blend` |
| Size | 151,227,275 bytes |
| SHA-256 | `89df9517421d983e0de812efd2d18a660e19bd6fa0284cdc45945b19affa3b6c` |
| Saved with | Blender 5.2.1 LTS (Python `bpy` module). Open it with Blender 5.2.x; older versions may not read it. |
| Original path (Claude cloud scratch, ephemeral) | `<scratchpad>/hgpt_ws/female/retopo/HGPT_Female_F12d_ChestShorts_WIP.blend` (read-only) |

`MANIFEST.json` holds the size and SHA-256 of every part ZIP and every chunk.

## 2. Rebuild and verify

1. Put all 8 ZIPs in one folder. Unzip only `HGPT_F12d_START_HERE.zip`, into that same folder. Leave the 7 part ZIPs zipped.
2. Run `python3 reassemble_f12d.py`. It:
   - checks the SHA-256 of each part ZIP and each chunk;
   - concatenates the chunks in order;
   - checks the rebuilt file's size and SHA-256;
   - renames the file only when everything matches;
   - refuses to overwrite an existing `.blend`.

   Expected last line:
   `VERIFIED HGPT_Female_F12d_ChestShorts_WIP.blend  151227275 bytes  sha256 89df9517…a3b6c`
3. Independently: `sha256sum HGPT_Female_F12d_ChestShorts_WIP.blend` (or `certutil -hashfile <file> SHA256` on Windows).
4. Open check in a **fresh** Blender:
   `blender -b --factory-startup --python verify_f12d_blender.py -- HGPT_Female_F12d_ChestShorts_WIP.blend f12d_check.json`.
   Compare the result with `F12d_verify_blender521.json` (Claude's run).
   - Objects: 9.
   - Body: 50,090 vertices / 50,088 faces.
   - Bra: 2,541 / 2,147.
   - Shorts: 2,075 / 1,939.
   - Ponytail: 3,539 / 6,233.
   - `HGPT_FEMALE_RIG`: 69 bones, 66 deform.
   - Images: 7, all packed. Linked libraries: none.
5. If any step fails, **stop**. Do not substitute F11a, the Meshy source or a script re-run and call it F12d.

## 3. What the .blend contains (self-contained)

**Character objects:**

| Object | Contents |
|---|---|
| `HGPT_FEMALE_RIG` | Armature: the 63-bone common contract plus `breast_l` / `breast_r` deform helpers and the extra bones; 69 bones in total. Natural standing pose stored as the pose; rest pose = bind. |
| `HGPT_Female_Body` | Body: all quads, closed. Armature-skinned, 67 vertex groups. Material `HGPT_Female_Body_mat` with packed 4K albedo. |
| `HGPT_Female_Bra` | Separate garment: Armature + Solidify (`Fabric_Thickness`), packed 2K albedo. |
| `HGPT_Female_Shorts` | Separate garment: Armature + Solidify, packed 2K albedo. Weights rebuilt from the skin in F12d. |
| `HGPT_Female_Ponytail` | Separate mesh, single-bone weighted, packed 2K albedo. |

**Source references (read-only):**
- `HGPT_FEMALE_SOURCE_Mesh_0`, `HGPT_FEMALE_SOURCE_TEXTURED` and `HGPT_FEMALE_SOURCE_BODY_TARGET`: her Meshy Pro source, 257,175 vertices.
- `Image_0`–`Image_2`: the source textures, packed.
- `HGPT_Female_Shell`: an early retopology scaffold, unused.

`bpy.utils.blend_paths()` lists the original source `.blend` path only as a weak reference left by appending. Nothing is linked and every image is packed.

**Original source files** (owner-supplied; not in this package, because the meshes and textures are embedded above):

| File | SHA-256 |
|---|---|
| `HGPT_Meshy_Female_Pro_1.68m_Clean_Unrigged.blend` | `4b53bebe89ca28fb84a1458fcb34da5d4ca78bda0c03f50d2bf39d8e468fc782` |
| `HGPT_Meshy_Female_Pro_1.68m_Clean_Unrigged.glb` | `de8ab078f2510c18bf3b05e82d3840583138f3c3feb6407fda7f24cfd6bf885b` |

**Licence:** Meshy-generated geometry. Do not commit it to the public GitHub repository or publish it until the Meshy licence (generation tier and commercial rights) is documented.

## 4. Other checkpoints (preserved in Claude's scratch, NOT in this package)

Full SHA-256 values are in `MANIFEST.json → other_checkpoints_not_in_this_package`. They include F11a
(`eafbc941…0573`, the rollback), F12a, F10b–F10e, F09a/F09b, F01a–F08c and Male 07c PROXY (`e9448c68…6866`).
None was modified. F12b and F12c were superseded gusset trials with broken shorts weights: never reviewed, and deleted.
Claude's scratch is ephemeral. Unless the owner also exports those files, **only F12d survives this transfer**.

## 5. What F12d changed (since the F11a review)

- **Bra:** the front is eased onto the body's sternal valley (3.5 mm over the sternum at the centre), so it now
  reads as two supported cups instead of one shelf. The body's two breast forms are unchanged (~30 mm valley).
- **Shorts:**
  - rebuilt with no front tab, slit or spike;
  - a continuous quad gusset under the crotch, laid as a collision-constrained membrane, tapered to 55 % width,
    ≥ 3 mm over the skin;
  - every shorts weight rebuilt from the skin (nearest skin point, top 4 influences, normalised).

**Defects found and fixed during F12** (both are documented in `rebuild_shorts_f_blender.py`):
- The F12a shorts had no crotch panel.
- The F12a shorts had lost their vertex-group names, so they lifted 30–67 mm off the skin in hip flexion.

## 6. Latest diagnostics (F12d; JSON in `reports/female_f12/`)

**Standing:**
- 0 skin vertices outside the shorts. Shorts off the skin: p95 4.4 mm, max 12.0 mm.
- Body: 52 self-intersecting face pairs, all in the hands.
- Clothed proportions within ±0.3 % of the source.

**Limited hip-flexion check** (structural only, no pelvis tilt):

| Pose | Skin outside shorts | F11a |
|---|---|---|
| hip 45° / knee 60° | 0 | 1 |
| hip 90° / knee 90° | 12 | 23 |

Groin self-intersections are 0 in every pose.

**Limited arm-elevation check** (glenohumeral only, 0 / 45 / 90 / 135 / 170°):

| Measure | 0° | 45° | 90° | 135° | 170° |
|---|---|---|---|---|---|
| Skin outside the bra | 81 | 2 | 27 | 29 | 20 |
| Breast centroid shift (mm) | 2.6 | 2.1 | 6.4 | 9.8 | 11.4 |

Breast core stretch is 1.00 at every elevation. The 0° pose puts the arms straight down through the torso sides, which accounts for its high count.

## 7. Remaining defects (visible; not hidden)

**Garments:**
- Shorts: small corner tips where the gusset meets the leg openings, front and back. The gusset point is visible in some views and needs owner review.
- Shorts waistband: keeps the source's raised elastic band, with small steps.
- Bra: 3 parts and 1 non-manifold edge. 70 cup vertices are > 6 mm off the skin (max 9.3 mm) where the cups span the valley.
- Straps: knots at the shoulder junctions.

**Body:**
- Thumb bases pinch, and 52 hand self-intersections remain (needs a thumb re-topology).
- A faint Y on the upper back and a faint neckline line on the upper chest.
- Some body vertices have a weight sum up to 1.59 (breast helpers). Blender's Armature modifier normalises this; normalise explicitly before export to other engines.

**Other:**
- Ponytail: decimated triangles.
- Raised arms: shoulder, armpit and strap distortion. Recorded for the movement phase; no shoulder-deformation cycle has been started.

## 8. Regenerating the diagnostics (scripts in `scripts/`, also on GitHub)

```
B="blender -b --factory-startup --python"     # or: python3 with the bpy 5.2 module
$B scripts/meshy/female/review_chest_shorts_f_blender.py -- F12d.blend renders F12d      # clay views + clearance map
$B scripts/meshy/female/chest_sections_f_blender.py -- F12d.blend sec_F12d.json && python3 scripts/meshy/female/chest_sections_draw.py sec_F12d.json renders/sec_F12d.png
$B scripts/meshy/female/hip_flexion_clearance_f_blender.py -- F12d.blend renders/hip hip_F12d.json
$B scripts/meshy/female/chest_bra_elevation_test_f_blender.py -- F12d.blend renders/elev chest_test_F12d.json
$B scripts/meshy/female/topology_stats_f_blender.py -- F12d.blend topology_F12d.json
$B scripts/meshy/female/compare_f_source_blender.py -- F12d.blend source_comparison_F12d.json
python3 scripts/meshy/female/make_f12_sheets.py renders sheets F12d   # needs the same renders for F11a too
```

To rebuild F12d from F11a:
`bra_cups_f_blender.py` and `rebuild_shorts_f_blender.py` (→ F12a), then `gusset_shorts_f_blender.py` (→ F12d).
Every script refuses to overwrite its output.

## 9. Rules carried over from the owner

- Do not hide problems with textures, shading or arbitrary corrective shapes.
- Never overwrite a checkpoint. Save each iteration under a new name with its full SHA-256.
- Do not change Male 07c.
- Full exercise animation and any prolonged shoulder-deformation work stay paused.
- Stop for the owner's visual approval of the female standing anatomy and clothing.

**GitHub:**
- Repository: `anyangle1409-code/animation-software`.
- Claude branch: `claude/home-gym-pt-animation-txux66`, F12d commit `3bee9e1f1f6f8ca8fe21bcbec0ef892974cb14ca`.
- Work's handoff branch: `chatgpt/f12d-work-handoff-20261106` (`docs/WORK_F12D_CONTINUATION_20261106.md`).
- Work its own new branch. Never commit `.blend`, `.glb` or Meshy textures.
