# Neutral driver residual localization plan

## Goal

Localize the verified post-neutral-driver matrix-basis residual by authored
control name without changing the frozen driver, rig, model or source blend.

## Method

1. Extend the existing skeletal basis snapshot with deterministic maximum
   rotation/translation control names and a sorted list of controls exceeding
   the existing `0.000001` degree/mm identity tolerances.
2. Keep the aggregate values and exact 77-control inventory gate unchanged.
3. Add strict pure-Python regression fixtures for deterministic ties, boolean
   rejection, malformed/tampered control rows and mismatch between the readable
   list and aggregate maxima.
4. Publish the expanded phone table and run the same pinned W8 native workflow.
5. Map the observed control name to its existing driver subsystem from frozen
   r57 source only; do not edit the driver or declare an anatomy defect.

## Verification

Require focused/full tests, compile checks, fresh seven-job cloud success, and
independent ZIP/member hashes before reporting the responsible control.
