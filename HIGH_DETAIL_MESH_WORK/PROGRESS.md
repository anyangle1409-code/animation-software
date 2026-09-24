# Candidate progress

## 2026-09-24 — V12c palm-volume hand review checkpoint

Built a new candidate from the current V11 Blender mesh, preserving V11 seams, caps, topology, UVs, weights, frozen rig and all production files. V12c adds symmetric interior palm/thenar/hypothenar volume with all open-boundary and 682 floor-contact vertices pinned. Two wider local trials produced 26 and 6 folded edges against V11's 4; V12c restores the count to 4. The trials remain local experiments, not review candidates.

V12c GLB and bare variant pass quick integrity, strict floor contact, five focused guards and seven exercises over 26 frames against pinned runtime `614033b`. Bind and posed seam bands match V11. Matched V11/V12c open-hand, fist and exercise boards are in `renders_v12c_palm_volume/`. The improvement is modest; inherited finger-pad facets and broad hand silhouette remain. Visual acceptance is pending; no grip refit or production promotion. See `REVIEW_V12C_HAND_PALM.md`.

## 2026-09-23 — V10 Blender hand-retopology review checkpoint

V8 remains the accepted body/knee geometry baseline. The user rejected V9 as a hand anatomy solution while preserving it as experimental. V10 was built from V8 in an isolated candidate branch; it adds 13,586 local Blender hand/wrist vertices through edge subdivision and anatomical sculpt fields. The editable Blend, dressed GLB, bare GLB and matched open/fist/exercise images are separate assets.

An early V10 pass had bone-blend ridges. A trial using an older pose reference made that worse and was discarded. Correcting added bind positions against the actual pinned-runtime curl matrices limited the adjustment to 1.361 mm. A stronger smoothing trial caused eight overlapping-edge failures and was discarded. The saved pass uses limited local smoothing and passes the topology check with zero degenerate/non-manifold edges.

The saved V10 passes five focused runtime guards, seven exercises over 26 frames, bare/dressed equivalence and the protected floor check. Bone and equipment matrices match V8; all 682 protected original floor vertices and all non-hand original vertices are fixed. Review renders still show faceted fingertips/joint bands, a thumb-web seam and a segmented wrist transition. V10 is not accepted or promoted. Stop for visual anatomy review before grip refit. See `REVIEW_V10_HAND_ANATOMY.md`.

2026-09-22. User authorised this Windows workspace as the equivalent of the Linux path.

Source branch chatgpt/absolute-retarget-imports, pinned snapshot f9cca7c34880a2c5e30b63a42c762d7fd99205e8 (archive, not a production checkout). Playbook and handoff reviewed, including historical rejected rig experiments; current mesh-only instruction takes precedence. All 63 manifest entries pass byte-size and SHA-256 verification. Blender 5.2.1 LTS launches.

Frozen references are under reference/anyangle1409-code-animation-software-f9cca7c/HOME_GYM_PT_GPT_MESH_HANDOFF/characters. Bare: 2303476 bytes, b08844339fb66e54a290eb9687fdc48296d087e4cbbb83981041a03d8501cc7a. Dressed: 2417316 bytes, fe30c1dadb1dca442b79155cf3bb662e7b22b4f6f48ee806258fde798e34a71b. Original v8 production binaries are not supplied; the playbook designates CORNER_FINAL as the frozen mesh reference.

## Pipeline

1. Reproduce sagittal measurements with copied, unchanged production source and supplied harness.
2. Model candidate shoulder surface using posed-space measurements mapped back through the unchanged skin transforms. Preserve hand geometry/topology/weights and all rig data.
3. Refine body surface with candidate-only topology, preserving UVs and accepted rig/grip metadata. Aim for 50–100k body triangles without claiming subdivision alone constitutes new anatomy.
4. Save editable Blender checkpoints and separate GLB. Verify raw node matrices, hierarchy, inverse binds, animation data and metadata against frozen source.
5. Run five exercise comparisons with current correctives and equipment transforms. Save matched renders and measurements. Report inherited regressions separately.

No production source, bundled.ts, frozen reference, exercise or rig edit is authorised or planned. No merge/promotion.

