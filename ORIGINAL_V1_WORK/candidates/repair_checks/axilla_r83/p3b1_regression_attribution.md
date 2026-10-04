# r83 strict regressions vs P3B1 - attribution

Pre-corrective reference: ORIGINAL_V1_WORK\candidates\repair_preparation\r83_shoulder_corrective_declared\weights_only_pre_corrective_pose_report.json. Attribution counts: {"INHERITED_FROM_WEIGHTS": 5, "ADDED_BY_CORRECTIVE": 1, "OUTSIDE_3A_POSES": 1}. All inside the development gate: True. All inside the production target: False.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| press_top | arm | region_min_ratio | 0.78 | 0.749 | 0.745 | 0.035 | 0.02 | INHERITED_FROM_WEIGHTS | 0.595 | 0.245 |
| pullup_top | torso | region_min_ratio | 0.693 | 0.68 | 0.669 | 0.024 | 0.02 | ADDED_BY_CORRECTIVE | 0.519 | 0.169 |
| pushup_bottom | mesh | self_intersecting_face_pairs | 158.0 | 164 | 164.0 | 6.0 | 5.0 | OUTSIDE_3A_POSES | 36.0 | -164.0 |
| squat_bottom | mesh | volume_deviation_from_1 | 0.04379999999999995 | 0.050000000000000044 | 0.050000000000000044 | 0.0062 | 0.005 | INHERITED_FROM_WEIGHTS | 0.05 | 0.0 |
| squat_bottom | mesh | edge_ratio_p01 | 0.613 | 0.579 | 0.579 | 0.034 | 0.02 | INHERITED_FROM_WEIGHTS | 0.179 | -0.071 |
| squat_bottom | arm | region_min_ratio | 0.597 | 0.383 | 0.383 | 0.214 | 0.02 | INHERITED_FROM_WEIGHTS | 0.233 | -0.117 |
| squat_bottom | shoulder | region_min_ratio | 0.244 | 0.182 | 0.182 | 0.062 | 0.02 | INHERITED_FROM_WEIGHTS | 0.032 | -0.318 |
