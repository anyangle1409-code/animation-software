# Reference body — promotion to the bundled production assets

**Branch:** `chatgpt/absolute-retarget-imports`
**Promotion performed from:** `4eeb761`
**Not merged.**

The two verified final candidates from `docs/REFERENCE_BODY_PHASE5_REVIEW_PACK.md` are now the
bundled production assets. One production-only issue was found during validation and is stated
below; it is **not** a regression, but it means the shipped default character does not receive
the locked Phase 1 grip. That needs a decision before this counts as fully delivered.

## What was promoted

| Production file | Source candidate | SHA-256 (verified after promotion) |
|---|---|---|
| `public/characters/HomeGymPT_Male_BASELINE_v8.glb` | `HomeGymPT_Male_STAGE2_CANDIDATE.glb` | `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0` ✓ |
| `public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb` | `HomeGymPT_Male_STAGE2_CANDIDATE_SHORTS.glb` | `841b01d6abb5649af8929f6b147b6aafbf95da4ecf13c2ea09f7f3e570306d72` ✓ |

Both were copied byte-for-byte and re-hashed in place after promotion. Both match the recorded
values exactly, so the promoted production assets are the same bytes the review pack validated.

Reference updates, the whole of the code change:

- `src/character/bundled.ts` — `BASELINE_CHARACTER_URL` and `DRESSED_CHARACTER_URL` now name the
  v8 files.
- `public/characters/.gitignore` — the drop-in note names the v8 files.

v7 and v6 remain in `public/characters/` as A/B fallbacks, unchanged and unreferenced, matching
how v6 was retained when v7 was promoted.

## Validation of the actually bundled result

Every focused figure below was measured on the files in `public/characters/`, not on the
candidates in the scratchpad.

| Check | Bundled v8 body | Review pack | |
|---|---|---|---|
| Renderer vs exporter handle transform | 0.0000 mm at t = 0, 2, 4, both sides | 0.0000 mm | ✓ |
| Grip contact, curl t = 2, shipped path | fingers −0.46 / −0.36 / −0.22 / −0.11 mm, 0 inside; thumb +1.18; palm −2.54, 2 inside; wrap 252° | identical | ✓ |
| Forearm twist, push-up Bottom | `forearmL` 9.1° → helper `forearmL001` **21.0°**, hand 57.7° | 21.0° / 57.7° | ✓ |
| Forearm twist, push-up Top | 31.7° → 42.9°, hand 57.7° | — | ✓ |
| Forearm girth bins, posed Bottom | 58.7 / 51.7 / 48.6 / 41.5 / 37.4 / 32.9 mm over 177 vertices | identical | ✓ |
| Push-up wrist | extension **81.18°**, bind offset 14.62°, L/R mismatch 0.0001°, decomposition residual 0.0000° | 81.18° / 14.62° | ✓ |
| Dumbbell-to-thigh clearance, curl Bottom / Return | **+4.68 / +4.79 mm, 0 vertices inside** | +4.68 / +4.79 mm | ✓ |
| Bone naming / skeleton discovery | clean | — | ✓ |

Whole-project gates after promotion: **typecheck clean**, **build clean**, **full suite 38 files,
298 passed / 1 skipped / 0 failed**. The `strainReview` timeout did not reproduce.

## Production-only finding — the shipped default does not get the solved grip

**The dressed file is the app's default character**, because `registerBundledCharacters` calls
`registerBundledCharacter` for it, which calls `setDefaultCharacter`. It is what the app shows
unless someone picks the bare body in the Character panel.

`retargetSource.ts` only wires up a solved grip when the GLB carries its own
`handleGripOffsets`: that extra is what sets `gripOffset`, and `gripSolutionId` falls back to
`'homeGymPTMale'` only when those offsets are present. Measured on the bundled files:

| Bundled file | `gripSolutionId` | `gripOffset` (left) |
|---|---|---|
| v8 body | `homeGymPTMale` | (0.0174, 0.0452, 0.0083) |
| **v8 dressed (shipped default)** | **NONE** | **NONE** |
| v7 body | NONE | NONE |
| v7 dressed | NONE | NONE |

`0.0452` is the authored `0.0542` less the locked −9 mm handle centre, so the bare body does
receive the full Phase 1 solution. The dressed file receives none of it.

The visible consequence is the dumbbell-to-thigh clearance that Phase 1 was partly built to fix:

| Bundled file | Curl Bottom / Return clearance | Vertices inside |
|---|---|---|
| v8 body | **+4.68 / +4.79 mm** | 0 |
| **v8 dressed (shipped default)** | **−16.66 / −16.62 mm** | 8 |
| v7 body (current production) | −16.56 / −16.61 mm | 3 |
| v7 dressed (current shipped default) | −16.56 / −16.61 mm | 8 |

**This is not a regression.** The shipped default moves from −16.56 mm to −16.66 mm, 0.1 mm on
the same 8 vertices — the residual of the Stage 2 shoulder shift with no solved grip to absorb
it, not a new fault. Every other measured figure is equal or better, and the bare body improves
from a 16.6 mm penetration to 4.7 mm of real clearance. Promotion is therefore safe to keep.

What it does mean is that the Phase 1 grip work, including the thigh-clearance fix, currently
reaches only the deformation-review character and not the one the app shows.

The body inside the dressed file is the same body, which is what makes this fixable rather than
a rebuild: mesh `Mike_Freeman`, 10,839 vertices, **worst vertex difference 0.0000 mm** against
the bare body, same 160 bones. The grip was solved on exactly these fingers, so the same offsets
are valid there. The dressed file is simply missing the metadata — `dress.mjs` rebuilds scene
extras from a template and does not carry `handleGripOffsets` through.

Two remedies, both needing a decision I did not take:

1. **Rebuild the dressed asset** carrying `handleGripOffsets` through `dress.mjs`. Correct at the
   source and keeps the rule that a solved grip belongs to the body that carries its offsets —
   but it produces new bytes, so the recorded dressed SHA-256 no longer applies and the file
   needs re-verification. I did not do this: the instruction was to verify the promoted files
   still match the recorded hashes exactly, which rules out altering them.
2. **Let the dressed registration declare the same solution** in `bundled.ts` or
   `retargetSource.ts`. No new asset, but it is an executable-code change beyond promotion, and
   it loosens the deliberate rule in `retargetSource.ts` that a solved grip is only offered to a
   character carrying its own handle offsets.

My recommendation is (1), with the new hash re-verified and the thigh-clearance figure re-measured
on the rebuilt dressed file before it is treated as delivered.

## Also noted

`public/characters/HomeGymPT_Male_BASELINE_v7_SHORTS.glb.correspondence.json` has no v8
counterpart. Nothing in `src/` reads it — it is consumed only by the `clothing`, `waistband` and
`clothdebug` diagnostics, which read `${glbPath}.correspondence.json`. So production is
unaffected, but those three garment harnesses cannot run against the promoted dressed file until
`scratchpad/repair/shorts.mjs` regenerates one for it.

## Status

Promoted, validated and recorded. Not merged. The shipped default's missing solved grip is open
and needs one of the two decisions above.
