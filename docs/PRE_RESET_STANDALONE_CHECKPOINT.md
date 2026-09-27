# Pre-reset standalone checkpoint — 2026-09-27

## Hard project rule

The finished operational Home Gym PT product must contain/require:
- zero third-party runtime code;
- zero third-party model/creative assets;
- zero MakeHuman/imported/legacy production content;
- zero remote/CDN/API runtime dependency.

External development tools are allowed if they are not shipped or required by
the finished operational product.

## Prepared and committed

### Release/provenance
- first-party standalone roadmap;
- component manifest;
- deny-by-default release asset allowlist;
- legacy/MakeHuman provenance findings;
- clean historical procedural scaffold provenance;
- canonical v4 clean rig provenance;
- geometry-independence/no-copy audit;
- runtime dependency anti-creep allowlist.

### ORIGINAL v1
- clean-room Blender initializer;
- clean procedural scaffold generator;
- deterministic scaffold guards:
  - 3,890 vertices;
  - 7,280 triangles;
  - 53 clean historical reference bones;
- ORIGINAL v1 movement-envelope plan;
- canonical v4 ORIGINAL rig plan;
- data migration map.

### Software runtime
- first-party observable store implementation;
- three editor stores migrated away from direct Zustand imports;
- focused store tests;
- verified dependency usage map;
- first-party software migration architecture.

### First-party math
Prepared but **not yet connected to production**:
- `src/core/linearMath.ts`;
- vector/quaternion/matrix implementation;
- XZY Euler convention;
- focused mathematical tests;
- parity migration plan.

### First-party GLB
Prepared but **not yet connected to production**:
- `src/core/glbContainer.ts`;
- GLB 2.0 header/chunk codec;
- `src/core/gltfAccessors.ts`;
- typed accessor reader with stride/offset/normalisation support;
- focused tests;
- staged GLB migration plan.

### Standalone guards
- dependency inventory;
- runtime usage scanner;
- provenance marker scanner;
- legacy coupling scanner;
- external runtime resource scanner;
- runtime network/API scanner;
- runtime dependency anti-creep gate;
- source release-readiness gate;
- production-output third-party scanner;
- one-command audit:
  `npm run audit:standalone`
- production-output audit:
  `npm run audit:production`

### One-command verification
`VERIFY_STANDALONE_PREP.bat`

Runs:
- typecheck;
- focused first-party tests;
- full test suite;
- production build;
- anti-creep gate;
- external-resource gate.

## Important generation finding

The prompt-generation architecture is already local and deterministic:
prompt → slots/intent → certified family → definition → validation → bounded
correction.

It does **not** require a hosted LLM/API.

Do not introduce a runtime AI/API dependency later. Make prompt handling smarter
by expanding project-owned grammar, vocabulary and certified movement families.

## What is intentionally still pending

Nothing unverified has been promoted.

Pending laptop/Work execution:
1. resolve the local V15f final benchmark state;
2. run full V15f audit/review and preserve as legacy benchmark;
3. run `VERIFY_STANDALONE_PREP.bat`;
4. fix any isolated-prep compile/test issue;
5. if store migration passes, remove Zustand from package.json/lock and rerun all gates;
6. run `npm run audit:standalone` and preserve blocker counts;
7. generate ORIGINAL v1 clean scaffold in Blender;
8. begin canonical v4 / clean model work;
9. implement Drei → R3F → React → Three migration incrementally.

## Do not repeat

Do not:
- re-investigate whether MakeHuman/legacy character content must be replaced;
- redesign prompt generation around a cloud AI;
- rebuild the Zustand replacement from scratch before testing the prepared one;
- start a generic glTF/rendering engine;
- start ORIGINAL v1 from V15f;
- copy v3 rig coordinates wholesale;
- add a new runtime dependency to simplify migration.

## Usage-saving principle

Use Work for:
- running/repairing prepared code;
- Blender execution/visual review;
- integration and parity testing.

Use ordinary GitHub/chat preparation for:
- plans;
- isolated first-party modules;
- audit tooling;
- manifests;
- deterministic handoffs.

This keeps expensive Work usage focused on things that genuinely require the
laptop/runtime/Blender.
