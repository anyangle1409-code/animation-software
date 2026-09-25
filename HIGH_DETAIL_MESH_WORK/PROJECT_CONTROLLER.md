# Home Gym PT Project Controller

## Purpose

Run a small local controller on the laptop so expensive AI sessions are used
only when they add real value.

The controller is **not another AI agent**. It spends no GPT Work or Claude
subscription allowance by itself.

It monitors local project state and routes the next action to the cheapest
capable resource:

1. LOCAL_SCRIPT
2. NORMAL_CHAT
3. CLAUDE
4. GPT_WORK
5. HUMAN_VISUAL

## What it does

While running it can:

- monitor the V15f candidate/report state;
- read `V15F_STATUS`;
- run whitelisted deterministic audits/renders/reports automatically;
- keep `V15F_LATEST_HANDOFF.md` fresh;
- record local branch/HEAD/dirty state;
- optionally check/fetch the live source branch on a slow cadence;
- maintain current Work/Claude budget percentages you enter;
- avoid recommending a new expensive task when an allowance is nearly empty;
- write:
  - `reports/project_controller_state.json`
  - `PROJECT_CONTROLLER_NEXT.md`
  - `PROJECT_CONTROLLER_WORK_PROMPT.txt`
  - `PROJECT_CONTROLLER_CLAUDE_PROMPT.txt`
- stop at any visual/subjective gate rather than pretending it can approve it.

## What it does NOT do

It cannot:
- edit Blender topology by itself;
- make subjective anatomy PASS/FAIL decisions;
- start GPT Work or Claude without a separate supported integration;
- bypass ChatGPT/Claude usage limits;
- promote assets;
- merge source;
- weaken validation thresholds.

Scheduled Work is intentionally **not** used as the polling engine because those
tasks consume agentic usage. Local monitoring is cheaper.

## Controls

Start:

`START_PROJECT_CONTROLLER.bat`

Stop:

`STOP_PROJECT_CONTROLLER.bat`

Status:

`PROJECT_CONTROLLER_STATUS.bat`

Update allowance estimates:

`SET_AI_BUDGET.bat work 14`

`SET_AI_BUDGET.bat claude 35`

After a reset:

`SET_AI_BUDGET.bat work 100`

The percentages are advisory because the controller cannot read private
subscription counters directly.

## Routing examples

### Blender edit required

Route:
`GPT_WORK`

The controller generates a tiny current-state Work prompt.

If Work allowance is below the configured low-budget threshold, it routes to:

`WAIT_FOR_WORK_RESET`

while continuing any deterministic work it can do.

### Numeric audit/render required

Route:
`LOCAL_SCRIPT`

The controller runs the whitelisted command automatically when enabled.

### One isolated code problem

Route:
`CLAUDE`

It writes a compact task prompt that points Claude at the repo memory rather
than pasting project history.

### Planning/report interpretation

Route:
`NORMAL_CHAT`

No Work/Claude allowance should be consumed.

### Visual decision

Route:
`HUMAN_VISUAL`

The controller identifies the exact board and mark command.

## Safety model

Only commands explicitly recognized from `V15F_STATUS` may auto-run.

No arbitrary shell string from a report/status file is executed.

Failures are logged and are not spin-retried indefinitely.

The controller can be stopped by creating
`reports/project_controller.stop` or running the stop BAT.
