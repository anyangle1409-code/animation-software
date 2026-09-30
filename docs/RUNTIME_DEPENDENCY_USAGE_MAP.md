# Runtime dependency usage map

## Authority

For the exact current task use `docs/CURRENT_HANDOFF.md`.

For live source counts run:

```bash
node scripts/map-third-party-runtime.mjs
node scripts/audit-test-three.mjs
```

## Verified state

At exact verified checkpoint
`017a063d2fdf563f58446113816511c1248a843b`:

- declared runtime dependencies: **0**
- `react` operational imports: **0**
- `react-dom` operational imports: **0**
- `@react-three/fiber` operational imports: **0**
- `@react-three/drei` operational imports: **0**
- `zustand` operational imports: **0**
- `three` operational imports: **0**
- `three` test imports: **0**
- `three` and `@types/three` packages: **removed**

The production-output third-party gate and automated Chromium viewport smoke both
pass at that exact checkpoint.

## Live first-party runtime

The active product path is project-owned across:

- editor state and DOM lifecycle;
- math, FK, IK, constraints, contacts and retargeting;
- scene graph, geometry, materials, skinning and deformation;
- local GLB parsing/materialisation/preservation/export;
- equipment geometry and attachment;
- camera/orbit, raycasting, selection and transform gizmos;
- WebGL rendering and viewport composition.

The old React/R3F/Drei/Three migration plans are historical implementation
records, not active instructions.

## Development tools

The project target is distributable/runtime independence, not removal of all
development tooling. Node/npm, TypeScript, Vite, Vitest, Playwright, Blender,
Git/GitHub and AI development tools may remain when they are not shipped as
prohibited runtime code/content.

## Ongoing rules

- no replacement third-party runtime framework;
- no reintroduction of removed runtime packages or guarded source imports;
- no exercise/biomechanics changes to make infrastructure work easier;
- keep dependency/import anti-creep, production-output, resource and network
  audits active;
- keep physical desktop/iPhone parity as a separate release gate;
- keep final production assets subject to their clean-room/provenance gates.
