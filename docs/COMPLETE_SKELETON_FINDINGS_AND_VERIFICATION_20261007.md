# Complete skeleton findings and verification — 7 October 2026

Branch: `codex/whole-body-biomechanics-audit-20261007`. Baseline: `a75926c8a2d9329a25af224f338cdfe3ed21beb2`. Production model and drivers preserved.

Phases 0–5 are accepted for isolation, reference inventories, semantic frames, evidence compilation and static comparison. **The character skeleton is not finally accepted. Phase 6 needs the local HomeGymPT_Male_ORIGINAL_v1 Blender character.** No anatomy is LOCKED, no source statistic is a production limit, and no runtime grouping is approved.

## What “verified” means here

Inventory verification checks anatomical coverage, identity, classification, source bindings and exceptions. Frame verification checks semantic landmark recipes and frame mathematics, without fitted coordinates. Evidence verification checks the source actually accessed, study context, measurement scope and mode. Static gap verification checks exported bone names, existing aliases, driver functions and input hashes. These checks do not prove live joint-centre accuracy, contact trajectories, deformation or performance.

## Programme-wide findings

| Finding | Evidence and verification | Result / required action |
|---|---|---|
| Conventional adult skeleton | Existing inventory, 206 unique IDs, 80 axial/126 appendicular; bilateral pairing checks | Count verified; retain naming and fit every reference. |
| Articulations | 427 named contact/articulation complexes in 24 families; two or more source references each; all 206 bones accounted for | Reference coverage passes; 427 is this atlas’s contact convention, not a universal textbook joint count. |
| Hyoid | Explicit no-osseous-articulation exception; greater/lesser horn interfaces recorded as variants | Do not invent a neck hinge or add horn components to the conventional 206 count. |
| Fusion variants | Sacrum/hip/coccyx conventional counting retained; variable coccygeal and hyoid interfaces separate | Choose the actual character’s variant in Blender; no universal fusion assumption. |
| Anatomy exceptions | No C1/C2 disc; ribs11/12 lack costotransverse joints; ulna does not directly articulate with radiocarpal proximal row; scapulothoracic is functional | Tests protect these exclusions; preserve TFCC and cartilage/contact distinctions. |
| Frame atlas | 30 sourced frame recipes; 206 bone assignments and 427 joint assignments; determinant/degeneracy tests | Semantic definitions verified; orientation adapter and numerical fitting unaccepted. |
| Movement atlas | 44 profiles and 62 contextual observations; 86 programme source entries; multiple independent works per profile | Reference evidence compiled; missing transferable numerical limits remain explicit qualitative classifications. |
| Current rig | 67 canonical controls including helpers; source-pinned comparison covers 206 bones/427 joints/44 profiles | Aggregate control count is not an anatomical bone count; extra reference anatomy does not imply 206 runtime deform bones. |
| Production protection | Git diff scoped to reference anatomy, validators, audit builder and documentation; pinned canonical/driver hashes | No production geometry, weights, poses or driver changes. |

## Regional findings: real anatomy, current rig, required change

Each row links to a mechanics profile in `whole_body_movement_atlas.json`. That profile supplies axes, command DOF, coupling, translations/COR, posture/load and plane dependence, evidence availability, test cases and acceptance criteria. The machine-readable gap matrix has an individual row for every bone and articulation.

