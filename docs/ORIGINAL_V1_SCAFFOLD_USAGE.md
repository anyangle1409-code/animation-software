# ORIGINAL v1 clean scaffold recovery reference

## Status

**Supporting recovery reference only.** Normal current work starts from `docs/CURRENT_HANDOFF.md` and uses `PREPARE_ORIGINAL_V1_O2.bat`.

Use this document only if the verified local O1 clean-room Blend is missing or must be reconstructed from the pinned first-party scaffold evidence.

## Recovery command

From repository root on the active standalone branch:

```bat
PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat
```

That guarded command initializes the clean-room workspace if required, regenerates the pinned scaffold, runs the clean-room audit, and opens the Blend only after the audit passes.

Do not run the lower-level generator/audit helper batch files directly during normal continuation work.

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

## After recovery

Do not polish the O1 scaffold as if it were final. Return immediately to the current O2 handoff and materialise/use `hgpt_canonical_v4_original` under the clean-room constraints.
