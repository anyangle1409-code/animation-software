# Body v2 isolated Actions recovery — execution ledger

Scope: execute the owner's 23 October recovery request from Claude's existing reconstruction scripts. No repeated muscle research.
Isolated branch: `work/body-v2-actions-recovery-20261023`.
Source branch stays at its independently owned HEAD; no merge, deployment or production asset replacement is authorized here.

## Pinned inputs

- Recovery sources: `9fb56a2763cda3036421c075013277bd5dee262e`.
- R57 read-only source checkout: `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- PR124 muscle checkout: `7c820d68de69dcdef7d567e836302123df953446`.
- R41 SHA256: `4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e`.
- Python 3.13 / bpy 5.2.0 selected explicitly. Actual wheel/dependency versions are recorded by each run.

## Completed and verified locally

- Handover and blend-source docs read; PR124 handoff, exercise contract and screenshot findings reconciled.
- Isolated local worktree and remote branch created. Claude's branch not edited.
- First workflow committed at `ca444ce7fd749d607e698e1d70922212567e04a2`.
- First cloud run: https://github.com/anyangle1409-code/animation-software/actions/runs/39916468327 .
  GitHub job API confirms Blender/dependency installation passed and reconstruction started. Models/results still pending at this ledger checkpoint.
- Archived evidence audit: 18 PASS, 0 FAIL. This is archive consistency, not reconstruction acceptance.
- PR124 Python suite: 38 tests PASS; visual-QA metadata PASS, native validation correctly NOT_RUN.
- Regression tests first reproduced verifier exit-status failure and invalid multiline JSON manifest; fixes pass.
- New completeness/quality summary rejects empty results, missing frames/metrics and existing deformation failures.
- New artifact finalizer and muscle-preparation gates tested. No invented anatomical bindings.
- Python compilation, bash syntax and parsed workflow-command syntax checked.
- Existing app suite: 887 PASS, 1 skipped across 74 files; TypeScript typecheck PASS.
- Independent review caught v14 report mismatch exit propagation and swallowed suite statuses; both reproduced and fixed with regressions.

## Cloud work configured; not complete until actual evidence exists

1. Reconstruct W8, v14 and separate R120; retain partial files on failures.
2. Compare archived W8 offsets/reports/rig edits and v14 report; run read-only native structural verification.
3. Render front, back, side and three-quarter directly in Blender. Cloud samples/skin resolution are lower than archive for compute; this is recorded, not pixel-identical evidence.
4. Independently inventory and run all 13 unchanged R57 movement paths at all nine frames on R41, W8, v14 and R120.
5. Run application tests/type checks and pinned Python and Blender test suites; retain logs and individual exit codes. Legacy tests are identified as legacy, not recovered-model acceptance.
6. Prepare only a byte-identical, unapproved muscle staging copy when W8/v14 archive/structure gates pass; preserve IDs and compile all curl/press/squat phases at fixed pose progress with independent activation.
7. Aggregate hashes, missing checks, quality failures and artifact locations. Update recovery handover only on this isolated branch.
8. Prepare a draft prerelease only after reconstruction gates pass. It is explicitly unapproved and does not promote production assets.

## Rulings and limits

- Ruling: use explicit bpy 5.2.0 with Python 3.13, as the source reconstruction environment was the 5.2 wheel; do not silently substitute a Blender major/minor. Exact original save patch remains unknown. Cost if different: content comparisons may expose a version-related discrepancy.
- Ruling: native movement execution and deformation quality are separate statuses. Zero intersection/collapse/stretch is reported separately; completing a diagnostic suite cannot approve anatomy. Raw counts across changed topologies are not like-for-like improvement evidence.
- Ruling: run movements independently after transient setup, preserving original benchmark paths/metrics and source bytes. One failing path must not suppress other paths. Runtime setup does not save the source.
- Ruling: allow later independent reconstruction/check/render tasks to run after nonfatal v14/R120 or verification failures; keep a nonzero aggregate exit status and preserve every discrepancy.
- Ruling: independent review found the saved remesh vertex-count declaration is stale. Native benchmark setup may update that declaration in memory only after the exact source hash and measured vertex count match its passing native verification report. The production guard and saved .blend are unchanged. Cost if wrong: native setup fails and is recorded, never an anatomy pass.
- No R52/R57 unsaved increment or screenshot provenance is invented. The exact original W8 bytes remain unavailable.
- Historical PR107/113 and R54/R55/R57 failures stay failed. R52/R57 sparse-array native validators depend on their original topology/response inputs and cannot be silently re-labelled as validated on remeshed W8/v14; the full native benchmark paths are reused explicitly.
- Anatomical side and reviewed attachment coordinates remain gates. A semantic muscle registry or staging copy is not a muscle-rigged model.
- PT_MODEL_VERSION remains 1.0. Existing source models, production assets and validated skeletal data are unchanged.

## Remaining / blocked

Actual reconstruction hashes, archive discrepancy results, native movement results, renders, native muscle inventory and accessible artifact/release locations await the cloud jobs. No reconstruction or anatomical success is claimed at this checkpoint.
Independent visual/anatomical review and actual landmark/tissue authoring remain after source recovery.

Independent review: three Important findings (remesh setup, test-status propagation, v14 mismatch propagation) addressed; 13 guard tests pass. Minor path wording corrected. Actual native execution remains pending.

## Additional executed legacy suite

Pinned R57 `python -m unittest discover -s scripts/tests -v`: 228 tests executed, 41 environment errors.
All error records are absent historical fixture environment variables (including HGPT_CONTOUR_NPZ,
HGPT_R41_NATIVE_AREA, HGPT_STRAIN_CANDIDATE and HGPT_R42–R52 response/solution/report paths).
These historical experiments cannot be certified by substituting reconstructed W8 arrays with a different topology.
Cloud logs retain each named error; no legacy suite pass is claimed. Independent recovery/native checks continue.

Ruling: the expanded run may reuse exact .blend bytes from the first cloud run if all three outputs exist,
then repeat archive/structural verification with the corrected tools. Original build provenance is preserved.
This avoids rebuilding completed outputs solely because validation coverage improved. Force fresh reconstruction
with the workflow_dispatch reuse_initial=false input if script reconstruction changes are being investigated.

## Additional pinned root-suite execution

`python -m unittest discover -s scripts -v` on untouched R57 code: 1,224 tests, seven failures, four errors, one skipped (256.442 seconds). R41 input rehashed unchanged at the pinned SHA256. No tracked R57 source files changed.

Failure/error records:

- ERROR: test_live_plan_covers_support_and_selects_active_r96_recovery (test_original_v1_execution_orchestration.ExecutionOrchestrationTests.test_live_plan_covers_support_and_selects_active_r96_recovery)
- ERROR: test_operational_tool_artifacts_are_validated (test_original_v1_execution_orchestration.ExecutionOrchestrationTests.test_operational_tool_artifacts_are_validated)
- ERROR: test_future_candidate_with_verified_sources_is_selected (test_original_v1_production_control.ControlTests.test_future_candidate_with_verified_sources_is_selected)
- ERROR: test_owner_accepted_regression_is_bound_to_exact_candidate_and_values (test_original_v1_production_control.ControlTests.test_owner_accepted_regression_is_bound_to_exact_candidate_and_values)
- FAIL: test_live_reverification_matches_committed (test_evidence_integrity_audit.Committed.test_live_reverification_matches_committed)
- FAIL: test_unknown_support_stage_refused (test_original_v1_execution_orchestration.ExecutionOrchestrationTests.test_unknown_support_stage_refused)
- FAIL: test_next_action_requires_both_source_bound_diagnostics (test_original_v1_production_control.ControlTests.test_next_action_requires_both_source_bound_diagnostics)
- FAIL: test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery (test_original_v1_production_control.ControlTests.test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery)
- FAIL: test_zero_blockers_cannot_hide_inherited_regressions (test_original_v1_production_control.ControlTests.test_zero_blockers_cannot_hide_inherited_regressions)
- FAIL: test_rebuild_is_deterministic (test_spine_trunk_audits.P003Rejected.test_rebuild_is_deterministic)
- FAIL: test_current_candidate_status_matches_repository_evidence (test_verify_original_v1_candidate_status.CandidateStatusTests.test_current_candidate_status_matches_repository_evidence)

Causes: missing archived evidence (18 missing vs committed allowance 1), historical orchestration phase/test expectations disagree with current pinned recovery plan; production-control fixtures now correctly refuse a development freeze while shoulder/axilla blockers remain; exact floating-point dictionary comparison differs in rejected spine reconstruction; candidate-status fixture expects candidate_not_production but evidence reports candidate_rejected_for_anatomical_repair. These baseline tests were not edited or weakened. Cloud repeats retain full logs; reconstructed-model native validation continues independently.

## Cloud recovery evidence — 23 October, follow-up

Reconstruction run 39916468327 actually wrote all three .blend candidates and rendered all requested views.
Its final ci-folder write failed because output permissions were read-only; artifacts were still uploaded.
Expanded run 39918805189 fixed that bookkeeping issue, repeated native verification, and correctly FAILED archive/content gates.
Actual files: W8 208,036,008 bytes (SHA256 2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c);
v14 211,149,283 bytes (5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91);
R120 314,795,547 bytes (fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb), experimental.

W8 native structural checks: 5 PASS, 0 FAIL; v14: 6 PASS, 1 FAIL (238,065 vs expected 238,067 vertices); R120: 4 PASS, 0 FAIL, measurement only.
W8 archive comparison: 0 PASS, 4 FAIL. Offset-array difference maximum 3.5928599834 mm and proportion-array difference 0.8375732899 mm against unchanged 0.01 mm guard. Mesh correspondence is not independently established, so these array differences are not a measured anatomical point displacement.
Full JSON discrepancies: 1 W8 skeleton-edit field, 12 W8 report fields, 10 v14 report fields, all retained in all_archive_json_discrepancies.json.
The single skeleton-edit difference is a 0.000431996 mm change in side-fit arm Y shift. v14 also has back_depth_smooth and pec_junction report fields absent from the archived report; current defaults include those operations. BMesh operations consume unordered edge sets; possible refinement non-repeatability is an unproven cause, not a resolved diagnosis.

Native inventory on all recovered models PASSED, recording 206 reference bones and 77 runtime authoring bones.
The older native benchmark setup refused all recovered models before posing: production bridge expects 67 runtime bones.
This is a harness applicability failure, not a demonstrated deformation defect. Production guard remains unchanged.
Muscle attachment/copy gate correctly BLOCKED. No native attachments or anatomy approval granted.

Artifact access run 39922636070 PASSED. Separate exact per-model artifacts are below the connector 512 MiB cap;
the original 1,031,651,971-byte combined artifact was too large for that connector. See docs/BODY_V2_RECOVERED_ACCESS_20261023.json and .md for links and hashes.
The 55,269,994-byte render/discrepancy ZIP was retrieved and SHA256 verified locally:
7c4bd7dd6e56393aabe8b3fa6ad86e6464663d9653fc9b01649460d59a8256b2.
The actual four-view comparison was visually inspected; no anatomical acceptance inferred from appearance.

Ruling: add a separate SHA-pinned recovered-candidate diagnostic cohort using saved reference guides and rest matrices,
with the unchanged R57 pose paths/metrics. It does not run through, modify, or pass the 67-bone production bridge;
archive FAIL and anatomy NOT_GRANTED remain explicit. Rest-bone signatures and source bytes are checked unchanged.
Unknown candidate hashes are refused. Independent static review found no Important findings; 15 combined guard tests pass.
Native execution of this new adapter is still pending. No reconstruction is repeated for this diagnostic continuation.


### 2026-10-23 — completed movement diagnostics and bounded measurement fix

Run [39923681466](https://github.com/anyangle1409-code/animation-software/actions/runs/39923681466) completed. W8 measured 12 of 13 paths at 9 frames each; grip failed the unchanged thumb-placement pair limit. There are 253 per-frame collapse/stretch/intersection failure records. Worst counts across measured frames: 229 collapsed triangles, 3509 stretched triangles, 3499 intersecting pairs. These are density-dependent diagnostic counts, not anatomical approval. All three source-file hashes remained unchanged.

V14 and R120 could not reach frame metrics on 12 paths because their polygon snapshots include non-triangles; grip independently failed its solver limit. This is a measurement-format blocker, not a passing model result. The isolated adapter now freezes Blender native loop-triangle indices from each path's rest snapshot and uses those exact indices for every pose, preserving coordinates, source polygons, bone data, original R57 paths/metrics and thresholds. Changes in evaluated topology fail closed. Existing W8 triangle order and completed failures are retained. Three new regression tests failed before implementation and then passed; 18 combined recovery/diagnostic/access guards pass. Native cloud verification of this fix remains pending. Follow-up runs only V14/R120 and reuses W8 artifact from run39923681466.

Archive/content gates remain FAILED; the unchanged 67-bone production bridge remains incompatible with the 77-bone authoring rigs. R120 remains experimental, anatomical approval NOT_GRANTED, and muscle attachment BLOCKED. No original assets, PT_MODEL_VERSION1.0, skeletal source data, production files or source branch were changed.


### 2026-10-23 — final native diagnostic outcome: recovery accessible, acceptance blocked

Run39927465329 has completed; V14/R120 now measured12paths x9frames each after the safe fixed-rest native tessellation adaptation. Each, like W8, failed grip at the unchanged thumb pair limit and failed zero collapse/stretch/intersection quality. Failure-record totals: W8=253,V14=256,R120=282. All source bytes remained unchanged. No path exception other than grip remains in this run; this resolves the polygon measurement blocker but does not resolve deformation, archive equivalence or production applicability. The record commit is1decd3d663cdb62c54e42832dad40ab3ba203bb2. V14/R120 diagnostic ZIP hashes were independently verified after retrieval. See [final recovery outcome](BODY_V2_RECOVERY_FINAL_OUTCOME_20261023.md) for exact gates, all hashes/artifact links, measurement limitations and required next evidence. Archive/content FAIL; anatomyNOT_GRANTED; muscle attachment and draft prerelease BLOCKED. R120 remains experimental. No production/source-branch/original asset or PT_MODEL_VERSION1.0 change. This supersedes earlier pending-native-execution entries; further monitoring stops because completed runs cannot resolve missing archive correspondence or repair/review requirements.
