# Home Gym PT Animation Studio

An authoring tool for building accurate, reusable 3D exercise animations.

You pick an exercise, the studio constructs a biomechanically controlled draft
from that exercise's definition, you inspect and adjust it, and you export an
animation your app can play.

This is not image or video generation. It is a skeletal animation system: a
canonical humanoid rig with anatomical joint limits, analytic inverse
kinematics, contact locks, rigid equipment attachment, and deterministic
keyframe generation driven by structured exercise data.

## Status

Five exercises prove the engine, chosen because they exercise different parts
of it:

| Exercise | What it proves |
|---|---|
| Dumbbell Bicep Curl | shoulder/elbow/wrist plus an implement rigidly held in each hand |
| Push-Up | four floor contacts at once, whole-body rigid constraint, root motion |
| Bodyweight Squat | hips, knees and ankles with the feet locked to the floor |
| Dumbbell Shoulder Press | the shoulder through nearly its whole abduction range, loaded |
| Pull-Up | no floor contact at all — the hands are locked to a rack's own grip sockets and the whole body is solved from them |

All five generate clean: every technique rule the exercise defines passes at
every sampled frame, every IK target is reachable, and each clip returns
exactly to its opening pose.

### Working now

- **Canonical rig** — 53 bones including fingers and toes, every joint with
  anatomical rotation limits and named axes ("Flexion", "Abduction", …)
- **Anatomical body** — one skinned mesh lofted from cross-section profiles:
  a trunk from crotch to crown, limbs as continuous tubes, joints whose vertices
  are shared between the two bones either side of them so an elbow creases
  instead of scissoring. The viewport and the GLB exporter build it from the
  same data, so what you see is what the file contains
- **Forward kinematics** with per-joint clamping, pose mirroring and blending
- **Inverse kinematics** — analytic two-bone solvers for both arms and both
  legs, with pole targets for elbow and knee direction, hinge joints solved as
  hinges, and joint limits that constrain the solve rather than being ignored
- **Contact locks** — hands and feet held to the floor, to a fixed point, or
  rigidly to an equipment socket; contacts do not slide
- **Equipment** — twelve items as real 3D objects with named attachment
  sockets; a two-handed bar is placed from both grips so it stays straight and
  moves symmetrically
- **Exercise definitions** — one structured schema carrying poses, phases,
  tempo, joint targets, grip, stance, muscles, camera, technique rules and
  common errors
- **Procedural generation** — deterministic clips built from a definition, with
  easing shaped for resistance training and perfect loop closure
- **Technique checking** — the exercise's own rules evaluated across the clip,
  reported per rule and per frame
- **Timeline editor** — play, scrub, keyframes, easing, duration, tempo, copy,
  paste, mirror, undo/redo
- **Muscle overlay** — 43 muscle bellies bound between origin and insertion, so
  they shorten and thicken with the joints; primary, secondary and stabiliser
  highlighting comes from the exercise definition
- **Retargeting** — import a rigged GLB, auto-guess a bone mapping, correct it
  by hand, and drive the imported character from the same animation
- **Export** — animated GLB (skinned rig, clip and equipment), clip-only GLB
  and JSON so many exercises share one character, and exercise metadata JSON

### Not built yet

More exercises, cable and band force lines, physics-based weight sag, facial
detail, and the Home Gym PT male/female characters themselves.

## Getting started

```bash
npm install
npm run dev
```

| Command | Purpose |
|---|---|
| `npm run dev` | Development server on port 5174 |
| `npm run build` | Typecheck and production build |
| `npm test` | Unit tests |
| `npm run typecheck` | Types only |

## How it fits together

The whole system turns on one idea: **a pose is plain data**, independent of any
visible character.

```
ExerciseDefinition
      │  generateClip
      ▼
   StudioClip  (keyframes: pose + IK targets, locks, equipment)
      │  resolveFrame(time)
      ▼
   blend keyframed pose
      → solve keyframed IK targets
      → place equipment from the hands
      → solve locks (which may pull hands onto that equipment)
      → place equipment again
      ▼
   ResolvedFrame  →  viewport · technique checker · exporters · retargeting
```

Everything downstream reads that one `Pose` structure, which is why the same
animation can drive the mannequin, an imported Meshy character, the muscle
overlay and a GLB export without being re-authored for any of them.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the module layout, the bone
frame convention, and the decisions behind them.

## Export formats

| File | Contains | Use |
|---|---|---|
| `<clip>.glb` | skinned rig, animation, equipment | drop straight into the app |
| `<clip>.anim.glb` | bone hierarchy and animation, no mesh | many exercises, one character |
| `<clip>.anim.json` | rotation tracks, plus a three.js-native clip | custom players |
| `<exercise>.json` | the full exercise definition and derived timings | the exercise database |

Clip names are app-friendly slugs: `bicep_curl`, `push_up`, `air_squat`,
`shoulder_press`, `pull_up`.
