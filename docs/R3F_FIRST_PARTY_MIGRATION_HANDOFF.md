# React Three Fiber first-party migration — exact current handoff

Branch: `work/standalone-first-party-audit-20260927`

Verified checkpoint: `3970ae603249d225d6a513d539dc496683036fcd`

The direct R3F source surface is now **one file / one import**:

- `src/viewer/R3FViewportHost.tsx`

`RUNTIME_MIGRATION_ALLOWLIST.json` enforces this as a one-way ceiling. No other source file may import `@react-three/fiber`.

## What has already moved off direct R3F APIs

The following live consumers no longer import `useFrame` or `useThree`:

- `BoneGroups.tsx`
- `CharacterFigure.tsx`
- `MuscleView.tsx`
- `EquipmentView.tsx`
- `IKHandles.tsx`
- `FirstPartyOrbitControls.tsx`
- `FirstPartyTransformGizmo.tsx`
- `SkeletonView.tsx` already had no direct R3F import

They register with the project-owned dispatcher through `useSceneFrame` and the priorities in `sceneStateCore.ts`.

`Viewport.tsx` is now host-agnostic: it creates the shared `SceneState` and mounts the temporary `R3FViewportHost`.

## Remaining R3F responsibilities

All remaining direct R3F use is intentionally concentrated in `R3FViewportHost.tsx`:

- `Canvas` creation and renderer/scene/camera lifecycle
- the single `useFrame` driver that advances playback, resolves the frame, applies the pose and dispatches project-owned consumers
- `useThree` access for camera, scene root and DOM canvas
- JSX Three-object reconciliation for lights, floor/grid and all visual subtrees
- R3F pointer/ray event routing, pointer-miss selection clearing and picking
- host insertion/removal of transform proxies

The direct import count therefore understates the remaining work: JSX intrinsic scene objects and event reconciliation still depend on the R3F reconciler even where child components have no R3F import.

## Project-owned foundations already verified

### Frame and scene state

- `src/core/frameLoop.ts`: project-owned priority/insertion-order scheduler and `HgFrameDispatcher`
- `src/viewer/sceneStateCore.ts`: renderer/framework-neutral evaluation, resolved-frame state and consumer dispatcher
- `src/viewer/sceneState.ts`: temporary React context wrapper with `useSceneFrame`

All live visual frame consumers now run through this dispatcher.

### Scene lifecycle and browser surface

- `src/core/sceneLifecycle.ts`
- `src/core/browserSceneSurface.ts`
- `src/viewer/threeSceneHost.ts`

These own frame scheduling, resize/DPR, context loss/restoration and disposal independently of R3F.

### Real-WebGL proof

The browser smoke mounts `scripts/browser-three-host-probe.js`, which creates a real Three `WebGLRenderer` behind the project-owned `ThreeSceneHost`.

Verified in Chromium:

- the first-party host renders real WebGL;
- its frame loop visibly advances a scene;
- its drawing buffer follows container resize;
- disposal is explicit.

This proves the host lifecycle can drive real WebGL. It does **not** yet prove the complete Studio scene has been migrated to that host.

### Live consumer browser evidence

The same browser smoke verifies the current production/R3F reference path for:

- BoneGroups/SkeletonView playback
- CharacterFigure across authored poses
- MuscleView across authored poses
- EquipmentView visibility/rendering
- IKHandles visibility/rendering with temporary editor IK state
- transform-gizmo selected/unselected rendering
- camera presets
- mouse orbit and wheel zoom
- backdrop and responsive resize

These checks are the parity reference for future host migration.

## Remaining migration problem

The remaining problem is no longer individual `useFrame` consumers. It is the **R3F host/reconciler itself**.

Do not redo the consumer dispatcher work.

### Next safe cloud increments

1. **Static scene ownership**
   - extract project-owned functions that create/update/dispose background, lights, floor and grid objects;
   - test them without R3F;
   - keep the live R3F JSX path unchanged until parity is proven.

2. **Frame driver ownership**
   - move playback advance + `resolveFrame` + pose application + consumer dispatch into a renderer-neutral driver callable by either host;
   - make the current R3F `useFrame` wrapper only adapt its clock/delta to that driver;
   - add Bottom/Mid/Peak/Return and playback-loop tests.

3. **Camera/orbit host injection**
   - move camera preset/focus logic to a host-neutral controller receiving camera + orbit handle ports;
   - keep React wrappers thin.

4. **Scene/pointer input bridge**
   - replace pointer-miss selection clearing, picking/raycast and proxy insertion/removal with project-owned host APIs;
   - preserve pointer capture/propagation and gizmo drag suspension;
   - automated browser tests may supplement this, but physical desktop/iPhone parity remains mandatory.

5. **First-party Studio host**
   - mount a reversible project-owned Studio host beside the R3F reference path;
   - compare the existing browser evidence set against both;
   - do not remove R3F until render/input/lifecycle parity passes.

6. **R3F removal**
   - when direct imports are zero and the complete host/reconciler parity gate passes, remove `@react-three/fiber`;
   - immediately rerun typecheck, full suite, production build, browser smoke, dependency anti-creep, external-resource and network gates.

## Drei

Drei source imports are already zero. Keep the package until the separate physical Grid/Orbit/Transform desktop/iPhone gate passes. Do not conflate Drei package removal with R3F host removal.

## Physical evidence boundary

Automated Chromium smoke is strong supplementary evidence but is **not** the physical/iPhone acceptance gate. Touch, real-device pointer capture and subjective visual interaction still require `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.

## After R3F

Proceed in order:

1. React/ReactDOM UI/lifecycle replacement;
2. Three.js math/rig/GLB/scene/renderer replacement last.

Do not replace R3F with another third-party scene/reconciler library.
