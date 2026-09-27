# GPT Work after-reset master handoff

Use this as the controlling instruction when the 5-hour Work allowance resets.

Repository:
`anyangle1409-code/animation-software`

There are three separate concerns. Keep them separate:
1. V15f legacy hand benchmark branch:
   `work/v15-deep-hand-rebuild-prep-20260925`
2. live source:
   `chatgpt/absolute-retarget-imports`
3. first-party standalone preparation:
   `work/standalone-first-party-audit-20260927`

Do not merge these branches together merely to simplify the workspace.

## A. First: finish the local V15f reference benchmark safely

The laptop may contain local/generated files newer than the last remote handoff.

Before pulling/resetting/cleaning anything:
1. inspect the existing local repository and working tree;
2. preserve all local/untracked Blender/generated files;
3. confirm branch;
4. run from `HIGH_DETAIL_MESH_WORK`:
   `V15F_STATUS.bat`
5. read the local generated status/handoff.

Remote files are slightly inconsistent:
- `NEXT_ACTION.md` and the latest heartbeat state say all eight digit numeric + visual gates are complete and checkpoint 012 is ready for full audit;
- one older/generated `V15F_LATEST_HANDOFF.md` copy still says middle_R visual is missing.

Resolve this from the actual local artifacts. Do not redo middle_R geometry just because a stale remote handoff says its visual marker is missing.

If the local status says middle_R visual evidence/decision is genuinely missing:
- generate/open the existing middle_R board;
- inspect it;
- record the missing decision only if supported by the current board;
- do not alter geometry unless the current visual gate actually fails.

When all incremental gates are current:
- run `AUDIT_V15F_FULL.bat`;
- if it passes, run the established V15f post-edit/frozen/current-source pipeline;
- inspect the complete matched hand review;
- preserve the final reports/checkpoint/heartbeat.

V15f is now a **legacy quality benchmark only** for the standalone project. Do not start Phase C grip refitting, shoulder polish, material polish or production promotion on the legacy character after the benchmark is preserved.

## B. Then: switch to the standalone preparation branch

Use:
`work/standalone-first-party-audit-20260927`

Read:
1. `docs/FIRST_PARTY_STANDALONE_PLAN.md`
2. `docs/FIRST_PARTY_PROVENANCE_FINDINGS_2026-09-27.md`
3. `docs/ASSET_PROVENANCE_AUDIT.md`
4. `docs/ORIGINAL_V1_CLEAN_ROOM_CHARACTER_BRIEF.md`
5. `docs/CANONICAL_V4_ORIGINAL_RIG_PLAN.md`
6. `docs/ORIGINAL_V1_DATA_MIGRATION_MAP.md`
7. `docs/STANDALONE_PROGRESS.md`

Confirmed provenance facts:
- imported/high-detail Home Gym PT character lineage is reference-only;
- built-in `src/body/anatomical*.ts` arrays are explicitly generated from MakeHuman CC0 data and are also reference-only for the user's stricter zero-third-party target;
- equipment is procedural/project-code geometry with no separate equipment model assets found;
- canonical rig architecture is project-authored candidate, but v3 numerical rest positions include legacy-character tuning and therefore need a clean v4 rest-proportion rebaseline.

Run:
```
node scripts/audit-third-party-dependencies.mjs
node scripts/map-third-party-runtime.mjs
node scripts/audit-first-party-markers.mjs
node scripts/audit-legacy-character-coupling.mjs
node scripts/check-first-party-release-readiness.mjs
```

The last command is expected to FAIL today. Preserve its report as the starting blocker count.

Produce/update the exact runtime dependency usage map before replacing code.

## C. Begin the clean production line

After the V15f reference benchmark is preserved, initialize the new clean-room Blender file with:

`START_ORIGINAL_V1_CLEAN_ROOM.bat`

This must create a blank ORIGINAL v1 workspace. Do not import V8/V13e/V15f/MakeHuman geometry into it.

New production identities:
- character: `HomeGymPT_Male_ORIGINAL_v1`
- clean rig target: `hgpt_canonical_v4_original`

The first modelling objective is **neutral anatomy and topology**, not grip fitting and not exercise-specific compensation.

Use generic/project-authored anatomical specifications and the clean-room brief. The old character may be used only as a defect/behaviour benchmark, never as a geometry/weights/UV/proportion projection source.

