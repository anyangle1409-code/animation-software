# Current handoff

## Start here

Single operational entry point for the Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation checkpoint:

`31855e2eb349aa9bb55d43ca409528baacd07bd0`

Do not reconstruct state from historical branches, old chats, removed reports or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md` and `docs/DECISION_LOG.md`, then continue only the exact task below.

## Verified state at 31855e2

GitHub `Standalone prep verification` passed completely:

- TypeScript typecheck: PASS
- Blender helper Python syntax: PASS
- repository authority / hygiene gate: PASS
- focused first-party foundation suite: PASS
- full suite: 148 test files PASS, 2 skipped
- full tests: 968 PASS, 62 skipped
- production build: PASS
- final-character runtime-path gate: PASS
- runtime dependency anti-creep gate: PASS
- external runtime resource gate: PASS
- runtime network/API gate: PASS

The separate real-browser `Browser viewport smoke` workflow also passed on the same commit.

## Preserved recovery state

- branch: `archive/pre-makehuman-removal-20260928`
- commit: `502adedc9fd5c7ddbee1b74cd0472879de6fb047`

Recovery/audit history only. Do not develop from it or copy legacy/derived production content back into the active branch.

## Character / provenance state

Removed from the active production path:

- hard-wired V8 bundled-character startup
- old mesh/review bundles
- MakeHuman-derived anatomical source/data lineage
- old anatomical generator/corrective stack
- legacy solved-grip default/fallback data
- legacy-only retarget asset paths/fixtures

Active temporary fallback:

- `src/body/profileMesh.ts`
- `src/character/procedural.ts`

Production target remains independently authored **ORIGINAL v1**.

## R3F status — source migration complete

The live viewport is first-party:

- `src/viewer/R3FViewportHost.tsx` is removed
- direct `@react-three/fiber` source imports: **0**
- direct `@react-three/drei` source imports: **0**
- the migration allowlist pins both ceilings at zero
- the rollback path has been removed
- browser smoke passes on the first-party viewport
- the project-owned WebGL host drives real exercise frames through `driveSceneFrame`

The packages remain declared temporarily because Drei's separate physical desktop/iPhone gate is still open and the packages share the same peer ecosystem. Do not reintroduce source imports.

## React / ReactDOM status — current software target

React/ReactDOM migration has advanced beyond scene composition.

Completed and verified:

- `src/core/observableStore.ts`: framework-neutral state primitive
- `studioStore` / `characterStore`: framework-neutral state instances
- keyboard and layout semantics are framework-neutral
- `firstPartyViewportRuntime.ts`: framework-neutral canvas/WebGL/frame/pointer lifecycle
- `studioSceneController.ts`: framework-neutral complete Studio scene composition
- live `src/viewer/firstPartyViewportDom.ts` uses that controller
- stage, skeleton, muscle, equipment, IK, character, orbit, camera and gizmo lifecycles are owned by plain TypeScript runtimes
- redundant React scene composition/context wrappers have been removed

React no longer owns startup, layout, keyboard lifetime, editor DOM or the viewport. Remaining compatibility code is limited to temporary React store-hook adapters and this now-unused `src/editor/App.tsx` reference, which is removed in the current cleanup checkpoint.

## Cloud/software track — next exact task

Continue from:

`docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md`

R1 (framework-neutral Studio scene controller) and R2 (switch live scene composition/remove redundant React scene wrappers) are complete.

Current objective: **remove the remaining temporary React store-hook adapters after the verified rootless startup switch**.

Verified live shell state:

- `src/editor/appShellDom.ts` owns the live Studio outer structure, left/right tabs, panel slots and panel visibility;
- `src/editor/toolbarDom.ts` owns the live Toolbar DOM/controller directly from `studioStore`;
- `src/editor/timelineDom.ts` owns the live Timeline DOM/controller directly from `studioStore`;
- `src/main.tsx` mounts the first-party shell, Toolbar and Timeline directly;
- `src/editor/Toolbar.tsx` and `src/editor/Timeline.tsx` are removed;
- `src/editor/panels/techniquePanelDom.ts` owns the live Technique panel only while that tab is active;
- Technique validation preserves the original 120 ms mount/clip-change debounce and does not run while the tab is inactive;
- `src/editor/panels/TechniquePanel.tsx` is removed;
- `src/editor/panels/musclePanelDom.ts` owns the live Muscle diagnostics panel only while that tab is active;
- Muscle diagnostics preserve the finished-frame biomechanics pipeline, activation ordering, labels/readings, CSS and local filter reset-on-remount behavior;
- `src/editor/panels/MusclePanel.tsx` is removed;
- `src/editor/panels/comparisonPanelDom.ts` owns the live Pose A/B comparison panel only while Compare is active;
- Comparison preserves review-only Capture A / Capture B / Clear behavior, both pose diagrams, snapshot metadata and selected-joint A/B/Δ readouts without editing clip/history state;
- `src/editor/panels/ComparisonPanel.tsx` is removed;
- `src/editor/panels/contactPanelDom.ts` owns the live Contacts diagnostics only while the left Contacts tab is active;
- Contact diagnostics preserve the production `contactDiagnostics(...)` pipeline, status/metric readouts and existing `setLockEnabled` edit/history behavior;
- `src/editor/panels/ContactPanel.tsx` is removed;
- `src/editor/panels/exercisePanelDom.ts` owns the live Exercise editor only while the right Exercise tab is active;
- Exercise preserves metadata, tempo, muscles, breathing, grip/stance and equipment presentation plus existing `setTempo` / `setGripClosure` regeneration/history behavior;
- `src/editor/panels/ExercisePanel.tsx` is removed;
- `src/editor/panels/ikPanelDom.ts` owns the live IK & locks editor only while the left IK tab is active;
- IK preserves viewport-handle visibility, all chain enabled states, target/pole readouts and selection, lock descriptions and existing `toggleIK` / `selectHandle` / `toggle('showIkHandles')` / `setLockEnabled` behavior;
- `src/editor/panels/IKPanel.tsx` is removed;
- `src/editor/panels/equipmentPanelDom.ts` owns the live Equipment editor only while the left Equipment tab is active;
- Equipment preserves selection, static object/socket transforms, reset, attachment wording, centimetre/degree formatting and existing store/history actions;
- the redundant `src/editor/panels/EquipmentPanel.tsx` is removed after both required workflows passed at `ea3b36d`;
- `src/editor/panels/characterPanelDom.ts` owns the live Character import/source/bind/mapping panel only while its left tab is active;
- Character preserves existing characterStore actions, import/view switching, report display and mapping controls;
- `src/editor/panels/CharacterPanel.tsx` is removed after both workflows passed at `954cc99`;
- `src/editor/panels/jointPanelDom.ts` owns the live Joint editor only while its left tab is active, with explicit disposal;
- Joint preserves limit-aware axis controls, selected bone/finger visibility, motion/coordination diagnostics, segment timing and pose actions;
- `src/editor/panels/JointPanel.tsx` is removed after both workflows passed at `0318a5f`;
- `src/editor/panels/gripPanelDom.ts` owns the live Grip panel only while its left tab is active; its DOM controls preserve grip closure, digit closure, one-hand offset, two-hand fit diagnostics and width plus history actions;
- `src/editor/panels/GripPanel.tsx` is removed after both required workflows passed at `c7bc112`;
- `src/editor/panels/correctivePanelDom.ts` owns Correctives only while its right tab is active, including preview tuning, live strain, whole-rep scans and morph diagnostics;
- `src/editor/panels/CorrectivePanel.tsx` is removed after both required workflows passed at `58915f8`;
- `src/editor/generationStoreCore.ts` owns the framework-neutral Generate session state, with the React hook retained only as a temporary compatibility adapter;
- `src/editor/panels/generatePanelDom.ts` owns the live Generate surface only while the right Generate tab is active;
- Generate preserves prompt/examples, async progress, candidate review details, Preview → Studio routing, passed-only approval, discard and session switching;
- `src/editor/panels/GeneratePanel.tsx` is removed after its cleanup checkpoint passed both required workflows at `deb5767`;
- `src/editor/panels/reviewPanelDom.ts` owns the live Review surface only while the right Review tab is active;
- Review preserves automated gates, movement diagnostics and locator actions plus exact document/character/deformation visual sign-off identity and the production-correctives requirement;
- `src/editor/panels/ReviewPanel.tsx` cleanup passed both required workflows at `aaf0163`;
- `src/editor/panels/exportPanelDom.ts` owns the live Export surface only while the right Export tab is active;
- Export preserves mount-local 24/30/60 fps selection, include-equipment state, all four existing export actions, exact filenames/options and busy/done/error status semantics, with defaults reset on remount;
- `src/editor/panels/ExportPanel.tsx` cleanup passed both required workflows at `3f8cd80`;
- all editor child panels are live first-party DOM;
- `src/viewer/firstPartyViewportDom.ts` now owns the live viewport host/canvas lifecycle in the viewport slot;
- the live viewport switch passed both required workflows at `c5558dd`, including real Chromium/WebGL frame/render/scene assertions;
- `src/viewer/FirstPartyViewportHost.tsx` and `src/viewer/Viewport.tsx` are removed in the current cleanup checkpoint as redundant references;
- React renders no visible surface and no longer owns `#root`, keyboard binding or layout state;
- `src/main.tsx` mounts only the first-party shell and binds keyboard shortcuts directly with an explicit disposer;
- Chromium verifies the React bridge is absent and ArrowRight still pauses/advances exactly one frame;
- `src/editor/App.tsx` is removed in the current cleanup checkpoint as an unused reference;
- focused unit coverage verifies shell and Toolbar state sync, routing and disposal;
- Chromium verifies the live first-party shell and Toolbar, including exercise/candidate selection, view modes, camera/backdrop routing and undo/redo behavior.