| Profile | Current rig / verified scope | Required change | Verification / sources |
|---|---|---|---|
| `fixed` — Adult exercise-fixed references | Grouped/absent anatomical reference structures; `reference_grouping_review` | Represent all fixed references in master; choose fusion variants; rigid runtime grouping requires later comparison. | Pinned canonical/aliases/driver inspection; source IDs OS_FIBROUS, OS_CARTILAGE, SP_SKULL, SP_CARPAL, SP_PELVIS, SP_FOOT. Character unverified. |
| `tmj` — Bilateral TMJ | No explicit mandible or TMJ controls; `absent_explicit_structure` | Separate mandible with bilateral constrained condylar/disc contact and glide. | Pinned canonical/aliases/driver inspection; source IDs TMJ_EM, TMJ_OPTICAL, OS_SELECTED. Character unverified. |
| `c0_c1` — Occiput–atlas | One neck plus head; `collapsed_segments` | Separate skull/atlas/axis and resolve paired condyle contact. | Pinned canonical/aliases/driver inspection; source IDs CERVICAL_NORMAL, CERVICAL_REVIEW, SP_CERVICAL. Character unverified. |
| `c1_c2` — Atlas–axis | One neck plus head; `collapsed_segments` | Separate atlas/axis, dens and lateral facets sharing a level transform. | Pinned canonical/aliases/driver inspection; source IDs CERVICAL_NORMAL, CERVICAL_REVIEW, SP_CERVICAL, C1C2_MRI. Character unverified. |
| `cervical` — Subaxial cervical motion segment | One neck plus head; `collapsed_segments` | Represent C2–C7 individually and cervicothoracic transition. | Pinned canonical/aliases/driver inspection; source IDs CERVICAL_NORMAL, CERVICAL_REVIEW, UNCOVERTEBRAL. Character unverified. |
| `thoracic` — Thoracic motion segment | Three aggregate spine segments for torso; `collapsed_segments` | Represent T1–T12 with disc/facet level transforms and rib attachments. | Pinned canonical/aliases/driver inspection; source IDs THORACIC_CADAVER, THORACIC_LB, ISB_I. Character unverified. |
| `lumbar` — Lumbar motion segment including L5/S1 | Three aggregate spine segments for torso; `collapsed_segments` | Represent L1–L5/sacrum and level-dependent sagittal contribution. | Pinned canonical/aliases/driver inspection; source IDs LUMBAR_REVIEW, LUMBAR_QF, ISB_I, LUMBAR_LIFT. Character unverified. |
| `ribs` — Rib posterior contacts | No individual rib controls; `absent_explicit_structure` | Posterior rib contacts, rib-specific follower trajectories and cartilage compliance. | Pinned canonical/aliases/driver inspection; source IDs RIB_GEOMETRY, RIB_4D, RIB_LIGAMENTS. Character unverified. |
| `anterior_thorax` — Anterior thoracic follower system | No explicit sternum/cartilage mechanics; `absent_explicit_structure` | Anterior thoracic follower system; preserve fusion/first-rib exceptions. | Pinned canonical/aliases/driver inspection; source IDs ANTERIOR_THORAX, STERNOCOSTAL_CADAVER, RIB_4D. Character unverified. |
| `si` — SI anterior/posterior system | Single pelvis segment; `collapsed_segments` | Separate sacrum and bilateral hip bones; constrained SI/pubic ring compliance. | Pinned canonical/aliases/driver inspection; source IDs SI_HEALTHY, SI_REVIEW, SP_PELVIS. Character unverified. |
| `pubis` — Pubic symphysis | Single pelvis segment; `collapsed_segments` | Reference symphysis and pelvic-ring follower compliance. | Pinned canonical/aliases/driver inspection; source IDs SP_PELVIS, PELVIC_ANATOMY. Character unverified. |
| `coccyx` — Sacrococcygeal/intercoccygeal variant | No explicit coccygeal components; `absent_explicit_structure` | Reference coccyx; choose component/fusion variant before follower fitting. | Pinned canonical/aliases/driver inspection; source IDs COCCYX_CT, COCCYX_MRI. Character unverified. |
| `sc` — Sternoclavicular | Clavicle control; generic elevation driver; `mechanics_gap` | SC three-dimensional elevation/retraction/roll with separate sternum centre. | Pinned canonical/aliases/driver inspection; source IDs SC_ELEVATION, SHOULDER_PINS, ISB_II. Character unverified. |
| `ac` — Acromioclavicular | Scapula/clavicle present; r97 pivot coincides with GH; `verified_static_gap` | Fit distinct AC and GH centres; relative scapula/clavicle rotations. | Pinned canonical/aliases/driver inspection; source IDs SHOULDER_PINS, SP_SHOULDER, ISB_II. Character unverified. |
| `st` — Scapulothoracic functional articulation | Scapula present; generic upward-rotation rule; `mechanics_gap` | Thorax-relative upward rotation, tilt and axial rotation; surface follower. | Pinned canonical/aliases/driver inspection; source IDs SHOULDER_PINS, SP_SHOULDER, ISB_II. Character unverified. |
| `gh` — Glenohumeral | Upperarm present; generic elevation/ER rule; `mechanics_gap` | Plane-dependent GH rotation and glenoid-relative translation; distinct GH centre. | Pinned canonical/aliases/driver inspection; source IDs SHOULDER_PINS, GH_DYNAMIC, SP_SHOULDER, ISB_II. Character unverified. |
| `elbow` — Humeroulnar/radiocapitellar elbow | Upperarm/forearm present; radius/ulna grouped; `present_requires_dynamic_validation` | Separate humeroulnar/radiocapitellar references; fit carrying angle and centre. | Pinned canonical/aliases/driver inspection; source IDs ELBOW_ANATOMY, ISB_II, SOUCIE_ROM. Character unverified. |
| `radioulnar` — Proximal/distal radioulnar coupled rotation | One forearm plus twist helpers; `collapsed_segments` | Separate radius/ulna and constrained PRUJ/DRUJ rotation; helper twist is not osseous articulation. | Pinned canonical/aliases/driver inspection; source IDs FOREARM_DYNAMIC, FOREARM_BIPLANE, ISB_II, SOUCIE_ROM, SP_PRUJ, SP_DRUJ, DRUJ_FUNCTIONAL. Character unverified. |
| `ru_iom` — Radioulnar interosseous membrane | Radius/ulna grouped; `collapsed_segments` | Forearm interosseous membrane follower constraint. | Pinned canonical/aliases/driver inspection; source IDs OS_FIBROUS, FOREARM_DYNAMIC. Character unverified. |
| `radiocarpal` — Radiocarpal stage | One hand for gross wrist; `collapsed_segments` | Separate radiocarpal and midcarpal stages; no ulna–carpal osseous contact. | Pinned canonical/aliases/driver inspection; source IDs WRIST_RC, WRIST_MC, ISB_II. Character unverified. |
| `carpal` — Intercarpal/midcarpal contact | No explicit eight carpal bones; metacarpals excluded from count; `absent_explicit_structure` | Individual carpal references and shared contact/row mechanics. | Pinned canonical/aliases/driver inspection; source IDs WRIST_RC, WRIST_MC, SP_CARPAL. Character unverified. |
| `pisiform` — Pisotriquetral follower | No explicit pisiform; `absent_explicit_structure` | Pisotriquetral/FCU follower reference. | Pinned canonical/aliases/driver inspection; source IDs SP_CARPAL, GRAY_WRIST. Character unverified. |
| `thumb_cmc` — Thumb saddle CMC | Three thumb segments; parallel hinge recipe; `verified_static_gap` | Saddle CMC axes and coupled opposition roll; distinguish metacarpal from phalanges. | Pinned canonical/aliases/driver inspection; source IDs THUMB_OPPOSITION, THUMB_BASE_CT, THUMB_ROM, ISB_II. Character unverified. |
| `thumb_mcp` — Thumb MCP | Thumb segment present; common-axis recipe; `mechanics_gap` | Anatomical MCP axis and task-dependent CMC/MCP/IP coordination. | Pinned canonical/aliases/driver inspection; source IDs THUMB_OPPOSITION, THUMB_ROM, ISB_II. Character unverified. |
| `thumb_ip` — Thumb IP | Thumb segment present; common-axis recipe; `mechanics_gap` | Anatomical IP hinge and independent measured coordination. | Pinned canonical/aliases/driver inspection; source IDs THUMB_OPPOSITION, THUMB_ROM, ISB_II. Character unverified. |
| `metacarpal` — Long-finger CMC/intermetacarpal cupping | Four long metacarpals per hand; `present_requires_dynamic_validation` | Fit CMC/intermetacarpal cupping; preserve ray differences. | Pinned canonical/aliases/driver inspection; source IDs SP_CARPAL, GRAY_WRIST, ISB_II. Character unverified. |
| `mcp` — Long-finger MCP | Long-finger chains present; uniform70deg recipe; `verified_static_gap` | Digit-specific MCP flexion/spread and wrist/posture-dependent coupling. | Pinned canonical/aliases/driver inspection; source IDs FINGER_ACTIVE, FINGER_GRIP, FINGER_WRIST, ISB_II. Character unverified. |
| `pip` — Long-finger PIP | Long-finger chains present; uniform88deg recipe; `verified_static_gap` | Digit-specific PIP hinge and grip/release trajectory. | Pinned canonical/aliases/driver inspection; source IDs FINGER_ACTIVE, FINGER_GRIP, FINGER_WRIST, ISB_II. Character unverified. |
| `dip` — Long-finger DIP | Long-finger chains present; uniform55deg recipe; `verified_static_gap` | Digit-specific DIP hinge and tendon/task coupling. | Pinned canonical/aliases/driver inspection; source IDs FINGER_ACTIVE, FINGER_GRIP, FINGER_WRIST, ISB_II. Character unverified. |
| `hip` — Femoroacetabular hip | Pelvis/thigh present; centres not anatomically fitted; `present_requires_dynamic_validation` | Fit femoral head/acetabulum and posture-dependent three-axis rotation. | Pinned canonical/aliases/driver inspection; source IDs HIP_POSITION, HIP_ACTIVE, ISB_I, SOUCIE_ROM. Character unverified. |
| `knee` — Tibiofemoral | Thigh/shin present; no anatomical contact solver verified; `present_requires_dynamic_validation` | Condyle/tibial contact, rolling/sliding, screw-home and load/path dependence. | Pinned canonical/aliases/driver inspection; source IDs KNEE_SHM, SP_KNEE, SOUCIE_ROM. Character unverified. |
| `patella` — Patellofemoral | No explicit patella; `absent_explicit_structure` | Patellar follower track and trochlear/contact geometry. | Pinned canonical/aliases/driver inspection; source IDs PF_LUNGE, PF_DYNAMIC, SP_PATELLA. Character unverified. |
| `ptf` — Proximal tibiofibular | One shin groups tibia/fibula; `collapsed_segments` | Separate proximal tibiofibular follower reference. | Pinned canonical/aliases/driver inspection; source IDs PTF_MOTION, PTF_ANATOMY, PTF_CADAVER. Character unverified. |
| `dtf` — Distal tibiofibular syndesmosis | One shin groups tibia/fibula; `collapsed_segments` | Distal syndesmosis compliance driven by ankle motion. | Pinned canonical/aliases/driver inspection; source IDs DISTAL_TF, DART_FOOT, OS_FIBROUS. Character unverified. |
| `tf_iom` — Tibiofibular interosseous membrane | One shin groups tibia/fibula; `collapsed_segments` | Interosseous membrane constraint between tibia/fibula. | Pinned canonical/aliases/driver inspection; source IDs OS_FIBROUS, PTF_MOTION. Character unverified. |
| `ankle` — Talocrural | One foot at shin; `collapsed_segments` | Talus/tibia/fibula talocrural contact and fitted oblique axis. | Pinned canonical/aliases/driver inspection; source IDs ANKLE_WB, ANKLE_GEOMETRY, DART_FOOT. Character unverified. |
| `subtalar` — Posterior subtalar | One foot; no separate talus/calcaneus; `collapsed_segments` | Independent anatomical hindfoot reference and coupled inversion/rotation. | Pinned canonical/aliases/driver inspection; source IDs ANKLE_WB, ANKLE_GEOMETRY, FOOT_REVIEW. Character unverified. |
| `tcn` — Talocalcaneonavicular compound follower | One foot; no separate talonavicular stage; `collapsed_segments` | Talocalcaneonavicular complex constrained with hindfoot/midfoot. | Pinned canonical/aliases/driver inspection; source IDs FOOT_PINS, FOOT_REVIEW, DART_FOOT. Character unverified. |
| `midfoot` — Midtarsal/intertarsal follower contacts | One foot segment; `collapsed_segments` | Individual tarsals; deformable load-dependent midfoot, no universal locking assumption. | Pinned canonical/aliases/driver inspection; source IDs FOOT_PINS, FOOT_REVIEW, DART_FOOT. Character unverified. |
| `tmt` — Tarsometatarsal/intermetatarsal | No separate metatarsal rays; `collapsed_segments` | Ray-dependent tarsometatarsal/intermetatarsal follower mechanics. | Pinned canonical/aliases/driver inspection; source IDs FOOT_PINS, FOOT_REVIEW, DART_FOOT. Character unverified. |
| `hallux` — First MTP | One toe segment groups all toes; `collapsed_segments` | Separate hallux MTP; weightbearing task and passive measurements kept distinct. | Pinned canonical/aliases/driver inspection; source IDs HALLUX_GAIT, HALLUX_REVIEW, DART_FOOT. Character unverified. |
| `lesser_mtp` — Lesser-toe MTP | One toe segment groups all toes; `collapsed_segments` | Four lesser-toe rays with individual MTP flexion/spread. | Pinned canonical/aliases/driver inspection; source IDs DART_FOOT, SP_FOOT, OS_SELECTED. Character unverified. |
| `toe_ip` — Hallux IP / lesser PIP-DIP | One toe segment groups all toes; `collapsed_segments` | Hallux IP and lesser PIP/DIP separately represented. | Pinned canonical/aliases/driver inspection; source IDs DART_FOOT, SP_FOOT. Character unverified. |
| `sesamoid` — Hallux sesamoid tracking | No separate hallucal sesamoids; `absent_explicit_structure` | Two plantar sesamoid follower tracks per foot. | Pinned canonical/aliases/driver inspection; source IDs HALLUX_REVIEW, DART_FOOT. Character unverified. |

