# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **5**

## Highest-priority failing poses

- `press_top`: 1 failed checks
- `press_top_rhythm`: 1 failed checks
- `pullup_bar`: 1 failed checks
- `pullup_hang`: 1 failed checks
- `pullup_hang_rhythm`: 1 failed checks

## Failing regions

- `shoulder`: 5 failed checks

## Failed checks

- `press_top / shoulder` — `region_min_ratio` = `0.133`; expected >= 0.15.
- `press_top_rhythm / shoulder` — `region_min_ratio` = `0.123`; expected >= 0.15.
- `pullup_hang / shoulder` — `region_min_ratio` = `0.133`; expected >= 0.15.
- `pullup_hang_rhythm / shoulder` — `region_min_ratio` = `0.117`; expected >= 0.15.
- `pullup_bar / shoulder` — `region_min_ratio` = `0.133`; expected >= 0.15.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
