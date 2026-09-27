# ORIGINAL v1 clean scaffold usage

## Purpose

Create the first ORIGINAL v1 modelling surface from project-authored historical numeric body profiles only.

This is a **clean scaffold**, not a production character.

## Preconditions

1. Preserve the final V15f legacy benchmark first.
2. Work on:
   `work/standalone-first-party-audit-20260927`
3. Ensure Blender is installed.
4. Do not copy/import any legacy character files into the clean-room workspace.

## Commands

From repository root:

```bat
START_ORIGINAL_V1_CLEAN_ROOM.bat
GENERATE_ORIGINAL_V1_CLEAN_SCAFFOLD.bat
```

The second command will initialize the clean-room Blend automatically if it does not yet exist.

## What is generated

`ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend`

Containing:
- `HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD`
- `HGPT_CLEAN_HISTORICAL_REFERENCE_RIG`

The reference rig is the clean historical 53-bone rig, **not canonical v4**.

Expected deterministic scaffold invariants:
- 3,890 vertices;
- 7,280 triangles;
- 53 historical reference bones;
- all skin rows normalized;
- no legacy/third-party geometry import.

Generation stops if these invariants drift.

## Provenance

Numeric profile source:
- commit `e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62`
- `src/body/profiles.ts` blob `ee56a49bfb2e32530520fd1811ed9427460256bd`

Historical clean rig:
- commit `287f72c6a6ac9b1dcd771946ef548d77a40b8ea1`
- `src/rig/humanoid.ts` blob `5c0182ae6db57e8de99547aa96d80216105a36ba`

The generator recreates geometry from those numeric specifications. It never loads an old GLB/Blend as geometry input.

## Next modelling phase

Do not polish the scaffold as if it were final.

Use it only as a clean starting volume for:
1. canonical v4 ORIGINAL proportion rebaseline;
2. shoulder/axilla topology;
3. pelvis/groin topology;
4. knee topology;
5. hand/palm/metacarpal/thumb reconstruction;
6. feet/toes;
7. face/head;
8. deformation-friendly edge flow;
9. original shorts/materials;
10. final v4 binding/weights.

The final ORIGINAL v1 must then pass the whole-body movement envelope and geometry-independence gates.
