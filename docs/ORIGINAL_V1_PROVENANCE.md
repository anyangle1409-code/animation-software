# Home Gym PT Male ORIGINAL v1 provenance

## O1 blank-source proof — PASS

- Created (UTC): `2026-09-27T21:39:23.143067+00:00`
- Branch: `work/standalone-first-party-audit-20260927`
- Source HEAD: `5acab2f65fb7ac78b41fc7a9f843f75ccc9815c0`
- Blender: `5.2.1 LTS`
- Authoring entry point: `PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat`
- Initializer: `scripts/init_original_v1_blender.py`
- Scaffold generator: `scripts/generate_original_v1_clean_scaffold.py`
- Audit: `scripts/audit_original_v1_blender.py`
- Starting geometry: blank
- Legacy geometry imported: false
- Legacy projection used: false
- Current clean scaffold Blend SHA-256:
  `33f67e42fb8f5bb524b72bfb7b0aee6e3656f853e1c54e6a53034881161f21bf`

The Blend binary stays local under the repository's existing ignore rule. Its
hash and generation inputs are recorded so it can be verified without adding an
intermediate modelling binary to the source checkpoint.

## Approved scaffold inputs

The generated volume uses only the previously approved project-authored numeric
profile and historical mesh algorithm:

- profile commit: `e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62`;
- profile blob: `ee56a49bfb2e32530520fd1811ed9427460256bd`;
- historical mesh algorithm blob: `0216035a6574a0b753f8716f49e603967923f68f`;
- historical clean reference-rig commit:
  `287f72c6a6ac9b1dcd771946ef548d77a40b8ea1`;
- historical clean reference-rig blob:
  `5c0182ae6db57e8de99547aa96d80216105a36ba`.

No V5–V15, CORNER_FINAL, imported character, or MakeHuman geometry, weights,
UVs, materials, bind matrices, or source-rig transforms were used.

## Generated scaffold evidence

- object: `HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD`;
- reference armature: `HGPT_CLEAN_HISTORICAL_REFERENCE_RIG`;
- vertices: 3,890;
- triangles: 7,280;
- reference bones: 53;
- skin rows: normalized by the deterministic generator;
- Blender clean-room audit: PASS;
- audit blockers: 0;
- audit warnings: 0.

This scaffold is not a production character. The 53-bone armature is a clean
historical reference and is not canonical v4. O2 neutral anatomy and the new
`hgpt_canonical_v4_original` numerical rest definition remain open.
