# Claude usage preflight

Claude Code does not publish a stable per-task percentage cost table comparable
to Work's local-message guidance, so this scheduler does not invent one.

It uses:
1. Anthropic's model guidance;
2. task scope/context rules;
3. the manually recorded Claude remaining percentage;
4. observed before/after samples from this project.

## Default model routing

- mechanical/simple edit -> **Haiku**, low effort
- one-file/routine code -> **Sonnet**, low effort
- multi-file feature/refactor -> **Sonnet**, medium effort
- difficult debugging/architecture -> **opusplan** where available:
  Opus for planning, Sonnet for execution
- open-ended task -> **split before starting**

Exact model/version availability comes from Claude Code `/model`.

## Context rule

For every new discrete task:

`/clear`

Then rely on `CLAUDE.md` and bare file paths.

Use `/compact` only when continuing the same task and its history is still
valuable.

Do not use web/tools/connectors unless the task actually needs them.

## Calibration

Set the current Claude remaining percentage:

`SET_AI_BUDGET.bat claude <percent>`

Estimate/route with:

`PLAN_CLAUDE_TASK.bat <task_class>`

After real tasks, log before/after samples with the helper scripts so the
controller can replace qualitative estimates with project-specific observed
ranges.

Until samples exist, the planner reports qualitative risk rather than a fake
percentage.
