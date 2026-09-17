# Reference body — dressed production metadata delivery fix

**Branch:** `chatgpt/absolute-retarget-imports`  
**Original decision HEAD:** `84fb2331a39abc75f3f59f27eeab57efc8b6bdad`  
**Executed/delivered at:** `a7428f99f7853233e0b5671e1aec898264a598be`  
**Promotion retained. Do not merge yet.**

The original decision below authorised repair of the dressed production character. That work is now complete and validated. The execution found that the defect was broader than missing grip metadata: the dressing transplant also retained v7 joint matrices/rest pose and inverse binds. The historical decision text is retained for traceability; the **Executed result and corrections** section near the end supersedes any earlier assumption that the dressed file already shared the v8 rest pose/skeleton state.

## Proven production finding at the time of the decision

Promoted production assets originally verified as:

- bare body `public/characters/HomeGymPT_Male_BASELINE_v8.glb` — SHA-256 `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0`;
- dressed default `public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb` — old SHA-256 `841b01d6abb5649af8929f6b147b6aafbf95da4ecf13c2ea09f7f3e570306d72`.

The original investigation correctly established that the body mesh inside the dressed asset was vertex-identical to the bare body, but it incorrectly inferred that the rest-pose skeleton also matched. Every relevant GLB node uses `matrix`, not TRS; the earlier comparison read absent `translation`/`rotation` fields and therefore missed the v7 rest-pose matrices.

The dressed file also did not retain the required character metadata:

- bare v8 resolves `gripSolutionId = homeGymPTMale` and character-specific `handleGripOffsets` (left grip offset `(0.0174, 0.0452, 0.0083)`, with corresponding mirrored/right-side data);
- the old dressed v8 resolved neither the grip solution nor the handle offsets.

As a result, the bare promoted body reproduced locked Phase 1 curl clearance at about **+4.68 / +4.79 mm with zero inside**, while the old dressed default remained around **−16.66 / −16.62 mm with 8 vertices inside** because it never received the solved grip. The later execution additionally proved the old dressed asset posed with v7 rest data: curl-bottom hand displacement was **73.14 mm** and **3,650 / 10,839** posed body vertices differed from the bare v8.

## Decision — rebuild the dressed asset from the retained v8 body

Use the **asset rebuild** remedy. Do **not** add an inference/fallback path in `retargetSource.ts`.

Reason: character-specific solved-grip data and the character's rest/bind state should travel with the character asset they belong to. Inferring them in executable code would weaken the deliberate requirement that an asset explicitly declares the data needed to opt into the solved grip.

### Required implementation

1. Keep the promoted bare v8 body byte-for-byte unchanged.
2. Fix the dressing/build path (`dress.mjs` and directly related transplant logic) so the dressed output carries from the source body:
   - joint node matrices/rest pose;
   - inverse bind matrices, matched safely by joint identity/name;
   - `scene.extras.homeGymPT`, including grip solution identity and character-specific handle-grip offsets.
3. Do not hard-code a second independent copy of those values. The source body is the authority.
4. Rebuild **only** `public/characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb` from the retained/promoted v8 body.
5. Accept that the dressed asset will have a **new SHA-256**. The old dressed hash is superseded after this fix; do not try to preserve it.
6. Preserve the approved garment geometry and prove that the transplanted body-state changes do not alter garment skinning unexpectedly.
7. Regenerate/restore the matching v8 `.correspondence.json` in the existing format so the permanent clothing, waistband and cloth-debug diagnostics can run against the promoted dressed asset.

## Required production validation

Validate the **rebuilt bundled dressed default**, not a scratch candidate.

At minimum prove:

- it resolves the same `gripSolutionId` and `handleGripOffsets` as the promoted bare body;
- its posed body is equivalent to the bare v8, not just vertex-identical in bind pose;
- Phase 1 solved grip is actually active on the default character;
- curl Bottom / Return thigh clearance returns to approximately the locked promoted-body result (**about +4.68 / +4.79 mm, zero body vertices inside**);
- finger contact remains about `−0.46 / −0.36 / −0.22 / −0.11 mm`, zero inside;
- thumb about `+1.18 mm`, palm about `−2.54 mm`, wrap about `252°`;
- renderer/exporter grip agreement remains `0.0000 mm`;
- push-up wrist, retained `0.50` twist-helper share, Stage 2 proportions, containment and all other locked results remain unchanged;
- dressed clothing remains non-interpenetrating;
- correspondence diagnostics run successfully.

Because the shipped production asset changes, finish with:

- new dressed v8 SHA-256 recorded in the review/promotion docs and `AI_CHANGELOG.md`;
- bare v8 SHA re-verified unchanged;
- typecheck;
- build;
- focused grip/curl/clothing diagnostics;
- full suite once on the retained production result;
- tracked tree clean.

If all checks pass, report the promotion as **delivered** and ready for a separate merge decision.

If the rebuild unexpectedly changes body geometry, weights, grip behaviour, clothing fit or any locked exercise result beyond the intended restoration of the v8 character state, stop and report rather than compensating elsewhere.

**Do not merge. Do not modify `retargetSource.ts` to infer the grip solution.**

---

# Executed result and corrections — `a7428f9`

The delivery fix passed and the promotion is now considered **delivered**, but not merged.

### What was actually repaired

The dressing transplant had been copying the v8 body mesh into the previous-generation dressed template while leaving three important classes of state behind:

- **joint node matrices/rest pose** — 50 arm-chain joints retained v7 matrices;
- **inverse bind matrices** — the same affected chain retained v7 bind data;
- **`scene.extras.homeGymPT`** — the solved-grip identity and handle offsets were dropped.

