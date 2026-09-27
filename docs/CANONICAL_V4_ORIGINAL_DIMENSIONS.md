# Canonical v4 ORIGINAL design dimensions

## Status

This is the first clean numerical rest definition for
`hgpt_canonical_v4_original`. It is a candidate for ORIGINAL v1 neutral-anatomy
work and is not the active runtime skeleton.

The values below are project-authored design targets. They were chosen as a
coherent neutral athletic adult figure and were not fitted to v3, V8, V13e,
V15f, MakeHuman, or any imported mesh or skeleton.

## Primary targets

| Dimension | Target |
|---|---:|
| Standing height | 1.820 m |
| Shoulder-joint breadth | 0.430 m |
| Hip-joint breadth | 0.184 m |
| Upper-arm length | 0.325 m |
| Forearm length | 0.270 m |
| Wrist to palm-axis end | 0.095 m |
| Femur length | 0.445 m |
| Tibia length | 0.430 m |

## Hand targets

| Chain | Segment lengths |
|---|---:|
| Thumb | 48 / 31 / 24 mm |
| Index | 45 / 27 / 20 mm |
| Middle | 49 / 30 / 22 mm |
| Ring | 46 / 28 / 21 mm |
| Pinky | 36 / 22 / 18 mm |
| Index metacarpal | 70 mm |
| Middle metacarpal | 72 mm |
| Ring metacarpal | 66 mm |
| Pinky metacarpal | 58 mm |

The left side is generated from these targets and the right side is mirrored
algorithmically. The palm narrows toward the carpus and keeps four articulated
metacarpals plus the three-axis thumb base required by the project-owned rig
architecture.

## Structural gate

The focused v4 test proves:

- new skeleton identity;
- exactly 63 complete project-owned bone names;
- valid parent ordering and nonzero finite lengths;
- exact designed left/right symmetry;
- complete scapula, metacarpal, thumb, and finger chains;
- all four IK chains resolve structurally;
- every current exercise can generate against v4 without a character asset;
- the v4 definition does not import `humanoid.ts`, `HUMANOID_BONES`, or the v3
  shoulder-fit constants.

## Next gate

Create the v4 armature inside the clean-room Blender file and shape O2 neutral
anatomy around these targets. Do not activate v4 in the current runtime, change
exercise mechanics, or remove v3 until ORIGINAL v1 binding and the full
movement envelope have passed.
