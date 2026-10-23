# V14 238,065 vs 238,067 vertices: root cause

Branch: `claude/v14-recovery-investigation-20261023`.

This was a read-only investigation. Nothing in W8, V14, R120, the production skeleton, `ORIGINAL_v1` or ChatGPT's workbench branch was opened for writing. No .blend file is committed.

## Answer

The two-vertex difference is not caused by a settings difference and not by the later stages. W8 itself cannot be reproduced exactly: its mesh refinement is non-deterministic. V14 inherits whichever triangulation its own W8 run happened to produce.

**1. The step that varies.** `scripts/body_v2/refine_torso_blender.py::refine()` is called by `build_body_v2_sculpt_blender.py` when it builds W8. It collects BMesh edges and faces in Python `set`s and passes them to:
- `bmesh.ops.subdivide_edges(edges=list(edges))`;
- `bmesh.ops.beautify_fill(faces=reg, edges=list({...}))`.

Python sets of BMesh elements iterate in memory-address order, which differs from process to process. With the same input file, the same code and the same machine, every run produces:
- **the same vertex positions** (the subdivision is linear, so the point set is identical);
- **different triangles**, because of the order in which `beautify_fill` flips edges (its tie-breaking) and the order of the new vertices.

The builder then smooths and sculpts with neighbour averages, so a different triangulation becomes a different surface. Measured on my two local W8 builds (the archived w8 run and L0, same code at 53ade15f / 6f781b74, same day), the offsets differ by up to **5.16 mm**. 499 vertices differ by more than 1 mm and 19,147 by more than 0.01 mm. This is also the explanation for the ledger's "W8 offsets differ by up to 3.59 mm" against the archive.

**2. How that becomes 699 vs 700.** The V14 leg step (`legs_v2_blender.py`) cuts each leg at z = z0 + 0.45·H. It deletes the old leg skin below the cut, and `bisect_plane` creates one vertex per edge that crosses the plane. The final vertex count is:

```
final = W8 vertices − old leg vertices removed + cut-loop vertices + ring vertices + foot vertices
```

From the two reports, the ring and foot terms are identical (rings 168×165 and 168×166, feet 26,877 each, total 109,362):

| | Archived V14 | Reconstruction |
|---|---:|---:|
| W8 vertices | 219,974 | 219,974 |
| Cut loops (right / left) | 699 / 696 | **700** / 696 |
| Old vertices removed (from the identity) | 92,664 | **92,667** |
| Final | 238,067 | 238,065 |

On the reconstructed W8, the cut creates one more vertex on the right leg and removes three more old vertices: net −2. Both follow from the reconstructed W8 having a different surface and triangulation at the cut height. These are not two vertices missing anywhere specific.

**3. The archived V14 was not built from the archived W8.** It was built (run L15, `legs_v2_blender.py` at bd439886) from a second W8 build, `L0`. L0 was built straight after the archived w8 run, with the same builder plus the `V2_SAVE_BLEND` block appended at the very end (53ade15f → 6f781b74). Only that build's .blend existed, so no rebuild can match the archived V14 bit for bit unless the refinement is made deterministic and L0's exact triangulation is recovered.

## Evidence

**A. `refine()` determinism, local** (bpy 5.2.1, R41 sha256 `4c44b1fe…af2e`). Script: `scripts/v14_investigation/refine_determinism_blender.py`. Outputs: `scripts/v14_investigation/evidence/local_refine_*.json`.

| Run | `beautify_geom` | Vertex set | Triangles (geometric hash) |
|---|---|---|---|
| As the builder, process 1 | 45861, 1147, 60943, 1360, 269418, 10883 | `ce90d1d7…` | `4bfd5274…` |
| As the builder, process 2 | 45869, 1147, 60965, 1360, 269440, 10884 | `ce90d1d7…` | `83d4b26b…` |
| Index-sorted, process 1 | 45864, 1144, 60934, 1357, 269375, 10890 | `ce90d1d7…` | `aaf86a9f…` |
| Index-sorted, process 2 | 45864, 1144, 60934, 1357, 269375, 10890 | `ce90d1d7…` | `aaf86a9f…` |

The full builder logs give more independent `beautify_geom` values for the same input:

| Build | `beautify_geom` |
|---|---|
| Archived w8 | 45863, 1141, 60949, 1357, 269463, 10873 |
| L0 (input to the archived V14) | 45858, 1144, 60946, 1357, 269382, 10884 |
| A third build today | 45859, 1144, 60945, 1360, 269455, 10881 |

**B. The cut replayed on L0, local.** Script: `scripts/v14_investigation/cut_accounting_blender.py`. Output: `evidence/local_cut_L0_archiveV14input.json`.
- **Cut loops:** 699 / 696.
- **Old vertices removed:** 46,336 + 46,328 = 92,664.
- **Vertices on or near the plane:** none lies exactly on it; the closest is 0.001 mm away.
- **Predicted total:** 238,067, the archived figure exactly.

**C. The later stages are not involved.** Every leg-step run I made from L0 with `legs_v2_blender.py` (L10–L18, versions v10–v18, with and without torso relief, `back_depth_smooth`, `pec_junction` and the hip fill), plus the legs-only base, reported cut loops 699 / 696 and 238,067 vertices. The stages that appear only in the reconstruction's report move vertices and never add or remove them.

**D. GitHub-hosted runs.** Workflow: `.github/workflows/v14-recovery-investigation.yml`, run 40020020099. It does the following:
- runs `refine()` four times on the R41 checkout at 025d5f28: twice as the builder runs it, twice index-sorted;
- replays the cut on the preserved reconstructed W8 (artifact 12487119841);
- summarises the results.

Results are recorded below once the run has finished.

## What this means for integration

- **Do not add or delete two vertices.** The archived V14 is one sample from a non-deterministic build. A reconstruction can only match it by chance.
- **Make the build deterministic first.** In `refine()`, pass sorted lists instead of sets, e.g. `sorted(edges, key=lambda e: e.index)` after `index_update()`. Do the same for every other `list({...})` passed to a `bmesh.ops` call: `legs_v2_blender.py` (bisect geometry) and `rebuild_v2_blender.py` (bisect). `--sorted` above shows this gives identical runs. This is a code change for a separate candidate branch. It is **not** applied to the original scripts here.
- **Exact equivalence with the archive is not recoverable** without L0's triangulation, because L0 was never committed. Equivalence would have to be redefined: matching counts within run-to-run spread, or a deterministic rebuild declared as the new reference by the owner.