## Shoulder findings independently reproduced

| Static check | Finding | Verification |
|---|---|---|
| STRUCT_AC_GH_SEPARATION_L | r97 labels scapula head as AC joint; add_gh_helper labels upperarm head as glenohumeral centre. They become coincident. | `FAIL`; reproduced by `python scripts/check_shoulder_driver_preblender.py`; pinned source inputs. |
| STRUCT_AC_GH_SEPARATION_R | r97 labels scapula head as AC joint; add_gh_helper labels upperarm head as glenohumeral centre. They become coincident. | `FAIL`; reproduced by `python scripts/check_shoulder_driver_preblender.py`; pinned source inputs. |
| DRIVER_EXPLICIT_DOF_COVERAGE | Current girdle driver explicitly commands only clavicle elevation and scapular upward rotation. | `FAIL`; reproduced by `python scripts/check_shoulder_driver_preblender.py`; pinned source inputs. |
| PLANE_DEPENDENCY | At the same elevation the current girdle and straight-arm axial-rotation formulas return the same values for every elevation plane. | `FAIL`; reproduced by `python scripts/check_shoulder_driver_preblender.py`; pinned source inputs. |
| SCAPULAR_RULE_SMOOTHNESS | The piecewise rule is C0-continuous but not C1-continuous; the contribution rate jumps at interval boundaries. | `FAIL_FOR_PRODUCTION_SMOOTHNESS`; reproduced by `python scripts/check_shoulder_driver_preblender.py`; pinned source inputs. |
| R97_GH_HELPER_SEMANTICS | Confirms the project itself treats upperarm head as the GH centre, making the AC/GH collapse test meaningful. | `PASS_EVIDENCE`; reproduced by `python scripts/check_shoulder_driver_preblender.py`; pinned source inputs. |

