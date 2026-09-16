# Phase 1 decision — reusable cylindrical power-grip solver

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting HEAD:** `416ca2d13bd03218ca1d7505f971698041af2807`  
**Stage 1 remains frozen. Stage 2 has not started. Do not promote or merge.**

This file authorises the next Phase 1 implementation direction after the corrected grip harness proved that a static closure profile cannot meet the visual and geometric acceptance criteria at the same time.

## Proven current state

The repaired harness is now the source of truth for grip contact diagnostics:

- vertex classification is by **summed skin weight per anatomical group**, not single dominant bone;
- contact uses signed distance to the real **finite capped cylinder**;
- the axial range is the real handle half-length from geometry, not an environment-variable slab;
- every sweep regenerates the posed clip/mesh and carries a posed-vertex checksum so dead sweeps are rejected;
- the same posed vertex set is used by the metric and the high-zoom render;
- left/right results agree and Bottom/Mid/Peak are pose-invariant for a rigidly held handle.

With that corrected harness, the shipped full-fist-looking pose is not acceptable geometry:

- finger penetration is about **11.48 mm over 53 vertices**;
- palm contact is only about **-0.59 mm over one vertex**, which is compatible with firm loaded contact;
- the high-zoom axial render agrees: the hand surface closes through the handle volume.

The earlier conclusion that the palm was the binding constraint is withdrawn.

Static profile tuning has also been exhausted:

- 120 per-joint profiles searched;
- only four were clean, all weak/cupped grips around ~160° wrap;
- the best high-wrap result (~336°) still penetrated by ~10.52 mm;
- moving the handle centre can clear the digits only by unloading/leaving the palm;
- therefore no static angle table + one closure scalar can produce both a visually convincing full fist and non-penetrating finger contact.

Root cause: `applyGrip` is a static angle table scaled by one closure scalar, so digits continue closing after they have reached the handle.

## Decision

Implement a **reusable cylindrical power-grip solver** based on **close-until-contact per digit**.

Do not change finger lengths, MCP locations, topology or skin weights as the first response. Do not accept the ~160° cupped grip as the target. Do not hide the problem by moving the handle away from the palm.

The solver should be the smallest reusable addition that produces the user's approved grip standard:

- handle sits deep in the palm;
- palm remains loaded/contacting naturally;
- index, middle, ring and pinky wrap substantially around the handle;
- proximal and middle phalanges participate, not just fingertips;
- fingertips continue around/under the handle rather than merely touching;
- thumb opposes and locks naturally;
- the result reads as a **fist around an object**;
- no meaningful finger-through-handle penetration;
- no large air gap between palm and handle;
- left/right symmetry;
- neutral/natural wrist for the exercise.

## Solver design constraints

### 1. Solve each finger against the real handle

Treat index, middle, ring and pinky independently enough to stop each digit when its posed surface reaches the real finite handle cylinder.

The solver must use:

- the actual handle axis/orientation;
- real handle radius/diameter;
- real handle half-length / finite end caps;
- character-specific `handleGripOffsets` / hand frame;
- the corrected summed-weight vertex classification from the harness;
- anatomical joint limits.

Do not use an infinite-cylinder approximation for final acceptance.

### 2. Preserve coordinated human finger behaviour

This is not permission to make five robot-like independent digits.

Retain sensible coupling/ordering across MCP/PIP/DIP motion so the hand still closes like a human power grip. Use the existing static profile as the anatomical starting pattern, then stop/limit individual joints or digits at contact.

Prefer the **minimum deviation from the existing accepted finger pose** needed to avoid penetration.

### 3. Thumb is solved separately

The diagnostic found a real sign issue:

- shipped/shared `thumbOppositionX = -14` drives the thumb into the handle;
- `+14` clears the thumb completely in the current character while preserving wrap.

Do **not** globally flip the shared `thumbOppositionX` constant yet because the same value currently affects bar/handle/rope grips in pull-up, press and row.

Instead, let the cylindrical power-grip solution own the thumb behaviour for this grip family:

1. establish thumb opposition/orientation appropriate to the cylindrical handle;
2. then flex the thumb until it locks naturally over the handle/fingers without penetration;
3. keep left/right mirroring correct;
4. verify reused behaviour on a second exercise/handle before locking it.

If the evidence later proves `+14` should become a shared general rule, make that decision only during the cross-exercise validation pass, not by assumption here.

### 4. Diameter-aware reuse

This must be reusable for dumbbells, straight bars and compatible cylindrical handles.

Do not hard-code one joint-angle answer only for the current dumbbell diameter.

Preferred implementation:

- solve/calibrate the grip for the character and handle diameter;
- cache the resulting joint targets by a compact key such as character/grip family/handle radius;
- interpolate or re-solve only when diameter changes materially;
- avoid expensive geometric collision solving every animation frame if the same rigidly held handle can reuse a stable solved grip.

A compact lookup/interpolation path is preferred over per-exercise magic numbers.

### 5. Keep contact frames separate

