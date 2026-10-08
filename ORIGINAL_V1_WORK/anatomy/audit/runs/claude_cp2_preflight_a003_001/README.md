# CP2 preflight: ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json

**Verdict: FAIL** ({'PASS': 8, 'FAIL': 1, 'UNVERIFIED': 1, 'INFO': 1}).

A full pass is necessary for CP2, not sufficient. UNVERIFIED means the required data does not exist yet; it is never a pass.

| Check | Status | Detail |
|---|---|---|
| `bone_identity_206` | PASS |  |
| `bone_coordinates_finite` | PASS |  |
| `bone_nondegenerate` | PASS | {"shortest_bone": "stapes_left", "shortest_mm": 3.0000000000000027} |
| `parent_tree` | PASS | {"roots": ["hyoid", "sacrum"]} |
| `side_sign_left_plus_x` | PASS | {"largest_midline_offset": "sacrum", "mm": 0.0} |
| `bilateral_mirror_asymmetry` | INFO | {"pairs": 86, "largest_pair": "hallux_distal_phalanx_left", "largest_mm": 0.3808202446156969} |
| `joint_identity_427` | PASS |  |
| `joint_frames_proper` | PASS |  |
| `shoulder_centres_distinct` | PASS | {"sternoclavicular-acromioclavicular_left_mm": 222.85962735242768, "sternoclavicular-glenohumeral_left_mm": 209.59236417610896, "acromioclavicular-glenohumeral_ |
| `spinal_disc_centre_gap_positive` | FAIL | 22 item(s); first: disc_c2_c3: superior body starts 0.00 mm along the inferior body axis (no disc space) |
| `disc_endplate_clearance` | UNVERIFIED | 23 item(s); first: disc_c2_c3: no endplate surfaces |

## What is still missing per region (freeze_ready=False, {'READY': 0, 'PARTIAL': 8, 'BLOCKED': 3})

| Region | Readiness | Bones | a003 placement | Unselected targets | Blockers |
|---|---|---|---|---|---|
| shoulder_girdle | PARTIAL | 4 | surface_landmark 4 | 4 | stature-aware final clavicle endpoint/centreline selection; landmark-compatible 3D scapular envelope and AC/acromion/coracoid placement; absolute SC/AC/GH centres, neutral thorax pose and independent endpoint-matched confirmation remain open |
| spine | PARTIAL | 26 | proportional 26 | 7 | L5-S1 through upper-lumbar 3D endplate/frame chain; thoracic per-level curvature/endplate distribution; cervical neutral family selection and head-over-pelvis check; mixed-method thoracic body/disc reconciliation before exact 3D freeze; independent endpoint-matched lumbar wedge pattern is supported; reconcile posture/sex and contact-envelope definitions before numerical freeze; lumbar middle/edge/normal height and standing/supine disc definitions require geometric reconciliation; CT2026 count and width-plane issues remain open; actual disc-facing endplate envelopes and continuous nonzero clearance over their overlap, not centre-only gap |
| ribs | BLOCKED | 25 | proportional 24, surface_landmark 1 | 3 | reference age/weight selection or explicit envelope; full proximal 2016 logarithmic-spiral reconstruction; verified distal segments are insufficient for complete ribs; 3D thoracic-frame mapping and rib head/tubercle/anterior contact coordinates |
| forearm | PARTIAL | 4 | surface_landmark 4 | 4 | endpoint-compatible canonical radius corridor; endpoint-compatible ulna corridor; revised DRUJ/wrist centre after retarget |
| carpus | BLOCKED | 16 | proportional 16 | 3 | all eight 3D centroids in one canonical wrist frame; intercarpal/radiocarpal contact-centre layout; pisiform line axis and envelope-axis mapping into HGPT |
| hand | PARTIAL | 38 | surface_station 38 | 3 | carpal/wrist layout; exact M2-M4 target values not frozen; thumb CMC local geometry |
| pelvis | PARTIAL | 2 | proportional 2 | 3 | landmark-rich os coxae envelope around retained HJC; SI auricular geometry tied to canonical sacrum/os coxae; pubic symphysis contact and pelvic-ring closure; final sacral width/curvature |
| lower_limb_long_bones | PARTIAL | 8 | proportional 4, regression 2, surface_landmark 2 | 1 | fibula endpoint semantics; patella width/thickness/trochlear contact path |
| tarsus | BLOCKED | 14 | proportional 14 | 5 | bone centroids/envelopes in common frame; subtalar/talonavicular/calcaneocuboid/naviculocuneiform contact centres; TMT base layout |
| forefoot_toes | PARTIAL | 38 | surface_landmark 38 | 5 | M3-M5 stature-aware reconciliation; toe phalanx stature-aware targets; partition of excess surface length across skeletal chain vs soft tissue |
| head_neck_fixed | PARTIAL | 29 | proportional 29 | 3 | cranial/facial envelope target coordinates; mandible full landmark target; independent matched hyoid geometry confirmation, body/cornu 3D landmarks and C3-relative neutral placement/tilt |

Bones without a readiness region: humerus_left, humerus_right.
