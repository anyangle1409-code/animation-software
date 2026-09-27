# ORIGINAL v1 Blender clean-room audit

After generating the clean scaffold:

```bat
GENERATE_ORIGINAL_V1_CLEAN_SCAFFOLD.bat
AUDIT_ORIGINAL_V1_CLEAN_ROOM.bat
```

The audit checks:
- clean-room scene metadata;
- no legacy-import flag;
- no linked external Blend libraries;
- no external images/textures;
- no image-texture material nodes;
- no obvious legacy/MakeHuman/Meshy identifiers in scene datablocks;
- deterministic scaffold vertex/triangle counts;
- clean scaffold provenance properties;
- 53-bone historical reference rig;
- reference-only rig metadata;
- no imported actions/animations.

Report:
`reports/original_v1_blender_audit.json`

A PASS means the **starting workspace** is clean. It does not make the scaffold a
finished production model.

As ORIGINAL v1 progresses, this stage audit should be supplemented by production
topology/rig/material/movement audits rather than weakening its clean-room rules.
