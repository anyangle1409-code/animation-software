# Animation Studio capability roadmap

The target is **not a clone of Blender**. It is a specialist exercise-animation authoring studio with Blender-like control where biomechanics needs it, while keeping the runtime deterministic and exportable to Home Gym PT.

## Acceptance target

An exercise is ready for the PT app only when the Studio can author, inspect and automatically validate the movement without relying on hidden manual fixes. The character, equipment, contacts, joint motion, grip, muscle behaviour and corrective deformation must all remain deterministic when the clip is regenerated.

## 1. Biomechanical core — first priority

- Joint-spanning muscle paths with wrap/via points where a straight chord is anatomically wrong.
- Functional tests for agonist/antagonist behaviour at elbow, wrist, knee, ankle, hip, shoulder/scapula and spine.
- Muscle containment and bilateral symmetry remain hard regression gates.
- Preserve-source-skeleton imported-character retargeting remains mandatory.
- Corrective deformation stays explicit, bounded and joint-driven.

## 2. Rig / pose workspace

- Select any anatomical joint in the viewport.
- FK rotation gizmos plus exact numeric angles and anatomical limits.
- IK handles for hands/feet with visible pole targets and contact error.
- Skeleton-inside-character diagnostic mode.
- Pose copy/mirror/reset and side-to-side comparison.
- Finger and thumb selection down to individual joints.

## 3. Animation workspace

- Dope-sheet style phase/keyframe lane rather than a general Blender timeline.
- Frame stepping, normal / 1/2 / 1/4 speed and loop-range playback.
- Per-joint timing, delay, finish and easing controls.
- Pose markers for start / transition / peak / return.
- Side-by-side candidate comparison without changing the accepted clip.

### Implemented animation-authoring foundation

- Exact one-frame stepping plus 1/4× and 1/2× review speeds.
- Custom In/Out loop ranges for repeated inspection of a difficult rep segment.
- Selected-bone timing authoring for delay, finish point and easing on each keyframe segment.
- Selected-joint frame-by-frame motion diagnostics report worst angular speed and acceleration with exact timestamps and jump-to-frame controls, giving elbow/shoulder timing review an objective signal without imposing a universal movement threshold.
- Keyframe transition continuity compares incoming/outgoing angular velocity around every interior keyframe, reports the largest per-axis velocity jump and exact boundary, and can jump directly there; intentional stops/holds remain descriptive rather than automatically failed.
- Segment-local joint coordination compares the selected joint against its anatomical parent, reporting excursion, meaningful-motion onset and onset lag; the parent can be selected directly for timing edits, making elbow-led/shoulder-follow sequencing explicit without extra stop/start keys.
- Bilateral timing symmetry is explicit: the Joint workspace compares delay/finish/easing against the anatomical opposite and can copy selected-side timing to the other side in one undoable edit without changing pose angles.
- Whole-rep resolved bilateral motion symmetry now samples the final clip and compares the opposite joint against the canonical rig's exact mirror transform, reporting maximum and RMS angular mismatch with a jump to the worst frame; intentional unilateral asymmetry remains descriptive rather than failed.
- Selected-joint spatial path diagnostics track the joint head relative to its anatomical parent, reporting maximum drift, total relative path length, return error and the worst timestamp. For a selected forearm this directly measures elbow wander relative to the shoulder while removing whole-body/root translation.
- Semantic Start / Transition / Peak / Return pose markers are generated deterministically and editable on keyframes.
- Non-destructive A/B pose snapshots provide side-by-side front-view comparison plus selected-joint angle deltas.
- Individual finger/thumb joint authoring remains available through the same joint workspace.
- Dedicated Grip workspace provides undoable closure presets and live measured finger/handle fit using the established regression envelope.
- Equipment-aware deterministic hand-shape profiles now distinguish dumbbell, bar/pull-up, neutral handle, rope/thick-handle, floor/open-palm and relaxed grips; an optional authoring override changes hand shape without changing the exercise's semantic equipment grip.
- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in.
- Live per-digit grip reach plus whole-rep frame-by-frame worst-point review identifies which digit exceeds the authored envelope, records the exact worst timestamp, and can jump the playhead directly to that frame without modifying the animation.
- Grip diagnostics now report the established contact-reach envelope per digit as well as globally, so thumb/pinky/index/middle/ring problems can be localized before using per-digit closure trims. Values above 100% mean the authored geometric reach envelope is exceeded; they are not claimed as literal mesh penetration or force.
- Per-instance hand-local grip-centre calibration edits handle X/Y/Z in millimetres, updates diagnostics live, and can reset to the anatomical default.
- Per-instance hand-local grip orientation calibration rotates one-hand equipment around the same socket/contact centre without twisting wrist/arm animation; position and orientation reset independently.
- Two-hand rigid equipment now fits its actual left/right grip sockets to the two hand-local targets. Per-exercise grip-width calibration adjusts only those contact sockets, bar roll rotates around the bilateral grip axis, and live diagnostics expose left/right millimetre residuals instead of hiding spacing mismatch with wrist/shoulder compensation.

