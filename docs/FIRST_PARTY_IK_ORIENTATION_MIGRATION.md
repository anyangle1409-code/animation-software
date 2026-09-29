# First-party IK orientation migration

## Status

This migration is complete at the production-source boundary.

Prepared and retained:
- `src/ik/firstPartyOrient.ts`
- `src/ik/firstPartyOrient.parity.test.ts`

Production `src/ik/orient.ts`, `src/ik/twoBone.ts`, and `src/ik/solve.ts` now execute the live IK orientation/solve path through project-owned `HgVec3` / `HgQuat` and `HgPoseEvaluation` math with no direct Three source import.

Completed pieces include:
- joint-limit clamping;
- rest-world orientation;
- analytic XZY swing;
- one-axis elbow/knee hinge solve;
- two-bone target/pole triangle geometry;
- hinge-twist / mid-flexion solve;
- end-bone aim and roll;
- goal derivation from FK;
- aim residual measurement and tibial settling;
- ball-foot / toe-out placement and contact residual.

Pinned regression fixtures cover representative arm/leg solved rotations, target residuals, end aim and ball-foot behaviour. Existing exercise/contact suites remain the authority for biomechanics.

## Verified checkpoint

Exact SHA `dd20158a0f557be0c66bf07ce59605f8593147ad`:

- typecheck PASS;
- 148 test files passed, 2 skipped;
- 976 tests passed, 62 skipped;
- production build PASS;
- standalone/hygiene/dependency/resource/network gates PASS;
- automated Chromium viewport smoke PASS.

## Continuing rule

IK thresholds, anatomical limits, exercise data and contact tolerances are frozen through the remaining Three migration. Do not reopen the IK implementation merely to reduce dependency counts.

The next runtime migration boundary is the remaining constraint/equipment transform math named by `docs/CURRENT_HANDOFF.md`.
