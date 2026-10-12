# G5i — Chat software consolidation, mobile audit, and Work handoff

## 1. Consolidation / review status (12 October 2026)
- Source parser base PR #85, consolidated renderer review PR #101, followed by PR #102 live-camera correction. Both remain drafts; no production merge.
- PR #101 exact-head 15/15 workflows PASS, #102 exact-head 4/4 PASS. Keep individual component PRs (#86-89 and #91-100) for traceability; sibling #90 camera work was reconciled through #102 rather than falsely claiming a merge.
- PT-App existing video-export architecture retained, PRs #4 handoff preflight, #5 fail-closed candidate readiness, #6 promotion ID/file collision guards remain isolated drafts, not installed in production. Do NOT bundle a direct-GLB player into PT-App as an unreviewed replacement for schema-v2 WebM/MP4.
- Human review and real authentic source full-body hardware GPU render remain pending. CI is not a visual/anatomy approval.

## 2. iPhone/mobile reliability risk and test
- Prior reviewer API permitted width <=2000, height <=2400 and DPR <=2. Worst case was 19.2 million drawing buffer pixels, about 76.8 MB for one 4-byte colour buffer **before** depth, GPU textures, webview/system overhead and buffers. This is a risk estimate, not measured iPhone memory.
- The new owner-review-only viewport helper caps requests at 2,000,000 pixels, about 8 MB RGBA8 colour-buffer budget. It lowers effective DPR when needed; preserves width/height logical dimensions and does not modify the general first-party GPU renderer or source GLB data.
- Unit tests assert ordinary unchanged scaling, worst-case bounding, invalid input rejection and deterministic bounds; existing local GLB/camera and renderer regressions run in CI.
- Remaining on-device tests: actual Safari/Chrome WebGL2 context creation and recovery, native palette shader/link and source vertex buffer, first 5-view image, zoom/orientation, memory usage, frame time, device throttling and disposal. Neither performance nor render quality is yet measured on a physical phone.

## 3. Exact Work → Chat model and motion handoff requirements

**Work is authoritative for Blender geometry and biomechanics**. For each reversible candidate send, as appropriate:
1. Exact source branch+commit and private binary SHA256/size, authored vs licensed provenance, candidate/rejected/approved classification and *actual* neutral GLB.
2. Human height and validated foot length / foot floor-contact profile; updated heel, ankle, MTP and toe-tip semantics with measurement convention, bilateral evidence and visual owner acceptance.
3. Rig joint count and ordered bone IDs, parent relationships, world-rest matrices, inverse binds, source coordinate frame and laterality mapping (the current reference runtime has 67 joints, Blender Z-up to glTF Y-up; names may reverse anatomical left/right).
4. Complete mesh schema: vertex and index counts, materials, normals, UVs, joint indices/weights, corrective target IDs+rest coefficients; any changed original SHA must **not** be substituted into the immutable older SHA-pinned review validator without a deliberate gate update.
5. Exercise motion samples with timestamps, continuous joint transforms, load/contact conditions, unsupported-movement declarations, and source/reference pose comparisons for representative overhead, press, pull, hinge, squat/lunge, push-up, grip, twist and stance/locomotion basis.
6. Actual Blender evidence: front, side, rear, three-quarter and overhead stills/videos for neutral and controlled movement, foot/toe close-ups, shoulder/chest/armpit deformations; per-view time/angle and acceptance result. Private restricted imagery stays out of public Git.
7. Source-grounded limits, contact/penetration residuals, joint-continuity and mirror tests, comparison protocol, performance budgets and explicit rejected/partial/accepted status.
8. Independent rights and release approvals. A diagnostic GLB is NOT an app-ready animation video. Final PT-App intake requires schema-v2 `animation-export.manifest.json`, exercise IDs confirmed in PT mapping, file hashes, approved character, rig, render profile, original motion SHA and verified first-party WebM/MP4.

**Critical current blockers:** rejected foot shape, raised neutral distal toes and disputed 30.92cm length; provisional shoulder/whole-body skin deformation; original human GPU proof; rights/visual/motion owner approval. Chat cannot mark these passed for Work or infer approval from a metadata boolean.

## Acceptance
Keep this branch draft and use targeted CI. No production merge, original mesh/skeleton edits, removal of temporary app media, or implied physical-device certification.
