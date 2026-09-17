# Reference body — dressed production delivery fix

**Branch:** `chatgpt/absolute-retarget-imports`
**Executed from:** `84fb233`
**Promotion retained. Not merged.**

Executes `docs/REFERENCE_BODY_DRESSED_METADATA_DELIVERY_FIX.md`. The bare v8 body is unchanged.
The dressed default was rebuilt, its correspondence regenerated, and the bundled result validated.
All acceptance criteria pass, so the promotion is now **delivered**.

`retargetSource.ts` was not touched. No inference or fallback path was added, as required.

## The defect was larger than the decision recorded

The decision authorised a metadata fix. Metadata was one of **three** things the dressing step
failed to carry, and the one that mattered most was not the metadata.

`dress.mjs` builds the dressed asset by transplanting a body into the **previous generation's
dressed file** — the garment is approved geometry that the builder cannot reproduce bit for bit,
so the v7 dressed file is the template. It transplanted `POSITION` and `NORMAL` and merged two
`asset.extras` keys. Everything else silently kept v7's answer:

| Carried by the old step | Left at the template's v7 values |
|---|---|
| `POSITION`, `NORMAL` | **node matrices** — the rest pose, 50 arm-chain joints |
| `asset.extras.referenceMatch`, `.shorts` | **`inverseBindMatrices`** — the bind repair, the same 50 joints |
| | `scene.extras.homeGymPT` — grip solution identity and handle offsets |

The rest pose is the one that made the shipped default the wrong character. `readCharacter` in
`retarget.ts` derives every bone's rest orientation and position from the **node hierarchy**
(`bone.getWorldQuaternion`, `bone.matrixWorld`), not from the bind matrices, so the node matrices
are what drive the whole retarget. With v7's arm-chain matrices in place, the promoted default
posed exactly like v7: **73.14 mm** of hand displacement at the curl bottom and 3,650 of 10,839
posed body vertices in the wrong place, while every vertex-level check passed, because the *bind*
vertices were correct and only the *posed* result was wrong.

### A mistake of mine this exposed

I reported in `REFERENCE_BODY_PROMOTION.md` that the dressed file's skeleton matched the bare
body's, on the strength of a comparison that read `node.translation` and `node.rotation`. **Every
node in these files uses `matrix`**, never TRS, so that comparison compared absent fields against
each other and reported 0.0000 mm for 50 joints that differed by up to 6.813e-2. The first guard I
wrote into `dress.mjs` for this fix repeated the same error and passed for the same reason. It now
compares `matrix`, and refuses outright if a source joint uses TRS, since this transplant would
not carry that.

The promotion doc's claim that the body inside the dressed file was "the same body" was true of its
vertices and false of its rest pose. That section is annotated rather than rewritten.

## What the rebuild does

`scratchpad/reference-fit/dress.mjs` now carries everything that describes the body from the
source, and proves its own assumptions instead of inheriting them. Each step reports and each
throws rather than degrading quietly:

1. **Rest pose** — all 160 joint matrices from the source; **50 changed**, worst component
   6.813e-2 at `DEF-shoulder.L`. Refuses if a source joint uses TRS.
2. **Inverse binds** — all 160, matched by joint *name* because two files need not order joints
   alike; **50 changed**.
3. **Scene metadata** — `scene.extras.homeGymPT` wholesale from the source, which is the
   authority; carried `gripFrameOffsets, offsetUnits, elbowCorrective, handleGripOffsets,
   handleGripNote`. Throws if the source carries no `handleGripOffsets`, since the solved grip
   would then silently not activate.
4. **Garment safety** — the garment is skinned to **9 joints**; **50** joints were re-bound or
   re-posed; **0 overlap**. So the clothing fit provably cannot have changed. Throws on any
   overlap.
5. **Correspondence** — written beside the GLB.

The values are carried, never hard-coded, so the source body stays the single authority.

### The correspondence file

Regenerated as the garment's own map rather than by re-running the garment builder, and this is a
deliberate reading of the instruction. `shorts.mjs` *builds* a garment and writes the map for what
it built; our garment is the approved F3 geometry transplanted whole, which the builder does not
reproduce bit for bit. Re-running it would produce a map for a garment this file does not contain.

