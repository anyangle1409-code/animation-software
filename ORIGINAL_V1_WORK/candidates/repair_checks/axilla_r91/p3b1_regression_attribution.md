# r91 strict regressions vs P3B1 - attribution

Pre-corrective reference: ORIGINAL_V1_WORK\candidates\repair_checks\full_r90_merged_pose_report.json. Attribution counts: {"INHERITED_FROM_WEIGHTS": 2}. All inside the development gate: True. All inside the production target: True.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| press_top | arm | region_min_ratio | 0.78 | 0.745 | 0.745 | 0.035 | 0.02 | INHERITED_FROM_WEIGHTS | 0.595 | 0.245 |
| pullup_top | torso | region_min_ratio | 0.693 | 0.669 | 0.669 | 0.024 | 0.02 | INHERITED_FROM_WEIGHTS | 0.519 | 0.169 |
