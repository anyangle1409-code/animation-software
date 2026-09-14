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

## 6. Corrective deformation workspace

- Joint-angle-driven corrective shapes for elbow, shoulder, hip, knee and wrist when skinning alone is insufficient.
- Safe displacement caps and zero-at-neutral guarantees.
- Before/after A/B view plus mesh-strain diagnostics.
- No destructive rebinding of imported characters.

## 7. Diagnostics and approval

- Focus-selected camera and joint-angle readout.
- Muscle path/stretch readout.
- Grip penetration, equipment drift, contact error, symmetry and mesh strain.
- Exercise-specific technique validators.
- One explicit Approved state only after automated checks and visual review pass.

## 8. Template-driven scale

- Reusable movement families (curl, press, row/pull, squat, hinge, lunge, calf raise, core, locomotion).
- Shared grip/contact/equipment presets.
- Exercise definitions supply the movement data; the engine supplies the solver/validation.
- New exercises should usually be data authoring, not new bespoke animation code.

## Deliberately out of scope

Sculpting, UV editing, texture painting, compositing, particles, general scene modelling and arbitrary renderer/node systems stay in Blender or another DCC. The Studio should own everything needed to pose, animate, validate and export exercise demonstrations.