Next exact increment:

1. verify this unused `App.tsx` cleanup in both required workflows;
2. migrate adapter-dependent tests/callers from `src/core/store.ts`, `src/editor/store.ts`, `src/editor/characterStore.ts` and `src/editor/generationStore.ts` to `observableStore` / `storeCore` / `characterStoreCore` / `generationStoreCore`;
3. preserve the existing Studio and character behavior tests rather than deleting coverage just because the React hook adapters are going away;
4. remove the temporary adapter files only when TypeScript confirms no callers remain;
5. update the runtime dependency source-import ceilings to zero only after direct `react` / `react-dom` source imports are actually zero;
6. then evaluate removal of direct React/ReactDOM packages against npm install consistency and the still-open R3F/Drei physical-device package gate;
7. keep R3F/Drei source imports at zero and replace Three.js last.

Viewport reference cleanup passed both workflows at `889b0e7`. The rootless live startup switch passed both at `31855e2` with 148 test files and 968 tests passed (2 files and 62 tests skipped); Browser smoke verifies `#root` owns only the first-party shell, no React bridge exists, the live WebGL viewport remains active, and direct keyboard stepping still preserves one-frame/pause semantics. This checkpoint removes only the unused `App.tsx` reference.

The left-side panels are all live first-party DOM. Correctives preparation passed both workflows at `cf95586` (139 files and 952 tests passed; 2 files and 62 tests skipped). The live switch passed both workflows at `58915f8` (140 files and 953 tests passed; 2 files and 62 tests skipped). It mounts `correctivePanelDom.ts` only on its right tab, removes React portal rendering, and checks active-character strain, full-rep scan, preview routing and disposal in Chromium. The redundant reference cleanup is pending its own workflows. Grip preparation passed both workflows at `208b7bf` (137 files and 948 tests passed, 2 files and 62 tests skipped). The live Grip switch passed both at `c7bc112` (138 files and 949 tests passed, 2 files and 62 tests skipped). Chromium covered sole ownership, closure and digit edits, one-hand offset, two-hand fit/width and tab disposal. The preparation parity compared curl and pull-up states; the live two-hand probe uses cable pushdown, which has a two-hand attachment.

