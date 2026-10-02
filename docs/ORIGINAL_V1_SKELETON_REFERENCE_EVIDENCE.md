# ORIGINAL v1 skeleton — external human-movement reference evidence

Status: RECORDED (reference-only) · Accessed: 2026-10-02 · Policy: `docs/EXTERNAL_HUMAN_MOVEMENT_REFERENCE_POLICY.md`,
`docs/SKELETON_HUMAN_MOVEMENT_AND_BONE_SUFFICIENCY_POLICY.md`

Only generic human-movement observations are recorded. Nothing from these sources was copied into the project: no skeleton, coordinates,
proportions, topology, weights, animation or imagery. The numeric ranges below become the project's OWN envelope
(`ORIGINAL_V1_SKELETON_MOVEMENT_ENVELOPE.json`), deliberately generous (they bound a pose, they are not targets). Where a fetched
page gave no number, that is stated and the limit is labelled project-conservative. NCBI Bookshelf NBK272 was not readable (bot check)
and is NOT used.

PMC/PubMed identifiers are the citation. "Fetched" = page text read this session; "search summary" = only the search-result abstract was
read.

## Hand: fingers, thumb, grip (high risk — three sources)

| Source | What it supports | Normal variation / limits | Project conclusion |
|---|---|---|---|
| PMC5010131 *Jam injuries of the finger* (fetched) | PIP is a hinge, flexion about 0–110 deg; DIP about 0–80 deg; both flexion/extension only | DIP range smaller than PIP | PIP envelope −5..110, DIP −10..90; both joints flex the same way |
| PMC3193629 *Hand kinematics: application in clinical practice* (fetched) | all three finger joints flex in the palmar direction; **DIP motion is linked to and follows PIP motion** through the extensor apparatus | no numeric ranges in the text | a DIP bend opposite to PIP flexion in a grip is not a human posture; the audit flags any joint < −2 deg |
| PMC10296280 *Finger kinematics during human hand grip and release* (fetched) | PIP has the largest dynamic range, then MCP, DIP smallest; flexion order PIP before DIP/MCP; index DIP range reduced by fingertip contact | joint contributions are not equal | do not assume equal MCP/PIP/DIP; grip uses 70/88/55 deg proximal→distal (all positive) |
| PMC6436119 *Influence of wrist position on MCP motion* (search summary) | MCP motion depends on wrist position | — | MCP envelope −45..100 |

Finding: the P1 stress poses bent the distal joint backwards (−55 deg; −85 deg on handle grips). Cause = pose construction, not rig bones.

## Wrist, palm, forearm, elbow (high risk — three+ sources)

| Source | Observation | Project conclusion |
|---|---|---|
| PMC8880601 *Anatomy, biomechanics and loads of the wrist joint* (fetched) | two-axis joint (flexion–extension, radial–ulnar deviation); functional ranges about 5–10 to 30–35 deg flexion/extension and 10–15 deg radial–ulnar deviation | radial deviation is small (envelope −45..25 incl. margin) — an 88 deg "radial deviation" is not wrist extension |
| PMC5658215 *Dorsal wrist pain in the extended wrist-loading position* (fetched) | extended-wrist loading (push-up type) is a recognised loaded position; no angle in the text | loaded extension is a real, expected wrist state |
| PubMed 30526465 *Scaphoid and lunate position at two wrist push-up positions* (search summary) | a push-up with the wrist extended about 90 deg is the studied position | push-up wrist extension target ~80 deg (envelope allows up to 90) |
| PMC3016043 *Mechanical axes of the wrist are oblique to the anatomical axes* (search summary) | wrist flexion–extension and deviation couple | no single-axis assumption; extension limit kept ≤ 90 |
| PMC8258984 *Clinical anatomy and biomechanics of the elbow* (fetched) | carrying angle about 10–15 deg (male); flexion axis ≈ transepicondylar axis; forearm rotation is a separate axis | elbow bends only about the humerus' lateral axis (abduction component ≤ 20); forearm twist is a separate component |
| PMC6692155 / goniometry summaries (search) | forearm rotation about 80 deg (AAOS) to 86–95 deg measured each way | forearm twist envelope ±100 |

Finding: P1 push-up forearm was never pronated (`twist_palm` target parallel to the forearm axis was degenerate) → the "wrist" bent 88 deg
toward the thumb side. P2 pronates, extends ~78 deg, and **solves the plank angle** so the palms and toe pads touch the floor together
(P1 left the hands 0.29 m in the air).

## Shoulder girdle (high risk — five sources)

