# r97 shoulder-foundation declaration (before any edit)

- Target: r97, fresh descendant of r95. Production approval false.
- Parent: r95, via its identity-verified BARE export (`c4b8e388…`, export of r95 blend `8a39a22d…`). The r95/r96 `.blend` files are not in the repository.
- Working parent: `r95_reconstructed.blend`. It is the committed r82 `.blend` (rest mesh, rig rev2c, quad topology, region attribute, shorts and metadata, identical to r95's export to within 5e-7 m) with r95's skin weights and six corrective shape keys transferred by vertex index (`scripts/r97/reconstruct_r95.py`).
- Fidelity check: the repository pose test (`scripts/pose_test_original_v1_o4_candidate_blender.py`, run through `scripts/r97/run_repo_script.py`) on the reconstruction reproduces r95's full-evidence metrics exactly for press_top, press_top_rhythm, pullup_hang and curl_peak (`r95_reconstruction_pose_check.json`).
- Readiness: `r97_readiness.json` = `BLENDER_FOUNDATION_EDIT_ALLOWED`.
- Scope, intent and stop conditions: `r97_declared_before_edit.json`.
