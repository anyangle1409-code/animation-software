# Reproducing V5 hands

Use a separate checkout of the V5 review branch. Run `python HIGH_DETAIL_MESH_WORK/scripts/bootstrap_from_repo.py` from the repo root to verify and copy the frozen source and validation files into the candidate workspace. The branch contains the required sculpt reference and `reports/hand_contact_guard_v5.json`.

From `HIGH_DETAIL_MESH_WORK` on Blender 5.2 or later:

```text
blender --background --factory-startup --python scripts/build_candidate_v5_hands_curved.py -- 0.90 v5_hands_curved_rebuild
python scripts/make_bare_variant.py v5_hands_curved_rebuild
python scripts/audit_weights_v5.py -- v5_hands_curved_rebuild 0.05
```

The suffix writes new files, preserving the reviewed V5 candidate. On Blender 5.2.1 the rebuilt dressed GLB was byte-identical to the reviewed file, SHA-256 `ec7db2925bd7274be099a1c9e4469faed8671b18f955aae6c289d808a33b2bd0`. Set `GLB`, `ASSETS` and `DRESSED` to the reviewed dressed GLB, `BARE` to its bare variant, and `CANDIDATE_VERSION=v5_hands_curved` to rerun the six focused checks with `validation/scratchpad/repair/vitest.config.mts`.
