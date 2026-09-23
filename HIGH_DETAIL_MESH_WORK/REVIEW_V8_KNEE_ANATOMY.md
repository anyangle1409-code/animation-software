# V8 knee anatomy refinement — accepted geometry checkpoint

V7 is the user-accepted knee topology. V8 changes its visible patellar shape only.
After reviewing the matched renders, the user accepted V8 as the knee geometry baseline for Phase B. This does not promote V8 to production.

## Geometry

- Source: `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.glb`
- Dressed: `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb`, SHA-256 `a7655f689e141686bbbbb146826bc78121edbe8edbb57f3152b5d5978bc756cb`
- Bare: `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy_BARE.glb`, SHA-256 `1edb5f37a89e782b35ad82696892932edbb8b51da7f8484f1e7838b7d8d890b1`
- Editable: `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend`, SHA-256 `704cb5f9bf1ef53a4c1bda1100f261844d8153034b18ef2ad045a75adb37c9ef`
- 33,089 GLB body vertices, 62,961 triangles; editable Blender mesh retains the 33,059-vertex V7 seam weld and unchanged UV loop counts.
- 1,206 knee position vertices changed at the verifier's 0.1-micron threshold, by at most 9.1 mm in rest space. The patch slightly flattens the broad patellar dome, smooths the medial dimple, and defines the upper-shin transition. The mirrored displacement field follows the existing left/right source topology (602 left / 604 right changed vertices; 1.0% difference in summed displacement).
- V7 and all earlier candidate files remain unchanged.

## Validation

`FINISH_CANDIDATE.bat v8_knee_anatomy knee` passed against runtime `614033b` and frozen 63-bone `hgpt_canonical_v3` structure. All five focused guards pass. All seven exercise clips pass over 26 frames each, with 0 hand-position, bone-matrix, and equipment-matrix differences from the frozen motion. The saved pose seam gap is 0 mm across 28 candidate poses. No degenerate triangles or edges shared by more than two faces.

The GLB document, UVs, joints, weights, indices, rig, materials and animation data match V7. Only body position and local normal buffers changed. No body position outside the knee region changed. The Blender topology, faces and UV loop counts match V7.

## Visual review

Inspect `renders_v8_knee_anatomy/V8_V7_DEEPEST_SQUAT_KNEE_COMPARISON.jpg` for matched front, side and three-quarter deepest-squat close-ups. The dome is slightly less round and the medial indentation softer while the V7 side outline remains. A small medial notch remains visible; this is an incremental anatomy pass, not a claim of finished photoreal anatomy.

## Status

Accepted knee geometry source for the separate Phase B hand candidate. Do not promote or merge into production automatically.
