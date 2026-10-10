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


## Independently recovered PRIMARY sternoclavicular evidence for U3

The old follower-source matrix listed U3 as blocked because a generic MyoArm/MoBL model predicted 0.1025 degrees clavicle elevation per degree humerothoracic arm elevation, crossing the previous secondary-review 'typically below 10 degrees' description at about 98 degrees HT. The existing c004 follower still did NOT install clavicular elevation. This is important for overhead press and realistic shoulder/glenoid position.

Verified *primary publication abstracts* have now been reviewed without conflating different clavicle rotations:

- Ludewig et al. 2004, primary experimental surface-electromagnetic tracking, n=39 total with 30 asymptomatic; humeral flexion, scapular-plane and coronal abduction. Reported observed **maxima**: clavicle elevation 11-15 degrees, retraction 15-29 degrees, posterior longitudinal rotation 15-31 degrees. PMID 15089027, DOI 10.2519/jospt.2004.34.3.140. Official: https://pubmed.ncbi.nlm.nih.gov/15089027/
- Ludewig et al. 2009, primary transcortical bone-pin 3D motion, n=12; clavicular elevation and retraction DO occur, but the **31-degree average refers specifically to posterior clavicular axial rotation**, NOT elevation. A 19-degree average refers to **scapular posterior tilt at the AC joint**, NOT clavicular elevation. DOI 10.2106/JBJS.G.01483, PMID 19181982. Official: https://pubmed.ncbi.nlm.nih.gov/19181982/
- Ludewig/Braman 2011 secondary biomechanical review says small clavicular SC elevation is typically below 10 degrees in healthy arm elevation, which cannot serve as an absolute universal cap when a 2004 primary study reports 11-15-degree **observed maxima** under another sensing method/context. DOI 10.1016/j.math.2010.08.004: https://pmc.ncbi.nlm.nih.gov/articles/PMC3010321/

Machine-readable source provenance and explicit measurement-role separation:
ORIGINAL_V1_WORK/anatomy/audit/primary_clavicle_motion_u3_source_review_20261010.json

First-party, no-model-change comparison:
scripts/anatomy_fit/clavicle_primary_source_compatibility.py

The generic 0.1025 curve gives ~12.3-degree candidate SC elevation at 120-degree humerothoracic elevation and ~17.22 degrees at 168 degrees, while the 2004 study's reported maxima are 11-15 degrees across tasks. **This is only a between-method source sensitivity difference, not proof either position is physiologically impossible.** A reported maximum is not a stage-by-stage trajectory; the original bone-pin 2009 public abstract provides no matched numerical SC-elevation curve. Differences in marker/sensor, thorax axes, task, rest pose, sex and exercise load remain unresolved.

Consequence: It is **not** correct to freeze zero clavicle elevation as natural overhead motion; nor to install 31 degrees (wrong axis), a universal 10-degree cap, or the 0.1025 generic coupling as a proven HGPT target. The source tool explicitly refuses to authorize any change. **U3 remains an evidence blocker** until a validated axis-compatible elevation/retraction curve is reviewed alongside true SC/AC contacts and the accepted thorax frame. Canonical readiness unchanged.
