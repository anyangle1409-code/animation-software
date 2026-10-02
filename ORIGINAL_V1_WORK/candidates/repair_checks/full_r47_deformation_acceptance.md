# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **4**
- Required group: `core_five`

## Highest-priority failing poses

- `press_top`: 1 failed checks
- `press_top_rhythm`: 1 failed checks
- `pullup_hang_rhythm`: 1 failed checks
- `pushup_bottom`: 1 failed checks

## Failing regions

- `torso`: 3 failed checks
- `hand`: 1 failed checks

## Failed checks

- `press_top / torso` — `region_max_ratio` = `5.118`; expected <= 5.0.
- `press_top_rhythm / torso` — `region_max_ratio` = `6.343`; expected <= 5.0.
- `pushup_bottom / hand` — `region_min_ratio` = `0.119`; expected >= 0.15.
- `pullup_hang_rhythm / torso` — `region_max_ratio` = `5.844`; expected <= 5.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
