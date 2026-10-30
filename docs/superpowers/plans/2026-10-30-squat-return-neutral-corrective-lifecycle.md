# Squat return-to-neutral corrective lifecycle plan

## Scope

Extend the existing hash-pinned, read-only W8 squat probe. Do not change the
frozen r57 benchmark or driver, save a blend, or claim anatomy/movement safety.

## Evidence question

The frozen benchmark resets every pose bone after its ninth squat sample, but
does not invoke its optional post-pose driver after that final reset. Determine
whether skeletal controls return to neutral while corrective shape-key values
and evaluated geometry remain at a stale terminal state, and whether one call
to the unchanged driver at neutral clears that state.

## Implementation

1. Add pure helpers for strict shape-key snapshots and same-topology geometry
   delta summaries (changed vertex count, maximum and RMS displacement in mm).
2. Retain sample-0 evaluated coordinates only in memory.
3. After `bench.run()` returns, update evaluation and capture skeletal reset,
   active corrective keys, and evaluated geometry delta versus sample 0.
4. Call the unchanged `drives.drive(rig, body)` once, update evaluation, and
   capture the same evidence after neutral driver refresh.
5. Validate exact stage labels, strict booleans/numbers, stable topology,
   fingerprints, and the semantic relationship to sample 0. Publish a concise
   phone-readable table with explicit non-anatomy and non-tissue-safety limits.

## Test-first cases

- Geometry summary rejects topology mismatch/nonfinite/bool coordinates and
  correctly reports zero and nonzero displacements.
- Shape-key state rejects duplicate names and nonfinite/bool values and has a
  deterministic all-values fingerprint.
- Report validation rejects swapped stages, false neutral claims, tampered
  shape-key state, geometry summaries, and missing limitations.
- Source guard continues to forbid blend writes.

## Verification

Run the focused unit suite, the full standard-library suite, compile checks,
then publish and require a fresh seven-job cloud run. Independently download,
CRC-check, and hash the W8 squat artifact before interpreting native values.
