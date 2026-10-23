# V14 deterministic build: candidate branch (not for merge without owner approval)

Branch: `claude/v14-deterministic-candidate-20261023`, branched from `claude/v14-recovery-investigation-20261023`.

## What changes here, and only here

1. **`scripts/body_v2/refine_torso_blender.py`:** the investigation's `CANDIDATE_deterministic_refine.patch`. Elements are sorted by index before `subdivide_edges`, `triangulate` and `beautify_fill`.
2. **`scripts/body_v2/rebuild_v2_blender.py`:** seam loops (`loop_on_plane`) start at their lowest-index vertex and are walked lowest-index-first. A Python set had changed the R120 seam strips from run to run.

The originals on every other branch are untouched. No .blend file is committed.

## Test

Workflow `.github/workflows/v14-deterministic-candidate.yml`:
- **Two runners (`a`, `b`) build independently.** Each builds W8 from R41 (025d5f28), then:
  - V14 (default leg step);
  - the legs-only base, then R120.
- **A compare job then checks:**
  - W8 `rest.npy`, `tris.npy`, offsets and proportion: bit-identical or max deviation;
  - V14 and R120 meshes: vertex and face counts, face lists, positions, weights, and nearest-vertex distance;
  - the three reports.

Results are published as job annotations and recorded below.

## Results

**Run 1** ([40030796708](https://github.com/anyangle1409-code/animation-software/actions/runs/40030796708), patched `refine()` and sorted seam loops only; all jobs passed):

| Output | Result |
|---|---|
| W8 `rest.npy`, `tris.npy`, proportion | **bit-identical** across the two runners |
| W8 offsets | identical to 2.8e-17 m (the limit of floating-point rounding) |
| W8 and V14 reports | identical |
| V14 | 238,068 vertices on both runners, but the vertex order and faces differ, and positions differ by up to 0.40 mm (4,928 vertices more than 0.01 mm) |
| R120 | 347,903 vs 347,904 vertices; nearest-vertex distance up to 1.03 mm |

So W8 is now deterministic. The **leg step has its own run-to-run variation**, and R120 inherits it through its legs-only base:
- **In-place relaxation loops:** the cut-seam relax and the band above the cut read neighbours' *current* positions while walking a Python set, so the result depends on the order the set comes out in.
- **Bisect inputs** built from sets.

**Run 2 changes:**
- `legs_v2_blender.py`: those loops are made Jacobi (neighbours' previous positions), the bisect inputs are index-sorted, and the weight-transfer list is index-sorted.
- `rebuild_v2_blender.py`: the cut's bisect inputs and the new-vertex list are index-sorted.

See `docs/V14_RECOVERY_INVESTIGATION_20261023.md` for the investigation this follows from.

## Decision needed (owner)

- **Adopting this makes every build reproducible** (shown for refine() locally and on GitHub). The W8/V14/R120 it produces are new models, not the archived ones.
- **To match the archive exactly**, use the replay (`scripts/v14_investigation/replay_build_blender.py`) instead.
