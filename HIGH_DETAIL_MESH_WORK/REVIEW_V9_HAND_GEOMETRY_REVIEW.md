# V9 hand geometry review — not accepted

V8 remains the accepted knee geometry baseline. V9 is a separate hand-only
review candidate. It is not a production asset and the grip has not been refit.

## Files

- Dressed: HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review.glb
  (SHA-256 e8c9c936fe971e3b6ac952970604d51bd7ae2bd0cd49ee0cea640edf96ddf4ac)
- Bare: HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review_BARE.glb
  (SHA-256 b9cb40233c183f63ec853ea3bdf5e931b81eb57dd128b03c99b4de4710801ea7)
- Editable: HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review.blend
  (SHA-256 9e9ce76dcfc36264981bbaf4e2bfb5df09e633055608f3a156adc86c46fc4af8)

## Geometry and preservation

V9 uses the V8 GLB as its exact source. The body retains 33,089 vertices and
62,961 triangles. A symmetric, bounded surface sculpt adjusts finger joint
pads and distal taper, thumb web/base, palm pads and wrist transition. The
largest rest-position displacement is 1.751 mm; 3,932 hand vertices changed.
The 682 protected push-up contact vertices and all non-hand vertices are
unchanged. The GLB JSON, rig, inverse binds, weights, UVs, indices, materials,
other binary data and animation definitions are identical to V8; only body
hand POSITION/NORMAL data changed. See reports/verify_v9_hand_scope.json.

The first added-vertex smoothing pass caused dark wrist/finger slits and was
rejected. A second pass without smoothing avoided those slits but was too
subtle. The reviewed pass also moves eligible original hand vertices while
preserving the protected floor vertices. A smoothing trial on that pass again
introduced wrist seams and was rejected.

## Validation

- Candidate structural quick check: pass.
- Five focused guards against runtime source 614033b: pass.
- Seven exercises, 26 frames each: pass; exact bone and equipment matrix
  agreement, closed loops, no technique or reachability violations.
- Push-up minimum hand-floor height: identical on both sides at every sampled
  frame.
- Strict 682-vertex floor guard: pass.
- V8/V9 scope verifier: pass; zero non-hand position changes.
- Dressed/bare posed equivalence: pass.
- Curl grip metrics are unchanged from V8. They have not been optimized
  for V9, as requested.

## Visual review

Matched baseline/candidate closeups are in renders_v9_hand_geometry_review:
dumbbell_bicep_curl_bottom_*_hand.png,
push_up_bottom_*_hand.png, and
pull_up_peak_*_hand.png / *_hand_back.png.
For pull-up review only, the obstructing vertical rack supports are hidden;
the horizontal grip bar and all pose/equipment data are unchanged.

The result is seam-free in the inspected curl and push-up views, but its
visible improvement is modest. The inherited polygonal finger tips, blocky
thumb/web and wrist bands remain. It should not be marked as finished
realistic hand anatomy or used to start grip refitting without visual review.
Substantive hand retopology and sculpting in Blender are the next candidate
side approach if the current appearance is insufficient.

## Promotion status

Review only. V7/V8 are preserved. No production asset, reference, rig,
exercise mechanic, grip offset, or equipment lock was promoted or changed.