Do not conflate `gripFrameOffsets` (palm contact frame used by floor/bar locks) with `handleGripOffsets` (held-handle centre inside the fist).

Do not apply the cylindrical closed-fist solver to push-up palm-floor contacts.

Preserve the accepted Stage 1 equipment-pipeline limitation unless this solver produces direct evidence that it causes an actual error.

## Implementation/validation sequence

Use focused diagnostics during iteration; do not run the expensive whole-suite validation on every trial.

1. Implement the smallest reusable close-until-contact mechanism for one hand/one cylindrical handle using the corrected harness.
2. Prove the per-digit result changes the posed mesh and does not rely on a dead/cached clip.
3. Mirror to the other hand and verify numerical symmetry.
4. Solve the thumb for the cylindrical grip family.
5. Validate on curl Bottom, Mid lift and Peak.
6. Reuse the same solver/profile on at least one second cylindrical-handle case, preferably shoulder press and/or pull-up/bar grip, without per-exercise finger magic numbers.
7. Only after the focused grip tests pass, run the relevant grip/equipment/hand-wrist regression tests.
8. If Phase 1 passes, lock the reusable grip and continue automatically with Phases 2–5 from `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`.

## Phase 1 acceptance criteria

Phase 1 may be declared locked only when all of the following are true:

1. high-zoom render reads as a convincing **full-fist power grip**, not a fingertip hook or cupped hand;
2. palm remains naturally loaded against the handle;
3. all four fingers substantially wrap the handle;
4. thumb provides natural opposition/locking;
5. no meaningful finger-through-handle penetration remains under the corrected finite-cylinder metric;
6. no destructive palm/handle separation is introduced just to clear digits;
7. no finger self-intersection or anatomically implausible joint angle is introduced;
8. both hands are effectively symmetric;
9. handle remains correctly centred in the grip and renderer/exporter agreement is preserved;
10. curl Bottom/Mid/Peak remain stable with the retained Stage 1 curl and forearm work;
11. the same grip family works on at least one second cylindrical-handle use without exercise-specific finger tuning;
12. hand/wrist deformation and equipment lock do not regress.

The visual render is the final arbiter when the metric is technically clean but the hand does not read as a human grip.

## Stop conditions

Stop and report rather than forcing a solution if any of these become necessary:

- finger lengths or MCP joint placement must be changed;
- destructive reweighting or topology change is required;
- a clean grip can only be achieved by visibly unloading the palm;
- the solver can only work by adding per-exercise magic numbers;
- the reusable solution breaks existing bar/press/pull-up contact in a way that cannot be isolated safely.

Do not start Stage 2 until Phase 1 is genuinely locked.

## Follow-on decision — controlled proximal handle-centre sweep

Current solver result at branch HEAD `899a9d93bb8ae4f3181a4e2886682b91ab934b81` is **not yet accepted as the final grip**.

The close-until-contact solver itself is retained as the correct mechanism, but the current solved shape reaches only about **240° wrap**. The high-zoom axial render shows an open arc of roughly 120° under the handle: all four digits contact, the palm is loaded, and the thumb opposes, but the fingertips do not finish curling underneath enough for the hand to read as the user's approved full-fist grip.

The measured reason is that every MCP locks early because the character-specific handle centre sits too close to the MCP/knuckle row. This is now authorised as the next controlled variable.

### Authorised test

Perform a **small controlled sweep moving only the character-specific held-handle centre proximally/deeper into the palm**. For every tested centre:

1. re-run the existing close-until-contact solver from scratch;
2. solve all four fingers and the cylindrical-grip thumb behaviour;
3. measure contact using the repaired finite-cylinder harness;
4. render a high-zoom matched view of the resulting grip;
5. record palm loading, finger penetration, wrap, thumb clearance/locking and left/right symmetry.

Do not optimise wrap angle alone. The final arbiter remains the visual target: a natural **fist around the handle**, not a numerical circle-coverage maximum.

### Selection rule

Retain the **smallest proximal handle-centre shift** that simultaneously produces:

- a convincing full-fist / power-grip appearance;
- the handle visibly deeper in the palm;
- all four fingers curling substantially around and under the handle;
- fingertips continuing under the handle rather than stopping at the sides;
- natural thumb opposition/locking;
- a loaded palm with no large air gap;
- no meaningful finger-through-handle penetration;
- no finger self-intersection or implausible joint angle;
- correct bilateral mirroring.

Do not keep moving the handle after those conditions are met just to increase wrap.

### Preserve while sweeping

Do not alter:

- frozen Stage 1 forearm correction;
- frozen curl motion, including the retained +4.3° neutral rebase;
- Stage 1 shoulder state;
- finger lengths;
- MCP locations;
- topology or skin weights;
- the close-until-contact solver mechanism.

Keep the thumb correction character/grip-family specific. Do **not** globally flip the shared thumb constant as part of this sweep.

### Regression checks for the retained centre

Before Phase 1 can lock, re-check at minimum:

- curl Bottom / Mid / Peak / Return;
- Bottom/Return dumbbell-to-thigh clearance;
- shoulder press grip/contact;
- at least one second cylindrical-handle use to prove reuse;
- left/right symmetry;
- renderer/exporter agreement;
- thumb behaviour;
- hand/wrist deformation and equipment lock.

If a tested centre gives a visually convincing true fist and all acceptance criteria pass, **retain it, lock Phase 1, and continue automatically with Phases 2–5 in `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`**.

If no proximal centre can achieve the target without unloading the palm, creating penetration, or forcing implausible finger geometry, stop and report the measured blocker. Do not change finger lengths, MCP placement, weights or topology without a new decision.

Keep usage low. Do not promote or merge.

## Final Phase 1 compatibility decision — keep the −9 mm full-fist target and buy back curl clearance

The proximal handle-centre sweep has now isolated the final Phase 1 compatibility trade-off.

Measured result:

- **−9 mm along the handle-frame proximal/deeper-in-palm direction is the grip target to preserve**;
- it is the smallest tested shift that visually reads as the user's approved true full-fist grip;
- at −9 mm the palm remains loaded (about −2.54 mm), the thumb remains clear (about +1.18 mm), and no meaningful finger penetration remains;
- 0 mm leaves the index standing off the bar;
- −6 mm still leaves the lower fingers at the side of the handle;
- −12 mm adds no meaningful visual benefit and spends almost all thumb clearance;
- therefore do **not** compromise to −5 mm merely to preserve the old curl clearance: it still does not achieve the accepted grip and leaves essentially no useful clearance margin.

The only blocker is curl Bottom/Return dumbbell-to-thigh clearance. The measured relationship is approximately:

| proximal grip shift | Bottom / Return clearance |
| --- | --- |
| 0 mm | +1.74 / +1.82 mm |
| −3 mm | +0.70 / +0.78 mm |
| −5 mm | +0.09 / +0.17 mm |
| −6 mm | −0.18 / −0.10 mm |
| −9 mm | −0.88 / −0.80 mm |

The full-fist target therefore needs only about **2.6 mm of world-space clearance bought back** relative to the current frozen curl.

### Authorised final compatibility test

Keep the **−9 mm proximal handle-centre target** and the existing close-until-contact solver unchanged.

Test only a tiny additional neutral upper-arm flexion rebase using the same already-proven mechanism that created the frozen +4.3° Stage 1 rebase.

Test exactly:

- `startPose.upperarm_l/r.x = 4.5°`, with `peakPose.upperarm_l/r.x = 8.5°`;
- `startPose.upperarm_l/r.x = 4.55°`, with `peakPose.upperarm_l/r.x = 8.55°`;
- `startPose.upperarm_l/r.x = 4.6°`, with `peakPose.upperarm_l/r.x = 8.6°`.

For every test value, move start and peak by the **same delta** so the existing relative late upper-arm drift remains exactly **4.0°**. Do not reshape the authored curve.

Do not change:

- elbow-flexion profile;
- supination profile;
- timing or easing;
- clavicle behaviour;
- abduction;
- corrected forearm length;
- Stage 1 shoulder state;
- finger solver;
- finger lengths/MCP placement;
- topology or weights.

### Measure for every value

At minimum report:

- curl Bottom/Return dumbbell-to-thigh clearance, both sides;
- whether any dumbbell/thigh vertices are inside;
- −9 mm grip palm loading;
- finger penetration/contact;
- thumb clearance/locking;
- Bottom / Mid / Peak / Return technique and visual silhouette;
- `shoulder_quiet_*`, `elbow_not_inward_*`, `elbow_under_shoulder_*` results;
- bilateral symmetry;
- renderer/exporter agreement;
- shoulder-press grip/contact regression check.

### Selection rule

Retain the **smallest tested neutral rebase** that simultaneously:

1. preserves the visually accepted −9 mm full-fist grip;
2. gives genuine positive dumbbell-to-thigh clearance on both sides at Bottom and Return;
3. preferably restores a practical margin around **+1.5 to +2.0 mm** rather than merely touching zero;
4. keeps the late upper-arm motion exactly 4.0° relative to its own neutral;
5. stays inside the existing shoulder-technique envelope;
6. still reads visually as a strict natural curl with no forward reach or shoulder swing;
7. introduces no new contact/deformation regression.

Do not optimise beyond the smallest passing value.

If one of 4.5° / 4.55° / 4.6° passes, retain **that rebase + the −9 mm handle centre + the current solved grip**, lock Phase 1, update the relevant result docs/changelog, then continue automatically with Phases 2–5 in `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`.

If none of the three passes, stop and report the exact measured blocker. Do not move MCPs, alter finger lengths, change weights/topology, or invent a different curl path without a new decision.

Keep usage low. Do not promote or merge.

## After Phase 1

Once the reusable power grip passes and is retained, continue from **Phase 2** in `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`:

**Stage 2 shoulders → full validation → push-up wrist/forearm deformation package → final cleanup/review pack**.

Continue automatically between those phases when their written acceptance criteria pass. Keep usage low. Do not promote or merge.