Reference-board photograph is not included; use the supplied diagnosis images and explicit numeric targets for this first review candidate, not an identity reconstruction. Candidate validation source is a disposable copy under validation; reference hashes are recorded for final integrity checks.

## Modelling and validation milestones
- Reproduced supplied sagittal baseline exactly: joint (214.9, 1412.1, -21.9) mm; deltoid apex 7.8 mm above, z +4.8 mm.
- Initial curved subdivision introduced a 3.7 mm runtime root offset via foot contacts. Rejected; feet and hands now preserve original topology. Source has two influence sets: originals retain both byte-for-byte; new vertices use the runtime's four-influence convention. Reported weight truncation is limited to new vertices.
- 59,128-triangle candidate at gain 0.75 reached 30.1–30.2 mm above, apex z -66.1. All original hand vertices, 160 bone matrices and equipment matrices matched baseline exactly at Bottom/Mid/Peak/Return across five exercises. Loops close. This numeric pass did not constitute visual acceptance.
- Visual inspection exposed ridges at shoulder ownership boundaries and interpolation cross-terms in new skinning vertices. Corrected midpoint rest placement through inverse runtime skin transforms; local anatomical smoothing now blends across ownership boundaries. Checkpoints retained before each change.
- Full unchanged code suite run: 290 passed / 8 failed / 1 skipped, exactly the handoff count. Run used one worker and 30-second test timeout to avoid machine-load timeouts; no assertions changed. Dependencies installed in candidate validation copy using package ranges (versions recorded in validation/pnpm-lock.yaml).
- Playbook's historical 22 unreachable push-up targets are 16 in the current validateClip report; full suite still has the same eight failures. No exercise mechanics retuned.

## First review candidate saved
- Final gain 0.90 and shoulder smoothing: 31.9 mm height, apex z -69.5 mm, joint unchanged.
- Five exercise render sets and overview inspected; shoulder transition improved. This is a review milestone, not production readiness.
- Final integrity: 400 reference files unchanged; copied source unchanged; raw rig/metadata and original binary preserved. Both deliverables saved and hashed in reports/final_integrity.json.
- Scope and remaining anatomy/topology/texture limitations recorded in REVIEW.md. No production files modified.

## V2 investigation
Claude independent review supplied by user: runnable guards passed; bare equivalence pending. Correspondence check on original vertices confirms real cap reshaping: mean z -32.315 mm in fixed baseline cap selection; upper shaft -8.458 mm, lower shaft +0.067 mm. Do not attribute the entire band change to vertex density. V2 trial reduces rearward sculpt coefficient from 0.040 to 0.012 m, with rig and height uplift unchanged. V1 preserved.

V2 review milestone: cap original-vertex mean backward motion reduced 32.315 to 10.727 mm. Height 31.9 mm; apex -47.8 mm. Bare variant created; six focused tests clean, 26 samples per exercise. V1/reference/production unchanged; see REVIEW_V2.md and final_integrity_v2.json.

## V3 candidate checkpoint
Weight audit showed v2's 20.82% maximum discarded influence occurs at neck/jaw midpoints; shoulder maximum is 3.87%. A 5% ceiling was verified red on v2, then the v3 builder skipped only the unsafe midpoint edges. V3 has 57,721 triangles and maximum new-vertex loss 4.98%. Shoulder sculpt and original vertices/weights are unchanged. Six focused tests passed cleanly over 26 frames per exercise; bare/dressed, grip, clearance and sagittal checks pass. Integrity report confirms 400 source files and all v2 deliverables unchanged, zero degenerate body triangles and no edges shared by more than two faces. Overhead armpit fold is visible in the frozen reference too; no speculative corrective added. See REVIEW_V3.md.

Reproduction audit: scripts/bootstrap_from_repo.py verified the 400 pinned files; the v3_rebuild run made a byte-identical GLB (SHA-256 07d1b809cb6ae649ee86cbb8e747b43274a557bb9f4f32b685bd50c19a31c16c). The posed sculpt reference and hash manifest are packaged for branch review. See REPRODUCE_V3.md.