## 4. Hand / grip workspace

- Grip presets for dumbbell, barbell, cable handle, pull-up bar, neutral handle and floor contact.
- Whole-hand closure plus individual finger and thumb opposition controls.
- Handle position/orientation calibration with penetration measurement.
- Rigid equipment attachment and bilateral symmetry checks.

## 5. Equipment / contact workspace

- Selectable equipment objects and sockets.
- Move/rotate authoring gizmos for equipment setup.
- Explicit world/equipment/floor contact locks.
- Live contact-distance and reachability diagnostics.

### Implemented equipment/contact foundation

- Dedicated Contacts workspace inspects every floor / world / equipment lock at the live playhead.
- Target and actual effector positions, millimetre contact error, solver reachability and physical over-extension are reported from the same production frame pipeline used by the viewport.
- Contact inspection is non-destructive; lock enable/disable still uses normal undoable clip editing.
- Static equipment is selectable in the viewport/Equipment workspace and can be translated or rotated with exact numeric inputs or the existing transform gizmo; edits regenerate the deterministic clip through normal undo/redo history.
- Hand-driven equipment rejects world-transform authoring because its attachment solver owns that transform; hand placement remains in the Grip workspace.
- Static equipment sockets are individually selectable and can be translated/rotated in equipment-local space through exact controls or the viewport gizmo. Overrides are per exercise instance and reset cleanly to immutable library defaults.

## 6. Corrective deformation workspace

- Joint-angle-driven corrective shapes for elbow, shoulder, hip, knee and wrist when skinning alone is insufficient.
- Safe displacement caps and zero-at-neutral guarantees.
- Before/after A/B view plus mesh-strain diagnostics.
- No destructive rebinding of imported characters.

### Implemented corrective inspection foundation

- Dedicated Correctives workspace discovers mesh-specific `homeGymPT_*` morph correctives on the active character.
- Live driver influence, affected-vertex count, authored maximum displacement and current maximum displacement are shown at the playhead.
- `Correctives on` / `Raw skinning` is a viewport-only A/B bypass; the accepted clip, source mesh, deformation sampler and export remain untouched.
- Relative and absolute source morph conventions are measured correctly, and unrelated expression/body morphs are never suppressed by the A/B control.
- Live surface-strain diagnostics sample posed mesh edges against bind geometry and report P95/P99/max strain plus >20% compression/stretch counts; rigid transforms correctly read as zero strain.
- On-demand whole-rep strain review scans the active character at the authored clip FPS, records worst P99/max deformation timestamps for each mesh, restores the current playhead pose, and can jump directly to the worst frame in either Correctives-on or Raw-skinning mode.
- Imported elbow outer-smoothing is now a bounded 0–100% character-level control. The retained radial volume morph remains separate, the measured candidate morph stays capped at 8 mm, and the active viewport plus GLB export sampler share the exact same source-level tuning value.
- Corrective tuning can run an on-demand 0/25/50/75/100% whole-rep strain sweep, report worst P99/max frame for each value, restore the pre-scan tuning and pose, and jump to any measured value for visual review without automatically choosing a winner.

## 7. Diagnostics and approval

- Focus-selected camera and joint-angle readout.
- Muscle path/stretch readout.
- Grip penetration, equipment drift, contact error, symmetry and mesh strain.
- Exercise-specific technique validators.
- One explicit Approved state only after automated checks and visual review pass.

### Implemented review/approval foundation

- Dedicated Review workspace aggregates conservative automated gates for technique errors, loop closure, IK reachability, explicit contact locks, the supported single-hand dumbbell grip envelope, and rigid two-hand socket alignment.
- Automated success means **Ready for visual review**, never automatic approval. A separate visual sign-off is required for naturalness, joint silhouette, grip/contact appearance and equipment stability.
- Visual sign-off is bound to the exact Studio document identity and active character source; edits or character swaps invalidate it automatically. Only automated-pass + matching visual sign-off displays `APPROVED`.

## 8. Template-driven scale

- Reusable movement families (curl, press, row/pull, squat, hinge, lunge, calf raise, core, locomotion).
- Shared grip/contact/equipment presets.
- Exercise definitions supply the movement data; the engine supplies the solver/validation.
- New exercises should usually be data authoring, not new bespoke animation code.

## Deliberately out of scope

Sculpting, UV editing, texture painting, compositing, particles, general scene modelling and arbitrary renderer/node systems stay in Blender or another DCC. The Studio should own everything needed to pose, animate, validate and export exercise demonstrations.
