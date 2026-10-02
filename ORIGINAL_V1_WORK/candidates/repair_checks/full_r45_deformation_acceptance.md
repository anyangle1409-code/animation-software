# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **5**
- Required group: `core_five`

## Highest-priority failing poses

- `press_top`: 1 failed checks
- `press_top_rhythm`: 1 failed checks
- `pullup_bar`: 1 failed checks
- `pullup_hang`: 1 failed checks
- `pullup_hang_rhythm`: 1 failed checks

## Failing regions

- None.

## Failed checks

- `press_top` — `edge_ratio_p99` = `2.153`; expected <= 2.0.
- `press_top_rhythm` — `edge_ratio_p99` = `2.398`; expected <= 2.0.
- `pullup_hang` — `edge_ratio_p99` = `2.093`; expected <= 2.0.
- `pullup_hang_rhythm` — `edge_ratio_p99` = `2.266`; expected <= 2.0.
- `pullup_bar` — `edge_ratio_p99` = `2.093`; expected <= 2.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
