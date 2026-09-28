# Current handoff

## Start here

This is the **single operational entry point** for the current Home Gym PT first-party standalone transition.

Active branch:

`work/standalone-first-party-audit-20260927`

Latest fully verified implementation/cleanup checkpoint:

`05d77a6904d2f0f9a7a5416e22b54b336d25c6a9`

Do not reconstruct project state from historical branches, old chats, removed reports, or superseded handoffs. Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md`, and `docs/DECISION_LOG.md`, then continue only the exact task named below.

## Verified state at 05d77a69

GitHub `Standalone prep verification` passed completely:

- TypeScript typecheck: PASS
- Blender helper Python syntax: PASS
- repository authority / hygiene gate: PASS
- focused first-party foundation suite: 83 / 83 PASS
- full suite: 92 test files PASS, 3 skipped
- full tests: 854 PASS, 67 skipped
- production build: PASS
- final-character runtime-path gate: PASS
- runtime dependency anti-creep gate: PASS
- external runtime resource gate: PASS
- runtime network/API gate: PASS

The separate real-browser `Browser viewport smoke` workflow also passed at this checkpoint. It is supplementary desktop/headless evidence; it does **not** replace the explicit physical desktop/iPhone interaction gate.

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
- final-character runtime-path audit: PASS and mandatory in CI

The active runtime fallback is the project-authored clean procedural profile path:

- `src/body/profileMesh.ts`
- `src/character/procedural.ts`

This fallback is **not** the final production-quality character. The production character remains the independently authored **ORIGINAL v1** line.

Generic capabilities that remain intentionally supported — GLB import, bone mapping, retargeting, imported-character deformation infrastructure, grip-solution mechanism, biomechanics — must stay source-agnostic and must not reacquire legacy character defaults.

## Repository hygiene

The active branch has removed duplicated/superseded mesh bundles, review assets, old progress/handoff files, obsolete migration entry docs, the redundant O1 launcher, and tracked generated audit reports.

`reports/` is now generated evidence and is gitignored. Run the relevant audit to create fresh reports; never treat an old committed report as current project state.

Every `docs/*.md` file must be classified in `DOCUMENTATION_MANIFEST.json`. The hygiene gate fails on unclassified documentation or reintroduced forbidden legacy paths.

Four historical remote branches were verified as fully contained and are safe to retire:

- `claude/home-gym-pt-animation-txux66`
- `codex/anatomical-reference-character`
- `codex/fix-dumbbell-grip-position`
- `work/self-sufficient-engine-integration-20260925`

The GitHub cloud connector cannot delete those refs. On the laptop, the guarded command is:

```bat
CLEANUP_CONTAINED_BRANCHES.bat --apply
```

It rechecks ancestry immediately before deletion. Do **not** manually delete divergent historical branches.

## Remaining standalone software blockers

There are exactly five direct runtime dependencies still declared during controlled migration:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is already removed.

The migration guard is one-way: third-party runtime imports/dependencies may decrease but may not spread into new source files.

Drei has zero source imports but remains installed until the explicit physical Grid/Orbit/Transform desktop/iPhone parity gate passes.

## Cloud/software track — next exact task

Continue only from:

`docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`

Do not redo the already prepared foundations. Existing first-party seams include the frame loop, scene lifecycle, browser surface, temporary Three host, framework-neutral scene state, resolved scene-frame snapshots/object adapter, equipment display-transform resolver, IK-handle snapshot, muscle snapshot, camera/orbit/grid/gizmo foundations, and one-way R3F import ceilings.

Continue the staged **R3F consumer/host migration** using numerical and browser parity. Keep the live R3F implementation until the required parity for the consumer/host being switched is demonstrated.

Do not remove R3F simply to reduce the dependency count.

After R3F is genuinely removed:

1. migrate React/ReactDOM UI/lifecycle to the project-owned DOM/store path;
2. remove React/ReactDOM after UI parity;
3. complete first-party math/rig/GLB/scene/renderer integration;
4. remove Three.js last.

## Physical browser/device gate

Use:

`docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`

The required physical evidence still includes Grid, Orbit, touch, Transform, rendering and interaction on the intended desktop/iPhone path.

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

Do not import, project, shrink-wrap, retopologise from, transfer, or copy any legacy character geometry, topology, UVs, weights, materials, morphs or bind/rest data.

The clean procedural fallback in the app must not be promoted as finished anatomy.

## Session start

Run:

```bat
STANDALONE_STATUS.bat
```

Then verify the checked-out branch is `work/standalone-first-party-audit-20260927`.

A new AI should **not** perform a historical audit before continuing. The authority files and executable gates already define the accepted state.

## Session end / agent handoff contract

Before another AI continues:

1. run focused tests for the change;
2. run typecheck/build for runtime changes;
3. run `VERIFY_STANDALONE_PREP.bat` or the equivalent CI gates;
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
- remove Drei/R3F/React/Three before their stated parity gates;
- weaken a test, threshold, provenance rule, allowlist, dependency ceiling or release gate merely to make a migration pass.
