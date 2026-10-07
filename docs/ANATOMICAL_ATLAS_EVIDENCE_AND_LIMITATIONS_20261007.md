# Anatomical atlas evidence and limitations — 2026-10-07

Baseline: a75926c8a2d9329a25af224f338cdfe3ed21beb2 on codex/whole-body-biomechanics-audit-20261007.

## Gate 2: inventory classification

427 named articulation/contact complexes cover 24 families. This is an explicit modelling inventory, not a claim that every human has exactly 427 joints. Compound capsules retain every participating bone; facets are bilateral; functional contact is separated from true synovial articulation. All 206 conventional bones have osseous connections except the explicitly documented hyoid. Additional cartilage, internal bone components and hallux sesamoids do not inflate 206.

Skull adjacencies, three C1-C2 articulations, 23 discs, 46 lower-spine facets, uncovertebral interfaces, rib-head/tubercle contacts, sternocostal/interchondral interfaces, SI anterior/posterior components, wrist rows and pisiform, metacarpal contacts, patella, tibiofibular syndesmoses, foot columns and individual digital joints are explicit. No C1-C2 disc, no rib 11/12 costotransverse articulation and no direct ulna-carpus surface is invented.

Variant policy: T10 head contact, lunate-hamate facet, cuboideonavicular facet, hyoid union, coccygeal component count/fusion and sternal union vary. The preserved Phase 1 coccyx adult_fused flag is conventional counting metadata, not proof that internal coccygeal joints are fused. Four coccygeal components are a reference convention. Fitting must select the individual's realization. Uncovertebral histology is disputed; a constrained contact record accounts for it without pretending consensus on a synovial classification.

Sources are identified in anatomy_sources.json. Access levels distinguish full text, indexed abstract and indexed excerpt. A source link alone does not validate a numerical value; future measurements must carry their own context and locator. Paired source URLs from the same work do not count as independent publications.

Verification: inventory validator plus omission/mutation tests. Removing a named rare articulation, unknown bones, duplicate joints, an unclassified type or a single-source record is rejected. Regional totals are a reviewed contract, not computed as the desired answer from the input. Passing it proves schema and coverage against that contract; it cannot replace expert anatomical review or bone-only Blender tests.

## Preserved baseline test failures

The unchanged baseline Python suite ran 534 tests: 5 failures and 4 errors. Affected tests: execution_orchestration.test_live_plan_covers_support_and_selects_active_r96_recovery; execution_orchestration.test_operational_tool_artifacts_are_validated; execution_orchestration.test_unknown_support_stage_refused; production_control.test_future_candidate_with_verified_sources_is_selected; production_control.test_owner_accepted_regression_is_bound_to_exact_candidate_and_values; production_control.test_next_action_requires_both_source_bound_diagnostics; production_control.test_wrist_repair_precedes_grip_and_lunge_after_hand_recovery; production_control.test_zero_blockers_cannot_hide_inherited_regressions; verify_original_v1_candidate_status.test_current_candidate_status_matches_repository_evidence. These are historical recovery-control/status mismatches outside this anatomical reference scope. They are not hidden, and this work does not change production control to make them green.

No production mesh, armature, weights, pose driver, recovery candidate or legacy V-series file has been changed.

## Gate 3: semantic frame definitions

30 semantic frame types are parameterized for all 206 bones and 427 articulation records. Joint contact centre, segment origin, reference landmark and instantaneous rotation centre are separate concepts. The atlas identifies full-text ISB 2002/2005 standards and the 2021 foot reporting recommendation; project extensions are labelled as extensions, including individual carpal, phalangeal and foot-bone frames.

The engineering basis constructor only verifies orthonormality/right-handedness and rejects coincident, collinear and non-finite inputs. It does not claim that a generic basis is the published JCS for every joint. The published wrist definitions have distinct left/right sign conventions and differ from the elbow radius/ulna frames; the atlas retains its extension labels rather than conflating them. The current rig's anatomical orientation must be measured before accepting any adapter from its project coordinate header; a bare axis permutation can be an improper reflection. No character coordinates have been guessed and no actual joint frame is dynamically accepted.
