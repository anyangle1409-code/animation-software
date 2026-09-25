# Automatic review-image UI — status

## Branch

`work/internal-reference-auto-review-ui-20260925`

Built on the browser capture bridge branch.

## Implemented

For the first independent reference family (curl):

- after a generated curl is previewed, if the browser capture bridge is mounted,
  a local deterministic review batch is captured automatically;
- capture failure never changes the generator result;
- evidence is stored only in the in-memory candidate;
- the Generate panel shows capture progress, any capture error, or a collapsible
  gallery of the locally generated review images;
- Blob object URLs are revoked when the evidence changes/unmounts.

This is still **evidence only**. The images do not yet vote on PASS/FAIL.

## Why this branch is separate

It proves the end-to-end path:

```
prompt
 -> generated candidate
 -> viewport
 -> semantic review manifest
 -> local PNG captures
 -> Generate-panel evidence
```

without coupling image capture to approval.

## Validation required

Run:

```
npm run typecheck
npm run build
npm test
```

Then in the browser generate a supported curl and verify:
- normal generator status is unchanged;
- review capture begins automatically;
- 20 images appear;
- images match the expected semantic moments/views;
- the user's viewport state returns after the batch;
- discarding/replacing evidence does not leak object URLs;
- a capture error leaves the candidate usable.

Do not make review images approval-gating until deterministic landmark/silhouette
QA has been independently validated.
