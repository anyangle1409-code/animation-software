# ORIGINAL v1 deformation acceptance

- Profile: `development_blocker`
- Status: **FAIL**
- Poses evaluated: **15**
- Failures: **4**

## Highest-priority failing poses

- `press_top`: 2 failed checks
- `press_top_rhythm`: 2 failed checks

## Failing regions

- None.

## Failed checks

- `press_top` — `edge_ratio_p99` = `2.026`; expected <= 2.0.
- `press_top` — `self_intersecting_face_pairs` = `250.0`; expected <= 200.0.
- `press_top_rhythm` — `edge_ratio_p99` = `2.053`; expected <= 2.0.
- `press_top_rhythm` — `self_intersecting_face_pairs` = `298.0`; expected <= 200.0.

## Interpretation

Passing this report does **not** promote the asset to production. It only proves the selected numerical deformation profile. Human anatomy review, provenance, runtime movement/contact validation, garment review and release acceptance remain separate gates.
