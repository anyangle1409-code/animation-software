# React Three Fiber first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Verified checkpoint:

`a78dcedbe363523805425f3d92e6d82ae133b38f`

Direct R3F source surface:

- imports: **1**
- file: `src/viewer/R3FViewportHost.tsx`

The migration allowlist forbids R3F imports anywhere else.

## Completed

Project-owned / host-neutral work now includes:

- `sceneFrameDriver.ts`
- `studioStage.ts`
- `cameraRigController.ts`
- `sceneHostBindings.tsx`
- `SceneObjectMount.tsx`
- `scenePointerRouter.ts`
- `transformGizmoScene.ts`
- first-party orbit model/input
- CharacterFigure scene ownership
- MuscleView scene ownership
- SkeletonView scene ownership/picking
- EquipmentView scene ownership/picking
- IKHandles scene ownership/picking
- transform gizmo geometry/pointers outside R3F reconciliation

The browser probe proves `ThreeSceneHost` can run real WebGL, the project-owned stage and real exercise-frame state.

## What remains in R3FViewportHost

Only the host adapter still depends directly on R3F:

1. `Canvas`
2. one `useFrame` clock adapter
3. one `useThree` adapter for camera/scene/canvas
4. React composition inside the Canvas
5. `onPointerMissed` fallback around the first-party router

Scene visuals and pointer targets are now mounted through project-owned objects/ports.

## Next exact task — reversible first-party Studio host

Create a React wrapper for the project-owned host that:

- owns a normal DOM container + canvas;
- creates a Three `WebGLRenderer`;
- creates `ThreeSceneHost(browserFrameScheduler(), browserSceneSurface(...), renderer)`;
- creates `HgScenePointerRouter(host.camera, host.scene, canvas, onMiss)`;
- provides the same `SceneHostBindingsProvider`;
- registers `host.onFrame` to call `driveSceneFrame`;
- mounts the same scene content components used by the R3F reference path;
- disposes router/renderer/scene resources deterministically.

Refactor shared scene content out of `R3FViewportHost.tsx` rather than duplicating behavior.

Add a reversible selection mechanism such as:

`?sceneHost=first-party`

Default remains R3F until browser parity passes.

## Acceptance before R3F removal

Run the same browser smoke against the first-party host and require:

- stage/backdrop parity
- skeleton playback
- character/muscle/equipment/IK rendering
- transform gizmo rendering/interaction
- camera presets
- orbit/wheel
- pointer picking/miss/capture
- resize/DPR
- no critical errors

Physical/iPhone touch evidence remains a separate gate.

## R3F removal

Only after first-party-host parity:

1. make first-party host default;
2. prove browser + full suite again;
3. remove `@react-three/fiber`;
4. set R3F import ceiling to zero;
5. rerun all standalone/release gates.

## Drei

Drei source imports are already zero. Package removal still waits for the physical desktop/iPhone Grid/Orbit/Transform gate.

## After R3F

1. React/ReactDOM replacement
2. Three.js replacement last
