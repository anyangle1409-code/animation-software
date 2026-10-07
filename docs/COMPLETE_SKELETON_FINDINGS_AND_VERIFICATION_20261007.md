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

## Additional validation preparation

At the owner's request, read-only local measurement and reporting tools have been prepared. See `BLENDER_ANATOMICAL_VALIDATION_HANDOFF_20261007.md` and `blender_validation_plan.json`. They provide all reference names/joint-marker requests, profile case specifications and functional task IDs, with explicit missing-evidence statuses. They do not author poses, fit bones or approve any Blender gate.

A fresh static inspection of the 67-control canonical export found no zero-length segments, missing parents or bilateral segment-length differences at numerical resolution. Those checks describe the exported hierarchy/lengths, not anatomical position, joint contact or correct operation. Physical scale, orientation/roll and live Blender geometry remain unverified.

Final tool verification: 21 synthetic tool tests and 16 atlas tests pass. The full repository runs 571 tests: 562 pass, with the same five failures and four errors recorded before this extension; no additional failures. Protected production input hashes match the prior baseline. Independent review found and verified fixes for incomplete/contradictory provenance reporting and absent geometry reporting. Machine-readable evidence: `ORIGINAL_V1_WORK/anatomy/blender_validation_tools_verification.json`. These results do not execute Blender or accept any character fitting/motion gate.

## Phase 6–7 character fitting on the r95 audit copy (live Blender, 7 October 2026)

Executed in Blender 5.2.1 LTS (`bpy` module). Source: r95 BARE export `HomeGymPT_Male_ORIGINAL_v1_CANDIDATE_r95_BARE.glb` (sha256 `c4b8e388…`), the frozen export of the r95 development-freeze candidate `8a39a22d…` (r97–r102 were rejected; no newer revision exists on any remote branch). Audit copies: `HGPT_ANATOMICAL_AUDIT_r95_a001.blend` (`0655dae1…`, import only) and `HGPT_ANATOMICAL_AUDIT_r95_a002.blend` (`f172720b…`, adds `HGPT_ANATOMICAL_MASTER`). Machine-readable record: `ORIGINAL_V1_WORK/anatomy/character_fit_r95_a002.json`. Review renders: `ORIGINAL_V1_WORK/anatomy/audit/review/master_a002/`. Independent capture: `ORIGINAL_V1_WORK/anatomy/audit/runs/master_static_001/`.

### What was built

- 206 `anat_<id>` reference bones (non-deforming), each tagged with role (92 ACTIVE, 87 FOLLOWER, 26 FIXED, 1 REFERENCE), placement class and confidence. 201 tree parents are inventory articulations; 3 are explicit carriers (sternum via costal cartilage at T4; malleus ligament suspension ×2); 2 roots (sacrum; hyoid, which has no osseous articulation).
- 427 `HGPT_JOINT_<id>` marker empties parented to the proximal participant, ISB axis pattern (X anterior, Y proximal, Z character right). 51 landmark empties with `hgpt_landmark_id`.
- Placement classes: 4 regression (femora/humeri), 49 surface-landmark, 38 surface-station (fingers and metacarpals inherit the generator finger stations; no independent anatomical evidence), 115 proportional (low confidence: skull, ossicles, spine, ribs, carpals, tarsals). 16 low-confidence placements were pulled inside the skin with a 3 mm margin; each move is recorded on the bone.

### Findings

