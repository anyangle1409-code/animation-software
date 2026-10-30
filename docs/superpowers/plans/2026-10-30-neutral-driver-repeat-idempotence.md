# Neutral driver repeat-idempotence plan

## Goal

Determine whether the frozen r57 neutral driver settles once or continues to
drift when called repeatedly, without modifying or saving any model state.

## Method

1. Retain evaluated vertices from the first neutral refresh in memory.
2. Invoke the unchanged driver a second time at the same neutral skeletal pose.
3. Capture the existing strict skeletal and shape-key fingerprints again.
4. Report a same-topology first-to-second evaluated-geometry delta and exact
   fingerprint-equality booleans derived from the captured stages.
5. Keep all anatomy, attachment, tissue-safety and movement approvals false.

## Verification

Add RED/GREEN regressions for stage order, strict refresh counts, derived
fingerprint booleans, topology binding and tampered repeat deltas. Require
focused/full tests, compile checks, fresh seven-job cloud success and
independent artifact hashes before classifying the residual as stable or drift.
