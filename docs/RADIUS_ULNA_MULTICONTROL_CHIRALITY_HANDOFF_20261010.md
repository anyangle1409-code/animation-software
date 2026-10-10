# Radius/ulna three-control chirality: follow-on to PR #27

## Coverage gap closed without altering Work or Claude

The base [independent side-binding audit](https://github.com/anyangle1409-code/animation-software/pull/27) intentionally covers only anatomical left/right pairs mapping to *one* runtime control per side.

- Parent: **59 bilateral single-control reference pairs** = **118 crossed alias entries**, corroborated by three independent major osseous pairs.
- This follow-on: **4 osseous reference records**, `radius_left`, `radius_right`, `ulna_left`, `ulna_right`, each mapped to *three* controls: `forearm`, `forearm_tw0`, `forearm_tw1`, with `_l` or `_r` suffix.
- Additional **12** crossed alias links, including **8 forearm twist-helper links**. The broad total is **130 crossed name-only links** across **122 reference records**. These are mapping links, not 130 independently shaped bones.

The source coordinate frame's proper rotation `(x,y,z) -> (x,z,-y)`
preserves lateral X, so the suffix inversion is a binding issue rather than
an instruction to mirror bones or meshes.

## Verification

```bash
python -m unittest -v scripts/test_anatomical_runtime_chirality_gate.py
python -m unittest -v scripts/test_forearm_multicontrol_chirality.py
python scripts/anatomy_fit/forearm_multicontrol_chirality.py --out /tmp/forearm-links.json
```

The standalone Python stdlib audit SHA-256-pins the three checked-in source
records and checks each reference, each of the three stored controls, the
coordinate sign in the anatomical fit and both current legacy controls.
Mutation tests reject missing or mirrored helpers, alias changes, unexpected
relationship status, and fit coordinate inversion.

## Work laptop handoff: do not immediately change anything

The forearm twist helpers are *not* osseous radius/ulna models and do not
independently reproduce proximal/distal radioulnar joint contact. Their
name-only side binding cannot be assumed correct when deriving new
anatomical motion into the current animation engine.

Before any production adapter change, use bilateral **pronation and
supination**, elbow flexion and grip motions to confirm which helper drives
each physical limb in 3D; check wrist orientation and skinned deforming
mesh against actual anatomy. Respect source evidence, coordinate frames,
and owner approval. Preserve the r95/a003 master and Work's active Blender
session unchanged.

**This pass is only reproducible static code evidence.** It does not
establish real bone-surface identity, correct joint range, correct motion,
or completion of the skeleton.
