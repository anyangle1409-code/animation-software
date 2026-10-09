# c004: c003 with the six stale arm skeleton_input points resynchronised (audit candidate, not canonical)

**Identity:** `r95_a003_shoulder_thorax_c004_arm_inputs`. **Status:** `AUDIT_PROPOSAL_NOT_CANONICAL_NOT_ACCEPTED`; `freeze_ready=false`. It derives from c003 (`3eb4fa1e2f7d815e…`). a003, c001, c002, c003 and production are untouched.

**What changed:** only `skeleton_input.sides.{left,right}`: EJC, WJC, humeroulnar, humeroradial, ulnar_styloid_bone and radial_styloid_bone. Each point takes the committed c003 position of the reference it is *identical* to in a003:
- the joint marker where one exists (WJC = radiocarpal marker; humeroulnar and humeroradial = their markers);
- otherwise the bone endpoint (EJC = humerus tail; the styloids = ulna and radius tails).

No joint marker coincides with EJC or the styloids in a003; the nearest are 9.4, 10.3 and 17.8 mm away. Moving those points onto markers would have redefined them, so the bone-endpoint identity is used. Every new value is asserted to equal old + the side's GH translation (38.432 mm), the rigid arm move c003 already applied to the bones.

Bones, joint markers, landmarks, acceptance checks and provenance are identical to c003. `carpals` and `hand` input points are also stale (same translation), but they are outside this change's scope; they are read only by `skeleton_fit.py`, not by the Phase 9 tests, and are recorded as **UNRESOLVED**.

**Blend:** geometry is unchanged, so the c003 blend (`3962215043cebbcf…`) is **reused byte-identically**; it still carries the scene property `hgpt_candidate_id = c003`.

**Evidence:**
- `candidate_record.json`: the per-point before/after table is in `candidate.arm_input_correction`.
- `correction_and_causality.json`: hashes, the record diff (exactly the 12 points), derived frames (c004 hand/forearm frames = a003 to 8e-14°; c003 off by up to 25.8°; all other frames identical), changed test specs (16 hand/thumb/wrist tests; wrist pivot 38.4 mm → 0 mm from the radiocarpal marker) and visual-input identity.

## Re-validation (all computed in `validation_summary.json`: `C004_ARM_INPUT_RESYNC_CRITERIA_MET`)

| Criterion | Result |
|---|---|
| Wrist-centre gaps | WJC = radiocarpal marker on both sides (c003: 38.4 mm). Wrist sweeps no longer open the radiocarpal joint: c003 16.687 mm → c004 0, the same as a003 |
| Hand/thumb axes | Every joint-frame-audit alignment equals a003 (worst difference 0.0°; c003 had 10 deviations up to ~19°). All 24 changed tests reproduce a003 rotations and angles within float32 bounds |
| Shoulder / ANSUR / SC | Bones, joint markers, landmarks, checks and `acceptance_checks` identical to c003 |
| Unrelated outputs | 111/135 sample sets byte-identical to c003. Mirror (0 FAIL; the same REST_ASYMMETRY_ONLY set), continuity (0 issues), collision, all-pairs and state restoration are unchanged except in the 24 corrected tests. In those tests, new info-only near approaches (digit 4/5 phalanges, 2.5–2.6 mm) equal a003's |
| Integrity | Phase 9 135/135, mirror 41/43; solver ↔ Blender AGREE; CP3 round trip PASS with a report identical to c003's; a003/c001/c002/c003 records and blends unchanged |
| Guard | Remaining stale points: `carpals` and `hand` only (UNRESOLVED, out of scope) |

**Renders:** none were made for c004. The c003 review pack is reused because every visual input is hash-identical (`review_reuse.json`); those images and their manifest still name c003. No movement clips are claimed for the changed hand and wrist tests.

## Follow-up: carpals/hand inputs (no c005)

The 108 carpal and hand input points are audited in `../../hand_input_audit/hand_input_source_rebuild_v1.json`. 98 are uniquely correctable. The 10 fingertip stations are not encoded by c004, and a source rebuild cannot reproduce c004's hand: the translated hand lies outside the unmoved a003 skin, so the pipeline's containment step relocates it. No c005 was built; c004 remains this line's latest candidate (non-canonical).
