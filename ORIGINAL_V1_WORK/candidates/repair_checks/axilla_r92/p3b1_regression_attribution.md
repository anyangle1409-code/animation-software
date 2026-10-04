# r92 strict regressions vs P3B1 - attribution

Pre-corrective reference: ORIGINAL_V1_WORK\candidates\repair_checks\full_r91_merged_pose_report.json. Attribution counts: {"INHERITED_FROM_WEIGHTS": 2}. All inside the development gate: True. All inside the production target: True.

| pose | region | metric | P3B1 | pre | cand | worse by | tol | attribution | gate margin | prod margin |
|---|---|---|---|---|---|---|---|---|---|---|
| press_top | arm | region_min_ratio | 0.78 | 0.745 | 0.758 | 0.022 | 0.02 | INHERITED_FROM_WEIGHTS | 0.608 | 0.258 |
| pullup_top | torso | region_min_ratio | 0.693 | 0.669 | 0.668 | 0.025 | 0.02 | INHERITED_FROM_WEIGHTS | 0.518 | 0.168 |
