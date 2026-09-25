# AI usage budget — Home Gym PT

## Goal

Keep scarce agentic/weekly allowance for the few tasks that genuinely need
interactive reasoning or Blender/desktop control.

The repository is the memory. Agents should recover state from small
authoritative files, not from a long chat history.

## Source of truth order

For V15f work read only these first:

1. `V15F_LATEST_HANDOFF.md` if present
2. `WORK_RESUME_AFTER_LIMIT.md`
3. `V15F_STATUS.bat` / its JSON output
4. the specific phase plan named by the status output

Do **not** recursively reread all historical V8–V15 documents unless a current
failure explicitly requires one of them.

## GPT Work budget policy

Use GPT Work only for:
- direct Blender topology editing;
- visual inspection that requires the desktop/3D viewport;
- operating local GUI tools that cannot be replaced by scripts;
- a genuinely ambiguous technical failure that local reports cannot route.

Do not spend Work allowance on:
- git history archaeology;
- generating reports;
- running deterministic audits;
- source-side unit tests;
- export plumbing;
- comparison-board assembly;
- status reconstruction;
- rewriting handoffs;
- planning a step already encoded in V15F_STATUS / phase docs.

Those are already scripted or can be handled in normal Chat.

### Model routing in Work

If model choice is available:
- use the cheapest/fastest capable model for commands, audits, file inspection,
  deterministic fixes and straightforward execution;
- reserve the strongest/highest-reasoning model for Blender topology strategy,
  difficult visual/anatomical judgement, or a genuinely novel blocker;
- do not leave high reasoning enabled for repetitive command execution.

Do not switch to Codex merely to save Work allowance: Work and Codex share the
same included usage pool on ChatGPT plans.

## Claude budget policy

Claude usage is shared across Claude.ai/Desktop/Claude Code when signed in with
the same subscription. Moving the same task between those surfaces does not
create a fresh allowance.

Use Claude for a **different role**, not as a duplicate of GPT Work.

Best Claude role for this project:
- source-code implementation that does not need Blender GUI;
- isolated review of a small script/diff;
- second-opinion diagnosis using one generated report;
- targeted mathematical/biomechanical checks.

Avoid asking Claude to:
- rediscover the entire repo;
- reread all hand-history documents;
- duplicate GPT Work's Blender session;
- rerun full suites repeatedly when a focused test is enough;
- produce long narrative status reports.

### Claude Code low-usage start

Start a fresh Claude Code context for a discrete task rather than carrying a
huge historical conversation indefinitely.

First ask it to read only:
- `V15F_LATEST_HANDOFF.md` (or the current phase handoff);
- the exact file(s) named in the task;
- the relevant failing report/test.

Then tell it:
- do not scan unrelated files;
- do not use web search;
- do not spawn subagents unless needed;
- do not run the full suite until focused tests pass;
- write durable state/results back to the repo;
- finish the task rather than explaining every intermediate step.

Use `/context` to inspect loaded context.
Use `/compact` when history is still useful but too large.
Use `/clear` for a genuinely new task; project/repo state remains on disk.

If available, use a planning-heavy model only for the plan/novel diagnosis and
a cheaper execution model for mechanical implementation.

## Context-size rule

Never paste the giant project history into Work or Claude again.

A fresh session should normally receive:
- one 10–20 line instruction;
- one small handoff/status file;
- only the directly relevant reports/files.

If an agent asks for history, point it at the exact repository document rather
than pasting history into chat.

## Test-cost rule

Use the smallest proving test first:

1. one-finger/local audit;
2. family/focused tests;
3. phase gate;
4. full suite only after the local/focused checks pass.

Never use a full 800+ test run as the first diagnostic step for a local mesh or
small source-code change.

## Visual-cost rule

For geometry:
1. ring/digit proof board;
2. explicit local visual verdict;
3. next digit;
4. Stage-A/Stage-B board;
5. full exercise review only after local shape gates pass.

Do not render the whole exercise corpus just to discover a bad local finger.

## Parallel-provider rule

Do not give GPT Work and Claude the same open-ended problem simultaneously.
That doubles discovery/context cost.

Instead:
- GPT Work owns Blender/visual mesh editing;
- normal Chat owns planning, GitHub/repo preparation and report analysis;
- Claude owns narrowly scoped source-code/second-opinion tasks when useful.

When handing work between providers, use repository files, not long copied chat
transcripts.

## End-of-session rule

Before a usage/context limit:
- save/checkpoint local work;
- update the smallest current handoff;
- record exact next command;
- commit/preserve useful source-side changes;
- do not spend the final allowance generating a long prose summary.

For V15f, the automatic handoff/status tools already do most of this.

## Paid overflow options

Only if desired:
- ChatGPT may offer usage credits or an instant/banked reset depending on the
  account; these cost money or consume a reset and are not an efficiency fix.
- Claude paid plans may offer usage credits; API-key Claude Code is separately
  pay-as-you-go.

Prefer reducing context/model cost first.
