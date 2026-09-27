# First-party skeleton migration

Prepared:
- `src/rig/firstPartySkeleton.ts`
- `src/rig/firstPartySkeleton.parity.test.ts`

This is a parallel implementation. It is **not** the production skeleton yet.

It uses:
- project `BoneDefinition` / `Pose` plain data;
- first-party `HgVec3`, `HgQuat`, `HgMat4`;
- no Three.js imports.

## Parity scope

The prepared test compares against the current Three-based implementation for:
- canonical names/hierarchy;
- lengths/rest transforms;
- every exercise in the library;
- multiple sampled poses per exercise;
- every bone matrix;
- head/tail queries;
- world quaternion queries.

Target tolerance is deliberately much tighter than biomechanical/contact gates.

## Why this matters

Once this parallel implementation passes, the core exercise/IK/contact engine can
be moved away from Three independently of the renderer.

This reduces risk:
- first prove biomechanics math;
- then replace viewport/rendering;
- never debug a new renderer and new skeleton math simultaneously.

## Integration rule

Do not change the live `canonicalSkeleton` export immediately.

First:
1. pass isolated math tests;
2. pass Three parity tests;
3. pass whole-library skeleton parity;
4. migrate IK/contact/attachment callers in controlled groups;
5. run full existing suite;
6. only then switch the production skeleton implementation.

Canonical v4 ORIGINAL rest geometry is a separate data/provenance change. Do not
combine the v3→v4 numerical rig rebaseline with the Three→first-party math
implementation switch in one commit.
