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

## After Phase 1

Once the reusable power grip passes and is retained, continue from **Phase 2** in `docs/REFERENCE_BODY_ONE_PASS_COMPLETION.md`:

**Stage 2 shoulders → full validation → push-up wrist/forearm deformation package → final cleanup/review pack**.

Continue automatically between those phases when their written acceptance criteria pass. Keep usage low. Do not promote or merge.
