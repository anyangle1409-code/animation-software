# Standalone first-party progress

## Target
A distributable Home Gym PT product with no third-party runtime implementation and no third-party/legacy creative assets.

## Current status

| Area | Status | Next gate |
|---|---|---|
| V15f legacy hand benchmark | near complete | final whole-hand audit/review |
| Imported/high-detail character lineage | reference-only identified | replace with ORIGINAL v1 |
| MakeHuman built-in anatomical body | third-party-derived identified | replace/remove from production path |
| ORIGINAL v1 clean-room scaffold | O1 blank-source proof PASS | O2 neutral anatomy |
| Clean-room Blender launcher | verified with Blender 5.2.1 LTS | keep generation/audit provenance current |
| Canonical rig architecture | project-authored candidate; 53-bone historical reference only in scaffold | create independent `hgpt_canonical_v4_original` rest dimensions |
| Equipment models | procedural/project-code candidate | remove legacy body-dimension coupling; validate provenance |
| Fonts | no bundled font assets found | keep system fonts or author owned fonts |
| Runtime images/icons/audio | no production bundle found in repo scan | keep deny-by-default |
| React / ReactDOM | present | replace |
| React Three Fiber / Drei | present; live Grid, Orbit, and Transform gizmo now use project-owned implementations | physically verify visual/input parity, then remove Drei |
| Zustand | direct dependency removed; first-party store active; full CI PASS | remaining transitive copies disappear with Drei/R3F removal |
| Three.js | present | replace last |
| Dependency audit tooling | prepared | run locally |
| Runtime usage scanner | prepared | run locally |
| First-party marker scanner | prepared | run locally |
| Release readiness gate | prepared | must eventually PASS |
| Release asset allowlist | deny-by-default prepared | populate only with approved first-party output |

## 2026-09-27 live Reference Grid checkpoint

The first Drei migration increment is implemented in the live viewport:

- `ReferenceGridView` renders the project-owned 12 m grid through the current
  temporary R3F/Three adapter;
- minor 0.25 m cells and major 1 m sections are packed separately from the
  renderer-neutral `referenceGrid` data;
- the live viewport no longer imports or mounts Drei `Grid`;
- Drei remains installed because OrbitControls and TransformControls have not
  yet been replaced.

Validation:

- focused grid tests: 4 passed;
- typecheck: passed;
- production build: passed;
- complete regression: 931 passed, 1 skipped, with three timeout-only failures
  under parallel load;
- isolated rerun of the two affected files: 41 passed, confirming the two calf
  foot cases and the generator case without changing code or thresholds.

The visual browser gate remains **OPEN**. The available in-app browser loaded
the localhost HTML but did not execute the module application and returned a
blank root without console errors. Do not report visual parity as passing from
that surface. Continue with the prepared Orbit adapter while preserving this
explicit review item for a compatible local browser.

Next implementation increment: first-party Orbit controls, including desktop
mouse orbit/zoom and iPhone one-finger rotate plus two-finger pinch zoom.

## 2026-09-27 live Orbit controls checkpoint

The live viewport now uses `FirstPartyOrbitControls`, backed by the prepared
renderer-neutral `HgOrbitModel`. The adapter preserves:

- camera preset and focus-camera synchronisation;
- 0.6–12 m zoom limits;
- frame-rate-independent 0.12 damping;
- desktop primary-pointer rotation and wheel zoom;
- iPhone-style one-finger rotation and two-finger pinch zoom;
- suspension of orbit input while either existing transform gizmo is dragging.

The viewport no longer imports Drei OrbitControls or `three-stdlib`. Focused
camera/orbit/input parity is 15/15, typecheck and production build pass, and the
complete regression is 939 passed / 1 intentional skip. The touch/input tests
exercise the same Pointer Event path used by modern iPhone Safari.

The physical browser/device visual gate remains **OPEN** because the available
in-app localhost browser still does not execute the module application. Do not
report that visual gate as passed. The next isolated increment is the first-party
Transform gizmo for bone rotation, equipment translation/rotation, and IK target
or pole translation.

## 2026-09-27 live Transform gizmo checkpoint

The live viewport now uses `FirstPartyTransformGizmo` for bone rotation,
equipment translation/rotation, socket transforms, and IK target/pole
translation. Dragging continues to suspend Orbit input and all existing
selection/update callbacks remain connected.