| ID | What is wrong / uncertain | Evidence and context | Measurement | Change made | Verification | Remaining limitation |
|---|---|---|---|---|---|---|
| F-SIDE-001 | Runtime `*_l` bones sit on the character's anatomical RIGHT. | Mesh faces −Y (nose y −0.121 m, toe tips −0.269 m) with +Z up ⇒ left = up×forward = +X. Independent hand chirality: on the −X hand, thumb = fingers × palm-normal ⇒ right hand. App front camera (0,1.05,3.4) shows −X on the screen's left; `src/rig/humanoid.ts` comment is internally inconsistent. Generator: "left (−X) authored". | 2 geometric methods + code reading agree. | Master uses geometric sides; anatomical left ↔ runtime `*_r` recorded in the fit record; Phase 5 side mapping reopened. No production rename. | `test_side_binding_follows_geometric_chirality`. | Runtime naming is an owner decision. |
| F-GH-001 | Runtime GH centre (upperarm head) is 53 mm above the fitted GH, at the height of the shoulder's own skin top. | Acromion skin (coronal-section corner) z 1.509 m; skin + acromion thickness (6.6–7.4 mm) + standing AHD (8.8±1.3 mm) + humeral head radius (24.7–28.8 mm) ⇒ centre 42–53 mm below. Two further methods: authored "humeral head level" ring (z 1.456) and deltoid-cap sphere (z 1.457). | Methods agree on z within 6.4 mm (1.456–1.462); x spread 33 mm. Selected (0.219, 0.032, 1.462). | Master GH at the fitted centre. | `distinct_centres` (AC–GH 41.8 mm), containment. | Bony acromion not modelled; probable contributor to the rejected r97–r102 shoulder deformation (not tested here). |
| F-PROP-001 | Fitted humerus and femur are short for a 1.82 m stature. | Trotter–Gleser white-male equations (SE 3.3–4.3 cm). | Humerus 319 mm ⇒ 1.688 m (−13.2 cm); femur 465 mm ⇒ 1.720 m (−10.0 cm): both outside 2 SE. Tibia +3.0, fibula +1.1, ulna −3.5, radius −6.4 cm within 2 SE. | None (check kept FAIL). | Recorded in `trotter_gleser_cross_check`. | Conflict between surface-consistent joint placement and population proportions. Owner decision: raise the shoulder/pelvic surface or accept shorter proximal segments. |
| F-HJC-001 | Runtime thigh head lies 37 mm from the regression HJC (30 mm higher, 19 mm posterior, 9 mm lateral). | Harrington PW-only, Bell, Hara and Davis regressions from mid-ASIS (inter-ASIS 216.6 mm, leg length 928 mm), standing tilt 9° (range 3–18°). ASIS = superolateral end of the authored inguinal line (verified unchanged since O2). | Method spread 22.9 mm; tilt sensitivity −5/+9 mm vertical. Selected (Harrington+Hara mean) (0.083, −0.019, 0.930). | Master uses the selected HJC. | Containment; ordering. | ASIS is an aesthetic groove end (±20 mm); the Trotter–Gleser femur check favours a higher HJC. Unresolved band ≈0.93–0.96 m. |
| F-KNEE-ANKLE-ELBOW-WRIST | Distal runtime joints are consistent with the surface. | Knee: min-area section + epicondyle offset (4 studies, 21.7–33.4 mm) agrees with 0.285H to 2 mm. Ankle: leg–foot junction (0.039H gives 7 mm lower). Elbow: soft-tissue waist. Wrist: min section. | Runtime vs fitted: knee 11 mm, ankle 7 mm, elbow 10 mm, wrist 2 mm. | None. | Rig comparison table in the record. | Elbow epicondyle level unsourced (±20 mm). |
| F-SCAP-001 | Runtime scapula head is not an AC marker. | r43/rev2c relocated the scapula head as a rotation pivot. | 97 mm from the fitted AC. | Master has distinct SC, AC, GH, glenoid, TS, AA, AI. | `distinct_centres`. | TS/AI from the authored medial-border line; T7–T9 inferior-angle variability. |
| F-HAND-001 | Runtime fingertip tails lie outside the finger skin. | Signed skin clearance. | 1.5–5.4 mm outside (all digits). | Master distal phalanges end 3 mm inside. | Containment PASS. | Finger joint stations have no independent evidence on this surface. |
| F-SPINE-001 | Thoracic level anchors conflict. | Jugular notch = T2/T3, xiphisternal = T8/T9 (surface-anatomy references); L5/S1 posterior to the ASIS plane. | Interpolated T8/T9 is 44 mm above the authored xiphoid (≈1.7 levels). | Spine kept as low-confidence interpolation (thoracic 26.5 mm, lumbar 41.6 mm per level). | Spine monotonic; vertebral bodies 56–78 mm in front of the back skin. | No vertebral prominences modelled. |
| F-HEAD-001 | Head has no ears; skull frame landmarks are estimates. | Authored eye/nose/chin rings. | Porion/TMJ at 60% head depth, 12 mm below the eye ring. | Skull bones proportional; 7 pulled inside the skin. | Containment. | Frankfort frame unverified. |
| F-FOOT-001 | Feet are long and five toes are modelled, against one runtime toe bone. | Coronal toe tracking from the web to each tip. | Foot length 305 mm (1.15 × 265 mm reference). | Five toe rays with measured tips; oblique MTP line. | Containment, symmetry. | MTP heads and tarsals are approximations. |
| F-EXPORT-001 | r95 BARE export contains an unparented 42-vertex `Icosphere`. | Object inventory on import. | Unit radius at the origin. | Hidden in review renders; not modified. | Receipt `audit_copy_r95_a001_receipt.json`. | Review before any runtime promotion. |