`readCharacter` derives bone rest orientation from the node hierarchy, so the stale node matrices were the largest functional defect. The repaired dressing step now carries all 160 joint matrices, all 160 inverse binds matched by joint name, and the full `homeGymPT` extras from the bare v8. It refuses unsupported source TRS instead of silently comparing or transplanting the wrong representation.

Garment safety was checked explicitly: the garment uses 9 joints and none overlap the 50 body joints that changed, so the approved garment fit is not being altered by the body rebind.

### Final production identity

- bare v8 — unchanged SHA-256: `951c2c3966a00caaa39fd5aaad063e852ac3d5e6e33fa0b3dd574e5040963ee0`;
- dressed v8 default — new SHA-256: `cc728366022315b031cfae7ec9cdf4b4bac245b93f708a25ae2f845f115722e3`.

The old dressed hash `841b01d6abb5649af8929f6b147b6aafbf95da4ecf13c2ea09f7f3e570306d72` is superseded.

The rebuild is deterministic.

### Final validated behaviour

On the actual production files in `public/characters/`:

- dressed default resolves `gripSolutionId = homeGymPTMale` and the same `handleGripOffsets` as the bare body;
- dressed-vs-bare posed hand equivalence: **0.0000 mm**;
- posed body equivalence: **0 / 10,839 differing vertices**;
- curl body/thigh clearance: **+4.68 / +4.79 mm**, zero inside;
- including the shorts garment: **+0.48 / +0.64 mm**, zero inside — the dumbbell no longer passes through the shorts;
- fingers `−0.46 / −0.36 / −0.22 / −0.11 mm`, zero inside;
- thumb `+1.18 mm`, palm `−2.54 mm`, wrap `252°`;
- renderer/exporter agreement `0.0000 mm`;
- push-up wrist `81.18°`, bilateral mismatch about `0.0001°`;
- forearm twist helper `9.1° → 21.0°`, hand held at `57.7°`;
- girth unchanged;
- clothing non-interpenetrating at `1.97 mm` closest approach;
- typecheck clean;
- build clean;
- full suite **298 passed / 1 skipped / 0 failed**;
- tracked tree clean.

### Correspondence decision accepted

Do **not** rerun `shorts.mjs` merely to regenerate correspondence. That tool builds a garment; the production shorts are approved transplanted geometry that it does not reproduce bit-for-bit. The retained correspondence is a topological garment-to-body map and neither topology changed.

The delivered map was regenerated for the actual retained garment and validated rather than assumed:

- 1,410 entries for 1,410 garment vertices;
- every index in range;
- every garment vertex within `37.53 mm` of its mapped body point;
- existing format unchanged;
- clothing, waistband and cloth-debug consumers all pass.

That is the preferred result for this asset pipeline.

### `strainReview` timeout accepted

The earlier timeout became reproducible both in isolation and under the suite. It is independent of the production GLBs and needs about 6.2 seconds against Vitest's 5-second default. A **20-second timeout on that one expensive test** is accepted because the assertions and code under test are unchanged and were proven to pass with a larger test-time budget.

Do not alter production deformation code to address this timeout.

### Durability note — do not block the curl preview on this

The production GLBs and correspondence file are intentionally ignored under `public/characters/`; a fresh Git checkout does **not** contain them. `bundled.ts` probes for these files and falls back to the built-in procedural character when they are absent.

Also, the current `dress.mjs` repair and `dressed_equivalence.test.mts` live under `scratchpad/`, and the repository root ignores the entire `scratchpad` directory. Therefore the wording "permanent guard" in the execution report describes the current working environment, not a guard preserved by GitHub.

This is **not a reason to spend more usage before the user's visual curl review**. After the curl and model are accepted, decide separately whether the minimal rebuild tooling/equivalence guard should move into a tracked location.

For any preview now, use the same working environment that contains the delivered v8 binaries and **prove before judging the animation that the app actually loaded `HomeGymPT_Male_BASELINE_v8_SHORTS.glb` / `baseline-dressed`**. Do not accept a preview of the procedural fallback or a generated approximation.

---

# User-priority scope after delivery

The dressed-default delivery fix is complete. **Do not continue into any other exercise work.** The immediate product goal is deliberately narrower:

1. **Visually approve the bicep curl on the real bundled dressed v8 character.**
   - Run the actual app/rendered production character, not a generated approximation.
   - First prove the loaded character is the bundled dressed v8 and not the procedural fallback.
   - Review one complete Bottom → Mid → Peak → Return loop.
   - Provide/inspect full-body plus close-up views of the hands/dumbbells, elbows and shoulders.
   - If anything still looks wrong, work only on genuine bicep-curl visual/mechanical issues until the curl is accepted.
2. **Then refine the character/model appearance to the user's preferred look.**
   - Model appearance work comes before expanding the exercise library.
   - Preserve the accepted curl mechanics/grip while changing the model.
   - Use objective checks to make sure model edits do not regress the accepted curl.
3. **Freeze the accepted bicep curl and final model together.**
4. **Only after the user explicitly approves both should work start on another exercise.**

Until that approval:

- do not start new squat, shoulder-press, push-up or pull-up improvement work;
- do not use remaining time/usage to broaden the exercise set;
- do not merge merely because production validation is green;
- keep existing non-curl exercises as regression checks only when required to prove a shared change did not break them;
- keep usage low and prefer focused diagnostics over broad exploratory work.

The next visible milestone is therefore **a trustworthy working preview of the actual dressed v8 bicep curl**, followed by model refinement — not another exercise.