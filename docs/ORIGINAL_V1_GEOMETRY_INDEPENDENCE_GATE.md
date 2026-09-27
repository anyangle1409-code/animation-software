# ORIGINAL v1 geometry-independence gate

The new clean-room character must be independently authored, not merely renamed or lightly altered legacy geometry.

Prepared guard:

`python scripts/audit_original_geometry_independence.py ORIGINAL.glb LEGACY1.glb [LEGACY2.glb ...]`

The guard uses only Python's standard library and compares:
- quantised POSITION sets;
- POSITION stream fingerprint;
- index-stream fingerprint;
- primitive vertex/triangle counts;
- exact-coordinate overlap.

## Acceptance

A clean asset must:
- not have an identical POSITION fingerprint to any legacy asset;
- not have an identical index fingerprint with suspiciously matching geometry;
- not show high exact coordinate overlap combined with the same primitive counts;
- have a documented clean-room provenance chain.

This check is intentionally conservative and is **not** a substitute for provenance records. A low overlap alone does not prove originality; the Blender/provenance history must also show that legacy/MakeHuman geometry was never used as a modelling source.

## Required comparisons

At minimum compare ORIGINAL v1 against:
- V8 body/knee baseline;
- CORNER_FINAL;
- V13e;
- final V15f reference benchmark;
- any MakeHuman-derived built-in GLB exported for comparison, if one exists.

The pinned project-authored procedural scaffold is an allowed ancestor and should be recorded as such rather than treated as a prohibited legacy comparison.
