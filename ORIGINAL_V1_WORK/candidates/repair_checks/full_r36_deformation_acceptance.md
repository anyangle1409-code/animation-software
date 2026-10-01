# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **2**
- Required group: `core_five`

## Highest-priority failing poses

- `lunge`: 2 failed checks

## Failing regions

- `pelvis`: 1 failed checks
- `torso`: 1 failed checks

## Failed checks

- `lunge / pelvis` — `region_max_ratio` = `7.237`; expected <= 5.0.
- `lunge / torso` — `region_max_ratio` = `6.371`; expected <= 5.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
