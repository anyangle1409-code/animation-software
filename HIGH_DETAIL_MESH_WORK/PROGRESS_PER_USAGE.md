# Progress-per-usage scheduling

The controller should optimize **useful project progress per percentage point of
scarce AI allowance**, not simply choose the cheapest model.

## Core score

For an AI task:

`expected_progress = task_value × blocker_importance × success_probability`

`efficiency = expected_progress / estimated_five_hour_cost_midpoint`

The model/configuration must pass the five-hour and weekly safety gates first.

Among safe capable configurations, choose the highest efficiency.

This means:
- a slightly more expensive model can win when it materially raises the chance
  of clearing a critical blocker;
- a powerful model does **not** win when its extra expected progress is too small
  for the extra allowance cost;
- deterministic local work always beats spending Work usage on the same result.

## Failure handling

A genuine failed attempt reduces the estimated success probability of repeating
the same capability level.

Re-run preflight after the failure.

Do not keep increasing reasoning inside the same task. Preserve the evidence and
let the scheduler decide whether escalation is now worthwhile.

## Project-specific intent

For the current V15f phase:
- one-finger topology is a critical blocker and has very high project value;
- local audit/render/report work is high-value but near-zero Work cost;
- broad repo review/documentation is low blocker value and should not displace
  the current hand blocker;
- final validation is high value but belongs to deterministic tooling;
- open-ended exploration is deliberately low-value-per-usage and blocked.

## Calibration

Starting success probabilities live in `USAGE_VALUE_POLICY.json`.

They are priors, not truths.

As real Work tasks are logged, task cost estimates become empirical. Success
probabilities can also be updated later if enough completed-task outcome data
exists.

The controller should prefer real observed data over these priors when
available.