AC-to-GH bind separation is 0.0mm on both sides; r97 moves the scapula pivot to clavicle tail and the GH helper uses upperarm head. This verifies coincidence in the named export/r97 construction, not the actual live character’s final centres. Generic clavicle elevation magnitude alone is insufficient to accept three-dimensional girdle motion. Existing static shoulder script reproduces its formula samples; the matrix also stores the actual driver function text for independent inspection.

## Measurement scope and numerical limits

| Evidence class | Verification / interpretation |
|---|---|
| CDC clinical ROM | Male20–44 means and 95%CI, passive mode from the companion study; CDC and Soucie are one independent work. CI describes a mean, not individual permissible ROM. Protocol positioning/sign unavailable. |
| Gross wrist, ankle and shoulder | Whole-complex statistics are stored separately; tests prohibit assigning humerothoracic flexion to GH. Wrist stage percentages and ankle/subtalar limits are not inferred. |
| C1/C2 | Primary MRI maximal-rotation sample replaces conflicting review prose. Segmental angles remain MRI-context observations, not neck limits. |
| Lumbar | Four distinct L2/L3–L5/S1 loaded lifting observations; no L1/L2 value inferred. Level-binding mutation test prohibits swapping L5/S1 into L2/L3. Lifting extension is not maximum flexibility or descent evidence. |
| Hip | Passive IR/ER recorded separately by side and sitting90deg versus prone neutral; active hip-position study independently supports context dependence. Do not average into one constant envelope. |
| Thumb | Six clinical measurements preserved with examination mode unspecified because accessible abstract does not resolve active/passive. Mutation test rejects mixing another joint into that collection. |
| Fingers | Named digit MCP/PIP/DIP table observations; published inconsistencies reduce quantitative confidence. No identical-finger acceptance bounds derived. |
| Hallux | Standing/gait/heel-rise task means separate; passive clinical ROM is not interchangeable with loaded functional dorsiflexion. |
| Small follower contacts | Numerical active/passive independent-contact maxima unavailable in reviewed evidence are recorded as qualitative availability, never zero. Shared contacts are not independent actuators. |

## Evidence issues retained

- `cervical_review_AR_typo` (CERVICAL_REVIEW): Maximal-ROM prose gives C1/C2 AR values inconsistent with its AR discussion and figure. Do not transcribe conflicting numbers; use primary segment study before selecting numerical curves. Effect: Conflicting review numbers excluded; three primary MRI observations retained instead. No fitted C1/C2 curve accepted.
- `finger_table_consistency` (FINGER_ACTIVE): National means not consistently between geographic-zone means; reliability prose inconsistent with claimed good ICC. Values retained as reported, reduced numerical confidence. Effect: Do not turn reported means/SD into anatomical acceptance limits.
- `cdc_protocol_missing` (CDC_ROM): Linked methods PDF returns404; posture/extension sign missing in accessed summary. Effect: Clinical descriptive statistics retained with context unavailable; no numeric solver acceptance.

Abstract-only sources cannot establish unreported full-method details. Such missing context is explicitly retained rather than reconstructed. Numerical envelopes, fitted curves and tolerance values require the later solver/character tests; the evidence gate does not waive them.

## Verification commands and results

```bash
python scripts/validate_complete_anatomical_atlas.py
python -m unittest discover -s scripts -p test_complete_anatomical_atlas.py
python scripts/check_shoulder_driver_preblender.py
python scripts/check_whole_body_driver_preblender.py
python -m unittest discover -s scripts -p "test_*.py"
```

Atlas tests currently pass 16/16. The validator reports zero inventory/frame/movement/gap errors. Its PASS is scoped to the reference gate, not a scientific endorsement of individual limits or Blender motion. Negative tests exercise omitted joints/bones/profiles, duplicate/unclassified anatomy, source loss, wrong side/fixed classifications, degenerate frames, mode/scope confusion, premature LOCKED claims, contact/follower actuator misuse, wrong digit/level and stale input hashes.

Whole-body and shoulder static checks intentionally report existing rig deficiencies; these are findings, not newly introduced test regressions. The legacy whole-body `carpal` substring matches `metacarpal`; the new matrix uses exact carpal names and correctly finds zero explicit carpal bones.

Full repository baseline has five failures and four errors in existing execution-orchestration/production-control/candidate-status tests. Those are documented in `ANATOMICAL_ATLAS_EVIDENCE_AND_LIMITATIONS_20261007.md`; unrelated production changes are outside this audit. Final post-review run: 550 tests in 34.671s; 541 passed, the same five failures and four errors as baseline. No additional failures. Exact test IDs and protected-input hashes are in `test_run_verification.json`.

## Fresh review and corrected findings

A fresh read-only reviewer checked the whole branch, reran the atlas tests and demonstrated two mutations that incorrectly passed before the fix. No critical findings; three important findings were corrected in one regression-test pass; no deferred minor findings.

