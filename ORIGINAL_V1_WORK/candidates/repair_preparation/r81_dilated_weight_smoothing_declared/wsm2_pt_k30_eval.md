# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **2**

## Highest-priority failing poses

- `press_top`: 1 failed checks
- `press_top_rhythm`: 1 failed checks

## Failing regions

- `shoulder`: 2 failed checks

## Failed checks

- `press_top / shoulder` — `region_min_ratio` = `0.123`; expected >= 0.15.
- `press_top_rhythm / shoulder` — `region_min_ratio` = `0.131`; expected >= 0.15.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
