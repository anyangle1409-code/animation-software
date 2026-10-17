# R42 owner-confirmed arm-to-body restoration — work in progress

The owner confirmed an annotated older reference: continue the newer arm's line
into the side and turn into the torso earlier, without a separate false joint.
The private photograph and its annotation are deliberately excluded from git.

R41 remains immutable. R42 has not been saved or accepted. The read-only native
export is Actions run 39048442821, artifact 12107030626; ZIP SHA256
6a02e10c14bf843b7c96e184e3c82b5358e86bbaa8a47270e1f96d8c762dd834.
It contains 82 native press responses and the exact 130-degree front response.

## Scope and fixed measurements

Only existing S7 keys 120, 130, 136 and 145 may change on the body side of the
shoulder. Upper-arm/elbow material vertices, controls 110/156/166, front anchors,
Basis, topology, weights, bones and all non-S7 keys remain fixed.

The new profile test is already RED on R41 (eight failures). It measures both
sides at the owner's marked 135.625 degrees against the unchanged R38 arm guide.
All older contour, front, arm-line, area, contact and preservation tests remain.
The 45 mm R42 saved-update bound is specific to restoring the confirmed contour;
it does not replace R41's 0.75 mm strain-only bound or change its tests. The
authored target is at most 36.567 mm in material coordinates, leaving room for a
5 mm redistribution. No acceptance threshold is relaxed to fit a solver result.

## Trials and limitations

Trial 1 locked a broad band behind the visible contour. It stalled near 220
stretched triangles at the marked pose (R41: 19) and was rejected before saving
a model. Trial 2 narrows that lock to the visible 3 mm band, retaining the same
target and acceptance gates. Its result is pending. Predictions are diagnostic
affine responses, not final native Blender validation or owner approval.

Temporary local trial files were lost between sessions. The native export and
branch source survived; trial 2 is being reproduced from those exact inputs.

If feasible, R42 must undergo native guard/preservation, all movement benchmarks,
front, contour, area, orientation and contact checks before acceptance. Delivery
requires native R41/R42 matching back/three-quarter comparisons and a press video.
