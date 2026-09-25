# Work usage estimator

## What can and cannot be predicted

OpenAI does not expose an exact "cost of this future Work task" API for a Plus
account.

The published Plus five-hour local-message estimates are broad:

| Model | Estimated local messages / 5-hour window |
|---|---:|
| GPT-6 Astra | 5-45 |
| GPT-5.6 Sol | 10-100 |
| GPT-5.6 Terra | 25-200 |
| GPT-5.6 Luna | 250-2,000 |

These are not fixed limits. Real usage depends on task size, context,
input/output length, reasoning settings, tool use, speed mode and the amount of
work performed.

Therefore this project uses a **range + calibration** estimator.

## Estimate philosophy

Before a task:
- use the model's published Plus range as a broad prior;
- score the task by project-specific work class;
- widen the estimate when context, GUI work, visual reasoning or open-ended
  exploration is expected;
- narrow it as personal historical samples accumulate.

After a task:
- record the before/after percentage shown in Settings -> Usage;
- record model, task class, approximate duration, context size and result;
- update the local historical estimate.

The estimator never claims an exact percentage.

## Task classes

- `local_script` — deterministic script. Work allowance target: 0%.
- `status_or_file_check` — brief Work inspection only.
- `visual_review` — inspect prepared board/viewport and decide.
- `one_digit_topology` — one local finger topology attempt + save.
- `one_file_code` — one small source/script fix.
- `multi_file_code` — several related source files.
- `blender_debug` — diagnose/recover a Blender/tooling failure.
- `full_validation` — should normally be local-script driven, not Work.
- `open_ended` — avoid when allowance is scarce.

## Commands

Estimate:

`ESTIMATE_WORK_USAGE.bat one_digit_topology Astra`

Record one completed sample:

`LOG_WORK_USAGE.bat one_digit_topology Astra 100 86 35`

Meaning:
- task class: one_digit_topology
- model: Astra
- before: 100% remaining
- after: 86% remaining
- duration: 35 minutes

If the task crossed a reset or the percentage shown was a different window,
do not log it as a normal sample.

## Decision bands

The estimator reports:
- **VERY LOW**
- **LOW**
- **MEDIUM**
- **HIGH**
- **VERY HIGH**

and compares the upper estimate to the manually recorded Work allowance.

A task is marked **WAIT FOR RESET** when its conservative upper estimate is too
close to the remaining allowance.

## Important

This is a scheduling tool, not an OpenAI billing meter.

It should become materially better after 5-10 real samples from this project.
