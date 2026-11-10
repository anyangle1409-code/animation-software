# Home Gym PT — Claude reset execution plan (10 November 2026)
Status: planning and preflight. NOT an asset approval or instruction to alter production.
Owner reports Claude quota resets at 12:00 UK time today. Do not use earlier 13:00 assumptions.

## Authority and preservation
- Male: 07c is the owner's retained standing structural base. Treat as immutable; verify actual stored .blend SHA, object counts, visual sign-off and transfer availability before recording "V1 locked".
- Female: F23d is the protected standing source; F83a is the prepared, isolated chest-repair working checkpoint with 7,522 chest-region vertices and packed camera/references. Owner has NOT approved the female chest or female V1. Latest intended child = F84. Do not restart from F11a/F12d or overwrite F23d.
- Verify current F83a full hash before use; prior handover reported SHA-256 a67ad573aa844199c1eb6bac8d6d0b913a482d95c0111624c737172e2b2bab7a. If this asset is absent, locate/export it first; do not silently reconstruct or substitute.
- Current GitHub branch claude/home-gym-pt-animation-txux66 last seen on 2026-11-06 at commit 8056f71d. Newer Blender checkpoints are not automatically in Git. Keep licensed .blend and private photos out of public GitHub. Preserve verified offline/private backups.
- Blender 5.2.x; the prior source opens under 5.2.1 LTS. Avoid accidental saves from earlier Blender versions.
- Preserve geometry/weights/rigs/references of approved or locked bases. Separate numbered working copies and SHA-256 for every attempt. Never force push or change PT-App/production in this lane.
- Maintain independent approval gates for each character: APPEARANCE/STANDING, then MOVEMENT/DEFORMATION, then separate owner release sign-off. A passed test never substitutes for owner's decision.

## Work package A — F84 chest: highest priority and sole geometry edit until owner's review
Read the current F83a handover and use its protected 7,522-vertex editable region. Make a MANUAL Blender chest rebuild, retaining the approved rest of the female proportions, facial features, hands, pelvis, groin U-contour, shorts and rig unless a local fit defect makes an isolated correction necessary.
Acceptance geometry: two naturally rounded breasts individually legible in front/three-quarter views; continuous sternum-to-underbust transition without bridge, horizontal shelf, ridge or flat spot joining the breasts; anatomically plausible attachment to chest wall and a clear side projection (no spherical add-ons); left/right symmetry without obvious loss of natural shape; no sharp seam at breast roots, armpits or underbust. Avoid changing cup size or overall physique gratuitously.
Do not use added spheres, metaballs, booleans, automated volume primitives or procedural shortcuts to fabricate the two shapes. Use hand-edited existing body mesh/topology. The bra is hidden while validating the body; once the BODY passes, locally refit existing bra, preserve modest support and coverage, confirm no skin-through-fabric or odd centre bridge, and retain short coverage and groin silhouette.
Review pack: consistent lighting/camera/scale; front, L/R three-quarter, true side, optional underside; neutral unclothed clay BODY and clothed BODY+BRA comparison with protected F23d and most recent F83a baseline. Include chest-section overlay and wireframe when useful. Mark the WIP F84, with exact paths, SHA and detailed change list. Only one candidate for owner review at a time. Do not label Female V1 approved until the owner explicitly accepts images.
Run existing read-only scripts as appropriate: scripts/meshy/female/chest_sections_f_blender.py, review_chest_shorts_f_blender.py, topology_stats_f_blender.py, compare_f_source_blender.py. Diagnostics may use scripts; geometry edit must be manual. Do not spend reset time on full animations while F84 appearance is unapproved.
STOP GATE A: publish renders and checkpoint; wait for owner appearance approval of female, not automatic further resculpting.

