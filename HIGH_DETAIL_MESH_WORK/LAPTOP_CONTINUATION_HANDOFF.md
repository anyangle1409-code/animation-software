# Laptop continuation handoff

Purpose: let Work spend its time in Blender rather than rediscovering state or rebuilding validation setup.

## Exact baselines

Mesh geometry baseline:
- branch: `codex-high-detail-candidate-v6-knee-review-20260922`
- V6 asset commit: `b2203cfccd30d6835473ef2e1dee37965da22d02`
- dressed GLB SHA-256: `ff39e07735697d5423968a8ec1c05f2c6c68fced0d757ea1b4047096bc7a5306`
- bare GLB SHA-256: `0170b3673d7a050e8aacd2683347cfa6dd000719dba0a6862c16bd7a4a5723e0`
- Blend SHA-256: `2a2d0326129ce5c2555c596a49a281d655f33acfd7bbd9514cad3e759586a0df`
- 33,089 body vertices / 62,961 triangles

Canonical runtime baseline:
- commit: `c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`
- 55 bones
- `scapula_l/r` between clavicle and upper arm
- scapulae neutral, rhythm off, no scapula weights
- export ID `hgpt_canonical_v2`
- 388 passed / 1 skipped; typecheck/build clean

The scapula commit changes runtime/source structure, not the production character GLB binary. Existing scapula-less character assets are supported by the retarget fallback and were proven equivalent.

## V6 open work

Knee:
- V6 aligned two nearly coincident medial boundary strips to 0 mm gap
- the strips remain topologically open
- the pointed medial-knee overhang remains
- next step is real connected anatomical knee loops plus deliberate patella/tendon/medial shaping

Hands:
- V5/V6 provide denser contact-safe topology
- preserve the 682 push-up floor-contact guard vertices
- improve finger volume, thumb web/base, palm and wrist geometry
- do not finalise hand weights before the hand-base/thumb-twist decision

Shoulder:
- shoulder/scapula structure is now confirmed
- geometry/topology planning may proceed against it
- final scapula deform weighting still requires a candidate asset with actual scapula influences and fresh neutral-equivalence proof
- rhythm remains off

Materials:
- may proceed independently while production assets remain untouched

## Laptop flow

```text
RESUME_WORK.bat
START_CANDIDATE.bat <version>
```

Edit in Blender and export the dressed GLB using the same version suffix.

Then:

```text
FINISH_CANDIDATE.bat <version> <task>
```

The finish workflow creates the bare variant if missing, validates against rig v2/c2372c1, runs the task audit, renders review sheets and writes checkpoint metadata.

## Stop conditions

Stop rather than forcing a visual fix if an edit:
- changes accepted exercise mechanics, IK, grips, contacts or equipment transforms
- requires loosening a guard
- unexpectedly changes hand floor contact
- requires scapular rhythm just to make a mesh-only candidate acceptable
- creates unexplained rig/skin/retarget differences

Preserve every previous candidate. No production promotion without explicit approval.