## V4B axilla checkpoint
Tracked 224 fixed original edges per axilla through frozen, V3, V4 and V4B posed meshes. V3's broad cap sculpt increased overhead underarm compression; V4 restricted it medially, then V4B tapered the lower anterior fold. Shoulder-press peak severe compression (left/right) fell from V3 43/41 to V4B 16/16; frozen is 7/6. V4B keeps the curl-shoulder objective (31.0 mm cap height, apex z −47.4 mm) and unchanged rig. Six focused checks and the five-exercise motion review pass. Frozen sources and V3 assets remain hash-identical. See REVIEW_V4B.md. The fold is improved, not solved.

## V5 hand topology checkpoint
An axilla weight-transfer trial worsened the V4B overhead fold (16 to 23 severely compressed fixed edges at shoulder-press peak) and was rejected. A hand-subdivision trial changed the push-up floor solution by 1.39 mm because the runtime samples the lowest skinned hand vertex. V5 protects 682 floor-contact vertices from subdivision and adds 2,778 safe interior hand vertices. The 62,961-triangle body passes six focused checks and the 26-frame/five-exercise review with original hands, bones and equipment transforms matching the frozen reference. The inherited finger shape remains coarse; this is a topology foundation, not finished anatomy. See REVIEW_V5_HANDS.md.

## V6 knee seam checkpoint
The squat close-up revealed two parallel 15-vertex boundary paths at each inner knee. Their skin weights and normals match, but posed gaps reach 0.58 mm. Three candidate-only surface-smoothing/contour trials failed to improve the pointed silhouette reliably and were rejected. V6 aligns 30 matched pairs by at most 0.335 mm per rest vertex. The paired gap is exactly 0 in 20 saved poses. Six focused checks pass, and 400 source files plus V5 assets are unchanged. The UV seam is still topologically open and the pointed overhang remains, so a true knee retopology/sculpt pass is still required. See REVIEW_V6_KNEE_SEAM.md.

## V7 knee review checkpoint — 2026-09-23

Read `WORK_MASTER_HANDOFF.md` on branch `codex-high-detail-candidate-v6-knee-review-20260922` at `9e7bc18`; ran `RESUME_WORK.bat`. Its audit initially expected a nonexistent `rig_baseline.commit` field instead of the manifest's `freeze_commit`, and the laptop lacked npm. Candidate-only automation was corrected to read `freeze_commit` and reuse the already installed validation dependencies. The complete resume audit then passed with Blender 5.2.1 LTS and the current 63-bone runtime source `614033b`.

Started a fresh V7 Blender candidate from unchanged V6. A direct GLB index weld reduced local open edges but produced inverted/stretched UV0 faces, so it was rejected. A narrow image-guided sculpt caused a cliff and was rejected. A topology-aware posed-space smoothing of two knee regions produced a substantially cleaner front, side and three-quarter squat contour. The editable Blender mesh welds the 30 paired knee-seam vertices while preserving per-corner UV loops. GLBs retain their UV split, with 0 mm geometric seam gap in all 28 saved poses. Only 1,078 knee positions changed, maximum 25.15 mm rest move; all GLB weights, UVs, indices, materials, rig and animation data match V6. The previous V6 artifacts and 400 pinned source files remain unchanged.

`FINISH_CANDIDATE.bat v7_knee_retopology knee` passed: five focused guards and 26-frame comparisons for seven clips (three curl variants, squat, press, push-up, pull-up). The original hand, bone and equipment transforms match the frozen reference exactly. Review renders and hashes are in `REVIEW_V7_KNEE_RETOPOLOGY.md`. The knee still has a small medial notch and broad patellar shape. V7 is review-only; stop before the hand pass, as the master handoff requires.

## V8 knee anatomy review checkpoint — 2026-09-23

The user accepted V7's connected knee topology and requested one final local anatomical shape pass before hand work. `RESUME_WORK.bat` passed. V8 was built from V7 with a shallow symmetric patellar reduction, a connected-surface medial smoothing pass, and subtle upper-shin/tendon definition. A strict paired-vertex trial produced a visible edge and was rejected; the final revision mirrors the smooth displacement field across the existing asymmetric vertex sampling. The V7 topology, UVs, rig, weights, exercise definitions and non-knee body surface remain unchanged.

