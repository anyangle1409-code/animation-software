# W8 squat lower-chain angle-geometry plan

## Goal

Derive unsigned authored segment-orientation changes and included knee/ankle
point-chain angles from the verified hip–knee–ankle–toe paths. These are
geometric rig proxies only, never ISB joint coordinates or anatomical ROM.

## Method

1. For each runtime suffix, compute thigh (hip→knee), shank (knee→ankle) and
   foot (ankle→toe) direction changes relative to sample 0 using finite vector
   dot products clamped to `[-1, 1]`.
2. Compute the included hip–knee–ankle and knee–ankle–toe point angles and
   their changes from sample 0.
3. Preserve exact sample/control inventories and strict nonfinite/zero-length
   rejection; add hand-calculated independent regressions.
4. Publish phone-readable values without signed axes, anatomical side labels,
   clinical limits, motion approval or claims of natural coordination.

## Verification

Run focused/full tests and compile checks, independent evidence review, then a
fresh seven-job native workflow with independently verified artifact hashes.
