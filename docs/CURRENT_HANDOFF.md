# Current handoff

## Start here

This is the **single operational entry point** for the current Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation checkpoint:

`3970ae603249d225d6a513d539dc496683036fcd`

Do not reconstruct state from historical branches, old chats, removed reports, or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md`, and `docs/DECISION_LOG.md`, then continue only the exact task below.

## Verified state at 3970ae60

GitHub `Standalone prep verification` passed completely:

- TypeScript typecheck: PASS
- Blender helper Python syntax: PASS
- repository authority / hygiene gate: PASS
- focused first-party foundation suite: 84 / 84 PASS
- full suite: 92 test files PASS, 2 skipped
- full tests: 856 PASS, 62 skipped
- production build: PASS
- final-character runtime-path gate: PASS
- runtime dependency anti-creep gate: PASS
- external runtime resource gate: PASS
- runtime network/API gate: PASS

The separate real-browser `Browser viewport smoke` workflow also passed at this checkpoint.

## Preserved recovery state

Before removing the derived anatomical character lineage, the exact working state was frozen as:

- branch: `archive/pre-makehuman-removal-20260928`
- commit: `502adedc9fd5c7ddbee1b74cd0472879de6fb047`

That branch is recovery/audit history only. Do not develop from it and do not copy legacy/derived production content back into the active branch.

## Character / provenance state

The active branch no longer contains or uses the old production character paths:

- hard-wired V8 bundled-character startup path: REMOVED
- old mesh handoff/review bundles: REMOVED
- MakeHuman-derived anatomical source/data lineage: REMOVED
- old anatomical generator and character-specific corrective stack: REMOVED
- legacy baseline solved-grip numerical row: REMOVED
- automatic legacy grip-solution fallback in retargeting: REMOVED
- legacy-only retarget test asset paths/fixtures: REMOVED or replaced with source-agnostic diagnostics
- final-character runtime-path audit: PASS and mandatory in CI

The active runtime fallback is the project-authored clean procedural profile path:

- `src/body/profileMesh.ts`
- `src/character/procedural.ts`

This fallback is **not** the final production-quality character. The production character remains the independently authored **ORIGINAL v1** line.

Generic capabilities that remain intentionally supported — GLB import, bone mapping, retargeting, imported-character deformation infrastructure, grip-solution mechanism and biomechanics — must stay source-agnostic and must not reacquire legacy character defaults.

## Repository hygiene

The active branch has removed duplicated/superseded mesh bundles, review assets, old progress/handoff files, obsolete migration entry docs, the redundant O1 launcher and tracked generated audit reports.

`reports/` is generated evidence and is gitignored. Run the relevant audit to create fresh reports; never treat a historical report as current state.

Every `docs/*.md` file must be classified in `DOCUMENTATION_MANIFEST.json`.

Five historical remote branches are verified as fully contained and safe to retire through the guarded laptop cleanup:

- `chatgpt/absolute-retarget-imports`
- `claude/home-gym-pt-animation-txux66`
- `codex/anatomical-reference-character`
- `codex/fix-dumbbell-grip-position`
- `work/self-sufficient-engine-integration-20260925`

Use:

```bat
CLEANUP_CONTAINED_BRANCHES.bat --apply
```

The script rechecks ancestry immediately before deletion. Do **not** manually delete divergent branches.

## Remaining standalone software blockers

Five direct runtime dependencies remain declared during controlled migration:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is removed.

Drei has zero source imports but remains installed until the explicit physical Grid/Orbit/Transform desktop/iPhone parity gate passes.

R3F is now much narrower:

- direct R3F source imports: **1**
- only allowed file: `src/viewer/R3FViewportHost.tsx`
- all visual consumers use the project-owned scene-frame dispatcher rather than importing `useFrame`
- `Viewport.tsx` is host-agnostic and owns the shared scene-state contract
- the migration allowlist prevents R3F imports from spreading again

The remaining R3F problem is now the **host/reconciler boundary**: Canvas ownership, JSX Three-object reconciliation, `useThree` camera/scene access, the one `useFrame` frame driver, R3F pointer routing/picking and host lifecycle.

## Browser evidence already obtained

Automated Chromium evidence now covers the live current viewport:

- WebGL context and drawing buffer
- camera preset rendering
- mouse orbit and wheel zoom
- backdrop rendering
- BoneGroups/SkeletonView playback
- transform-gizmo selection rendering
- CharacterFigure across authored poses
- MuscleView across authored poses
- EquipmentView visibility/rendering
- IKHandles visibility/rendering through real editor IK state
- responsive resize
- no page/console/critical-request errors

The browser smoke also mounts an isolated **project-owned `ThreeSceneHost` with a real `WebGLRenderer`**, verifies its frame loop visibly advances and verifies drawing-buffer resize through the project-owned browser surface.

This is strong automated evidence, but it does **not** close the explicit physical/iPhone pointer/touch gate.

## Cloud/software track — next exact task

Continue only from:

`docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`

Do not redo consumer frame migration or browser evidence already completed.

The next cloud-safe objective is to replace more of the **single `R3FViewportHost.tsx` boundary** with project-owned host/reconciler functionality while keeping the live R3F host available as the parity reference.

Priority order:

1. isolate host-owned static scene construction (background, lights, floor/grid) behind project-owned scene functions;
2. move frame resolution/playback driving from the R3F `useFrame` callback onto the project-owned scheduler/scene contract;
3. move camera/orbit host injection away from `useThree`;
4. replace R3F pointer-miss/picking/event routing with project-owned DOM/raycast routing;
5. create a reversible first-party host switch only after the same browser checks pass against it;
6. remove the last R3F import and package only after host/reconciler parity is demonstrated.

Do **not** rewrite exercise mechanics or consumer semantics during the host cutover.

After R3F is genuinely removed:

1. migrate React/ReactDOM UI/lifecycle to project-owned DOM/store bindings;
2. remove React/ReactDOM after UI parity;
3. complete first-party math/rig/GLB/scene/renderer integration;
4. remove Three.js last.

## Physical browser/device gate

Use:

`docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`

Required physical evidence still includes Grid, Orbit, touch, Transform, rendering and interaction on the intended desktop/iPhone path.

Do not infer physical/iPhone PASS from automated Chromium smoke.

Drei may be removed only after this gate passes.

## Laptop / Blender track — next exact task

Use:

`docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`

From repository root:

```bat
STANDALONE_STATUS.bat
PREPARE_ORIGINAL_V1_O2.bat
```

Then work only on:

`ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend`

Materialise/use the independent 63-bone `hgpt_canonical_v4_original` target and continue O2 neutral anatomy under the clean-room constraints.

Do not import, project, shrink-wrap, retopologise from, transfer, or copy legacy character geometry, topology, UVs, weights, materials, morphs or bind/rest data.

The clean procedural fallback must not be promoted as finished anatomy.

## Session start

Run:

```bat
STANDALONE_STATUS.bat
```

Then verify the checked-out branch is `work/standalone-first-party-audit-20260927`.

## Session end / agent handoff contract

Before another AI continues:

1. run focused tests for the change;
2. run typecheck/build for runtime changes;
3. run `VERIFY_STANDALONE_PREP.bat` or equivalent CI gates;
4. preserve browser/Blender evidence where required;
5. make a coherent commit;
6. update this handoff with verified facts only;
7. state the exact next task and any physical/Blender blocker.

GPT and Claude follow the same repository authority, reference rules, tests, quality stack and handoff format.

## Do not

- re-audit historical branches as a prerequisite to normal continuation;
- reopen V15f development;
- restore removed MakeHuman/anatomical or V8 production paths;
- restore legacy solved-grip rows/defaults;
- copy legacy/reference character data into ORIGINAL v1;
- promote the O1/procedural scaffold as final anatomy;
- spread R3F imports outside `R3FViewportHost.tsx`;
- remove Drei/R3F/React/Three before their stated parity gates;
- weaken a test, threshold, provenance rule, allowlist, dependency ceiling or release gate merely to make migration pass.
