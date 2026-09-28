# Current handoff

## Start here

Single operational entry point for the Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation checkpoint:

`6b3532539c4b44137196fe595b1861e1bc149c55`

Do not reconstruct state from historical branches, old chats, removed reports or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md` and `docs/DECISION_LOG.md`, then continue only the exact task below.

## Verified state at 6b353253

GitHub `Standalone prep verification` passed completely:

- TypeScript typecheck: PASS
- Blender helper Python syntax: PASS
- repository authority / hygiene gate: PASS
- focused first-party foundation suite: PASS
- full suite: 122 test files PASS, 2 skipped
- full tests: 921 PASS, 62 skipped
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
- live `FirstPartyViewportHost` uses that controller
- stage, skeleton, muscle, equipment, IK, character, orbit, camera and gizmo lifecycles are owned by plain TypeScript runtimes
- redundant React scene composition/context wrappers have been removed

React remains in:

- `src/main.tsx` / temporary ReactDOM child-surface bridge root
- `src/editor/App.tsx` portal bridge and editor panels
- `src/viewer/FirstPartyViewportHost.tsx` and `src/viewer/Viewport.tsx` as thin DOM/lifecycle adapters
- temporary React store hooks/adapters

## Cloud/software track — next exact task

Continue from:

`docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md`

R1 (framework-neutral Studio scene controller) and R2 (switch live scene composition/remove redundant React scene wrappers) are complete.

Current objective: **R3 editor DOM shell**.

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
- remaining panel content and Viewport still retain their existing React behavior inside first-party slots;
- the viewport child slot has an explicit `studio__viewport-slot` layout boundary;
- focused unit coverage verifies shell and Toolbar state sync, routing and disposal;
- Chromium verifies the live first-party shell and Toolbar, including exercise/candidate selection, view modes, camera/backdrop routing and undo/redo behavior.

Next exact increment:

1. migrate `src/editor/panels/ComparisonPanel.tsx` to project-owned DOM/lifecycle code;
2. preserve review-only Capture A / Capture B / Clear behavior without changing clip or undo history;
3. preserve both pose diagrams, snapshot time/marker labels, selected-joint A/B angle deltas and empty-state wording;
4. preserve the local mount lifecycle so no hidden comparison surface remains subscribed while another tab is active;
5. keep the React Comparison panel as the parity reference until focused tests and Chromium parity pass;
6. switch only the Compare tab after those checks pass, then remove the redundant React wrapper;
7. continue Contact/Exercise and other editing panels incrementally, leaving generation/review/export until lower-risk surfaces are complete;
8. migrate the thin viewport DOM adapter after editor child surfaces no longer need React;
9. replace the remaining ReactDOM child-surface bridge only after editor + viewport parity;
10. remove React/ReactDOM source imports and packages only after final browser/build gates;
11. replace Three.js last.

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
