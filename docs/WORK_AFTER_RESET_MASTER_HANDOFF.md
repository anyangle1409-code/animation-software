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
npm test -- --run src/core/store.test.ts src/editor/store.test.ts src/editor/characterStore.test.ts
npm test -- --run
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
