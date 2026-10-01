# First-party push-up / equipment contact source bridge

Stage 9 GPT preparation. This package closes the *source-definition* gap identified
after Stage 8. It does not execute the animation runtime, does not add Blender
stress poses and does not claim Phase 9 or Phase 10 completion.

The current model/Blender priority remains `RUN_ORIGINAL_V1_R30.bat`.

## Why this bridge exists

Stage 8 correctly refused to invent:

- a continuous push-up range from `neutral` to `pushup_bottom`;
- moving dumbbell transforms;
- moving pull-up-bar transforms.

The repository already contains first-party authored answers for these domains, but
they belong to the exercise/runtime system, not the frozen Blender stress-pose
protocol. Stage 9 therefore records and verifies those source semantics without
copying them into a second motion implementation.

The bridge contract is `ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.json`. The verifier is
`scripts/original_v1_contact_source_bridge.py`.

## Verified source semantics

### Push-up

The project-owned `push_up` definition is built by `horizontalPressFamily`.
Its authored runtime path has a real top and bottom, not the synthetic neutral
pose used by the Stage 8 model-range sampler.

The bridge verifies from source:

- top root pitch/placement: 75.59°, y 0.1804 m, z 0.0045 m;
- bottom root pitch/placement: 85.54°, y 0.2062 m, z 0.0382 m;
- left hand world target: (-0.3, 0.055, 1.295) m, mirrored bilaterally;
- world-locked hand contact;
- floor grip semantics;
- planted toe-contact rule;
- start label Top and peak label Bottom.

These facts remain runtime-source evidence. Do **not** reproduce them as a new
Blender pose family merely to make Stage 8 look complete.

### Dumbbell bicep curl

The bridge verifies that `dumbbell_bicep_curl` is built by `curlFamily` with
the supinated grip, and that each dumbbell is attached in `hand` mode to its
`grip` socket. The equipment library's dumbbell grip socket is at its authored
local origin.

Most importantly, `equipment/attach.ts` resolves a hand-attached implement from
the **real evaluated hand matrix** multiplied by the local grip/socket transform.
Therefore future continuous dumbbell evidence must call the real resolver at every
sampled runtime frame. Stage 8 must not invent a separate dumbbell trajectory.

### Pull-up

The bridge verifies that `pull_up` is built by `verticalPullFamily`, with:

- dead-hang root y -0.0631 m, z -0.06 m;
- top root y 0.5 m, z -0.2 m;
- a static squat-rack equipment instance;
- bilateral equipment locks to the rack's `pullup_l` / `pullup_r` sockets;
- bar-grip semantics;
- pull-up socket height 1.97 m and first-party body-relative horizontal spacing.

The rack is static. The **body moves relative to a fixed bar**. Do not create a
moving bar interpolation for model evidence.

## Source evidence command

On a clean reconciled checkout:

```bat
RUN_ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.bat
```

or choose a fresh repository-relative output path:

```bat
RUN_ORIGINAL_V1_CONTACT_SOURCE_BRIDGE.bat "ORIGINAL_V1_WORK\contact_source_bridge\stage9_trial1.json"
```

The verifier reads all declared project-owned source files, calculates SHA-256 for
the exact bytes, checks the current authored constants and contact/attachment
signatures, and writes an EVIDENCE_ONLY packet. Existing output is never
overwritten.

If any source semantics change, the verifier stops. Reconcile the change and update
the bridge deliberately; never silently accept drift.

## Critical branch boundary

This model branch is **not** automatically the live standalone runtime target.
The bridge proves only the exact current model-branch source semantics.

Before Phase 10 execution:

1. discover the actual live standalone runtime branch and commit read-only;
2. compare the corresponding exercise/contact/equipment definitions;
3. bind the runtime evidence harness to that exact commit;
4. use the real solver and equipment resolver;
5. record any semantic difference instead of copying old model-branch runtime code.

Never merge this model branch wholesale into the standalone runtime.

## Required later runtime capture

The bridge specifies the minimum future packet:

- exact live runtime commit;
- exercise-definition identity;
- deterministic frame times;
- real solver pose evaluation;
- resolved equipment transforms;
- bilateral hand/floor contact error;
- body/garment clearance/contact;
- continuity and turnaround metrics;
- source-bound images/clips;
- export/reimport identity.

For push-up this means the actual Top→Bottom→Top runtime path with fixed hand/toe
contacts. For curl it means actual hand-resolved dumbbell transforms at every
sample. For pull-up it means actual body motion against fixed rack sockets.

This package intentionally stops before that execution boundary. It adds no
third-party input, no legacy V-series data and no production approval.