| Review finding | Correction | Verification |
|---|---|---|
| Paired contacts could double commands; hindfoot functional command missing | 339 explicit command groups with exact members, one joint/control owner, command DOF and coupling references. TMJ/C0–C1 contacts share ownership; PRUJ/DRUJ share a forearm group; each hindfoot has a proposed inversion/eversion input while contacts remain followers. | Missing/split groups, doubled paired DOFs, missing hindfoot control and incorrect owner mutations reject; tests observed RED then GREEN. |
| Forearm citation count did not prove relevant support | PRUJ bindings use the selected-joints text plus dedicated PRUJ anatomy and conventions; DRUJ uses dedicated anatomy, functional anatomy and conventions. Shaft syndesmosis chapter retained for IOM. Forearm bindings explicitly state supported claim and locator. OpenStax chapters share one work ID. | Wrong synovial-to-shaft citation mutation and one-book/two-chapter mutation observed RED then GREEN; new sources read directly/indexed with access recorded. |
| Equal-DOF joints could receive another region's mechanics | Reviewed anatomical ID/family-to-profile compatibility contract independent of DOF values. | Hip→GH, GH→hip and thumb IP→finger PIP mutations observed RED then GREEN. |

The reviewer did not exhaustively endorse every source or numerical extraction; targeted review supplements the reference compilation and its context checks. It also did not evaluate local Blender geometry, motion, deformation or performance, which remain unaccepted. Unchanged baseline failures were outside the audit scope.

## Decisions and their practical cost

- Checked Phase1 inventory is authoritative over the stale tracker summary; it was revalidated. Cost if wrong: repeat inventory classification.
- Conventional 206 counting does not imply universal mechanical fusion; variable subcomponent interfaces are separate metadata. Cost if wrong: select/correct the actual character variant during fitting.
- Project orientation cannot be converted to anatomical axes without character measurements. Cost if wrong: resolve the adapter before building fitted transforms.
- Existing production-control/execution failures are retained because production must remain unchanged; a full-suite pass is not claimed. Cost: those pre-existing failures still require their own authorised repair before production release.
- Source compilation and targeted review do not substitute for exhaustive scientific endorsement or motion acceptance. Cost: source-method gaps and contradictory numerical evidence must be resolved if used for solver tolerances; each final movement still needs local validation.

## Local Blender acceptance checklist — next authorised work

1. Open the exact local character in an isolated audit copy; record file revision/hash. Measure orientation, proportions and selected fusion variants.
2. Fit all anatomical references and semantic landmarks; resolve anatomical-to-project coordinates from measurements.
3. Verify bilateral symmetry, segment lengths and distinct SC/AC/GH, wrist-stage, knee/patella and hindfoot centres. Store measured coordinates and results before checking Gate6.
4. Build HGPT_ANATOMICAL_MASTER with ACTIVE/FOLLOWER/FIXED/REFERENCE roles; validate hierarchy and every conventional bone before checking Gate7.
5. Implement source-context solvers and explicit tolerances; inspect both sides, intermediate/near-reference positions, raising/lowering, reversal, multi-plane motion, contact trajectories and continuity before checking Gates8/9.
6. Run every Phase10 functional task, including loaded grip/pinch, wrist support, calf raise and forefoot loading. Save bone-only views and machine-readable kinematics.
7. Derive runtime grouping only after quantitative master/runtime comparison passes; then address skin/deformation and export/performance in tracker order.

Execution probe: the r97/r98 candidate `.blend` files are present (5,234,876 / 5,201,002 bytes), but `shutil.which("blender")` returns `None`. Files alone do not verify the fitted character; this environment cannot execute the Phase6 Blender checks. The recorded probe is in `test_run_verification.json`.

Final acceptance requires the recorded local results. The deliverable here removes the need to reconstruct inventories or repeat the same static audit. New evidence, a changed character or failed motion tests can still require targeted revision.

## Source register and access verification

Every articulation retains anatomy source IDs; every mechanics profile retains independent movement/convention sources. Access labels describe what was actually available, not promised full-text access.

