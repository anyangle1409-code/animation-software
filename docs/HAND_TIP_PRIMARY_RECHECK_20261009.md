# Primary hand-tip recheck — 9 October 2026

No coordinates, accepted assets, source values or movement limits changed. No c005 or canonical promotion. This follows the independently audited 108 input points, 98 correspondences and ten unresolved tails.

## Evidence and endpoint scope

The official J-STAGE scanned PDF was downloaded and its Methods (p210), measurement diagram (p211) and Table5 (p213) visually inspected. The registered 19 male bone means/SD match the printed table. Five distal means/SD are thumb23±2, index18±1, middle19±1, ring19±1 and little17±1mm. They measure AP bony boundary-midpoint spans in 50 men aged20–40, not soft tips or 3D joint-centre coordinates. DOI `10.1620/tjem.185.209`, PMID9823781; authors Aydinlioglu, Akpinar and Tosun. Existing compatibility ID `DOGAN_1998_HAND_RELATIONS` is preserved; it must not count as another publication.

Hamilton/Dunsmuir2002's primary abstract uses cadaver-derived joint rotation centres and clinical radiographs for interarticular/fingertip distances. Those endpoints differ from bony boundary midpoints. Full methods remain restricted; no ratios adopted. Huan2026's open primary Methods measure medullary/cortical diameters, not longitudinal lengths. Neither paper supplies all ten world endpoints. Source URLs, locators and the J-STAGE PDF SHA256 are retained in `primary_endpoint_semantics_review.json`.

## Stored coordinate finding

`character_fit.hand_from_stations` copied runtime finger `_03` endpoints. The legacy skeletal builder labels these `surface_station`, confidence `low`; raw stations are not independently validated skeletal positions. Their lengths must not be treated as source truth merely because they precede containment.

| Digit | Raw station span mm | Stored a003 span mm | Raw difference in source SD units |
|---|---:|---:|---:|
| Thumb | 31.0001 | 22.9400 | +4.00 |
| Index | 27.0000 | 18.9000 | +9.00 |
| Middle | 30.0000 | 21.0000 | +11.00 |
| Ring | 28.0001 | 20.1600 | +9.00 |
| Little | 22.0000 | 16.7200 | +5.00 |

Values are identical bilaterally within numerical rounding. Standardized differences are descriptive context comparisons; 3D station spans versus AP endpoints and population adaptation are unresolved. They are not a diagnostic anatomical tolerance or a rule to replace bones with means. Stored lengths being nearer the source means does not validate the mesh containment that produced them.

The report refuses raw/stored head-frame disagreement instead of misreading c004's stale inputs as a fingertip clearance. Ten tests cover units/bilateral values, nonfinite geometry, positive SD, frame mismatch, immutability and refusal to accept containment from population agreement. The initially failing harness and review cases remain recorded. Containment origin is unverified without consistent displacement metadata; nonfinite derived comparisons are rejected.

## Constructor preservation check

Expanded replay checks cover all five records: a003 and c001–c004. Each preserves all206 bones and427 markers exactly, reports CP2 FAIL and leaves promotion false. Eighteen constructor tests pass; this confirms reproduction, not correctness.

Next: obtain independently defined bony distal tips and IP/DIP articular landmarks with coordinate registration, plus carpal centres/contacts. Rebuilding from raw generator tips or choosing source means would bypass those requirements. The existing metacarpal M2–M4 length findings and source corridors are preserved.

## Regression check

The post-review full suite ran 1,031 tests in145.625s:1,022 passed,5 failed and4 errored. The nine failing/error test names match the original live-branch baseline. Their production-control and execution-orchestration expectations remain incompatible with current anatomical rejection/freeze state; no gate was weakened. Full trace and name comparison are retained alongside this report.
