# R39 approved straight arm-to-body outline — 17 October 2026

Spec: owner confirmed the cyan guide in docs/review_guides/r39_arm_line_20261017/arm_line_guide.jpg and clarified that it must meet the body without the inward curve. Immutable parent R38; branch claude/original-v1-consolidated-review-20261014.

Constraints: only separately named R39 candidate; preserve frozen skeleton/basis/topology/weights/allnonS7 includingHGPT_SHOULDER, protected anterior sentinel, and156/166endkeys. No Vassets, third-party assets, private reference images, merge or force push. All previous tests remain unchanged. Every failure and worse metric stays reported.

Task1: approved-line regression. Done: new test compares final owner-frame rear profile to the immutableR38 arm-edge line fitted at60..160mm along the frozen humerus axis. Require upperarm0..60mm maxerror<2mm and no inward bodyjoin deficit>2mm from-140..0mm. UnchangedR38 reproduces four expected bilateral failures:17.52/17.43mm nearshoulder,25.20/26.41mm towardbody. Raw posed target passes within0.23mm.

Task2: native response and constrained solve. Add136degree S7 control as exactR38 interpolation(.6key130+.4key145); preserve parent geometry at owner frame<0.01mm. Native export checks82sample prediction<0.01mm. Material line-normal component is fixed on outer control vertices; area redistribution and final safety may adjust tangential components but may not erase the approved line. Six safety tests pass; new line-preservation fixture first failed against ordinary target cutback. Export-only first cloud stage intentionally saves no candidate model, to obtain native response before final build.

Task3: separateR39 native build with unchanged original guards, endkeys unchanged or refuse save. Fresh native identity, front goals, R37contour/R38mark goals unchanged, final82pose orientation, strict lockoutvolume and original post95collision rules. Compare all41pressframes and actualframes of13benchmarks againstR34 andR38; reject any count increase. Add approvedline tests on finalsavedprobe, not just target. Render matchedR38/R39 cameras/angles plus exact135.625bilateralcloseups and pressvideo. Final doc reportsallregressions and remainingissues.

Ruling: use the existing connector/cloudBlender workflow and dedicated r39-work source fragments because localBlender/completegitcheckout is unavailable. The requested branch remains the sole source of truth; normal expected-head pushes only. Cost if wrong: fail native stage without touching protected assets.

Ruling: the former25..65mm spherical front protection covered the marked lateral outline and prevented the desired line. R39 keeps the anterior sentinel fixed but uses8..26mm spatial taper for target generation. Existing front tests are unchanged; any crease worsening must be reported, not hidden.

Current status: line regression RED and target GREEN; safety line-component RED→GREEN. Native response export pending. No R39 model exists yet. Owner visual acceptance remains open.
