# r80 strict regressions vs P3B1 - attribution

Pre-corrective reference: ORIGINAL_V1_WORK/candidates/repair_checks/axilla_r80/r68_metrics_only_pose_report.json. Attribution counts: {"INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE": 6, "INHERITED_FROM_WEIGHTS": 5, "OUTSIDE_3A_POSES": 1, "ADDED_BY_CORRECTIVE": 1}. All inside the development gate: True. All inside the production target: False.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| press_bottom | torso | region_min_ratio | 0.698 | 0.673 | 0.505 | 0.193 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.355 | 0.005 |
| press_top | arm | region_min_ratio | 0.78 | 0.721 | 0.606 | 0.174 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.456 | 0.106 |
| press_top_rhythm | mesh | self_intersecting_face_pairs | 54.0 | 168 | 74.0 | 20.0 | 5.0 | INHERITED_FROM_WEIGHTS | 126.0 | -74.0 |
| pullup_bar | mesh | self_intersecting_face_pairs | 4.0 | 126 | 40.0 | 36.0 | 5.0 | INHERITED_FROM_WEIGHTS | 160.0 | -40.0 |
| pullup_bar | arm | region_min_ratio | 0.865 | 0.798 | 0.554 | 0.311 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.404 | 0.054 |
| pullup_hang | mesh | self_intersecting_face_pairs | 4.0 | 126 | 40.0 | 36.0 | 5.0 | INHERITED_FROM_WEIGHTS | 160.0 | -40.0 |
| pullup_hang | arm | region_min_ratio | 0.865 | 0.798 | 0.554 | 0.311 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.404 | 0.054 |
| pullup_hang_rhythm | mesh | self_intersecting_face_pairs | 0.0 | 134 | 48.0 | 48.0 | 5.0 | INHERITED_FROM_WEIGHTS | 152.0 | -48.0 |
| pullup_hang_rhythm | arm | region_min_ratio | 0.838 | 0.787 | 0.542 | 0.296 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.392 | 0.042 |
| pullup_top | torso | region_min_ratio | 0.693 | 0.659 | 0.645 | 0.048 | 0.02 | INHERITED_FROM_WEIGHTS | 0.495 | 0.145 |
| pushup_bottom | mesh | self_intersecting_face_pairs | 158.0 | 164 | 164.0 | 6.0 | 5.0 | OUTSIDE_3A_POSES | 36.0 | -164.0 |
| squat_bottom | arm | region_min_ratio | 0.597 | 0.529 | 0.413 | 0.184 | 0.02 | INHERITED_FROM_WEIGHTS_PLUS_CORRECTIVE | 0.263 | -0.087 |
| squat_bottom | shoulder | region_min_ratio | 0.244 | 0.229 | 0.178 | 0.066 | 0.02 | ADDED_BY_CORRECTIVE | 0.028 | -0.322 |
