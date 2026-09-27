# First-party software replacement architecture

## Objective

Replace every third-party runtime dependency while preserving the current Home Gym PT behaviour as the specification.

Current direct runtime dependencies:
- zustand
- react
- react-dom
- @react-three/fiber
- @react-three/drei
- three

Three.js is deeply used beyond rendering and must be replaced last.

## Existing first-party seams worth preserving

The codebase already has several useful project-owned data boundaries:
- `src/rig/types.ts` defines plain `Vec3`, poses, limits and bone definitions.
- exercise definitions are plain data.
- animation clips and technique rules are plain project data.
- equipment definitions are plain project data.
- generation intent/family architecture is independent of the visible renderer.

The replacement should strengthen these seams rather than push graphics objects deeper into the engine.

## S1 — first-party observable store (replace Zustand)

Target module:
`src/core/store.ts`

Required interface:
- create store from `set/get` initializer;
- `getState()`;
- `setState()`;
- `subscribe()`;
- selector-capable UI hook while React remains;
- deterministic synchronous updates.

Migration targets include:
- `src/editor/store.ts`
- `src/editor/characterStore.ts`
- `src/editor/generationStore.ts`
- any additional imports found by `map-third-party-runtime.mjs`.

During this phase React may still be used only to expose store snapshots to components. The state engine itself must be project-authored.

Acceptance:
- editor/store tests unchanged;
- undo/redo unchanged;
- playback unchanged;
- generated-candidate flow unchanged;
- character loading state unchanged;
- zero imports from `zustand`.

## S2 — first-party viewport helpers (replace Drei)

Replace separately:
- orbit camera controls;
- transform gizmo;
- grid;
- any helper geometries/loaders used only by Drei.

Do not remove R3F or Three in this step.

Create project-owned equivalents with behavioural tests for:
- camera target/zoom/rotation;
- touch rotate/zoom;
- transform drag start/change/end;
- grid visibility.

Acceptance:
- zero `@react-three/drei` imports.

## S3 — first-party scene bridge/render loop (replace R3F)

Keep Three temporarily, but remove React Three Fiber.

Create a project scene host that owns:
- canvas;
- renderer lifecycle;
- resize/device-pixel ratio;
- animation frame loop;
- scene/camera creation;
- per-frame playback callback order;
- pointer/touch event routing;
- disposal.

React UI may still mount the canvas host as a normal DOM component during this phase.

Convert viewer components from JSX scene declarations to explicit project scene-controller modules.

Acceptance:
- `FrameDriver` ordering preserved;
- cameras preserved;
- character/equipment/muscle/skeleton visibility preserved;
- transform controls preserved through S2 helpers;
- mobile inspection preserved;
- zero `@react-three/fiber` imports.

## S4 — first-party UI layer (replace React/ReactDOM)

Once the viewport no longer depends on React rendering, replace the editor UI with project DOM modules.

Required project primitives:
- element creation/update;
- event binding/disposal;
- keyed list update;
- conditional sections;
- store subscription binding;
- form field binding;
- focus/keyboard handling.

Avoid creating a general-purpose framework. Implement only the primitives this application needs.

Preserve:
- toolbar;
- timeline;
- all editor panels;
- generation/review workflows;
- accessibility labels and keyboard behaviour;
- mobile inspection layout.

Acceptance:
- zero `react` / `react-dom` imports;
- no JSX/TSX required in production source;
- UI parity tests / browser snapshots pass.

## S5 — first-party mathematics

This begins before Three removal, but becomes mandatory for S6+.

Project-owned types:
- Vec2/Vec3/Vec4;
- Quaternion;
- Mat3/Mat4;
- Euler conversion for the project's fixed `XZY` convention;
- compose/decompose;
- inverse;
- basis construction;
- vector transform;
- quaternion slerp;
- interpolation;
- bounding boxes/spheres as needed.

Important migration target:
`src/rig/skeleton.ts` currently relies on Three for FK matrices/quaternions.

Build numerical parity tests against the current runtime before switching it.

Acceptance tolerances should be explicit and substantially tighter than model/contact tolerances.

## S6 — first-party rig/animation math

Move:
- skeleton rest-frame construction;
- pose evaluation;
- IK helper matrices;
- hand/equipment attachment matrices;
- retarget transform math;

onto S5 math.

Do this before replacing the renderer so biomechanics do not change at the same time as visual output.

Acceptance:
- existing pose matrices match current runtime within tolerance;
- IK tests unchanged;
- contact locks unchanged;
- exported sampled transforms match reference.

## S7 — first-party GLB reader/writer

Using the glTF/GLB file format is allowed; the implementation must be project-authored.

Reader needs only the subset Home Gym PT supports:
- GLB container chunks;
- JSON;
- bufferViews/accessors;
- POSITION/NORMAL/UV/COLOR;
- indices;
- JOINTS/WEIGHTS;
- nodes;
- skins/inverse bind matrices;
- animations;
- materials required by the project;
- project extras/metadata.

Writer needs:
- project character;
- bone hierarchy;
- skin;
- animation tracks;
- equipment geometry;
- materials;
- extras.

Do not try to implement the entire glTF ecosystem before the supported subset is proven.

Create fixture round-trip tests before replacing Three's GLTFLoader/GLTFExporter.

## S8 — first-party rendering

Start with WebGL2 as the simplest widely available browser target.

Required renderer scope:
- indexed meshes;
- skinned meshes;
- vertex colours;
- basic PBR-like or project-specific lit material;
- line/skeleton drawing;
- simple primitives/equipment;
- camera;
- directional/ambient/rim lighting;
- depth;
- transparency only where actually required;
- picking.

Do not build a generic game engine.

The renderer needs only Home Gym PT features.

Acceptance:
- matched screenshots of canonical views;
- silhouette parity;
- contact/equipment placement parity;
- mobile performance threshold.

## S9 — delete Three.js

Only after S5–S8 are active:
- remove `three`;
- remove `three/examples`;
- remove any `three-stdlib` transitive use;
- regenerate package lock;
- run full suite;
- run `check-first-party-release-readiness.mjs`.

## Architectural rule

Biomechanics must not depend on rendering types.

Long-term:
- rig/exercises/generation/constraints use project plain data/math;
- renderer adapts those results for display;
- exporter serialises project data;
- UI observes project stores.

This makes future renderer/UI replacements independent of exercise correctness.

## Progress measurement

After every stage run:

```
node scripts/map-third-party-runtime.mjs
node scripts/audit-third-party-dependencies.mjs
node scripts/check-first-party-release-readiness.mjs
```

The dependency counts must move monotonically toward zero.
