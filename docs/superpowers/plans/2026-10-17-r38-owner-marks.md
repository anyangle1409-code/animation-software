# R38 local owner-mark refinement — 17 October 2026

Owner feedback on R37 at135.625degrees: remaining posterior surface lobe at77%,69%; excess broad rear bow at73%,32%. Scope is the already-approved local S7 skin rebuild; no skeleton change. Private image stays excluded.

1. Reproduce both marks as additional bilateral local goals on immutable R37. Done: four expected failures, broad-bow RMS9.5747/9.6932mm and posterior quadratic residual p952.7149/2.7158mm.
2. Author local anchored rear correction (12mm cap), posterior smoothing (6mm cap), and broad sentinel protection. Offline geometric target reduces both diagnostics; this is not a saved native model or visual acceptance.
3. Export native82-pose response from R37; verify predicted geometry<0.01mm. Couple area and signed-orientation constraints; reject any extra stretch/collapse samples or normal rotations>90degrees. New solver reversed-triangle test reproduced unsigned-area blind spot then passed; transformed-pose/fixed-vertex and NaN tests pass.
4. Save only new R38 if original unchanged guards leave156/166keys exactly R37. Fresh-process identity versusR33 protects skeleton/basis/topology/weights/allnonS7 includingHGPT_SHOULDER. Run all old front/contour/guard/volume checks unchanged plus the new mark tests. Additional no-count-increase checks versusR37 supplementR34 comparisons over41pressframes and actualframes of13benchmarks.
5. Render native matchedR37/R38 rear/front/threequarter and exactowner-angle bilateral closeups; packagevideo, metrics, doc including failures. Preserve rejected experiments; no production merge, noforcepush.

New metrics: broad rear chord deviation RMS<7.5mm over-120..+60mm fromshouldercentre; posterior surface p95residual<2mm aroundthe marked patch. These are local author goals, not clinical/anatomical approval. Owner visual review remains decisive. Front crease, topstretch and two benchmarkcrushedtriangles stay open unless separately demonstrated improved.

Current status: source prepared and local checks passed; native verification pending. Branch base b1c9835ab3409d3a0f523c4543e91b0f42ad1229. No existing candidate/test files modified.
