# Final rig intake — completed for the shoulder-girdle baseline

The canonical-rig intake was completed on 2026-09-23.

## Confirmed

- source commit: `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`
- `chatgpt/absolute-retarget-imports`: verified at that commit
- `claude/home-gym-pt-animation-txux66`: verified at that commit
- canonical count: 55 bones
- `scapula_l/r`: neutral at rest
- scapular rhythm: disabled
- scapula skin weights: not painted
- upper-arm limits: unchanged
- retargeter: nearest mapped descendant for rest direction; nearest mapped ancestor for attachments
- mannequin baked skin: resolved through the 53 baked bone names
- export skeleton id: `hgpt_canonical_v2`
- suite: 388 passed / 1 skipped; typecheck/build clean
- no production GLB/Blend asset was changed by this commit

See `RIG_55_BASELINE.md` for the accepted equivalence evidence and mesh implications.

## Meaning for the high-detail mesh

Do **not** rebind V6 merely because the canonical runtime rig now has 55 bones. Current scapula-less character assets remain supported through the retarget fallback and were proven equivalent.

The next asset-level shoulder stage is separate:
1. keep/build suitable shoulder/back/chest/armpit topology
2. introduce/use scapula deform influences in a candidate character asset when the binding pass starts
3. prove neutral equivalence
4. paint/tune local girdle weights
5. only later enable/tune scapular rhythm

## Remaining pre-final-weight decisions

Still open unless a later source commit settles them:
- palm-arch / hand-base decision
- thumb-twist decision
- forearm twist distribution
- carrying angle

The hand-base/thumb decision blocks **final hand weighting**, not knee retopology, hand geometry or material work.

## External consumer warning

Animation exports from this baseline are `hgpt_canonical_v2`: two extra joints are present and upper-arm local rotations are relative to the scapula. Any external consumer still assuming the 53-joint v1 layout must be updated before consuming new exports.
