# Original rib thesis: acquisition and equation audit

The current University of Michigan item advertises a downloadable bitstream; the 24,996,572-byte PDF is now acquired and SHA256 checked. Read `rib_inplane_derivation_holcombe2016_v1.json` for its URL/hash and source-versus-inference distinction. No PDF/pages redistributed. Legacy HTTP success produced HTML, so status 200 alone was insufficient; the downloaded file was checked as PDF, text-extracted and equations visually inspected on printed pages 37/39.

Printed Eq2.18 is legible but its second inequality lacks the proximal-angle parameter described by the prose. Eq2.16/2.17 also mix row/column matrix conventions. A Bp=0 unit-circle case satisfies literal Eq2.11 under standard atan2(y,x) but lacks a stationary Y peak after the intended rotation. Independent numerical counterexamples are retained in `check_literal_equations.py` and JSON. They expose ambiguity, not the author's intended corrections. No automatically repaired convention or proximal branch is accepted.

Original access is resolved; full proximal reconstruction remains blocked by source notation/branch semantics. Verified distal curves and demographic data remain intact. No full 24-rib dataset, head/tubercle contacts, canonical candidate or production change is claimed. The safest next action is verified source implementation/corrected derivation or an independently justified equivalent branch rule, followed by source-shape and contact checks.

33 affected tests pass. Prior full hyoid checkpoint: 809 tests with the same nine baseline failures; this evidence-only checkpoint changes no runtime or geometry. Target validator retains freeze_ready=false.
