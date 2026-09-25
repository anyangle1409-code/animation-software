# Reference system notes

This folder holds design-time examples for HOME GYM PT's future offline Internal Reference Engine.

The goal is not to store photographs or videos. The runtime reference is structured biomechanical data that HOME GYM PT owns and can evaluate locally.

## Principle

A reference is an **acceptable envelope**, not one perfect human pose.

Examples:
- elbow flexion may be 115–135 degrees at peak;
- torso sway may be limited to a small corridor;
- a dumbbell path may be allowed inside a normalized band rather than one line.

## Normalization

Do not store camera pixels as the primary truth.

Prefer:
- joint angles in degrees;
- distance divided by standing height;
- distance divided by shoulder width;
- distance divided by relevant limb length;
- cycle position from 0.0 to 1.0;
- equipment orientation relative to a body or world axis.

This lets the same reference work across characters with different proportions.

## Reference images

Reference images can be generated locally from the structured record using a neutral mannequin.

They are useful for:
- human inspection;
- silhouette comparison;
- projected landmark comparison;
- visual evidence in QA reports.

The structured reference remains authoritative.

## Versioning

Every reference needs:
- stable id;
- schema version;
- reference version;
- movement family;
- supported variants;
- provenance/review note;
- certification state.

A family implementation may change without changing the reference automatically.
