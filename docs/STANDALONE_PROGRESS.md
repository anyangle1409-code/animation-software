# Standalone first-party progress

## Target
A distributable Home Gym PT product with no third-party runtime implementation and no third-party/legacy creative assets.

## Current status

| Area | Status | Next gate |
|---|---|---|
| V15f legacy hand benchmark | near complete | final whole-hand audit/review |
| Imported/high-detail character lineage | reference-only identified | replace with ORIGINAL v1 |
| MakeHuman built-in anatomical body | third-party-derived identified | replace/remove from production path |
| ORIGINAL v1 clean-room brief | prepared | initialize blank Blender workspace after V15f benchmark |
| Clean-room Blender launcher | prepared | run `START_ORIGINAL_V1_CLEAN_ROOM.bat` at correct phase |
| Canonical rig architecture | project-authored candidate | create independent `hgpt_canonical_v4_original` rest dimensions |
| Equipment models | procedural/project-code candidate | remove legacy body-dimension coupling; validate provenance |
| Fonts | no bundled font assets found | keep system fonts or author owned fonts |
| Runtime images/icons/audio | no production bundle found in repo scan | keep deny-by-default |
| React / ReactDOM | present | replace |
| React Three Fiber / Drei | present | replace |
| Zustand | first-party store implementation patched; package removal pending verification | run typecheck/tests, confirm zero imports, then remove dependency/lock entry |
| Three.js | present | replace last |
| Dependency audit tooling | prepared | run locally |
| Runtime usage scanner | prepared | run locally |
| First-party marker scanner | prepared | run locally |
| Release readiness gate | prepared | must eventually PASS |
| Release asset allowlist | deny-by-default prepared | populate only with approved first-party output |

## Prepared commands

```bat
node scripts\audit-third-party-dependencies.mjs
node scripts\map-third-party-runtime.mjs
node scripts\audit-first-party-markers.mjs
node scripts\check-first-party-release-readiness.mjs
```

The final command is expected to FAIL today. Its purpose is to become the objective standalone completion gate.

## Immediate Work sequence after usage reset

1. Finish V15f final reference audit/review.
2. Record V15f reference benchmark; do not promote it as the standalone model.
3. Run the four standalone audit commands above.
4. Generate the exact runtime dependency usage map.
5. Start the smallest safe software replacement (Zustand) only after parity tests are identified.
6. Initialize ORIGINAL v1 from the clean-room launcher.
7. Begin original neutral anatomy / canonical v4 work without importing legacy geometry.

Do not spend final grip/shoulder/material effort on the legacy character line.


## 2026-09-27 first implementation milestone

A project-owned observable store now exists at `src/core/store.ts`.

Migrated on the standalone audit branch:
- `src/editor/store.ts`
- `src/editor/characterStore.ts`
- `src/editor/generationStore.ts`

A focused store-core test was added at `src/core/store.test.ts`.

**Verification is still required on the laptop/Work environment.** This environment cannot clone/run the repo, so do not remove `zustand` from `package.json` / lockfiles until:
1. typecheck passes;
2. store tests pass;
3. full current suite passes;
4. an exact runtime scan confirms zero Zustand imports.

If those pass, remove the package and regenerate the lockfile. If not, fix the first-party store implementation rather than reverting the standalone plan.


## 2026-09-27 clean scaffold implementation

Prepared:
- `scripts/generate_original_v1_clean_scaffold.py`
- `GENERATE_ORIGINAL_V1_CLEAN_SCAFFOLD.bat`
- `docs/ORIGINAL_V1_SCAFFOLD_USAGE.md`

The generator reconstructs the pinned pre-MakeHuman project-authored procedural body from numeric profiles only.

Hard deterministic guards:
- 3,890 vertices;
- 7,280 triangles;
- 53 clean historical reference bones;
- normalized weights.

It refuses to run unless the Blender scene is marked as a clean-room scene and refuses a scene marked as having imported legacy geometry.

**Laptop verification remains pending** because this environment cannot execute Blender.
