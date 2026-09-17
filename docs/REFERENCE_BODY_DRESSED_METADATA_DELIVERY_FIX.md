# Reference body — dressed production metadata delivery fix

**Branch:** `chatgpt/absolute-retarget-imports`  
**Starting HEAD:** `84fb2331a39abc75f3f59f27eeab57efc8b6bdad`  
**Promotion is retained. Do not merge yet.**

The v8 production promotion itself is valid, but it is **not yet considered delivered** because the shipped default character is the dressed asset and that asset currently drops the character-specific solved-grip metadata during dressing.

## Proven production finding

Promoted production assets currently verify as:

- bare body `public/characters/HomeGymPT_Male_BASELINE_v8.glb` — SHA-256 `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0`;
- dressed default `public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb` — SHA-256 `841b01d6abb5649af8929f6b147b6aafbf95da4ecf13c2ea09f7f3e570306d72`.

The body inside the dressed asset is bit-identical to the bare body: same `Mike_Freeman` mesh, 10,839 vertices, same 160 bones, worst body-vertex difference 0.0000 mm. Therefore the solved grip derived for the bare body is valid for the dressed default too.

However, the dressed file does not retain the required character metadata:

- bare v8 resolves `gripSolutionId = homeGymPTMale` and character-specific `handleGripOffsets` (left grip offset `(0.0174, 0.0452, 0.0083)`, with the corresponding mirrored/right-side data);
- dressed v8 resolves neither the grip solution nor the handle offsets.

As a result, the bare promoted body reproduces locked Phase 1 curl clearance at about **+4.68 / +4.79 mm with zero inside**, while the shipped dressed default remains around **−16.66 / −16.62 mm with 8 vertices inside** because it never receives the solved grip.

This is a metadata-delivery defect in the dressing pipeline, not a geometry, weight, topology, or retarget-solver defect.

## Decision — rebuild the dressed asset with preserved metadata

Use the **asset rebuild** remedy. Do **not** add an inference/fallback path in `retargetSource.ts`.

Reason: character-specific solved grip data should travel with the character asset it belongs to. Inferring it in executable code would weaken the deliberate requirement that an asset explicitly declares the metadata needed to opt into the solved grip.

### Required implementation

1. Keep the promoted bare v8 body byte-for-byte unchanged.
2. Fix the dressing/build path (`dress.mjs` and any directly related metadata-copy step) so the dressed output preserves the source body's required `scene.extras.homeGymPT` character metadata, including the grip solution identity and character-specific handle-grip offsets.
3. Do not hard-code a second independent copy of the values if they can be carried through from the source body. The source body is the authority.
4. Rebuild **only** `public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb` from the retained/promoted v8 body.
5. Accept that the dressed asset will have a **new SHA-256**. The old dressed hash is superseded after this fix; do not try to preserve it.
6. Preserve the dressed body geometry, skeleton, weights and clothing result except for bytes necessarily changed by the repaired metadata/build output.
7. Regenerate the matching v8 `.correspondence.json` through the existing shorts/clothing tooling so the permanent clothing, waistband and cloth-debug diagnostics can run against the promoted dressed asset. Do not invent a new correspondence format.

## Required production validation

Validate the **rebuilt bundled dressed default**, not a scratch candidate.

At minimum prove:

- it resolves the same `gripSolutionId` and `handleGripOffsets` as the promoted bare body;
- Phase 1 solved grip is actually active on the default character;
- curl Bottom / Return thigh clearance returns to approximately the locked promoted-body result (**about +4.68 / +4.79 mm, zero vertices inside**);
- finger contact remains about `−0.46 / −0.36 / −0.22 / −0.11 mm`, zero inside;
- thumb about `+1.18 mm`, palm about `−2.54 mm`, wrap about `252°`;
- renderer/exporter grip agreement remains `0.0000 mm`;
- push-up wrist, retained `0.50` twist-helper share, Stage 2 proportions, containment and all other locked results remain unchanged;
- dressed clothing remains non-interpenetrating;
- regenerated correspondence diagnostics run successfully.

Because the shipped production asset changes, finish with:

- new dressed v8 SHA-256 recorded in the review/promotion docs and `AI_CHANGELOG.md`;
- bare v8 SHA re-verified unchanged;
- typecheck;
- build;
- focused grip/curl/clothing diagnostics;
- full suite once on the retained production result;
- tracked tree clean.

If all checks pass, report the promotion as **delivered** and ready for a separate merge decision.

If metadata preservation unexpectedly changes body geometry, skeleton, weights, grip behaviour, clothing fit or any locked exercise result beyond the intended metadata activation, stop and report rather than compensating elsewhere.

**Do not merge. Do not modify `retargetSource.ts` to infer the grip solution.**