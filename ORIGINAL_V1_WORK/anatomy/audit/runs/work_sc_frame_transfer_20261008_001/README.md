# Source shoulder frame transfer — 8 October 2026

Original model body basis differs by 7.8584 degrees from its own four-landmark thorax basis. Passing body XYZ directly as landmark-frame XYZ displaces the source SC point by 1.28585 mm even before any target mapping. The rigid transfer now converts source body point to its landmark frame before applying the target landmark frame. It applies no scale and does not select global anatomy.

Two regression tests first failed on the missing helper; now all six thorax-frame tests pass. Tests cover a tilted original-source frame under a known rigid transform, source-origin subtraction, fixed distance, invalid coordinates and degeneracy. Fresh bpy 5.2.1 LTS quaternion-parent check verifies bilateral signs and coordinates in a synthetic target pose within 1e-7 m. No .blend file or canonical skeleton was created. The first Blender rehearsal used an incorrect repository-parent path; its failure is retained and the path corrected before rerunning.

Full discovery 808 tests: unchanged five failures/four errors relative to the 806-test preceding checkpoint. This validates coordinate transfer and Blender storage math only, not anatomy, contact/follower mechanics or movement acceptance. Source dimensions/stature compatibility and canonical IJ/C7/PX/T8 pose remain unresolved.
