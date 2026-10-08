# CP3 build rehearsal 002: builder roll and marker-precision fixes (not an audit revision)

These are owner-approved fixes to `scripts/anatomy_fit/build_anatomical_master_blender.py`, rehearsed as in run 001 (Blender 5.2.1, empty scene, fresh-process capture). The scratch .blend files were not kept; their sha256 were `941038baa33c2b85d3e95f1319e6d0d443f99b932e8f390ede1a34ee115b87f1` (a003 data) and `e865da0d2577c361abbe79d7590a47d979b81644c79ba15e0bd52405989b5750` (mirrored).

## Fixes

1. **Defined roll for every bone.**
   - `roll_reference()` passes `align_roll` the frame's anterior axis. Where `bone_frame` puts anterior along the bone (its horizontal-bone branch), it passes the frame's superior axis instead, which is perpendicular to the bone by construction. No new threshold is introduced.
   - Each bone records `hgpt_roll_reference` ('anterior' or 'superior'), and the convention text in the fit record is updated.
2. **Marker rotations are stored as quaternions.** With defined rib rolls, the costochondral and interchondral markers of ribs 8–10 sit at about −90° Euler pitch relative to their rib. Euler storage at gimbal lock lost up to 3.6e-4 in frame components (found on the mirrored run). Quaternion storage has no gimbal lock.

## Results (both inputs)

| Input | Round trip | Bone endpoints | Marker centres | Marker frames | Roll (all 206) | The 74 superior-reference bones | L/R roll mirror | CP2 preflight |
|---|---|---|---|---|---|---|---|---|
| a003 record | PASS | 5.9e-8 m | 1.9e-7 m | 5.3e-7 | ≤ 0.024° | ≤ 0.019° (previously undefined) | 0.39° | Same as input: 8 PASS / 1 FAIL / 1 UNVERIFIED / 1 INFO |
| Exactly mirrored copy of a003 bones | PASS | 5.9e-8 m | 1.9e-7 m | 5.3e-7 | ≤ 0.024° | ≤ 0.022° | **0.027°** | Same |

**Reading:**
- The 0.39° left/right difference on a003 is a003's own slight bilateral asymmetry: the rule follows the geometry, and an ideal float capture gives the same 0.39°.
- On an exactly mirrored skeleton, Blender's rolls mirror within 0.027°, which is align_roll's numerical precision (about 0.02° on all bones).
- The movement tests are unaffected, because they conjugate world deltas by each rest matrix.
- a003's .blend files and records are untouched. The new behaviour applies only to future builds.