## D. Software migration

Do not rewrite everything at once.

After the runtime usage map is generated, begin with the smallest dependency:
1. Zustand;
2. Drei;
3. React Three Fiber;
4. React/ReactDOM;
5. Three.js last.

For every removal:
- identify parity tests first;
- implement project-authored replacement;
- run typecheck/build/tests;
- verify user-visible behaviour;
- remove the dependency only after no runtime import remains;
- checkpoint and update `docs/STANDALONE_PROGRESS.md`.

Do not remove development tools yet unless needed. The immediate requirement is zero third-party code/assets in the distributable runtime; Level-2 build-tool independence comes later.

## E. General rules

Do not:
- merge source into mesh branches;
- copy legacy/MakeHuman geometry into ORIGINAL v1;
- transfer legacy weights/UVs/materials;
- use shrink-wrap/retopo against the legacy model as the source shape;
- preserve old rig coordinates merely to match the legacy body;
- change exercise intent/biomechanics to hide clean-model defects;
- loosen validation thresholds;
- package reference renders/legacy GLBs/Blends.

Continue autonomously through safe deterministic work and publish small durable state updates. If a subjective final decision blocks one lane, continue independent audit/setup work in another lane rather than stopping the whole session.

At every unattended stop, record:
- branch/HEAD;
- completed task;
- reports;
- blockers;
- exact next command;
- whether geometry/code changed;
- standalone readiness blocker counts.


## Prepared Zustand replacement checkpoint

The standalone branch now contains:
- `src/core/store.ts` — project-owned synchronous observable store + temporary React selector hook;
- `src/core/store.test.ts`;
- the three editor stores migrated away from direct `zustand` imports.

Do **not** reimplement this from scratch first.

First verify it locally:
```
npm run typecheck
npm test -- src/core/store.test.ts src/editor/store.test.ts src/editor/characterStore.test.ts
npm test
npm run build
```

Use the repository's actual test command syntax if the package scripts differ.

Then run the dependency/runtime scanners.

Only if all checks pass:
- remove `zustand` from `package.json`;
- regenerate/update the lockfile through the normal package manager;
- rerun typecheck/build/full tests;
- update `docs/STANDALONE_PROGRESS.md`.

If compilation exposes a selector/subscription parity issue, repair `src/core/store.ts`; do not restore Zustand as the final solution.


## Prepared ORIGINAL v1 clean scaffold generator

After V15f benchmark preservation, use:
```
START_ORIGINAL_V1_CLEAN_ROOM.bat
GENERATE_ORIGINAL_V1_CLEAN_SCAFFOLD.bat
```

Then verify in Blender:
- object `HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD` exists;
- reference rig `HGPT_CLEAN_HISTORICAL_REFERENCE_RIG` exists;
- 3,890 vertices;
- 7,280 triangles;
- 53 reference bones;
- provenance JSON says `third_party_geometry_imported: false`.

Do not treat the 53-bone reference rig as canonical v4. Its purpose is to reconstruct the clean historical procedural surface. Build/rebind to `hgpt_canonical_v4_original` as the next rig phase.


## Pre-reset standalone preparation checkpoint

Before doing new standalone implementation, read:
`docs/PRE_RESET_STANDALONE_CHECKPOINT.md`

New prepared foundations since the earlier handoff:
- `VERIFY_STANDALONE_PREP.bat`;
- `npm run audit:standalone`;
- runtime dependency anti-creep gate;
- runtime network/API gate;
- production-output third-party audit;
- `src/core/linearMath.ts` + tests (isolated, not integrated);
- `src/core/glbContainer.ts` + tests (isolated, not integrated);
- `src/core/gltfAccessors.ts` + tests (isolated, not integrated);
- verified runtime dependency usage map;
- standalone prompt-generation audit.

After V15f benchmark preservation, the **first standalone action** is now:

```
VERIFY_STANDALONE_PREP.bat
```

Do not connect the prepared math/GLB implementations to production until their
isolated tests pass and temporary parity tests against the current Three-based
implementation are in place.

The prompt generator must remain operationally local: do not add a hosted AI/API
runtime dependency.


## Consolidated prepared commands — latest

### Finish legacy benchmark first
From the V15f branch/workspace:
`V15F_STATUS.bat`
then follow the genuine local state through the final V15f audit/review.

