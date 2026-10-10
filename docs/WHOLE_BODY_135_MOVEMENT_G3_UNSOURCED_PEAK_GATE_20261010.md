# Home Gym PT: whole-body 135-test source amplitude rejection

10 October 2026. Read-only, separate from canonical skeleton. NO real Blender movement was performed by this branch.

## Actual problem

The original a003 isolation suite contains **135 movement tests** and **278 nonzero commanded extrema**. The existing independently reviewed amplitude provenance includes **78 explicitly UNSOURCED TEST AMPLITUDES across 49 tests**. These are diagnostic commands, not validated human joint limits, normal exercise ranges, or clinical safety values.

The new first-party program at scripts/anatomy_fit/whole_body_motion_source_gate.py independently cross-checks the two committed movement evidence ledgers (a003_isolated_014 original peak-provenance audit, and the separate unsupported-peak queue) against all 135 tests and 278 archived peak records. It SHA-pins the original body record, atlas, movement test generator script, and actual recorded test sample input. It matches all 78 unsupported peak tuples (test, channel, value) and refuses omissions or silent upgrades. It does not rerun the old NumPy-dependent pose generator or pretend Blender was used.

## Actual source rejection distribution

| Physiology or joint family | Unsourced original test peaks |
|---|---:|
| Hip abduction/adduction | 4 |
| Talocrural | 4 |
| Subtalar | 4 |
| Glenohumeral elevation | 6 |
| Glenohumeral rotation | 8 |
| Finger extension | 24 |
| Thumb opposition | 2 |
| Rib inspiration | 14 |
| Hallux plantarflexion | 2 |
| Knee conditioning | 4 |
| Isolated cervical C4/C5 | 4 |
| Temporomandibular joint | 2 |
| **Total** | **78** |

The flagged examples are methodological mismatches: whole ankle-foot complex ROM cannot define isolated talocrural or subtalar range; humerothoracic elevation cannot define a fixed-scapula GH maximum; whole-neck ROM cannot be assigned directly to C4/C5; interincisor displacement cannot serve as mandibular condyle glide; an arbitrary -10% of finger flexion mean is not sourced finger extension.

## Available without laptop

Execute with Python 3 in an isolated checkout:

    python3 scripts/anatomy_fit/whole_body_motion_source_gate.py --source-only --out /private/hgpt/whole_body_movement_source_v1.json

It emits 135 source-test rows and 12 families. Exactly 49 will be DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDES. All others remain TRACEABLE_BASIS_ONLY_NOT_PHYSIOLOGICAL_CERTIFICATION. The tool never claims Blender ran or a full-body exercise is anatomically correct.

## Future actual Blender checks

Following draft PR #24, run the read-only 206-bone/427-articulation gate on a real Blender-evaluated report and independently verified .blend file. The same private measured report can be screened by:

    python3 scripts/anatomy_fit/whole_body_motion_source_gate.py --input /private/hgpt/whole_body_bpy_MEASURED.json --scene-file /private/hgpt/ACTUAL_SKELETON_REVIEW.blend --out /private/hgpt/whole_body_amplitude_screen_v1.json

Any optional per-pose source_isolated_test_id must be one exact ID from the 135 originals. The ID is merely a claimed association, NOT proof that actual angles, force, range, source population, posture, motion axis, exercise biomechanics or joint geometry agree with that test. Missing ID remains NO_TEST_AMPLITUDE_PROVENANCE. An ID containing any of the 78 unsupported source peaks is DIAGNOSTIC_ONLY_UNSOURCED_AMPLITUDE; a sourced basis alone is not an accepted physiological or anatomical ROM.

An attempted Boolean claim physiological_ROM_certified, exercise_anatomy_approved, or source_test_execution_independently_proven is rejected. Source script and files never change the model, rig or skeleton.

## Remaining blockers

Actual verified pelvic surfaces, coupled thoracic/shoulder geometry, ribs, wrist carpal contact, tarsal contact, source-compatible motion axes, and full-body exercise pose/muscle/skin validation still need evidence and (for real pose outputs) local Blender. Region readiness stays 0 READY / 9 PARTIAL / 3 BLOCKED. Preserve a003 and c001-c004; c005 is unapproved. No production mesh retargeting based on test peak values.
