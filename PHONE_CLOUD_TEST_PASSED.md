# Cloud execution test passed — 23 October 2026
GitHub-hosted run [40001879043](https://github.com/anyangle1409-code/animation-software/actions/runs/40001879043), code b8856690417d7c0899a892237ce2a59b2b43a931:
- W8 job 120579764076: completed / success. Report artifact 12521604080.
- V14 job 120579763613: completed / success. Report artifact 12521319904.
- R120 job 120579764231: completed / success. Report artifact 12523060607.

All jobs installed cloud Blender dependencies, retrieved the model, ran the task and uploaded results successfully. This used GitHub-hosted Ubuntu and did not depend on the laptop. Task asserts expected model SHA256 before opening and after inspection, disables embedded scripts, and never saves a .blend.

This is a passing infrastructure test, not anatomical/model acceptance. V14 remains 238065 versus archived 238067 vertices. Editing and rendering changes have not been tested by this smoke task.

Start at [PHONE_START_HERE.md](PHONE_START_HERE.md). Phone route is a cloud GitHub-enabled agent OR direct GitHub web editing of scripts/phone_blender/task.py on this isolated branch, which triggers the workflow. A local desktop chat cannot run with the laptop off. No new cloud conversation has been created or phone sign-in tested. Sign in to the GitHub account with repository write access to change task scripts or re-run jobs. Model-editing outputs require separate explicit permission for a new candidate; never overwrite source files.
