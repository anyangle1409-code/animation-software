# First-party GLB implementation plan

## Prepared layer 1

- `src/core/glbContainer.ts`
- `src/core/glbContainer.test.ts`

This first layer implements only the GLB 2.0 container:
- header;
- JSON chunk;
- BIN chunks;
- 4-byte alignment;
- deterministic validation.

It has no Three.js or other third-party imports and is not connected to the
production importer/exporter yet.

## Why a narrow implementation

Home Gym PT does not need a general glTF engine.

Implement only what the operational product uses.

## Layer 2 — typed accessors

Project-owned support for:
- bufferViews;
- accessors;
- byte offsets/strides;
- component types:
  - BYTE / UNSIGNED_BYTE;
  - SHORT / UNSIGNED_SHORT;
  - UNSIGNED_INT;
  - FLOAT;
- SCALAR / VEC2 / VEC3 / VEC4 / MAT4;
- normalized integer attributes where actually required.

Reject unsupported sparse/interleaved/extension cases until deliberately added.

## Layer 3 — character mesh/skin

Read/write:
- POSITION;
- NORMAL;
- TEXCOORD_0 only if ORIGINAL v1 uses UVs;
- COLOR_0 if used;
- indices;
- JOINTS_0;
- WEIGHTS_0;
- nodes;
- skins;
- inverseBindMatrices;
- project materials.

## Layer 4 — animation

Read/write:
- translation;
- rotation quaternion;
- scale only if project output uses it;
- LINEAR interpolation initially;
- project-authored exercise extras/metadata.

## Layer 5 — project round-trip

Required fixtures:
1. ORIGINAL v1 neutral character;
2. one curl clip;
3. one push-up clip;
4. one squat/lunge clip;
5. one pull-up clip;
6. equipment primitives.

Compare:
- vertex/index bytes where deterministic;
- bone hierarchy;
- bind matrices;
- animation sampled transforms;
- materials/extras;
- load → save → load semantic equivalence.

## Migration rule

Use Three's GLTF loader/exporter only as temporary development comparison
evidence while both implementations coexist.

Do not make the first-party codec imitate unsupported Three/glTF features merely
for completeness.

When project fixtures all pass through the first-party codec and renderer, remove
the Three GLTF paths from the operational product.
