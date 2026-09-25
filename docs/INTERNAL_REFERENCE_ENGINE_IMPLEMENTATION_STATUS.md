# Internal Reference Engine — implementation status

## Branch

`work/internal-reference-engine-r0-r1-20260925`

This branch was forked from the planning branch, which was itself created from source HEAD:

`8ec5247f9a5ef53dd023b3ebb7dd26339fac3060`

No production/source branch was modified.

## Implemented here

### R0 — reference contract

Added:

- `src/reference/types.ts`
- `src/reference/library.ts`
- `src/reference/index.ts`
- `src/reference/report.ts`

The contract supports:

- versioned reference specifications;
- independent numeric envelopes;
- joint-angle envelopes;
- joint excursion;
- root/support angle;
- mirrored bilateral symmetry;
- semantic phase order;
- world-landmark monotonicity;
- PASS / FAIL / SKIP results;
- explainable measurements and expected limits.

### R1 — first curl evaluator

Added:

- `src/reference/specs/curl.ts`
- `src/reference/evaluate.ts`

The draft curl reference currently checks:

1. curl phase order;
2. bottom elbow extension;
3. peak elbow flexion;
4. total elbow ROM;
5. upper-arm sagittal corridor;
6. upper-arm excursion;
7. upper-arm abduction corridor;
8. grip orientation (supinated / neutral / pronated);
9. wrist flexion/extension neutrality;
10. wrist side-to-side neutrality;
11. quiet torso;
12. relaxed clavicle;
13. standing vs incline root angle;
14. elbow bilateral symmetry;
15. grip bilateral symmetry;
16. upper-arm bilateral symmetry;
17. monotonic hand/dumbbell rise;
18. monotonic hand/dumbbell lowering.

The reference is intentionally marked `draft`, not `certified`.

Its numeric envelopes are stored in the reference spec and are not read from
`curlFamily()` at runtime.

### R2a — deterministic review manifest

Added:

- `src/reference/reviewManifest.ts`
- `src/reference/reviewManifest.test.ts`

The curl reference now owns four local review views:

- front;
- side;
- three-quarter;
- grip close-up.

`buildReviewManifest()` converts a clip into five semantic review moments:

- start/stretch;
- mid concentric;
- peak/contraction;
- mid eccentric;
- return.

It crosses those moments with the family camera set, producing a deterministic
20-capture manifest for a curl. This is capture **planning only**; no renderer,
image model or network dependency has been added.

### Tests prepared

Added:

- `src/reference/evaluate.test.ts`
- `src/reference/generation.test.ts`

The tests are designed to prove:

- accepted bicep, hammer, reverse and incline curl clips clear the draft reference;
- deleting the exercise's own technique rules does not delete reference QA;
- deliberately shortened elbow ROM fails;
- a false neutral grip on a declared supinated curl fails;
- excessive upper-arm involvement fails;
- left/right corruption fails;
- wrong phase order fails;
- a prompt-generated curl can be reference-reviewed without changing generator behaviour;
- reference QA cannot turn skipped production-character body checks into a generator PASS.

## Deliberately not wired into production yet

The reference engine is additive and currently has no effect on:

- `src/generation/generate.ts`;
- family builders;
- existing exercise definitions;
- rig or retargeting;
- grip;
- production assets;
- approval/promotion behaviour.

That is intentional until the evaluator has been run and its independent
reference values reviewed.

## Validation still required on the laptop

This environment can read/write the GitHub repository but cannot execute the
repository's npm toolchain. The next laptop/Claude/Work session should run:

```
npm run typecheck
npm test -- src/reference/evaluate.test.ts src/reference/generation.test.ts src/reference/reviewManifest.test.ts
npm run build
```

If the focused tests are green, run the complete suite:

```
npm test
```

Expected protection target before any integration:

- all existing 28 library clips remain byte-identical;
- current source suite remains green;
- no production asset change.

## If a draft curl reference check fails an accepted curl

Do **not** change the exercise merely to make the new reference test pass.

Instead:

1. print the failing reference measurement;
2. decide whether the reference envelope is too narrow or the accepted exercise exposes a real reference problem;
3. update the draft reference only with a recorded reason;
4. keep it `draft` until the envelope is independently reviewed.

## Next code step after focused tests pass

Do not jump immediately to all families.

Proceed in this order:

1. connect the existing review manifest to local image capture/rendering (finish R2);
2. expose the reference report beside generator mechanical QA, initially read-only;
3. only then connect reference failures to existing bounded family levers (R4);
4. certify additional reference families in the same order as prompt generation.

No reference failure should directly edit bones.