### Verification results (a002)

| Check | Result |
|---|---|
| Authored features unchanged since O2 (ASIS ×2, IJ, PX, chin, S1 ring points) | PASS (max change 1.3e-7 m; 681 other vertices, mainly hands, changed) |
| 618 bone points and 427 markers inside the body (winding number) | PASS |
| Bilateral symmetry (independent per-side fit) | PASS, max mirror difference 0.38 mm |
| Distinct centres (named pairs; no two markers within 0.1 mm) | PASS |
| Limb ordering, spine monotonic | PASS |
| Trotter–Gleser long-bone/stature consistency | **FAIL** (humerus, femur) |
| Independent capture (`master_static_001`): coverage 206/206, identity, geometry integrity, 427/427 markers, landmarks | PASS; anatomical placement and joint operation UNVERIFIED |
| Blender round trip (bones / markers) | 5.9e-8 m / 2.9e-7 m |

Running the capture on the real master exposed three more tool defects, fixed with regression tests: TOOL-004 (orthogonality tolerance 1e-6 rejected valid single-precision Blender matrices on short bones; now 1e-5), TOOL-005 (a derived relative-rotation error crashed the analysis instead of failing `sample_integrity`) and TOOL-006 (the capture was written only after analysis, so a crash lost the evidence).

### Sources added in this phase

Harrington et al. 2007 and Sangeux 2015 (pyCGM2 implementation), Bell et al. 1990 (snippets; the pyCGM2 SI coefficient −0.19 conflicts with the published 30% and is not used), Hara et al. 2016 and Davis et al. 1991 (pyCGM2 and pyCGM code), standing pelvic tilt (IJSPT review), epicondyle-to-joint-line studies (Brazilian and Thai MRI, MRI n=130, cadaver n=40), Drillis & Contini proportions (knee and ankle labels only; 0.530H label conflicts), Trotter & Gleser stature equations, acromiohumeral distance (J Orthop Surg Res 2020), acromion thickness studies, humeral head radius studies, and surface-anatomy vertebral levels. General web hosts were blocked by the session's egress policy. Access was limited to search snippets and GitHub-hosted source code; this is recorded per source in `character_fit_r95_a002.json:sources`.

## Phase 8–9 joint solvers and isolated bone-only tests (fit revision a003)

### Fit revision a003 (supersedes a002)

A direction regression test on the a002 fit found that the elbow flexion axis was tilted about 23° from mediolateral. The cause was an unsourced 10 mm vertical offset between the capitulum and trochlea centres; 90° of elbow flexion moved the forearm only 0.917 forward. In a003 both centres lie on a near-mediolateral axis; valgus obliquity is unmodelled because it is not measurable on this surface. The forearm rotation axis now runs from the radial head centre to the ulnar head centre; previously it ran between radius–ulna midpoints. a002 is retained as the superseded revision. a003 (`HGPT_ANATOMICAL_AUDIT_r95_a003.blend`, record `character_fit_r95_a003.json`) passes the same Phase 6/7 checks; its independent capture is `runs/master_static_002`.

### Solver conventions (`scripts/anatomy_fit/joint_solver.py`)

- Segment frames use the ISB pattern: X anterior/palmar, Y proximal, Z to the character's right. The forearm, hand and digits use landmark frames (styloids, elbow centre, metacarpal heads), because the palms face medially at rest. The thumb flexes across the palm, so its X axis is ulnar.
- Joint coordinate systems: Z-X-Y for hip, knee, ankle, elbow, wrist, spine and digits (Grood & Suntay; ISB 2002/2005); Y-X-Y for the glenohumeral joint, commanded as swing–twist so that zero elevation is not gimbal-locked, with raw ISB angles also reported.
- Clinical signs: flexion, adduction and internal rotation positive on both sides; knee flexion is −Z.
- Verification: unit tests round-trip 200 random Z-X-Y triples and GH commands. Direction tests on the committed fit cover hip, knee, GH plane, elbow, pronation, ankle, subtalar inversion, wrist and C1/C2.
- Sourced couplings (`FOLLOWER_COUPLINGS`):
  - Subtalar axis: 42° inclination, 23° medial deviation (Inman).
  - Scapulothoracic rhythm: 0.43° upward rotation per GH degree, plus McClure 2001 end values (50° upward rotation, 30° posterior tilt, 24° external rotation).
  - Clavicular posterior rotation: 31° (Ludewig 2009).
  - Knee screw-home: 3.6° tibial external rotation into terminal extension (magnitude sourced; spread over the last 20° as an approximation).
  - Wrist stage split: the accessible sources conflict, so the equal split is UNVERIFIED.

