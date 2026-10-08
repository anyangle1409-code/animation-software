# Independent forearm landmark source review

Reviewed Hong 2021 original article and downloaded its S1 workbook read-only. Matched 132 radius/ulna donor IDs; ID-based sex labels disagree with manuscript totals. Raw length headers use mm2 although manuscript describes mm. No individual stature field was identified; no proportion rescaling or target selection was performed. Download URL and SHA256 are retained in hong_supplement_inspection.json.

Reviewed Thillemann 2021 Methods / Coordinate system and kinematic axis and Figures 4/5. Recorded radial-head to ulnar-head neutral kinematic reference and separately named surface landmarks. The paper is a TFCC lesion/repair experiment, not a normal male stature reference. Its three-point sphere-fitting description needs additional constraints: three synthetic counterexample fits with different centres have zero residual. This is an independent geometry limitation, not an assertion that the authors' software had no extra constraints.

No bone/joint coordinates, Blender files, production assets, runtime drivers or selected numerical lengths changed. Source register/alias scan and target evidence links updated; readiness remains false. Full suite was verified at the preceding 2c8979f9 checkpoint (805 tests, existing five failures/four errors); only affected data/owner-policy/source/readiness checks are rerun here.
