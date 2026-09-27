# First-party math parity plan

Prepared implementation:
- `src/core/linearMath.ts`
- `src/core/linearMath.test.ts`

This module is intentionally **not connected to production code yet**.

## Why prepare it now

Three.js currently supplies mathematics to the rig, IK, equipment attachments,
viewer and GLB paths. Replacing rendering before replacing the engine maths would
mix too many variables at once.

The first-party math module establishes:
- vectors;
- quaternions;
- XZY Euler conversion;
- matrix basis/compose/multiply/inverse;
- vector transforms;
- quaternion interpolation.

## Verification before integration

Run:
```bat
npm test -- src/core/linearMath.test.ts
npm run typecheck
```

Then add temporary migration-only parity tests against Three.js for:
1. random vectors/quaternion application;
2. XZY Euler conversion;
3. basis → quaternion;
4. compose;
5. parent × local multiplication;
6. inversion;
7. canonical skeleton rest frames;
8. every sampled exercise pose matrix.

Parity tolerance target:
- pure math: <= 1e-12 where practical;
- float32 exported/runtime samples: <= existing export tolerance.

The temporary Three parity tests are development evidence and can be deleted
after Three is removed. The production implementation remains entirely
first-party.

## Integration order

1. verify isolated math tests;
2. add parity harness;
3. migrate a copy of `boneFrame`;
4. migrate Skeleton construction;
5. migrate PoseEvaluation;
6. run every exercise/contact/IK gate;
7. then migrate IK/attachments;
8. do not remove Three until GLB + renderer paths are independently replaced.

## Stop rule

If a parity difference appears, investigate the convention/order. Do not retune
exercise angles, rig limits or contact tolerances to make the replacement pass.
