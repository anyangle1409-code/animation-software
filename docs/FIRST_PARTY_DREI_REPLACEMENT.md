# First-party Drei replacement foundations

The application currently imports only three helpers from \`@react-three/drei\`:
- Grid
- OrbitControls
- TransformControls

Drei itself pulls a much larger transitive runtime tree, including MediaPipe,
HLS, text helpers, BVH utilities and Zustand. Home Gym PT does not need those
features.

## Prepared, not yet wired into production

- \`src/viewer/firstPartyCameras.ts\`
  - project-owned camera preset data using first-party vectors;
  - parity-tested against the current Three camera resolver.

- \`src/viewer/orbitModel.ts\`
  - renderer-independent target/yaw/polar/distance orbit state;
  - 0.6–12 m zoom envelope;
  - current 0.12 damping characteristic;
  - pointer-delta rotation input;
  - reusable later with the first-party renderer.

- \`src/viewer/referenceGrid.ts\`
  - project-owned 12 m reference-grid geometry;
  - 0.25 m cells;
  - 1 m major sections.

- \`src/viewer/transformGizmoMath.ts\`
  - axis translation drag solve;
  - ray/plane intersection;
  - signed rotation drag around an axis.

## Integration order

1. Verify all isolated tests.
2. Replace static camera preset vectors with the first-party camera data.
3. Render \`referenceGrid\` through the existing R3F/Three adapter and remove Drei Grid.
4. Add a small R3F adapter around \`HgOrbitModel\`; verify mouse + iPhone touch rotate/zoom.
5. Add rendered axis handles using \`transformGizmoMath\`; verify:
   - bone rotate;
   - equipment translate/rotate;
   - IK target/pole translate;
   - undo/redo boundaries.
6. Remove all Drei imports.
7. Remove \`@react-three/drei\` from package.json and regenerate the lockfile.
8. Re-run the full suite/build and standalone audits.

## Rules

Do not replace Drei with another controls/gizmo package.

Do not alter exercise mechanics, camera presets, contact logic or joint limits to
make an interaction replacement appear to work.

Drei is a temporary comparison implementation only; the prepared interaction
math remains useful when R3F and Three are removed later.
