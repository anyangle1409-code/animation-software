# Next action — Internal Reference Engine

Use branch:

`work/internal-reference-engine-r0-r1-20260925`

Do not redesign the reference engine from scratch.

## First

Run:

```
npm run typecheck
npm test -- src/reference/evaluate.test.ts src/reference/generation.test.ts
npm run build
```

Inspect any failure rather than weakening the accepted exercise or a validation threshold.

The curl reference is intentionally `draft`. If one of the four accepted curl
variants falls outside a draft envelope, print the measurement and adjust the
reference only if the envelope itself is shown to be wrong.

When focused checks are green, run `npm test` and confirm the existing library
clips remain byte-identical.

## Then

Implement R2 only:

**automatic review evidence for a generated candidate**

- define a review manifest;
- capture semantic phase times;
- define family review camera ids;
- for curl capture front, side, three-quarter and grip-close-up views;
- keep rendering/capture local;
- do not add visual AI yet;
- do not change exercise mechanics.

Reference QA should first appear as read-only evidence beside the existing
mechanical generator report.

Do not let it participate in auto-correction until the curl reference and review
capture are proven trustworthy.

## Protected state

- source baseline at branch creation: `8ec5247f9a5ef53dd023b3ebb7dd26339fac3060`
- 28 library exercises
- prompt-certified: curl, overhead press, squat, lunge
- source suite at handoff: 868 passed / 1 skipped
- frozen 63-bone hierarchy remains untouched
- production assets remain untouched
