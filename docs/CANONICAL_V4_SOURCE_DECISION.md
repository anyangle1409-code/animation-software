# Canonical v4 ORIGINAL source decision

## Approved clean base

Use the original Home Gym PT humanoid rig at commit:

`287f72c6a6ac9b1dcd771946ef548d77a40b8ea1`

as the **clean numerical starting reference** for canonical v4.

That rig already contained:
- root/pelvis/spine/neck/head;
- clavicles;
- upper arms/forearms/hands;
- hips/thighs/shins/feet/toes;
- full 3-segment fingers;
- joint limits;
- left/right mirroring;
- project-owned pose conventions.

It predates the later MakeHuman and imported high-detail character work.

## Retain from later rig development

Later project work added useful capabilities that should remain in canonical v4:

### Scapulae
Commit:
`c2372c16ad4b7a0763a4cfdf9a0da6a23c3524f2`

Retain:
- scapula bones between clavicle and upper arm;
- structural role;
- axis/limit intent;
- joint-parent handling.

Do **not** retain its rest coordinates unchanged because its own commit documentation says the blade was positioned relative to the production character's back skin.

### Metacarpals and thumb base
Commit:
`19ca602ca2f2a821237dcf5b1b50c7906d86b0fe`

Retain:
- four metacarpals per hand;
- 3-DOF thumb base;
- cupping/opposition capability;
- 63-bone overall architecture.

Do **not** carry the numerical hand placements blindly into v4. Re-derive them against ORIGINAL v1 hand dimensions.

## Canonical v4 construction rule

Build `hgpt_canonical_v4_original` as:

clean historical core rig
+ project-authored scapula architecture
+ project-authored metacarpal/thumb architecture
+ newly authored ORIGINAL v1 numerical rest dimensions

The result should preserve the best capabilities of v3 without preserving any coordinate whose provenance depends on the old production character.

## Required v4 audit

Before v4 is frozen, record for every bone:
- parent;
- head/tail;
- length;
- body-height fraction;
- joint limits;
- source category:
  - clean historical project value;
  - newly authored original value;
  - retained structural concept;
- whether the value was independently re-authored.

The final audit must be machine-readable and stored alongside the rig version.
