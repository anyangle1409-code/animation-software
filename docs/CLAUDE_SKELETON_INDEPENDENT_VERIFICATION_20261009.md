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
