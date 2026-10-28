# Prospective symmetric grip capture contract — 2026-10-28

## Purpose

The verified native diagnosis contains 263 trials per model but only authored runtime suffix `l`. Before any new Blender grip search, the capture format must require paired finite coverage for both authored suffixes and must record object/contact evidence separately from the existing self-collision solver guard.

This task defines that contract only. It does not execute a new pose search, bind anatomical sides, choose a grip object, or define a passing threshold.

## Research basis

- Wu et al., ISB joint-coordinate recommendations Part II, DOI `10.1016/j.jbiomech.2004.05.042`: wrist/hand motion should be reported in defined segment coordinate systems. Home Gym PT landmarks and segment frames remain unbound, so authored suffixes and bone Euler channels are not promoted to anatomical axes.
- Reilmann et al., DOI `10.1007/s002210100838`: whole-hand grasp experiments record digit contact timing plus normal and tangential forces with an instrumented object. A mesh collision count cannot substitute for those measurements.
- Nataraj and Li, DOI `10.1080/10255842.2013.820722`: digit kinematics, joint centres, aligned coordinate systems, contact forces and object coordinates are integrated for pinch mechanics. The contract therefore pins an object surface/frame and records digit/object geometry in a common frame.
- Marquardt and Li, DOI `10.1142/S0219519413500474`: precision-pinch contact mechanics include force-vector magnitudes/directions and centre-of-pressure locations. Geometric Blender capture does not measure those quantities and reports them as unavailable rather than inferred.

Population means from these studies are not joint limits or acceptance thresholds.

## Contract

Machine source: `docs/anatomy/HGPT_GRIP_CAPTURE_CONTRACT_V1.json`.

- A hash-pinned finite search-cell manifest must be declared before capture. Observed unique keys must equal its exact Cartesian product with authored suffixes `l/r`, with no missing or duplicate records.
- Suffix-specific Euler observations are recorded independently; the contract does not assume the two runtime bone frames mirror.
- Object evidence requires an object ID, mesh and surface-triangle hashes, metre unit declaration and 4x4 object frame.
- Every trial separately records self-intersection pairs, body/object intersection pairs, and at least one closest-surface sample for each authored digit label (`thumb/index/middle/ring/little`). Samples use zero-based pinned topology, points and unit outward normals in the object frame, and signed separation defined as positive=separated, zero=touching, negative=penetrating. These labels remain authored identifiers, not independently bound anatomy.
- Force, pressure, friction and slip remain unmeasured by a geometric capture.
- Self-intersection, contact, collapse and return-residual acceptance thresholds all remain `NOT_DEFINED`.

Status: `PROSPECTIVE_SYMMETRIC_GRIP_CAPTURE_CONTRACT_NOT_ACCEPTANCE`. No native search, contact acceptance, grip acceptance or anatomical approval is granted.
