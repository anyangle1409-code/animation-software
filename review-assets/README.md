# Review assets

Binaries and rendered evidence, committed so they can be reviewed outside this workspace. They are
normally gitignored (`scratchpad/`, `public/characters/.gitignore`) because they are large; this
folder is a deliberate copy for review, **not** the path the app loads from.

To run the studio against these characters, copy the two `BASELINE_v8` files and the
`.correspondence.json` back into `public/characters/`. Without them the app falls back to the
built-in procedural character.

## characters/

| File | SHA-256 | What it is |
|---|---|---|
| `HomeGymPT_Male_BASELINE_v8.glb` | `951c2c39…963ee0` | promoted production body |
| `HomeGymPT_Male_BASELINE_v8_SHORTS.glb` | `cc728366…5722e3` | promoted production dressed default |
| `HomeGymPT_Male_BASELINE_v8_SHORTS.glb.correspondence.json` | — | garment correspondence for the above |
| `HomeGymPT_Male_CORNER_FINAL.glb` | `b0884433…01cc7a` | **accepted upper-body geometry baseline**, bare |
| `HomeGymPT_Male_CORNER_FINAL_SHORTS.glb` | `fe30c1da…8e34a71b` | **accepted baseline, dressed** — the character every recent review render uses |
| `HomeGymPT_Male_CORNER_FINAL_SHORTS.glb.correspondence.json` | — | garment correspondence for the above |

`CORNER_FINAL` carries the Phase A normals repair, the skin/material pass and rounds 2–5 of the
upper-body geometry work. It is the current accepted character.

### There is no newer GLB from the shoulder-alignment work

Both recent candidates are **code-only** and run on `CORNER_FINAL_SHORTS` unchanged:

- the **Stage 1 arm-muscle layer** (`src/character/muscleDeformation.ts`) adds pose-driven corrective
  morph targets at load time, so nothing is baked into the asset;
- the **shoulder alignment true fix** (`src/rig/humanoid.ts`,
  `src/exercises/definitions/bicepCurl.ts`) corrects the canonical clavicle's rest angle, which is
  rig data rather than character data.

An arm-root edit *was* tried in the asset (`harnesses/armroot.mjs`) and is kept for reference, but
it is measurably ineffective — see `docs/SHOULDER_ALIGNMENT_TRUE_FIX.md`, "Why the asset could not
carry the fix". The face candidate (`FACE_FINAL`) is not included: it has never been rendered or
reviewed, so it is not part of any accepted state.

## renders/

Matched before/after pairs and loop strips, all captured in the running app on
`CORNER_FINAL_SHORTS`, `light` backdrop, canvas-only frames, identical camera and frame in each
pair.

- `shoulder-true-fix/` — the current candidate. `shoulder_side_bottom_ab.png` is the headline;
  `hip_clearance_ab.png` shows the dumbbell clearance; `loop_*.png` are Bottom → Mid → Peak → Return.
  Left column is the accepted alignment, right column the corrected one.
- `muscle-stage1/` — the arm-muscle layer, off vs on at the same frame.
- `shoulder-diagnosis/` — the earlier diagnosis pack. Its right column is a **rejected** −4° clavicle
  pose workaround, shown to demonstrate the cost, not a proposal.

## harnesses/

The measurement scripts behind the numbers in the docs. They are vitest files run against a GLB
passed by environment variable, e.g.

```
GLB=review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb \
  npx vitest run --config scratchpad/repair/vitest.config.mts scratchpad/repair/capsector.test.mts
```

Notable ones: `capsector` (deltoid cap cross-section by sector and slice), `armrootsweep`
(alignment and clearance across candidates and curl re-solves), `clavsweep` (clavicle axis sweep),
`muscle` (Stage 1 deformation), `overlap` / `gripmetric` / `gripagree` / `technique` /
`dressed_equivalence` (the curl guards).

They expect to run from the repo root with `scratchpad/repair/vitest.config.mts`; the copies here
are for reading. The live versions remain in `scratchpad/repair/`.

## Reading order

1. `docs/SHOULDER_ALIGNMENT_DIAGNOSIS.md` — what the defect was and what it was not.
2. `docs/SHOULDER_ALIGNMENT_TRUE_FIX.md` — the correction, the re-solve, and the 8 out-of-scope
   test failures it costs.
3. `docs/BICEP_CURL_REALISM_STAGE1.md` — the muscle layer.
4. `AI_CHANGELOG.md` — chronological summary of every round.
