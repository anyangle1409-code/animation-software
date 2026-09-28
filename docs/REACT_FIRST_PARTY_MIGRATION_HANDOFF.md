# React / ReactDOM first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Verified checkpoint:

`6294907d3bd48a775e6250584b5420537a43a89b`

## Boundary

R3F source migration is complete. The live viewport uses the project-owned WebGL host and there are zero R3F/Drei source imports.

The current migration target is React/ReactDOM.

Do not replace React with another third-party UI framework. The target is project-owned DOM/lifecycle code backed by existing first-party stores/controllers.

## Already framework-neutral

### State and editor behavior

- `src/core/observableStore.ts`
- `src/editor/store.ts` exports framework-neutral `studioStore`
- `src/editor/keyboardController.ts`
- `src/editor/layoutState.ts`
- existing history/playback/comparison/diagnostic/generation logic

React hooks are adapters, not the source of truth.

### Viewport runtime

- `src/viewer/firstPartyViewportRuntime.ts`
- `src/viewer/threeSceneHost.ts`
- `src/core/browserSceneSurface.ts`
- `src/viewer/sceneFrameDriver.ts`
- `src/viewer/scenePointerRouter.ts`
- `src/viewer/sceneHostTypes.ts`
- `src/viewer/studioStage.ts`
- renderer-neutral scene resource modules for skeleton/equipment/muscle/IK/gizmo/camera/orbit

The canvas, WebGL renderer, frame clock, clip tracking, pointer router and host disposal no longer need React.

## React-owned surfaces that remain

### Root/editor chrome

- `src/main.tsx`
- `src/editor/App.tsx`
- `src/editor/Toolbar.tsx`
- `src/editor/Timeline.tsx`
- `src/editor/panels/*.tsx`

### Viewport composition adapters

- `src/viewer/FirstPartyViewportHost.tsx` — DOM refs + temporary content mount
- `src/viewer/StudioSceneContent.tsx`
- `src/viewer/sceneState.ts`
- `src/viewer/sceneHostBindings.tsx`
- thin React lifecycle wrappers around project-owned scene resources
- asynchronous character-build lifecycle wrapper

## Migration order

### R1 — framework-neutral Studio scene controller

Build a plain TypeScript controller that can mount/update/dispose the current scene using the existing project-owned modules.

Requirements:

- receives `SceneState` + `SceneHostBindings`;
- subscribes directly to framework-neutral state stores;
- owns static stage replacement when backdrop/grid changes;
- owns skeleton/equipment/muscle/IK scene resource creation and disposal;
- registers/unregisters pointer handlers explicitly;
- registers frame consumers with existing priorities;
- owns camera/orbit and transform-gizmo controllers;
- preserves async character build cancellation/disposal semantics.

Do not delete the React scene path until automated browser parity passes.

### R2 — switch scene composition

- make the framework-neutral controller the live first-party viewport scene path;
- retain a short-lived dev/reference switch only if needed for parity;
- rerun the full current Chromium evidence set;
- remove redundant React scene wrappers/context adapters after parity.

### R3 — editor DOM shell

Build project-owned DOM primitives and migrate, in small parity-gated groups:

1. app shell/tabs/panel visibility;
2. toolbar/playback controls;
3. timeline;
4. simple read-only panels;
5. editing panels/forms;
6. generation/review/export workflows.

Use `studioStore.subscribe/getState` and `studioLayoutStore`; do not create a second state model.

### R4 — React root removal

When all live editor/viewport surfaces are first-party DOM/lifecycle code:

- replace `createRoot(...).render(<App />)`;
- remove temporary React hook/context adapters;
- remove React/ReactDOM source imports;
- set one-way import ceilings to zero;
- remove React/ReactDOM packages only after build/browser parity passes.

## Acceptance for every increment

- focused unit tests for extracted controller/model behavior;
- typecheck;
- full suite;
- production build;
- current standalone/provenance/network gates;
- Chromium browser smoke for user-visible/lifecycle changes;
- no migration-threshold weakening.

## Preserve

- CSS/classes and visible editor layout unless a separate product change explicitly authorizes a redesign;
- keyboard shortcuts;
- timeline/playback semantics;
- camera/orbit/picking/gizmo behavior;
- accessibility-relevant labels/button semantics;
- current exercise and biomechanical behavior.

## Do not

- mix React removal with Three.js math/renderer replacement;
- replace React with another third-party framework;
- create a parallel state architecture;
- change exercise data/mechanics to accommodate UI migration.
