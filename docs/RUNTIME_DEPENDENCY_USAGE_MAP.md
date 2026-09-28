# Runtime dependency usage map — verified source surfaces

Source reference inspected:
`chatgpt/absolute-retarget-imports @ 47187360b5d631d438a6b33b284ad06732e244cb`

This is a manually verified map of the main runtime surfaces. The local scanner
`scripts/map-third-party-runtime.mjs` remains the authoritative exhaustive check
when Work has the repository locally.

## Zustand

Direct store modules already migrated on the standalone branch:
- `src/editor/store.ts`
- `src/editor/characterStore.ts`
- `src/editor/generationStore.ts`

Replacement:
- `src/core/store.ts`

Status:
- implementation patched;
- typecheck/build/full-test verification pending;
- package removal pending.

## @react-three/drei

Verified direct usage is concentrated in:

### `src/viewer/Viewport.tsx`

Imports:
- `Grid`
- `OrbitControls`
- `TransformControls`

Roles:
- floor/reference grid rendering;
- mouse/touch orbit, zoom and damping;
- camera target control;
- rotation/translation gizmo for bones/equipment;
- translation gizmo for IK target/pole handles.

This is a favourable isolation boundary: replace these three helpers first while
keeping R3F and Three temporarily.

### First-party replacement interfaces

`OrbitController`
- canvas pointer/touch/wheel input;
- target vector;
- distance clamp 0.6–12 m;
- damping equivalent to current 0.12;
- update(dt);
- programmatic target updates from camera presets/focus mode;
- enable/disable while gizmo drag is active.

`TransformGizmo`
- translate and rotate modes;
- object/proxy transform;
- dragStart / change / dragEnd;
- axis picking;
- camera-aware scale;
- emits project plain position/quaternion values.

`ReferenceGrid`
- 0.25 m cells;
- 1 m major sections;
- configurable cell/section/background colours;
- fade/distance behaviour;
- optional floorless mode.

Acceptance:
- zero `@react-three/drei` imports;
- camera behaviour and mobile touch controls preserved;
- all gizmo edits remain undoable through the existing store APIs.

## @react-three/fiber

### `src/viewer/Viewport.tsx`
Uses:
- `Canvas` — WebGL scene/camera/renderer lifecycle;
- `useFrame` — frame pipeline, camera movement and gizmo proxy sync;
- `useThree` — current camera/scene access.

Critical current ordering:
- `FrameDriver` runs at priority -1;
- it advances playback;
- writes studio time;
- resolves the frame;
- applies pose evaluation;
- scene consumers then read that resolved frame.

This ordering must be preserved exactly by the first-party render loop.

### `src/viewer/BoneGroups.tsx`
Uses `useFrame` to copy evaluated bone matrices to per-bone visual groups.

### `src/viewer/CharacterFigure.tsx`
Uses `useFrame` to apply the resolved character pose/grip/correctives.

### `src/viewer/EquipmentView.tsx`
Uses `useFrame` to apply resolved equipment transforms and character-specific
hand attachment transforms.

### `src/viewer/IKHandles.tsx`
Uses `useFrame` to update target/pole handle positions.

### `src/viewer/MuscleView.tsx`
Uses `useFrame` to update resolved muscle belly transforms.

### `src/viewer/SkeletonView.tsx`
No longer imports R3F directly. Selectable joints use the project-owned minimal `HgSceneStopEvent` structural type; R3F still supplies the JSX runtime event until the input bridge moves.

### R3F-independent scene host target

Create a project-owned `StudioSceneHost` that owns:
- canvas element;
- renderer;
- scene root;
- camera;
- resize/DPR;
- requestAnimationFrame loop;
- ordered frame callbacks;
- pointer/touch routing;
- object picking;
- disposal.

Proposed callback phases:
1. `resolve` — playback + frame resolution;
2. `pose` — character/bones/equipment/muscles/handles;
3. `camera`;
4. `interaction`;
5. `render`.

Do not let individual views start their own RAF loops.

Acceptance:
- zero `@react-three/fiber` imports;
- one project-owned frame loop;
- current FrameDriver ordering preserved;
- exact animation/contact/equipment results unchanged.

## React / ReactDOM

Verified UI dependence includes:
- `src/editor/App.tsx`
- `src/editor/Timeline.tsx`
- `src/editor/Toolbar.tsx`
- all `src/editor/panels/*.tsx`
- viewer JSX components;
- `src/viewer/sceneState.ts` context;
- `src/core/store.ts` temporary `useSyncExternalStore` bridge.

Do not remove React before R3F is gone.

Target:
- project-owned DOM rendering/update helpers;
- project-owned store subscriptions;
- explicit lifecycle/disposal;
- standard DOM pointer/keyboard events;
- no general-purpose framework beyond the app's actual needs.

The core observable store is deliberately usable without React once the temporary
hook wrapper is removed.

## Three.js

Verified usage spans multiple concerns and must be replaced last.

### Viewer
- `Group`, `Mesh`, `Object3D`
- `Vector3`
- `Quaternion`
- `Matrix4`
- `Euler`
- `MeshStandardMaterial`

### Rig/pose
`src/rig/skeleton.ts` uses Three mathematics for rest frames, FK and pose
evaluation.

### Character
Skinned character objects/materials/geometry are currently represented through
Three classes.

### Equipment/attachments
Matrices/quaternions/vector transforms are Three-based.

### GLB
Import/export currently relies on Three ecosystem GLTF functionality.

Replacement order inside Three removal:
1. first-party linear algebra;
2. rig/FK/IK/contact math migration;
3. first-party GLB subset;
4. project scene/object data;
5. project WebGL renderer;
6. delete Three only after all parity gates pass.

## three-stdlib

Verified in `src/viewer/Viewport.tsx` as the `OrbitControls` implementation
type. It disappears with the first-party orbit controller/Drei removal.

## Equipment geometry

`src/viewer/equipmentMeshes.tsx` does not import a third-party equipment model.
It renders the project's own primitive equipment descriptions as JSX geometry.

This means the equipment **design/data can remain**, while its JSX/Three rendering
adapter is replaced.

## Scene state

`src/viewer/sceneState.ts` contains only:
- `PoseEvaluation`;
- current resolved frame;
- React context wrapper.

Preserve the plain scene-state object; replace only React context access with the
project scene host's direct state reference.

## Usage-saving implementation order

1. Verify/remove Zustand.
2. Implement first-party OrbitController + grid while Drei still exists as a comparison.
3. Implement TransformGizmo and compare behaviour.
4. Remove Drei.
5. Implement StudioSceneHost while keeping Three.
6. Convert viewer components into explicit scene-controller modules.
7. Remove R3F.
8. Replace React UI.
9. Move rig/engine math from Three onto first-party math.
10. Add first-party GLB reader/writer.
11. Add first-party renderer.
12. Remove Three.

At every removal, run the one-command standalone audit and preserve blocker counts.
