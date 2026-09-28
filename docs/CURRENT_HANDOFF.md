# Current handoff

## Start here

Single operational entry point for the Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation checkpoint:

`6294907d3bd48a775e6250584b5420537a43a89b`

Do not reconstruct state from historical branches, old chats, removed reports or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md` and `docs/DECISION_LOG.md`, then continue only the exact task below.

## Verified state at 6294907d

GitHub `Standalone prep verification` passed completely:

- TypeScript typecheck: PASS
- Blender helper Python syntax: PASS
- repository authority / hygiene gate: PASS
- focused first-party foundation suite: PASS
- full suite: 105 test files PASS, 2 skipped
- full tests: 898 PASS, 62 skipped
- production build: PASS
- final-character runtime-path gate: PASS
- runtime dependency anti-creep gate: PASS
- external runtime resource gate: PASS
- runtime network/API gate: PASS

The separate real-browser `Browser viewport smoke` workflow also passed.

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

The live viewport is now first-party:

- `src/viewer/Viewport.tsx` mounts only `FirstPartyViewportHost`
- `src/viewer/R3FViewportHost.tsx` is removed
- direct `@react-three/fiber` source imports: **0**
- direct `@react-three/drei` source imports: **0**
- the migration allowlist pins both ceilings at zero
- the rollback path has been removed
- browser smoke passes on the first-party viewport
- the project-owned WebGL host drives real exercise frames through `driveSceneFrame`

The packages remain declared temporarily because Drei's separate physical desktop/iPhone gate is still open and the packages share the same peer ecosystem. Do not reintroduce source imports.

## React / ReactDOM status — current software target

React still renders the editor and scene-content adapters, but core state/runtime ownership is already moving out:

Completed and verified:

- `src/core/observableStore.ts`: framework-neutral state primitive
- `studioStore`: framework-neutral Studio state instance
- `useStudio`: temporary React adapter only
- `keyboardController.ts`: framework-neutral shortcut semantics
- `layoutState.ts`: framework-neutral editor tab/panel state
- `firstPartyViewportRuntime.ts`: framework-neutral canvas/WebGL/frame/pointer lifecycle
- `sceneHostTypes.ts`: host bindings type no longer owned by a React context file
- first-party viewport lifecycle no longer depends on R3F

React remains in:

- `src/main.tsx` / ReactDOM root
- `App.tsx`, Toolbar, Timeline and editor panels
- temporary scene-state and scene-host context adapters
- `StudioSceneContent.tsx` and thin visual lifecycle wrappers
- asynchronous character-build/view lifecycle wrappers
- temporary React store hooks

## Cloud/software track — next exact task

Continue from:

`docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md`

Next objective: build a **framework-neutral Studio scene controller** while preserving the current React scene as the verified reference.

Use the project-owned modules already present; do not rewrite rendering logic.

Priority:

1. compose the existing stage, skeleton, muscle, equipment, IK-handle and transform-gizmo scene modules under one plain TypeScript controller;
2. subscribe directly to `studioStore` / character state and the scene frame dispatcher;
3. own create/update/pointer-registration/disposal explicitly;
4. keep `StudioSceneContent.tsx` as the reference adapter until browser parity passes;
5. then make the controller the live scene path and remove the redundant React scene wrappers;
6. migrate editor chrome/panels to project-owned DOM bindings;
7. replace `src/main.tsx` ReactDOM root only after editor + viewport parity;
8. remove React/ReactDOM;
9. replace Three.js last.

## Remaining declared runtime dependencies

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is removed.

Source use of R3F/Drei is already zero; React/ReactDOM is the active source migration; Three stays last.

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
