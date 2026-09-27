# Canonical v4 provenance decision

The canonical rig can be retained as a **project architecture**, but the standalone production line will use newly authored numerical rest geometry.

## Clean base

The first substantive studio commit, `287f72c6...`, already contained a complete 53-bone canonical humanoid:
- centre spine/head;
- clavicles;
- arms/forearms/hands;
- hips/legs/feet/toes;
- all finger chains;
- joint limits;
- mirroring;
- 1.75 m design height.

This predates the later MakeHuman and imported/high-detail character work.

## Later 63-bone capabilities

Two later project-authored upgrades are worth keeping conceptually:

### Scapulae
Commit `c2372c16...` added left/right scapula bones and proved the hierarchy could remain movement-equivalent while they were at rest.

However, that commit explicitly placed the inferior angle relative to the **production character's back skin**. Therefore the scapula coordinates are not carried verbatim into v4.

Retain:
- scapula between clavicle and upper arm;
- structural role;
- DOF/axis concept;
- retargeting support for unmapped structural bones.

Re-author:
- rest head/tail;
- blade length/orientation;
- limits if needed after clean anatomical review.

### Metacarpals / thumb base
Commit `19ca602c...` expanded the rig to 63 bones with four metacarpals per hand and a 3-DOF thumb base.

Retain:
- metacarpal hierarchy;
- palm-cupping capability;
- true thumb-opposition capability;
- mirrored-hand semantics.

Re-author:
- hand/palm numerical rest positions;
- metacarpal lengths/spacing;
- thumb-base rest geometry.

## v4 rule

`hgpt_canonical_v4_original` is **not** a copy of v3 coordinates.

It is:
clean initial project rig architecture
+ clean project-authored scapula/palm capabilities
+ new ORIGINAL v1 dimensions/rest positions
+ full movement-envelope validation.

This gives the standalone model the capabilities we already developed without carrying forward geometry measurements taken from the legacy character.
