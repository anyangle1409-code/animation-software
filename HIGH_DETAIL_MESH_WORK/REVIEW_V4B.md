# V4B shoulder/axilla review candidate

V4B is a separate dressed and bare test asset. The production files, frozen rig, application source, exercise mechanics, and V1–V3 candidates remain unchanged. V4 was a local test checkpoint; V4B is the better of the two underarm masks and is the revision submitted for review.

## Change

The V3 cap sculpt extended into the medial/front underarm. At the shoulder-press peak, 43 of 224 fixed original axilla edges on the left side compressed below 80% of rest length (frozen: 7). V4 first guarded the medial axilla (25 edges). V4B also tapers the sculpt off the lower anterior underarm (16 edges). The same right-side counts are 41, 25, 16, and 6 frozen. This metric uses the *same original vertex IDs and edges* across every revision; extra subdivision cannot change the sample. The fold remains visible and is not fully repaired.

The external deltoid cap remains within the approved target at curl Bottom: 31.0 mm above the unchanged joint (target 25–35 mm), apex sagittal z −47.4 mm, posterior to the joint at −21.9 mm. Body topology remains 57,721 triangles / 30,311 vertices. The maximum new-vertex four-influence loss remains 4.98%. Original skin weights and all non-position attributes are the same as V3.

## Validation

Six focused checks passed: sagittal shoulder profile; bare/dressed equivalence; grip contact and 343° wrap; renderer/exporter agreement; dumbbell/shorts clearance; and 26 frames in each of curl, squat, shoulder press, push-up and pull-up. The original hand positions, 160 bone matrices, and equipment transforms match the frozen dressed model at every sampled frame. Push-up reach and elbow-flare findings are inherited from the frozen rig. V4B has no degenerate body triangles or edges shared by more than two faces. All 400 pinned source files and the V3 deliverables were verified unchanged; the GLB retains the frozen rig, animation, materials, and binary prefix. See `reports/final_integrity_v4b.json`, `reports/v4b_guard_tests.log`, `reports/v4b_exercise_tests.log`, and `reports/axilla_audit_v4b.json`.

`renders_v4b/V4B_OVERHEAD_REVISIONS.jpg` compares frozen, V3 and V4B at shoulder-press and pull-up peaks. `renders_v4b/V4B_ANATOMY_AND_EXERCISES.jpg` shows body views and all exercise peaks. The underarm still needs dedicated joint-loop topology and local weighting, and the inherited hand/knee anatomy and skin materials need work before any production consideration.
