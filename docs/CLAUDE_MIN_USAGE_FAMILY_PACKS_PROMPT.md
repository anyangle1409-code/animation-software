# Minimal-usage validation prompt — reference family packs

> Open `work/internal-reference-family-packs-20260925`.
> Read only `docs/INTERNAL_REFERENCE_FAMILY_PACKS_STATUS.md`.
> Do not redesign the system and do not merge.
>
> Run:
>
> ```
> npm run typecheck
> npm test -- src/reference/worldChecks.test.ts src/reference/familyPacks.test.ts src/reference/reviewCamera.test.ts src/reference/evaluate.test.ts src/reference/measure.test.ts
> npm run build
> ```
>
> If green, run `npm test`.
>
> If an accepted exercise fails a draft reference pack, do not change the
> exercise and do not loosen existing mechanical validation. Report the exact
> reference check, measured value, expected envelope and phase/time.
>
> Report only READY/NOT READY, exact HEAD, focused result, full-suite result if
> run, and any measured draft-envelope failures.
