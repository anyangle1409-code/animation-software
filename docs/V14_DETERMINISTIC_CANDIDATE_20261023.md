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

Pending the first run. See `docs/V14_RECOVERY_INVESTIGATION_20261023.md` for the investigation this follows from.

## Decision needed (owner)

- **Adopting this makes every build reproducible** (shown for refine() locally and on GitHub). The W8/V14/R120 it produces are new models, not the archived ones.
- **To match the archive exactly**, use the replay (`scripts/v14_investigation/replay_build_blender.py`) instead.
