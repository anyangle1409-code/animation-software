# React / ReactDOM first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Latest fully verified checkpoint:

`0b9bb62a809ee4af7f7bf35fc4f8ae5b5c936714`

## Boundary

R3F source migration is complete. The live viewport uses the project-owned WebGL host and there are zero R3F/Drei source imports.

The current migration target is React/ReactDOM.

Do not replace React with another third-party UI framework. The target is project-owned DOM/lifecycle code backed by existing first-party stores/controllers.

## Verified checkpoint

At `0b9bb62a`:

- Standalone prep verification: PASS
- full suite: 116 test files PASS, 2 skipped
- full tests: 910 PASS, 62 skipped
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
- `src/editor/Toolbar.tsx`
- `src/editor/Timeline.tsx`
- `src/editor/panels/*.tsx`

### Thin viewport DOM adapter

- `src/viewer/FirstPartyViewportHost.tsx`
- `src/viewer/Viewport.tsx`

The viewport adapter now owns only React DOM/effect lifetime; all renderer and scene composition work underneath it is plain TypeScript.

## Current stage

### R3 — editor DOM shell: IN PROGRESS

The outer editor shell is now live first-party DOM at `0b9bb62a`:

- `src/editor/appShellDom.ts` owns the live Studio structure, tab buttons, panel visibility and stable child slots;
- `src/main.tsx` mounts the shell directly under `#root`;
- `src/editor/App.tsx` no longer renders the shell markup and is only a temporary portal bridge for React child surfaces;
- the viewport has a dedicated first-party slot so the panel-toggle overlay and child viewport layout stay independent;
- the temporary React bridge is a sibling of the shell, not its owner;
- focused shell tests pass;
- Chromium verifies live shell ownership, five-slot contract, viewport layout boundary, tab/focus behavior and the empty portal bridge container;
- full suite/build/provenance/dependency/resource/network gates pass.

The initial shell preparation commit exposed a test-only strict TypeScript cast; the typecheck gate stopped that checkpoint, the cast was corrected without runtime changes, and all later shell checkpoints are green.

Next exact increment: **toolbar/playback controls**.

1. build a React-free Toolbar DOM/controller backed directly by `studioStore`;
2. preserve the existing brand, Exercise selector including generated-candidate behavior, view modes, Backdrop, Camera, Regenerate, Undo and Redo;
3. preserve current CSS classes, roles, labels, disabled states and selector semantics;
4. prove it with focused tests and browser parity while the React Toolbar remains the reference;
5. switch the live toolbar slot only after those checks pass;
6. then continue with timeline, simple panels, editing panels/forms and generation/review/export workflows.

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
