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

## F-PROP-001 / F-GH-001 / F-HJC-001 investigation: stylised body or method mismatch? (fit a003 retained)

**Question.** The stature-equation check (Trotter–Gleser) fails for the femur (−10.0 cm), humerus (−13.2 cm) and radius (−9.5 cm). Is the character's skeleton really short, is the body stylised, or is the check itself mismatched with a joint-centre fit?

**Evidence used (all reachable from this session).**
- **ANSUR II male public data** (US Army 2012 survey; 4,082 men). The file is committed as `ORIGINAL_V1_WORK/anatomy/sources/ansur2/ANSUR_II_MALE_Public.csv` (sha256 `e468eb57…`). It was retrieved from a GitHub copy because the Penn State and Army hosts are blocked here. Integrity check: radiale–stylion length mean 267.9 mm, SD 15.4 mm, exactly as published.
- **Open musculoskeletal models** (OpenSim models on GitHub): Rajagopal 2016 (generic 1.70 m, 75 kg male), Arm26 (Holzbaur 2005 derived) and Gait2354. URLs, hashes and the values used are in `sources/open_musculoskeletal_models.json`.
- **Radiographic relation** (two independent search snippets): the greater-trochanter tip lies on average 8 mm above the femoral head centre on neutral AP radiographs (100 hips: 75% above, 15% below, 10% level).
- **New surface measurements** of the r95 body (`scripts/anatomy_fit/proportion_audit.py measure`). These use sections and loop splits, not the fitted joint centres; values that do depend on the fit are labelled. The audit file hash is unchanged before and after.

Evidence: `ORIGINAL_V1_WORK/anatomy/audit/proportion_audit_001/` (`character_surface.json`, `proportion_report.json`).

### 1. The stature-equation chain fails on real men too (method bias)

The fit's own conversion was applied to every ANSUR subject, using ANSUR landmarks in place of fitted centres: surface → joint centre → osteometric length (head radius, condyle and trochlea allowances) → Trotter–Gleser.

| Bone | ANSUR mean bias | ANSUR men beyond −2 SE | Character | Character's percentile among ANSUR men |
|---|---|---|---|---|
| Femur | −6.4 cm (SD 5.6) | 50% | −10.0 cm | 26th: within normal spread |
| Humerus | −9.7 cm (SD 4.2) | 65% | −13.2 cm | 20th: within normal spread |
| Radius | +4.6 cm (SD 4.9) | 0.2% | −9.5 cm | **0.15th: outside the central 95%** |

Second estimator for the femur: Feldesman's femur/stature ratio (26.74%) gives −6.2 cm on ANSUR men and −8.3 cm for the character, the same pattern. The ratio is reported to overestimate stature for femurs over 50 cm.

So the femur and humerus "failures" are what this chain produces for ordinary men. They are **not evidence of short bones**. Which link is biased (the stature equations, an allowance, or both) cannot be separated without osteometric data on living subjects. The check therefore cannot be used as an acceptance test for a joint-centre fit.

### 2. Fitted joint centres against independent landmarks

