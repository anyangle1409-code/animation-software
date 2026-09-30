# Final first-party character runtime path

## Goal

The finished operational app must load and animate only first-party production
character assets by default.

Final production identity:
- `HomeGymPT_Male_ORIGINAL_v1.glb`
- optional project-authored dressed variant;
- `hgpt_canonical_v4_original`.

## Current runtime state

The legacy production-character path has already been removed from active
runtime source.

Current guarded source/runtime state:
- no V8/V13e/V15f production character URL/name in operational `src/`;
- no MakeHuman-derived built-in anatomical body in active source/runtime;
- no Three/GLTFLoader runtime dependency;
- first-party GLB parsing, skinning, retargeting and rendering are live;
- a clean project-authored procedural character remains the temporary runtime
  fallback while ORIGINAL v1 is not production-approved.

Do not reintroduce a legacy loader/model path as a shortcut while integrating
the final asset.

## Final default path

The promotion contract currently reserves these standalone production targets:

`characters/HomeGymPT_Male_ORIGINAL_v1.glb`

and:

`characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb`

The corresponding repository inputs will live under `public/characters/`
only after explicit approval. Until then, those production paths and their
hashes must remain absent.

`ORIGINAL_V1_PROMOTION_CONTRACT.json` is the deny-by-default authority for
this cutover. Do not copy candidate GLBs into the runtime merely because their
container/rig structure passes.

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

## Generic retarget/import path

The generic import/retarget path is now implemented with first-party runtime
code rather than Three. It may remain if it continues to serve user-import
functionality and passes release/offline gates.

Historical source-character-specific assumptions must remain outside the
operational production path. The final ORIGINAL v1 path should use the
project-owned canonical-v4 identity directly wherever possible rather than
routing through legacy compatibility behaviour.

## Legacy-specific runtime assumptions

The active runtime gate already blocks V8/V13e/V15f/MakeHuman/Meshy identities
from operational `src/`. Continue removing or isolating any remaining
source-character-specific calibration assumptions when they are proven unused
by ORIGINAL v1.

Historical docs/tests may stay outside the operational package where useful,
but must never be release-allowlisted or restored to the live character path.


## Promotion sequence

Do not merge the model branch into the standalone branch.

When ORIGINAL v1 is genuinely ready:

1. record explicit anatomy/body/garment production approval;
2. require development and production deformation/grip gates to pass;
3. pin one exact approved commit from
   `claude/original-v1-blender-o2-20260929` (or its explicitly designated
   successor model branch);
4. create production-named GLBs with no `CANDIDATE`/legacy identity;
5. record exact SHA-256 values in `ORIGINAL_V1_PROMOTION_CONTRACT.json`;
6. copy only the approved assets/evidence into the standalone branch;
7. add only the exact final release paths to
   `RELEASE_ASSET_ALLOWLIST.json`—never a broad character-directory or
   extension wildcard;
8. change `male_character`, `male_shorts` and `canonical_rig` to
   `first_party_approved` only after their exact production artifacts have
   passed;
9. switch the runtime default from the procedural fallback to ORIGINAL v1;
10. run full typecheck/tests/build, standalone/production/release audits,
    offline browser acceptance and physical desktop/iPhone parity on the exact
    resulting commit.

Until all of that is true, promotion mode remains
`blocked_pending_approval`.

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
