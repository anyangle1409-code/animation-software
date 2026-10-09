# Claude independent skeleton verification — 9 October 2026

Branch `claude/skeleton-independent-verification-20261009`, created from Work's verified head `42943652` (which contains the whole-body audit branch at `2d4b352`). Work's branches, PR #8 (draft, unmerged), a003, c001–c004, production assets and all existing evidence are unchanged. No c005. Nothing here is anatomical acceptance.

**Environment:** Blender 5.2.1 runs as a Python module here. Literature hosts (PubMed/PMC, J-STAGE, DOI, Crossref, Europe PMC, Zenodo, figshare and others) are **unreachable** from this session's network; only GitHub and package indexes are reachable. Primary-paper evidence therefore cannot be added from this session. Open musculoskeletal models on GitHub can be read, but each counts as **one** source.

## Stage 1 — independent review of Work's 9 commits (`audit/claude_independent_review_20261009/stage1_work_review.json`)

- **Full suite reproduced exactly:** 1,031 tests, 1,022 pass, 5 failures + 4 errors. The names are identical to Work's and to the earlier baseline (old production-control/orchestration expectations).
- **Fresh skeleton-only Blender rehearsal:**
  - All 6 manifest files verify (raw and gzip sha256).
  - All 135 isolated-test sample sets are **byte-identical** to Claude's independent c004 run, which used the c003 blend with the a003 body mesh present; Work's run used an empty scene. So the body mesh has no influence on skeletal motion, and Work's Blender execution is independently reproduced.
- **Hand points:** 108 / 98 exact / 10 unresolved, identical to Claude's own source-rebuild audit.
- **Unsupported peaks:** 78 peaks in 49 tests, identical to Claude's amplitude-provenance audit.
- **Evidence integrity:** 1,094 hash references, 1,007 OK; no new non-OK entry from Work.
- **Review notes:**
  - The constructor accepting improper or skewed joint frames without raising is **not a defect**: CP2 `joint_frames_proper` flags both, and strict mode rejects any CP2 failure (mutation-verified).
  - Fifteen Work evidence files are named only through their directory (traceability note).
  - Strict mode is intentionally fail-closed: `coverage_complete` is hard-coded False until a contact/envelope checker exists.

## Stage 2 — wrist/hand source context from a published open model (`audit/claude_independent_review_20261009/wrist_hand_model_context_v1.json`)

**Source:** OpenSim wrist model, Gonzalez, Buchanan & Delp, *J Biomech* 30:705–712 (1997). It is read from `opensim-org/opensim-models` at commit `d9b05d47`, with the model sha256 and every mesh's sha256 recorded. A new read-only OpenSim/VTP evaluator, `scripts/anatomy_fit/opensim_model_geometry.py`, produces the default-pose geometry: all 8 carpals, 5 metacarpals and every phalanx (one mesh each).

| Finding | Result |
|---|---|
| Model bone lengths vs registered male radiographic means (Aydinlioglu 1998, 19 bones) | Ratio **1.12–1.43** (mean 1.24, SD 0.07). The radius is not enlarged (235 mm), so the hand is not at a population scale. **The model is not a dimensional source**: no length or coordinate is adopted from it. |
| Scale-free digit proportions | Distal/proximal phalanx: index 0.435 vs 0.439; ring 0.443 vs 0.442; middle 0.438 vs 0.413; little 0.443 vs 0.500; thumb 0.769 vs 0.742. Broad agreement except the little finger; descriptive only. |
| Carpal topology (9 standard relations: proximal row scaphoid → lunate → triquetrum radial-to-ulnar; distal row trapezium → trapezoid → capitate → hamate; distal row distal to proximal; pisiform palmar to triquetrum) | **All hold on the model and on a003, both sides.** a003's palmar direction is derived from its committed digit-3 flexion sweep, not assumed (a first draft with an assumed handedness inverted it). |
| Index-ray model geometry | MCP→PIP 48.9 mm, PIP→DIP 33.2 mm, DIP centre → bony tip **23.6 mm** = distal-phalanx extent 21.3 mm + 2.3 mm from the DIP centre to the phalanx base |

