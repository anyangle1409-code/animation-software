# First-party provenance findings — 2026-09-27

## Confirmed third-party-derived content

### 1. MakeHuman-derived built-in anatomical character
`THIRD_PARTY_ASSETS.md` states that the split `src/body/anatomical*.ts` character data is generated from MakeHuman CC0 files:
- base.obj
- default_weights.mhw
- default.mhskel
- caucasian-male-young.target
- universal-male-young-maxmuscle-averageweight.target

Although CC0 permits broad reuse, the project goal is stricter: **zero third-party creative content in the distributable**.

Therefore the following are legacy/reference-only for the standalone target:
- `src/body/anatomicalPositions.ts`
- `src/body/anatomicalIndices.ts`
- `src/body/anatomicalSkinIndices.ts`
- `src/body/anatomicalSkinWeights.ts`
- `src/body/anatomicalColours.ts`
- `src/body/anatomicalMeta.ts`
- any generated surface/corrective logic whose values are specific to those vertices.

The project-authored procedural debug mannequin may remain useful as a diagnostic, but it is not the final ORIGINAL v1 character.

### 2. Imported/high-detail Home Gym PT male lineage
Existing project documents explicitly describe the production path as preserving an imported source skeleton, bind data, mesh, weights and proportions before later repairs.

Treat the whole lineage as reference-only:
- proven v5 / HAND_REPAIR line;
- v6/v7;
- v8;
- CORNER_FINAL variants;
- V9–V15 candidates and descendants;
- related correspondence data;
- derived Blend checkpoints.

## Canonical rig finding

The canonical rig architecture is present in the project's first substantive studio commit and is implemented as project source code. The hierarchy, bone naming, axes, mirroring logic, limits and IK semantics are therefore much stronger first-party candidates than the character meshes.

However, the current `humanoid.ts` also contains numerical rest-position/proportion changes that were later tuned with measurements from the production/imported character, including shoulder and hand relationships.

For the strict standalone target:
- retain the project-authored **hierarchy, names, semantics and algorithms**;
- create a new `hgpt_canonical_v4_original` numerical rest pose;
- derive v4 rest positions/proportions from an explicit project-authored anatomical specification independent of the legacy meshes;
- do not transfer imported source-rig transforms or inverse bind matrices.

This avoids ambiguity over whether any final rest geometry is derived from the legacy character.

## Equipment finding

The equipment system is code-generated from primitive shapes in:
- `src/equipment/library.ts`
- `src/equipment/geometry.ts`

The repository tree contains no separate equipment GLB/FBX/OBJ/image asset that needs to be shipped.

Current equipment labels are generic rather than branded, and materials are project-authored numeric colour/roughness/metalness values.

Provisional classification: **project-authored candidate**, subject to the normal source-history/code audit.

Recommended standalone treatment:
- retain the generic equipment definitions;
- remove the dependency on legacy shoulder dimensions (for example sockets that currently incorporate `SHOULDER_WIDENING`);
- parameterise body-relative sockets from ORIGINAL v1 / canonical v4 dimensions instead;
- continue generating equipment geometry from project-authored primitives.

## Fonts / icons / audio / textures

Repository asset scan at source HEAD `47187360...` found:
- no shipped font files;
- no shipped audio files;
- no runtime icon/image bundle;
- non-character raster assets are engineering/review renders.

The UI currently uses a CSS system-font stack rather than bundled font files.

Therefore:
- system fonts may remain external platform resources and are not bundled assets;
- review renders must stay out of release packages;
- future textures/icons/audio require explicit provenance before inclusion.

## Release consequence

The standalone release must replace both:
1. the imported/high-detail production character line;
2. the MakeHuman-derived built-in anatomical character data.

The new ORIGINAL v1 character and canonical v4 rest proportions become the only production character path.

The legacy and MakeHuman-derived paths may remain in engineering history/reference branches but must not be packaged into the standalone product.
