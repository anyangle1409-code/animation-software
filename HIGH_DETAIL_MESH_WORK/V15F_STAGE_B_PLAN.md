# V15f Stage B — index/middle local reconstruction

## Entry gate

Do not begin Stage B until all of these are true:

- ring_L numeric proof PASS;
- ring_L visual proof PASS;
- ring_R / pinky_L / pinky_R incremental gates PASS;
- Stage-A numeric gate PASS;
- Stage-A ring/pinky visual proof PASS.

The approved ring/pinky surface fingerprints from
`reports/v15f_stage_a_visual_decision.json` are frozen through Stage B.

## Evidence from V15b

V15b is rejected overall, but its per-digit measurements are useful:

| Digit | Δ >35° sharp ratio vs V13e | Δ >50° sharp ratio | Δ >100° folds |
|---|---:|---:|---:|
| index_L | -0.0003758 | -0.0002315 | 0 |
| index_R | -0.0003762 | -0.0002316 | 0 |
| middle_L | -0.0013976 | **+0.0004956** | 0 |
| middle_R | -0.0017152 | +0.0000148 | 0 |

Therefore:
- index is the lower-risk proof target;
- the V15b index direction can be used as evidence that conservative local
  change can help;
- V15b middle must **not** be copied blindly because middle_L traded broad
  >35° improvement for worse >50° sharpness.

## Order

1. index_L
2. index_R
3. middle_L
4. middle_R

Work one digit at a time.

After each digit run:

`AUDIT_V15F_STAGE_B_DIGIT.bat <digit>`

The gate requires:
- all general V15 invariants;
- approved Stage-A ring/pinky fingerprints unchanged;
- later Stage-B digits untouched;
- selected digit >35° no worse than V13e;
- selected digit >50° no worse than V13e;
- selected digit >100° fold count no worse than V13e;
- total >100° digit folds no worse than V13e.

## Modelling principle

Do not rerun V15b's whole-hand radial script.

For index/middle:
- inspect cross-band and longitudinal hotspot direction;
- repair only visible local surface problems;
- preserve original tracked vertices;
- add only minimum local support geometry;
- preserve shaft/joint volume;
- do not disturb approved ring/pinky;
- keep original skin weights exact.

Index may use the **principle** demonstrated by V15b's conservative improvement,
but not blind coordinate transfer.

Middle requires extra caution at >50° sharpness.

## Visual proof

A numeric Stage-B pass is still not anatomy approval.

Generate a matched per-digit V13e/V15f visual proof, inspect it, and record
PASS/FAIL before propagating the same approach.

Final whole-hand acceptance still happens in the normal V15 post-edit pipeline.

## Exit

After all four Stage-B digits pass numeric + visual proof:

1. checkpoint;
2. run the full Blender audit;
3. run:
   `RUN_V15_POST_EDIT_ALL.bat v15f_deep_hand_rebuild`
4. open:
   `OPEN_V15_REVIEW.bat v15f_deep_hand_rebuild`

Do not begin Phase C until final V15f visual acceptance.
