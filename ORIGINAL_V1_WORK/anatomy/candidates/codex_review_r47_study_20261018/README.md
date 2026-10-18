# R47 inward arm-root and upper-side shape study

Status: UNSAVED_SHAPE_STUDY_NOT_ACCEPTED. Model saved: false. Owner visual review pending.

The owner approved the cyan whole-outline proposal and broader skin scope on18October at19:05 Europe/London. R47 authors an inward side-cap envelope directly in S7, without a long fit. It starts from immutable R41; R46 is the visual comparison. No reference photo or traced outline is in the repository.

New allowed area: local shoulder-side/proximal upper-arm and upper-flank skin. Skin classified as distal (at least0.16m from the shoulder along the humerus) at ANY original key remains fixed at EVERY source key; fade begins at0.12m.166, fixed anchors, centre seam, skeleton, Basis, weights, topology, HGPT_SHOULDER and all non-S7 keys remain protected. Original source and dense45mm caps stay in force.

The author scope regression first failed on the old locked mask, then passed. A stronger any-angle distal preservation assertion caught0.109mm leakage and passed after the global distal mask was applied. Four own scope tests are required. In-memory protected identity: {"basis": true, "bones": true, "groups": true, "non_s7": true, "weights": true}.

All83 native responses passed: False; new contact records: 468.
Back acceleration excess: 3.556961mm against unchanged0.5mm.
Posterior crease excess: 179.212928degrees against unchanged2degrees.
13 benchmarks passed: False; regression records: 8.
Test exit codes (zero passes): {"r37_contour_test_exit.txt": 0, "r38_marks_test_exit.txt": 1, "r41_front_test_exit.txt": 1, "r41_line_test_exit.txt": 1, "r42_profile_test_exit.txt": 1, "r43_back_surface_test_exit.txt": 1, "r43_motion_test_exit.txt": 1, "r47_scope_test_exit.txt": 0}.

No existing test was edited. The historical R42 outward-fill and R41 proximal-arm line targets are still executed and retained; their interpretation conflicts with the owner's newly approved inward skin scope. They are not falsely labelled passed. All area/contact/orientation, front, motion, crease and benchmark failures remain visible. This is a shape review study, never a model acceptance or a saved production candidate.

Review R46_R47_full_outline.jpg, R46_R47_marked_l/r.jpg, R46_R47_press_comparison.mp4 and shoulder_press_r47.mp4. These are actual native Blender5.2.1 geometry, same poses/cameras/lighting. No cosmetic image correction is used.
