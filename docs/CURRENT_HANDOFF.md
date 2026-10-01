# Current handoff

> **MODEL BRANCH PICKUP — 2026-10-01:** On `claude/original-v1-blender-o2-20260929`, read `docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md`, `ORIGINAL_V1_HIGH_DETAIL_STATUS.json`, `docs/ORIGINAL_V1_DAILY_STATUS.md` and `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`. Run `RUN_ORIGINAL_V1_SESSION_PREFLIGHT.bat`; next is the existing r30/o22 experiment from verified r29. `docs/ORIGINAL_V1_PRODUCTION_CONTROL_QUICKSTART.md` gives the exact sequence. R2 remains pinned; production approval is false. Review snapshots are non-blocking by default. The runtime checkpoint below belongs to its separate branch and is retained as history on this isolated model branch; do not use it to restart O2 or shoulder exploration.

## Start here

Active branch: `work/standalone-first-party-audit-20260927`.

Latest fully verified implementation checkpoint: `dd20158a0f557be0c66bf07ce59605f8593147ad` — IK solve/orientation, lightweight constraint/contact math, and equipment reflection now use project-owned math/data rather than Three. Exact-SHA `Standalone prep verification` and `Browser viewport smoke` both passed.

Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md`, `docs/DECISION_LOG.md`, and `FIRST_PARTY_COMPONENT_MANIFEST.json`, then the current Three migration documents. Current source/tests and exact remote HEAD supersede old instructions.

## Verified runtime migration state

The React/R3F source migration is complete: direct `react`, `react-dom`, `@react-three/fiber`, `@react-three/drei`, and `zustand` production-source imports are all **0**. No production TSX remains. Their retained package peer ecosystem still awaits the physical device package gate.

The previous mapper baseline was **71** direct `three` / `three/examples` production-source imports. Eight verified source-import boundaries have since been removed — `src/ik/twoBone.ts`, `src/ik/solve.ts`, `src/ik/orient.ts`, `src/constraints/points.ts`, `src/constraints/locks.ts`, `src/constraints/contactDiagnostics.ts`, `src/constraints/rules.ts`, and `src/equipment/mirror.ts` — so the live count is **63**. Declared runtime packages remain `@react-three/drei`, `@react-three/fiber`, `react`, `react-dom`, and `three` (5). Final standalone readiness remains open.

Production first-party boundaries now include:

- `src/core/linearMath.ts`: project-owned vector, quaternion and matrix math with parity tests.
- `src/rig/pose.ts`: pivot-aware pose blending uses first-party math.
- `src/rig/skeleton.ts`: production FK is computed by `HgSkeleton` / `HgPoseEvaluation`; Three objects remain only as compatibility facades for unmigrated callers.
- `src/ik/orient.ts`, `src/ik/twoBone.ts`, and `src/ik/solve.ts`: production orientation, two-bone triangle/pole geometry, hinge twist, end aim, goal derivation, tibial settling and ball-foot placement are first-party and have no direct Three source import.
- `src/constraints/points.ts`, `locks.ts`, `contactDiagnostics.ts`, and `rules.ts`: point resolution, contact locking/anchors, contact residual diagnostics, and technique-rule geometry are first-party and have no direct Three source import.
- `src/equipment/mirror.ts`: reflected placement math is project-owned and preserves the caller's matrix object type without importing Three.

Still Three-dependent runtime surfaces include:

- `src/constraints/collision.ts` and `src/constraints/bodyClearance.ts`;
- equipment attachment/socket/cable/two-hand transform math in `src/equipment/attach.ts`;
- character deformation, imported-character and retarget-contact transforms;
- retargeting import/retarget transforms;
- export clip baking / rig building / GLB import-export, including `GLTFLoader` / `GLTFExporter`;
- viewer scene objects, camera/raycasting and final WebGL rendering, including `src/viewer/threeSceneHost.ts` and the Three-backed portion of `firstPartyViewportRuntime.ts`;
- compatibility facades in `src/rig/skeleton.ts` until all downstream callers migrate.

First-party GLB container/accessor/builder groundwork exists but is not yet the operational reader/writer.

## Verification at dd20158a

GitHub Actions on exact SHA `dd20158a0f557be0c66bf07ce59605f8593147ad`:

- typecheck: PASS;
- full suite: **148 files passed, 2 skipped; 976 tests passed, 62 skipped**;
- production build: PASS;
- repository hygiene: PASS;
- final-character runtime-path gate: PASS;
- runtime dependency anti-creep gate: PASS;
- external runtime resource gate: PASS, 0 blockers;
- runtime network/API gate: PASS, 0 blockers;
- automated Chromium first-party viewport smoke: PASS.

The browser smoke is supplementary and does not close the required real desktop/iPhone physical parity gate.

## Next exact deterministic task

Continue S6 without changing authored biomechanics, thresholds or exercise data.

1. Add parity-covered first-party XYZ Euler-to-quaternion support needed by equipment-part transforms.
2. Migrate `src/constraints/collision.ts` to project-owned vector/quaternion/matrix math while preserving signed-distance results and all equipment/self-collision tests.
3. Then migrate `src/constraints/bodyClearance.ts` only where its own math can move without rewriting imported-character mesh APIs.
4. Continue into `src/equipment/attach.ts` in isolated attachment modes (static, hand, two-hand, cable/socket), preserving all existing attachment and grip diagnostics.
5. Retarget/character math follows; S7 operational GLB reader/writer follows engine math stability; S8 renderer follows GLB; Three package retirement is S9 only after live source imports reach zero and parity gates pass.

After every material cut: re-read remote HEAD, run/observe exact-SHA typecheck/full suite/build/audits/browser smoke, and commit only green checkpoints.

## Separate tracks and prohibitions

Physical viewport parity: `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`; real desktop/iPhone evidence remains open before Drei/R3F/React peer-package retirement.

Blender/ORIGINAL v1 O2: `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`; on the laptop run `STANDALONE_STATUS.bat`, then `PREPARE_ORIGINAL_V1_O2.bat`. Cloud CI does not close Blender/anatomy gates.

ORIGINAL v1 plus `hgpt_canonical_v4_original` remains the production character target. `src/body/profileMesh.ts` and `src/character/procedural.ts` are temporary clean first-party fallbacks. Do not mix canonical-v4 rest-geometry changes into Three math migration.

Preserve `archive/pre-makehuman-removal-20260928` / `502adedc9fd5c7ddbee1b74cd0472879de6fb047` for recovery only. Do not restore legacy-derived production paths.

Do not weaken tests, timeouts, parity thresholds, provenance checks, dependency ceilings, release allowlists, resource/network guards or browser assertions. Never force-push or overwrite newer branch work.