Validation:

- focused transform maths and interaction tests: 8 passed;
- typecheck: passed;
- production build: passed (233 modules transformed);
- complete regression before the final nested-parent robustness adjustment: 942
  passed, 1 intentional skip, 0 failures;
- final complete rerun: 941 passed, 1 intentional skip, with one unrelated
  5-second neck-weight timeout; that exact test passed unchanged in an isolated
  rerun (4.592 seconds);
- exact source imports from `@react-three/drei`: zero.

No test timeout or threshold was changed. The physical browser/device visual
gate remains **OPEN**. The available in-app
localhost browser still does not execute the Vite module application, so the
Grid, Orbit, touch, and Transform visual/input review cannot be claimed as
passing. `@react-three/drei` remains in the locked dependency set until that
gate can be completed; removing it now would violate the required parity rule.

Next: publish this checkpoint, run the standalone audit and preserve its blocker
counts, then continue the independent ORIGINAL v1 clean-room preparation.

## 2026-09-27 post-Transform standalone audit

The complete standalone audit was rerun after the live Grid, Orbit, and
Transform replacements. The dependency-creep, inventory, usage-map,
first-party-marker, legacy-coupling, external-resource, and runtime-network
checks completed successfully. The final-character-runtime and release-readiness
gates remain expected failures.

Current blocker counts:

- direct runtime dependencies: 5;
- bare runtime imports: 126;
- operational legacy assets: 0;
- MakeHuman-derived source files in the current runtime path: 9.

The five direct runtime dependencies remain `@react-three/drei`,
`@react-three/fiber`, `react`, `react-dom`, and `three`. Drei now has zero source
imports, but its package removal remains held until the open physical visual and
touch parity gate can be completed. No guard was weakened and no legacy asset
was added to an operational asset root.

## 2026-09-27 ORIGINAL v1 O1 checkpoint

`PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat` completed with Blender 5.2.1 LTS and
opened the verified clean-room Blend. The deterministic scaffold contains 3,890
vertices, 7,280 triangles, and the 53-bone clean historical reference armature.
The Blender audit passed with zero blockers and zero warnings.

The provenance record states that no third-party or legacy geometry was
imported and no legacy projection was used. The current Blend SHA-256 is
`33f67e42fb8f5bb524b72bfb7b0aee6e3656f853e1c54e6a53034881161f21bf`.
The Blend remains local under the existing ignore rule; its provenance JSON,
audit report, and O1 evidence are versioned. This is a scaffold, not a production
character, and its 53-bone reference armature must not be renamed or promoted as
canonical v4.

Next gate: define independent project-authored target dimensions for
`hgpt_canonical_v4_original`, then begin O2 neutral anatomy without fitting to a
legacy mesh or copying v3 numerical rest coordinates.

## 2026-09-27 canonical v4 ORIGINAL definition checkpoint

The first independent `hgpt_canonical_v4_original` numerical rest definition is
implemented as a non-runtime candidate. It preserves the project-owned 63-bone
architecture while deriving every rest point from newly declared ORIGINAL
design dimensions. It does not import the v3 humanoid definition or its
legacy-fit shoulder constants.

Focused gates pass 6/6: identity, hierarchy, finite bone lengths, exact designed
symmetry, target dimensions, complete hand/IK chains, all 28 exercise generators
resolving structurally, and source independence. Typecheck passes. The active v3
runtime rig and every existing exercise remain unchanged.

Production build passes. The complete shared regression passed 944 tests with
one intentional skip and four time-limit failures in pre-existing long-running
tests. The two calf cases and the generator case passed unchanged immediately
in isolation. The neck-weight case remains above its 5-second limit under the
current laptop load; that same unchanged case passed in 4.592 seconds at the
preceding Transform checkpoint. No timeout or threshold was changed.

Next: materialize this armature in the clean-room Blend, preserve the historical
53-bone armature as reference-only, and begin O2 neutral anatomy against v4.

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
2. Record V15f as a legacy benchmark only; do not continue grip/shoulder/material production polish on that lineage.
3. Switch to `work/standalone-first-party-audit-20260927`.
4. Run `STANDALONE_STATUS.bat`.
5. Run `VERIFY_STANDALONE_PREP.bat`.
6. Integrate the prepared Drei replacements incrementally:
   - Reference Grid first;
   - Orbit controls second, including iPhone rotate/zoom;
   - Transform gizmo last.
