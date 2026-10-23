# Home Gym PT: continue from your phone
Laptop-independent execution branch: `work/phone-blender-workbench-20261023`.
[First cloud test](https://github.com/anyangle1409-code/animation-software/actions/runs/40001879043).
[Workflow runs](https://github.com/anyangle1409-code/animation-software/actions/workflows/phone-blender-workbench.yml).

## What works
GitHub Actions runs Blender 5.2.0 and Python 3.13 with NumPy/SciPy on GitHub-hosted Ubuntu. It retrieves the existing preserved model artifacts and checks each exact SHA256 before opening. The initial task only inventories the models and writes JSON reports. Source files are never saved. No laptop connection is used.

Check the first run's conclusion and artifacts before calling this tested. A green result proves cloud retrieval and Blender inspection, not anatomical correctness or an editing task.

## Phone use
Open this document and the run link in your phone browser, signed in to the repository's GitHub account.
Use a CLOUD coding/chat session with GitHub write access to this repository to request each change. A local laptop-bound chat cannot execute while the laptop is off. This document does not create a cloud chat or configure your phone account.
Tell the cloud agent:
> Continue Home Gym PT from branch work/phone-blender-workbench-20261023. Read PHONE_START_HERE.md and the pinned recovery handovers. Use GitHub-hosted Phone Blender workbench; do not depend on the Windows laptop. Check run 40001879043. Implement the requested task in scripts/phone_blender/task.py, commit on this isolated branch, wait for the Actions run, and show the real output artifacts. Preserve all source hashes. Do not merge, deploy or change production.

A commit changing scripts/phone_blender/** or this workflow on this branch triggers a new run. To repeat the identical task, use GitHub's Re-run jobs on an existing run when signed in. workflow_dispatch may require the workflow on the default branch before GitHub exposes a Run workflow button; no merge was performed to add that button.

## Editing boundary
The current task is READ-ONLY. Model/muscle editing has NOT been performed or tested. To author an experimental model later, the user must explicitly authorize creating a NEW candidate .blend and its scope, replacing the earlier no-save rule for that candidate only. A cloud agent can then implement Blender Python edits and upload outputs as Actions artifacts; never overwrite/download-replace the immutable inputs or commit binaries. Existing anatomy/movement failures and unresolved muscle attachments are not waived. This is scripted Blender execution, not a touch-based live Blender interface.

## Preserved sources
Run 39922636070:
- W8 artifact 12487119841, blend SHA256 2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c.
- V14 artifact 12487932177, blend SHA256 5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91.
- R120 experimental artifact 12488550235, blend SHA256 fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb.
These are UNVERIFIED RECONSTRUCTIONS, not originals. Previously recorded artifact expiration: 2027-01-21. Results from this workflow retain for 90 days, subject to repository policy.

## Latest laptop evidence
All 3 ZIP and blend hashes matched. Second-drive ZIP backups matched. W8 native inventory passed 7 checks. V14 had 238065 vertices against archived expectation 238067, with 77 groups and 79 shape keys. Both inspection copies stayed byte-identical. Missing SciPy was resolved in an isolated local dependency folder. User authorized continuing read-only diagnostics despite known V14 discrepancy. No original discovered in the earlier 931 Blender/backup-file inventory; absence is not proven.

Outstanding: start-pose intersection localization (armpit, inner arm, inner thigh, groin, hands, other with rest-space centres), expanded original search on laptop, anatomical side/attachment review. Prior native diagnostic geometry may avoid repeating already-completed cloud diagnostics.

Read docs/BODY_V2_RECOVERY_HANDOVER_20261023.md, docs/BODY_V2_READONLY_VISUAL_DIAGNOSIS_RESULTS_20261023.md, docs/BODY_V2_PRESERVATION_VERIFIED_20261023.md from base 1ca2b283b553a88b58a9af1cbfade34c9ac7a6d8. Do not rebuild models or modify Claude's branch, ORIGINAL_v1, validated skeleton or PT_MODEL_VERSION 1.0.
