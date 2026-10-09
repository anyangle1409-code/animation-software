# Home Gym PT — Anatomical bone surfaces: first-party foundation (9 October 2026)

**Status: diagnostic engineering contract only. NO bone-shape anatomy accepted.**
This work is separate from Claude's 9 October skeleton-independent review and all a003/c001–c004 records. It must NOT be merged as an anatomy fix or treated as new canonical bone shapes.

## Architectural decision

A straight armature control is not an actual physical bone. Preserve three different layers:

1. **Anatomical motion/control skeleton:** independently validated joint centres, frames, relative motion, measured bone endpoints and contacts; source of truth. Blender armature bones can remain straight.
2. **Individual anatomical bone surfaces:** distinct, rigid local-frame meshes of humerus, scapula, clavicle, vertebrae, ribs, carpals, etc. Their natural curvature, articular surfaces and important muscle/ligament landmarks come from appropriate anatomical source records. They follow the motion skeleton and never move its joint centres.
3. **Muscles, fat, tendons, ligaments, skin and clothing:** soft-tissue/deformation system separately fit to the accepted skeleton and accepted anatomical envelopes. Do not infer muscle shapes directly from arbitrary cylinder volume.

For the user-facing PT App, detailed internal bone geometry is optional unless an educational skeleton view is added. High-resolution study meshes may remain authoring assets; an optimized rig/soft-tissue representation should drive exercise animation.

## Priorities and anatomical accuracy

| Region | Surface requirements before musculature | Why |
| --- | --- | --- |
| Scapula, clavicle, proximal humerus | Glenoid/humeral head geometry, SC/AC contact landmarks, scapular spine/acromion/coracoid, attachment regions | Raised-arm and armpit/chest deformation |
| Pelvis, proximal femur | Acetabular orientation/hip capsule envelope, pelvis ring, greater trochanter and proximal muscle attachments | Squats, lunges, gluteal/hip volume |
| Knee | Femoral condyles, tibial plateaus, patella contact corridor and extensor mechanism | Rolling/sliding and loaded knee motion |
| Radius/ulna, wrist and hand | Radioulnar articulations, carpal contacts, CMC/MCP/PIP/DIP surfaces and pads/attachments | Forearm twist and equipment grip |
| Spine, ribs, sternum | Vertebral endplate/foramen relations, curved rib centreline and rib/sternal contact surfaces | Flexion, breathing and torso deformations |
| Foot/ankle | Talus, calcaneus, midfoot/toe contacts, plantar interface | Balance, weight-bearing and dorsiflexion |
| Long bone shafts | Anatomical bows, torsion, head-to-shaft relations and gross attachment ridges | Muscle trajectories; tiny pores/striations are unnecessary |
| Skull and small ossicles | Only movement/contact and visual requirements relevant to the app | Avoid spending development time on invisible high-poly details |

The target is **mechanically and anatomically credible** geometry, **not** CT-microtexture everywhere. Modelling a realistic condyle does not alone create a validated contact solver. Cartilage, ligament and muscle constraints must be separately modelled or bounded by evidence.

## Separate surface-registration contract

`scripts/anatomy_fit/bone_surface_contract.py` is a **read-only** proof-of-integration tool for *candidate* shape exports.

Each candidate JSON contains:
- `schema_version: 1`, `status: AUDIT_ONLY`, `units: m`;
- `bone_id` mapping to an already recorded bone;
- `surface_type: closed_bone | open_review_patch`;
- `vertices_m` and `triangles` in an independent *local* mesh frame;
- a proper rigid, non-reflecting 4x4 `world_from_local` transform (never fitted via the old skin);
- local `rig_anchors_local_m.head/tail` which map back to the actual recorded skeleton head/tail;
- optional `articular_patches` with `id`, `joint_id`, `triangle_indices`, linked to an inventory articulation for which this bone is a participant;
- optional `attachment_landmarks` with `id` and `point_local_m`.

**Checks:** finite coordinates, metre units, proper rigid/non-reflecting registration, 0.01 mm anchor numerical agreement, valid triangles, edge-manifoldness for surfaces declared closed, unique patch/landmark identifiers, valid triangle references and articular joint participation (including cartilage-owner resolution).

These are **numerical/interface checks only**. The tool does not decide: true bone lengths or shapes, precise articular congruence/clearance, cartilage thickness, joint movement, clinical anatomy, connectedness/self-intersections/consistent face winding, muscle attachments, suitable scientific sources, or final acceptance. Its result *always* has `canonical_promotion_allowed: false` and `GEOMETRY_CONSISTENT_ANATOMY_UNVERIFIED`.

The `rig_anchors_local_m` are registration anchors, NOT a claim that head/tail coincide with actual bony extreme surfaces or joint centres. Metadata claiming a paper or a review does not establish scientific truth.

### Example invocation

```bash
python -m unittest discover -s scripts -p 'test_bone_surface_contract.py' -v

python scripts/anatomy_fit/bone_surface_contract.py \
  --asset /path/to/independently-modeled-bone.json \
  --skeleton ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json \
  --articulations ORIGINAL_V1_WORK/anatomy/adult_articulation_inventory.json \
  --out /tmp/bone_surface_report_new.json
```

The existing a003 skeleton is used here solely as a **diagnostic mapping baseline**, not a canonical source of anthropometric truth. Output is create-only so older reports cannot be overwritten.

## Required next steps (separate from this delivered contract)

1. **Skeleton gate first:** wait for source-compatible accepted joint centres, contact axes and skeletal proportions, particularly the existing 0 READY / 9 PARTIAL / 3 BLOCKED region gates.
2. **Bone-shape evidence:** acquire licensed anatomical geometric data and sources with defined population, units, registration frame, end-surface meaning and articular landmark definitions. CT-derived or specimen data must be scaled/fitted only with evidence, not an arbitrary uniform scale to cover joint gaps.
3. **Register surfaces:** derive the rigid bone-local registration to the canonical skeleton, export Blender mesh triangles, patches and ligament/muscle attachment points. Validate with this module.
4. **Extend geometry validation:** check closed-surface orientation, connected components and self-intersections; assess inter-bone joint surface proximity and clash in both neutral and extreme poses. Flag which joints require cartilage/contact representation rather than direct bone-on-bone collision.
5. **Muscle attachments:** maintain origin/insertion as source-bound local surface points and test trajectories/deformation over a broad exercise set; do not assume the visible muscle mesh automatically simulates anatomy.
6. **Production & variants:** male and female characters may share animation semantics and anatomical inventory; separately verify skeletal morphology, articular geometry and muscle attachment profiles. Export appropriately optimized app assets.

No files on Claude's branch, PR #8, c004, original rig, existing character mesh, freeze report or tracker are changed by this spike.
