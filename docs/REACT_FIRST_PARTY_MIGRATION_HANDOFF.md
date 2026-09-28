# React / ReactDOM first-party migration — completed source-transition record

Branch: `work/standalone-first-party-audit-20260927`

Verified completion checkpoint:

`431a20e4fcb7f470951f1a4be618fd23ded8bb71`

## Result

React/ReactDOM no longer own any production source surface or application lifecycle.

Verified at the completion checkpoint:

- direct `react` source imports: **0**
- direct `react-dom` source imports: **0**
- direct `@react-three/fiber` / `@react-three/drei` source imports: **0**
- React/ReactDOM source-import ceilings pinned to zero
- all editor panels, Toolbar, Timeline and shell are project-owned DOM/controllers
- viewport host/canvas lifecycle is project-owned
- project-owned startup mounts `#root` directly
- keyboard binding/disposal is plain TypeScript
- React store-hook compatibility adapters are removed
- browser smoke imports `storeCore` directly
- no production TSX remains; startup is `src/main.ts`
- Vite no longer loads `@vitejs/plugin-react`
- full suite: **148 test files passed, 2 skipped**
- tests: **968 passed, 62 skipped**
- production build: PASS
- standalone/provenance/dependency/resource/network gates: PASS
- Browser viewport smoke: PASS

## Package-retention boundary

The declared `react` and `react-dom` packages are retained temporarily only because the still-declared R3F/Drei package ecosystem has React peer requirements and the separate physical desktop/iPhone parity gate is still open.

This retention does **not** authorize React source imports. The source ceilings are zero and may not increase.

Do not remove packages merely to reduce a count if doing so would make the retained peer/install state inconsistent.

## Completed stages

- R1 framework-neutral Studio scene controller
- R2 first-party live scene composition / zero R3F source path
- R3 complete project-owned editor DOM shell and every child panel
- first-party viewport DOM/lifecycle switch
- R4 rootless startup / direct keyboard lifecycle
- temporary React store-adapter removal
- final TSX/React Vite-plugin source/config cleanup

## Superseding next task

This document is now a completed migration record, not the operational task handoff.

Continue from `docs/CURRENT_HANDOFF.md`.

The next active software work is:

- `docs/FIRST_PARTY_MATH_PARITY_PLAN.md`
- `docs/FIRST_PARTY_POSE_MIGRATION.md`

Three.js replacement remains last and must proceed through parity-gated math/rig/IK/GLB/rendering layers without changing biomechanics or thresholds.
