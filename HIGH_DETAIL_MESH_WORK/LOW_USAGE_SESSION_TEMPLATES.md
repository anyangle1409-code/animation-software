# Low-usage session templates

These are intentionally short. Repository files hold the history.

## GPT Work — resume V15f

Paste only this:

> Open `anyangle1409-code/animation-software` on
> `work/v15-deep-hand-rebuild-prep-20260925`.
> Do not modify/merge `chatgpt/absolute-retarget-imports`.
> From `HIGH_DETAIL_MESH_WORK`, run `RESUME_V15F_WORK.bat`.
> Follow `V15F_STATUS.bat`, `WORK_RESUME_AFTER_LIMIT.md`, and the generated
> `V15F_LATEST_HANDOFF.md`.
> Continue unattended through documented recoverable steps.
> Use Work time mainly for Blender topology/visual judgement.
> Do not promote geometry, start Phase C, merge source, alter production
> references, or weaken gates without the documented acceptance step.

Do not paste the long historical prompt unless the repo itself is unavailable.

## GPT Work — after a visual PASS

> Continue from the current V15f state. Run `V15F_STATUS.bat` and perform only
> the next documented step. Do not reread historical hand docs unless the
> current gate/report explicitly requires them.

## GPT Work — after a visual FAIL

> The current visual gate is FAIL. Read `V15F_LATEST_HANDOFF.md` and
> `V15F_FAILURE_RECOVERY.md`. Keep the repair local to the failing digit,
> checkpoint before risky changes, rerun the same numeric/visual gate, and do
> not propagate the failing topology strategy.

## Claude Code — narrow source task

> Read `CLAUDE.md`.
> Read `HIGH_DETAIL_MESH_WORK/V15F_LATEST_HANDOFF.md` only if relevant.
> Work only on: <ONE TASK>.
> Read only the files/report needed for that task.
> Use focused tests first.
> Do not modify `chatgpt/absolute-retarget-imports`.
> Stop after the task is verified and write durable state to the repo.

## Claude Code — review one failure

> Read `CLAUDE.md` and this report only:
> `<REPORT PATH>`.
> Identify the owning defect and the smallest safe fix.
> Inspect only the files directly implicated by the report.
> Do not run the full suite until the focused check passes.
> Return/commit only the verified fix and concise handoff.

## Normal Chat — repo analysis

Ask normal Chat to:
- inspect current GitHub branch/report state;
- prepare scripts/docs/tests;
- compare reports;
- plan next steps;
- review Work/Claude output.

Keep Blender GUI work in Work.

## Rule

One session = one clear task or one current phase.

If the task changes materially:
- Claude: use `/clear`;
- Work: start from the repo handoff/status rather than carrying a huge chat.
