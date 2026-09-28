# React Three Fiber migration — completed source transition

## Status

**Completed for operational source. Supporting historical record only.**

Verified completion checkpoint:

`fba111978563a09dc991bb79b341f1bd9164ee14`

Subsequent verified work continues on the first-party viewport.

## Completion state

- live viewport: `FirstPartyViewportHost`
- `R3FViewportHost.tsx`: removed
- `@react-three/fiber` source imports: 0
- `@react-three/drei` source imports: 0
- R3F/Drei import ceilings: 0
- first-party host is the sole live viewport path
- rollback path removed
- automated Chromium parity/smoke passes
- real WebGL + real exercise-frame driving verified through project-owned host/runtime
- scene pointer routing, orbit, camera, stage, frame scheduling and scene object ownership are project-owned

## Package note

The R3F and Drei packages remain declared temporarily while the separate physical desktop/iPhone Grid/Orbit/Transform gate is open. This does **not** authorize source imports to return.

Package retirement must preserve install/peer consistency and follow the current handoff.

## Current work

Do not continue migration work from this document.

Current software migration is React/ReactDOM:

`docs/REACT_FIRST_PARTY_MIGRATION_HANDOFF.md`
