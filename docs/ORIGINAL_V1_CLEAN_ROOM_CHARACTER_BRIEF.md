# Home Gym PT Male ORIGINAL v1 — clean-room character brief

## Objective

Create the first distributable Home Gym PT male character whose geometry, topology, rig binding, clothing and materials are wholly project-authored and not derived from the imported/legacy character lineage.

This character is a new asset, not V16 of the imported line.

Suggested asset identity:
- `HomeGymPT_Male_ORIGINAL_v1.blend`
- `HomeGymPT_Male_ORIGINAL_v1.glb`
- `HomeGymPT_Male_ORIGINAL_v1_SHORTS.glb`

## Clean-room rule

Begin from a blank/new Blender scene. The initial mesh may either be authored manually or generated from the **pinned project-authored procedural profile scaffold at commit `e6ef05b4312a1928cc6fbb71b92a94ceaff1cc62`**, as defined in `ORIGINAL_V1_PROCEDURAL_SCAFFOLD_DECISION.md`. Do not use current profile values unless separately audited.

Do not:
- duplicate/import legacy body geometry into the modelling file as a mesh source;
- retopologise or shrink-wrap against V5/V6/V7/V8/V13e/V15f;
- copy vertex positions, edge loops or face layout;
- transfer weights;
- transfer UVs;
- transfer textures/materials;
- transfer legacy morph targets;
- transfer imported source skeleton transforms or inverse bind matrices;
- run nearest-surface projection from legacy body/hand surfaces.

Legacy character renders may be used only as examples of defects to avoid and as a behavioural benchmark where necessary. The new shape should be driven from anatomical requirements, project-authored measurements and generic human anatomy.

## What may be reused

Project-authored system specifications may be reused:
- `hgpt_canonical_v3` bone naming/hierarchy if provenance review confirms it is project-authored;
- project joint axes and anatomical ranges;
- exercise definitions;
- contact-lock semantics;
- equipment socket definitions;
- generic dimensional targets;
- validation thresholds;
- animation engine behaviour;
- test methodology;
- movement-family requirements.

## Required anatomical coverage

The mesh must be designed from the start for more than the current exercise list.

Required deformation zones:
- cervical spine;
- thoracic spine;
- lumbar spine;
- pelvis/hip crease;
- glute/upper-thigh junction;
- knee/patella region;
- ankle/Achilles;
- shoulder/deltoid/axilla;
- scapular region;
- elbow;
- forearm pronation/supination;
- wrist flexion/extension/deviation;
- palm;
- thumb CMC/opposition region;
- MCP/PIP/DIP finger joints.

## Whole-body movement envelope

Before character acceptance, validate at minimum:
- trunk flexion: sit-up/crunch class;
- trunk extension;
- trunk axial rotation: Russian-twist class;
- lateral flexion;
- deep hip flexion;
- squat;
- forward/reverse lunge;
- hip hinge/RDL;
- calf raise;
- horizontal push;
- vertical push;
- horizontal pull;
- vertical pull/hang;
- shoulder raise/elevation;
- elbow flexion/extension;
- forearm pronation/supination;
- wrist-loaded floor contact;
- loaded dumbbell grip;
- bar grip;
- bilateral and unilateral stance where applicable.

The purpose is to prove the body, not merely replay a fixed catalogue.

## Topology principles

The modelling target is deformation quality, not maximum polygon count.

Require:
- continuous loops across bending joints;
- enough circumferential resolution for shoulders, elbows, knees, wrists and fingers;
- no long planar bands across finger shafts;
- no razor-thin joint faces;
- retained volume under flexion;
- symmetric starting topology where anatomically appropriate;
- deliberate asymmetry only when explicitly authored;
- manifold production surface unless a documented design reason requires otherwise.

## Hands

Use lessons from V13e/V15f without copying their geometry.

Requirements:
- anatomically continuous finger shafts;
- rounded transitions through MCP/PIP/DIP;
- usable thumb-index web;
- adequate thenar/hypothenar volume;
- palm capable of handle contact;
- fingertips suitable for wrapping around cylindrical handles;
- enough topology for closed fist, dumbbell grip, pull-up grip and push-up loading;
- no dependence on moving a handle into the hand to hide bad anatomy.

## Shoulder girdle

Model the shoulder around the intended canonical chain rather than inheriting the legacy imported forward shoulder placement.

Requirements:
- deltoid cap reads as centred over humeral axis;
- upper arm visually hangs beneath shoulder;
- clavicle/scapula region supports later scapular motion;
- axilla does not collapse under elevation;
- chest/back/shoulder topology supports overhead positions.

## Rigging

Bind to the project-owned canonical rig only after the new mesh exists.

Weights must be authored for ORIGINAL v1; do not transfer legacy skin rows.

Required proof:
- weights normalised;
- no unexplained cross-body influences;
- mirrored regions behave equivalently where expected;
- hands/fingers independently controllable;
- scapular influences available for later activation;
- bind pose reproducible.

## Clothing

Rebuild shorts from new topology around ORIGINAL v1.

Do not transplant the existing F3/legacy garment.

Requirements:
- independent garment mesh;
- safe squat/push-up containment;
- no groin/body intersection visible at required views;
- waistband and hems deform naturally;
- garment weights authored for ORIGINAL v1.

## Materials

Use project-authored simple materials first.

Avoid introducing texture provenance risk during geometry development.

Initial acceptance can use:
- authored numeric skin colour/material values;
- authored shorts material;
- authored eye/material values.

Textures, if added later, require their own provenance record.

## Stage gates

### O1 — blank-source proof
Record:
- creation date;
- branch;
- Blender version;
- empty/new starting file hash;
- authoring script/tool path;
- declaration that no legacy mesh was imported as modelling source.

### O2 — neutral anatomy
Approve bind/neutral silhouette and proportions before rigging.

### O3 — topology audit
Check manifold state, degenerates, loop structure and left/right consistency.

### O4 — canonical binding
Bind and prove neutral equivalence plus joint control.

### O5 — movement-envelope validation
Run the whole-body movement battery.

### O6 — contact/equipment validation
Run floor, grip, equipment and collision gates.

### O7 — dressed equivalence
Add original shorts and rerun movement/contact tests.

### O8 — final visual acceptance
Only after all previous gates pass may ORIGINAL v1 become the production character.

## Legacy benchmark use

V15f may remain as a reference benchmark for:
- visible hand faceting to avoid;
- push-up contact behaviour;
- exercise clearances;
- deformation metrics;
- approximate visual quality.

It must not be a geometry-transfer source.

## Deliverable evidence

Create:
- `docs/ORIGINAL_V1_PROVENANCE.md`
- `reports/original_v1_topology.json`
- `reports/original_v1_rig.json`
- `reports/original_v1_motion_envelope.json`
- matched review boards for the movement envelope;
- SHA-256 hashes for every accepted Blend/GLB.