| Source | Observation | Project conclusion |
|---|---|---|
| PMC3377910 *Scapulohumeral rhythm* (fetched) | overall humeral:scapular ratio ≈ 2.34:1 but 0–30 deg scapula ≈ 2.5 % of motion, 30–90 deg 21–38 %, 90–120 deg ≈ 53 %; interval ratios 0.9:1 to 3.8:1; large inter-subject spread | **no fixed 2:1 rule**; rhythm poses keep a modest scapular/clavicular contribution inside the envelope |
| PMC9246406 *Scapular movement during elevation depends on posture* (fetched) | upward rotation, tilt and external rotation all change through elevation and with thoracic posture | scapula is a free 3-axis control; limits project-conservative |
| PMC6620199 *Scapulothoracic rhythm and glenohumeral force* (fetched) | rhythm varies from none to 0.5:1; scapular motion strongly individual | same |
| PMC9081276 *Kinematic coupling of GH and ST joints generates humeral axial rotation* (search summary) | much of the axial rotation of the arm in elevation comes from scapulothoracic motion (13–20 deg); "true" glenohumeral axial rotation is small | axial rotation is a coupled quantity; the pose only needs the elbow hinge consistent with the forearm direction, and the twist split along the arm is distributed by the helper bones |
| PMC8111677 *Biomechanics of the rotator cuff* (fetched) | external rotators matter most at 150–180 deg abduction; glenohumeral elevation to ~120 deg then scapular rotation | overhead poses carry external rotation (up to 90 deg in the press) |

Finding (axilla/webbing, owner item E): classified as **pose/rig-construction**, not weights or topology. P1 elevated the arm with zero humeral
axial rotation, so the elbow hinged *sideways* in the humerus frame (up to 107 deg) and the forearm carried an 85 deg twist; weights/topology
were being asked to hide a wrong joint chain. P2 + twist helpers remove that.

## Hip, knee, ankle (two+ sources each)

| Source | Observation | Project conclusion |
|---|---|---|
| PMC5685413 *Hip ROM in recreational weight-training participants* (search summary) | flexion ≈ 120, extension ≈ 13, abduction ≈ 43, rotations ≈ 32–36 deg | hip envelope −30..130 / −30..50 / ±60 |
| PMC7276781 *Deep squat vs hip/knee/ankle ROM and strength* (search summary) | deep squat uses large hip, knee and ankle motion; peak hip flexion about 95–107 deg in squats | squat bottom hip ≈ 91, knee ≈ 98, ankle dorsiflexion ≈ 23 deg |
| PMC7160724 *Knee joint biomechanics* (fetched) | passive flexion up to ~160; walking 53–78, stair 83–105, sit-to-stand 82–96 deg; tibial rotation coupled with flexion | knee envelope −5..145; coupled tibial rotation allowed ±30 |
| PMC5405570 *Normal knee kinematics in deep flexion* (fetched) | internal tibial rotation up to ~15 deg and abduction up to ~11 deg through deep flexion | same |
| PMC4994968 *Biomechanics of the ankle* (fetched) | dorsiflexion 10–20, plantarflexion 40–55 deg; functional demands below the maximum | ankle envelope −55..30; push-up/squat dorsiflexion stays ≤ ~25 deg |

Finding: P1 squat put the ankle in front of the knee (plantarflexed, "seated-chair" posture). P2: knee over the foot, ankle dorsiflexion 23 deg.

## Foot and toes (high risk — three sources)

| Source | Observation | Project conclusion |
|---|---|---|
| PMC12019138 *First MTP joint* (fetched) | first MTP dorsiflexion about 57–82 deg, plantarflexion about 17–37 deg; passive > active | toe envelope −40..90; push-up toe dorsiflexion 80 deg |
| PMC4266096 *3-D kinematics of the human MTP joint during walking* (fetched) | the MTP functional axis is not the anatomical axis (about 16 % foot length anterior); one unified joint was measured | a single transverse toe hinge is a defensible rigid approximation for loaded forefoot support |
| PMC5095951 *Midfoot and forefoot in lateral ankle sprains* (search summary, from the matrix) | the foot behaves as several functional segments | single toe bone is adequate for support mechanics; separate hallux not required unless toes are modelled individually (see sufficiency decision) |

Finding: P1 bent the toe the wrong way (plantarflexion −60 deg) in push-up and lunge. P2: dorsiflexion toward the dorsum; floor-contact audit shows
the toe pads (not the bare tips) carrying the foot contact in the push-up (262 contact vertices) with the palms on the floor (hand 3.6 mm, thumb pad 0 mm).

## Thorax and rib cage (two sources)

| Source | Observation | Project conclusion |
|---|---|---|
| PMC9240654 *How does the rib cage affect thoracic spine biomechanics* (fetched) | the rib cage markedly increases thoracic stability (esp. axial rotation); ribs move relative to vertebrae/sternum but the sternal connection constrains | thoracic motion is distributed and stiff; no 24 independent rib bones |
| PMC3140236 *Chest wall anatomy and physiology* (starter list; not separately fetched) | ribs/sternum move with respiration | breathing is not a current requirement; no respiratory skeleton |

## Not claimed

* No source here gives a single universal range; every limit is a project envelope with margin.
* Push-up toe-support specifics come from the foot/toe literature plus the project's own contact audit; a competent push-up video reference was not
  recorded this session (no third-party frames were captured or stored).
