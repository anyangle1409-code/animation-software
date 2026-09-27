# GPT Work handoff — first-party standalone transition

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
