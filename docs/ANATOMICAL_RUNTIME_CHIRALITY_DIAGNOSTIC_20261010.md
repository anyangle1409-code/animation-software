# Anatomical ↔ runtime handedness: independent no-Blender gate (10 October 2026)

## Why this matters

The anatomical master is the source of truth. A frame convention error can animate the
wrong arm or leg even when **every** pose matrix is numerically valid. This is not a
skeleton-size issue and must not be fixed by mirroring skin or renaming production
bones without an owner-approved runtime mapping.

This gate is independent of concurrent Blender evidence and motion
source work (#24/#25). It alters **no** skeletal coordinates, bone inventory,
skin, mesh, Blender file, animation driver, atlas alias or approved candidate.

## Source-grounded finding

The pinned character_fit_r95_a003.json states +Z up, character facing -Y,
anatomical **left = +X**, with existing explicit side-binding note
left -> _r, right -> _l. Measured clavicle, humerus and femur head/tail
midpoints establish positive X on the anatomical-left side.

Frozen hgpt_canonical_v4_original_rev2c.json uses +Y up, +Z forward.
Rotating the fitted frame into runtime is a proper right-handed rotation:

    (x, y, z)_fitted  ->  (x, z, -y)_runtime

This preserves left=+X and is **not a reflection**. The frozen runtime bones
clavicle_l, upperarm_l and thigh_l nevertheless sit on **negative X**,
while their _r equivalents sit on positive X.

The separate 206-reference alias inventory maps clavicle_left -> clavicle_l,
humerus_left -> upperarm_l, femur_left -> thigh_l and likewise for the
right side. All **six independently measured anchor aliases** therefore point
physically across the body. This is a *binding ambiguity*, not evidence
that any real anatomical bone needs to move.

## Broader descriptive mapping inventory

The new static scanner also enumerates all 206 reference aliases. The 59
bilateral anatomical-reference pairs mapped to one sided runtime control each
have physically crossed control assignments (118 side-specific alias entries).
These are *not* 59 independent osseous structures: carpals and tarsals,
for example, collapse into the hand/foot runtime controls. This broad
sign-only mapping result is intentionally distinguished from the three
fitted, physically measured bilateral anchor pairs above. All 206 anatomy
entries and all 427 articulation contacts still require separate bone geometry
and movement verification.

## Run with no Blender, no Claude and no third-party Python packages

    python scripts/anatomy_fit/anatomical_runtime_chirality_gate.py --out /tmp/hgpt_chirality_gate.json
    python -m unittest discover -s scripts -p 'test_anatomical_runtime_chirality_gate.py' -v

The report lists exact fitted and runtime lateral offsets for three bilateral
probes and SHA-256 hashes for each input. The gate refuses unknown frame
conventions, flipped fitted side identity, absent counterparts, duplicates
and nonfinite coordinates. Mutation tests check the failure paths, including grouped carpal mapping.

## Handoff / sequence before ANY runtime integration

1. Treat the 206 alias table as **descriptive, not accepted** for runtime
   anatomical left/right. Pause automatic side translation relying only
   on *_left -> *_l.
2. Do not amend the frozen 206-bone anatomical master, a003, c001-c004 or
   the currently running Blender/Work session from this branch.
3. At a safe integration checkpoint, owner and driver developer explicitly
   agree which API field means anatomical left versus a pre-existing runtime
   name. Decide translation in a single adapter rather than renaming
   every bone.
4. Before approval, exercise **bilateral** shoulder flexion/abduction,
   elbow flexion, grip, hip flexion/abduction and foot placement using both
   side-specific command labels; capture each anatomical side's expected
   world response after the proper coordinate transform.
5. Re-run full 206-bone identity, 427-joint, mirrored-motion and source
   provenance checks. Verify actual Blender rig aliases and nonuniform
   rest offsets in addition to this three-pair static test.
6. Only after independently verified evidence and owner sign-off, update
   the canonical-to-runtime adapter, its tests and integration policy.
   Never mark an anatomical region READY based on this gate alone.

## Hard limits

- Six anchors **do not** establish correctness of all 206 bones, all 427
  contacts or every movement channel.
- The current runtime naming can remain intact if the exported adapter
  consistently translates anatomy left/right. The defect concerns treating
  *names* as equivalent physical laterality.
- This report is a new read-only regression gate. Its passing tests mean
  discrepancy was **detected correctly**, not that it is fixed.
- Work's concurrent #24/#25 movement-source and Blender checks remain separate.
