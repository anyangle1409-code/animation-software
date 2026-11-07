# Home Gym PT — Option 5 standing alignment handoff (2026-11-07)

Branch: `chatgpt/option5-standing-alignment-20261107`

## Status

Two new standing-only approval candidates were derived without overwriting the approved/rollback checkpoints.

- Male source: `HGPT_MaleV1_AthleticBack_StandingApprovalCandidate.blend`
  - restored SHA-256: `4a5e4a0cd037febb4d66ba5c354a34e088b1f696805106c4532c27f684f74748`
- Female source: `HGPT_Female_F16b_Front_Panel_WIP.blend`
  - restored SHA-256: `61e056ede724a4ac81bc5159bb8cf0a528d2de347bc2d96410bb880b2274928a`
- Female F11a remains the rollback checkpoint.
- Male 07c and the prior athletic-back candidate remain unchanged.

## New candidates

- Male Option 5 standing candidate
  - SHA-256: `db79984aba305c42c1fe5ebd0cf5d18d2cfd9a611673d502e3475cb18669399a`
  - [Library file](https://chatgpt.com/library?file_id=libfile_30f027d95a048191a36eec0e3a4a7f7b&account_id=personal)
- Female Option 5 standing candidate
  - SHA-256: `3617189bf6d1b67dba9dd9f91c053b56e163922f94f9d71cd4b43a1c67660835`
  - [Library file](https://chatgpt.com/library?file_id=libfile_90c991351484819190677d85972968a7&account_id=personal)

## Visual intent

- Male: reduce bodybuilder-style volume in chest, lats, upper arms, forearms, thighs and calves while retaining the approved waist, face, shorts coverage and natural lower-back arch.
- Female: retain the approved feminine proportions and front shorts fit while adding only subtle Option 5 athletic balance through shoulders, waist, arms and calves.

## Verification

Both candidates opened successfully in Blender 5.2.2 LTS.

- Male: 56,677 body vertices; 81 bones.
- Female: 50,090 body vertices; 69 bones.
- Source/candidate polygon topology matches exactly.
- Armature rest matrices match exactly.
- High-weight head, hand and foot vertices are unchanged.
- Lower-back/lumbar side-profile coordinates are unchanged.
- Three physique-policy tests pass.
- SHA-256 hashes are recorded above.

## Approval renders

- [Combined front approval](https://chatgpt.com/library?file_id=libfile_1b790d5f302c81919ef4d94477b1a521&account_id=personal)
- [Male four-angle sheet](https://chatgpt.com/library?file_id=libfile_30c125511234819196aebd6ba0beb0d2&account_id=personal)
- [Female four-angle sheet](https://chatgpt.com/library?file_id=libfile_41becca7bca48191971e714c65baca18&account_id=personal)

## Gate

These are standing-pose approval candidates only. Do not mark Male V1 or Female V1 approved until the owner explicitly approves the renders. Do not begin exercise animation from this handoff.
