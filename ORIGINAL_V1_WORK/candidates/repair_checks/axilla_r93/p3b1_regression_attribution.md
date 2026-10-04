# r93 strict regressions vs P3B1 - attribution

Pre-corrective reference: ORIGINAL_V1_WORK\candidates\repair_checks\full_r92_merged_pose_report.json. Attribution counts: {"INHERITED_FROM_WEIGHTS": 1}. All inside the development gate: True. All inside the production target: True.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| pullup_top | torso | region_min_ratio | 0.693 | 0.668 | 0.67 | 0.023 | 0.02 | INHERITED_FROM_WEIGHTS | 0.52 | 0.17 |
