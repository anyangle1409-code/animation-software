# React / ReactDOM first-party migration — current handoff

Branch: `work/standalone-first-party-audit-20260927`

Latest fully verified checkpoint:

`31855e2eb349aa9bb55d43ca409528baacd07bd0`

## Boundary

R3F source migration is complete. The live viewport uses the project-owned WebGL host and there are zero R3F/Drei source imports.

The current migration target is React/ReactDOM.

Do not replace React with another third-party UI framework. The target is project-owned DOM/lifecycle code backed by existing first-party stores/controllers.

## Verified checkpoint

At `31855e2`:

- Standalone prep verification: PASS
- full suite: 148 test files PASS, 2 skipped
- full tests: 968 PASS, 62 skipped
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

### Remaining React compatibility layer

- temporary React store-hook adapters in `src/core/store.ts`, `src/editor/store.ts`, `src/editor/characterStore.ts` and `src/editor/generationStore.ts`
- `src/editor/App.tsx` is an unused reference removed in the current cleanup checkpoint

No React-owned root, editor, keyboard, layout or viewport surface remains on the live path.

## Current stage

### R3 — editor DOM shell: COMPLETE ON THE LIVE PATH

The outer editor shell, Toolbar, Timeline, Technique, Muscle, Comparison, Contact, Exercise, IK and Equipment panels are now live first-party DOM at `ea3b36d`:

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
- `src/editor/panels/ikPanelDom.ts` is live only while IK & locks is active, with explicit mount/disposal bound to `studioLayoutStore`;
- the IK React wrapper is removed after focused/browser parity;
- IK chain toggles, target/pole selection, viewport-handle visibility and lock edits continue through the existing store/history actions;
- `src/editor/panels/equipmentPanelDom.ts` is live only while Equipment is active, with explicit mount/disposal;
- Equipment selection, attachment wording, static object/socket editors and Reset socket preserve existing store/history actions and cm/degree formatting;
- the Equipment React reference is removed only after both required workflows passed at `ea3b36d`;
- Character, Joint and Grip left panels are also live first-party DOM with verified actions, selection, diagnostics and disposal; their React references are removed after each live checkpoint passed both workflows;
- `src/editor/generationStoreCore.ts` now owns Generate session state independently of React;
- `src/editor/panels/generatePanelDom.ts` is live only while Generate is active, preserving prompt/examples, progress, candidate details, Preview/Approve/Discard and session switching;
- the live Generate switch passed both workflows at `79d37eb`; its redundant React wrapper cleanup passed at `deb5767`;
- `src/editor/panels/reviewPanelDom.ts` is live only while Review is active, preserving automated gates, movement diagnostics/locators and exact visual sign-off invalidation semantics;
- the live Review switch passed both workflows at `8abf619`; its redundant React wrapper cleanup passed at `aaf0163`;
- `src/editor/panels/exportPanelDom.ts` is live only while Export is active, preserving mount-local fps/equipment options, all four export actions, exact filenames/options and status semantics;
- the live Export switch passed both workflows at `5656ca6`; its redundant React wrapper cleanup passed at `3f8cd80`;
- `src/viewer/firstPartyViewportDom.ts` owns the live viewport host/canvas lifecycle and wires the existing first-party runtime/controller directly;
- detached viewport DOM/WebGL parity passed at `67c227a`, and the live viewport switch passed both workflows at `c5558dd`;
- the obsolete `FirstPartyViewportHost.tsx` / `Viewport.tsx` cleanup passed both workflows at `889b0e7`;
- `src/main.tsx` now mounts the first-party shell directly, owns keyboard binding/disposal and contains no React/ReactDOM imports;
- Chromium verifies no React bridge remains and keyboard frame stepping still routes correctly;
- the rootless live startup switch passed both workflows at `31855e2`;
- `src/editor/App.tsx` is removed in the current cleanup checkpoint as the final unused React component reference;
- a focused mount-lifecycle guard verifies validation stays dormant while Technique is inactive;
- Chromium verifies live shell/Toolbar ownership and Toolbar routing for generated candidates, view modes, backdrop, camera and undo/redo;
- full suite/build/provenance/dependency/resource/network gates pass.

The initial shell preparation commit exposed a test-only strict TypeScript cast; the typecheck gate stopped that checkpoint, the cast was corrected without runtime changes, and all later shell checkpoints are green. A Toolbar smoke assertion also initially expected a camera preset to survive `loadExercise`; the established store behavior correctly resets camera to `recommended`, so the parity assertion was corrected rather than changing runtime semantics. The IK preparation also exposed two test-harness assumptions: the shell tab is labelled `IK & locks`, and a smoke probe cannot assume an IK chain starts enabled. Both assertions were corrected to follow established runtime state; IK mechanics were not changed.

Next exact increment: **temporary React store-adapter removal**.

1. verify the current `App.tsx` cleanup checkpoint in both required workflows;
2. rewrite adapter-dependent tests to exercise `createStore` / `studioStore` / `characterStore` directly, preserving behavioral coverage;
3. remove `src/core/store.ts`, `src/editor/store.ts`, `src/editor/characterStore.ts` and `src/editor/generationStore.ts` only after no source/test callers remain;
4. replace any focused-workflow reference to the React adapter test with framework-neutral observable-store coverage;
5. require full typecheck, suite, build, standalone guards and Chromium after adapter deletion;
6. only after direct React/ReactDOM source imports reach zero, pin their migration ceilings to zero and assess package removal without disturbing the separate R3F/Drei physical-device gate.

The rootless live startup checkpoint `31855e2` passed both workflows with 148 test files / 968 tests passed. React no longer participates in the live application lifecycle.

Direct R3F/Drei source imports remain zero. Direct React/ReactDOM source import statements after this `App.tsx` cleanup are 1 (`src/core/store.ts`). Five runtime packages remain declared: `@react-three/drei`, `@react-three/fiber`, `react`, `react-dom`, `three`.

Use `studioStore.subscribe/getState` and `studioLayoutStore.subscribe/getState`; do not create a second state model.

### R4 — React root removal: COMPLETE ON THE LIVE PATH

`src/main.tsx` now mounts the first-party shell directly and owns keyboard binding/disposal. The temporary ReactDOM root, StrictMode wrapper and React bridge are gone. Remaining work is compatibility-adapter cleanup followed by zero-import/package gates.

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
