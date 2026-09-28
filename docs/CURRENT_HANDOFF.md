# Current handoff

## Start here

Single operational entry point for the Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation checkpoint:

`a78dcedbe363523805425f3d92e6d82ae133b38f`

Do not reconstruct state from historical branches, old chats, removed reports, or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md`, and `docs/DECISION_LOG.md`, then continue only the exact task below.

## Verified state at a78dcedb

GitHub `Standalone prep verification` passed completely:

- TypeScript typecheck: PASS
- Blender helper Python syntax: PASS
- repository authority / hygiene gate: PASS
- focused first-party foundation suite: PASS
- full suite: 101 test files PASS, 2 skipped
- full tests: 887 PASS, 62 skipped
- production build: PASS
- final-character runtime-path gate: PASS
- runtime dependency anti-creep gate: PASS
- external runtime resource gate: PASS
- runtime network/API gate: PASS

The separate real-browser `Browser viewport smoke` workflow also passed.

## Preserved recovery state

- branch: `archive/pre-makehuman-removal-20260928`
- commit: `502adedc9fd5c7ddbee1b74cd0472879de6fb047`

Recovery/audit history only.

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

## Remaining runtime dependencies

Five direct runtime dependencies remain declared:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is removed.

Drei has zero source imports but remains installed until the explicit physical desktop/iPhone Grid/Orbit/Transform gate passes.

## Current R3F boundary

Direct R3F imports are isolated to exactly:

`src/viewer/R3FViewportHost.tsx`

Already project-owned / R3F-neutral:

- scene frame driver
- static Studio stage
- camera rig controller
- scene host bindings
- scene object mounting
- scene pointer router with raycast/bubbling/capture
- CharacterFigure scene ownership
- MuscleView scene ownership
- SkeletonView scene ownership/picking
- EquipmentView scene ownership/picking
- IKHandles scene ownership/picking
- transform-gizmo scene geometry/pointer handling
- orbit model/input
- real-WebGL first-party host probe running real exercise frames

R3F still owns only:

- `Canvas` renderer lifecycle
- one `useFrame` outer clock adapter
- one `useThree` binding adapter
- React composition around those adapters
- `onPointerMissed` fallback around the first-party pointer router

## Browser evidence

Automated Chromium covers the live viewport for:

- WebGL/drawing buffer
- camera presets
- orbit/wheel zoom
- stage/backdrop
- skeleton playback
- character/muscle/equipment/IK visuals
- transform gizmo selection/rendering
- responsive resize
- no critical page/console/request errors

The isolated project-owned `ThreeSceneHost` also runs real WebGL, the first-party stage, and real bicep-curl exercise frames through `driveSceneFrame`.

Physical/iPhone touch acceptance remains separate.

## Cloud/software track — next exact task

Continue from `docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`.

Build a **reversible first-party Studio viewport host** while keeping R3F as the default reference path.

Requirements:

1. reuse the same `SceneState`, scene host bindings, visual components, pointer router, orbit controls, camera rig and transform gizmo;
2. create canvas/renderer/lifecycle through `ThreeSceneHost` + `browserSceneSurface`;
3. drive frames through `driveSceneFrame`;
4. expose a deliberate test/dev switch such as `?sceneHost=first-party` while R3F remains default;
5. run the same Chromium evidence set against the first-party path;
6. do not remove R3F until parity passes.

After R3F removal:

1. React/ReactDOM replacement
2. Three.js replacement last

## Physical browser/device gate

Use `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.

Physical desktop/iPhone touch/Transform evidence is still required before Drei removal.

## Laptop / Blender track

Use `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`.

```bat
STANDALONE_STATUS.bat
PREPARE_ORIGINAL_V1_O2.bat
```

Do not use legacy/reference geometry as production input.

## Do not

- reopen V15f development
- restore removed legacy/MakeHuman/V8 paths
- promote procedural fallback as final anatomy
- spread R3F imports beyond `R3FViewportHost.tsx`
- remove dependencies before their parity gates
- weaken tests, provenance rules, ceilings or release gates
