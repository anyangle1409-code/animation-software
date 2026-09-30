# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **14**
- Failures: **42**
- Required group: `core_five`

## Highest-priority failing poses

- `curl_handle`: 4 failed checks
- `curl_peak`: 4 failed checks
- `press_top`: 4 failed checks
- `press_top_rhythm`: 4 failed checks
- `pullup_top`: 4 failed checks
- `grip`: 3 failed checks
- `lunge`: 3 failed checks
- `press_bottom`: 3 failed checks
- `pullup_bar`: 3 failed checks
- `pullup_hang`: 3 failed checks

## Failing regions

- `hand`: 19 failed checks
- `finger`: 11 failed checks
- `grip_l`: 2 failed checks
- `grip_r`: 2 failed checks
- `torso`: 2 failed checks
- `pelvis`: 1 failed checks

## Failed checks

- `curl_peak` — `self_intersecting_face_pairs` = `268.0`; expected <= 200.0.
- `curl_peak / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `curl_peak / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `curl_peak / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `press_bottom / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `press_bottom / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `press_bottom / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `press_top` — `self_intersecting_face_pairs` = `202.0`; expected <= 200.0.
- `press_top / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `press_top / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `press_top / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `press_top_rhythm` — `edge_ratio_p99` = `2.013`; expected <= 2.0.
- `press_top_rhythm / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `press_top_rhythm / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `press_top_rhythm / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `pushup_bottom / hand` — `region_min_ratio` = `0.139`; expected >= 0.15.
- `pullup_hang / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `pullup_hang / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `pullup_hang / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `pullup_hang_rhythm / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `pullup_hang_rhythm / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `pullup_hang_rhythm / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `pullup_top` — `self_intersecting_face_pairs` = `216.0`; expected <= 200.0.
- `pullup_top / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `pullup_top / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `pullup_top / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `lunge / pelvis` — `region_max_ratio` = `7.559`; expected <= 5.0.
- `lunge / torso` — `region_min_ratio` = `0.121`; expected >= 0.15.
- `lunge / torso` — `region_max_ratio` = `7.2`; expected <= 5.0.
- `row / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `row / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `row / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `grip / finger` — `region_min_ratio` = `0.113`; expected >= 0.15.
- `grip / hand` — `region_min_ratio` = `0.07`; expected >= 0.15.
- `grip / hand` — `region_max_ratio` = `5.387`; expected <= 5.0.
- `curl_handle` — `self_intersecting_face_pairs` = `266.0`; expected <= 200.0.
- `curl_handle / finger` — `region_min_ratio` = `0.086`; expected >= 0.15.
- `pullup_bar / finger` — `region_min_ratio` = `0.086`; expected >= 0.15.
- `curl_handle / grip_l` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `curl_handle / grip_r` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `pullup_bar / grip_l` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.
- `pullup_bar / grip_r` — `grip_max_penetration_mm` = `5.93`; expected <= 2.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
