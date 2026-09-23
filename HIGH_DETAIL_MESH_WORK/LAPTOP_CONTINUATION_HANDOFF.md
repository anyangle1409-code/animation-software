# Laptop continuation handoff

Purpose: make the next Blender/Work session deterministic and keep the high-detail mesh work isolated from production while the canonical rig is being finalized.

## Current review baseline

Branch: `codex-high-detail-candidate-v6-knee-review-20260922`  
Commit: `b2203cfccd30d6835473ef2e1dee37965da22d02`

Latest candidate:
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb`
- `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend`

Recorded hashes:
- dressed GLB: `ff39e07735697d5423968a8ec1c05f2c6c68fced0d757ea1b4047096bc7a5306`
- bare GLB: `0170b3673d7a050e8aacd2683347cfa6dd000719dba0a6862c16bd7a4a5723e0`
- blend: `2a2d0326129ce5c2555c596a49a281d655f33acfd7bbd9514cad3e759586a0df`

V6 body: 33,089 vertices / 62,961 triangles. Integrity report records zero degenerate triangles and zero edges shared by more than two faces.

## What V6 proves

V6 is a candidate-only knee-seam checkpoint derived from V5.

- The paired inner-knee gap that reached 0.58 mm in V5 is 0 mm in all saved V6 pose snapshots.
- The largest individual rest-position move was 0.335 mm.
- The original rig, skin weights, animations, exercise definitions, grip/equipment logic and production references were not changed.
- Six focused guards passed: shoulder sagittal target, bare/dressed equivalence, grip/343-degree wrap, renderer/exporter agreement, dumbbell/shorts clearance, and the sampled five-exercise review.
- Original hand positions, all 160 existing production-character bone matrices, and equipment transforms matched the frozen dressed reference in the sampled review.
- All 400 pinned source files and V5 deliverables were verified unchanged.

This is not a finished mesh.

## Known open mesh work

### 1. Knee
The medial knee is only geometrically aligned, not topologically repaired. Two open boundary strips remain. The pointed medial overhang remains.

Next real knee step: retopologize the medial-knee strips into connected anatomical joint loops and deliberately shape the patella/tendon/medial-knee transition. Do not repeat the three rejected broad smoothing/contour trials as if they were a solution.

### 2. Hands
V5/V6 provide denser, contact-safe hand topology but not finished anatomy.

Preserve the 682 original push-up floor-contact guard vertices in `reports/hand_contact_guard_v5.json`. Do not alter the floor-contact solution just to improve appearance. Model finger volumes, thumb web/base, palm forms and wrist transition around that constraint, then re-run grip and floor-contact checks.

### 3. Shoulder / axilla
Do not make a final shoulder/chest/back/armpit weighting decision against the old frozen hierarchy.

The canonical-rig audit and scapula spike performed after this candidate showed that a scapula-bearing hierarchy is likely to be adopted. The structural rig change is being handled separately on `chatgpt/absolute-retarget-imports`.

Safe before that rig lands:
- geometry study
- topology planning
- material work
- non-destructive shoulder surface experiments kept as separate candidates

Hold until the final rig is confirmed:
- final shoulder/chest/back/armpit skin weights
- final scapular deformation tuning
- any production promotion

### 4. Materials
Final skin materials are still pending and can be worked on independently of the rig, provided production assets remain untouched.

## Reproduce the V6 baseline first

From `HIGH_DETAIL_MESH_WORK`, with Blender 5.2+:

```text
python scripts/bootstrap_from_repo.py
blender --background --factory-startup --python scripts/build_candidate_v6_knee_seam.py -- v6_knee_seam_rebuild
python scripts/make_bare_variant.py v6_knee_seam_rebuild
```

The reviewed V6 dressed rebuild was byte-identical on Blender 5.2.1. Reproduce and verify the baseline before doing new modelling so any later difference is attributable to the new work.

## When the finalized canonical rig is available

Do not merge this review branch into the production/source branch just to obtain the rig.

Use the V6/V-next mesh as a geometry source and migrate it deliberately onto the confirmed rig in a fresh candidate checkout.

Required order:

1. Record the exact source-rig commit and candidate commit.
2. Confirm the final canonical hierarchy and any retarget changes first.
3. Confirm the pre-weight decisions for forearm twist distribution and carrying angle.
4. Transfer/rebind the candidate mesh to the confirmed production-character hierarchy without changing exercise mechanics.
5. With any new scapula bones neutral, prove current exercise output remains equivalent within numerical tolerance before painting them.
6. Paint shoulder-blade/back/chest/armpit regions across the final girdle bones.
7. Only after the weights support it, enable/tune scapular rhythm.
8. Re-run full current source tests plus all candidate mesh guards and visual exercise stress poses.

If the final source character gains new deform bones, do not assume old positional joint indices remain valid. Map/remap by bone name.

## Mandatory regression gates after each candidate-only modelling step

At minimum re-run:
- bare/dressed equivalence
- grip contact and finger wrap
- push-up floor contact
- renderer/exporter agreement
- dumbbell/shorts clearance
- knee/hip deformation checks for squat changes
- overhead shoulder/axilla checks for shoulder changes
- sampled motion review for curl, squat, shoulder press, push-up and pull-up
- the latest full source test/build suite from the exact rig commit being targeted

Preserve all previous candidates and comparison renders. Create a new review branch for each accepted candidate-only step. Do not overwrite V6.

## Stop conditions

Stop rather than forcing a visual fix if any edit:
- changes exercise mechanics, IK targets, contact/grip logic or accepted equipment transforms
- alters production/bundled assets
- requires loosening a validation threshold merely to pass
- changes floor-contact behavior through new low hand vertices
- creates a shoulder improvement that depends on the pre-scapula hierarchy
- introduces unexplained topology, skin-weight, or retarget differences

The goal is to arrive at the final rig with the best geometry candidate intact, then do one intentional final binding/weight/deformation pass instead of repeatedly repainting against obsolete skeletons.
