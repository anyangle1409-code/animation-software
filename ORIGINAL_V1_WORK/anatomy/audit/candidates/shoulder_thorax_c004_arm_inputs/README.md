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
