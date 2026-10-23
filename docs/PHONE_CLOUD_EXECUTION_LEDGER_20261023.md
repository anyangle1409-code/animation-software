# Home Gym PT — phone-only cloud Blender execution ledger
Date: 2026-10-23

## Source of truth
- Repository: `anyangle1409-code/animation-software`
- Isolated execution branch: `work/phone-blender-workbench-20261023`
- Prior handover: `ad5b6f012427c2bc378534bb566c72ad37d41776`
- Previously VERIFIED initial cloud run: https://github.com/anyangle1409-code/animation-software/actions/runs/40001879043 (W8, V14, R120 completed successfully).
- Current code updates: `c064ecbd45f5b2ff6bdd2450fca2d65e12157232` (read-only bone/weight/rest coordinates) and `d0446b66bd299b3ceb2b6d0a28b67730402e41f3` (report integrity gates).
- Workflow: `.github/workflows/phone-blender-workbench.yml` (push to `scripts/phone_blender/**` auto-triggers three cloud jobs).
- Worker script: `scripts/phone_blender/task.py`.
- Workflow runs page: https://github.com/anyangle1409-code/animation-software/actions/workflows/phone-blender-workbench.yml

## Important status distinction
- VERIFIED: The original cloud smoke test retrieved and opened each reconstruction in Blender 5.2.0 and preserved expected source SHA256.
- COMMITTED, NOT YET VERIFIED IN CLOUD: Both follow-on commits. The read-only audit should now output `rest_anatomy_inventory.json`, `integrity_checks.json`, and the earlier `inventory.json` for each model. GitHub has not yet returned a confirmed job run/result for these commits to this chat.
- NOT APPROVED: anatomy, archive equivalence, movement/grip deformation, and experimental muscle attachments.

## Immutable reconstruction IDs and hashes
- W8: run 39922636070, artifact 12487119841, SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`
- V14: run 39922636070, artifact 12487932177, SHA256 `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91`
- R120: run 39922636070, artifact 12488550235, SHA256 `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb`
These are *reconstructions*, not verified originals. Artifacts expire under GitHub retention; earlier independent second-drive copies were recorded as verified. Check artifact availability afresh.

## Outstanding existing defects
- V14: 238065 vertices vs archived 238067 (two-vertex discrepancy).
- W8 archive content mismatch (offset difference up to 3.59286 mm against 0.01 mm tolerance); unresolved archived JSON discrepancies.
- Previously reproduced shoulder press/squat collapse/stretch/intersection quality-gate failures and grip solver failures in all three reconstructions.
- Recovered authoring rig 77 bones vs old production bridge 67; movement bridge applicability cannot be presumed.
- Anatomical left/right landmark mapping not independently certified. Weight-group centroids or bone names are only evidence for triage.
- Muscle attachment authorization, validated anchors and source acceptance are not satisfied.

## Next safe steps (ordered)
1. **Confirm the new Actions runs** for `c064ecb` and especially `d0446b6`. Obtain the run ID through GitHub Actions; check three model jobs and all artifacts. Do not call reports verified just because a commit exists.
2. For each successful run, check `inventory.json`, `rest_anatomy_inventory.json`, `integrity_checks.json` (result PASS, correct SHA256, model label, sane rig counts) and any job warnings. If a job fails, fix only the isolated diagnostic script and re-run.
3. Analyse the JSON output for rig hierarchy, group influence distributions and candidate shoulder/axilla/arm regions. Compare rest-space centres and independently verify coordinate handedness; *do not infer anatomical sides from names alone*.
4. Use prior immutable diagnostic artifacts and renders documented in `docs/BODY_V2_READONLY_VISUAL_DIAGNOSIS_RESULTS_20261023.md` to prioritize shoulder-press, squat and grip defects with numerical evidence.
5. Keep any later corrections in **NEW isolated experimental candidates** only after explicit scope/authorization, with before/after renders and movement tests; never overwrite a preserved source or claim anatomical approval without independent evidence.

## Guardrails
Laptop OFF is supported for GitHub-hosted scripts; the original-session search and interactive desktop-only Blender tasks remain unavailable until laptop return. No production asset, validated skeleton, `ORIGINAL_v1`, `PT_MODEL_VERSION 1.0`, original reconstructive artifact, Claude branch, merge or deployment should be changed. Do not commit binary .blend files.

The assistant/Work does not run indefinitely after chat termination. GitHub Actions does execute independently once triggered; further code commits require an active authorized cloud session.
