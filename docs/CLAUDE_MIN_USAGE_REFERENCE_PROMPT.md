# Minimal-usage Claude prompt

Copy/paste this into Claude when usage is tight:

> Open `anyangle1409-code/animation-software` branch
> `work/internal-reference-engine-r0-r1-20260925`.
> Do not redesign or extend it.
> Read `docs/INTERNAL_REFERENCE_ENGINE_IMPLEMENTATION_STATUS.md` and
> `docs/INTERNAL_REFERENCE_ENGINE_NEXT_ACTION.md`.
> Run only:
>
> ```
> npm run typecheck
> npm test -- src/reference/evaluate.test.ts src/reference/generation.test.ts src/reference/reviewManifest.test.ts src/reference/measure.test.ts
> npm run build
> ```
>
> If those pass, run `npm test`.
> Do not modify the live source branch, production assets, rig, exercises, grip
> or validation thresholds. Do not merge anything.
>
> Report only:
> - READY or NOT READY;
> - exact branch HEAD;
> - focused test/typecheck/build result;
> - full-suite result if run;
> - any failing reference check with its measured value and expected envelope.
>
> If a draft reference test fails an accepted curl, do not change the exercise.
> Stop and report the measurement.

The optional read-only UI integration lives separately on
`work/internal-reference-engine-readonly-ui-20260925`. Do not validate that
until the core branch above is clean.
