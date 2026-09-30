# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **8**
- Required group: `core_five`

## Highest-priority failing poses

- `lunge`: 3 failed checks
- `curl_handle`: 2 failed checks
- `pullup_bar`: 2 failed checks
- `curl_peak`: 1 failed checks

## Failing regions

- `grip_l`: 2 failed checks
- `grip_r`: 2 failed checks
- `torso`: 2 failed checks
- `pelvis`: 1 failed checks

## Failed checks

- `curl_peak` — `self_intersecting_face_pairs` = `210.0`; expected <= 200.0.
- `lunge / pelvis` — `region_max_ratio` = `7.559`; expected <= 5.0.
- `lunge / torso` — `region_min_ratio` = `0.12`; expected >= 0.15.
- `lunge / torso` — `region_max_ratio` = `7.2`; expected <= 5.0.
- `curl_handle / grip_l` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `curl_handle / grip_r` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `pullup_bar / grip_l` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `pullup_bar / grip_r` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