### Isolated tests (`runs/isolated_bone_only_003`; current run `isolated_bone_only_004`)

66 tests: 31 paired on both sides plus 4 midline. Every test runs neutral → intermediate → context reference → return → reversal → return with C1 easing, keyed in a new audit file and measured from Blender's evaluated pose. The integrity thresholds (1e-3°, 1e-6 m) check the implementation only.

| Test | Profile | Measured primary range | Max angle error | Max centre drift | Integrity | Amplitude basis |
|---|---|---|---|---|---|---|
| `hip_flexion_extension_{left,right}` | hip | flexion -17.4…130.4° | 3.4e-05° | 3.0e-08 m | PASS | CDC passive mean (male 20-44); amplitude only, not a character limit |
| `hip_abduction_adduction_{left,right}` | hip | adduction -30.0…20.0° | 7.7e-06° | 4.6e-09 m | PASS | TEST AMPLITUDE (no hip ab/adduction observation in the atlas): +20 adduction / -30 abduction |
| `hip_rotation_at_0_flexion_{left,right}` | hip | internal -53.2…44.2° | 1.2e-05° | 3.6e-09 m | PASS | Prone (hip 0 deg) passive means, side-specific |
| `hip_rotation_at_90_flexion_{left,right}` | hip | internal -43.2…40.6° | 2.9e-05° | 2.5e-08 m | PASS | Sitting (hip 90 deg) passive means, side-specific |
| `knee_flexion_extension_{left,right}` | knee | flexion -1.0…137.7° | 2.4e-05° | 2.9e-08 m | PASS | CDC passive knee complex means; screw-home coupling not applied (no sourced magnitude) |
| `talocrural_dorsi_plantarflexion_{left,right}` | ankle | angle -40.0…20.0° | 1.1e-05° | 4.1e-09 m | PASS | TEST AMPLITUDE +20 DF / -40 PF for the talocrural stage; CDC values are the ankle-foot complex and are not ass |
| `subtalar_inversion_eversion_{left,right}` | subtalar | angle -10.0…20.0° | 3.3e-06° | 3.8e-09 m | PASS | TEST AMPLITUDE +20 inversion / -10 eversion about the Inman axis (42 deg / 23 deg); midfoot followers not driv |
| `gh_elevation_plane_0_{left,right}` | gh | elevation 0.0…120.0° | 1.7e-05° | 5.8e-08 m | PASS | TEST AMPLITUDE to 120 deg GH elevation with the scapula fixed; CDC 168.8 deg is humerothoracic and is not assi |
| `gh_elevation_plane_40_{left,right}` | gh | elevation 0.0…120.0° | 5.5e-05° | 6.0e-08 m | PASS | TEST AMPLITUDE to 120 deg GH elevation with the scapula fixed; CDC 168.8 deg is humerothoracic and is not assi |
| `gh_elevation_plane_90_{left,right}` | gh | elevation 0.0…120.0° | 2.5e-05° | 5.9e-08 m | PASS | TEST AMPLITUDE to 120 deg GH elevation with the scapula fixed; CDC 168.8 deg is humerothoracic and is not assi |
| `gh_axial_rotation_at_0_elevation_{left,right}` | gh | internal -50.0…50.0° | 2.3e-05° | 7.0e-09 m | PASS | TEST AMPLITUDE +/-50 deg axial rotation at stated elevation |
| `gh_axial_rotation_at_90_elevation_{left,right}` | gh | internal -50.0…50.0° | 2.7e-05° | 6.0e-08 m | PASS | TEST AMPLITUDE +/-50 deg axial rotation at stated elevation |
| `elbow_flexion_at_pronation_0_{left,right}` | elbow | angle -0.8…144.6° | 4.0e-05° | 5.8e-08 m | PASS | CDC passive elbow means at the stated forearm rotation |
| `elbow_flexion_at_pronation_60_{left,right}` | elbow | angle -0.8…144.6° | 4.0e-05° | 5.8e-08 m | PASS | CDC passive elbow means at the stated forearm rotation |
| `forearm_rotation_at_elbow_0_{left,right}` | radioulnar | pronation -85.0…76.9° | 1.7e-05° | 4.4e-16 m | PASS | CDC passive forearm means; dynamic biplane active means retained as a second context |
| `forearm_rotation_at_elbow_90_{left,right}` | radioulnar | pronation -85.0…76.9° | 3.0e-05° | 5.6e-08 m | PASS | CDC passive forearm means; dynamic biplane active means retained as a second context |
| `wrist_flexion_{left,right}` | radiocarpal | flexion -68.0…73.6° | 1.6e-05° | 2.8e-08 m | PASS | Active wrist-complex means (flexion / extension); split equally between radiocarpal and midcarpal stages (spli |
| `wrist_adduction_{left,right}` | radiocarpal | adduction -18.6…31.3° | 8.6e-06° | 2.8e-08 m | PASS | Active wrist-complex means (ulnar deviation / radial deviation); split equally between radiocarpal and midcarp |
| `digit2_flexion_{left,right}` | mcp | mcp -8.6…86.0° | 4.1e-05° | 2.9e-08 m | PASS | Digit-specific active means (reduced numerical confidence, see finger_table_consistency); -10% of each mean as |
| `digit3_flexion_{left,right}` | mcp | mcp -8.7…86.6° | 2.9e-05° | 2.9e-08 m | PASS | Digit-specific active means (reduced numerical confidence, see finger_table_consistency); -10% of each mean as |
| `digit4_flexion_{left,right}` | mcp | mcp -8.4…84.2° | 4.6e-05° | 1.8e-08 m | PASS | Digit-specific active means (reduced numerical confidence, see finger_table_consistency); -10% of each mean as |
| `digit5_flexion_{left,right}` | mcp | mcp -8.5…85.0° | 3.5e-05° | 2.6e-08 m | PASS | Digit-specific active means (reduced numerical confidence, see finger_table_consistency); -10% of each mean as |
| `thumb_flexion_{left,right}` | thumb_mcp | mcp -8.1…60.0° | 3.8e-05° | 9.6e-09 m | PASS | Clinical thumb means (examination mode unspecified in the accessible abstract); flexion axis normal to the thu |
| `sacroiliac_rotation_{left,right}` | si | angle -0.8…0.9° | 2.2e-06° | 5.7e-08 m | PASS | Functional total SI rotation 1.7 deg (healthy volunteers), split +/-0.85 about a mediolateral axis through the |
| `hallux_mtp_dorsiflexion_{left,right}` | hallux | angle -20.0…44.0° | 7.7e-06° | 7.0e-09 m | PASS | Standing active DF mean (task-specific); -20 plantarflexion TEST AMPLITUDE |
| `knee_flexion_with_screw_home_{left,right}` | knee | flexion -0.0…60.0° | 1.8e-05° | 2.5e-08 m | PASS | TEST AMPLITUDE 0-60 deg knee flexion; coupled tibial internal rotation 3.6 deg over the first 20 deg of flexio |
| `shoulder_complex_scapular_plane_{left,right}` | st | elevation 0.0…117.5° | 2.9e-05° | 1.3e-07 m | PASS | GH elevation 0-117.5 deg in the 40 deg plane with sourced scapulothoracic rhythm (0.43 upward rotation per GH  |
| `c1_c2_axial_rotation` | c1_c2 | angle -32.4…34.2° | 6.6e-06° | 4.6e-10 m | PASS | MRI maximal voluntary rotation means (left/right) |
| `cervical_c4_c5_flexion` | cervical | flexion -5.0…5.0° | 1.6e-06° | 9.6e-10 m | PASS | TEST AMPLITUDE +/-5 deg (cervical review values excluded: cervical_review_AR_typo; no per-level transferable v |
| `cervical_c4_c5_adduction` | cervical | adduction -5.0…5.0° | 8.5e-07° | 1.4e-10 m | PASS | TEST AMPLITUDE +/-5 deg (cervical review values excluded: cervical_review_AR_typo; no per-level transferable v |
| `cervical_c4_c5_internal` | cervical | internal -5.0…5.0° | 1.3e-06° | 3.8e-11 m | PASS | TEST AMPLITUDE +/-5 deg (cervical review values excluded: cervical_review_AR_typo; no per-level transferable v |
| `tmj_opening` | tmj | angle 0.0…25.0° | 2.6e-06° | 2.5e-08 m | PASS | TEST AMPLITUDE 25 deg rotation with 16 mm anteroinferior condylar glide (within the observed 7.5-25.3 mm condy |
| `lumbar_l2_l3_extension` | lumbar | flexion -9.9…-0.0° | 5.0e-06° | 9.2e-10 m | PASS | Level-specific extension during a lift (task context, not maximum flexibility); rotation about the disc marker |
| `lumbar_l3_l4_extension` | lumbar | flexion -10.7…0.0° | 2.9e-06° | 3.9e-10 m | PASS | Level-specific extension during a lift (task context, not maximum flexibility); rotation about the disc marker |
| `lumbar_l4_l5_extension` | lumbar | flexion -12.1…-0.0° | 2.7e-06° | 2.7e-10 m | PASS | Level-specific extension during a lift (task context, not maximum flexibility); rotation about the disc marker |
| `lumbar_l5_sacrum_extension` | lumbar | flexion -9.6…-0.0° | 3.6e-06° | 5.9e-08 m | PASS | Level-specific extension during a lift (task context, not maximum flexibility); rotation about the disc marker |
| `thoracic_t6_t7_flexion` | thoracic | flexion -1.9…1.9° | 9.2e-07° | 1.2e-09 m | PASS | Half of the upper pooled cadaver total (3.8 deg) each way; cadaver passive context |
| `thoracic_t6_t7_adduction` | thoracic | adduction -2.2…2.2° | 3.8e-07° | 2.7e-11 m | PASS | Half of the upper pooled cadaver total (4.4 deg) each way; cadaver passive context |
| `thoracic_t6_t7_internal` | thoracic | internal -2.6…2.6° | 5.3e-07° | 6.7e-12 m | PASS | Half of the upper pooled cadaver total (5.2 deg) each way; cadaver passive context |
**Results**
- **Integrity:** 66/66 tests pass. All 27 left/right mirror pairs pass; side-specific source amplitudes (hip rotation) are compared as errors, not raw angles.
- **Commanded vs measured:** the reversal frames match between commands and measurements, and the joint-centre markers follow their proximal segments.
- **Second measurement:** the verified capture tool sampled peak and reversal frames independently (`runs/isolated_bone_only_001/crosscheck_result.json`). Its parent-relative principal rotations reproduce every commanded amplitude to within 1.1e-5° on both sides: knee 137.7/1.0°, hip 130.4/17.4°, hip rotation 44.2/53.2° (left) and 45.6/51.7° (right), elbow 144.6/0.8°, pronation/supination 76.9/85.0°, GH 120°, talocrural 20/40°, subtalar 20/10°, digit 3 MCP 86.6°, and the midcarpal stage (half of the 73.57° wrist flexion).

**Context checks inside the tests** (consistency with source observations, not acceptance):
- *Shoulder complex.* GH 117.5° in the 40° plane with the sourced rhythm gives 174.1° humerothoracic elevation, against the CDC humerothoracic flexion mean of 168.8°. The contexts differ: active scapular plane versus passive flexion. AC closure is exact. The GH centre travels 39 mm with the scapula and keeps its 41.8 mm separation from AC.
- *TMJ.* A 25° opening with a 16 mm condylar glide moves the fitted incisor point 43.3 mm, inside the observed 34.9–54.3 mm range. The 16 mm glide is inside the observed 7.5–25.3 mm condylar range.
- *Hip rotation.* Side-specific prone (0° flexion) and sitting (90° flexion) passive means are applied separately, never averaged.

**Movement clips:** `audit/review/isolated_clips_001/` (14 isolated sweeps, left side; bone-only, coloured by placement class) and `isolated_clips_002/` (shoulder complex, knee screw-home).

### What these tests do not establish (remaining UNVERIFIED)

- **Contact behaviour.** Articular contact paths, rolling/sliding, moving centres of rotation and capsular translations are not modelled. Every joint except the TMJ glide rotates about a fixed fitted centre.
- **Follower mechanics not implemented.** No source magnitudes were accessible for: patellar tracking, proximal/distal tibiofibular motion, midfoot and tarsometatarsal motion, lesser toes, individual carpal kinematics, rib and costal motion, pubic symphysis, coccyx, hyoid, SC elevation and retraction, and the plane dependence of scapular rhythm.
- **Joints with no isolated test yet.** Thumb CMC (saddle) and opposition; C0–C1; C2–C3 to C7–T1 apart from the sampled C4/C5; T1–T5 and T8–T12 apart from the sampled T6/T7; L1/L2; individual ribs; finger abduction; and wrist dart-thrower paths.
- **Amplitudes that are not limits.** Test amplitudes without a joint-specific source are labelled as such. CDC ankle and humerothoracic values are complex-level and are not assigned to single joints. No result is a character ROM limit.
- **Inherited fit uncertainty.** Placement uncertainty from Gate 6 (F-PROP-001, F-HJC-001) carries into every sweep.

### Run 004 update: clavicular retraction and a defect caught by the mirror check

Clavicular retraction of 15° (secondary review snippet, consistent with Ludewig's 31° posterior rotation) was added to the shoulder-complex coupling. Clavicular elevation is not applied, because only a bound (<10°) is sourced. The scapula keeps its thorax-relative target orientation and is carried with the moving AC point, so the AC joint absorbs the remainder; AC closure remains exact.

The first run with retraction failed the left/right mirror check. The angle errors matched between sides (1.6e-5°), but the GH centre travelled 32 mm on the left and 90 mm on the right. The cause was a retraction-sign probe that tested the rotated clavicle axis instead of its change: on the right side, the axis's own 0.22 posterior component outweighed the change, so that clavicle protracted. Fixed, with a regression test (`ShoulderComplexMirrorTests`). Run 004: 66/66 integrity and 27/27 mirror pairs. The GH centre travels 32 mm on both sides with 15° retraction and 31° posterior rotation; humerothoracic elevation stays 174.1°. Clip: `audit/review/isolated_clips_003/`.

## Independent review of the Phase 6–9 code and corrections (current: isolated run 006)

A fresh read-only reviewer checked the solver, test, capture and fit code against the committed evidence. Every material finding was re-measured independently before being fixed. **Two statements earlier in this report were wrong**; they are left in place above and corrected here.

| Review finding | Independent re-check | Correction | Verification |
|---|---|---|---|
| **TMJ "opening" closed the mouth.** The axis pointed to the character's right, so the incisor moved 36.9 mm up and 22.6 mm forward. The earlier statement "incisor 43.3 mm, inside the observed range" is **invalid**. | Reproduced: the incisor moved +36.9 mm in z. | Axis now points to the character's left. | Run 006: the incisor moves **down** 45.1 mm, inside the observed 34.9–54.3 mm range; condylar glide 16 mm. Direction test added. |
| **Spinal flexion sign inverted** for superior moving segments. The four "lumbar extension" tests were flexion; cervical and thoracic flexion labels were reversed. | Reproduced: L3 tail moved 7.4 mm anterior under "extension". | `spine` uses −Z for flexion, like the knee. Lateral bending and axial-rotation meanings are documented. | Run 006: extension moves the superior vertebra posteriorly (7.8–8.1 mm at the next disc); flexion moves it anteriorly. Clips: `audit/review/isolated_clips_004/`. |
| **Integrity checks were blind to sign errors.** Commands and measurements passed through mutually inverse mappings, and mirror checks compared values the same sign table had already mirrored. | Confirmed by reasoning and by the two defects above. | New `AbsoluteDirectionTests`: every spec must move in its anatomically named world direction, and a spec without an assertion fails the suite. | Red/green: fails on the old spine sign and the old TMJ axis, passes now. |
| **Mirror checks could pass vacuously.** Side-specific amplitudes were compared as errors, and some distal markers never moved. | Confirmed (DRUJ on the static ulna; spine distal markers on the inferior vertebra). | Mirror now compares reflected world transforms (M·R_left·M vs R_right); side-specific pairs are reported as `SOLVER_TEST` and covered by an exact solver mirror test. Distal markers are carried by the moving bone and must travel at least 0.5 mm. | Run 005 failed two spinal axial tests whose marker sat on the rotation axis (kept as a recorded run). Run 006 uses off-axis facet markers: 70/70 tests; 27 pairs pass on reflected transforms; 2 pairs are solver-test only. |
| **Missing or ungated measurements counted as PASS.** | Confirmed. | Unmeasured channels FAIL unless whitelisted (GH plane below 1° elevation). Digit cross-talk, TMJ off-axis, humeroradial drift (pronation axis now through the radial-head centre), midcarpal-centre drift and marker-vs-centre drift are all gated. | All gated values in run 006 are ≤ 6e-8 m or ≤ 2e-5°. |
| **`rigid_matrix` accepted non-uniform scale.** | Reproduced: diag(1,2,1) accepted. | Uniform scale allowed; non-uniform scale rejected. | Regression test `RigidScaleTests`. |
| **Trotter–Gleser derivations biased** (tibia included the malleolus; radius started at the capitulum centre). | Recomputed. | Tibia excludes the malleolus; radius starts at the radial-head surface. | Addendum `character_fit_r95_a003_review_addendum.json`. Femur −10.0 cm, humerus −13.2 cm and **radius −9.5 cm** fall outside 2 SE; tibia +0.5, fibula +1.1, ulna −3.5 cm are within. F-PROP-001 now reads: the upper limb and thigh are short for the 1.82 m stature. |
| **Midline symmetry check could not fail** (it ran after snapping). | Confirmed. | The addendum records pre-snap offsets. | Maximum 2.4 mm (sternum); every other midline bone is under 0.5 mm. |
| **Parallel-segment branch of `segment_closest`.** | 90 markers use it (collinear chains). | None needed: s = 0 with p0's projection is a valid closest pair. | Distance matches brute force within 4.5e-9 m for all 90. |
| **Wrist split applied the half-angle Cardan channels twice** (exact only for single-channel commands). | Confirmed by algebra. | Exact half rotation (`half_rotation`, H·H = R). | Unit test. |
| **Thumb CMC unsigned angle.** | Confirmed. | Specs fail fast if the target does not exceed the rest angle. | Current targets exceed rest by 24–39°. |

The reviewer confirmed as correct: the Blender basis composition, GH swing–twist, pronation sign and composition, subtalar axis, talocrural/hallux/SI/C1–C2 signs, hip and knee JCS signs and mirroring, forearm/hand/thumb frame handedness, scapular decomposition, screw-home direction, quaternion utilities, winding number, regression coefficients, Trotter–Gleser coefficients, and the capture-tool fixes.

Current evidence: `audit/runs/isolated_bone_only_006` (test file `HGPT_ANATOMICAL_AUDIT_r95_a003_isolated_tests_v6.blend`). Runs 001–005 are retained as history: 001–004 predate the review, and 005 is the recorded failing run.

## Second independent review of the fixes (current: isolated run 007)

The same read-only reviewer re-checked commit `c0f8561b`. It found no critical defect and confirmed the spine and TMJ sign fixes, `half_rotation` (5,000 random rotations, H·H = R within 1.2e-15), the pronation axis, the new runner gates, the thumb CMC guard and the corrected Trotter–Gleser derivations. Every remaining finding was reproduced before it was fixed.

| Finding | Re-check | Correction | Verification |
|---|---|---|---|
| **Mirror check reflected only the first moving bone.** In forearm rotation that bone is the static ulna (reflected difference 4e-16), so the radius was never compared; the shoulder complex compared only the clavicle. | Confirmed in run 006 (`moving_delta` held one bone). | Every commanded bone (moving, second wrist stage, digit chain) is stored and reflect-compared; the report lists `bones_compared`. | Run 007: 27 pairs PASS with all bones compared (for example radius + ulna; clavicle + scapula + humerus; six carpals; three phalanges), max 1.1e-6. |
| **`rigid_matrix` accepted any uniform scale**, so a pose bone scaled ×1.5 passed. | Confirmed by a unit test. | Captures record the armature object's world scale; bone axes must equal it. New `bone_scale` check (UNVERIFIED for older captures without the field). | Test red on the old code, green now. Smoke re-run `blender_smoke_002` PASS; master capture `master_static_003`: `bone_scale` PASS, source hash unchanged. |
| **Coupled-follower directions were not asserted** (screw-home rotation; scapular tilt, external rotation, clavicle posterior rotation). | Confirmed. | Absolute assertions added: the tibia rotates internally as the knee leaves extension; posterior tilt brings the inferior angle forward; external rotation moves the lateral scapula back; posterior rotation turns the clavicle's anterior surface up; retraction moves the AC point back. | Each of four sign mutations makes the suite fail; restored code passes. |
| **A missing primary marker dropped its gate silently.** | Confirmed by reading. | A missing `HGPT_JOINT_` object is now reported as unmeasured, so the test fails. | Run 007: no test has an unmeasured item. |
| **TMJ glide direction was not checked.** | Confirmed. | Condylar glide must be anterior and inferior throughout. | Run 007: peak glide 14.3 mm anterior and 7.2 mm inferior; never posterior or superior. |
| **`segment_closest` point query** returned p0 when the query fell inside the 1e-6 m "segment". | Confirmed: 39 of 338 calls differ, by at most 0.0017 mm. | Degenerate segments are handled explicitly (Ericson 5.1.9); the parallel test is now relative. | Unit test red on the old code, green now. The effect on the a003 markers is below 0.002 mm, so the fit is not regenerated. |
| Hip-rotation pairs are solver-tested only. | Correct and reported honestly. | Not changed: their source amplitudes differ by side. | Exact solver mirror test. |

Current evidence: `audit/runs/isolated_bone_only_007` (test file `HGPT_ANATOMICAL_AUDIT_r95_a003_isolated_tests_v7.blend`, sha256 `7604c857…`). Repository suite: 595 tests, with the same 9 inherited failures/errors as the baseline. Clips: `audit/review/isolated_clips_005` (19 clips from the run 006 test file; command authoring is identical in run 007).
