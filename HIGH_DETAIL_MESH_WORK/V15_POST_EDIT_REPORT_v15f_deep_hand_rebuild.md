# V15f post-edit summary

**Candidate:** v15f_deep_hand_rebuild
**State:** COMPLETE AS LEGACY BENCHMARK; NOT APPROVED FOR PROMOTION

## Automated gates

- PASS - Blender invariants.
- PASS - protected floor guard.
- PASS - frozen `614033b` pipeline.
- PASS - matched review boards.
- COMPLETE - hand seam audit and visual-change metrics.
- INCOMPLETE - optional latest-source integration.

## Geometry and export

- Body vertices: 48,321.
- Body triangles: 93,153.
- New GLTF vertices: 15,232.
- New-vertex maximum lost weight: 0.
- Protected contacts: 682 exact, maximum movement 0 mm.
- Non-hand movement: 0 mm.
- Original skin rows changed: 0.

## Hand topology

V13e to V15f fingertip hole edges remain 0. GLB seam-audit folds over 100 degrees improve from 4 to 2; the full Blender invariant audit reports severe digit folds improving from 3 to 0.

## Visual review

The matched open-hand, closed-fist and exercise boards are present under `renders_v15f_deep_hand_rebuild/`. The visual-change calibration clears the rejected V14e magnitude: median changed-subject area is 0.7012% versus 0.1662% for V14e. This confirms a visible change but does not make V15f a production candidate.

## Current-source integration

The optional latest-source lane is incomplete. The full suite reached 878 passing tests with one unrelated five-second timeout in `src/body/neck.test.ts`. Focused production and V8 scans completed; the long-running V13e scan was stopped. Do not report current-source integration as passing.

## Decision

V15f is preserved as the final imported-lineage legacy benchmark. Do not refit grips, promote it, merge it into the standalone lane, or continue its geometry. See `V15F_LEGACY_BENCHMARK_FINAL.md` for the authoritative final record and hashes.
