# Current handoff

## Start here

Active branch: `work/standalone-first-party-audit-20260927`.

Latest fully verified implementation checkpoint: `fa06d26da9e0a99a2aa9d1b2ca9528075b4b5025` — IK hinge-twist math also uses first-party quaternion/vector math. Exact-SHA `Standalone prep verification` and `Browser viewport smoke` both passed.

Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md`, `docs/DECISION_LOG.md`, and `FIRST_PARTY_COMPONENT_MANIFEST.json`, then the current Three migration documents. Current source/tests and exact remote HEAD supersede old instructions.

## Implementation and verification at dd4a7ab

The React/R3F source migration is complete: direct `react`, `react-dom`, `@react-three/fiber`, `@react-three/drei`, and `zustand` source imports are all **0**. No production TSX remains. Their retained package peer ecosystem awaits the physical device gate.

The repository mapper reports **71 direct `three` / `three/examples` source imports**, including type-only imports. This count has not dropped because the converted IK functions retain Three types at their caller boundary. Declared runtime packages remain `@react-three/drei`, `@react-three/fiber`, `react`, `react-dom`, `three` (5). The dependency anti-creep gate passes; final standalone readiness remains open.

Production first-party boundaries:

- `src/core/linearMath.ts`: project-owned vector, quaternion and matrix math with parity tests.
- `src/rig/pose.ts`: pivot-aware pose blending uses `HgVec3`/`HgQuat`.
- `src/rig/skeleton.ts`: rest frames and production FK are computed by `HgSkeleton`/`HgPoseEvaluation`. Three matrix/vector/quaternion objects remain as caller compatibility facades; `firstPartyEvaluation` exposes the live first-party FK to engine callers.
- `src/ik/orient.ts`: rest-world orientation, analytic XZY swing, clamped local swing, and elbow/knee hinge orientation delegate to first-party `src/ik/firstPartyOrient.ts`. Three vector inputs and a quaternion output remain as temporary caller boundaries.
- `src/ik/twoBone.ts`: the internal hinge-twist / mid-flexion quaternion calculation uses `HgQuat`/`HgVec3`, with a frozen solved-rotation fixture. The two-bone triangle and public caller types still use Three vectors.

Still Three-dependent engine paths include `src/ik/twoBone.ts`, `src/ik/solve.ts`, constraints/contact/locks, equipment attachments and mirrors, character/retarget transforms, export baking/GLB, and some editor/diagnostic calculations. `src/viewer/firstPartyViewportRuntime.ts` and `src/viewer/threeSceneHost.ts` still render with Three. The first-party GLB container/accessor/builder groundwork is not the operational reader/writer; `src/export/glb.ts` still uses `GLTFExporter` and import paths still use `GLTFLoader`.

Local verification on `fa06d26` (orientation-only `dd4a7ab` had 970 passing tests):

- focused IK orientation parity and two-bone IK: 12 passed;
- typecheck: PASS;
- full suite: 148 files passed, 2 skipped; 971 tests passed, 62 skipped;
- production build: PASS;
- repository hygiene, final-character runtime path, runtime dependency anti-creep, external runtime resources, and runtime network/API gates: PASS;
- automated first-party Chromium viewport smoke: PASS (`reports/browser-smoke/first-party-host/browser-smoke-first-party.json`).
- GitHub Actions on `fa06d26`: `Standalone prep verification` PASS; `Browser viewport smoke` PASS.

The browser script expects a running Vite server at `127.0.0.1:5174`; launch Vite and the script in the same local execution session. Automated Chromium is supplementary and does not close physical desktop/iPhone parity.

## Next exact deterministic task

After checking both Actions workflows on the exact implementation SHA, migrate the remaining two-bone triangle/pole/target vector arithmetic in `src/ik/twoBone.ts` to `HgVec3` through the live first-party evaluation. Pin solved rotations, effector residuals, poles, limits, contact locks, ball-foot behaviour, tibial settling and end-aim across representative exercises before switching the calculation. Keep the public Three caller contract as a temporary boundary where needed. Do not rewrite `solve.ts` and `twoBone.ts` together or change authored data, thresholds or tolerances. Run focused IK parity, all IK/exercise/contact gates, typecheck, full suite, build, audits and Chromium before another checkpoint.

Then continue controlled S6 migration of `solve.ts`, attachments, constraints, retarget math and export calculations. S7 GLB reader/writer follows engine math stability and fixture round trips; S8 renderer follows the engine/GLB boundary. Three package retirement is S9 only after live source paths reach zero and gates pass.

## Separate tracks and prohibitions

Physical viewport parity: `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`; real desktop/iPhone evidence remains open before Drei package retirement. Blender/ORIGINAL v1 O2: `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`; on the laptop run `STANDALONE_STATUS.bat`, then `PREPARE_ORIGINAL_V1_O2.bat`. Neither physical nor Blender gate is closed by cloud CI.

ORIGINAL v1 plus `hgpt_canonical_v4_original` is the production character target. `src/body/profileMesh.ts` and `src/character/procedural.ts` are a temporary clean fallback. Do not mix canonical-v4 rest geometry changes into Three math migration. Preserve `archive/pre-makehuman-removal-20260928` / `502adedc9fd5c7ddbee1b74cd0472879de6fb047` for recovery only; do not develop on it or restore legacy-derived production paths.

Do not weaken tests, timeout limits, parity thresholds, provenance checks, dependency ceilings, release allowlists, resource/network guards or browser assertions. Never force-push or overwrite newer branch work. Re-read remote HEAD before every commit and reconcile any intervening changes.
