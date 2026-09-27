# Final first-party character runtime path

## Goal

The finished operational app must load and animate only first-party production
character assets by default.

Final production identity:
- `HomeGymPT_Male_ORIGINAL_v1.glb`
- optional project-authored dressed variant;
- `hgpt_canonical_v4_original`.

## Current legacy path to remove from production

Current source still contains:
- `BASELINE_CHARACTER_URL = characters/HomeGymPT_Male_BASELINE_v8.glb`;
- `DRESSED_CHARACTER_URL = characters/HomeGymPT_Male_BASELINE_v8_SHORTS.glb`;
- MakeHuman-derived built-in anatomical body;
- generic imported-character retarget path implemented with Three GLTFLoader;
- imported-character corrective/retarget/grip calibration paths.

These remain useful migration/reference code today but are not the final
operational character path.

## Final default path

Replace the default registration with first-party assets:

`characters/HomeGymPT_Male_ORIGINAL_v1.glb`

and, if clothing remains a separate file:

`characters/HomeGymPT_Male_ORIGINAL_v1_SHORTS.glb`

or preferably one project-authored production file if one asset can represent
the desired runtime variants cleanly.

The local browser fetch of a packaged relative URL is acceptable:
- it is a browser/platform capability;
- the file is shipped with the product;
- no external service is contacted.

The final production asset should still be available through the same app
without an internet connection.

## Built-in fallback

Do not fall back to MakeHuman-derived anatomical arrays.

If a fallback character is required, it must be either:
- ORIGINAL v1 itself; or
- a separately documented project-authored procedural fallback generated only
  from clean first-party specifications.

## Generic user import

A feature that lets a user import **their own** GLB is not inherently a
third-party dependency.

It may remain only after:
- Three GLTFLoader is replaced by the first-party GLB reader;
- import/retarget maths is first-party;
- no hosted service is required;
- no third-party sample/model is bundled;
- user-visible copy does not imply a specific third-party source.

The generic import feature is optional for the standalone release. Do not let it
block replacing the production character.

## Legacy retarget path

Do not delete it prematurely while it is still useful as a comparison harness.

Final options:
1. keep a fully first-party generic retarget/import implementation; or
2. remove generic retargeting from the release if Home Gym PT does not need it.

Either is compatible with the zero-third-party goal. The deciding factor is
product usefulness, not provenance.

## Remove legacy-specific runtime assumptions

Before standalone acceptance, eliminate from production:
- V8/V13e/V15f asset URLs/names;
- legacy grip-solution IDs;
- imported-character shoulder/body calibration constants;
- legacy corrective defaults;
- MakeHuman anatomical fallback;
- source-character-specific hand-frame compatibility shims once no accepted
  first-party asset needs them.

Historical docs/tests may stay outside the operational package where useful.

## Offline acceptance

Test the release with network unavailable.

Require:
- app opens;
- ORIGINAL v1 loads;
- all exercises play;
- prompt generation works;
- model/rig/equipment validation works;
- GLB import/export features intended for release work locally;
- no request attempts an external host.

This offline test is part of final standalone acceptance.
