# Reproducing V6

Use a separate checkout of the V6 review branch. From the repository root run `python HIGH_DETAIL_MESH_WORK/scripts/bootstrap_from_repo.py` to verify and copy the pinned frozen reference and validation source. The V5 model and `reports/knee_seam_v5.json` are included in the branch.

From `HIGH_DETAIL_MESH_WORK` with Blender 5.2 or later:

```text
blender --background --factory-startup --python scripts/build_candidate_v6_knee_seam.py -- v6_knee_seam_rebuild
python scripts/make_bare_variant.py v6_knee_seam_rebuild
```

The rebuild suffix preserves the reviewed V6 assets. On Blender 5.2.1 the rebuilt dressed GLB was byte-identical to the reviewed SHA-256 `ff39e07735697d5423968a8ec1c05f2c6c68fced0d757ea1b4047096bc7a5306`.

For focused checks, set `GLB`, `ASSETS` and `DRESSED` to `../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb`, `BARE` to the corresponding `_BARE.glb`, and `CANDIDATE_VERSION=v6_knee_seam`. Run the six named tests with `validation/scratchpad/repair/vitest.config.mts`. `scripts/audit_knee_seam_v6.py` verifies the matched gap over the saved pose snapshots. No production file is written.
