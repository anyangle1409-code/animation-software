# Claude low-usage handoff

## Role

Claude is **not** the primary Blender operator for the current V15f phase.

Use Claude only for a small, isolated source-code or analysis task that does
not require direct Blender GUI judgement.

## Starting a fresh Claude session

Do not paste the project history.

Use this minimal instruction:

> Open `anyangle1409-code/animation-software` on
> `work/v15-deep-hand-rebuild-prep-20260925`.
> Read `HIGH_DETAIL_MESH_WORK/AI_USAGE_BUDGET.md` and
> `HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md` if it exists.
> Read only the files/report explicitly relevant to the task I give you.
> Do not scan the repository or historical hand documents unless a current
> failure requires them.
> Use focused tests first; do not run the full suite until focused tests pass.
> Do not modify `chatgpt/absolute-retarget-imports`.
> Keep output concise and write durable results/handoff state to the repo.

Then give Claude exactly one task.

## Good Claude tasks

Examples:
- review one failing Python/TypeScript script;
- inspect one V15f JSON report and identify the owning defect;
- implement one source-side test/fix on a disposable branch;
- independently review the prompt-family adapter architecture;
- check mathematical assumptions in a grip/biomechanics solver.

## Bad Claude tasks

Avoid:
- "review everything";
- "continue the whole project";
- "read all the docs and tell me what to do";
- duplicating the current GPT Work Blender session;
- full-repo audits before a focused failure exists.

## Claude Code commands

When using Claude Code:
- `/status` — check remaining plan usage;
- `/context` — see what is consuming context;
- `/compact` — retain a summary when the existing thread is still useful;
- `/clear` — start fresh for a new discrete task;
- `/model` — choose an appropriate available model.

If available, prefer a plan/execute split: use the stronger model for the
difficult plan/diagnosis, then a cheaper execution model for mechanical edits.

## Stop condition

Once the one requested task is complete:
- run its focused verification;
- write/commit the result if appropriate;
- leave the exact next action;
- stop.

Do not consume the remainder of a Claude window inventing additional work.


## Minimal prompt printer

For one discrete Claude task, run:

`PRINT_CLAUDE_TASK_PROMPT.bat <task description>`

It prints a compact Claude Code prompt that points to the persistent repo memory
instead of repeating project history.