7. Remove `@react-three/drei` only after zero imports plus visual/touch parity.
8. Run `npm run audit:standalone` and preserve blocker counts.
9. Start ORIGINAL v1 with `PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat`.
10. Begin clean neutral anatomy / canonical v4 work without importing legacy geometry.

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


## 2026-09-27 verified software checkpoint

Completed:
- project-owned observable store is in use by all three editor stores;
- direct `zustand` was removed from `package.json` and the root lock declaration;
- full CI passed after direct Zustand removal;
- the anti-creep allowlist now prevents re-adding Zustand directly.

Five direct runtime dependencies remain:
- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Zustand still appears transitively while Drei/R3F remain; this is expected and
is not being hidden. It disappears from the operational dependency tree when
those parents are removed.

Prepared and focused-test verified:
- first-party camera preset data/parity;
- renderer-independent orbit state;
- first-party reference-grid geometry;
- transform-gizmo axis/rotation drag maths.

The current lock graph indicates Drei accounts for roughly 46 runtime package
names that are otherwise unnecessary for the current direct dependency set.
That makes Drei the next high-value removal.

Also prepared/verified:
- first-party math;
- frame scheduler;
- skeleton parity across the exercise library;
- IK orientation parity;
- pose blending parity;
- GLB container/accessor/writer foundations;
- runtime network/API guard;
- production-output scan;
- release allowlist gate;
- offline standalone acceptance;
- Blender clean-room generator/audit helpers.

Use `STANDALONE_STATUS.bat` at the start of future sessions instead of
reconstructing this state manually.

## 2026-09-28 Cloud O2 and R3F preparation checkpoint

The O2 handoff is `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`. The clean v4 numerical rest definition now has a committed deterministic JSON export and independent Python structure/symmetry/dimension checks. `PREPARE_ORIGINAL_V1_O2.bat` checks the export, backs up the existing O1 Blend, and creates the unbound 63-bone v4 armature while preserving the 53-bone historical rig as reference-only. A separate Blender audit compares every name, parent and rest endpoint to the export. These Blender scripts have syntax and payload tests but **have not executed against the laptop's local Blend in this Cloud environment**. O1 scaffold height is 1.75 m; v4 target height is 1.82 m. O2 remains subject to genuine visual review.

R3F migration map and reversible increments are in `docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`: nine current R3F import sites, symbols `Canvas`, `useFrame`, `useThree`, `ThreeEvent`, plus implicit JSX/event/lifecycle behavior. Existing renderer-independent `HgFrameLoop` has an added ordered-consumer parity assertion. No production renderer path or model data changed. React/ReactDOM follow R3F; Three.js is last. Drei remains installed until physical browser/device parity.

Focused verification here: v4 export/check, 3 Python payload tests, Python syntax compile, 7 v4 TypeScript tests, 5 frame-loop tests, typecheck and production build passed. Standalone audit still intentionally fails final-character-runtime and release-readiness; its other stages pass. Counts remain **5 direct runtime dependencies, 126 bare imports, 0 operational legacy assets, 9 MakeHuman-derived source files on runtime path**. No release guard was loosened.

A separate O2 mesh auditor now reports symmetry, 1.82 m height, manifold/winding, loose and degenerate/duplicate face counts from the actual Blender mesh. Its pure geometry logic has 3 fixture tests. Draft runs report without claiming acceptance; `-- --strict` gates a completed neutral mesh. Blender execution and subjective silhouette approval remain pending.

## 2026-09-28 R3F lifecycle foundation

A renderer-neutral `HgSceneLifecycle` owns one ordered frame loop, surface resize, clamped DPR [1, 2], context-loss pause/restore, and idempotent disposal through injected adapters. Eight focused scene/frame tests and typecheck pass. This is isolated preparation; the live R3F `Canvas` and all production rendering remain unchanged. Next Work task: implement a DOM/WebGL surface adapter and its tests, then establish R3F frame/pose snapshot parity before switching any consumer.
