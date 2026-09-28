# React / ReactDOM first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Latest fully verified checkpoint:

`db473efdf819e64c88193e7d80d99a2510c49b22`

## Boundary

R3F source migration is complete. The live viewport uses the project-owned WebGL host and there are zero R3F/Drei source imports.

The current migration target is React/ReactDOM.

Do not replace React with another third-party UI framework. The target is project-owned DOM/lifecycle code backed by existing first-party stores/controllers.

## Verified checkpoint

At `db473efd`:

- Standalone prep verification: PASS
- full suite: 128 test files PASS, 2 skipped
- full tests: 931 PASS, 62 skipped
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
- remaining `src/editor/panels/*.tsx` surfaces other than Technique, Muscle, Comparison, Contact and Exercise

### Thin viewport DOM adapter

- `src/viewer/FirstPartyViewportHost.tsx`
- `src/viewer/Viewport.tsx`

The viewport adapter now owns only React DOM/effect lifetime; all renderer and scene composition work underneath it is plain TypeScript.

## Current stage

### R3 — editor DOM shell: IN PROGRESS

The outer editor shell, Toolbar, Timeline, Technique, Muscle, Comparison, Contact and Exercise panels are now live first-party DOM at `db473efd`:

- `src/editor/appShellDom.ts` owns the live Studio structure, tab buttons, panel visibility and stable child slots;
- `src/editor/toolbarDom.ts` owns the live Toolbar and subscribes directly to `studioStore`;
- `src/editor/timelineDom.ts` owns the live Timeline and subscribes directly to `studioStore`;
- `src/main.tsx` mounts the shell, Toolbar and Timeline directly under the first-party slot structure;
- `src/editor/App.tsx` is only a temporary portal bridge for the remaining React child surfaces;
- `src/editor/Toolbar.tsx` and `src/editor/Timeline.tsx` are removed after focused tests and Chromium parity passed;
- `src/editor/panels/techniquePanelDom.ts` is live only while the Technique tab is mounted;
- the Technique React wrapper is removed after focused/browser parity;
- `src/editor/panels/musclePanelDom.ts` is live only while the Muscles tab is mounted;
- the Muscle React wrapper is removed after focused/browser parity;
- Muscle local filters reset on remount and the existing `MusclePanel.css` remains owned by the first-party module;
- `src/editor/panels/comparisonPanelDom.ts` is live only while Compare is active, with explicit mount/disposal bound to `studioLayoutStore`;
- the Comparison React wrapper is removed after focused/browser parity;
- Comparison capture remains review-only and preserves both diagrams, snapshot metadata, selected-joint A/B/Δ readings and Clear behavior without changing document/history state;
- `src/editor/panels/contactPanelDom.ts` is live only while the left Contacts tab is active, with explicit mount/disposal bound to `studioLayoutStore`;
- the Contact React wrapper is removed after focused/browser parity;
- Contact diagnostics preserve the production solver inspection pipeline and route checkbox edits through the existing lock/history action;
- `src/editor/panels/exercisePanelDom.ts` is live only while the Exercise tab is active, with explicit mount/disposal bound to `studioLayoutStore`;
- the Exercise React wrapper is removed after focused/browser parity;
- Exercise tempo/grip edits continue through the existing regeneration/history actions with all metadata/readouts preserved;
- a focused mount-lifecycle guard verifies validation stays dormant while Technique is inactive;
- Chromium verifies live shell/Toolbar ownership and Toolbar routing for generated candidates, view modes, backdrop, camera and undo/redo;
- full suite/build/provenance/dependency/resource/network gates pass.

The initial shell preparation commit exposed a test-only strict TypeScript cast; the typecheck gate stopped that checkpoint, the cast was corrected without runtime changes, and all later shell checkpoints are green. A Toolbar smoke assertion also initially expected a camera preset to survive `loadExercise`; the established store behavior correctly resets camera to `recommended`, so the parity assertion was corrected rather than changing runtime semantics.

Next exact increment: **IK panel**.

1. build a React-free IK panel DOM/controller backed directly by `studioStore`;
2. preserve viewport-handle visibility, all chain active states, target/pole coordinate readouts and active handle selection state;
3. preserve `toggleIK`, `selectHandle`, `toggle('showIkHandles')` and lock edits through the existing actions; do not change IK/contact mechanics;
4. preserve lock descriptions and the no-locks empty state;
5. prove focused unit behavior and Chromium parity while `IKPanel.tsx` remains the reference;
6. switch only the IK left tab after those checks pass, mount only while `leftTab === 'ik'`, then remove the redundant React wrapper;
7. continue Joint/Grip/Equipment/Character and remaining right-side editing panels incrementally, leaving generation/review/export until lower-risk surfaces are complete.

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
