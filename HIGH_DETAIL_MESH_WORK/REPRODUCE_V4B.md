# Reproducing V4B

Use a separate checkout of this candidate branch. Run `python HIGH_DETAIL_MESH_WORK/scripts/bootstrap_from_repo.py` from the repository root to verify and copy the 400 pinned frozen files and validation source into the candidate workspace. It does not change production source. Install the project's existing dependencies inside `HIGH_DETAIL_MESH_WORK/validation` and use Blender 5.2 or later.

From `HIGH_DETAIL_MESH_WORK`, run:

```text
blender --background --factory-startup --python scripts/build_candidate_v4b.py -- 0.90 v4b_rebuild
python scripts/make_bare_variant.py v4b_rebuild
```

The rebuild suffix writes separate files and preserves reviewed V4B files. The builder uses the frozen dressed GLB and `reports/sculpt_reference.json`, which are both available from the repository and candidate branch. On Blender 5.2.1 the rebuild was byte-identical to the reviewed dressed GLB, SHA-256 `bba52a7eebcd845508209b82c6171efd48067b68032e8bb18a25ce5c64aab455`.

For the focused tests, set `GLB`, `ASSETS` and `DRESSED` to `../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v4b.glb`; `BARE` to the `_v4b_BARE.glb` file; and `CANDIDATE_VERSION` to `v4b`. Run the six tests named in `REVIEW_V4B.md` using `validation/scratchpad/repair/vitest.config.mts`. `scripts/audit_axilla_v3.py v4b` reproduces the fixed-edge underarm measurements. The original mesh and rig paths remain read-only throughout.
