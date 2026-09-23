# Reproduce the V7 knee candidate without overwriting reviewed files

The builder reads the unchanged V6 GLB and `reports/squat_sculpt_reference_v5.json.gz`. The latter contains the saved squat-peak skin transforms used to map the local posed-space knee adjustment back into rest space. Neither builder changes the frozen source rig.

From `HIGH_DETAIL_MESH_WORK` with Python, Blender 5.2.1 and the existing V6 assets available:

```text
python scripts/build_candidate_v7_knee_retopology.py
START_CANDIDATE.bat v7_knee_retopology_rebuild
blender --background --factory-startup --python scripts/finalize_v7_knee_blend.py -- v7_knee_retopology_rebuild
```

The default output suffix is `_rebuild`, so the review files are not overwritten. The rebuilt dressed GLB was byte-identical to V7: SHA-256 `f6346ac4da1508cc15bb16d6406d7cc0cc8c97a92c173d57d2d422bcb9a59d6d`. The rebuilt Blender body had 33,059 vertices, 62,961 triangles and unchanged UV loop counts. Blender files can differ in bytes when saved again; the review Blend hash is recorded in `REVIEW_V7_KNEE_RETOPOLOGY.md`.

`FINISH_CANDIDATE.bat v7_knee_retopology knee` and `python -m scripts.verify_v7_knee_retopology` passed on the review files. The final integrity report verifies the V6 hash, 400 pinned source files, unchanged GLB UV/skin/rig/material/animation data, and a 0 mm seam gap in 28 saved poses.

The GLB retains separate vertex indices along the UV0 island boundary. The editable Blender file joins those 30 pairs while keeping UVs on polygon corners. A direct GLB-index weld was rejected because it damaged UV0; it is not part of the review candidate.
