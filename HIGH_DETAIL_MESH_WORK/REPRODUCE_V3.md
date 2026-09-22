# Reproducing the v3 candidate

This review branch contains the three v3 model files, the frozen handoff already present at repository root, the 400-file SHA-256 list, and `reports/sculpt_reference.json` captured with the corrected runtime pose. These inputs let another agent reproduce the candidate without a Claude session.

Work in a separate checkout of `codex-high-detail-candidate-v3-review-20260922`. In that checkout, run `python HIGH_DETAIL_MESH_WORK/scripts/bootstrap_from_repo.py`. It checks every pinned source file before copying the reference and validation source under `HIGH_DETAIL_MESH_WORK`; it does not modify the application source.

Install the existing project dependencies inside `HIGH_DETAIL_MESH_WORK/validation` with `pnpm install --ignore-scripts`. Run Blender 5.2 or later from the candidate workspace:

```text
blender --background --factory-startup --python scripts/build_candidate_v3.py -- 0.90 v3_rebuild
python scripts/make_bare_variant.py v3_rebuild
```

The `v3_rebuild` suffix writes new candidate files alongside the reviewed v3 files. The script reads the verified frozen dressed GLB and sculpt reference. On the builder's Blender 5.2.1 installation, the rebuild produced the exact reviewed GLB SHA-256 `07d1b809cb6ae649ee86cbb8e747b43274a557bb9f4f32b685bd50c19a31c16c`. Compare hashes and visual output on other Blender versions; do not overwrite the reviewed v3 files during a reproduction attempt.

To run the focused guards from `HIGH_DETAIL_MESH_WORK/validation`, set `GLB` and `ASSETS` to `../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v3.glb`, `DRESSED` to the same file, `BARE` to `../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v3_BARE.glb`, and `CANDIDATE_VERSION` to `v3`. Then run Vitest with `scratchpad/repair/vitest.config.mts` against `sagittal.test.mts`, `dressed_equivalence.test.mts`, `gripagree.test.mts`, `gripmetric.test.mts`, `overlap.test.mts`, and `review_v3.test.mts` in the repair folder. The saved result is `reports/v3_tests.log`.

For the anatomy audit, run Blender with `scripts/audit_weights_v3.py -- v3 0.05`; the saved result is `reports/weight_audit_v3.json`. To re-render with saved exercise poses, use `scripts/render_review_v3.py -- all` or `-- overhead` after the five-exercise test has written `reports/poses_v3`. The two labeled JPG sheets are included for immediate review.

All reproduction writes belong inside `HIGH_DETAIL_MESH_WORK` in the separate checkout. Production model references and the frozen rig remain untouched.

