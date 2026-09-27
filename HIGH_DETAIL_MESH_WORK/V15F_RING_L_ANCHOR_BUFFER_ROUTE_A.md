# V15f ring_L Route A anchor-buffer analysis

- Candidate: `checkpoints\v15_manual\v15f_deep_hand_rebuild_checkpoint_004.blend`
- Operation: read-only; no geometry was saved
- Decision: **ROUTE_A_SAFE_FOR_ONE_BOUNDED_EXPERIMENT**

## Evidence

- Direct protected ring_L vertices: 7 (movement allowance 0.00 mm)
- Anchor-buffer-only vertices: 390
- Distance distribution: {1: 68, 2: 162, 3: 160}
- Eligible distance-two/three vertices: 322
- Eligible vertices touching or face-adjacent to a >35 degree edge: 136
- Fixed distance-one safety collar: 68 vertices
- Maximum Route A movement: 0.55 mm

The accepted direct-contact set and its skin rows remain exact. The wider anchor group was created by
the V15 preparation script as a four-edge modelling transition; it is not part of the accepted contact
guard. Route A can therefore test only distance-two and distance-three buffer vertices while keeping
the direct set and a one-edge safety collar fixed.

## Movement envelope

- graph distance 0: 0.00 mm (direct contact)
- graph distance 1: 0.00 mm (fixed safety collar)
- graph distance 2: 0.25 mm
- graph distance 3: 0.55 mm

These caps are 2.5% and 5.5% of the existing 10 mm digit-source audit ceiling. The trial must still
prove zero direct-contact movement, zero weight-row changes, exact non-ring geometry, numeric PASS and
a visible improvement in the matched V13e comparison. The full per-vertex classification is in
`reports\v15f_ring_l_anchor_buffer_route_a.json`.
