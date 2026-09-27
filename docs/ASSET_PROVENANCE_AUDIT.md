# Asset provenance audit

## Purpose

Track whether every asset intended for distribution is wholly project-authored or has third-party provenance that must be removed/replaced.

## Current classification

### Legacy/reference-only character lineage
The following line must be treated as derived from an imported source character until proven otherwise:

- imported source character
- HomeGymPT_Male_HAND_REPAIR_CANDIDATE / proven v5 lineage
- HomeGymPT_Male_BASELINE_v6
- HomeGymPT_Male_BASELINE_v7
- V8 accepted body/knee geometry
- V9–V14 hand review/experimental candidates
- V13e hand geometry source
- V15a–V15f descendants

Project documentation states that the production path preserved imported source:
- skeleton;
- bind data;
- mesh;
- weights;
- proportions;

before project-authored repairs and later topology work.

For first-party standalone distribution, modification depth does not convert this lineage into a clean-room asset. Preserve it as an engineering/reference benchmark only.

## Clean-room character rule

The first distributable Home Gym PT character must start from a new/blank project-authored asset and may not receive copied:
- positions;
- faces/edge topology;
- UV coordinates;
- skin weights;
- morph targets;
- textures;
- materials;
- source-rig transforms;
- source-specific bind matrices;

from the legacy/imported lineage.

Abstract specifications may be reused:
- canonical project bone names/hierarchy;
- project-authored joint ranges;
- dimensional targets stated as numbers;
- contact requirements;
- deformation thresholds;
- exercise requirements;
- human-anatomy constraints;
- validation methodology.

## Asset inventory to complete

Before standalone release, classify each shipped item:

| Asset class | Current state | Required action |
|---|---|---|
| Male character mesh | legacy/import-derived | replace with ORIGINAL v1 |
| Character rig | project canonical rig appears project-authored; verify history | document origin and freeze |
| Shorts/clothing | tied to legacy body lineage | rebuild original |
| Skin/materials | project-modified/unknown provenance chain | rebuild/document |
| Equipment geometry | likely project-generated; verify file-by-file | provenance audit |
| Icons/images | audit required | replace/document |
| Fonts | audit required | use system fonts or project-owned font assets |
| Audio | none known / audit | verify |
| Exercise animation data | project-generated | document |
| Validation/reference renders | reference-only, not distributable | keep out of release |
| Legacy GLBs/Blends | reference-only | exclude from release package |

## Required final files

Create and maintain:
- FIRST_PARTY_COMPONENT_MANIFEST.json
- THIRD_PARTY_REFERENCE_ONLY.md
- RELEASE_ASSET_ALLOWLIST.json

The release process should include only allowlisted first-party assets.
