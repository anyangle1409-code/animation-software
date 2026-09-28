# Runtime dependency usage map

## Authority

This document describes the migration surfaces and ordering. It does **not** freeze import counts.

For exact current imports, always run:

```bash
node scripts/map-third-party-runtime.mjs
```

and use `reports/third_party_runtime_usage.json` from that run.

For the exact current task and branch, start with `docs/CURRENT_HANDOFF.md`.

## Current package-level state

The standalone branch still declares five direct runtime dependencies while migration is in progress:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand has already been removed and the project-owned observable store is active.

Drei has zero source imports. It remains installed only because the physical Grid/Orbit/Transform desktop/iPhone parity gate has not yet been completed. Do not remove it merely to reduce the dependency count.

## @react-three/fiber

R3F still owns the live scene host and/or frame/event lifecycle around several viewer consumers. The exact import list is scanner-generated and changes as the migration advances.

The behaviours that must survive removal are:

- one canvas/scene/camera lifecycle;
- DPR/resize/context-loss handling;
- ordered frame evaluation with pose resolution before visual consumers;
- character, bone, equipment, muscle and IK-handle updates;
- orbit/camera progression;
- picking, pointer capture, missed selection and gizmo interaction;
- disposal and detach semantics.

Prepared project-owned boundaries include:

- `src/core/frameLoop.ts`
- `src/core/sceneLifecycle.ts`
- `src/core/browserSceneSurface.ts`
- `src/viewer/threeSceneHost.ts`
- `src/viewer/sceneFrameSnapshot.ts`
- `src/viewer/sceneFrameObjects.ts`
- renderer-neutral per-consumer snapshots/resolvers recorded in the current R3F handoff
- framework-neutral `sceneStateCore.ts`

The live host must move only after the required numerical and browser/device parity evidence exists.

## React / ReactDOM

React still drives the editor UI and temporary viewer wrappers.

Removal comes **after R3F**, because replacing UI state/lifecycle while the scene bridge is still changing would combine unrelated risks.

Target behaviour:

- project-owned DOM construction/update helpers;
- project-owned store subscriptions;
- explicit lifecycle/disposal;
- standard DOM pointer/keyboard events;
- preserved accessibility, timeline/editor behaviour and mobile inspection.

The core store is already framework-independent apart from its temporary React hook bridge.

## Three.js

Three remains the largest and final runtime dependency.

Current responsibilities include combinations of:

- vectors/quaternions/matrices/Eulers;
- rig/FK/IK/contact math;
- bones and skinning objects;
- character/equipment scene objects;
- materials/geometry;
- camera and picking helpers;
- GLTF/GLB loading/export;
- final WebGL rendering.

Prepared first-party foundations already exist for math, skeleton/pose parity, GLB container/accessor/builder work and scene lifecycle.

Three removal stays last so renderer replacement is not mixed with a simultaneous biomechanics rewrite.

## Required order

1. Complete the R3F consumer/host migration and physical parity.
2. Remove R3F.
3. Remove React/ReactDOM after UI parity.
4. Migrate remaining engine/rig/GLB/renderer responsibilities off Three.
5. Remove Three.
6. Remove Drei as soon as its separate physical parity gate permits; it does not need to wait for the later steps once that gate is genuinely passed.
7. Re-run the full standalone/release audits after every dependency removal.

## Non-negotiable rules

- Do not replace one third-party runtime library with another.
- Do not change exercise mechanics, joint limits, contacts or acceptance thresholds to accommodate a replacement implementation.
- Do not delete a dependency while production imports/behaviour still require it.
- Do not treat a unit-test pass as a substitute for an explicitly required physical visual/input gate.
