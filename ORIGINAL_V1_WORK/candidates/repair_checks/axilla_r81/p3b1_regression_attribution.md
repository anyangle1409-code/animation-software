# r81 strict regressions vs P3B1 - attribution

Pre-corrective reference: r80. Attribution counts: {"INHERITED_FROM_WEIGHTS": 7, "ADDED_BY_CORRECTIVE": 3, "OUTSIDE_3A_POSES": 1, "INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE": 1}. All inside the development gate: True. All inside the production target: False.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| press_bottom | torso | region_min_ratio | 0.698 | 0.505 | 0.526 | 0.172 | 0.02 | INHERITED_FROM_WEIGHTS | 0.376 | 0.026 |
| press_top | arm | region_min_ratio | 0.78 | 0.606 | 0.702 | 0.078 | 0.02 | INHERITED_FROM_WEIGHTS | 0.552 | 0.202 |
| press_top_rhythm | arm | region_min_ratio | 0.679 | 0.686 | 0.621 | 0.058 | 0.02 | ADDED_BY_CORRECTIVE | 0.471 | 0.121 |
| pullup_bar | arm | region_min_ratio | 0.865 | 0.554 | 0.688 | 0.177 | 0.02 | INHERITED_FROM_WEIGHTS | 0.538 | 0.188 |
| pullup_hang | arm | region_min_ratio | 0.865 | 0.554 | 0.688 | 0.177 | 0.02 | INHERITED_FROM_WEIGHTS | 0.538 | 0.188 |
| pullup_hang_rhythm | arm | region_min_ratio | 0.838 | 0.542 | 0.727 | 0.111 | 0.02 | INHERITED_FROM_WEIGHTS | 0.577 | 0.227 |
| pullup_top | torso | region_min_ratio | 0.693 | 0.645 | 0.654 | 0.039 | 0.02 | INHERITED_FROM_WEIGHTS | 0.504 | 0.154 |
| pushup_bottom | mesh | self_intersecting_face_pairs | 158.0 | 164 | 164.0 | 6.0 | 5.0 | OUTSIDE_3A_POSES | 36.0 | -164.0 |
| squat_bottom | mesh | volume_deviation_from_1 | 0.04379999999999995 | 0.04610000000000003 | 0.050000000000000044 | 0.0062 | 0.005 | ADDED_BY_CORRECTIVE | 0.05 | 0.0 |
| squat_bottom | mesh | edge_ratio_p01 | 0.613 | 0.6 | 0.579 | 0.034 | 0.02 | ADDED_BY_CORRECTIVE | 0.179 | -0.071 |
| squat_bottom | arm | region_min_ratio | 0.597 | 0.413 | 0.383 | 0.214 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.233 | -0.117 |
| squat_bottom | shoulder | region_min_ratio | 0.244 | 0.178 | 0.182 | 0.062 | 0.02 | INHERITED_FROM_WEIGHTS | 0.032 | -0.318 |
