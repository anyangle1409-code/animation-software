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

**D. GitHub-hosted runs.** Workflow: `.github/workflows/v14-recovery-investigation.yml`, on `ubuntu-24.04` with the `bpy==5.2.0` wheel and R41 checked out at 025d5f28.

Runs (all jobs passed):
- [40020020099](https://github.com/anyangle1409-code/animation-software/actions/runs/40020020099)
- [40020438245](https://github.com/anyangle1409-code/animation-software/actions/runs/40020438245)
- [40020914504](https://github.com/anyangle1409-code/animation-software/actions/runs/40020914504)

The results are published as check-run annotations on the `summarize` job, which can be read through the API without downloading artifacts.

*`refine()` on GitHub:*

| Run | `beautify_geom` | Vertex set | Triangles |
|---|---|---|---|
| As the builder, 1 | 45859, 1144, 60962, 1360, 269434, 10880 | `ce90d1d7…` | `210ad3c1…` |
| As the builder, 2 | 45859, 1150, 60947, 1357, 269407, 10901 | `ce90d1d7…` | `9377e6ff…` |
| Index-sorted, 1 | 45864, 1144, 60934, 1357, 269375, 10890 | `ce90d1d7…` | **`aaf86a9f…`** |
| Index-sorted, 2 | 45864, 1144, 60934, 1357, 269375, 10890 | `ce90d1d7…` | **`aaf86a9f…`** |

The vertex set is identical in all eight runs, local and GitHub. The as-builder triangulation differs every time. The sorted triangulation is identical locally (bpy 5.2.1) and on GitHub (bpy 5.2.0): it is deterministic across machines and Blender patch versions.

*The V14 cut replayed on the preserved reconstructed W8* (artifact 12487119841, read-only), next to L0:

| W8 input | Cut height `zc` (m) | Stature (m) | Right loop / removed | Left loop / removed | Predicted V14 total |
|---|---|---|---|---|---|
| L0, the archived V14's input | 0.8338477725 | 1.8561579757 | 699 / 46,336 | 696 / 46,328 | **238,067** (= archive) |
| Reconstructed W8 | 0.8338477725 | 1.8561579757 | **700 / 46,339** | 696 / 46,328 | **238,065** (= reconstruction) |

The cut plane and stature are identical to the last digit, and the left leg is identical.

The whole difference is on the right leg: bisect creates one more vertex there (700 vs 699) and deletes three more old vertices (46,339 vs 46,336), net −2.

The right leg's skin within 1 cm of the cut differs between the two W8 files in both vertex positions (band hash `cdaee16f…` vs `56bc5edc…`) and triangles (`864d4581…` vs `6f855116…`). That is what the non-deterministic refinement and the neighbour-average sculpting downstream of it produce.

## What this means for integration

- **Do not add or delete two vertices.** The archived V14 is one sample from a non-deterministic build. A reconstruction can only match it by chance.
- **Make the build deterministic first.** In `refine()`, pass sorted lists instead of sets, e.g. `sorted(edges, key=lambda e: e.index)` after `index_update()`. Do the same for every other `list({...})` passed to a `bmesh.ops` call: `legs_v2_blender.py` (bisect geometry) and `rebuild_v2_blender.py` (bisect). `--sorted` above shows this gives identical runs. This is a code change for a separate candidate branch. It is **not** applied to the original scripts here.
- **Exact equivalence with the archive is not recoverable** without L0's triangulation, because L0 was never committed. Equivalence would have to be redefined: matching counts within run-to-run spread, or a deterministic rebuild declared as the new reference by the owner.

## A third unpatched build (local, 23 Oct)

The unchanged builder, run again on the same R41, was followed by the V14 leg step and the cut replay. Evidence: `evidence/local_cut_W8b_third_build.json` and `evidence/local_V14b_third_build_legs_report.txt`.
- `beautify_geom`: 45864, 1144, 60955, 1357, 269431, 10888.
- **Right leg:** 701 / 46,338. **Left leg:** 696 / 46,328.
- **Final count: 238,067.**

| W8 build | Right leg: loop / removed | V14 total |
|---|---|---|
| L0 (the archived V14's input) | 699 / 46,336 | 238,067 |
| Reconstruction (GitHub, 39922636070) | 700 / 46,339 | 238,065 |
| Third build | 701 / 46,338 | 238,067 |

The right leg's skin near the cut differs in all three. The third build's total equals the archive's **by coincidence** (+2 −2 on the right leg). **A matching vertex count is not evidence that two models are the same.** Acceptance checks should compare triangle and position fingerprints, as `cut_accounting_blender.py` does, not counts alone.

## Recovery: the archived V14 reproduced exactly by replaying L0

`scripts/v14_investigation/replay_build_blender.py` runs the unchanged builder in-process. Immediately after `refine()`, it gives the refined mesh the preserved L0 vertex order and triangles:
- every refined vertex is matched to the preserved L0 vertex at the same position (checked to be a one-to-one match at 0.0 mm);
- the vertices are re-ordered and the triangles replaced (R41 has no UVs or other face data);
- L0's refine map is returned, so the builder continues exactly as in the L0 build.

The V14 leg step is then run at the **archived script version** (`legs_v2_blender.py` at bd439886, taken from a scratch copy).

Local result (bpy 5.2.1). Evidence: `evidence/local_replay_*`, `evidence/local_cut_W8r_replay.json`.

| Check | Result |
|---|---|
| Refined rest positions and triangles vs L0 | **identical** (array equality) |
| W8 offsets / proportion vs L0's preserved arrays | max **0.000035 mm** / 0.0000075 mm (float rounding; guard 0.01 mm) |
| `body_v2_report.json` vs L0 | identical except the 6 `refine/beautify_geom` counts. These describe the discarded original triangulation (expected). |
| `skeleton_edits.json` vs L0 | one value differs, in the 16th significant digit (0.01263357708668723 vs …046) |
| Leg-cut fingerprints, both legs (faces, crossings, created / removed vertex IDs, band positions and triangles) | **all identical** to L0 |
| V14 `legs_v2_report.json` vs the archived `draft_v14b_torso/legs_v2_report.json` | **54 / 54 fields identical**: 238,067 vertices, loops 699 / 696, above-cut 6,675, torso relief 60,485, and every other field |
| `compare_replay.py` verdict | **PASS_exact_archived_V14_reproduced = True** |

The new files (not committed, about 200 MB each) have these SHA-256s:
- W8: `1798d839…4c9a`
- V14: `2d707be4…6b84`

The .blend bytes cannot match the archive's own files. L0's .blend hash is `78f30e59…`; it embeds session data and float rounding. Equivalence is established on the geometry, topology, report and cut, not on file bytes.

**Confirmed on GitHub-hosted Blender 5.2.0** in run [40024573317](https://github.com/anyangle1409-code/animation-software/actions/runs/40024573317) (all 9 jobs passed). Job `replay-l0-archived-v14` annotations:
- `PASS_exact_archived_V14_reproduced` True; V14 vertices 238,067; 54 / 54 report fields equal to the archive.
- Cut fingerprints identical to L0; refined rest and triangles identical.
- W8 offsets max deviation 3.5011908e-05 mm, **the same value as locally**, so the replay is reproducible across machines and Blender patch versions.
- The W8 report differs only in `refine/beautify_geom` (5 of the 6 counts on this run). These are the counts of the discarded triangulation.

The same run also repeated the earlier legs: refine as-builder non-deterministic, sorted and patched identical, reconstructed-W8 cut 700/46,339.

**Consequence for the blockers:** blocker 1 (exact archived V14) is resolved by replay. The remaining open question is the owner's choice of the W8/V14 reference: an L0 replay (matches the archive) or a deterministic patched build (new, reproducible, does not match the archive).

## Archived w8 (v13s) and R120 replays

**w8 / v13s:** reproduced. Replaying the preserved w8 arrays (`evidence/build_w8`) gives the following against the committed `review-assets/body_v2/draft_v13s_standing` files, which are byte-identical to that build's originals (SHA-256 checked):

| Check | Result |
|---|---|
| Offsets | max **0.0000347 mm** (the workbench reported 3.59 mm for its reconstruction) |
| Proportion | max 0.0000075 mm |
| Skeleton edits | identical |
| `body_v2_report.json` (275 numeric fields) | only the `refine/beautify_geom` counts of the discarded triangulation differ |

Script: `compare_w8_replay.py`. Evidence: `evidence/local_w8_replay_compare.json`. Verdict: **PASS_archived_w8_reproduced**.

**On GitHub-hosted Blender** (run [40030600165](https://github.com/anyangle1409-code/animation-software/actions/runs/40030600165)):
- **w8 replay: PASS.** Offsets 3.47e-05 mm, proportion 7.5e-06 mm, skeleton edits identical, rest and triangles identical to the preserved arrays. Only the discarded `beautify_geom` counts differ.
- **L0 → V14 replay: PASS again.**
- **R120 replay: 347,916 vertices** (archive 347,917, local replay 347,917).
  - **Occupied voxels:** 2,965,289 (archive 2,965,298, local replay 2,965,299).
  - **Marching cubes:** 251,890 / 503,060 (archive 251,892 / 503,064).
  - **Legs-only base:** 51 / 51 identical again.
  - **Reading:** the rebuild's voxelisation is sensitive at the level of single voxels to sub-micrometre input differences. The marching-cubes counts change by a few between machines; the geometry stays within about 1 mm.

**R120:** close, but not exact. The chain was the L0 replay, then the legs-only base (`legs_v2_blender.py` at bee05007 with `V2_TORSO_RELIEF=0 V2_PEC_JUNCTION=0`), then the rebuild (`rebuild_v2_blender.py` at d5141ad3). It was compared with the session's archived R120 run (RB2; reports in `evidence/archive_R120`, .blend SHA-256 recorded, .blend not committed).

- **Legs-only base report:** 51 / 51 fields identical.
- **R120:** 347,917 vertices and 646,098 faces, both equal to the archive. The rebuild report differs in two places:
  - **Voxels:** occupied voxels differ by 1 (of about 2.97 million), and the parity-disagreement count by 8.
  - **Thigh seams:** they are listed in swapped order, and one seam has one more vertex.
- **Geometry, order-independent** (`compare_r120_replay_blender.py`; evidence `local_r120_replay_geometry_compare.json`):
  - 342,707 of 347,917 vertices are within 0.01 mm of an archived vertex;
  - 5,210 differ, by at most **1.14 mm**, and only 2 by more than 1 mm;
  - matched skin weights differ by at most 0.011.
- **The rebuild twice on the same input file** (`local_r120_rebuild_same_input_twice.json`): every vertex position and weight is identical (0.0 mm). 1,057 seam faces differ, because the seam loops come from a Python set (`loop_on_plane`), so the zipper starts at a different vertex.

**Conclusion for R120.**
- The rebuild's geometry is deterministic for a given input, but extremely input-sensitive. The replayed W8 differs from L0 by about 35 nanometres (float rounding in the builder), and that is enough to flip one ray-parity voxel, which changes the marching-cubes surface locally.
- An exact R120 would need a bit-identical W8. That is not available, because L0's .blend was never preserved and the builder's float rounding is not bit-stable.
- R120 is EXPERIMENTAL in any case.
- **Recommendation:** treat the replayed R120 as the reference if one is needed, and record this tolerance (5,210 vertices, ≤ 1.14 mm). If R120 is pursued, sort the set-ordered seam loops in `rebuild_v2_blender.py` too.

## Deterministic pipeline: proven on a separate candidate branch

Branch `claude/v14-deterministic-candidate-20261023`; see `docs/V14_DETERMINISTIC_CANDIDATE_20261023.md` there.

In GitHub run 40032993456, two independent runners built W8, V14 and R120 from R41. All three came out **bit-identical** (positions, faces, weights, offsets and reports). That needed:
- the `refine()` patch;
- Jacobi relaxation and index-sorted lists in the leg step;
- index-sorted seam loops and bisect inputs in the rebuild.

The run before those leg-step and rebuild fixes (40030796708) showed that the leg step and rebuild had run-to-run variation of their own: up to 0.4 mm in V14, and ±1 vertex in R120.

**Owner choice:**
- **Archived models:** reproduce them by replay (W8 and V14 exact; R120 within 1.14 mm).
- **New reproducible models:** adopt the deterministic candidate.

## Candidate fix (not applied)

`scripts/v14_investigation/CANDIDATE_deterministic_refine.patch` changes only `refine_torso_blender.py`. It adds `_ordered(bm, elems)`, which updates the indices and sorts by index, and uses it for:
- `subdivide_edges`;
- `triangulate`;
- both `beautify_fill` calls (faces and edges).

It applies cleanly (`git apply --check`) and has **not** been applied to `scripts/body_v2`.

Applied to a scratch copy and run in two fresh processes, it gives `beautify_geom` 45864, 1144, 60934, 1357, 269375, 10890 and triangle hash `aaf86a9f…` both times. That is identical to the index-sorted runs locally and on GitHub. Evidence: `evidence/local_refine_candidate_patch_{1,2}.json`. **Confirmed on GitHub-hosted Blender** in run [40021718681](https://github.com/anyangle1409-code/animation-software/actions/runs/40021718681) (all jobs passed): the `patched` leg twice produced `beautify_geom` 45864, 1144, 60934, 1357, 269375, 10890 and triangles `aaf86a9f…`, the same as the sorted leg. Verdicts: R1 (set order non-deterministic) True, R2 (sorted deterministic) True, R3 (patch deterministic and equal to sorted) True.

Integrating it is the owner's decision. It changes W8 itself to a new, reproducible triangulation that is not L0's, so W8, V14 and R120 would need to be rebuilt and re-reviewed. Other `list({...})` set inputs to `bmesh.ops` remain:
- `legs_v2_blender.py`: the leg-cut bisect;
- `rebuild_v2_blender.py`: bisect.

A bisect's result does not depend on input order, but sorting those inputs too would be the conservative choice.

## Remaining blockers

1. ~~**Exact equivalence with the archived V14 needs L0's triangulation.**~~ **Resolved by the replay (see Recovery).** Originally: L0's refined positions, triangles, coarse map and offsets are preserved in `evidence/build_L0/` (with the original files' SHA-256s). A "replay L0" builder mode that loads them instead of calling `refine()` has not been written or tested.
2. **The archived w8 .blend never existed.** That run saved renders and arrays only, and its arrays are preserved in `evidence/build_w8/`. The archive's W8 offsets are therefore also only reproducible by replay.
3. **Owner decision needed:** which W8 becomes the reference (L0 replay, archived w8 replay, or a new deterministic build), and whether to adopt the patch.
4. **GitHub artifacts and logs can't be downloaded from the Claude session** (the blob host is refused), so evidence is read from job annotations. ChatGPT's workbench can download the artifacts directly.
