# Optional read-only reference-QA integration

Branch:

`work/internal-reference-engine-readonly-ui-20260925`

Base:

`work/internal-reference-engine-r0-r1-20260925`

This branch goes one step beyond the core reference implementation.

## What it changes

- `GenerationResult` gains optional `referenceQA`.
- Final generated **curl** candidates run the draft local curl reference.
- The Generate panel displays the independent reference checks.
- Existing generator `status` is unchanged.
- Existing correction logic never sees reference failures.
- Approval rules are unchanged.
- Non-curl generation is unchanged.

This is intentionally **read-only evidence**.

A reference PASS cannot promote an unverified or mechanically failed candidate.
A draft reference FAIL cannot block a mechanically passed candidate yet.

## Why keep this separate

The independent curl envelope has not been executed in this environment against
the repository test suite. The core R0/R1 branch can therefore be validated
first without also taking a UI integration change.

If the core tests pass, validate this branch with:

```
npm run typecheck
npm test -- src/reference/evaluate.test.ts src/reference/generation.test.ts src/reference/reviewManifest.test.ts
npm run build
npm test
```

Then manually generate:

```
Create a standing dumbbell curl with 10 kg dumbbells.
Create a standing hammer curl with 12 kg dumbbells and controlled tempo.
Create an incline dumbbell curl at 45 degrees with 8 kg dumbbells.
```

Confirm:

- existing mechanical status is exactly as before;
- a new "Independent reference QA" section appears;
- no reference result changes approval state;
- no library clip changes.

Only after the reference values themselves are reviewed should reference QA
be considered for gating or correction.