**Fingertip tails (10): still UNRESOLVED.** The model supplies one DIP-centre-to-bony-tip geometry, for the index finger only, from a decimated mesh at non-population scale. The project rule needs two compatible independent sources plus a frame derivation. The exact remaining requirement:
- an independent source giving either DIP-centre-to-bony-tip distances, or distal-phalanx length together with the DIP-centre-to-base offset, for all five rays;
- in an adult male population compatible with 1.82 m stature;
- with endpoint definitions matching the joint centre used by HGPT.

Hamilton & Dunsmuir 2002 (joint rotation centres to fingertip) is the closest candidate, but its full text is restricted and unreachable here. The old containment offsets are not used as evidence.

**Carpal layout:** topology is corroborated only; no centroid is adopted. The readiness blockers (8 centroids in one canonical wrist frame, contact layout) stand.

**Tests:** `scripts/test_wrist_hand_model_context.py` (5): pinned findings; a live re-run when the external clone is present; topology mutations (pisiform moved dorsal, lunate/triquetrum swapped); a synthetic compressed-VTP round trip; the rotation convention.

## Owner-requested full anatomical investigation (9 October, Claude)

**Method.** Every visual impression was turned into a measurable claim and checked against the coordinates and the committed evidence. It was then classified as one of:
- a genuine **geometry** defect;
- a **joint/coordinate** defect;
- a hard **structural invariant** failure;
- a **movement-test design** defect;
- a missing **movement model**;
- a **representation limit** of the stick diagnostic;
- an **evidence gap**;
- **not a defect**.

The owner's three screenshots did not reach this session; the same views were regenerated as real Blender renders. Literature hosts are still unreachable from this cloud session, so no new primary paper could be read. Everything uses the project's committed source records plus one open published model.

**Tools added (all read-only on accepted assets):**
- `bone_by_bone_audit.py` → `bone_by_bone_audit_v1.json`: all 206 bones on a003 and c004 — region, parent articulation, length, direction, what the stick represents, joint-centre distances, mirror, sourced corridors.
- `skeleton_defect_register.py` → `skeleton_defect_register_v1.json`: 30 classified entries with numbers computed live.
- `whole_body_interaction_scan.py` → `whole_body_interaction_{a003,c004}.json`.
- `render_skeleton_annotated.py`: annotated renders with axes, a 100 mm scale bar, joint labels, white/grey bone-end dots and an automatic camera check (a red probe at a known world point is located in the image and compared with its analytic projection).
- `build_proposal_p001_metacarpals.py`: diagnostic proposal P001.
- Readiness addendum: `readiness_review_addendum_20261009.json` (no status change: 0 READY / 9 PARTIAL / 3 BLOCKED).

### What is genuinely wrong (and what was done)

| ID | Finding | Class | Status |
|---|---|---|---|
| U1 | a003 clavicles 222.9 mm and AC breadth 481 mm (male endpoint range 130–175 mm) | geometry | Corrected in candidate c003/c004 (151.3 mm; 338 mm, inside the feasible 333–353 mm family); non-canonical |
| U2 | a003 scapula transverse span 227 mm (male 3D-CT 113 ± 6.6 mm) | geometry | Corrected in c003/c004 (129 mm, rebuilt from the Lee 29-landmark male scapula); exact 3D target open |
| H1 | Metacarpals 2–4 short: 58.4 / 54.0 / 51.6 mm, z −2.4 / −2.5 / −1.6; two independent male sources agree (68 / 64 / 58 and 67.7 / 66.1 / 58.0 mm) | geometry | **Diagnostic proposal P001** (see below); canonical freeze waits for carpal/CMC geometry |
| U7 | Radius short for stature (ANSUR direct regression, z −2.85) | geometry | Blocked: endpoint-compatible second source needed |
| U5 | Zero disc space at every disc-bearing level (CP2 FAIL) | structural invariant | Blocked: full sagittal stack rebuild. The C3–L5 sticks sum to 625.6 mm vs 536.0 mm sourced bodies + discs. The current thoracic span agrees with the CT source (343.9 mm, +3.4%) and not the mixed-sex donor source (268.8 mm, −19%). Lumbar sticks absorb their discs. A local re-partition would move C7/T1 by about 40 mm and cascade into the ribs and sternum, so it was not applied |
| H3 | Thumb CMC: the trapezium stick ends 10.6 mm short of the first-metacarpal base | joint/coordinate | Blocked (carpal geometry) |
| L5 | Calcaneocuboid and talonavicular joint centres float 33.5 and 38.3 mm from their bones. The calcaneus control stick runs posteriorly, so its anterior process is absent | joint/coordinate | Blocked (tarsus); also explains the 37 mm midfoot split |
| H7 | c001–c003 wrist sweeps pivoted 38.4 mm off the radiocarpal joint (opening it 16.7 mm) | joint/coordinate | Corrected in c004 |

