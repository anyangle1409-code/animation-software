# Landmark evidence and saved-failure localization — 23 October 2026

All three hash-pinned reconstructions were opened on new read-only copies in run39935614546 at6877b5926bd656ade9db804fe7618895fbb03a78. No Blender file was saved. All source/copy before/after hashes remained identical.

Existing non-sided landmark identities used: LM_sternum__ij_skin (anterior), HGPT_JOINT_disc_t1_t2 (posterior spinal reference), LM_frontal__vertex_skin (superior), HGPT_JOINT_disc_l5_sacrum (inferior). Superior is head vertex minus lumbosacral disc; anterior is sternum IJ minus T1/T2 disc projected perpendicular to superior; anatomical-left direction is superior cross anterior. Measured left unit vector is [1,-2.7721075963687246e-15,-4.998507863721762e-15] for all3, effectively world+X. Exact existing landmark coordinates and projections are preserved in LANDMARK_FRAME_EVIDENCE_20261023.json.

| Candidate | Landmark-frame measurement | Six measured runtime pairs | Review / attachment |
|---|---|---|---|
| W8 | PASS: +X geometric anatomical-left direction | upperarm/forearm/hand/thigh/shin/foot: runtime _r on LEFT, _l on RIGHT | Independent visual landmark review NOT_GRANTED; attachment BLOCKED |
| v14 | Same measured evidence | Same six-pair mapping | Same blockers |
| R120 experimental | Same measured evidence | Same six-pair mapping | Same blockers |

This supports F-SIDE-001 from actual coordinates rather than trusting suffixes. It does not automatically map every other bone/group, approve the source landmark identities, certify anatomical accuracy, or create reviewed muscle bindings. No new landmark or anchor was created. Existing landmark identities and their placement still require independent visual review before binding approval.

W8 full diagnostics artifact12489875422 was separately downloaded and ZIP SHA256 checked:6853e820ac3431cc59cd4ea90a161d52e6c1b192a5e5aaec95c313d1f257aa3b. Its press stretch maximum3509 occurs at sample6,t=0.75; press collapse173 and intersections441 at sample8,t=1. Squat collapse34 at sample7,t=0.875; stretch973 at sample8,t=1; maximum2687intersection pairs already at sample0,t=0. These are benchmark sample indices, not Blender timeline frames. V14/R120 sample-level maxima and literal dominant-weight group classes are in SAVED_REPORT_LOCALIZATION_20261023.md. Dominant weight labels do not prove anatomical causation. Actual triangle/vertex IDs and matching native pose views are still needed for spatial diagnosis; no repair location is approved.

The grip error message is broader than its wording: acceptance requires <=5 thumb/finger skin-pair intersections AND zero collapsed hand triangles below0.1rest area. All trials were rejected in the recorded solver search. The logs do not distinguish which condition rejected each trial; no exact causal diagnosis or anatomical-thumb defect is inferred. Neither condition was relaxed. See GRIP_SOLVER_LIMITS_20261023.txt.

Preservation remains PASS. Archive equivalence remains FAIL/NOT_ESTABLISHED; movement quality FAIL; original-session files and their saving version UNKNOWN; muscle attachment BLOCKED pending accepted source content, reviewed landmarks and explicit user approval. No geometry, weights, correctives, validated skeletal data, production asset, ORIGINAL_v1 or PT_MODEL_VERSION1.0 changed.
