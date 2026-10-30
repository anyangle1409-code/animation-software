# W8 squat lower-chain trajectory plan

## Goal

Derive a strict, read-only authored hip–knee–ankle–toe control-chain record
from the already captured nine W8 squat samples. Bone heads remain explicitly
unverified anatomical joint centres and runtime suffixes remain unverified side.

## Method

1. Use thigh, shin, foot and toe control heads as authored points only.
2. Report each point's world-space change from sample 0.
3. Report hip-to-knee, knee-to-ankle and ankle-to-toe point distances as
   authored chain lengths, not human segment lengths.
4. Report an X-reflection disagreement proxy between runtime suffixes without
   claiming a verified sagittal plane or anatomical bilateral symmetry.
5. Validate exact sample/control/segment inventories, strict numeric types,
   derived deltas/distances, and non-anatomy limitation text.

## Verification

Add RED/GREEN synthetic tests, run focused/full suites and compile checks,
review evidence integrity, then require a fresh seven-job native run and
independent artifact hashes before interpreting W8 values.
