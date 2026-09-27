# First-party pose blending migration

Prepared:
- `src/rig/firstPartyPose.ts`
- `src/rig/firstPartyPose.parity.test.ts`

Most of `src/rig/pose.ts` is already project-owned plain-data logic.

Its meaningful Three.js dependency is pivot-aware root blending, which rotates a
pivot by the root quaternion while interpolating.

The prepared implementation replaces that calculation with `HgQuat/HgVec3`
and parity-tests:
- ordinary interpolation;
- pivot-aware interpolation;
- several blend fractions and pivots.

After parity passes, `blendPoses` can be migrated directly rather than keeping
a parallel implementation.

This should remove Three imports from `pose.ts` without changing authored
exercise data or animation timing.
