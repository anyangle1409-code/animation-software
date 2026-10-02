# External human-movement reference policy

Status: OWNER-AUTHORISED DEVELOPMENT VALIDATION POLICY  
Effective: 2026-10-02  
Scope: ORIGINAL v1 character deformation, exercise pose validation and later automated visual QA.

## Purpose

External human exercise imagery/video may be used as **reference-only development evidence** to answer:

> Does the independently authored ORIGINAL v1 character move and load like a plausible human?

This is a validation/reference layer only. It does not become production content and does not change the clean-room / zero-third-party requirement for the shipped character, rig, clothing, animation system or runtime.

## Allowed use

Claude/GPT/development tooling may:
- inspect publicly accessible human exercise images/video and reputable anatomical/biomechanical references;
- use several examples where practical rather than copying one person's exact form;
- identify common human movement relationships, contact patterns and joint directions;
- note source URL/title, access date and relevant timecode/frame location;
- record qualitative findings and generic derived measurements such as approximate joint-angle ranges, support direction, silhouette relationships and contact regions;
- compare those observations with project-owned Blender renders and numerical evidence;
- use the resulting generic observations to improve independently authored project geometry, weighting, pose construction, constraints and validation rules.

## Prohibited use

Do not:
- import a third-party human mesh, scan or rig into the production authoring path;
- trace/project/reference-fit the production mesh directly to a copyrighted/person-specific silhouette;
- transfer vertices, topology, UVs, weights, bind matrices, materials, textures, motion-capture data or authored animation curves from an external asset;
- copy a specific person's body proportions or identity;
- use an external image/video frame as a production texture or shipped asset;
- claim that a single external example defines the only correct exercise form;
- alter protected thresholds merely to match a reference visually;
- commit third-party reference media to the production repository unless explicit rights/provenance permit it and the project authority deliberately approves that storage.

Prefer repository evidence consisting of source metadata, links/timecodes and project-authored observations rather than copied external media.

## Reference quality

Prefer:
1. reputable exercise/clinical/biomechanical demonstrations;
2. clear camera angles with the relevant joint/contact visible;
3. competent exercise execution;
4. multiple people/sources where normal human variation matters.

Treat external sources as observational evidence, not authority by themselves. Distinguish:
- common/required mechanics;
- normal human variation;
- clear model defects.

## Required comparison workflow

For each affected exercise or deformation region:

1. Define project-owned phase checkpoints first.
2. Inspect multiple suitable external human references when practical.
3. Record source metadata and the exact checkpoint/timecode used.
4. Write generic observations only.
5. Compare the current Blender candidate at matched functional checkpoints.
6. Classify mismatches as one of:
   - pose/constraint problem;
   - contact/support problem;
   - rig/joint-direction problem;
   - weighting/deformation problem;
   - topology/support problem;
   - surface-anatomy/proportion problem;
   - normal human variation / no actionable defect.
7. Correct the smallest general first-party cause.
8. Re-run existing numeric gates and project-owned visual evidence.
9. Never accept a visually improved correction that creates a material regression elsewhere.

## Immediate Phase 3 pre-freeze use

External human reference is REQUIRED before accepting the current corrections for:

### Finger flexion
Compare flexed grips and pull-up/bar contact to confirm:
- MCP/PIP/DIP flex in anatomically coherent directions;
- distal segments do not visibly reverse-bend under ordinary flexed grip;
- fingertip and thumb opposition remain plausible through the range.

### Push-up hand / palm / wrist
Compare top/mid/bottom push-up support to confirm:
- palm/metacarpal region is planted;
- support does not load primarily on the side edge of the hand;
- fingers project/splay naturally;
- wrist extension is plausible under load;
- forearm-to-hand alignment is coherent.

### Push-up foot / toes
Compare push-up support to confirm:
- load reads through a plausible forefoot/toe-pad region;
- toe dorsiflexion is plausible;
- ankle/foot/toe alignment is coherent.

### Shoulder / axilla
Compare press and pull-up checkpoints to help distinguish:
- real weighting/deformation/support failure that must be fixed before freeze;
- coarse surface anatomy that may proceed to Phase 5B.

Use at least front/three-quarter/side evidence where needed to avoid making a conclusion from one view.

## Exercise checkpoint records

Begin building project-owned reference checkpoint specifications from these reviews. The external material is development evidence; the retained deliverable should increasingly be project-owned rules such as:
- expected contact region;
- permissible joint-direction range;
- approximate angle/relationship ranges;
- silhouette continuity requirements;
- forbidden hyperextension/inversion cases.

These project-owned checkpoint specifications are intended to become inputs to later automated visual/biomechanical QA so final standalone operation does not depend on live third-party reference access.

## Provenance

All production geometry, rigs, weights, textures, clothing and runtime logic remain independently authored first-party work.

External reference metadata should be clearly tagged:
- `reference_only: true`
- `production_asset: false`
- source/title/URL or citation
- access date
- timecode/frame description where relevant
- derived observation
- project-owned corrective conclusion

No production approval is implied by reference comparison alone.