## Work package B — prepare animation infrastructure WITHOUT moving approved geometry
Can run before owner F84 approval, using read-only/preflight tests:
1. Inventory exact Male07c / Female-F84 body, rig, garments, materials, packed images, vertex weights, deform helper bones, bone names/parents, rest transforms, axes, bone roll, unit scale, silhouette landmarks and SHA-256. Both share canonical control names/conventions, NOT identical bone lengths, skin weights or corrective keys.
2. Reconcile canonical contract/version. docs/CANONICAL_SKELETON_FREEZE.md describes hgpt_canonical_v3 (63 control bones), while PT-App AI/ANIMATION_SOFTWARE_COMPATIBILITY.md reports active v4 and an older JSON exporter still labelling v3. Determine actual active rig, export semantics and backwards-compatibility; never silently rename a v3 motion as v4. Keep per-character helper bones outside the 63 common-contract count.
3. Audit existing 2026-11-03 character profiles, retargetSource.ts, joint constraint tests, 2026-10-24 R121 movement tests and docs/FEMALE_CHEST_BRA_MOVEMENT_REQUIREMENTS_20261106.md. Reuse confirmed work, do not replace with an unrelated rig or global reweight.
4. Create report-only, repeatable rig/mesh QA for both characters. Check weight normalization, bind/rest and A-pose, bone rolls, armature parenting, winding/manifold/topology abnormalities, packed file paths, deformed clothing coverage, mirrored motion, animation frame-to-frame smoothness, return-to-neutral, feet and hands contacts.
5. Prepare fixed camera, deterministic pose fixtures and before/after phone-friendly contact sheets; include numerical JSON reports and existing baseline. For any thresholds, use repository's established values; proposed new thresholds must be labelled proposed and owner-reviewed, never relaxed to pass.
6. Do not edit PT-App, do not promote an animation, do not expose licensed character sources in a public repo. Commit only scripts/documentation/synthetic fixtures to a separate non-Claude branch if needed.

STOP GATE B: produce an actionable audit table showing which rig problems are real, test coverage and whether any contract migration is required. No gameplay animations yet.

## Work package C — only after BOTH standing/appearance approvals: prove deformation foundation
Use the SAME canonical pose fixtures on each character with its own skin weights, corrections and body-relative IK. Do not copy male mesh proportions or shape keys onto the female.
Pose matrix, with start/mid/end + return where applicable:
- arm elevation 0,45,90,135,170 degrees in forward and sideways planes; shoulder press rack/mid/lockout, front/lateral raise, overhead extension (twist-sensitive)
- elbow curl 10-140, forearm pronation/supination, wrist/finger grasp; each hand on the specified handle
- squat shallow/deep + lunge, hip hinge, push-up, row, pull-up; foot plant and equipment/bar path.
Special scrutiny: shoulder girdle and scapulohumeral rhythm currently OFF in the frozen v3 exercise motion path, despite candidate girdle work in other branches. Determine and integrate a physically plausible, measured scapular/clavicular path at the CONTROL layer instead of hiding the axilla problem via a bra or corrective surface alone. Inspect scapula rotational axes/signs and back-skin glide. Avoid assuming a fixed universal 2:1 ratio.
Female-specific: breast helper deformation and sports bra containment at every arm elevation; non-stretching centre tissue; side panels and straps at high elevation; pelvic/shorts coverage through squat/hinge. Existing chest elevation test script and old reports are useful baselines, not proof that F84 passes.
Use angle/plane/twist-conditioned correctives only when the core rig and skinning are right; no per-exercise hacks that regress another pose.
Evidence for every pass/fail: identical front, back, side, three-quarter; at least frame extrema and critical transitions; collision/penetration, mesh fold/crumple/stretch, stance/hand/handle drift, joint limits, cloth containment, return to neutral, comparison against fixed approved checkpoint and against prior best results. A wrong reference pose or test harness artifact must not be silently fixed by deforming the mesh.
STOP GATE C: if one stress pose is bad, identify whether defect is skeleton/control, weight, corrective, motion target, solver or contact, fix at correct shared level, rerun whole affected pose matrix; do not push to animations.

