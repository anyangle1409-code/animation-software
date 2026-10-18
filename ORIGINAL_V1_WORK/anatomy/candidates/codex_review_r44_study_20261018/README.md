# R44 area-bound correction and finer body-field study

Status: REJECTED_NUMERIC_CHECKS. Owner visual review pending; approved=false.
Model saved: False.

R41 is the immutable model baseline; R43 is the previous rejected motion study; R42 supplies the owner-confirmed junction target.
This candidate adds S7 samples96..166 and a clamped cubic body increment. Original
R41 arm/elbow deformation is reproduced by the added baseline samples. Body-side
controls110/156 are now editable; original arm coordinates,166, anchors, bones,
weights, topology, Basis, HGPT_SHOULDER and non-S7 keys are preserved. R42's endpoint
test remains unchanged for R42; R44 has its own explicit preservation and fixed-domain tests.
The optimizer severity cap now applies even when no triangles exceed2x area.
The smooth field has finer controls, within the exact same free material mask.

All83 native responses: passed=True; new contact records=0.
Back second-difference excess: 0.448339mm (limit0.5).
Posterior crease excess: 1.847103deg (limit2).
13 original benchmarks: passed=True; regressions=0.
Test exit codes: {"r37_contour_test_exit.txt": 0, "r38_marks_test_exit.txt": 0, "r41_front_test_exit.txt": 0, "r41_line_test_exit.txt": 0, "r42_profile_test_exit.txt": 1, "r43_back_surface_test_exit.txt": 0, "r43_motion_test_exit.txt": 0, "r44_area_bounds_test_exit.txt": 0, "r44_domain_test_exit.txt": 0, "r44_field_test_exit.txt": 0, "r44_preservation_test_exit.txt": 0}.

The attached comparisons and videos use actual Blender5.2.1 geometry at matching
poses, cameras and lighting. They are review evidence. No private owner photo is
included. Failed checks remain in the JSON and logs; tests were not weakened.