The map is topological — one `[body vertex index, weight]` list per garment vertex — and neither
mesh's topology changes, so the template's map still describes this pair. It is validated rather
than assumed: 1,410 entries against 1,410 garment vertices, every index in range, and every
garment vertex within **37.53 mm** of its mapped body point (mean 13.94 mm, consistent with the
garment's authored 11–19 mm offsets). `dress.mjs` throws above 50 mm. The format is unchanged.

All three consumers — `clothing`, `waistband`, `clothdebug` — now run against the promoted dressed
asset and pass.

## Final asset identity

| Role | File | SHA-256 |
|---|---|---|
| Bare body — **unchanged** | `public/characters/HomeGymPT_Male_BASELINE_v8.glb` | `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0` ✓ |
| Dressed default — **new** | `public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb` | `cc728366022315b031cfae7ec9cdf4b4bac245b93f708a25ae2f845f115722e3` |

The dressed hash **supersedes `841b01d6…306d72`**, as the decision anticipated. The rebuild is
deterministic: running `dress.mjs` twice produced the same hash. The scratchpad candidate
`HomeGymPT_Male_STAGE2_CANDIDATE_SHORTS.glb` and its correspondence were synced to the same bytes.

Rebuilt from the retained body with:

```
node scratchpad/reference-fit/dress.mjs \
  public/characters/HomeGymPT_Male_BASELINE_v8.glb \
  public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb
```

## Validation of the bundled dressed default

Measured on `public/characters/`, not on a scratch candidate.

| Requirement | Result | |
|---|---|---|
| Same `gripSolutionId` as the bare body | `homeGymPTMale` on both | ✓ |
| Same `handleGripOffsets` | (0.0174, 0.0452, 0.0083) on both — the authored 0.0542 less the locked −9 mm | ✓ |
| Phase 1 solved grip active on the default | yes; grip contacts resolve on the shipped path | ✓ |
| Curl Bottom / Return thigh clearance | **+4.68 / +4.79 mm, 0 inside** — exactly the bare body | ✓ |
| Finger contact | −0.46 / −0.36 / −0.22 / −0.11 mm, 0 inside | ✓ |
| Thumb / palm / wrap | +1.18 mm / −2.54 mm (2 inside) / 252° | ✓ |
| Renderer vs exporter | 0.0000 mm at t = 0, 2, 4, both sides | ✓ |
| Push-up wrist | extension 81.18°, bind offset 14.62°, L/R mismatch 0.0001°, residual 0.0000° | ✓ |
| Twist-helper share 0.50 | `forearmL` 9.1° → `forearmL001` **21.0°**, hand 57.7° | ✓ |
| Forearm girth | 58.7 / 51.7 / 48.6 / 41.5 / 37.4 / 32.9 mm, unchanged | ✓ |
| Clothing non-interpenetrating | closest body-to-garment 1.97 mm, no interpenetration | ✓ |
| Correspondence diagnostics | `clothing`, `waistband`, `clothdebug` all pass | ✓ |
| Bone naming / skeleton discovery | clean | ✓ |

**Equivalence to the bare body**, which is the check that matters and the one that was missing:
posed hand difference **0.0000 mm**, and **0 of 10,839** posed body vertices differ at the curl
bottom. Before the fix those were 73.14 mm and 3,650.

A bonus the decision did not ask for: measured **including** the garment, curl clearance is now
**+0.48 / +0.64 mm with 0 vertices inside**. The dumbbell previously passed through the shorts
(−16.99 mm, 15 inside after the metadata-only attempt; −16.56 mm, 8 inside on v7). It no longer
touches them.

Whole-project gates: **typecheck clean**, **build clean**, **full suite 38 files, 298 passed /
1 skipped / 0 failed**, tracked tree clean.

## The `strainReview` timeout, now reproducible

It failed this run in the full suite **and in isolation**, so it is no longer the intermittent case
the acceptance decision covered. Diagnosed rather than assumed: the test imports nothing from
`public/characters/` — it runs the built-in procedural character against the canonical skeleton —
and no `src/` file changed in this round before it failed, so the asset work cannot have caused it.
It needs **6.2 s** of CPU skinning against vitest's 5 s default, which is why the same code has
been over and under the line depending on machine load.

Applied the remedy the decision permits: a **per-test timeout of 20 s** on that one test, after
confirming with `--testTimeout=30000` that **both assertions pass unchanged** (2 passed, 6.61 s).
The code under test is untouched, and no other test's budget changed.

## One new permanent guard

`scratchpad/repair/dressed_equivalence.test.mts` asserts that the dressed default carries the same
grip solution and offsets as the bare body and poses identically to it — the same grip solution,
hand frame within 0.001 mm, and every posed body vertex within 0.001 mm.

This is the check whose absence let the defect ship: every existing harness ran one file at a time,
so nothing compared the pair. Confirmed to have teeth by pointing it at the stale pairing, which it
fails on the first assertion.

`scratchpad/repair/overlap.test.mts` gained an opt-in `SKIN_ONLY`, because a clearance figure
measured over a dressed file includes the garment and is not comparable with the bare body's.

## Status

Delivered. The bare body is byte-identical to the promoted one, the dressed default is genuinely
the same character, and every written acceptance criterion passes. Ready for a separate merge
decision. **Not merged.**
