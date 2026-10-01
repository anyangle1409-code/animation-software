# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **6**
- Required group: `core_five`

## Highest-priority failing poses

- `curl_handle`: 2 failed checks
- `lunge`: 2 failed checks
- `pullup_bar`: 2 failed checks

## Failing regions

- `grip_l`: 2 failed checks
- `grip_r`: 2 failed checks
- `pelvis`: 1 failed checks
- `torso`: 1 failed checks

## Failed checks

- `lunge / pelvis` — `region_max_ratio` = `7.093`; expected <= 5.0.
- `lunge / torso` — `region_max_ratio` = `6.37`; expected <= 5.0.
- `curl_handle / grip_l` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `curl_handle / grip_r` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `pullup_bar / grip_l` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `pullup_bar / grip_r` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