## Work package D — production motion pilot (only after approval and Gate C)
Two proofs, not 304 clips:
- Simplest end-to-end integration pilot: animation-software dumbbell_bicep_curl => PT-App db-bicep-curl, as defined in AI/FIRST_PRODUCTION_ANIMATION_PILOT.md.
- Deformation stress pilot: dumbbell shoulder press plus comparison with lateral raise and overhead extension to catch the prior armpit/shoulder regression. Include squat for contact/hip coverage.
For both male and female, reuse one canonical movement definition and body-relative retarget/IK, with separate per-body correctives. Film smooth full eccentric/concentric motion; loops must be stable and return to neutral. Check correct equipment grip and appearance.
Do NOT transfer to PT-App yet. Only an owner-approved model, motion and release package may be rendered/promoted.
Then, after explicit approval, use deterministic WebM/MP4 with schema-v2 animation-export.manifest.json containing actual rig/version/character SHA, source motion SHA, approved status, source_exercise_id and stable exercise_id, first-party provenance; run npm run animation:readiness, animation:validate, animation:promote dry-run. Promote exactly one clip with --apply only after explicit owner agreement and full app regression. No direct 3D runtime dependency in PT-App.

## Export fidelity gate (before any approved video render or app intake)
Blender 5.2 glTF can export bone transforms and morph/shape-key values, but arbitrary Blender mechanisms do not necessarily survive as live runtime logic. Test exact export settings; ensure bone-driven shape-key animations are sampled/baked appropriately. Round-trip a small representative candidate clip (.blend to GLB to fresh Blender/importer or independent reader), compare rest, rack, mid and lockout frames, bone transforms, morph values, garment penetration and cameras with original. A beautiful Blender viewport result is NOT proof of correct exported motion. Keep PT-App playback on first-party rendered WebM/MP4, not a new live third-party 3D runtime.

## Claude usage minimization
- On session start, inventory/verify available assets and read this plan; no re-telling the entire project history.
- Limit first execution to F84 manual chest and report-only B audits. If F83a not accessible, stop A and spend time on B only.
- Every iteration: defect + visual measurement + one change + before/after sheet + regression report + save numbered file. Two consecutive failed variants => revert to last good, diagnose rather than repeating the method.
- Use low-cost clay thumbnails and crop comparisons during edits; render full resolution only for review-ready candidate; preserve evidence.
- Do not claim 'complete' from screenshots alone; do not classify an approval as granted merely because the base looks good.
- If no work remains without owner review, stop and return specific checkpoint paths, hashes, pass/fail evidence and next requested approval. Do not burn quota exploring other models.
- Final session handoff format: BASE USED (path+SHA), CHANGES, TESTS/RUNS, BEFORE/AFTER RENDERS, BLOCKERS, FILES TO RETAIN, NEXT EXACT COMMAND/PROMPT.

## Owner review checkpoints
1. F84 standing bare chest + bra front/three-quarter/side: explicit female appearance approval or concrete corrections.
2. Male07c/Female V1 exact rig inventory and compatibility report; resolve any mismatch before posing.
3. Joint/pose deformation sheet: separate male and female acceptance.
4. One full curl and one shoulder press, per-character, then one PT app demo; only then expand families.

Supporting existing source documents:
- docs/FEMALE_CHEST_BRA_MOVEMENT_REQUIREMENTS_20261106.md
- docs/CHARACTER_ARCHITECTURE_MALE_FEMALE_20261103.md
- docs/CLAUDE_MOVEMENT_SYSTEM_HANDOVER_20261024.md
- docs/HIGH_END_EXERCISE_ENGINE_ROADMAP.md
- PT-App AI/FIRST_PRODUCTION_ANIMATION_PILOT.md
- PT-App AI/FIRST_PARTY_ANIMATION_IMPORT.md