Current direct `react`/`react-dom` source import statements after this `App.tsx` cleanup: 1 (`src/core/store.ts`); direct R3F/Drei source imports: 0. The declared runtime dependencies remain the five listed below.

The Equipment reference removal passed both workflows at `3bc0d87`. Character preparation, live switch and cleanup passed at `55592fb`, `954cc99` and `162b08d`. Joint preparation, live switch and cleanup passed at `5866c57`, `0318a5f` and `3f2766d`. Grip reference cleanup passed both workflows at `fc7f365` (138 files and 949 tests passed; 2 files and 62 tests skipped).

## Remaining declared runtime dependencies

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is removed.

Source use of R3F/Drei is zero; React/ReactDOM is the active source migration; Three stays last.

## Physical browser/device gate

Use `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.

Physical desktop/iPhone touch/Transform evidence remains required before Drei removal. Automated Chromium is supplementary evidence, not a substitute for this physical gate.

## Laptop / Blender track

Use `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`.

```bat
STANDALONE_STATUS.bat
PREPARE_ORIGINAL_V1_O2.bat
```

Continue only the independent ORIGINAL v1 / canonical-v4 path.

## Do not

- reopen V15f development
- restore removed legacy/MakeHuman/V8 paths
- promote the procedural fallback as final anatomy
- restore R3F/Drei source imports
- replace React with another third-party UI framework
- alter exercise mechanics to simplify UI/runtime migration
- remove dependencies before their stated parity gates
- weaken tests, provenance rules, ceilings or release gates
