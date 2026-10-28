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

## Cloud verification

- Published implementation commit `caa9ca194c2a71fbd59fb8d944c2d5f26eed8d79` and evidence-hardening commit `1f732a3d659e27df8ffe1d39a75064e758bea3c9`. [Run 40754389702](https://github.com/anyangle1409-code/animation-software/actions/runs/40754389702) completed **SUCCESS 7/7** at the hardened commit.
- Job IDs: pose `123049293770`, W8 `123049293930`, localization `123049294025`, R120 `123049294240`, V14 `123049294274`, cross-model `123050444057`, driver `123053895611`. Cloud logs confirm localization `298/298`, pose `24/24 + 19/19 + 6/6 + 10/10`, and driver `10/10 + 20/20 + 8/8` tests passed.
- Localization artifact `12844682968` was independently downloaded, CRC-checked and SHA256-matched GitHub at `1a3b9f89111bf466add42f004742d5aa001311e9578e994e3a3f3f348ffbe57c`. Embedded contract JSON SHA256 is `e1f00b12077ae637e6f37d4a7f544b3622908a8148f5450b7eb9ebe3bc8dc941`; phone Markdown SHA256 is `39d12f698668e29efc4b81e0a1fdbbb7fbae9f0fc6c898ff83a920f5bcbf015d`.
- Pose artifact `12845492862` (`4907334c0f30f8e7a801f4026bcd2debe6f7323ae813ebbf69658dffb436358f`) and driver artifact `12846001745` (`c9c01bcf8fecfeaa34474e1b78693072fcfea0189e5fedb322924c1d8ce851df`) were also independently downloaded, CRC-checked and rehashed. Pose JSON remains byte-identical to prior verified native evidence at `2eb9888735444b6ba50282087eb48d0dff43604885e64c97ec0a0995a2c9035e`.
- The remaining six artifact digests are recorded from GitHub metadata in `docs/recovery_20261023/cloud_verification_20261028_run40754389702.json` without claiming independent byte download. No failed job, step or retry occurred.
- This verifies the report generator, schema, workflow publication and nonclaims in cloud CI. It does **not** validate a grip pose, contact, force, pressure, friction, slip, object fit, anatomical laterality/axes or return threshold; no native grip search ran.