| ID | Work / URL | Access / locator |
|---|---|---|
| `OS_SKULL` | [OpenStax: The Skull](https://openstax.org/books/anatomy-and-physiology-2e/pages/7-2-the-skull) | full_text — Structure and function / articulations |
| `OS_FIBROUS` | [OpenStax: Fibrous Joints](https://openstax.org/books/anatomy-and-physiology-2e/pages/9-2-fibrous-joints) | full_text — Structure and function / articulations |
| `OS_CARTILAGE` | [OpenStax: Cartilaginous Joints](https://openstax.org/books/anatomy-and-physiology-2e/pages/9-3-cartilaginous-joints) | full_text — Structure and function / articulations |
| `OS_SELECTED` | [OpenStax: Anatomy of Selected Synovial Joints](https://openstax.org/books/anatomy-and-physiology-2e/pages/9-6-anatomy-of-selected-synovial-joints) | full_text — Structure and function / articulations |
| `SP_SKULL` | [StatPearls: Skull](https://www.ncbi.nlm.nih.gov/sites/books/NBK499864/) | full_text — Structure and function / articulations |
| `SP_CARPAL` | [StatPearls: Hand Carpal Bones](https://www.ncbi.nlm.nih.gov/sites/books/NBK535382/) | full_text — Structure and function / articulations |
| `SP_PELVIS` | [StatPearls: Pelvic Joints](https://www.ncbi.nlm.nih.gov/sites/books/NBK538523/) | full_text — Structure and function / articulations |
| `SP_THORACIC` | [StatPearls: Thoracic Vertebrae](https://www.ncbi.nlm.nih.gov/sites/books/NBK459153/) | full_text — Structure and function / articulations |
| `SP_FOOT` | [StatPearls: Foot Joints](https://www.ncbi.nlm.nih.gov/sites/books/NBK536941/) | full_text — Structure and function / articulations |
| `SP_OSSICLE` | [StatPearls: Ossicular-Chain Dislocation](https://www.ncbi.nlm.nih.gov/sites/books/NBK560621/) | full_text — Structure and function / articulations |
| `SP_SC` | [StatPearls: Sternoclavicular Joint](https://www.ncbi.nlm.nih.gov/sites/books/NBK537258/) | full_text — Structure and function / articulations |
| `SP_CERVICAL` | [StatPearls: Cervical Vertebrae](https://www.ncbi.nlm.nih.gov/sites/books/NBK459200/) | full_text — Structure and function / articulations |
| `DART_FOOT` | [Dartmouth: O'Rahilly Basic Human Anatomy, chapter 17](https://humananatomy.host.dartmouth.edu/BHA/public_html/part_3/chapter_17.html) | full_text — Structure and function / articulations |
| `GRAY_WRIST` | [Gray's Anatomy: wrist and hand](https://elsevier-elibrary.com/contents/fullcontent/58750/epubcontent_v2/OEBPS/B9780443066849500585.htm) | indexed_excerpt — Structure and function / articulations |
| `GRAY_HEAD` | [Gray's Anatomy for Students: head](https://elsevier-elibrary.com/contents/fullcontent/58090/epubcontent_v2/OEBPS/B9780443069529000138.htm) | indexed_excerpt — Structure and function / articulations |
| `ISB_I` | [Wu et al. 2002: ISB joint coordinate systems, ankle, hip, spine](https://pubmed.ncbi.nlm.nih.gov/11934426/) | full_text — Sections 3-5; ISB-hosted PDF |
| `ISB_II` | [Wu et al. 2005: ISB joint coordinate systems, shoulder, elbow, wrist, hand](https://pubmed.ncbi.nlm.nih.gov/15844264/) | full_text — Sections 2-4; ISB-hosted PDF |
| `OSSICLE_MORPH` | [Morphological study of human tympanic ossicular articulations](https://pubmed.ncbi.nlm.nih.gov/9376136/) | indexed_abstract — Structure and function / articulations |
| `PELVIC_ANATOMY` | [Anatomy of the pelvic joints: a review](https://pubmed.ncbi.nlm.nih.gov/2011709/) | indexed_abstract — Structure and function / articulations |
| `UNCOVERTEBRAL` | [Anatomy and clinical significance of uncinate process / uncovertebral joint](https://pubmed.ncbi.nlm.nih.gov/24453021/) | indexed_abstract — Structure and function / articulations |
| `UNCOVERTEBRAL_HISTO` | [Histological study of human uncovertebral joints](https://pubmed.ncbi.nlm.nih.gov/19455000/) | indexed_abstract — Structure and function / articulations |
| `PTF_ANATOMY` | [Anatomy of the proximal tibiofibular joint](https://pubmed.ncbi.nlm.nih.gov/16374587/) | indexed_abstract — Structure and function / articulations |
| `PTF_CADAVER` | [The proximal tibiofibular joint: an anatomic study](https://pubmed.ncbi.nlm.nih.gov/12579012/) | indexed_abstract — Structure and function / articulations |
| `STERNOCOSTAL_CADAVER` | [Sternocostal joints in adult cadavers](https://pubmed.ncbi.nlm.nih.gov/2777528/) | indexed_abstract — Structure and function / articulations |
| `ANTERIOR_THORAX` | [Anterior joints of the thoracic cage](https://pubmed.ncbi.nlm.nih.gov/6364977/) | indexed_abstract — Structure and function / articulations |
| `RIB_LIGAMENTS` | [Ligaments of the costovertebral joints: comprehensive review](https://pmc.ncbi.nlm.nih.gov/articles/PMC5154401/) | indexed_excerpt — Structure and function / articulations |
| `HYOID_CT` | [Hyoid growth and relationship to mandible: CT study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8649784/) | indexed_excerpt — Structure and function / articulations |
| `HYOID_KIN` | [Sagittal plane kinematics of the adult hyoid](https://pmc.ncbi.nlm.nih.gov/articles/PMC3295612/) | indexed_excerpt — Structure and function / articulations |
| `COCCYX_CT` | [CT morphology and morphometry of the normal adult coccyx](https://pmc.ncbi.nlm.nih.gov/articles/PMC3631051/) | indexed_abstract — Abstract: structural variation |
| `COCCYX_MRI` | [MRI anatomy of adult coccyx](https://pubmed.ncbi.nlm.nih.gov/28091426/) | indexed_abstract — Abstract: structural variation |
| `HYOID_FUSION` | [Hyoid fusion and bone density across lifespan](https://pubmed.ncbi.nlm.nih.gov/27114259/) | indexed_abstract — Abstract: structural variation |
| `HYOID_JUNCTION` | [Hyoid body-greater horn synchondrosis: radiological assessment](https://pubmed.ncbi.nlm.nih.gov/2097227/) | indexed_abstract — Abstract: structural variation |
| `LUNATE_FACET` | [MR imaging of type II lunate](https://pubmed.ncbi.nlm.nih.gov/10430130/) | indexed_abstract — Abstract: structural variation |
| `LUNATE_POPULATION` | [Population variation in medial hamate facet of lunate](https://pubmed.ncbi.nlm.nih.gov/16623089/) | indexed_abstract — Abstract: structural variation |
| `TARSAL_VARIANTS` | [Cadaveric tarsal joint variants and coalitions](https://pubmed.ncbi.nlm.nih.gov/12903063/) | indexed_abstract — Abstract: structural variation |
| `SP_SHOULDER` | [StatPearls: Shoulder](https://www.ncbi.nlm.nih.gov/sites/books/NBK536933/) | full_text — Structure and Function |
| `SP_KNEE` | [StatPearls: Knee](https://www.ncbi.nlm.nih.gov/sites/books/NBK500017/) | full_text — Structure and Function |
| `SP_PATELLA` | [StatPearls: Knee Patella](https://www.ncbi.nlm.nih.gov/sites/books/NBK519534/) | full_text — Structure and Function |
| `ISB_FOOT_2021` | [Leardini et al. 2021: ISB multi-segment foot kinematics](https://media.isbweb.org/images/documents/standards/leardinietal2021.pdf) | full_text — Segment landmarks and reporting recommendations |
| `TMJ_EM` | [Yoon et al.: Kinematic study of the mandible using an electromagnetic tracking device and custom dental appliance](https://pubmed.ncbi.nlm.nih.gov/16125713/) | indexed_abstract — Methods/results abstract |
| `TMJ_OPTICAL` | [Ferrario et al.: Translation and rotation movements of the mandible during mouth opening and closing](https://pubmed.ncbi.nlm.nih.gov/19173245/) | indexed_abstract — Methods/results abstract |
| `CERVICAL_NORMAL` | [Bogduk and Mercer: Biomechanics of the cervical spine. I: Normal kinematics](https://pubmed.ncbi.nlm.nih.gov/10946096/) | indexed_abstract — Methods/results abstract |
| `CERVICAL_REVIEW` | [Lindenmann et al.: Kinematics of the Cervical Spine Under Healthy and Degenerative Conditions](https://link.springer.com/article/10.1007/s10439-022-03088-8) | full_text — Healthy conditions: active movement only; Fig 2 / Maximal ROM / Coupling / COR |
| `THORACIC_CADAVER` | [Borkowski et al.: Challenging the Conventional Standard for Thoracic Spine Range of Motion](https://pubmed.ncbi.nlm.nih.gov/27487429/) | indexed_abstract — Methods/results abstract |
| `THORACIC_LB` | [Fujimori et al.: Kinematics of the thoracic spine in trunk lateral bending: in vivo three-dimensional analysis](https://pubmed.ncbi.nlm.nih.gov/24333460/) | indexed_abstract — Methods/results abstract |
| `LUMBAR_REVIEW` | [Widmer et al.: Kinematics of the Spine Under Healthy and Degenerative Conditions](https://link.springer.com/article/10.1007/s10439-019-02252-x) | indexed_abstract — Abstract; full content requires subscription |
| `LUMBAR_QF` | [A Reference Database of Standardised Continuous Lumbar Intervertebral Motion Analysis for Conducting Patient-Specific Comparisons](https://pubmed.ncbi.nlm.nih.gov/34646820/) | indexed_abstract — Methods/results abstract |
| `RIB_4D` | [Movement of the ribs in supine humans for small and large changes in lung volume](https://pubmed.ncbi.nlm.nih.gov/34013751/) | indexed_abstract — Methods/results abstract |
| `RIB_GEOMETRY` | [Geometry and respiratory displacement of human ribs](https://pubmed.ncbi.nlm.nih.gov/3597261/) | indexed_abstract — Methods/results abstract |
| `SI_HEALTHY` | [The mobility of the sacroiliac joints in healthy volunteers between 20 and 50 years of age](https://pubmed.ncbi.nlm.nih.gov/11415579/) | indexed_abstract — Methods/results abstract |
| `SI_REVIEW` | [Three-dimensional movements of the sacroiliac joint: a systematic review of the literature and assessment of clinical utility](https://pubmed.ncbi.nlm.nih.gov/19119382/) | indexed_abstract — Methods/results abstract |
| `SC_ELEVATION` | [Ludewig et al.: Three-dimensional clavicular motion during arm elevation: reliability and descriptive data](https://pubmed.ncbi.nlm.nih.gov/15089027/) | indexed_abstract — Methods/results abstract |
| `SHOULDER_PINS` | [Ludewig et al.: Motion of the shoulder complex during multiplanar humeral elevation](https://pubmed.ncbi.nlm.nih.gov/19181982/) | indexed_abstract — Methods/results abstract |
| `GH_DYNAMIC` | [In vivo kinematic analysis of the glenohumeral joint during dynamic full axial rotation and scapular plane full abduction in healthy shoulders](https://pubmed.ncbi.nlm.nih.gov/27511218/) | indexed_abstract — Methods/results abstract |
| `ELBOW_ANATOMY` | [Clinical anatomy and biomechanics of the elbow](https://pubmed.ncbi.nlm.nih.gov/34262850/) | indexed_abstract — Methods/results abstract |
| `FOREARM_DYNAMIC` | [Matsuki et al.: In vivo 3D kinematics of normal forearms: analysis of dynamic forearm rotation](https://pubmed.ncbi.nlm.nih.gov/20696507/) | indexed_abstract — Methods/results abstract |
| `FOREARM_BIPLANE` | [Reproduction of forearm rotation dynamic using intensity-based biplane 2D-3D registration matching method](https://pubmed.ncbi.nlm.nih.gov/38448504/) | indexed_abstract — Methods/results abstract |
| `WRIST_RC` | [Crisco et al.: In vivo radiocarpal kinematics and the dart thrower's motion](https://pubmed.ncbi.nlm.nih.gov/16322624/) | indexed_abstract — Methods/results abstract |
| `WRIST_MC` | [In vivo three-dimensional kinematics of the midcarpal joint of the wrist](https://pubmed.ncbi.nlm.nih.gov/16510829/) | indexed_abstract — Methods/results abstract |
| `WRIST_ACTIVE` | [Pourahmadi et al.: Reliability and concurrent validity of a new iPhone goniometric application for measuring active wrist range of motion](https://onlinelibrary.wiley.com/doi/10.1111/joa.12568) | full_text — Procedure; Table 2 universal goniometer rater A |
| `THUMB_OPPOSITION` | [Li and Tang: Coordination of thumb joints during opposition](https://pubmed.ncbi.nlm.nih.gov/16643926/) | indexed_abstract — Methods/results abstract |
| `THUMB_BASE_CT` | [Sciacca et al.: In vivo quantification of the 3D kinematics and coupling of the thumb base joints](https://pubmed.ncbi.nlm.nih.gov/35926959/) | indexed_abstract — Methods/results abstract |
| `THUMB_ROM` | [Barakat et al.: The Range of Movement of the Thumb](https://journals.sagepub.com/doi/10.1007/s11552-013-9492-y) | indexed_abstract — Results; examination mode not explicit in accessible abstract |
| `FINGER_GRIP` | [Li et al.: Finger Kinematics during Human Hand Grip and Release](https://pubmed.ncbi.nlm.nih.gov/37366869/) | indexed_abstract — Methods/results abstract |
| `FINGER_WRIST` | [Influence of Wrist Position on the Metacarpophalangeal Joint Motion of the Index Through Small Finger](https://pubmed.ncbi.nlm.nih.gov/29072491/) | indexed_abstract — Methods/results abstract |
| `FINGER_ACTIVE` | [Ibrahim et al.: The Normal Active Range of Motion of the Index, Middle, Ring, and Little Fingers in a Sample of Indian Population](https://www.thieme-connect.com/products/ejournals/pdf/10.1055/s-0044-1788593.pdf) | full_text — Table 2 national means; Methods; national/zone summaries and text contain inconsistencies |
| `HIP_POSITION` | [Han et al.: Hip rotation range of motion in sitting and prone positions in healthy Japanese adults](https://www.jstage.jst.go.jp/article/jpts/27/2/27_jpts-2014-454/_pdf/-char/en) | full_text — Methods passive; Table 2 male left/right sitting/prone |
| `HIP_ACTIVE` | [Simoneau et al.: Influence of hip position and gender on active hip internal and external rotation](https://pubmed.ncbi.nlm.nih.gov/9742472/) | indexed_abstract — Methods/results abstract |
| `KNEE_SHM` | [Jeon and Hong: Comparison of screw-home mechanism in the unloaded living knee subjected to active and passive movements](https://pubmed.ncbi.nlm.nih.gov/33554884/) | indexed_abstract — Methods/results abstract |
| `PF_LUNGE` | [Nha et al.: In vivo patellar tracking: clinical motions and patellofemoral indices](https://pubmed.ncbi.nlm.nih.gov/18627809/) | indexed_abstract — Methods/results abstract |
| `PF_DYNAMIC` | [In vivo and noninvasive six degrees of freedom patellar tracking during voluntary knee movement](https://pubmed.ncbi.nlm.nih.gov/12763436/) | indexed_abstract — Methods/results abstract |
| `PTF_MOTION` | [Kinematics of the proximal tibiofibular joint is influenced by ligament integrity, knee and ankle mobility: an exploratory cadaver study](https://pubmed.ncbi.nlm.nih.gov/30056605/) | indexed_abstract — Methods/results abstract |
| `DISTAL_TF` | [Kinematics of the distal tibiofibular syndesmosis: radiostereometry in 11 normal ankles](https://pubmed.ncbi.nlm.nih.gov/12899556/) | indexed_abstract — Methods/results abstract |
| `ANKLE_WB` | [Yamaguchi et al.: Ankle and Subtalar Kinematics during Dorsiflexion-Plantarflexion Activities](https://journals.sagepub.com/doi/10.3113/FAI.2009.0361) | indexed_abstract — Methods/results: seven healthy subjects; task span is not joint-specific ROM |
| `ANKLE_GEOMETRY` | [The relation between geometry and function of the ankle joint complex: a biomechanical review](https://pubmed.ncbi.nlm.nih.gov/20300732/) | indexed_abstract — Methods/results abstract |
| `FOOT_PINS` | [Lundgren et al.: Invasive in vivo measurement of rear-, mid- and forefoot motion during walking](https://www.sciencedirect.com/science/article/pii/S0966636207002640) | indexed_excerpt — Bone-pin walking study; segment pairs do not isolate all individual contacts |
| `FOOT_REVIEW` | [Nester: Lessons from dynamic cadaver and invasive bone pin studies: do we know how the foot really moves during gait?](https://link.springer.com/article/10.1186/1757-1146-2-18) | full_text — Intrinsic motion / implications / between-subject variation |
| `HALLUX_GAIT` | [Nawoczenski et al.: Relationship between clinical measurements and motion of the first metatarsophalangeal joint during gait](https://pubmed.ncbi.nlm.nih.gov/10199275/) | indexed_abstract — Methods/results abstract |
| `HALLUX_REVIEW` | [Embaby and Elalfy: First metatarsophalangeal joint: Embryology, anatomy and biomechanics](https://www.wjgnet.com/2218-5866/full/v16/i4/102506.htm) | full_text — Anatomy; ROM variability; Table 1 reproduced values not used as primary observations |
| `CDC_ROM` | [CDC: Joint Range of Motion Study public summary](https://archive.cdc.gov/www_cdc_gov/ncbddd/jointrom/index.html) | full_text — 20–44 year male summary, means and 95% confidence intervals; same study as SOUCIE_ROM |
| `SOUCIE_ROM` | [Soucie et al.: Range of motion measurements: reference values and a database for comparison studies](https://onlinelibrary.wiley.com/doi/10.1111/j.1365-2516.2010.02399.x) | indexed_abstract — Methods: bilateral passive universal goniometry; protocol PDF unavailable |
| `C1C2_MRI` | [Roche et al.: The atlanto-axial joint: physiological range of rotation on MRI and CT](https://pubmed.ncbi.nlm.nih.gov/11977941/) | indexed_abstract — Methods and Results |
| `LUMBAR_LIFT` | [Aiyangar et al.: Apportionment of lumbar L2–S1 rotation across individual motion segments during a dynamic lifting task](https://stacks.cdc.gov/view/cdc/203201/cdc_203201_DS1.pdf) | full_text — Methods 2.1; Results; Table 2; Limitations |
| `SP_PRUJ` | [StatPearls: Anatomy, Shoulder and Upper Limb, Proximal Radio-Ulnar Joint](https://www.ncbi.nlm.nih.gov/sites/books/NBK551614/) | full_text — Introduction; Structure and Function: radial head/radial notch, annular ligament, PRUJ/DRUJ coordination |
| `SP_DRUJ` | [StatPearls: Anatomy, Shoulder and Upper Limb, Distal Radio-Ulnar Joint](https://www.ncbi.nlm.nih.gov/sites/books/NBK547720/) | full_text — Introduction; Structure and Function: DRUJ surfaces, TFCC and forearm ring |
| `DRUJ_FUNCTIONAL` | [Haugstvedt et al.: Distal radioulnar joint: functional anatomy, including pathomechanics](https://pubmed.ncbi.nlm.nih.gov/28699788/) | indexed_abstract — Abstract: distal radius–ulna function and stabilizing structures |