| Centre | Fitted height | Independent expectation | Difference |
|---|---|---|---|
| HJC (F-HJC-001) | 0.930 m | ANSUR trochanterion at 1.82 m (0.940 m) − 8 mm radiographic offset = 0.932 m | **−2 mm** (trochanterion residual SD 26 mm) |
| KJC | 0.517 m | ANSUR lateral femoral epicondyle height 0.513 m | +4 mm (SD 14 mm) |
| Tibial joint line | 0.490 m | ANSUR tibial height 0.490 m | 0 mm |
| EJC (from the character's own acromion) | acromion → EJC 0.3295 m | ANSUR acromion–radiale at 1.82 m − 15 mm = 0.3332 m | −3.7 mm (SD 10.6 mm) |
| GH depth below acromion skin (F-GH-001) | 47.1 mm | Acromion marker → GH: Arm26 47 mm; Rajagopal 53.5 mm (57 mm scaled), with marker radius and skin above the skin surface | within 10 mm of both |

A weak, soft-tissue check also fits. The new lateral hip profile has a small local prominence at z ≈ 0.92 m, which is consistent with a greater trochanter just below a ~0.93–0.94 m tip; the bony trochanter is not modelled.

**F-HJC-001 reading.** The selected HJC (Harrington + Hara mean) is corroborated by an independent route. The runtime thigh head (~0.96 m, about 30 mm higher) is not. The fit keeps its HJC; the runtime offset remains a runtime-rig finding.

**F-GH-001 reading.** The fitted GH depth is corroborated by two open models. The runtime GH sits above the acromion skin (1.515 m vs 1.5095 m), which cannot be a joint centre. The runtime finding stands.

### 3. What is genuinely character-specific (authored surface proportions)

These are stature-conditioned z-scores against ANSUR men (regression on stature, residual SD):

| Measure | Character | ANSUR at 1.82 m | z |
|---|---|---|---|
| Acromion to fingertip (arm hanging) | 779.5 mm | 825.8 mm | **−2.18** |
| Acromion to wrist | 590.5 mm | 617.0 mm | −1.40 |
| Hand length | 189 mm | 200 mm | −1.43 |
| Wrist height | 919 mm | 881 mm | +1.78 |
| Crotch height | 839 mm | 883 mm | −1.85 |
| Axilla height | 1411 mm | 1383 mm | +1.92 |
| Sternal notch height | 1519 mm | 1495 mm | +2.10 |
| Foot length | 305 mm | 280 mm | +2.77 |
| Bideltoid breadth | 575 mm | 520 mm | +1.79 |
| Acromial height | 1510 mm | 1498 mm | +0.73 |
| Knee, tibial and malleolus heights | — | — | +0.30 / +0.03 / +0.52 |

Second measurement of the arm length. The fingertip height (0.730 m, loop tracking) agrees with the runtime middle-finger tip (0.724 m, which lies 1.5–5.4 mm outside the skin per F-HAND-001). The runtime wrist (0.920 m) agrees with the wrist section (0.919 m).

The body has population-typical leg joint heights and a typical upper arm. The forearm and hand are short (the arm is about 46 mm shorter than expected, z −2.2, about the 1st percentile). The trunk is long above a low crotch, the feet are long, and the shoulders are broad. These are properties of the authored body surface, and the fitted skeleton follows them. The short radius (0.15th percentile in the chain) is the skeletal reflection of the short forearm surface, not a fitting error.

**Wrist placement uncertainty.** The WJC sits at the minimum-area wrist section. The narrowest part of the distal forearm usually lies proximal to the styloid tips (direction only; no accessible magnitude). The hand widens from about 0.905 m, so the styloid level is probably within about 10 mm of the fitted centre. Even with a lower wrist, elbow-to-fingertip stays short, because the fingertip height is fixed by the surface.

### Decision

- **No a004.** The evidence does not support changing skeleton geometry. Femur, humerus, hip, knee, elbow and GH placements are each corroborated by an independent route. The remaining discrepancy (forearm and hand) is in the authored body, and moving bones would place them outside the skin.
- **a003 is retained unchanged** (sha256 `670a37bf…`).
- **F-PROP-001 reclassified.** It is no longer "femur/humerus/radius too short". It now reads: the stature-equation check is method-biased for this pipeline (femur, humerus), and the authored forearm and hand are short (character-specific limitation). The stature-equation check stays recorded as FAIL. **No bone is declared anatomically correct by this investigation**; the proportional placements remain low confidence.
- **The owner decision narrows** to one question: is the short forearm and hand (and the long feet) intended character styling, or should the production body change? Changing the body is a production change and outside this audit.
- **Recorded defect F-HJC-002.** The stored trochanterion landmark (z 0.86 m) is a search-range boundary artefact (thigh bulge). It feeds only the Davis HJC method (low confidence, not selected), so the selected HJC is unaffected. The new lateral-profile measurement replaces it as evidence.

## Phase 8–9 extension: newly sourced isolated tests and followers (current: run 014)

New sources are recorded in `ORIGINAL_V1_WORK/anatomy/phase9_supplementary_observations.json` and merged into the test specs; the Phase 4 atlas is not modified. Full texts were blocked by the egress policy, so every value comes from an abstract or table snippet and is labelled with its access level, population and conflicts.

| Test (both sides unless midline) | Value used | Source and context | Notes |
|---|---|---|---|
| C0–C1 flexion/extension | total 17.9°, split ±8.95° | Biplane radiography, 20 young adults (J Biomech 2024) | **Conflicting reports** (6.3° in vivo, 24–27° cadaver, 25.6° in a 2026 study) recorded. The split is unsourced. |
| Cervical C3/4, C4/5, C5/6, C6/7 flexion/extension | 7.9/6.3, 8.0/7.9, 7.4/7.3, 7.1/5.4° | Anderst 2013 JBJS Table II, 20 asymptomatic controls (biplane, 30 fps) | Second source: Yu 2017 totals agree within 1 SD. Replaces the earlier ±5° C4/5 TEST AMPLITUDE. |
| Thoracic T1/T2–T12/L1 FE, LB and AR (33 new tests) | half of the **lower** pooled cadaver total each way | THORACIC_CADAVER (Phase 4 atlas) | Level-specific values not accessible; the lower bound stays within every level's pooled mean. |
| Ribs 1–7, pump-handle | 4.6° TEST AMPLITUDE | Beyer 2014 CT, 8 volunteers: level means 4.6–8.9° and 5.7–12.2° for the two major components | Amplitude is no larger than the smallest reported level mean. **F-RIB-001** (below) forces a mediolateral axis. Ribs 8–12 unresolved. |
| Finger spreading, MCP abduction (digits 2, 4, 5) | 25° | Clinical expected value (secondary goniometry references) | Not digit-specific. |
| Thumb opposition components (abduction, then pronation) | palmar abduction 20.7°, which takes the intermetacarpal anteposition from the fitted rest (37.3°) to the clinical maximum (61.2°); pronation 30° TEST AMPLITUDE | THUMB_ROM anteposition (atlas); 3D-CT TMC 37 ± 5° at opposition (30 volunteers) and Kawanishi 2017 for direction | The 3D-CT 37° is in a joint frame whose zero is not the fitted rest, so it is **not added** (review finding). Pronation magnitude is frame-dependent (unresolved). |
| Talonavicular dorsi/plantarflexion (midfoot) | total 7.39°, split ±3.7° | Fluoroscopic 3D-2D tarsal study during walking (7.39 ± 2.75°); second source: about 7° arc (Ouzounian & Shereff, method not stated) | Talonavicular inversion/eversion and rotation not used (frame not transcribed). The lateral rays stay with the cuboid in this isolated test. First TMT unresolved. |
| Knee flexion with **patellar follower** | patella flexes 0.66° per knee degree (vs femur) | In vivo lunge study (R² = 0.992), cadaver study agrees up to 100° | The patellar translation path is not sourced; the patella rotates about the fitted knee axis. |
| Talocrural with **fibular follower** | over 30° PF → 30° DF: fibula 1.04 mm lateral, 1.03 mm posterior, vertical 0 | Roentgen stereophotogrammetry, 8 volunteers (1989) | Applied linearly (shape unsourced). Rotation is unquantified, so not applied. A textbook's proximal-migration claim conflicts. |

**Run 014** (`audit/runs/isolated_bone_only_014`, test file `…isolated_tests_v14.blend`, sha256 `46db1e81…`; 135 tests including the talonavicular pair):
- **Integrity:** 135/135 tests pass. Every channel is measured. Angle error ≤ 5.6e-5°, centre drift ≤ 1.9e-7 m, off-axis ≤ 3.8e-5° (patella off-axis now gated).
- **Mirror:** 41 of 43 pairs pass on reflected world transforms of every commanded bone, followers included (max 1.1e-6). The 2 hip-rotation pairs are covered by the solver mirror test.
- **Followers:** patellar flexion reaches 59.4° at 90° knee flexion (ratio 0.660). The fibula moves 0.52 mm laterally and 0.515 mm posteriorly at 30° DF, with fibular rotation gated to zero. Follower errors are ≤ 2e-5° and ≤ 7e-9 m, and a follower without its error key fails as unmeasured.
- **Source binding:** every new spec has an absolute world-direction assertion. Six sign mutations (rib, finger, opposition, patella, fibula, C0–C1) each fail the suite. One weak assertion (patella) was found by mutation and strengthened. `SupplementarySourceBindingTests` checks that amplitudes come from the source file and that unresolved items stay untested.

**Gate refinement (runs 008 → 012).** Run 008 failed 18 thoracic tests on the distal-marker travel floor of 0.5 mm. Each failing marker sat 26–34 mm from the rotation centre, but the sourced amplitudes are only ±0.95–1.05°. The floor exists to catch markers that are not carried by the moving bone or that sit on the rotation axis. It is now an amplitude-independent **lever arm**: peak travel ÷ peak primary angle ≥ 10 mm. A static or on-axis marker still gives zero. The independent review then showed that dividing *total* travel by the *primary* peak let secondary channels supply the travel (forearm rotation at 90° elbow got its lever from the flexion). The lever is now measured only on frame pairs where the primary command changes while every other authored channel is held. Two kinds of channel do not need holding: chain channels keyed as a fixed multiple of the primary (digit chains), and chain joints distal to the marker's carrier bone (the thumb IP cannot move a marker on the proximal phalanx). Run 010 failed the digit chains under the stricter rule, and run 011 failed thumb flexion. Both are kept as recorded runs, alongside 008. In run 012 all 132 tests with a distal marker had a primary-specific lever of at least 11.0 mm (TMJ has none and is gated by its glide direction). Run 013 added the talonavicular pair, and both sides failed the radius-constancy check (0.34 mm). That check measured from the primary marker, which here sits about 30 mm off the rotation axis. For fixed-axis rotations with an off-centre primary marker, the invariant is the distance to the commanded rotation centre, and the check now uses it. Run 014: every radius is constant within 3.6e-7 m. Run 013 is kept as a recorded run.

**Thumb opposition outcome (functional, not gated).** With abduction (to the clinical anteposition maximum) and pronation only, the thumb-tip-to-little-finger-MCP distance rises from 134 mm to 142 mm. In this hand the thumb already sits anterior and palmar of the index ray, so palmar abduction lifts it further from the palm. Reaching the little finger also needs TMC flexion and MCP/IP flexion. Their magnitudes at opposition are not in the accessible sources (the relevant snippet's labels were garbled), so **full opposition remains unverified**. These tests verify the two sourced or labelled components and their directions only.

**New finding F-RIB-001.** Ribs are fitted as straight head-to-anterior-end segments, and the costotransverse marker is placed 12% along that line. The anatomical rib-neck axis (costovertebral → costotransverse) is therefore collinear with the rib, and rotation about it moves nothing. A pump-handle component is tested about the mediolateral axis through the rib head instead. Proper rib-neck axes need curved-rib geometry or a sourced axis orientation (Beyer reports similar axis orientation at every level, but the values are not accessible).

**Still unresolved (no values invented):** L1/L2; C2/C3 and C7/T1 control values; SC elevation (sources span <10° to 13°, with 25–28° in another method); first TMT (one approximately 3° quotation with an unstated method), naviculocuneiform, calcaneocuboid and lesser toes; talonavicular inversion/eversion and rotation; ribs 8–12; thumb pronation magnitude and the TMC/MCP/IP flexion needed to complete opposition; patellar translation path; fibular rotation; wrist stage split.

Clips: `audit/review/isolated_clips_007/`, rendered from the run-012 test file (`isolated_clips_006` used the superseded run-009 opposition): C0–C1, C3/C4, rib 4, index and little-finger spreading, thumb opposition components, and knee with the patellar follower. The fibular translation (0.5 mm) is below render resolution and has no clip.

### Third independent review (of the newly sourced tests) and corrections

| Finding | Re-check | Correction | Verification |
|---|---|---|---|
| **Opposition overshoot.** 37° added to a rest already at 37.3° anteposition gives 78.8°, beyond the sourced 61.2°. | Reproduced: 78.8°. | Abduction is driven (by bisection) until the anteposition reaches 61.2°; the measured peak is gated against it. | Run 012 peak: 61.200°. A unit test checks both sides. |
| **Lever gate could credit a secondary channel.** | Confirmed by reasoning: forearm rotation at 90° elbow had a 0.244 m lever. | Primary-only segments, with the proportional-chain and distal-joint exemptions. | Forearm rotation lever is now 23.8 mm, from pronation alone. |
| **Patella off-axis not gated; a missing follower error could pass.** | Confirmed. | Off-axis added to the gate; follower error keys are required. | Run 012. |
| Patella twist measured about the posed axis, where the rest axis is correct. | Confirmed (equal only while the femur is static). | Uses the rest-frame axis. | Unchanged results (femur static). |
| Weak or non-independent direction assertions (thumb pronation, ribs, fibula, MCP abduction). | Confirmed. | The pronation check is now independent: the pulp must turn toward the little-finger MCP. The other limits now scale to the expected motion. | Mutation of the opposition, patella and fibula signs fails the suite. |
| Fibula arc typed in. | Confirmed. | Arc read from the source file (`arc_deg`); the binding test checks the sweep against it. | Unit test. |
| Fibular rotation unchecked; the whole fibula translates although only the distal fibula was measured. | Confirmed. | Rotation gated to zero; proximal-fibula motion recorded as unsourced. | Run 012. |

## 2026-10-08 live continuation — target preflight reconciliation

Live starting commit: `bbdfd4cbd51353be8430220c29a5b98c3a01de83`. Newer shoulder, radius, C2, P1 spine, pelvis and hyoid work is preserved. A live validator failure was reproduced: it still required the abstract-only withdrawal state after the newer full-text check had restored a separately reported AC–acromion distance. The source Results paragraph independently confirms 34±8 mm (23–52 mm), and the validator now requires the full-text record and checks agreement between source, constraints and selection. It continues to reject STSL subtraction and treating the distance as transverse equality. The measured posterior AC aspect is not automatically the AC joint centre. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC13184462/.

Adversarial checks: missing full-text record, substituted 77 mm STSL measurement, transverse equality and NaN shoulder length all fail. Canonical subset: 39/39 tests; complete atlas validator: 206 bones/427 articulations, 30 semantic frames and 44 mechanics profiles, no structure/classification errors. This is preflight/inventory verification, not anatomical target acceptance.

Other reproduced baseline discrepancies corrected: readiness had eight PARTIAL regions but reported seven; a foot regression expected superseded terminology while the corrected source-conflict conclusion remained intact. Full Python baseline: 658 tests, eight failures and four errors. Three canonical failures were addressed here; nine legacy production/recovery failures remain outside this skeleton-only change (execution-orchestration live recovery phase, production-control freeze/regression fixtures and candidate-status terminology). They must not be represented as a green whole-project suite. No production geometry, weights, runtime drivers or a003 asset changed.

## 2026-10-08 measured scapula continuation

**PROVISIONAL:** Added a source-bound relative 29-landmark scapular envelope from Lee/Lawrence/Rainbow 2024 (dataset DOI 10.5683/SP3/PHVS3D; paper DOI 10.1111/joa.14124). The raw workbook, SHA256, source endpoint mapping and recomputable direct stature regressions are committed. Coverage: 125 subjects, 45 male; the asymptomatic/no-full-thickness-tear male subgroup has 34 subjects, 33 with stature. At the current ~182 cm stature, that subgroup predicts superior-to-inferior angle distance ~167.16 mm and medial spine to exterior acromial angle ~129.23 mm. These are provisional measurements, not frozen joint coordinates.

**CONFIRMED source-definition correction:** The 2022 scapular study d1 measures glenoid tubercles rather than articular rim endpoints; d6/d7 are projected distances along a reference line rather than direct chords. Exact endpoints remain distinct. No averaging with incompatible definitions, or substitution of the interior acromial angle to force agreement, is permitted.

Verification: 13 scapular tests, 44 canonical tests and atlas structure validation pass. Tests reject reflection/chirality errors, degeneracy, missing/duplicate IDs, nonfinite values and extrapolation; rigid coordinate invariance and committed report reproduction are checked. Workbook A1-only dimension metadata was independently found incorrect; actual cells give complete coverage. Live Blender 5.2.1 LTS bpy adapter: 22 synthetic checks pass. Bilateral sparse-landmark save/reload: 58 points, max coordinate error 5.58e-9 m. Evidence: `ORIGINAL_V1_WORK/anatomy/audit/runs/work_bpy_preflight_20261008_001/`. Initial Blender harness failure from a stale RNA pointer is retained and corrected; it changed no anatomy.

**BLOCKED exact shoulder freeze:** Absolute SC/AC/GH centres, thorax-relative neutral scapular pose and endpoint-matched independent confirmation remain required. The glenoid shallowest point is not a GH sphere centre. The safest next action is resolve these mappings and constraints using the measured envelope. Gate 6 remains open, and no new canonical skeleton/production mesh is created.

## 2026-10-08 lumbar semantics, rib validator and radius recheck

**PROVISIONAL:** P1 now has six superior-endplate orientation frames, S1 through L1. The retrieved original source Figure 5C confirms superior-to-superior segment angles. They include the upper vertebral body wedge plus intervening disc; using the entire angle as a disc-only wedge would double-count body shape. Frame/sign tests give S1 slope +40.9° and L1 slope −15.5°, consistent with provisional 56.4° total lordosis. Absolute centres and inferior endplates remain undefined. The legacy KIM_2022 source identifier is retained, while the DOI/title and PDF attribution are explicitly recorded. Source: https://d-nb.info/127884676X/34 (Figure 5, printed page 6).

**CONFIRMED validation weakness:** Rib demographic evaluator accepted NaN/Infinity predictors and could silently truncate malformed coefficient lists through zip. A failing mutation test reproduced it; finite predictor/coefficient/result and exact five-term checks now reject those inputs. Six rib tests pass. Source parameters are unchanged, and no age/weight is silently selected. Full curved ribs remain blocked on the unambiguous proximal Eq 2.18 branch constraint; three University of Michigan source routes returned HTTP 403.

**STRONGLY SUPPORTED:** Direct ANSUR radius regression independently recomputed from the committed 4,082-man dataset and matches the stored report within 1e-9. The a003 proxy is ~30.72 mm below the stature-conditioned prediction. Ulna dimensions are not inferred. The report-builder default pointed to a missing surface filename; corrected to the existing character_surface.json and verified by the recomputation.

Verification: 48 canonical, 13 scapular and six rib tests pass. Full Python discovery: 685 tests, five failures and four errors, all in the previously identified production/recovery fixtures; retained output at `ORIGINAL_V1_WORK/anatomy/audit/runs/work_bpy_preflight_20261008_001/python_suite_685_tests.txt`. Region-specific essential targets and safest next actions are recorded in `target_blockers.json`. Gate 6 remains NOT FREEZE READY; Gates 8/9 are not accepted. Blender is available, but a new canonical candidate must wait for the essential numerical geometry.

## 2026-10-08 clavicle endpoint cross-check

**STRONGLY SUPPORTED context; exact target still open:** Qiu et al. 2016 (PMC4819086, DOI 10.1155/2016/6219761) independently reports male clavicular articular-surface-centre chord 152.9±9.3 mm. This is more directly mapped to the desired bone endpoints than an extremal-point length, but it is not an instantaneous rotation-centre measurement. The sample has 26 men with bilateral bones, and no stature regression; its mean is not promoted into the canonical skeleton. It remains separate from 154.8 mm extremal chord and 166.8 mm true centreline evidence. Source semantics and cross-check: canonical_clavicle_endpoint_crosscheck_v1.json.

SC anchor search: Li 2012 PMID22340551 measured bilateral clavicle separation, but the accessible abstract omits the required value and endpoints. Tuscano 2009 PMID19308406 reports joint-space/head-diameter/offset variability, not SC-centre breadth. Wijeratna 2013 PMID22933016 concerns joint-plane orientation. None justifies substituting maximum manubrial width for SC-centre breadth. Need the endpoint-matched full table/figure or independent articular landmarks before exact placement.

## 2026-10-08 Work Blender recheck and Claude inspection handoff

Fresh Blender 5.2.1 LTS bpy run: unchanged a003 master, 135/135 implemented isolated integrity tests pass; 41 mirror pairs pass and two remain SOLVER_TEST (43 total). Source SHA256 before/after matches and the frame is restored. This is repeatability/implementation evidence for the diagnostic baseline, not acceptance of canonical proportions or all contact/follower mechanics. Compact per-test evidence, hashes and explicit mirror statuses: `ORIGINAL_V1_WORK/anatomy/audit/runs/work_bpy_baseline_recheck_20261008_001/`.

Eight independent distal-spiral tests pass: all 12 source mean endpoints, derivative-zero peak check, analytic circular special case, no loops, physical scale, arc/chord distinction, sampling consistency and nonfinite/bad sample rejection. Failure before correction retained: nonfinite physical span was accepted, and noninteger sample count raised the wrong exception. Source-mean distal segments are now reproducibly exported. No reference age/weight is selected, and no full proximal rib is claimed. Live bpy non-bone curve save/reload checks 24 bilateral distal curves, 101 points each, 7.44e-9 m maximum coordinate error, zero bilateral reflection error, and no costotransverse permission for ribs 11/12.

Prepared independent review handoff: `docs/CLAUDE_WORK_SKELETON_INSPECTION_HANDOFF_20261008.md`. Gate 6 remains open; no new canonical skeleton or corrected-skeleton renders are presented. Production geometry, weights and drivers unchanged.

## 2026-10-08 adversarial carpal-axis verification

Existing unit-length and mirror checks could accept seven identical proximal lines, despite failing every non-zero source angle. Added a separate projection validator: sagittal palmar-positive and coronal ulnar-positive angles must be recovered from each bilateral XYZ line. Four tests reject mirrored/unit stubs, palmar sign reversals, side swaps, missing vectors and NaN; existing vectors pass. Numeric targets are unchanged. This checks source-frame arithmetic, not contact geometry.

Evidence independence guard: the 2021 and 2023 normal alignment reports both describe 121 asymptomatic wrists. Until subject provenance proves otherwise, treat them as a potentially shared cohort rather than two independent replications. The 2023 publisher abstract independently confirms the angle signs and geometric-versus-articular-normal axis definitions. Absolute carpal centres, pisiform orientation and contact layout remain open. Primary: https://journals.sagepub.com/doi/10.1177/17531934231160100.

## 2026-10-08 lumbar body/disc orientation continuation

**PROVISIONAL:** Bailey et al. 2016 (DOI 10.1111/joa.12451, Methods/Table 2) supplies separate male body wedge angles, with standing disc angles retained as context. P1 now has five inferior endplate frames and five derived disc wedges alongside the six superior frames. Body + disc closes each superior-to-superior segment, without assigning the entire segment to the disc. The source reports standard errors, not population SD; no corridors are fabricated. Pooled body means plus standing disc means leave a 0.50° source closure residual because the subsets differ; this is preserved. Derived P1 disc angles are explicitly cross-cohort provisional calculations, not the source's standing means or a measured individual.

**CONFIRMED coordinate convention:** +X left, +Y posterior, +Z superior. Positive body lordosis is inferior slope minus superior slope. An independent anterior-taller trapezoid checks this sign; body L1 is kyphotic, so its inferior plate slope is −19.56°, not −11.44°. No absolute centres or thickness/contact placement are inferred.

**REOPENED source review:** The 2026 lumbar CT paper text states 50 men/50 women, while Table 1 counts total 46/54. Its width definitions also mix mid-sagittal language, lateral-edge language and a later reference to mid-coronal planes. Existing height means remain available as provisional context; no AP/ML width target is frozen. Machine-readable review: `canonical_lumbar_ct_source_review_v1.json`. Need independent endpoint-matched height/envelope corroboration or author clarification before freezing these dimensions.

Verification: 60 canonical tests plus 27 scapula/rib tests pass (87 total). Atlas remains 206 bones/427 contact complexes; source target selection and carpal projection validators pass their limited scopes. Blender 5.2.1 LTS save/reload checks 11 local orientation fixtures, maximum matrix error 5.96e-8, maximum determinant error 1.79e-7. No canonical candidate is created. Evidence: `audit/runs/work_bpy_lumbar_orientation_20261008_001/verification.json`; reproducible command in its README. Gate 6 and Gates 8/9 remain open. Production mesh/weights/runtime unchanged; engine checks remain deferred per owner priority.

## 2026-10-08 independent lumbar edge-height cross-check

**PROVISIONAL:** Added Hegazy/Hegazy 2014 primary full-text male MRI data (46 men, age 25–57; DOI 10.1155/2014/370852). Anterior/posterior body heights and separate anterior/posterior disc gaps are stored with endpoint definitions, distinct from CT central body heights and three-point mean disc heights. The MRI posture is supine with hips/knees flexed; disc heights cannot silently become standing geometry. No AP depth is inferred, so height differences do not uniquely determine angular wedges. Source data: `canonical_lumbar_edge_height_crosscheck_v1.json`.

**CONFIRMED source statistic inconsistency:** Table 4 prints L1 male posterior mean 26.30 mm and SD 26.30 mm, with observed range 20–30 mm. For n=46 the maximum possible sample SD is about 5.06 mm. The printed SD is preserved separately, the usable SD field is null, and no guessed correction is made. Other source-table statistics are not blanket accepted. A new necessary statistical consistency checker uses a bounded-variance test with the sample correction; it rejects impossible SD, nonfinite values, reversed ranges and bad sample counts. Passing this check alone does not prove anatomical validity.

Verification: 60 canonical, 27 scapula/rib and five statistical source tests pass (92 total). Current freeze-readiness records the new provisional lumbar orientations and independent edge-height evidence while retaining all essential global geometry blockers. Gate 6 remains NOT FREEZE READY. Existing Blender master, production mesh, weights and animation drivers unchanged. Need standing/contact/normal-height reconciliation, independent matched angle/envelope confirmation, and resolution of CT2026 source inconsistencies before placing lumbar centres.

## 2026-10-08 independent lumbar angle sensitivity and source identity audit

**STRONGLY SUPPORTED wedge pattern; exact target PROVISIONAL:** Been et al. 2007 primary Methods/Table 1 (DOI 10.1002/ar.20607) provides independent standing, same-body endplate-angle evidence: 106 adults, 56 men/50 women, radiographically normal clinical cohort, age 20–50. The pooled-sex wedge pattern supports upper lumbar kyphosis, near-neutral L3 and lower lumbar lordosis. These definitions match body wedges rather than full segments. Two source-separated P1 constructions are stored in `canonical_lumbar_orientation_sensitivity_p1.json`. Their inferior slopes differ by at most 1.06°; no averaging or numerical freeze occurs. This difference of means is not population SD or an uncertainty bound. Source: `canonical_lumbar_wedge_independent_crosscheck_v1.json`.

**CONFIRMED source identity correction:** CLAVICLE_CADAVER_3D_2013 and DARUWALLA_2013_CLAVICLE_3D share PMID24142486/DOI10.1002/ca.22288. Primary publisher metadata identifies Bernat et al.; the Daruwalla attribution was wrong. Both legacy IDs remain for compatibility, but count as one publication. Registry scan finds four bibliographic alias groups across clavicle, tarsal and rib evidence: 105 records map to 101 identifier groups. That count does not establish independent cohorts; missing identifiers and repeated cohorts across separate papers still require review. All four groups are explicitly guarded against double counting in the register. Numeric geometry and confirmed clavicle defect direction are unchanged.

Verification: 63 canonical tests plus 37 source-statistics/source-identity/scapula/rib tests pass (100 relevant tests). Live Blender 5.2.1 LTS checks 22 local endplate orientation helpers across both families, save/reload matrix error 5.96e-8 and determinant error 1.79e-7. No absolute centres or candidate skeleton created. Evidence: `audit/runs/work_bpy_lumbar_sensitivity_20261008_001/verification.json`. Source selection/atlas validators retain 206 bones and 427 articulations; Gates 6/8/9 remain open. Exact shoulder SC-centre breadth and full clavicle curve definition still lack essential compatible evidence; publisher abstract retrieved, Antwerp PDF routes returned 403 and Ghent copy is institution-restricted. Safest action is recover source endpoint/curve data or compatible independent landmarks, without inferring absolute joint positions from a surface width.

## 2026-10-08 measured glenoid rim orientation

**PROVISIONAL:** Derived a least-squares glenoid rim plane from the measured Lee2024 LM15 inferior, LM16 posterior, LM17 anterior and LM18 superior landmarks. The 34 asymptomatic/no-full-thickness-tear male subject orientations are retained as statistical context; the stature-conditioned mean-shape frame is separate. Report: `canonical_glenoid_rim_frame_v1.json`. Its centroid is the arithmetic rim-landmark centroid, not the humeral-head/GH centre. SC/AC/GH coordinates remain null. The predicted rim plane residual is 1.574 mm; nonplanarity is recorded rather than hidden. Projection angles are in this measured scapular basis and must not be compared directly with clinical version/inclination definitions.

**CONFIRMED bilateral frame convention:** Right first tangent is anterior; left first tangent is posterior so both pose rotations have determinant +1 while their outward normals and point geometry reflect correctly. Left anatomical anterior is negative first axis. Improper reflections are not used as rig rotations. Source-coordinate shape is still unposed relative to the thorax.

**CONFIRMED adversarial validation weakness and correction:** An isotropic four-point tetrahedral rim has no unique least-squares plane, but the initial fitter accepted an arbitrary normal. The failed mutation test is retained at `audit/runs/work_bpy_glenoid_rim_20261008_001/ambiguous_plane_before_fix.txt`. A smallest-singular-value separation check now rejects it. Seven tests cover analytic signs, tilt/translation covariance, rank deficiency, NaN, mirror/chirality errors, nonplanarity, proper bilateral frames and exact report reproduction.

Verification: 70 canonical plus 37 source/scapula/rib tests pass (107 total). Blender 5.2.1 LTS bilateral relative-rim helper save/reload: max matrix error 1.01e-7, determinant error zero, reflected centroid error zero. Evidence: `audit/runs/work_bpy_glenoid_rim_20261008_001/verification.json`. No canonical candidate, global shoulder pose or GH sphere is claimed. Exact SC-centre breadth, neutral scapular thorax pose and GH contact/sphere geometry are still essential blockers; need compatible primary landmarks/mechanics before global placement. Gates 6/8/9 stay open; production mesh, weights and runtime drivers unchanged.

## 2026-10-08 continuous endplate clearance and finite shoulder invariants

**CONFIRMED geometric validation requirement:** A positive disc-centre gap is insufficient. Two tilted planes can intersect inside an elliptical endplate footprint even when the centre and four cardinal rim points all have positive gaps. Added an analytic minimum over the entire caller-supplied common ellipse, with an explicit minimum witness and strict nonzero clearance. Measurement is HGPT +Z projection, not nearest-point/normal distance. It applies only to planes over an established common footprint; actual curved endplate surfaces and coverage remain required.

**PROVISIONAL diagnostic only:** 90 explicitly synthetic footprint/gap cases across the two provisional P1 lumbar orientation families expose six intersect/touch cases. These sweep radii and centre gaps are neither anatomical population means nor selected targets. No vertebral centres are inferred from them. Report: `canonical_endplate_clearance_sensitivity_v1.json`. Eight tests include independent dense-boundary verification, tangency, normal scaling, nonfinite/vertical/overflow rejection and exact report reproduction.

**PROVISIONAL source surface context:** Wang/Battié/Videman 2012 primary publisher abstract (DOI 10.1007/s00586-012-2415-8; 591 endplates from 76 male spines) supports asymmetric concavity. Its cranial/caudal labels are relative to the DISC: cranial means the upper vertebra's INFERIOR plate; caudal means the lower vertebra's SUPERIOR plate. Pooled mean depths 1.5/0.7 mm are recorded as context, not assigned to individual levels. Level-specific table/footprint and height definition remain essential. See `canonical_lumbar_endplate_surface_semantics_v1.json`.

**CONFIRMED shoulder validator weakness and correction:** Existing chord helper could accept an infinite curved length and coincident SC/AC endpoints; other measurement helpers could return NaN. Three failing tests are retained at `audit/runs/work_endplate_clearance_20261008_001/shoulder_invalid_before_fix.txt`. Finite numeric inputs are now required, collapsed chords fail, malformed/nonfinite endpoint predicates return false, and normal valid geometry is preserved. This changes validators, not target values or a003 geometry.

Verification: 78 canonical + 37 source/scapula/rib + 10 shoulder constraint tests pass (125 affected tests). Independent Blender 5.2.1 LTS mesh fixture: six synthetic planar surfaces, 128 rim points each, max coordinate error 4.38e-10 m. Mesh minima independently give intersection −0.656854 mm, separated +6 mm and tangency 0 mm. Report: `audit/runs/work_endplate_clearance_20261008_001/blender_verification.json`. The anatomy atlas/target validators retain their limited accepted scopes; Gates 6/8/9 remain open. New canonical skeleton and production geometry/weights/runtime remain unchanged. Actual endplate envelopes, source-compatible standing gaps and continuous curved contact clearance block global spine placement.

## 2026-10-08 hyoid axis correction and current dependency reconciliation

**CONFIRMED source mapping error:** Primary Abdelkader2025 Table 1 (DOI 10.1038/s41598-025-85518-w) defines CC-prime as AP body thickness, while Figure 1A shows the BB-prime minor axis vertically across the body. The existing provisional `body_AP_length=11.32` was an incorrect label. Source values are preserved; explicit local body extents are X width 24.3, Y AP thickness 6.99 and Z minor-axis height 11.32 mm. A neutral body tilt is not inferred from these population means. Historical source keys and the 6.99 generic thickness alias remain with explicit semantics. The failing pre-fix regression is retained in `audit/runs/work_hyoid_axis_review_20261008_001/hyoid_axis_before_fix.txt`.

**PROVISIONAL:** Six Blender dimension markers reproduce these axis extents after save/reload with maximum span error 4.35e-7 mm. These are a dimension fixture, not a whole hyoid, landmark envelope, global pose or canonical candidate. One unpaired reference bone and no osseous parent are preserved. Independent matched geometry/stature context, body/cornu landmarks, neutral tilt and canonical cervical placement remain open; C3 level alone does not fix AP position.

Current implementation specification/readiness/selection now reflect existing measured scapular/glenoid frames, verified distal rib segments, independent lumbar wedge context and provisional hyoid dimensions. Earlier subtraction-based AC inference remains rejected; the later direct full-text 3D distance remains available with its endpoint restrictions. These updates remove stale descriptions of missing work without clearing numerical freeze or contact/placement blockers. Hyoid overall D grade is retained pending complete independent geometry review.

Verification: 79 canonical + 47 source/scapula/rib/shoulder tests pass (126 relevant tests); target-selection, atlas and carpal projection validators pass their limited scopes. Current freeze_ready=false, Gates 6/8/9 remain open, production geometry/weights/runtime and a003 unchanged. No new corrected skeleton render is claimed. Primary PDF checked at Table 1/page 3, Figure 1/page 4 and Results/page 6; source review stored beside the hyoid values. Details/hashes: `audit/runs/work_hyoid_axis_review_20261008_001/`.

## 2026-10-08 target-selection gate adversarial continuation

**CONFIRMED validator defects corrected:** Unsupported, empty or missing evidence grades could falsely pass a synthetic otherwise-unblocked freeze check; nonboolean falsy freeze flags were accepted; malformed shoulder values raised TypeError rather than reporting rejection. The gate now requires a literal boolean, explicit A/B evidence leaves for freeze, and finite positive measurements before comparisons. C/D, unknown labels, empty collections and missing grades cannot justify freezing. Synthetic test fixtures are not anatomical target data. No target value or production geometry changes.

Verification: 82 canonical + 47 source/scapula/rib/shoulder tests pass (129 relevant tests). Full discovery: 740 tests, five failures/four errors, exactly the same named legacy production/recovery failures as the earlier 685-test checkpoint. No whole-project green claim; raw traces and per-name comparison retained in `audit/runs/work_target_gate_mutations_20261008_001/`. Target-selection/atlas/carpal-axis validators pass their limited scopes; 206 bones/427 articulations retained, freeze_ready=false. Gates 6/8/9 and new canonical skeleton construction remain open.

**BLOCKED exact shoulder SC anchor:** Li2012 PMID22340551 primary abstract omits bilateral clavicle distance value and precise endpoints. PubMed-linked Ovid full-text route was checked and returns HTTP402 Payment Required. Need accessible primary full table/figure or independent endpoint-matched SC articular landmarks before absolute SC/AC placement. No surface width or manubrial outer breadth is substituted. Other region-specific evidence/contact dependencies remain in current readiness; independent validation work continued despite this evidence blocker.

## 2026-10-08 checkpoint plan

A reviewable checkpoint ladder now records the baseline, regional target closure, machine-readable preflight, new immutable Blender revision, visual review, contact/follower acceptance, isolated movement, exercises and downstream production/app stages. See `docs/superpowers/plans/2026-10-08-skeleton-verification-checkpoints.md`. Current position CP1/Gate 6; no numerical target, anatomy gate or production permission is promoted by this planning update.

## 2026-10-08 independent review of Claude's 21 recent commits

Reviewed live HEAD `6570e750fdf0b6fbd899b3ab594ba1a84bd248e4`; all newer work is preserved. Details: `docs/GPT_REVIEW_OF_CLAUDE_RESULTS_20261008.md`. CP2 ledger covers all 206 bones and catches a003's zero disc gaps; CP3 builder rehearsals and source-register corrections are useful within their limited scopes. They do not close CP1 or create an accepted canonical skeleton.

**CONFIRMED validator weaknesses:** collapsing C3 crashes CP2 with division by zero; an unknown non-root parent-relation type passes; tiny positive disc planes 100 metres away from the candidate pass clearance. The axial specimen report also checks fitted planes over a partial footprint rather than full curved endplates. Read-only adversarial fixtures/results are retained in `audit/runs/work_claude_review_20261008_001/`; these implementation weaknesses remain unresolved at this review checkpoint.

**REOPENED measurement claim:** Claude's review again compares oblique GH-to-inferior-angle span with vertical scapular height. That does not establish a matched numerical scapular shortening target. The existing corrected shoulder audit remains authoritative; clavicle rebuild is still justified. Forearm shortness is strongly supported, but exact radius/ulna endpoints remain open. The de-Leva-only thigh-shortness claim was withdrawn; three recalled de Leva values still need primary-table verification.

Verification: 52 focused tests pass. Full discovery runs 787 tests with five failures/four errors; all nine names match the retained pre-Claude baseline. Static target/atlas validators pass within scope with `freeze_ready=false`, 206 bones, 427 articulations and 30 frames. Blender run-002 results were reviewed as archived observations, not freshly rerun; its raw captures/.blend were not retained. CP1 remains PROVISIONAL/BLOCKED, CP2 needs validation repair and anatomy closure, CP3 remains a builder rehearsal, CP4 is blocked. Gates 6/8/9 and Phase 10 remain open/deferred. Production geometry/weights/runtime and a003 are unchanged.

Next safe action: fix and adversarially test CP2 rejection/geometry binding, then continue CP1a source-compatible shoulder mapping and regional target closure; fresh Blender rehearsal with retained captures precedes a new immutable canonical candidate.

## 2026-10-08 CP2 adversarial repair checkpoint

**CONFIRMED fixes:** Degenerate vertebral disc participants now return failure instead of division by zero; unknown/malformed parent relations reject, with explicit root/carrier constraints preserving existing valid relations. Malformed plane entries return rejection. Positive plane-only clearance is now UNVERIFIED for actual endplates, with diagnostic gaps retained; a remote tiny footprint cannot yield structural acceptance. This is a scope correction, not completed curved-contact validation.

Before-fix failing regressions and after-fix adversarial observations are retained in `audit/runs/work_cp2_repair_20261008_001/`. 27 affected tests pass; full discovery runs 792 tests with the same named five failures/four errors as the preceding 787-test review. Target-selection/atlas validators pass within their static scopes; freeze_ready=false. Actual candidate-bound endplates, full footprints and surface error bounds remain unresolved. CP1/CP2 anatomy acceptance and Gates 6/8/9 remain open. a003 and production geometry/weights/runtime are unchanged.

## 2026-10-08 fresh Blender rehearsal and CP1a source-frame correction

**CONFIRMED build-path verification:** Blender 5.2.1 LTS restored via Python 3.13. Fresh empty-scene a003-data and mirrored-copy builds retain 206 bones/427 markers; both fresh-process captures pass round-trip comparison. Marker-position error is below 2e-7 m; exactly mirrored roll difference 0.027 degrees. All 135 isolated implementation tests pass on the new builder output; 41 Blender mirror pairs pass and two side-specific-amplitude pairs remain solver-only checks. Retained raw captures, both rehearsal .blend files, input fixtures, movement report/samples and hashes: `audit/runs/work_cp3_independent_20261008_001/`. This is an a003-data rehearsal, not corrected anatomy or Gate 9 acceptance.

**CONFIRMED source mismatch corrected:** Historical shoulder vector paired medial/lateral-extrema clavicle length with ventral/dorsal-extrema standing angles; surface landmarks were being treated as articular centres, and pooled data lacked male context. The vector/sweep numbers are preserved as illustrative history and their current states are reopened/ineligible for freeze. Matsumura2020 male data and precise definitions are now source-registered. Proper IJ/C7/PX/T8 source-point mapping is implemented and tested; it does not select global landmarks or transform clinical Euler angles. Tilted Blender fixture errors are below 2.1e-8 m / 3.6e-8 frame components. See `audit/runs/work_shoulder_source_frame_20261008_001/`.

Verification: 25 focused tests pass; full discovery 796 tests with the same named five failures/four errors. Static target/atlas validators retain scope and freeze_ready=false. CP1 numerical closure still requires endpoint-compatible SC/AC surface-to-articular mapping, canonical thorax pose and independent/stature context. CP2 actual curved-contact validation remains open. CP3/CP4 corrected-candidate acceptance and Gates 6/8/9 remain open; Phase 10 is deferred. a003, production geometry/weights and runtime remain unchanged.

## 2026-10-08 CP1a clavicle-shape statistics and SC-contact review

**CONFIRMED source-statistics conflict:** Fontana2020's printed pooled height/clavicle correlation 0.968 is incompatible with its reported subgroup/overall summaries if they describe the same paired sample. A conservative covariance bound, including printed-mean rounding and the full observed height range, is 0.691416 (below 0.692 with correlation rounding). Primary Figures 5/6 were inspected. The printed statistic is quarantined; no guessed replacement, inverted height-on-length fit or 1.82 m target is selected. Projected curvature radii and conoid context are retained with explicit endpoint, ratio-direction and unit limitations in `canonical_clavicle_shape_source_review_v1.json`.

**PROVISIONAL contact evidence:** Languth2024 MRI provides AP clavicular diameters, not bilateral SC-centre breadth; Table 1 interreader ICCs below .001 to .154 prevent precision target use. Lee2014 primary dissection distinguishes whole osseous end, anteroinferior cartilage patch, first-costal-cartilage contact and intra-articular disc; pooled disc thickness is not a uniform joint gap. See `canonical_SC_contact_semantics_v1.json`. Three source records added; identity scan retains five alias groups. Qiu's mean/SD remain unchanged; the unsupported claim that per-bone SD necessarily understates between-person SD is removed.

Verification: 21 affected tests pass; nine statistics tests also pass under Python 3.13. Full discovery: 800 tests, same named five failures/four errors as previous 796-test checkpoint. Source hashes, before-fix traces, a corrected analytic-test fixture mistake and transient annotation failure remain in `audit/runs/work_shoulder_shape_review_20261008_001/`. Static target/atlas validators retain scope and freeze_ready=false, 206 bones/427 articulations/30 frames. Exact SC articular anchors, matched stature/chord evidence and neutral shoulder contacts remain BLOCKED; CP1/CP2 acceptance and Gates 6/8/9 remain open. No Blender geometry or corrected candidate is claimed; a003 and production geometry/weights/runtime remain unchanged.

**2026-10-08 CP1a follow-up:** Checked Suarez Romero2026 full primary text (PMID41659779 / PMC12876668, DOI10.1016/j.xrrt.2025.100650), including Table I from ten bilaterally dissected cadavers. Its coordinates are surgical-portal distances to capsule/neurovascular structures, not bilateral SC articular-centre geometry. Source/access hash and exclusion reason are retained; no numerical shoulder target inferred. Exact SC anchor remains BLOCKED by essential endpoint-matched primary coordinates. Safest next action remains contact-patch/manubrial landmark acquisition rather than substitution of an unrelated distance.

## 2026-10-08 CP3 capture rejection/metadata repair and laptop handoff

**CONFIRMED validation weaknesses repaired:** Round-trip max reductions could hide NaN endpoints/frames; invalid bone Z vectors and substituted marker frame IDs could falsely pass; missing/empty data could crash. Full finite numeric/shape/nondegeneracy/identity checks now precede calculations, with structured rejections and CLI exit 1 for failed comparisons. Extreme finite inputs that overflow the frame norm also reject; the false-pass trace is retained.

**CONFIRMED capture semantic error:** Old `frame_bone` was populated from the attachment host, mislabeling 202 marker reference frames in the fresh legacy-file recheck. Builder now stores the source `hgpt_frame_bone` separately; capture retains source frame, carrier and actual parent as distinct fields. Fresh metadata-corrected a003/mirrored rehearsals retain 206 bones/427 markers and pass storage round-trip checks; all marker attachments and centres are unchanged. Older files/reports remain archived with this scope correction. No anatomical targets, a003 file or production geometry/weights/runtime changed.

Evidence: `audit/runs/work_cp3_rejection_repair_20261008_001/`, including new .blend/capture archives, SHA256, failed runs and parent comparison. 26 affected tests pass; full discovery 805 tests, same named five failures/four errors as the preceding 800-test checkpoint. CP2 anatomy remains FAIL on known baseline defects; freeze_ready=false, Gates 6/8/9 remain open, no corrected canonical candidate or Phase 10 acceptance. Planned 20:30 BST laptop inspection/continuation handoff: `docs/LAPTOP_SKELETON_HANDOFF_20261008_2030.md`. First unfinished numerical task remains CP1a matched SC/manubrial/clavicle/contact geometry; independent regional work may continue while essential evidence is unavailable.

## 2026-10-08 primary limb-endpoint review of Claude proposal

**CONFIRMED source correction:** Recovered original de Leva1996 PDF and visually checked Table 4, plus Tables 1/2 and the estimation text. Adjusted male SJC-EJC 281.7, EJC-WJC 268.9 and HJC-KJC 422.2 mm are confirmed source means. They are Table 4, not Table 1. **434.0 mm is KJC-LMAL; KJC-AJC is 440.3 mm.** The proposal now uses the correct endpoint row (460.3 mm under its diagnostic 1.82 m proportional scaling); the old 434.0 value remains in history/source review with its actual endpoint. No shank defect or resize is selected from this single scaled mean.

**REOPENED conversions:** Primary Table 2 HJC is 3.2 mm proximal of trochanterion, differing from the proposal's 8 mm below assumption. Added an explicitly approximate longitudinal-to-vertical sensitivity near 430 mm; no global HJC change or thigh shortening is selected. Primary WJC offsets are distal to stylion, differing from the proximal ISB-midpoint sensitivity. The old all-methods-within-1-SD forearm assertion is corrected: 12 mm exceeds the unshifted 10.8 mm ANSUR residual SD. That SD also excludes conversion uncertainty. Strong forearm shortness direction remains, while numerical radius/ulna targets require matched landmarks.

Machine-readable evidence: `canonical_de_leva_primary_endpoint_review_v1.json`, regenerated `canonical_limb_length_proposal_182_v1.json` and `canonical_forearm_endpoint_decision_v1.json`. Radius and ulna remain distinct/unselected; PRUJ/DRUJ and pronation-axis contact requirements persist. Source/statute-owner rules, talus exclusion, C2 dispersion quarantine, mandible quarantine, Rausch endpoints, source aliases and hyoid corrections are preserved. This review does not undo Claude's owner-approved decisions or promote freeze_ready.

Verification: 5 limb, 5 owner-policy/source-fix and 7 source-identity tests pass; target/atlas structural validators pass. Full discovery: 805 tests, unchanged 5 failures/4 errors from the previous checkpoint; no new remaining failures. Logs and SHA256 manifest: `ORIGINAL_V1_WORK/anatomy/audit/runs/work_limb_primary_review_20261008_001/`. No numerical radius/ulna selection or anatomical gate promotion.

### 2026-10-08 independent forearm landmark review

- STRONGLY SUPPORTED: named radial/ulnar articular and surface landmarks, neutral radial-head → ulnar-head reference, and distinct DRUJ notch projection versus wrist centre are now recorded in `canonical_forearm_landmark_requirements_v1.json`. Coordinates and bone lengths remain unselected.
- Hong 2021 supplementary workbook downloaded/read without alteration. Both bone sheets contain 132 matched donor IDs; IDs imply 75 M/57 F, conflicting with manuscript 71 male/61 female. Length headers say mm2 although the paper describes linear mm. No individual stature field identified. These issues are recorded, not silently corrected or converted into a 1.82 m target.
- Adversarial geometry check: the three-point sphere-fit wording in Thillemann 2021 cannot determine a unique 3D centre without extra constraints. Three different sphere centres reproduce the same synthetic points exactly; a small residual alone must not validate an anatomical centre. No builder/production fitting algorithm was changed.
- Source register adds two primary papers; existing source aliases and owner fixes are preserved. The numerical forearm selection remains BLOCKED by matched surface/centre geometry and stature context. Evidence: `audit/runs/work_forearm_landmark_review_20261008_001/`.

Affected verification: 5 owner-policy/source-fix, 7 bibliographic identity and 5 freeze-readiness tests pass; target-data validator reports no errors with the required not-freeze-ready warning. Source register now 113 records / 108 identifier groups / unchanged 5 alias groups and 11 missing-identifier records. No movement/Blender rerun required for this evidence-only checkpoint; prior full-suite failures remain explicitly open.

### 2026-10-08 original shoulder archive acquired and C2 reread

- CONFIRMED acquisition: Seth's original Stanford archive is publicly downloadable in Work, including the generic shoulder .osim and three subject models. SC is explicitly relative to the thorax/IJ origin; source coordinates, AC constraint points and GH reference are recorded with SHA256 in `canonical_sc_primary_model_reference_v1.json`. The model download is no longer laptop-only. Anatomical target selection remains PROVISIONAL: dimensions derive from Holzbaur 2005 and are not independent 1.82 m male evidence. No global SC target or production geometry selected.
- C2 primary Table 2 explicitly labels its dispersion SD. Calling it SE is an unconfirmed interpretation. The reported sex-specific means/SDs and pooled upper range cannot coexist: the single largest measurement needs more squared residual than both group SDs permit together. Kept Claude's usable SD quarantine and extended it to the source register, which still exposed 0.66 under `sd`. Printed label/value remain beside the value. Details: `canonical_c2_primary_dispersion_review_v1.json`. No C2 height/target/stack changed.

Verification: 6 owner-policy/source-fix and 7 bibliographic identity tests pass; target validator no errors with required freeze block. Full suite 806 tests retains the same 5 failures/4 errors, no new failures. Logs/manifest: `audit/runs/work_primary_shoulder_c2_review_20261008_001/`. Anatomical gates remain open.

### 2026-10-08 source shoulder frame-transfer checkpoint

The original Seth model body basis differs by 7.8584° from its own IJ/C7/PX/T8-derived thorax frame. A direct model-XYZ → ISB mapping displaces SC by 1.28585 mm. `map_between_thorax_frames` now performs source inverse-frame then target-frame rigid transfer, without scaling. SC source-frame coordinates and reconstruction evidence are recorded; no global canonical SC target selected. Six frame tests pass. Fresh bpy 5.2.1 LTS quaternion-parent verification checks bilateral signs in a synthetic pose; no anatomical Blender candidate created. Full suite: 808 tests, same 5 failures/4 errors, no new failures. Evidence/retained failed runs: `audit/runs/work_sc_frame_transfer_20261008_001/`.

### 2026-10-08 foot source acquisition and Blender inspection

- CONFIRMED acquisition: Zenodo 3464747 metadata and eight files downloaded in Work, repository MD5 and SHA256 verified. A matched M02 left calcaneus/talus/M1/grouped-midfoot set imports in bpy 5.2.1 LTS. Download is no longer laptop-only. No anatomical master, production geometry or .blend candidate changed.
- BLOCKED contact mapping: source methods transform segments individually; native common-foot transforms are not in the four filename lists. STL physical units and this case's sex/stature are not established. The grouped midfoot represents nine named bones, but this import has eight large components plus small fragments (28 components total). Components cannot be silently counted as named bones or cleaned into a complete 206-bone target. No length/contact selected. See `canonical_zenodo_foot_source_access_review_v1.json`.
- Other acquisition recheck: Brown carpal project page is accessible but actual dataset download requires SimTK sign-in. RibSeg v2 binary pages show sign-in; public quality document lists missing/incomplete ribs and labeling exceptions. Storage shape alone is insufficient completeness evidence. Laptop actions are recorded in `audit/runs/work_zenodo_foot_source_20261008_001/carpal_rib_access_recheck.json`.

Foot source checkpoint verification: 6 owner-policy, 7 source-identity and 5 readiness tests pass; target validator reports no errors and retains freeze_ready=false. Native Blender import preserves every source float32 vertex and triangle geometry in all four STLs. Retained initial bbox-only run demonstrates the weaker check; full geometry comparison replaces it. Audit run: `work_zenodo_foot_source_20261008_001`. No canonical candidate or movement acceptance is claimed.

### 2026-10-08 laptop source-only Blender pickup

CONFIRMED source-only Blender inspection file created in `audit/runs/work_foot_source_blender_pickup_20261008_001/`: four separate Grant/Zenodo sample scenes and four visibly labelled renders. Save/reload mesh hashes preserve all coordinates/polygon indices; original source hashes retained. No rig, canonical candidate, a003 or production changes. Units/common pose/contact centres remain UNVERIFIED. The owner can inspect actual acquired source geometry on the laptop without mistaking it for the rebuilt skeleton. Li 2012 full-table retry: publisher routes returned 403/402; bilateral-clavicle numerical distance and endpoint definition remain BLOCKED. Abstract joint spaces cannot supply SC-centre breadth.

### 2026-10-08 hyoid landmark semantics reopened

CONFIRMED primary figure/text endpoint conflict recorded in `canonical_hyoid_landmark_semantics_review_v1.json`. Figure 1B marks D/E at free horn tips and Dprime/Eprime near the body; the source table calls Dprime-Eprime a posterior-end span. Printed values remain preserved, but unresolved posterior-end and centre spans are removed from provisional coordinate nominals. GGprime is not a proven volume-centroid span. Do not bend horns to reproduce these marginal means. Whole hyoid geometry remains PROVISIONAL; existing corrected body axes and one suspended-bone topology retained. The old local READY wording is removed.

Verification: new semantic regression fails against the preceding target despite six old tests passing. After correction, 37 affected tests pass; full 809-test suite has the same 5 failures and 4 errors as baseline. Target validator has no errors and retains freeze_ready=false. Logs and hashes: `audit/runs/work_hyoid_landmark_semantics_20261008_001/`. No coordinates, a003, production, Blender candidate or movement acceptance changed.

### 2026-10-08 original rib thesis obtained; printed notation conflict retained

CONFIRMED original Holcombe 2016 thesis acquired through the university's current advertised bitstream (24,996,572 bytes, SHA256 recorded). The old legacy route returned HTML despite HTTP 200; file type and rendered equations were checked. PDF access is no longer laptop-only. Eq2.18 is legible but lacks phi_pia in its second inequality despite describing a phi_pia upper-bound purpose. Eq2.16/2.17 mix row/column conventions; an independent zero-spiral-rate case exposes nonstationary peak behaviour under literal Eq2.11 with standard atan2. These are notation conflicts, not accepted corrections.

Full proximal curves remain BLOCKED pending verified intended conventions or an independently justified equivalent branch rule. Verified distal curves remain intact. 33 affected tests pass, target validator no errors/freeze_ready=false. No rib coordinates, contacts, new canonical candidate, a003 or production changes. Evidence: `audit/runs/work_rib_primary_equation_review_20261008_001/`; updated source derivation retains historical OCR limitation and the new primary review.

### Claude continuation, 8 October (after GPT live head 0f8e677c)

- **CP2:** a femur declared as an extra root, or a radius declared "carried" by the humerus or femur, still passed GPT's relation repair. Roots are now limited to one skeletal root plus non-articulating bones, and carriers to documented exceptions (malleus–temporal, sternum–thoracic) (`a5f35880`). a003 still passes the structure checks.
- **Humerus** (`canonical_humerus_target_review_v1.json`): the joint-span sources agree (ANSUR GH–EJC 286.2 ± 10.6 mm, de Leva 294.5 mm), and a003's 287.7 mm lies inside both. Through the humeral head radius (24–28.8 mm) and the distal allowance (10.7–13 mm), they imply a maximum length of 312–336 mm. That is consistent with Mall's 334 mm, but below the inverted Trotter–Gleser 359.5 mm: the same pattern as the thigh. Nothing is selected, and the region stays PARTIAL.
- **Sternum** (`canonical_sternum_target_review_v1.json`): male population ranges are recorded (manubrium 46–55 mm, body 95–108 mm, total including xiphoid 154 ± 13 mm). In the BodyParts3D layout (grade D), rib 2 sits at the sternal angle and every topology rule holds. **a003 sternum:** a 213 mm stick (z +4.5); rib 2 is 38.7 mm down while the manubriosternal marker is 76.1 mm down; spacing is uniform (schematic). Per-notch dimensions need the Selthofer 2006 full text (Hrčak is blocked from the cloud). The ribs/sternum region stays BLOCKED.
- **Accepted GPT corrections:** the scapula-height claim is withdrawn (only the AA–TS width defect is established); the de Leva shank endpoint is KJC–LMAL.
- **Thorax frame / CP1a** (`canonical_thorax_frame_182_review_v1.json`):
  - **ANSUR standing anchors at 1.82 m:** IJ (suprasternale) 1494.5 ± 11.7 mm, C7 1575.2 ± 11.2 mm, acromion 1497.7 ± 16.2 mm.
  - **Conflict:** living men put C7 80.7 ± 11.4 mm above IJ, but the Seth model frame (32.8 mm) and the BodyParts3D specimen (45.5 mm) do not. Standing thorax pitch therefore stays OPEN.
  - **SC:** the Seth SC is 7.2 mm anterior, 6.0 mm superior and 25.5 mm lateral of IJ (breadth 50.9 mm, now a primary-model value for the feasible family's assumed 50 mm). Provisional SC height is 1500.5 mm (band 1486–1514); it is IJ-dominated, with ±20° of pitch moving it by under 5 mm.
  - **a003:** IJ is 24.7 mm high (z +2.1) and SC 13.7 mm high; its SC breadth of 50.0 mm matches.
  - Nothing is selected.
