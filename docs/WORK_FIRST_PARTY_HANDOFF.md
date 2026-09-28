# GPT Work handoff — first-party standalone transition

## Current implementation checkpoint — 2026-09-27

V15f is preserved on its separate legacy branch. Standalone preparation is
verified: 933 tests passed with one intentional skip, typecheck/build passed,
and dependency-creep, external-resource and runtime-network guards passed.

The live Reference Grid increment is complete on this branch and is ready for a
durable checkpoint. Its focused tests, typecheck and build pass. The full
regression had three parallel-load timeouts, and all affected tests passed in an
isolated rerun (41/41). The in-app localhost browser could not execute the module
application, so the Grid visual gate is explicitly open rather than falsely
marked pass.

The first-party Orbit controls increment is now implemented and validated:
15/15 focused camera/orbit/input tests, typecheck, build, and 939/939 full-suite
tests pass with one intentional skip. Desktop pointer/wheel and iPhone-style
one-finger rotate/two-finger pinch input share the tested Pointer Event adapter.
The physical visual/device gate remains open because the available localhost
browser surface does not execute the module application.

The first-party Transform gizmo increment is now implemented. It preserves bone
rotation through the existing anatomical clamp callback, static equipment
translation/rotation, socket transforms, IK target/pole translation, selection
behavior, and Orbit suspension while dragging. Focused transform tests are 8/8,
typecheck and build pass. A complete regression passed 942/942 with one
intentional skip before the final nested-parent robustness adjustment. The
final complete rerun passed 941 tests and hit one unrelated 5-second
neck-weight timeout; that exact test passed unchanged in an isolated rerun in
4.592 seconds. No threshold was changed. Exact source imports from
`@react-three/drei` are now zero.

Do not remove Drei yet. The only available localhost browser surface still does
not execute the Vite module application, so physical Grid, Orbit/touch, and
Transform visual/input parity remains an explicit open gate. Run and preserve
the standalone audit blocker counts, then continue ORIGINAL v1 clean-room work
independently of that browser limitation.

The post-Transform standalone audit is now preserved. It reports five direct
runtime dependencies, 126 bare imports, zero operational legacy assets, and
nine MakeHuman-derived source files on the current runtime path. The
final-character-runtime and release-readiness gates fail as expected; all other
audit stages pass. Continue with `PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat` while the
physical browser gate remains open. Do not remove Drei or weaken the gate merely
to reduce the dependency count.

`PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat` has now completed successfully with
Blender 5.2.1 LTS. O1 blank-source proof passes: 3,890 vertices, 7,280 triangles,
53 clean historical reference bones, zero clean-room audit blockers/warnings,
and no legacy import or projection. The Blend is open locally and remains
ignored by the repository as intended; its provenance JSON and audit evidence
are checkpointed. Continue with independent canonical-v4 target dimensions and
O2 neutral anatomy. Do not treat the 53-bone reference armature as canonical v4.

The first independent `hgpt_canonical_v4_original` rest definition is now a
non-runtime code candidate. It contains all 63 project-owned architecture bones,
uses newly declared ORIGINAL dimensions, mirrors the right side algorithmically,
and has no import from the v3 numerical rig. Its six focused structural and
independence tests pass, including all 28 exercise generators. Materialize this
armature in the clean-room Blend next; do not switch the runtime skeleton yet.

Typecheck and production build pass. The full shared suite passed 944 tests and
hit four pre-existing performance timeouts under current laptop load. Three
passed unchanged in immediate isolated reruns; the neck-weight case is still
over 5 seconds now but passed unchanged at the prior checkpoint. No guard,
timeout, or threshold was changed.

## Objective

Prepare Home Gym PT so the distributable product contains no third-party runtime code or third-party creative assets.

This work is isolated on:
`work/standalone-first-party-audit-20260927`

Do not merge this branch into `chatgpt/absolute-retarget-imports` merely because the audit exists. Use it as a planning/audit branch until the migration steps are separately validated.

## Read first

1. `docs/FIRST_PARTY_STANDALONE_PLAN.md`
2. `docs/ASSET_PROVENANCE_AUDIT.md`
3. `scripts/audit-third-party-dependencies.mjs`
4. current V15f hand-state docs on `work/v15-deep-hand-rebuild-prep-20260925`

