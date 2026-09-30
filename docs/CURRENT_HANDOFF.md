# Current handoff

## Start here

Active branch: `work/standalone-first-party-audit-20260927`.

Latest fully verified implementation checkpoint:
`017a063d2fdf563f58446113816511c1248a843b` — first-party runtime dependency migration complete.

Exact-SHA `Standalone prep verification` and `Browser viewport smoke` both passed.

Read `docs/PROJECT_AUTHORITY.md`, `docs/AI_OPERATING_CONTRACT.md`,
`docs/DECISION_LOG.md`, and `FIRST_PARTY_COMPONENT_MANIFEST.json` first.
Current source/tests and the exact remote HEAD supersede older migration plans.

## Verified first-party runtime state

The shipped/operational software has **zero declared runtime dependencies**.

Guarded source imports are all **0** for:

- `react`
- `react-dom`
- `@react-three/fiber`
- `@react-three/drei`
- `zustand`
- `three`

Three is also absent from development dependencies and tests. The repository-wide
Three inventory reports:

- operational imports: **0**
- test-only imports: **0**

The live product path is project-owned across:

- observable state and editor DOM lifecycle;
- vector/quaternion/matrix math;
- skeleton/FK, IK, constraints, contacts and retargeting;
- scene graph, geometry, materials, skinning and deformation;
- GLB parsing, preservation, animation writing and full export;
- equipment geometry/attachment/export;
- camera/orbit/raycasting/selection/gizmos;
- WebGL rendering and the live viewport.

Do not restore a removed framework or renderer as a compatibility shortcut.

Development tools such as Node/npm, TypeScript, Vite, Vitest, Playwright,
Blender, Git/GitHub, GPT and Claude remain permitted by the frozen product
boundary. They are development tools, not shipped runtime dependencies.

## Verification at 017a063d

GitHub Actions on exact SHA
`017a063d2fdf563f58446113816511c1248a843b`:

- clean `npm ci`: PASS with Three absent;
- typecheck: PASS;
- focused first-party foundations: **84 files / 236 tests passed**;
- full suite: **185 files passed, 2 skipped; 1096 tests passed, 62 skipped**;
- production build: PASS;
- production-output third-party gate: PASS;
- repository hygiene: PASS;
- final-character runtime-path gate: PASS;
- runtime dependency anti-creep gate: PASS;
- external runtime resource gate: PASS;
- runtime network/API gate: PASS;
- automated Chromium first-party viewport smoke: PASS.

The automated browser smoke does **not** close the required real desktop/iPhone
physical visual/input parity gate.

## What is still open

Runtime dependency removal is complete. The overall product/release is **not**
complete because separate asset and acceptance gates remain:

1. **ORIGINAL v1 production character**
   - `HomeGymPT_Male_ORIGINAL_v1` remains in O2+ clean-room authoring.
   - Use `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md`.
   - O2 requires guarded Blender work and human anatomy review.
   - Do not claim the final character is finished from cloud CI.

2. **Original production garment**
   - Final male shorts remain independently authored/reviewed work after the
     appropriate ORIGINAL-v1 body stage.

3. **Physical viewport parity**
   - Real desktop and iPhone Safari evidence remains open.
   - Use `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.
   - This is now a release-quality visual/input gate, not a dependency-removal
     prerequisite.

4. **Final offline / generation / release acceptance**
   - Keep `docs/OFFLINE_STANDALONE_ACCEPTANCE.md`,
     `docs/STANDALONE_GENERATION_AUDIT.md`,
     `RELEASE_ASSET_ALLOWLIST.json`, and `npm run audit:release` authoritative.
   - Final release remains deny-by-default until the required production assets,
     physical evidence, prompt-generation behaviour and offline acceptance pass.

## Next exact deterministic work

For cloud/repository work, do not restart completed framework/Three migration.

1. Keep the zero-dependency/import ceilings and first-party regression gates
   active while improving the remaining release/generation acceptance evidence.
2. Work only on release/offline/prompt-generation items that can be proven in
   repository/CI without pretending to close physical-device or Blender gates.
3. When a laptop is available, follow
   `docs/ORIGINAL_V1_O2_WORK_HANDOFF.md` for guarded Blender O2 work.
4. Separately collect real desktop/iPhone evidence using
   `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.
5. Promote assets or release status only after their explicit gates pass.

After every material code or authority change: re-read remote HEAD, run/observe
exact-SHA typecheck/full suite/build/audits/browser smoke, and keep only green
checkpoints.

## Separate tracks and prohibitions

ORIGINAL v1 plus `hgpt_canonical_v4_original` remains the production character
target. `src/body/profileMesh.ts` and `src/character/procedural.ts` are
temporary clean first-party fallbacks, not the finished production model.

Preserve `archive/pre-makehuman-removal-20260928` /
`502adedc9fd5c7ddbee1b74cd0472879de6fb047` for recovery only. Do not restore
legacy-derived production paths.

Do not weaken tests, timeouts, parity thresholds, provenance checks, dependency
ceilings, release allowlists, resource/network guards or browser assertions.
Never force-push or overwrite newer branch work.