### What is a movement-test problem, not a bone problem

| ID | Finding |
|---|---|
| H6 | With c004's realistic (narrower) shoulders, a003's hanging-arm posture was kept. Isolated forearm rotation, elbow flexion at 60° pronation, GH rotation and wrist flexion then sweep the hand to within 1.5–6.9 mm of the femoral axis. a003 has none of these, because its over-wide shoulders kept the hands clear |
| L4 | Hip adduction 20° (unsourced) makes the tibiae cross |
| L7 | Hip internal rotation brings the hallux onto the opposite foot |
| L3 | The patella stays fixed during plain knee flexion; the follower exists only in its own test |
| U3, H8, H9 | Clavicle does not elevate with the arm (SC elevation not applied); midcarpal followers separate 2.7–3.9 mm in two-stage wrist sweeps; thumb opposition only partial |

### What only looks wrong because of the stick diagnostic

| ID | Appearance | Reality |
|---|---|---|
| U4 | Straight "feather" ribs | Two-point chords of curved bones. Rib curvature *is* a genuine model deficiency for rib kinematics (blocked), but straightness in the picture is not a coordinate error |
| L1 | Femoral heads floating 71 mm from the pelvis | The os coxae stick is the SI-to-pubic chord; the hip centre coincides with the femoral head (0.0 mm) and is an independently corroborated anchor |
| S1, S2 | Skull and face as scattered sticks; mandible through the mouth | Schematic placement sticks (grade D) and a U-shaped bone's chord |
| H5 | Carpus as a clump of stubs | Control sticks, not whole-bone lengths |
| — | Tibiofibular, talocrural and costotransverse joints off the sticks | Bone axes lie 16–33 mm from the joint centre where the bone surfaces actually touch |

### Checked and not a defect

- **H4 carpal topology:** all 9 standard relations hold, on the model and on both a003 sides.
- **L2 knee and ankle centres:** exactly shared (0.0 mm).
- **G1 symmetry:** within 0.29 mm.
- **L6 long foot:** that is the r95 surface; metatarsals are source-conflicted.
- **G2 hand outside the a003 skin:** the mesh must refit to the skeleton.

**Evidence gap (not decided either way):** U9, the medial clavicle 7.5 mm from rib 1 in c004 (a003: 16.4 mm), is in the costoclavicular region and needs surface geometry.

### P001 — metacarpals 2–4 (diagnostic proposal, not a candidate)

- **Change:** M2–M4 lengthened to 68 / 64 / 58 mm with fixed CMC ends and unchanged axes; digit chains translate 6.4–9.9 mm. Everything else is byte-identical to c004 (test-enforced).
- **Checks:** fresh empty-scene Blender build with round-trip PASS. 135/135 sweeps; 109 sample sets byte-identical to c004, 26 hand/thumb/wrist tests changed. Solver AGREE; mirror, continuity, joint-frame and attachment-v2 checks all clean; amplitudes TRACED.
- **Hand length:** bony wrist-to-middle-fingertip 186.5 → 196.4 mm (ANSUR surface hand length at 1.82 m: 199.5 mm; descriptive).
- **Renders:** before/after in [`proposals/p001_metacarpal_m2_m4/before_after`](https://github.com/anyangle1409-code/animation-software/blob/claude/skeleton-independent-verification-20261009/ORIGINAL_V1_WORK/anatomy/audit/proposals/p001_metacarpal_m2_m4/before_after).

### Renders (real Blender 5.2.1 output)

- First pass, 28 views including 8 movement extremes: [`skeleton_only_renders_c004`](https://github.com/anyangle1409-code/animation-software/blob/claude/skeleton-independent-verification-20261009/ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/skeleton_only_renders_c004)
- Annotated pass (axes, scale bar, labels, camera check): [`annotated_renders_c004`](https://github.com/anyangle1409-code/animation-software/blob/claude/skeleton-independent-verification-20261009/ORIGINAL_V1_WORK/anatomy/audit/claude_independent_review_20261009/annotated_renders_c004)
