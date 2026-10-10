# No-Claude optional Blender CT review

For the standalone Windows laptop workflow, use the branch `codex/non-destructive-blender-ct-launch-20261010` as a **separate detached Git worktree**. Run `start_private_ct_review.cmd` for the verified 10-point browser review first.

Next, optionally double-click `start_private_ct_blender_review.cmd`. This fetches six original CT source pairs required by the **existing** `scripts/anatomy_fit/ct_pelvis_review_scene_blender.py`. The six source files are independently checked against both the 72-slice manifest and the original six-frame Blender manifest, including SHA-256 and scanner positions.

The launcher discovers an installed Blender application, starts a **fresh background scene**, and attempts to create `BLENDER_CT_REVIEW_ONLY.blend` and `BLENDER_CT_REVIEW_REPORT.json` in your home directory under `HomeGymPT_Private_Original_CT_Review`. It will not open or modify the existing production Blender project. Existing target files are refused rather than overwritten.

This is an **unregistered display-only CT inspection**. It does not verify bone identities, establish scanner-to-skeleton registration or promote any canonical geometry. GitHub CI can verify the original source files and standalone Blender plan; actual `bpy` scene creation requires Blender on the laptop.

The overall status is unchanged: 0 accepted true pelvic osseous landmarks out of seven, 0 READY / 9 PARTIAL / 3 BLOCKED. No Claude usage is required for either launcher.