`FINISH_CANDIDATE.bat v8_knee_anatomy knee` passed against runtime `614033b` / frozen `hgpt_canonical_v3`: five focused guards, all seven 26-frame exercise comparisons, and knee audit. V8's 28 saved poses have 0 mm paired medial-seam gap. The matched V7/V8 deepest-squat front, side and three-quarter comparison is `renders_v8_knee_anatomy/V8_V7_DEEPEST_SQUAT_KNEE_COMPARISON.jpg`; see `REVIEW_V8_KNEE_ANATOMY.md`. V8 awaits the user's visual review. No hand geometry, production promotion or frozen-source change was made.

## V8 knee geometry accepted — 2026-09-23

The user reviewed the matched V7/V8 deepest-squat renders and accepted V8 as the knee geometry baseline, retaining V7's topology. V7 and V8 remain separate preserved candidate assets; neither is promoted to production. The baseline manifest now points new candidate work at V8 while retaining the V6 historical baseline and the frozen `hgpt_canonical_v3` / runtime `614033b` references. Phase B hand anatomy may proceed from V8; grip refit remains held until after hand visual review.

## 2026-09-23 — V8 acceptance and Phase B V9 hand review

V8 is recorded as the accepted knee geometry checkpoint; V7 and V8 remain
preserved and unpromoted. The current hand review candidate derives exactly
from V8: HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v9_hand_geometry_review
(dressed, bare and editable Blend).

The first hand-only added-vertex smoothing pass introduced dark seams and was
rejected. A no-smoothing pass avoided seams but had little visible effect.
The reviewed pass adjusts both eligible original and added hand surface
vertices, leaving 682 protected floor vertices and all non-hand vertices
unchanged. A later smoothing trial again showed wrist slits and was rejected.

The reviewed V9 passes structural, five focused runtime guards, seven exercise
comparisons over 26 frames each, strict floor-contact guard, bare/dressed
equivalence and V8 binary scope verification. Bone and equipment matrices
match exactly. The matched hand closeups show a modest shape change, while
inherited polygonal finger tips, thumb/web and wrist bands remain. The user
must visually review it before any grip refit; hand anatomy is not yet
accepted. No production, rig, UV, weight, exercise or grip files changed.\n

## 2026-09-24 — V11 hand cleanup built (Claude, cloud, Blender 5.2.1)

Built from V10 in a cloud session with Blender 5.2.1 LTS running headless (`bpy`), the laptop's version. `scripts/run_v11_pipeline.sh` rebuilds and re-validates it end to end.

**Before building, the V10 defects were measured** (`scripts/audit_hand_seams.py`):

- V8's hand is unwelded skin patches, and V10 opened those seams into 0.5–4 mm cracks. They are the thumb-web seam and the wrist slits, and also V9's rejected smoothing seams.
- The four finger tips are open holes.
- V10's finger sculpt made the ring banding.
- V10's thenar and web fields, pushed along normals that differ across a seam, made the web wedge.

**V11**:

- returns the hand to V8's shape on V10's topology;
- caps the fingertips;
- smooths the hand without shrinking it, keeping the 682 protected vertices fixed;
- relaxes folds;
- closes every seam onto its partner edge or face;
- gives each closed seam vertex matching weights;
- has the packer share normals across closed seams.

**Left-hand results:**

- Seam cracks of 0.05–1.5 mm: 94 in V8, 331 in V10, 0 in V11.
- Fingertip hole edges: 32 in V8, 41 in V10, 0 in V11.
- Folds over 100°: 10 in V8, 104 in V10, 4 in V11.

**Validation.** Quick check, strict floor guard, five focused guards and seven exercises over 26 frames all pass against `614033b`. Bone and equipment matrices match exactly. The largest original-hand difference from V8 is 3.638 mm (V10: 5.674 mm), inside the default 4 mm envelope.

Visual review is pending (`REVIEW_V11_HAND_CLEANUP.md`). There was no grip refit and no rig, exercise, equipment or production change.
