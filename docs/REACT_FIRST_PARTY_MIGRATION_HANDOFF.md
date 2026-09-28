# React / ReactDOM first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Latest fully verified checkpoint:

`5be6098519be536cbd08b21d85dfec0313d83eea`

## Boundary

R3F source migration is complete. The live viewport uses the project-owned WebGL host and there are zero R3F/Drei source imports.

The current migration target is React/ReactDOM.

Do not replace React with another third-party UI framework. The target is project-owned DOM/lifecycle code backed by existing first-party stores/controllers.

## Verified checkpoint

At `5be60985`:

- Standalone prep verification: PASS
- full suite: 118 test files PASS, 2 skipped
- full tests: 914 PASS, 62 skipped
- production build: PASS
- final-character runtime-path gate: PASS
- dependency/resource/network gates: PASS
- Browser viewport smoke: PASS

## Completed React-migration stages

### R1 — framework-neutral Studio scene controller: COMPLETE

`src/viewer/studioSceneController.ts` now composes the existing project-owned runtimes for:

- static stage
- skeleton
- muscles
- equipment
- IK handles
- character
- orbit
- camera
- selection/handle transform gizmos

It subscribes directly to framework-neutral Studio/character stores and owns explicit creation, update, pointer registration and disposal.

### R2 — live scene composition switch: COMPLETE

The framework-neutral controller is the live first-party viewport scene path.

Verified consequences:

- redundant React scene composition wrappers were removed
- React scene-state/host context wrappers were removed where no longer required
- first-party browser smoke passes with the controller live
- exercise mechanics, IK, contacts, timing and rendering behavior were not changed to achieve the migration

Do not restore the removed React scene path as a production fallback.

## Framework-neutral foundations already available

### State and editor behavior

- `src/core/observableStore.ts`
- `src/editor/storeCore.ts`
- `src/editor/characterStoreCore.ts`
- `src/editor/keyboardController.ts`
- `src/editor/layoutState.ts`
- existing history/playback/comparison/diagnostic/generation logic

React hooks are temporary adapters, not the source of truth.

### Viewport/runtime

- `src/viewer/firstPartyViewportRuntime.ts`
- `src/viewer/studioSceneController.ts`
- `src/viewer/threeSceneHost.ts`
- `src/core/browserSceneSurface.ts`
- `src/viewer/sceneFrameDriver.ts`
- `src/viewer/scenePointerRouter.ts`
- `src/viewer/sceneHostTypes.ts`
- project-owned stage/scene/resource runtimes

The renderer, frame clock, clip tracking, pointer router, scene composition and disposal semantics no longer need React.

## React-owned surfaces that remain

### Remaining React child surfaces / bridge

- `src/main.tsx` — temporary ReactDOM bridge root beside the first-party shell
- `src/editor/App.tsx` — temporary portal bridge only
- `src/editor/panels/*.tsx`

### Thin viewport DOM adapter

- `src/viewer/FirstPartyViewportHost.tsx`
- `src/viewer/Viewport.tsx`

The viewport adapter now owns only React DOM/effect lifetime; all renderer and scene composition work underneath it is plain TypeScript.

## Current stage

### R3 — editor DOM shell: IN PROGRESS

The outer editor shell, Toolbar and Timeline are now live first-party DOM at `5be60985`:

- `src/editor/appShellDom.ts` owns the live Studio structure, tab buttons, panel visibility and stable child slots;
- `src/editor/toolbarDom.ts` owns the live Toolbar and subscribes directly to `studioStore`;
- `src/editor/timelineDom.ts` owns the live Timeline and subscribes directly to `studioStore`;
- `src/main.tsx` mounts the shell, Toolbar and Timeline directly under the first-party slot structure;
- `src/editor/App.tsx` is only a temporary portal bridge for the remaining React child surfaces;
- `src/editor/Toolbar.tsx` and `src/editor/Timeline.tsx` are removed after focused tests and Chromium parity passed;
- Chromium verifies live shell/Toolbar ownership and Toolbar routing for generated candidates, view modes, backdrop, camera and undo/redo;
- full suite/build/provenance/dependency/resource/network gates pass.

The initial shell preparation commit exposed a test-only strict TypeScript cast; the typecheck gate stopped that checkpoint, the cast was corrected without runtime changes, and all later shell checkpoints are green. A Toolbar smoke assertion also initially expected a camera preset to survive `loadExercise`; the established store behavior correctly resets camera to `recommended`, so the parity assertion was corrected rather than changing runtime semantics.

Next exact increment: **simple/read-mostly panels**, starting with Technique.

1. build a React-free Technique panel DOM/controller backed directly by `studioStore`;
2. preserve the current automatic 120 ms validation scheduling/cancellation behavior;
3. preserve validation status, loop/unreachable readouts, technique-rule pass/fail details and common-error guidance;
4. preserve current CSS classes and text semantics;
5. prove focused unit behavior and Chromium parity while `TechniquePanel.tsx` remains the reference;
6. switch only the Technique tab after those checks pass, then remove the redundant React wrapper;
7. continue other panels incrementally, leaving editing/generation/review/export surfaces until their lower-risk dependencies are migrated.

Use `studioStore.subscribe/getState` and `studioLayoutStore.subscribe/getState`; do not create a second state model.

### R4 — React root removal

When all live editor/viewport surfaces are first-party DOM/lifecycle code:

- replace `createRoot(...).render(<App />)`;
- remove temporary React hook adapters;
- remove React/ReactDOM source imports;
- set one-way import ceilings to zero;
- remove React/ReactDOM packages only after build/browser parity passes.

## Acceptance for every increment

- focused unit tests for extracted controller/model behavior
- typecheck
- full suite
- production build
- current standalone/provenance/network gates
- Chromium browser smoke for user-visible/lifecycle changes
- no migration-threshold weakening

## Preserve

- CSS/classes and visible editor layout unless a separate product change explicitly authorizes a redesign
- keyboard shortcuts
- timeline/playback semantics
- camera/orbit/picking/gizmo behavior
- accessibility-relevant labels/button semantics
- current exercise and biomechanical behavior

## Do not

- mix React removal with Three.js math/renderer replacement
- replace React with another third-party framework
- create a parallel state architecture
- change exercise data/mechanics to accommodate UI migration
