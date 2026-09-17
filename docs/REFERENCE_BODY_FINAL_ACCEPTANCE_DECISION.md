# Reference body — final acceptance decision before promotion

**Branch:** `chatgpt/absolute-retarget-imports`  
**Decision based on HEAD:** `07d5e940e521d58d49818e6323b82c33328eee8f`  
**Phases 1–5 are complete. Nothing is promoted or merged by this decision.**

This document resolves the two carried-forward items in `docs/REFERENCE_BODY_PHASE5_REVIEW_PACK.md` and defines the next step. It does **not** authorize production promotion or a merge.

## Decision 1 — accept the retained push-up wrist on rest-relative anatomy

Keep the retained Push-up floor contact at:

- `z = 1.295`
- raw character forearm/hand axis angle: **81.18°**
- character hand-to-forearm bind/rest offset: **14.62°**
- actual wrist rotation from the character's own rest orientation: approximately **66.6°**

The earlier 70–75° target was useful as a diagnostic band, but it was expressed as a raw axis-angle target and does not account for this character asset's built-in 14.62° hand-to-forearm rest offset.

The measured geometry also proves that forcing the raw axis angle into 70–75° conflicts with the authored `forearm_vertical` push-up rule: the required hand placement is around `z = 1.34`, while `z = 1.30` already exceeds the rule's 60 mm elbow-to-wrist `dz` cap.

Therefore the final acceptance criterion for this character is:

> **Judge push-up wrist extension relative to the character's own neutral/rest hand-to-forearm orientation, not by the raw forearm/hand world-axis angle alone.**

Retain `z = 1.295` because it gives about **66.6° actual extension from rest**, keeps the palm planted, preserves the authored near-vertical-forearm technique requirement, remains bilateral, and passes all authored push-up rules.

Do **not**:

- move the hands farther forward merely to make the raw axis angle read 70–75°;
- weaken `forearm_vertical` to force that number;
- change weights, Stage 1 geometry, Stage 2 proportions or the retained 0.50 forearm twist-helper share for this reason.

This resolves the push-up wrist item as an accepted asset-relative criterion rather than an unresolved defect.

## Decision 2 — `strainReview` timeout is non-blocking unless reproducible

The final retained run completed at **298 passed / 1 skipped / 0 failed**, and the intermittent `strainReview` 5 s timeout did not reproduce.

Treat the historical timeout as environmental/flaky, not as a product defect and not as a blocker to acceptance.

Do not change the code under test for a timeout that is not reproducible. If it returns consistently under full-suite load while still passing in isolation, the permitted response is a targeted per-test timeout adjustment after confirming the test result itself is unchanged.

## Final candidate identity

Before any later promotion action, verify the local candidate files still exist and match these recorded SHA-256 values exactly:

| Role | File | SHA-256 |
|---|---|---|
| Body | `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE.glb` | `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0` |
| Dressed | `scratchpad/reference-fit/HomeGymPT_Male_STAGE2_CANDIDATE_SHORTS.glb` | `841b01d6abb5649af8929f6b147b6aafbf95da4ecf13c2ea09f7f3e570306d72` |

These assets are gitignored. Do not delete, overwrite or regenerate them as part of this decision. If either hash does not match, stop and report before any promotion step.

## Next action — acceptance/readiness only

Perform a short final acceptance/readiness close-out:

1. Treat Phases 1–5 as complete and locked.
2. Update `docs/REFERENCE_BODY_PHASE5_REVIEW_PACK.md` so the push-up wrist item is recorded as **accepted by rest-relative rotation (~66.6°)** rather than left unresolved.
3. Keep the flaky `strainReview` timeout documented as non-blocking historical evidence.
4. Confirm the two final candidate files exist locally and hash-match the values above.
5. Confirm the tracked tree is clean apart from the documentation commit(s) required for this close-out.
6. Do **not** rerun the expensive full suite solely for documentation changes; the final validated code state already passed 298 / 1 / 0. If any executable code or asset is changed unexpectedly, then re-run the appropriate validation before reporting readiness.
7. Return a concise **promotion-readiness report** stating the branch HEAD, candidate hashes, final validation state, accepted push-up wrist interpretation, and that nothing has been promoted or merged.

After this close-out, stop. Production promotion / replacing bundled assets / merging remains a separate explicit user decision.

**Do not promote. Do not merge. Keep usage low.**
