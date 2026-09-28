# React / ReactDOM first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Latest fully verified checkpoint:

`1110bb611b73612293a60762fccfdf0c82bc3db4`

## Boundary

R3F source migration is complete. The live viewport uses the project-owned WebGL host and there are zero R3F/Drei source imports.

The current migration target is React/ReactDOM.

Do not replace React with another third-party UI framework. The target is project-owned DOM/lifecycle code backed by existing first-party stores/controllers.

## Verified checkpoint

At `1110bb61`:

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

### Root/editor chrome

- `src/main.tsx`
- `src/editor/App.tsx`
- `src/editor/Toolbar.tsx`
- `src/editor/Timeline.tsx`
- `src/editor/panels/*.tsx`

### Thin viewport DOM adapter

- `src/viewer/FirstPartyViewportHost.tsx`
- `src/viewer/Viewport.tsx`

The viewport adapter now owns only React DOM/effect lifetime; all renderer and scene composition work underneath it is plain TypeScript.

## Current stage

### R3 — editor DOM shell: IN PROGRESS

First preparation increment is verified at `1110bb61`:

- `src/editor/appShellDom.ts` is a React-free Studio shell DOM/controller;
- it owns current shell classes, left/right tab buttons, panel slots and Hide/Show panels behavior;
- it reads/subscribes directly to `studioLayoutStore`;
- focused tests verify state sync, click routing and explicit disposal;
- the browser smoke now baselines the current live React shell's Equipment/Review tab activation and focus-mode toggle semantics;
- the first-party shell is not live yet.

The initial preparation commit exposed a test-only strict TypeScript cast; the typecheck gate stopped the checkpoint, the cast was corrected without runtime changes, and the complete standalone/browser gates then passed.

Next exact increment:

1. mount the project-owned shell as the live outer editor structure through a reversible temporary bridge;
2. keep the existing Toolbar, active React panel, Viewport and Timeline surfaces intact inside the shell's slots;
3. keep keyboard binding exactly once;
4. preserve current classes, labels, selectors, responsive behavior and state semantics;
5. run focused tests, typecheck, full suite/build/gates and Chromium;
6. only after parity, remove the superseded React outer-shell markup.

Then continue in parity-gated groups:

1. toolbar/playback controls
2. timeline
3. simple read-only panels
4. editing panels/forms
5. generation/review/export workflows

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
