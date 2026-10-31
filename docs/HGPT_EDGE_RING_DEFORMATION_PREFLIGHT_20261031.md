# Read-only expanded mesh-ring deformation preflight — 31 October 2026

## Owner finding
User rejected the visible W8/V14/R120 shoulder/axilla and joint deformation as unacceptable. These sources remain unapproved, and no muscle layer may conceal skin defects.

## What was added
- `scripts/cloud_body_analysis/edge_ring_coverage.py` selects deterministic connected mesh-topology rings around *existing exact vertex-ID edge pairs*. It validates all positions, faces, edge presence, degenerate geometry, seed identity and ring depth, returning a face-order topology fingerprint.
- `scripts/cloud_body_analysis/tests/test_edge_ring_coverage.py` has ten synthetic regression cases for topology, IDs, nonfinite coordinates, duplicates, degenerate edges, repeatability, ring membership and approval flags.
- An equivalent checkout of the committed helper and test cases was executed in the isolated chat runtime with Python unittest discovery: **10/10 tests PASS**. This establishes synthetic behavior in that local execution only. No full-repository integration run or GitHub Actions cloud validation is claimed.

## Integration requirements before measuring real W8
1. Load the immutable W8 reconstructed model identified by SHA256 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`, without modifying or saving it.
2. Use the four existing pinned pairs in `scripts/phone_blender/elbow_edge_endpoint_audit.py`. Preserve exact vertex indices, mesh identity and face winding/order. Do not interpret the original suffix names as proven anatomical side.
3. Call `describe` on rest body vertex coordinates and original triangles, initially 1, 2 and 3 topology hops. Record rings and count overlaps between neighborhoods. These are topological neighborhoods and must not be described as the complete elbow.
4. Reuse the same **frozen vertex IDs** at every original row sample for evaluated plain and driven-corrective poses, separately. Require source/evaluated topology equality and no saved model changes. Report per-edge length ratios, within-region distributions and frame-to-frame discontinuity with units and baseline explicitly stated.
5. Generate front/back/side same-camera, same-frame visual evidence for any candidate corrective change. A baseline vs proposed edit should differ in one isolated variable, be reversible and undergo the existing full benchmark guards.
6. Wider anatomically defined region acceptance still requires independent landmark calibration, topology locality and expert review. Do not apply tissue stretch thresholds based on clinical ROM means.

## Current status and limitations
- Four-edge original row ZIP integrity and 36 edge observations verified in draft PR #126's audit; the four edges are not enough to establish anatomical quality.
- New ring preflight: **pure helper and synthetic tests committed**, not yet wired into Blender or cloud CI; no native W8 ring output or correction performed.
- Shoulder/axilla, elbow, groin, knee, ankle and grip movement/skin failures remain open. No model source, weights, rig, pose keys, muscle IDs, PT-App or production code changed. No merge/deployment.
