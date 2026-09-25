# Phase D — final skin/material refinement plan

## Gate

Dormant until:
- hand geometry is visually accepted;
- Phase C grip work has either been accepted or explicitly deferred;
- the candidate body geometry to carry forward is named and hashed.

This phase changes **appearance only**. It must not alter geometry, rig, weights,
exercise mechanics, contacts, equipment or production references.

## Proven project behaviour to preserve

Earlier material investigation established an important renderer constraint:

- the body originally had no real skin material and therefore read as a dull
  grey default glTF surface;
- `CharacterFigure` overwrites the material colour, so persistent authored skin
  tone belongs in `COLOR_0`, not a non-white material base colour;
- metalness/roughness can remain material properties;
- position-neighbour curvature modulation avoids UV-seam colour discontinuities.

Use that architecture again on the **final accepted high-detail body**, rather
than copying an old candidate binary.

## Candidate-only appearance pass

Create a new preserved appearance candidate from the accepted geometry.

Allowed:
- body material creation/refinement;
- `COLOR_0` skin tone;
- subtle curvature-derived tone modulation;
- roughness/metalness;
- later, if deliberately approved, texture maps for regional roughness/colour.

Not allowed:
- POSITION/NORMAL edits merely to improve highlights;
- skin-weight edits;
- body-proportion edits;
- exercise or lighting changes to make the material look better;
- shorts/material changes unless separately scoped.

## Starting numerical reference

The earlier proven candidate used:
- metallic: 0
- roughness: 0.5
- white material base factor
- warm skin through `COLOR_0`
- subtle curvature multiplier roughly 0.86–1.05

Treat these as measured historical references, not mandatory final values.
The earlier review noted that roughness 0.5 could read slightly wet under close
studio lighting; include at least one duller candidate around 0.6 for matched
comparison rather than deciding from memory.

## Automated candidate set

Prefer a tiny bounded appearance sweep, for example:
- roughness 0.50
- roughness 0.58
- roughness 0.64

Keep geometry and all other material inputs byte-identical between variants.

Do not create a large aesthetic search.

## Verification

For every variant prove:
- body POSITION identical to accepted geometry;
- NORMAL identical unless a separately accepted normals-only repair exists;
- UV0/UV1 identical;
- indices/topology identical;
- JOINTS/WEIGHTS identical;
- inverse binds/nodes/skins/animations identical;
- shorts mesh/material identical;
- bare/dressed body colour identical;
- no production asset changed.

Generate matched neutral-light views:
- front;
- three-quarter;
- side;
- upper-body close-up;
- forearm/hand close-up;
- curl Bottom and Peak;
- overhead pose.

Capture each imported candidate in a fresh session if the existing import-cache
behaviour still reuses an earlier `import` source.

## Visual acceptance

Look for:
- skin reads human rather than metallic/grey;
- no orange cast;
- highlights do not exaggerate mesh irregularities;
- shoulder/chest/forearm definition remains readable but not painted-on;
- no visible UV seam tone jump;
- hand tone matches body;
- shorts retain fabric appearance.

Do not make the material compensate for a geometry defect.

## Output

Record:
- accepted geometry hash;
- material parameters;
- colour/curvature algorithm;
- byte-level invariant report;
- matched review boards;
- chosen variant or explicit rejection.

No production promotion in this phase.
