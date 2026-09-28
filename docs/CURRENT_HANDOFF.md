# Current handoff

## Start here

This is the single operational entry point for the current standalone transition.

Branch:

`work/standalone-first-party-audit-20260927`

The repository has been pruned of the duplicated legacy mesh handoff, duplicated review-assets bundle, and superseded reference-body/model-repair handoff documents. The cleanup checkpoint `f6ef7856b15c762f1873ba942cdcff50f92aea8a` passed the complete GitHub `Standalone prep verification` workflow.

Do not re-audit removed historical material before starting work.

## Latest verified software baseline

After the cleanup checkpoint:

- 92 test files passed, 3 skipped;
- 897 tests passed, 67 skipped;
- typecheck passed;
- production build passed;
- runtime-dependency anti-creep gate passed;
- external-runtime-resource gate passed;
- runtime-network gate passed.

Skipped tests are existing explicit skips; the cleanup did not create new failures.

## Repository hygiene

The active branch has already removed the duplicated legacy mesh handoff, duplicated review-assets bundle, and superseded reference-body/model-repair handoffs.

Four obsolete remote branches have been verified as fully contained in the active branch and are safe to retire. The cloud GitHub connection cannot delete refs, so the guarded laptop command is:

```bat
CLEANUP_CONTAINED_BRANCHES.bat --apply
```

See `docs/BRANCH_HYGIENE.md`. Do not manually delete any divergent historical branch.

## Current standalone blockers

The final standalone/release gates are intentionally not green yet.

Current direct runtime dependencies:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Current known character blocker:

- MakeHuman-derived built-in anatomical source remains on the runtime path and must be removed/replaced before release.

Operational legacy asset count in the current audit is zero.

## What is already decided

Read `docs/DECISION_LOG.md`. Do not revisit V15f provenance, the need for ORIGINAL v1, or the canonical-v4 independence decision.

## Cloud/software track — next exact task

Continue from `docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`.

The isolated first-party lifecycle, DOM surface, temporary Three host, framework-neutral scene state, resolved-frame snapshot, flat scene-object adapter, and BoneGroups-style transform fixture are already prepared.

Do not redo those foundations. The equipment display-transform orchestration is also isolated in `src/viewer/equipmentDisplayTransforms.ts`, and IK target/pole state semantics are isolated in `src/viewer/ikHandleSnapshot.ts`; those are test-only/unmounted preparation; the muscle overlay is likewise copied through `src/viewer/muscleFrameSnapshot.ts`. All must be compared against their live consumers before any switch.

The next safe migration work is browser-backed visual/skin/lifecycle parity for the first actual visual consumer, then a reversible consumer bridge. Keep the live R3F hook until the relevant parity gate passes.

Drei has zero source imports but remains installed until the physical Grid/Orbit/Transform browser/device gate passes.

## Laptop/Blender track — next exact task

Use `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`.

From repository root:

```bat
STANDALONE_STATUS.bat
PREPARE_ORIGINAL_V1_O2.bat
```

Then work only on `ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend`.

Materialise the independent 63-bone `hgpt_canonical_v4_original` armature and continue O2 neutral anatomy under the clean-room constraints. Do not import, project, shrink-wrap, transfer, or copy from a legacy character.

## Automated browser evidence

The separate `Browser viewport smoke` workflow is supplementary evidence for the executing Vite/WebGL app. If green, use its screenshots/JSON to catch module, WebGL, camera, desktop-orbit, playback and resize regressions. Do not use it to mark the physical/iPhone gate complete.

## Physical browser/device gate

Use `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.

Record PASS/FAIL/NOT TESTED evidence for Grid, Orbit/touch, Transform, rendering, and interaction. Do not infer a pass from unit tests.

## Session-start command

Run:

```bat
STANDALONE_STATUS.bat
```

If its branch target does not match the checked-out branch, correct the checkout before changing files.

## Session-end requirements

Before handing to another AI:

1. run the relevant focused tests;
2. run typecheck/build for runtime changes;
3. run standalone guards;
4. commit the coherent increment;
5. update this file with verified facts only;
6. state the exact next task and any open physical/Blender gate.

## Do not

- search old branches for alternative instructions;
- reopen V15f development;
- use removed legacy bundles as production input;
- promote O1 scaffold geometry as finished production anatomy;
- remove R3F/React/Three before their parity/integration gates;
- weaken a test, timeout, provenance guard, release denylist, or allowlist to force progress.
