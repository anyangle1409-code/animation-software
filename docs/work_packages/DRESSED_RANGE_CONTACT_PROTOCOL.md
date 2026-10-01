# Continuous dressed range/contact sampling protocol

Stage 8 GPT preparation, not Phase 9 execution/completion. This stage adds a
deterministic finite movement-range sampler for the ORIGINAL-v1 body and garment,
plus an explicit per-sample contact-classification record. It extends the static
Stage 7 evidence without changing the model, canonical rig, R2 baseline, frozen
stress poses, thresholds or runtime exercise definitions.

The current real Blender deformation priority remains `RUN_ORIGINAL_V1_R30.bat`.

## Source plan and scope

The authoritative sampling plan is `ORIGINAL_V1_DRESSED_RANGE_PLAN.json`.
It uses only waypoints already defined by the frozen stress-pose source:

- neutral → curl_peak → neutral;
- press_bottom → press_top → press_bottom;
- pullup_hang → pullup_top → pullup_hang;
- neutral → squat_bottom → neutral;
- neutral → lunge → neutral;
- neutral → row → neutral.

Each segment uses 21 uniformly spaced normalized samples including endpoints;
shared waypoints are de-duplicated. Pose-bone matrix_basis transforms are
decomposed and interpolated with linear location/scale plus quaternion slerp.
The armature-object transform uses the same deterministic policy.

This is deliberately **model-range interpolation**, not proof of runtime exercise
biomechanics. The plan explicitly does not fabricate a continuous push-up path:
the frozen set contains `pushup_bottom` but no compatible independently authored
top/support endpoint. It also does not invent moving dumbbell/bar transforms:
`curl_handle` and `pullup_bar` remain static equipment-contact evidence until
a source-bound continuous equipment path or real runtime harness exists.

## Laptop execution

Entry requires a verified same-candidate Stage 7
`verified_dressed_evidence.json`. Check LIVE branch HEAD, reconcile newer work,
run the normal session preflight, set the verified `BLENDER_EXE`, and use a fresh
trial label:

```bat
RUN_ORIGINAL_V1_DRESSED_RANGE.bat rN "ORIGINAL_V1_WORK\candidates\dressed_evidence\rN_trial1\verified_dressed_evidence.json" trial1
```

The runner refuses stale/dirty branch state, conflicting Blender processes,
candidate/static-evidence identity drift and existing output folders. The Blend is
opened with factory startup and is never saved. Outputs live under
`ORIGINAL_V1_WORK/candidates/dressed_range/rN_trialN/`.

## Raw evidence per sample

`scripts/capture_original_v1_dressed_range_blender.py` first executes the
authoritative stress-pose script in metrics-only mode and reuses its actual
`POSES` functions to capture the declared waypoint states. For each deterministic
sample it records:

- exact path/segment/index and normalized sample time;
- pose-state SHA-256;
- exact body/garment intersecting face-pair list and pair-list SHA-256;
- bidirectional nearest body↔garment vertex-to-surface distance;
- body and garment lowest-Z;
- exact body and garment vertices below the floor;
- exact body and garment vertices within 2 mm of the floor.

The body visibility mask is disabled for measurement so garment coverage cannot
erase underlying body findings. Raw intersections and floor penetration are not
automatically defects or acceptable contacts. No new clearance threshold is
introduced.

The finite uniform policy is explicit. It does not mathematically prove unsampled
intervals, and Stage 8 does not claim adaptive refinement. If later runtime or
production evidence requires denser sampling around a peak defect, preserve this
run and create a new source-bound plan/revision rather than silently changing the
existing sample times.

## Explicit contact classification

The verifier writes `contact_classification.json` beside the raw range report.
Every sampled body/garment, body/floor and garment/floor domain is represented.

Allowed classifications:

- `NO_FINDING` — only when the raw evidence count is zero;
- `UNCLASSIFIED` — a raw finding exists and still needs evidence-backed review;
- `LEGITIMATE_CONTACT` — reviewed intentional contact with a concrete evidence note;
- `UNEXPLAINED_DEFECT` — reviewed finding that remains a defect.

The classification file is bound to the exact range-report SHA and candidate SHA.
Raw face-pair hashes, counts and floor vertex IDs must remain unchanged. A
`LEGITIMATE_CONTACT` or `UNEXPLAINED_DEFECT` entry requires a non-empty evidence
note. Classification never edits raw measurements and never by itself grants a
production PASS.

The default generated template leaves all real findings `UNCLASSIFIED`. That is
intentional and fail-closed.

## Verification and boundaries

`scripts/original_v1_dressed_range_evidence.py` verifies exact sample ordering,
times, source hashes, candidate/rig identity, pair hashes, floor IDs and finite
metrics. It refuses missing samples, altered raw evidence, classification source
mismatch, false `NO_FINDING` labels, unsupported classification values and
approval claims.

Stage 8 still leaves open:

- real continuous push-up support motion;
- continuous equipment/grip contact;
- adaptive/runtime-specific refinement where warranted;
- production clearance/contact thresholds;
- final legitimate-contact review;
- real runtime exercise biomechanics and smoothness;
- Phase 9 zero-failure evidence and owner acceptance.

This stage is therefore PREPARED tooling only. Actual Blender execution and
classification of real findings remain future evidence work. Phase 3/r30 remains
the model execution priority.
