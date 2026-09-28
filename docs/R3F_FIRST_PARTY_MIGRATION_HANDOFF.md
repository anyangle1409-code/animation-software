# React Three Fiber first-party migration — exact current handoff

Branch: `work/standalone-first-party-audit-20260927`. Source scan: `node scripts/map-third-party-runtime.mjs`; generated exhaustive import details in `reports/third_party_runtime_usage.json`. The current direct R3F surface is **nine files / nine imports**. Imported symbols: `Canvas`, `useFrame`, `useThree`, and type `ThreeEvent`. R3F also supplies JSX intrinsic scene objects, reconciler lifecycle, event raycasting and canvas sizing without an explicit named import; import counts alone understate this work.

| Subsystem | Files | R3F API and behavior to preserve |
|---|---|---|
| Host and ordered evaluation | `src/viewer/Viewport.tsx` | `Canvas` scene/camera/WebGL lifecycle, DPR [1,2], shadows, missed pointer selection, JSX light/background/floor; `useFrame` priority -1 resolves playback and pose before other frame consumers; `useThree` camera/scene for presets and transform proxies. |
| Character and visual pose | `BoneGroups.tsx`, `CharacterFigure.tsx`, `MuscleView.tsx` | `useFrame` applies evaluated bone, skin/grip/corrective, and muscle transforms. |
| Equipment and IK visuals | `EquipmentView.tsx`, `IKHandles.tsx` | `useFrame` reads the same resolved frame for equipment and handle transforms. |
| Orbit and camera input | `FirstPartyOrbitControls.tsx` | `useThree` camera and GL DOM element; `useFrame` advances project-owned orbit model. Physical mouse/iPhone parity remains open. |
| Editing and picking | `FirstPartyTransformGizmo.tsx`, `SkeletonView.tsx`, `Viewport.tsx` | `ThreeEvent` ray, intersections, pointer capture and propagation; frame-based gizmo scale; joint picking; transform proxy scene insertion/removal and missed-click clearing. |

Use `rg -n 'useFrame|useThree|ThreeEvent|<Canvas|onPointerMissed' src/viewer` before every increment; re-run the scanner to catch new imports. `src/viewer/sceneState.ts` currently uses React context. Its plain evaluation/frame data can become a direct host reference only after parity tests. `src/core/frameLoop.ts` provides project-owned priority and insertion-order scheduling. `src/core/sceneLifecycle.ts` now owns one frame loop, size/DPR updates (the existing 1–2 range), context-loss pause/restore and disposal through an injected surface adapter. Focused tests pin scheduling and lifecycle behavior. Neither foundation is connected to the live viewport.

## Renderer-neutral boundary

A future `StudioSceneHost` should own exactly one frame scheduler, canvas resize/DPR, camera, scene root, picking/DOM input, render and disposal. Consumers should receive plain resolved scene-state and ordered callbacks rather than calling R3F hooks. Keep the current Three objects behind a temporary adapter while R3F is replaced. Do not move biomechanics, exercise definitions or contact semantics into the host.

The R3F replacement order is small and reversible:

1. **Parity baseline:** test scheduler ordering, delta clamping, camera preset/focus, selection miss, pointer capture, and exact equipment/pose frame snapshots in the existing R3F path. Capture physical desktop/iPhone visual/input evidence when a compatible browser is available. No dependency removal.
2. **Host lifecycle seam:** the renderer-neutral RAF/resize/DPR/context-loss owner is prepared and tested. Next supply a real DOM/WebGL adapter with lifecycle tests and rendered evidence; keep live `Canvas` intact.
3. **Frame bridge:** route one deterministic resolution and one selected visual consumer through the project frame contract, with side-by-side frame equality at Bottom/Mid/Peak/Return and the exercise catalogue. Revertible per consumer.
4. **Visual consumers:** migrate bone, character, muscle, equipment and IK groups one at a time. Check transform matrices, disposal and contact/equipment clearance after each.
5. **Input bridge:** migrate orbit/gizmo/picking and `ThreeEvent` semantics, including touch and drag suspension. Physical pointer/device parity is a gate.
6. **Host switch:** move canvas, lights, grid/floor and scene root to the first-party host. Verify rendered parity, click/miss/drag, shadows, resize/DPR and export unchanged. Only then can R3F imports and the package be removed.
7. **Next:** React/ReactDOM UI replacement; Three.js renderer/math/GLB removal last. Drei remains installed until the separate physical Grid/Orbit/Transform gate passes even though it has zero source imports.

Run focused tests, typecheck, production build, usage scanner and standalone guard after each increment. The current browser failure (HTML loaded with a blank unexecuted module root) does not count as visual evidence. Avoid broad JSX replacement until the host and one consumer pass their test and review gates.
