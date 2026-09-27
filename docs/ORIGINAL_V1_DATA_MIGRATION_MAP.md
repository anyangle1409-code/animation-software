# ORIGINAL v1 data migration map

This map distinguishes project concepts that can be retained from body-specific data that must be re-authored for the standalone ORIGINAL v1 line.

## Character/body

### Replace
- MakeHuman-derived `src/body/anatomical*.ts` surface arrays.
- Imported/high-detail GLB/Blend lineage and correspondence data.
- Vertex-specific corrective masks/values tied to those surfaces.
- Legacy garment mesh and skin rows.
- Legacy head corrections that are expressed as fixes to the MakeHuman/source head.

### Retain as concepts only
- continuous-surface deformation goals;
- topology/strain/fold metrics;
- contact requirements;
- silhouette review methodology;
- project-authored material parameter approach.

## Rig

### Retain
- 63-bone hierarchy design;
- names and parent relationships;
- pose data model;
- joint-axis conventions;
- mirror logic;
- IK architecture;
- contact-lock architecture.

### Re-author / revalidate
- v3 world rest coordinates and body proportions;
- shoulder widening/setback constants;
- hand/metacarpal numerical placements that were measured/tuned against production character;
- body-relative equipment grip spacing derived from those constants.

Target: `hgpt_canonical_v4_original`.

## Muscle system

### Retain
- trainer-level muscle-group taxonomy;
- activation model;
- origin/insertion/via-point architecture;
- mirrored left/right generation;
- path-length/bulge/flatten/spread concepts.

### Re-author / re-fit
- numerical muscle attachment offsets;
- belly thicknesses that were fitted to the current body surface;
- containment thresholds calibrated to the MakeHuman/legacy body;
- shoulder-widening-dependent origins;
- ecorche surface deformation fields tied to the MakeHuman vertex surface.

The muscle system should be regenerated/fitted against ORIGINAL v1 after canonical v4 is frozen.

## Equipment

### Retain
- generic equipment kinds;
- primitive geometry construction;
- generic material values;
- socket/attachment system;
- two-hand placement logic.

### Re-author / revalidate
- sockets that directly incorporate legacy body constants;
- clearances calibrated only against the old character;
- grip offsets attached to legacy hand geometry.

No separate third-party equipment mesh assets were found in the current source tree.

## Exercises / biomechanics

### Retain
- exercise schema;
- phase/tempo architecture;
- pose/IK/contact data model;
- exercise-generation families;
- technique validation architecture;
- collision/clearance framework.

### Revalidate against canonical v4 / ORIGINAL v1
- any pose angle introduced solely to compensate for old mesh proportions;
- character-specific grip offsets;
- equipment/body clearances;
- bench/body support bands;
- collision thresholds tied to legacy dimensions.

Do not rewrite exercise intent simply because the new clean model differs; first solve the clean model/rig correctly.

## UI/runtime

### Retain behaviour as specification
- editor workflows;
- timeline behaviour;
- inspection modes;
- generation panel;
- review state;
- mobile inspection requirements.

### Replace implementation
- Zustand state runtime;
- Drei helper runtime;
- React Three Fiber scene bridge;
- React/ReactDOM UI runtime;
- Three.js runtime last.

## Validation principle

For every migrated subsystem:
1. preserve existing behaviour as the reference specification;
2. replace the third-party/legacy-dependent implementation or data;
3. run parity and whole-body tests;
4. only then remove the old path.
