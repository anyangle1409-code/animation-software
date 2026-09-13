# Architecture

## Module layout

Each directory owns one concern and depends only on the ones above it.

```
src/
  core/          numeric helpers, ids
  rig/           canonical skeleton, joint limits, poses, forward kinematics
  body/          the character's surface: profiles, skinning, the skinned mesh
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

Anything that writes a y or z angle for both sides has to flip the sign, and
forgetting to is silent rather than loud: the grip generator once sent both
hands the same finger flexion, which closed the left hand and *extended* the
right one into its limits — a flat open palm holding a dumbbell, with no error
anywhere. `applyGrip` and `applyStance` both carry an explicit per-side sign,
and a test checks the two hands close by the same amount.

### Rest pose

The arms hang vertically at rest. An A-pose with built-in splay would silently
add several degrees to every shoulder angle an exercise author writes down.

Imported hands use the source skeleton's index-to-pinky knuckle line to recover
the palm plane. This keeps finger flexion anatomical when the source hand frame
differs from the body's general forward axis. A repaired character may also
store small per-hand grip-frame offsets in `scene.userData.homeGymPT` so
equipment placement follows the actual palm surface without changing exercise
definitions.

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

## The body

The character's surface is data, in `body/profiles.ts`: a list of **chains**,
each a continuous tube of elliptical cross-sections running along several bones.
The trunk is one chain from the crotch to the crown; an arm is one chain from
the shoulder to the fingertips. Every ring gives a half-width across its bone, a
half-depth front to back, and an offset for the shapes that are not centred on a
bone — a calf, a set of glutes, the face.

Two decisions matter:

**Chains, not one capsule per bone.** The first version built a capsule for each
bone. Where two capsules met they z-fought along the overlap, which drew a hard
ring around every joint, and when a joint bent the two rigid volumes scissored
through one another. A chain has no join to fight over: the wall runs straight
from the last ring of one bone to the first ring of the next.

**Vertices are shared across a joint.** A ring within a blend width of a joint
splits its weight between the two bones either side of it — evenly at the joint,
entirely to one bone a blend width away. That single rule creases an elbow,
rounds a shoulder and folds a hip, and it is why the exported mesh is no longer
one bone per vertex. Nothing needs more than two influences.

Small features — a nose, ears, lips, eyeballs, the pad at the base of a thumb —
are ellipsoids that intersect the surface they sit on. How deep they sit is the
whole trick: buried to their own radius they lie almost tangent to the skin and
the two surfaces fight for pixels; sitting on the surface they read as balls
stuck on. Half a radius in crosses the skin at about 60° and reads as one form.

Colour is a vertex attribute rather than a second material: skin, shorts,
waistband, eyes, lips and hair all ship in one mesh with one draw call, which is
what keeps the character cheap enough for the phone app.

`body/containment.ts` answers "is this point inside the character?" from the
profiles rather than the built mesh. Because the profiles are authored in each
bone's own frame, the same test works in any pose, and it is what lets the
muscle overlay be checked automatically — a belly poking out through the skin
becomes a number rather than an opinion.

The viewport and the GLB exporter call the same `buildSkinnedRig`, so the figure
on screen is the figure in the file — bound to the same bones, with the same
weights. `body/body.test.ts` holds the mesh to a person's proportions: the crown
at the rig's stated height, the soles on the floor, a waist narrower than both
ribcage and hips, a deltoid that does not rise into a shoulder pad, and a
positive enclosed volume of roughly the right size, which is what catches a
surface accidentally wound inside out.

## Muscles

A muscle is defined by an origin and an insertion, both in bone space. Because
those two points ride their own bones, the muscle follows the skeleton for free:
bend the elbow and the biceps shortens and thickens, with no second rig to keep
in sync. Activation levels come from the exercise definition, never from
inspecting the animation at runtime.

Each belly is built on an explicit frame — length along the muscle, width across
the body, depth through the skin — with "outward" taken from the direction the
muscle's own origin sits off its bone. An earlier version spread sheet muscles
along whatever axis the maths happened to pick, which sent the abdominals seven
centimetres out through the stomach.

Two things then keep a belly under the skin. It is **tapered**, stopping short of
both attachments in tendon, because a belly drawn all the way to the bone cuts
the corner of a bent joint and appears outside the arm. And it is **fitted**: its
own surface is measured against the profiles and pulled in until it clears them.
However carefully a muscle is authored, a pose can bring the skin closer than
the belly is wide — a raised arm pulls the pectoral's line across the armpit —
and a muscle cutting through the surface is the one thing an exercise
demonstration must never show.

## Retargeting

Imported characters use their original skeleton, inverse bind matrices and
weights. Each mapped bone receives the canonical absolute anatomical frame,
converted through the source bone's authored basis. This replaces an imported
A-pose/open-hand rest orientation rather than adding exercise deltas to it.
Forward direction comes from the feet; the thigh positions identify an opposite
left/right convention. Reflection conjugates rotations, never the mesh.

Some Rigify deform-only GLBs omit constraints and export shoulders, arms,
thighs and detail bones as armature siblings. The binding captures their rest
attachment to the mapped anatomical parent. At runtime these branches receive
local translations (and rigid transforms for recognised face, breast and pelvis
details), without reparenting bones or rebinding the mesh. Connected helpers
retain their source offsets. Facial branches are not used as a head bone's tail;
Rigify leaf bones use their authored +Y shaft when no tail node is exported.

Root rotation rotates the resting pelvis around the scene origin before root
translation is applied. Scene transforms introduced after binding are applied
once. Reset restores both local rotations and local positions.

Imported animation export samples rotations and positions of all source bones,
including virtual attachments and detail followers. Rest-valued tracks are
removed by the usual compression; remaining tracks reproduce viewport posing.

Mappings remain separate from exercise definitions. Correct bone frames do not
certify skin deformation: an asset with misplaced pivots or inappropriate
weights can still tear under a mathematically correct pose. Source proportions
also differ from the canonical contact solver's proportions. Hand-carried
objects follow source hand bones, but floor/bar contacts and actual mesh grip
require independent validation. The optional real-character test is a coarse
catastrophic-strain guard, not visual approval.

## Export

The GLB exporter builds a real skinned rig — a `Bone` hierarchy matching the
canonical skeleton and one `SkinnedMesh` bound to it, from the same body
profiles the viewport uses, joint weights included. The clip is baked by running
the full frame pipeline at every sample, so what is exported is what the studio
showed, not the raw keyframes before constraints.

A constant track is reduced to two keys, but only *dropped* when its constant
value is the bone's rest value. Dropping a constant track that differs from rest
would silently reset the bone — a planted foot, a closed grip or a set stance
would all snap back on export.

Hand-held equipment is parented to the hand bone with a fixed local transform,
so the attachment stays exact in whatever engine plays the file, with no extra
animation. A two-handed bar, whose position comes from both hands, gets its own
baked tracks instead.
