# Current handoff

## Start here

Active branch: `work/standalone-first-party-audit-20260927`.

Latest fully verified implementation checkpoint:
`66684f9e73ea7db931e4c5573bf80f7a2e1c40bf` — first-party runtime dependency migration remains complete, canonical-v4 ORIGINAL is safely in guarded shadow mode, and deterministic prompt generation now covers all 16 core movement families and all 28 exercises currently registered in the first-party library.

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

## Canonical v4 ORIGINAL runtime compatibility

`hgpt_canonical_v4_original` now clears the automated shadow-runtime
compatibility gate across the full exercise library: there are **no remaining
v3 PASS -> v4 FAIL automated review-gate regressions**.

The compatibility work kept authored exercise biomechanics and acceptance
thresholds intact. Adaptation is confined to deterministic runtime/generation
boundaries where body proportions legitimately differ:

- exact floor contacts are resolved in the active rig's foot frame;
- exact/reached IK contacts are not failed merely by floating-point reach noise;
- rigid two-hand grip sockets are calibrated at runtime without scaling equipment;
- equipment-locked root height is solved from active arm geometry;
- pitched floor-supported roots preserve authored knee geometry on active leg
  proportions;
- calf-rise root travel is derived from the active ankle-to-ball lever;
- pelvis-pivot endpoint paths are preserved across canonical proportions;
- arm IK preserves shoulder-relative direction and elbow flexion against active
  upper-arm/forearm lengths;
- the ORIGINAL-v1 packaged asset seam remains dormant and restricts its reviewed
  browser resource read to the two exact product-relative production paths.

This proves deterministic engine/rig compatibility only. It does **not** approve
the current O4/O7 character or close Blender deformation/anatomy/garment review.

## Verification at 66684f9e

GitHub Actions on exact SHA
`66684f9e73ea7db931e4c5573bf80f7a2e1c40bf`:

- clean typecheck: PASS;
- focused first-party foundations: **86 files / 245 tests passed**;
- full suite: **189 files passed, 2 skipped; 1,183 tests passed, 62 skipped**;
- canonical-v4 ORIGINAL shadow-runtime review compatibility: PASS;
- production build: PASS;
- standalone aggregate audit: PASS;
- production-output third-party gate: PASS;
- repository hygiene / prepared first-party foundations: PASS;
- final-character runtime-path gate: PASS;
- runtime dependency anti-creep gate: PASS;
- external runtime resource gate: PASS;
- runtime network/API gate: PASS;
- automated Chromium first-party viewport smoke: PASS.

The runtime-network audit permits no remote host/API exception. Its only reviewed
dynamic browser resource-read seam is the dormant ORIGINAL-v1 packaged loader,
restricted to the exact production-relative paths frozen by
`ORIGINAL_V1_RUNTIME_CUTOVER_CONTRACT.json`.

The automated browser smoke does **not** close the required real desktop/iPhone
physical visual/input parity gate.

## Verified prompt-generation expansion

The deterministic local prompt pipeline now covers **all 16 core movement
families** and all **28 exercises currently registered in the first-party
library**.

The final core-family work added the existing project-authored cable rotation
and anti-rotation motions:

- `exercise: cable woodchop` -> the accepted high-to-low cable woodchop;
- `exercise: Pallof press` -> the accepted standing cable Pallof press.

The remaining two registered library variants were then exposed without new
motion math:

- `exercise: dumbbell calf raise` -> the existing loaded calf-family variant;
- `exercise: cable triceps pushdown` -> the existing straight-bar pushdown
  variant in `extensionFamily`.

Both of those variants pass the same clean first-party body/equipment/IK/
technique validation path with no skipped body checks. No validation threshold
or global timeout was increased.

`src/generation/libraryCoverage.test.ts` now makes complete current-library
coverage an invariant: every registered exercise must belong to exactly one
generator family, and `exercise: <its product-facing name>` must parse back to
that exact library reference. A future library exercise therefore cannot be
added silently without a deterministic prompt path.