### Verify standalone preparation
On `work/standalone-first-party-audit-20260927`:

```
VERIFY_STANDALONE_PREP.bat
```

This now verifies:
- first-party store;
- first-party linear algebra;
- temporary Three math parity;
- first-party GLB container/accessors;
- first-party frame loop;
- first-party skeleton parity across the exercise library;
- first-party IK orientation parity;
- first-party pose blending parity;
- existing store tests;
- full suite/build;
- runtime dependency anti-creep;
- external resource/network gates.

Do not integrate an isolated replacement module if this verification fails.

### Record current standalone blockers
```
npm run audit:standalone
```

This is expected to fail on remaining migration blockers. Preserve the reports.

### Start ORIGINAL v1
After V15f is preserved as reference:

```
PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat
```

This is now preferred over manually running the initializer/generator/audit. It
branch-checks, generates the pinned first-party scaffold, audits it and opens the
Blend only after the clean-room gate passes.

### Final release gate (much later)
```
npm run audit:release
```

Do not attempt to make this pass by weakening scanners/allowlists. It passes only
when the operational product is genuinely first-party and the release allowlist
is explicitly populated with approved production output.

## Runtime AI/network rule

The existing prompt generator is local/deterministic and should remain so.
Do not add a hosted AI/API runtime dependency.

The one reviewed dynamic fetch in `src/character/bundled.ts` is permitted only
as a local packaged-character probe. Its final target must be ORIGINAL v1, not
the V8 legacy asset.


## Zustand lockfile nuance

After the prepared first-party store passes verification and the project's
**direct** `zustand` dependency is removed, `package-lock.json` may still
contain Zustand entries temporarily.

Current lockfile inspection shows Zustand is also required transitively by the
existing R3F/Drei stack (including tunnel-rat).

That is expected during migration.

Do not manually delete transitive lock entries. Let `npm install` /
`npm uninstall zustand` regenerate the lockfile normally.

Milestones:
1. first Zustand milestone = zero Home Gym PT runtime imports + no direct
   `package.json` dependency;
2. final standalone milestone = no Zustand code in the production output;
3. lockfile/transitive Zustand disappears naturally when R3F/Drei and their
   dependency graph are removed.

The final product gate remains zero third-party runtime code. Temporary
development/migration lockfile presence is not acceptance.


## 2026-09-27 verified first-party checkpoint — do not redo Zustand

Direct Zustand removal is complete on the standalone branch.

Evidence:
- the three editor stores use `src/core/store.ts`;
- direct `zustand` is absent from `package.json`;
- root lockfile declaration removed;
- full typecheck / focused parity suite / full regression / build / guards passed
  on the direct-Zustand-removal checkpoint;
- the anti-creep policy no longer permits Zustand as a direct dependency.

Transitive Zustand packages remain only because Drei/R3F currently depend on
them. Do not spend Work time trying to hand-edit those transitive lock entries.
Remove them naturally when their parent packages are removed.

### New first command on the standalone branch

```
STANDALONE_STATUS.bat
```

Then:

```
VERIFY_STANDALONE_PREP.bat
```

### Next software task: Drei

Do not rediscover or rewrite the interaction maths. Prepared files:
- `src/viewer/firstPartyCameras.ts`
- `src/viewer/orbitModel.ts`
- `src/viewer/referenceGrid.ts`
- `src/viewer/transformGizmoMath.ts`

Integrate in this order:
1. Grid;
2. Orbit, with desktop and iPhone touch rotate/zoom review;
3. Transform gizmo for bone rotation, equipment translation/rotation and IK handle translation.

Only after all three live adapters pass should `@react-three/drei` be removed.

Do not substitute another controls/gizmo package.

### ORIGINAL v1

The Blender helper Python files are now syntax-checked in CI. The scaffold hard
counts have also been independently reconciled from the generator construction:
- 3,890 vertices;
- 7,280 triangles;
- 53 historical clean reference bones.

After the V15f legacy benchmark is preserved, the preferred clean start remains:

```
PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat
```

### Final-build warning

Vite/TypeScript/Vitest/Playwright may remain development tools, but no runtime
helper/vendor code they generate may survive inside the final operational
package. The final production output itself is what must pass the first-party
release audit and offline test.
