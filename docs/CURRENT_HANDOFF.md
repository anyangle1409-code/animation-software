# Current handoff

## Start here

Single operational entry point for the Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation checkpoint:

`431a20e4fcb7f470951f1a4be618fd23ded8bb71`

Do not reconstruct state from historical branches, old chats, removed reports or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md` and `docs/DECISION_LOG.md`, then continue only the exact task below.

## Verified state at 431a20e

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

## React / ReactDOM status — source migration complete

Verified at `431a20e4fcb7f470951f1a4be618fd23ded8bb71`:

- direct `react` source imports: **0**
- direct `react-dom` source imports: **0**
- direct R3F/Drei source imports remain **0**
- React/ReactDOM source-import ceilings are pinned to zero
- all editor surfaces are project-owned DOM/controllers with explicit lifecycle/disposal
- the viewport host/canvas lifecycle is project-owned by `src/viewer/firstPartyViewportDom.ts`
- `#root`, keyboard binding and startup are plain TypeScript
- temporary React store-hook adapters are removed
- the browser smoke harness uses `storeCore` directly
- no production `.tsx` source remains; startup is `src/main.ts`
- Vite no longer loads the React plugin

The declared `react` / `react-dom` packages are **not live application dependencies**. They remain temporarily declared with the retained `@react-three/fiber` / `@react-three/drei` package ecosystem while the separate physical desktop/iPhone Drei gate remains open. Do not reintroduce React source imports.

## Cloud/software track — next exact task

React/ReactDOM source migration is complete. Continue with the first deterministic Three.js-replacement layer using:

- `docs/FIRST_PARTY_MATH_PARITY_PLAN.md`
- `docs/FIRST_PARTY_POSE_MIGRATION.md`

Current objective: **S5 first-party mathematics / pose integration**.

Next exact increment:

1. switch the pivot-aware production calculation in `src/rig/pose.ts` from Three `Vector3/Quaternion/Euler` to the already parity-tested `HgVec3/HgQuat`;
2. preserve the existing public `blendPoses` semantics and all authored exercise data;
3. keep Three only as test/development comparison evidence while the migration proceeds;
4. run focused math/pose parity, full suite, build, provenance/dependency/resource/network gates and Chromium;
5. after that is green, continue into the prepared first-party skeleton parity path before IK orientation;
6. do **not** combine this with canonical-v4 ORIGINAL rest-geometry changes;
7. keep renderer/GLB package removal for later layers; Three remains the last direct runtime replacement.

Package note: do not remove `react` solely to lower the dependency count while retained R3F/Drei still declare it as a peer and their physical-device package gate is open. Package retirement follows peer/install consistency and the physical parity handoff.

The React migration completion record is now supporting reference in `docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md`.

## Remaining declared runtime dependencies

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is removed.

Source use of R3F/Drei and React/ReactDOM is zero. React packages are temporarily retained for the still-gated R3F/Drei peer ecosystem; Three.js is now the active software migration and remains the last direct runtime replacement.

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
