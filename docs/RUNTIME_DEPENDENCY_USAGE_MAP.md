# Runtime dependency usage map

## Authority

This document describes durable migration boundaries. It does not freeze live import counts.

For the exact current task use `docs/CURRENT_HANDOFF.md`.

For live source counts run:

```bash
node scripts/map-third-party-runtime.mjs
```

## Declared runtime packages

The branch still declares:

- `@react-three/drei`
- `@react-three/fiber`
- `react`
- `react-dom`
- `three`

Direct Zustand is removed.

A declared package is not evidence of a live source dependency; source import ceilings and production-output gates are separate.

## R3F / Drei

Operational source imports for both are **zero**.

The live viewport is project-owned and the R3F rollback path is removed.

Both packages remain temporarily because the explicit physical desktop/iPhone Grid/Orbit/Transform gate for Drei is still open and the packages share the peer ecosystem. Source imports may not return.

## React / ReactDOM — active source migration

React currently supplies editor/scene composition lifecycle and the ReactDOM root.

Already moved outside React:

- observable Studio store core
- keyboard shortcut controller
- editor layout state
- WebGL/canvas/frame/pointer viewport runtime
- scene-host binding types
- substantial scene geometry/update/pointer logic

Current task-specific handoff:

`docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md`

Target:

- project-owned DOM creation/update/disposal;
- direct store subscriptions;
- explicit browser event lifecycle;
- project-owned scene controller;
- preserved editor/viewport behavior.

## Three.js

Three remains the final large migration target and stays last.

It still supplies significant math, rig/IK helpers, scene objects/materials, camera/raycasting, GLB integrations and final WebGL rendering.

Prepared first-party foundations already exist for math, skeleton/pose parity, GLB building and lifecycle.

## Required order

1. R3F source migration — **complete**.
2. React/ReactDOM source and UI/lifecycle migration — **current**.
3. Complete physical gate and retire Drei/R3F packages when install/peer behavior is safe.
4. Three.js replacement last.
5. Run final provenance, production-output, release-allowlist and offline gates.

## Non-negotiable rules

- no replacement third-party runtime framework;
- no exercise/biomechanics changes to make migration easier;
- no dependency removal before behavioral/parity requirements are met;
- no test or provenance threshold weakening.
