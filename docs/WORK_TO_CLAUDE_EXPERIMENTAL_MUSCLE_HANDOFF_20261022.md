# Home Gym PT — Experimental Muscle Layer (Work → Claude)

Status: TEST-ONLY / NOT PRODUCTION / OWNER REVIEW REQUIRED
Date: 2026-10-22
Authority: docs/ORIGINAL_V1_MUSCLE_ARCHITECTURE_RESEARCH_20261022.md (this branch); original shared master plan in PR #48; skeleton precedence policy in codex/whole-body-biomechanics-audit-20261007.
Known evidence: PR #107 rejected standalone Blender Preserve Volume solution; PR #113 has nine ORIGINAL_v1 movement benchmarks and rejected/partial corrective experiments.

## Non-negotiable protection
1. Fetch live GitHub HEADs, review open PRs/other agents' work, inspect local working changes and source assets. Do not reuse a stale checkpoint. Respect existing owner-assigned lanes.
2. Do NOT edit, rename, delete, replace, push onto, merge or promote the existing ORIGINAL_v1 source, authoritative skeleton, original production skin/rig, approved assets or main branch.
3. Create an **isolated named experiment branch from the freshest reconciled source snapshot**, e.g. work/experimental-anatomical-muscles-20261022. Record exact original commit SHA, source .blend path, file hash, provenance and a reproducible copy procedure before work.
4. If Blender is available, generate a distinct copy named e.g. HomeGymPT_ORIGINAL_v1_MUSCLE_LAYER_EXPERIMENT.blend. Verify copied input hash before modifications; after editing confirm original bytes are unchanged.
5. If Blender is not available, limit Work to research, muscle registry, schema, scripts and tests that actually run in accessible environment; label Blender-required acceptance as BLOCKED. Do not claim executed model tests.
6. Keep optional .blend, meshes, rendered evidence, and proprietary reference assets private if Git LFS/licensing/resource constraints apply. Commit scripts, registry, manifests and non-sensitive reports in experiment branch. Never assume an inaccessible binary was transferred to Claude.
7. NO production GLB replacement, no renderer switching, no PT_MODEL_VERSION modification (preserve 1.0), no merge or deploy without owner approval. No automatic approval on passing synthetic tests.

## Work order: bounded independent phases
W0. Baseline / evidence inventory. Confirm latest source model branch and commit, exact Blender version, rig joint count/IDs, source asset hash, current proposed physics/deformation systems, and Nine movement baselines PR #113. Check prior failed approach PR #107 so no blind repetition. Produce blocker/evidence manifest.
W1. Author scientific muscle registry with stable IDs for individual functional heads/bundles (not only broad muscle groups) in shoulder/axilla and hip/pelvis. For every record: side, anatomical region, origin/insertion names and accepted bone/landmark IDs, path/via/wrap targets, joint crossings, tendons vs fibres, deep/superficial neighbors, overlying skin mask, suggested visible activation mode, provenance URL, reliability, license, implementation state. Do not fabricate numerical landmark positions. Include code that checks schema, bilateral completeness, valid available bone IDs, source information, neighbor references and layered status.
W2. Shoulder functional design. One prototype with deltoid anterior/middle/posterior, trapezius upper/middle/lower, serratus, rotator cuff, pec major, lat, teres major and biceps/triceps long heads. Keep bones as separate anatomical reference vs kinematic rig. Use verified original skeleton; do not move canonical centers. Demonstrate muscle length changes and safe path wrapping from neutral to overhead. **No default automatic skin deformation accepted from simply placing muscle meshes underneath skin.**
W3. Pelvis/hip functional design. Gluteal group, iliopsoas, TFL, sartorius, rectus femoris, vasti, hamstrings and selected adductors. Diagnose upper-thigh horizontal-band artifacts, central groin pinching and gluteal shelf (topology/normals/overlap/weights/modifier-order) before modifying geometry. Leave torso/hip joint anchors untouched. Preserve genital-neutral smooth outer mesh.
W4. Rigged skin response experiment. Preserve baseline skinned body; author targeted region-local pose correctives/muscle cages/skin influence and compare frame-by-frame. Independently control joint pose vs activation; do not equate contraction with shortening or treat an exercise name as measured activation. Check expected tissue contact vs genuine triangle penetration.
W5. Benchmark native Blender results when environment permits: front/side/back/3-quarter neutral/overhead/hip-flex/squat pose sheets at identical camera alignment, muscle-only skin-only overlay, objective collapse/stretch/contact/volume and mesh normal/topology diagnostics; preserve baseline methods. Regress all nine M1/M2 benchmarks and inspect extra shoulder and hip transition frames. Record results as pass/fail/baseline changes, no passing declarations without actual execution.
W6. Hand over precise scene files or accessible private artifact links, source and modified binary hashes, branch+SHA, collection/asset names, rig attachments and caveats, reproduction commands and test results. Ask Claude to perform independent Blender visual/anatomical review and amend **the experimental candidate only**. Hand off any new GLB morph-target/runtime contract requests separately to first-party engine owner.

## Claude independent reviewer checklist
- Fetch Work branch + artifacts, verify exact source and experiment hashes, compare against untouched ORIGINAL_v1.
- Confirm landmark correctness, tendon paths and deep/superficial layering against primary anatomical evidence.
- Identify and correct interpenetration, skin deformation, axilla/cuff collisions, glute fold/inner-thigh pinching, muscle sliding, unrealistic bulges and topological faults.
- Validate static views AND whole movement trajectories at realistic scales and mirrored joints; do not infer measured forces from poses.
- Report before/after metrics and images including fail cases. No release approval, merge, runtime integration or source replacement without owner consent.

## Work checkpoint format (required)
- Branch and exact commit SHA
- Baseline branch + commit + original .blend path/hash and experiment .blend path/hash (or say not available)
- Files modified/created, reproducible generation steps
- Sources newly assessed, provenance and license constraints
- Native Blender version and actual tests (PASS/FAIL/SKIP/BLOCKED), phone-view renders, exact known defects
- Claude next task and verification targets; requested input if truly blocked
- Explicit production unchanged: yes/no, with evidence

## Stop/go rule
Only a review-only branch and copy is permitted. Accepted canonical skeletal anatomy and original source never change to accommodate experimental surface shapes. No irreversible changes; no endorsement of clinical or physiological accuracy based on screenshots or morph metrics alone.
