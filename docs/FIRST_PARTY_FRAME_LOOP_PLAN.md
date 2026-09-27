# First-party frame-loop migration

Prepared:
- `src/core/frameLoop.ts`
- `src/core/frameLoop.test.ts`

The module is isolated and not yet connected to the viewport.

## R3F behaviour it replaces

The current R3F viewport uses `useFrame`, including:
- FrameDriver at priority -1;
- bone visual matrices;
- character posing;
- equipment placement;
- muscle transforms;
- IK handle transforms;
- camera interpolation;
- gizmo proxy synchronisation.

`HgFrameLoop` preserves:
- numeric priority ordering;
- stable insertion order;
- one shared requestAnimationFrame loop;
- deterministic delta/elapsed values;
- safe subscription removal during a frame.

## Intended integration

Do not give each scene controller its own RAF.

Use one loop:
1. priority -100: resolve playback/frame/pose;
2. priority 0: character/bones/equipment/muscles/handles;
3. priority 50: camera;
4. priority 100: interaction proxy sync;
5. priority 1000: renderer draw.

Exact priorities are migration implementation details; the invariant is that
frame resolution happens before every consumer.

## Verification

Run:
```
npm test -- src/core/frameLoop.test.ts
```

Then add a migration test recording current R3F callback ordering on a known
exercise frame before switching the viewport.

No exercise, grip, contact or character mechanics should change when the frame
host changes.