## Important sequencing decision

When Work usage resumes, do **not** abandon V15f halfway through its final gate.

First finish the already-near-complete V15f reference benchmark:
1. inspect current local V15f state;
2. run `V15F_STATUS.bat`;
3. if all per-digit visual gates are current, run `AUDIT_V15F_FULL.bat`;
4. if that passes, run the normal V15f post-edit/frozen/current-source validation;
5. inspect the final matched review;
6. record V15f as a reference benchmark only.

Do not promote V15f as the final first-party distributable character.

## After V15f reference benchmark

Pivot expensive character work to a clean-room/original character before doing final grip/shoulder/appearance passes.

Create a separate clean-room character branch/workspace. The new character must start from a blank/new mesh and must not copy legacy/imported:
- vertices;
- faces/topology;
- UVs;
- weights;
- materials/textures;
- morph targets;
- imported source-rig transforms/bind matrices.

The legacy V15f line may supply abstract acceptance targets and visual failure examples only.

## Software audit task

On this audit branch:

1. Run:
   `node scripts/audit-third-party-dependencies.mjs`

2. Inventory every runtime import/use of:
   - react
   - react-dom
   - three
   - @react-three/fiber
   - @react-three/drei
   - zustand

3. Produce `docs/RUNTIME_DEPENDENCY_USAGE_MAP.md` with:
   - exact files;
   - imported symbols;
   - role of each dependency;
   - replacement surface/API required;
   - dependency relationships;
   - test coverage guarding that behaviour.

4. Do not begin a broad rewrite until the usage map is complete.

5. Recommended implementation order:
   - Zustand;
   - Drei;
   - React Three Fiber;
   - React/ReactDOM;
   - Three.js last.

6. For each replacement:
   - add parity tests before removal;
   - implement project-authored substitute;
   - switch one subsystem;
   - run typecheck/build/tests;
   - prove user-visible and animation/export behaviour is unchanged;
   - remove the dependency only when no runtime import remains;
   - checkpoint before moving to the next dependency.

## Do not waste Work usage on

- re-investigating whether the legacy character is imported/derived; project docs already establish that;
- trying to make V15f legally/provenance-clean by modifying it further;
- replacing dev/test tooling before Level-1 runtime independence;
- rewriting Three.js first;
- changing exercise mechanics to accommodate a new renderer/model;
- merging the Blender branch into source.

## Deliverables before implementation begins

Work should create/update:
- `docs/RUNTIME_DEPENDENCY_USAGE_MAP.md`
- `docs/FIRST_PARTY_COMPONENT_MANIFEST.md` or JSON equivalent
- `docs/THIRD_PARTY_REFERENCE_ONLY.md`
- a clean-room character creation handoff
- a release allowlist design that excludes legacy GLBs/Blends/reference renders

## Stop conditions

Stop rather than guess if:
- ownership/provenance of a supposedly first-party asset is unclear;
- an implementation step would copy geometry/data from the legacy character;
- removing a library requires changing biomechanics/exercise definitions;
- parity cannot be demonstrated;
- the only path requires loosening existing guards.

## Principle

Use the current product as a behavioural specification and engineering reference, not as a source of third-party implementation or character geometry for the final standalone product.


## New provenance findings from pre-reset audit

The repo explicitly documents that the built-in anatomical body arrays in `src/body/anatomical*.ts` are generated from MakeHuman CC0 assets. CC0 is permissive, but the user's target is stricter than licence compliance: zero third-party creative content in the distributable.

Therefore Work must treat both of these as reference-only:
1. imported/high-detail Home Gym PT character lineage;
2. MakeHuman-derived built-in anatomical character arrays.

Read:
- `docs/FIRST_PARTY_PROVENANCE_FINDINGS_2026-09-27.md`
- `docs/CANONICAL_V4_ORIGINAL_RIG_PLAN.md`
- `docs/ORIGINAL_V1_CLEAN_ROOM_CHARACTER_BRIEF.md`

The current rig architecture appears project-authored, but its v3 numerical rest coordinates include later tuning against the legacy/imported character. Keep the 63-bone hierarchy/names/semantics as a first-party design candidate, but author new clean numerical rest proportions as `hgpt_canonical_v4_original`.

