# Architecture

## Module layout

Each directory owns one concern and depends only on the ones above it.

```
src/
  core/          numeric helpers, ids
  rig/           canonical skeleton, joint limits, poses, forward kinematics
  ik/            two-bone solvers, pole targets, bone aiming
  constraints/   contact locks, technique rules and their evaluator
  equipment/     equipment definitions, geometry data, attachment solving
  muscles/       muscle groups, deformation model, activation levels
  exercises/     the ExerciseDefinition schema and the definitions themselves
  animation/     keyframes, easing, the frame pipeline, generation, validation
  retargeting/   bone mapping, GLB import, retarget binding
  export/        skinned rig builder, clip baker, GLB and JSON exporters
  viewer/        R3F scene, skeleton, mannequin, muscles, equipment, gizmos
  editor/        store with undo/redo, panels, timeline, app shell
```

Nothing in `rig/`, `ik/`, `constraints/`, `animation/` or `export/` imports
React or touches the DOM, which is what lets the whole engine be tested
headlessly — and what will let it be lifted into Home Gym PT later.

## The pose model

```ts
interface Pose {
  rotations: Partial<Record<BoneName, Vec3>>;  // Euler radians, bone-local
  rootPosition: Vec3;
  rootRotation: Vec3;
}
```

That is the entire animation data model. Poses do not reference a character, a
mesh, or a scene. Everything else — FK, IK, constraint checking, muscles, the
timeline, every exporter, retargeting — reads and writes this one structure.

## Bone frames

Every bone has the same frame convention, built from its rest geometry:

- **+Y** runs along the bone, head to tail
- **+Z** is the body's forward, projected perpendicular to Y
- **+X** = Y × Z

That gives every joint in the body the same meaning for its three axes:

| Axis | Meaning |
|---|---|
| x | flexion / extension |
| y | axial rotation (twist along the bone) |
| z | abduction / adduction |

Because limbs bend in opposite directions, the *sign* of flexion differs between
the arm and the leg — elbow flexion is +x, knee flexion is −x. Rather than hide
that, every axis carries its own labels (`positive: 'Flexion'`,
`negative: 'Extension'`), so the editor can describe each joint correctly and
exercise definitions read the way a coach would say them.

Handedness is likewise explicit: a right-handed rotation about Z carries +Y
towards −X, so on the character's left side (which lives at −X) positive z is
*ad*duction. Left-side limits are authored once and mirrored, flipping the y and
z ranges and swapping their labels.

### Rest pose

The arms hang vertically at rest. An A-pose with built-in splay would silently
add several degrees to every shoulder angle an exercise author writes down.

## Euler order — and why it is `XZY`

Rotations are stored as Euler angles because joint limits, the editor's numeric
readouts and the exercise definitions all need per-axis values a person can read
and reason about. Quaternion storage would make all three worse.

The cost of Euler storage is a gimbal singularity when the **middle** axis
reaches ±90°: the outer and inner axes then trade off freely, a solver picks an
arbitrary split, the joint limits clamp it, and the pose falls apart.

With order `XZY` the middle axis is **abduction**, so the singularity sits at 90°
of abduction — which a hip cannot reach at all. The obvious-looking `ZXY` puts
**flexion** in the middle, and 90° of hip and shoulder flexion is exactly where a
squat and a press live. That choice was not theoretical: with `ZXY` the squat's
IK saturated the hip's rotation and abduction limits on every frame.

`y` stays innermost so it is a pure twist about the bone's own axis, which is
what the IK solver needs to orient a hinge's bend plane.

## Inverse kinematics

`solveTwoBone` is analytic, not iterative:

1. The triangle of the two bone lengths and the root-to-target distance fixes
   the bend angle (law of cosines).
2. The pole target fixes which way the hinge points.
3. The upper bone is twisted about its own axis so the hinge's flexion plane
   contains the target. Without this the elbow or knee would need an abduction
   it does not anatomically have, and clamping that away breaks the chain. The
   twist is solved in closed form; two solutions exist, and the joint's own
   limits pick the branch — which is how an elbow bends forwards and a knee
   backwards from the same code.
4. The hinge is then solved directly for its flexion angle rather than by
   decomposing a swing, which would spill rotation into the twist axis that the
   limit clamps away.

Every result is clamped to the joint's anatomical range, so an unreachable
target produces a limb that falls short and a reported error — never an
impossible pose.

## The frame pipeline

`resolveFrame(clip, time)` is the heart of the runtime, and the order matters:

1. blend the keyframed forward-kinematic pose
2. solve keyframed IK targets
3. place equipment from the resulting hands
4. solve the locks, which may pull hands onto that equipment
5. place equipment again, now from the locked hands

Steps 4 and 5 run twice when any lock targets equipment. That is what makes a
two-handed bar settle: the bar straightens between the grips, the grips are
re-solved onto the straightened bar, and the pair converges instead of drifting.

## Contacts

Floor locks are anchored to where the contact sits in the clip's **opening
pose**, computed once per clip and reused for every frame. Deriving a contact
height from the mesh instead asks the limb to reach somewhere it cannot, and the
foot visibly sinks and slides.

Where an exercise's whole body moves — the push-up, the squat — the root
placement is *derived* rather than guessed: it is the position that puts the
contacts back on their anchors for the authored joint angles. The locks then
have nothing left to correct, and the technique rules verify it.

## Technique rules

Rules are data on the exercise definition, not code:

```ts
{ kind: 'stationary', id: 'feet_planted_l', label: 'Left foot stays planted',
  point: { bone: 'foot_l' }, tolerance: 0.012, severity: 'error' }
```

Seven rule kinds cover joint angles, segment angles against world references,
stationary contacts, distances, relative positions, left/right symmetry and
three-point alignment. The same objects drive the checker and the editor's
technique panel, so what is enforced and what is documented cannot drift apart.

## Muscles

A muscle is defined by an origin and an insertion, both in bone space. Because
those two points ride their own bones, the muscle follows the skeleton for free:
bend the elbow and the biceps shortens and thickens, with no second rig to keep
in sync. Activation levels come from the exercise definition, never from
inspecting the animation at runtime.

## Retargeting

Transferring a world-space rotation onto another rig only works when both rigs
share a rest pose. Applied to a T-posed import of an A-posed animation, elbow
flexion arrives as a forearm twist.

So each target bone gets its own anatomical frame, built exactly the way ours
are, from its rest direction and the character's own forward (detected from its
feet). Joint angles are then carried through the change of basis between the two
frames. An elbow flexes by the same number of degrees whatever pose the
character was modelled in.

Mappings are stored separately from exercises: a character is mapped once, and
every exercise retargets onto it with no further work.

## Export

The GLB exporter builds a real skinned rig — a `Bone` hierarchy matching the
canonical skeleton and one `SkinnedMesh` bound to it, each body segment weighted
entirely to its own bone. The clip is baked by running the full frame pipeline
at every sample, so what is exported is what the studio showed, not the raw
keyframes before constraints.

A constant track is reduced to two keys, but only *dropped* when its constant
value is the bone's rest value. Dropping a constant track that differs from rest
would silently reset the bone — a planted foot, a closed grip or a set stance
would all snap back on export.

Hand-held equipment is parented to the hand bone with a fixed local transform,
so the attachment stays exact in whatever engine plays the file, with no extra
animation. A two-handed bar, whose position comes from both hands, gets its own
baked tracks instead.