The clean-fallback support gate initially measured the flat-bench pad at
**3.04 mm** from the body against the existing **3.00 mm** contact limit. The
family bench was lifted by **0.1 mm**; no validation threshold was changed.
After that correction the all-family clean-fallback generation suite passed,
including equipment/body clearance.

See `docs/STANDALONE_GENERATION_AUDIT.md` for the current generation boundary
and evidence.

## What is still open

Runtime dependency removal is complete. The overall product/release is **not**
complete because separate asset and acceptance gates remain:

### Canonical v4 runtime status — guarded shadow

Canonical v4 is **not** the live runtime default yet.

- the accepted v3 humanoid remains the live `canonicalSkeleton`;
- `hgpt_canonical_v4_original` remains explicitly testable through the shadow
  compatibility suite and keeps all proportion-adaptation work completed so far;
- a 2026-09-30 v4 activation attempt was rolled back after the full verification
  suite exposed v3 parity regressions and remaining v4 technique regressions;
- activation is permitted only when the v3 parity suite, full repository suite,
  browser smoke, and v4 shadow behavioural compatibility all pass on the same
  exact commit;
- the procedural first-party character remains the live/default character;
- ORIGINAL v1 production GLBs remain dormant and unapproved.

The rollback preserves the v4 code/data and compatibility work; it only prevents
an unverified rig cutover from becoming the operational default.

A later v4 reactivation attempt was also rejected by the exact full-suite gate:
at the active-v4 state the focused v4/parity checks could be made green, but the
full suite still produced **140 failures** across authored family geometry,
contacts, grips, equipment and legacy-coordinate invariants. Commit
`5d63e7eb07f9b8340cfad8d0360e953346a725e0` restored the verified shadow
runtime without discarding the decoupled authoring-reference or v4 compatibility
work. Do not reactivate v4 by changing parity expectations; the actual full
behavioural suite must be green first.

1. **ORIGINAL v1 production character**
   - The isolated model branch `claude/original-v1-blender-o2-20260929` has
     progressed beyond O2 to an independently authored O4 bound candidate.
   - Latest isolated model-branch HEAD observed while this handoff was updated:
     `f5f4913a4a2f6525e252ba8b1d15883c6de5d426`.
     The model branch's own `docs/CURRENT_HANDOFF.md` and
     `docs/ORIGINAL_V1_HIGH_DETAIL_MASTER_PLAN.md` remain authoritative for
     Claude's current Blender execution node; do not infer Blender completion
     from this runtime handoff.
   - The machine-readable candidate-status verification remains anchored by the
     successful validation batch around `7d35754677f48414dc9fa5ff5511f422bd79af50`
     / status-recording checkpoint `bb0cef0d869ea7ff7544c6e23bf5b7b61465c0e2`.
     Later model-branch commits preserve future GLB extras and document the
     production grip-metadata gate; they do not make the current candidate
     production-approved.
   - Candidate bare/dressed GLBs pass structural/self-contained audits, but
     they are **not production-approved**.
   - The standalone runtime contains and tests the same 63-bone
     `hgpt_canonical_v4_original` architecture in guarded shadow mode.
     The live default remains v3 until full cutover verification is green;
     this does not bypass any model/deformation gate.
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

1. Keep the zero-dependency/import ceilings, canonical-v4 shadow-runtime gate
   and first-party regression gates active; do not restart completed framework,
   Three or v4 compatibility work.
2. Continue cloud/repository work on release/offline/prompt-generation
   acceptance evidence that can be proved in CI without pretending to close
   physical-device or Blender gates. Core-family and current-library prompt
   coverage are complete. The next safe generation work is deterministic
   language/intent breadth for already-certified biomechanics (tested aliases,
   synonyms and clearer disambiguation), while keeping genuinely new movement,
   support, grip, side or equipment variants blocked until they gain their own
   family-level validation evidence.
3. When a laptop is available, continue the isolated model branch from
   `docs/ORIGINAL_V1_O4_DEFORMATION_HANDOFF.md`: repair **Priority 1 shoulder
   deformation** first, regenerate the targeted evidence, and clear its owned
   development blockers without regression before moving to Priority 2 hands/grip.
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