The equipment system is procedural/project-code geometry (generic primitives, no separate equipment model assets found). Retain it provisionally, but remove body-relative constants inherited from legacy character dimensions and recalibrate against canonical v4 / ORIGINAL v1.

## Prepared local audit commands

Run from repository root:

`node scripts/audit-third-party-dependencies.mjs`

`node scripts/map-third-party-runtime.mjs`

`node scripts/audit-first-party-markers.mjs`

These should be run before beginning the runtime migration so the exact dependency/marker reports are preserved.

## Prepared clean-room Blender entry point

When the project is ready to begin ORIGINAL v1, use:

`START_ORIGINAL_V1_CLEAN_ROOM.bat`

This launches Blender with factory startup and creates:
- `ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend`
- `ORIGINAL_V1_WORK/ORIGINAL_V1_PROVENANCE.json`

The initializer deliberately imports no legacy geometry and creates no body geometry. It establishes blank clean-room collections and provenance metadata only.

Do not run it as a substitute for finishing the V15f reference benchmark first. After V15f final review is preserved, this becomes the correct start point for the new production character line.

## 2026-09-28 current next actions (supersedes older sequence above)

- Branch: `work/standalone-first-party-audit-20260927`; V15f is finished and reference-only. Grid, Orbit and Transform are already first-party; do not redo them.
- Laptop: from repository root run `PREPARE_ORIGINAL_V1_O2.bat`, then open `ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend`. First region: torso/chest/back against the 1.82 m v4 target. Follow `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md` for stage checks, stop conditions and checkpoints. The untracked local O1 Blend must be present; Cloud cannot execute this step.
- Work: add R3F parity coverage and host lifecycle seam in the small increments of `docs/R3F_FIRST_PARTY_MIGRATION_HANDOFF.md`, then migrate one visual consumer at a time. Keep R3F/React/Three and Drei installed until their gates pass.
- 2026-09-28 audit: 5 direct runtime dependencies, 126 bare runtime imports, 0 operational legacy assets, 9 MakeHuman-derived runtime-path source files. Final-character and release-readiness gates remain expected failures.

- After each O2 modelling region, run the mesh audit command in `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`; use its strict mode only on the completed neutral mesh.

- Cloud follow-up: `HgSceneLifecycle` now has tested scheduling, DPR, resize, context-loss and disposal. Add an isolated DOM/WebGL adapter and parity tests, then bridge one scene consumer. Do not switch the live viewport before parity evidence.

- DOM scene surface adapter is prepared and focused-tested; next use an isolated Three renderer fixture to establish rendered/pose parity before any live R3F migration.

- Isolated Three scene host is tested with a fake renderer. Next Work step needs compatible browser evidence for pixels, lights/shadows, picking and input before switching `Viewport.tsx`.

- Audit regressions added for test-file exclusion and root/nested `**/` release denies. Run `node --test scripts/audit-legacy-character-coupling.test.mjs scripts/audit-release-allowlist.test.mjs` after editing either scanner.

- O2 v4 export is dimension-gated for breadth, limbs, palm, metacarpals and all finger segments; Blender materialisation still requires the local O1 Blend.

- Latest Cloud audit after the isolated host: 5 direct runtime dependencies, 127 bare source imports (the additional temporary Three import is not mounted in production), 0 operational legacy assets, 9 MakeHuman-derived source files. Final-character and release-readiness gates remain open.

- Release allowlist now blocks symbolic links and incorrect policy mode. Four scanner regression fixtures pass. Cloud has no browser binary or Blender, so run laptop visual/Blender gates without treating Cloud fixture tests as visual approval.

- O2 laptop launcher now fails early on wrong branch/missing Node development tools. If it reports missing `esbuild`, run `npm ci` in that repo, then rerun `PREPARE_ORIGINAL_V1_O2.bat`.

- O2 materialisation rejects a local O1 Blend whose SHA-256 differs from committed O1 provenance; inspect/recover the verified source rather than rewriting the hash to bypass the guard.

- When the laptop is available, use `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md` for exact desktop/iPhone Grid, Orbit and Transform checks. Record PASS/FAIL/NOT TESTED evidence; do not remove Drei from unit-test evidence alone.
