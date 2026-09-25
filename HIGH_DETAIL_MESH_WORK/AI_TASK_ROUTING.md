# AI task routing — cheapest capable surface first

Use this to avoid spending the wrong allowance.

## Normal Chat

Default for:
- planning;
- GitHub/repo inspection;
- report analysis;
- writing scripts/docs/tests;
- comparing candidate evidence;
- preparing handoffs/prompts;
- deciding which narrow task should go to Work or Claude.

## GPT Work

Use only when direct local/GUI control materially helps:
- Blender topology editing;
- 3D viewport inspection;
- local desktop interaction;
- visual anatomy judgement;
- local app workflows that scripts cannot perform.

Before using Work ask:
> Can this be done deterministically by a script or from GitHub/report data?

If yes, do it outside Work.

## Claude

Use for a narrow, independent role:
- one source-code implementation;
- one script/diff review;
- one report diagnosis;
- one mathematical/biomechanical second opinion.

Do not give Claude the whole project as an open-ended continuation task.

## Local scripts

Cheapest path for:
- audits;
- renders;
- report generation;
- status;
- test orchestration;
- export;
- checkpoint summaries.

Prefer local scripts over any AI agent when the next action is deterministic.

## Escalation order

1. local deterministic script;
2. normal Chat;
3. Claude narrow source task;
4. GPT Work direct Blender/GUI task;
5. strongest/highest-reasoning model only for a genuine blocker.

## Stop duplicate work

Never give two paid agent surfaces the same open-ended problem at the same time.
Use repository handoffs to transfer state.
