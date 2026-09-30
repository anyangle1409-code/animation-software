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

### Canonical v4 runtime status — active

The runtime rig cutover has now moved beyond shadow validation:

- `hgpt_canonical_v4_original` is the live `canonicalSkeleton`;
- the historical v3 humanoid rig is no longer reachable from `src/main.ts`;
- the full v4 shadow compatibility suite cleared every v3→v4 automated
  review-gate regression before activation;
- the procedural first-party character remains the live/default character;
- ORIGINAL v1 production GLBs remain dormant and unapproved.

This is a **rig activation only**. It does not promote the O4/O7 character
candidate, change the ORIGINAL-v1 promotion contract, or authorize release.

1. **ORIGINAL v1 production character**
   - The isolated model branch `claude/original-v1-blender-o2-20260929` has
     progressed beyond O2 to an independently authored O4 bound candidate.
   - Verified model-branch checkpoint:
     `bb0cef0d869ea7ff7544c6e23bf5b7b61465c0e2`.
   - Candidate bare/dressed GLBs pass structural/self-contained audits, but
     they are **not production-approved**.
   - The standalone runtime now already uses the same 63-bone
     `hgpt_canonical_v4_original` rig architecture; this removes v3 runtime
     coupling but does not bypass any model/deformation gate.
   - Deformation remains blocked: **54 development checks / 133 production
     checks** at the pinned R2 baseline; current repair priority is
     **1 — shoulder/upper torso**.
   - On the model branch, use `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`.
     The O2 handoff remains provenance/setup history, not the current repair task.
   - Historical V8–V15f material remains reference-only: lessons/failure modes
     may be used, but no geometry, weights, bind data, materials or other
     implementation data may be copied into ORIGINAL v1.
   - Do not claim the final character is finished from cloud CI.

2. **Original production garment**
   - An independently authored O7 shorts **candidate** now exists on the
     isolated model branch.
   - It records no legacy/third-party garment, texture or external-material
     source, but garment deformation/visual review and production approval
     remain open.

3. **Physical viewport parity**
   - Real desktop and iPhone Safari evidence remains open.
   - Use `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.
   - This is now a release-quality visual/input gate, not a dependency-removal
     prerequisite.

4. **Final offline / generation / release acceptance**
   - Keep `docs/OFFLINE_STANDALONE_ACCEPTANCE.md`,
     `docs/STANDALONE_GENERATION_AUDIT.md`,
     `RELEASE_ASSET_ALLOWLIST.json`, `ORIGINAL_V1_PROMOTION_CONTRACT.json`,
     and `npm run audit:release` authoritative.
   - `scripts/audit-original-v1-promotion.mjs` now guards the promotion seam:
     while approval is blocked, production GLBs, production hashes, release
     allowlisting and component approval must all remain absent.
   - Never merge the model branch wholesale. Final promotion must pin one exact
     approved model-branch commit plus exact production asset SHA-256 values and
     copy only the approved artifacts/evidence.
   - Final release remains deny-by-default until the required production assets,
     physical evidence, prompt-generation behaviour and offline acceptance pass.

## Next exact deterministic work

For cloud/repository work, do not restart completed framework/Three migration.

1. Keep the zero-dependency/import ceilings and first-party regression gates
   active while improving the remaining release/generation acceptance evidence.
2. Work only on release/offline/prompt-generation items that can be proven in
   repository/CI without pretending to close physical-device or Blender gates.
3. When a laptop is available, continue the isolated model branch from
   `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`: repair Priority-1 shoulder
   deformation first and use the grouped regression checks before moving on.
4. Keep `ORIGINAL_V1_PROMOTION_CONTRACT.json` in
   `blocked_pending_approval` mode until all model/garment/runtime gates pass.
   Do not copy candidate GLBs into `public/characters/`.
5. Separately collect real desktop/iPhone evidence using
   `docs/PHYSICAL_VIEWPORT_PARITY_HANDOFF.md`.
6. Promote assets or release status only after their explicit gates pass.

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
