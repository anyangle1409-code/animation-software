# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **3**
- Required group: `core_five`

## Highest-priority failing poses

- `press_top_rhythm`: 1 failed checks
- `pullup_hang_rhythm`: 1 failed checks
- `pushup_bottom`: 1 failed checks

## Failing regions

- `hand`: 1 failed checks

## Failed checks

- `press_top_rhythm` — `edge_ratio_p99` = `2.196`; expected <= 2.0.
- `pushup_bottom / hand` — `region_min_ratio` = `0.119`; expected >= 0.15.
- `pullup_hang_rhythm` — `edge_ratio_p99` = `2.172`; expected <= 2.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
