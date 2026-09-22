# HOME GYM PT — first review candidate

Status: reviewable candidate, not approved for production. Production was not modified or promoted.

## Deliverables
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v1.blend — editable skinned mesh and imported frozen rig.
- HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v1.glb — candidate with original rig and runtime metadata preserved.
- renders/REVIEW_CONTACT_SHEET.jpg — overview; individual PNGs include front, side, three-quarter, back, shoulder close-ups and five exercise poses.
- checkpoints/ — modelling checkpoints and frozen review-pose Blender scenes.

## Source and protection
Playbook and complete handoff package read. Blender 5.2.1 LTS launched successfully. Read-only source branch chatgpt/absolute-retarget-imports pinned to f9cca7c34880a2c5e30b63a42c762d7fd99205e8. This is an archive snapshot, not a production checkout HEAD. Frozen CORNER_FINAL and CORNER_FINAL_SHORTS were supplied and verified; older named v8 binaries were not supplied. Current playbook selects CORNER_FINAL as reference.

Final integrity check verified all 400 reference files unchanged and all copied application source files unchanged, including bundled.ts. Candidate nodes, skins, hierarchy, inverse binds, scenes, animation definitions, materials and runtime metadata match source. Original binary data and shorts mesh remain intact. See reports/final_integrity.json for hashes.

## Shoulder and mesh
| Measurement at curl Bottom | Frozen | Candidate |
|---|---:|---:|
| Deltoid above joint | 7.8 mm | 31.9 mm |
| Deltoid apex sagittal z | +4.8 mm | -69.5 mm |
| Shoulder joint x/y/z | 214.9 / 1412.1 / -21.9 mm | unchanged |

Candidate height meets 25–35 mm target. Apex is posterior to the requested -21.9 mm reference; it is not an exact positional match and warrants visual review. Supplied sagittal.test.mts reproduces measurements; its success alone is not an anatomical acceptance gate.

59,128 body triangles, 31,033 body vertices. Shoulder sculpt and surface blending are candidate-only. Original hand and foot topology is protected. Two inherited UV channels and materials are retained for texture work; no new 4K skin maps have been authored.

## Validation
Dumbbell Bicep Curl, Bodyweight Squat, Dumbbell Shoulder Press, Push-Up and Pull-Up sampled at Bottom/Mid/Peak/Return using unchanged runtime retargeting, correctives and grip/equipment placement. Original hand vertices, all 160 bone matrices and equipment transforms match baseline exactly. Positions are finite and loops close. Review renders use these runtime poses, not manually invented replacements.

Focused candidate and supplied sagittal tests: 2 passed. Unchanged application suite: 290 passed, 8 failed, 1 skipped, matching the handoff totals. Push-up retains inherited technique/reach problems; no mechanics were changed. Details: reports/exercise_validation.json, candidate_tests.log, project_suite.log.

## Review limits and next refinement
This is a shoulder-focused refinement of inherited triangulated topology, not a completed new quad retopology or a photorealistic human rebuild. Clay review renders show form rather than final skin texture. Existing face, fingers, knees and other baseline anatomical limitations remain. The supplied photo target was unavailable.

New vertices use four runtime skin influences; discarded influence mass averages 0.48%, with a worst case of 20.82%. Original vertex weights remain preserved. Continuous-motion and extreme-pose checks, local joint-loop refinement, higher-detail hand/knee anatomy and texture authoring remain before production readiness. Overhead armpits, posterior shoulder balance and squat knee contours deserve particular review.

The editable main blend shows imported rest space. Runtime pose scene checkpoints show the application corrections. Do not replace the metadata-preserving GLB by a casual Blender re-export; use the candidate builder and repeat compatibility checks. No production promotion is authorised.
