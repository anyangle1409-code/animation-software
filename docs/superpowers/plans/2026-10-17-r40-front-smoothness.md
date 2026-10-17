# R40: keep the approved straight outline and resolve the front crease

Owner scope remains the approved17October straight arm-edge guide continued into the body. R39 is immutable and rejected; its rear line passed(1.148/1.122mm arm,0.240/0.202mm body), but front130dihedral worsened23.4225to102.2674degrees(right) and90.6777left. No skeleton, production asset, non-S7 key or private reference photo is changed.

Investigation reproduces R38=23.4225, rawR39target82.812, finalR39=102.267degrees. At edge18634-18635 the parent5.403degree fold became102.267. The localized8..26mm anchor taper displaces neighboring vertices by sharply different amounts. Area/orientation/count safety does not bound dihedral quality. Simply restricting the correction to posteriorpositive-y points preserves the front but misses the approved line by13to26mm, so it is not a valid solution.

R40 keeps the same approved target and hard line components, anchors and frozen156/166keys. Add an exact native130degree front response and analytic adjacent-normal smoothing penalty to the coupled localS7 solve, alongside all82 pose safety constraints and nativeBVH contact separation. This addresses front quality directly; no existing test or threshold is weakened. New bilateral frontgoal<=25degrees reproduces two R39 failures. Analytic crease gradients and the complete material/matrix/projection chain match finite differences.

Start with export only; noR40model is saved until exact native response and offline feasibility are checked. Then run original guards, all prior R34/R37/R38/R39 goals, new R40front goal, preservation,82orientation and fullframe/benchmark measurements. Render matched comparisons and video and report regressions. R39 and R38 remain available for comparison.
