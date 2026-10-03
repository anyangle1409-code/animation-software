# r76 strict regressions vs P3B1 - attribution

Pre-corrective reference: r48. Attribution counts: {"INHERITED_FROM_WEIGHTS": 9, "INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE": 8, "ADDED_BY_CORRECTIVE": 4, "OUTSIDE_3A_POSES": 2}. All inside the development gate: True. All inside the production target: False.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| press_bottom | arm | region_max_ratio | 2.099 | 2.234 | 2.256 | 0.157 | 0.1 | INHERITED_FROM_WEIGHTS | 2.744 | -0.256 |
| press_bottom | torso | region_min_ratio | 0.698 | 0.643 | 0.507 | 0.191 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.357 | 0.007 |
| press_top | mesh | self_intersecting_face_pairs | 95.0 | 166 | 132.0 | 37.0 | 5.0 | INHERITED_FROM_WEIGHTS | 68.0 | -132.0 |
| press_top | arm | region_min_ratio | 0.78 | 0.754 | 0.528 | 0.252 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.378 | 0.028 |
| press_top | arm | region_max_ratio | 2.425 | 2.499 | 2.82 | 0.395 | 0.1 | ADDED_BY_CORRECTIVE | 2.18 | -0.82 |
| press_top_rhythm | mesh | self_intersecting_face_pairs | 54.0 | 155 | 112.0 | 58.0 | 5.0 | INHERITED_FROM_WEIGHTS | 88.0 | -112.0 |
| press_top_rhythm | arm | region_min_ratio | 0.679 | 0.679 | 0.596 | 0.083 | 0.02 | ADDED_BY_CORRECTIVE | 0.446 | 0.096 |
| press_top_rhythm | arm | region_max_ratio | 2.244 | 2.405 | 2.82 | 0.576 | 0.1 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 2.18 | -0.82 |
| pullup_bar | mesh | self_intersecting_face_pairs | 4.0 | 100 | 102.0 | 98.0 | 5.0 | INHERITED_FROM_WEIGHTS | 98.0 | -102.0 |
| pullup_bar | arm | region_min_ratio | 0.865 | 0.84 | 0.529 | 0.336 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.379 | 0.029 |
| pullup_bar | arm | region_max_ratio | 2.346 | 2.497 | 2.786 | 0.44 | 0.1 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 2.214 | -0.786 |
| pullup_hang | mesh | self_intersecting_face_pairs | 4.0 | 100 | 102.0 | 98.0 | 5.0 | INHERITED_FROM_WEIGHTS | 98.0 | -102.0 |
| pullup_hang | arm | region_min_ratio | 0.865 | 0.84 | 0.529 | 0.336 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.379 | 0.029 |
| pullup_hang | arm | region_max_ratio | 2.346 | 2.497 | 2.786 | 0.44 | 0.1 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 2.214 | -0.786 |
| pullup_hang_rhythm | mesh | self_intersecting_face_pairs | 0.0 | 132 | 126.0 | 126.0 | 5.0 | INHERITED_FROM_WEIGHTS | 74.0 | -126.0 |
| pullup_hang_rhythm | arm | region_min_ratio | 0.838 | 0.831 | 0.574 | 0.264 | 0.02 | ADDED_BY_CORRECTIVE | 0.424 | 0.074 |
| pullup_hang_rhythm | arm | region_max_ratio | 2.214 | 2.398 | 2.772 | 0.558 | 0.1 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 2.228 | -0.772 |
| pullup_top | torso | region_min_ratio | 0.693 | 0.627 | 0.64 | 0.053 | 0.02 | INHERITED_FROM_WEIGHTS | 0.49 | 0.14 |
| pushup_bottom | mesh | self_intersecting_face_pairs | 158.0 | 164 | 164.0 | 6.0 | 5.0 | OUTSIDE_3A_POSES | 36.0 | -164.0 |
| pushup_bottom | shoulder | region_min_ratio | 0.753 | 0.724 | 0.726 | 0.027 | 0.02 | OUTSIDE_3A_POSES | 0.576 | 0.226 |
| squat_bottom | mesh | edge_ratio_p99 | 1.796 | 1.825 | 1.859 | 0.063 | 0.05 | ADDED_BY_CORRECTIVE | 0.141 | -0.359 |
| squat_bottom | mesh | self_intersecting_face_pairs | 108.0 | 134 | 138.0 | 30.0 | 5.0 | INHERITED_FROM_WEIGHTS | 62.0 | -138.0 |
| squat_bottom | arm | region_min_ratio | 0.597 | 0.519 | 0.529 | 0.068 | 0.02 | INHERITED_FROM_WEIGHTS | 0.379 | 0.029 |
