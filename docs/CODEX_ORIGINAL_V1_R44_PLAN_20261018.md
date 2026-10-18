# R44: correct the area ceiling and recover the confirmed junction

R43 completed as a rejected unsaved study, committed21255f8b. Its artifacts are
run39079213916/artifact12120445839. No R43 blend was saved. It passed all13
benchmarks, with zero new native contacts, motion excess0.450320mm and posterior
crease excess1.840896deg. It failed the owner-confirmed junction envelope and
area severity at full-press samples20/21. Those maximum ratios increased from
1.933816/1.929584 to1.999024/1.999013, above the unchanged1% relative allowance.

The optimizer's area upper bound mistakenly applied the relative ceiling only
to triangles already above2x area. This disagreed with the native area_safety
checker, which applies it to every sample. A new R44 regression test reproduces
the bug and passes after using the minimum of the count and relative severity
caps for every triangle. No native checker or earlier test was changed.

R43's coarse field stalled after133 steps, retaining a large profile deficit;
the final proposed step was4.8e-9mm. R44 uses finer compact smooth controls
(25mm centre spacing,70mm support,25mm boundary fade), within exactly the same
free-vertex mask. The new domain test fixes hashes of the free/frozen masks,
rest geometry and faces. There is no expansion of editable material. All prior
motion, crease, contact, original contour/front/line and owner-envelope tests
remain mandatory, as do13 benchmarks and original82-pose saved-model guards.

R41 remains the immutable model baseline. All original arm/elbow source
coordinates, control166, anchors, bones, weights, topology, Basis, HGPT_SHOULDER
and non-S7 keys stay protected. Existing S7 dense sampling reproduces the old
baseline before the new body increment. Changes and outputs are separately
named R44; frozen R43 study files and all V-assets remain unchanged.

An optimizer stall now stops after five negligible proposed steps and retains
the failed study, instead of spending the full budget repeating it. This is an
optimization stopping rule, not acceptance. Native tests still decide whether
a model may be saved. A failed fit is still rendered, packaged, documented and
committed with its failures. The cloud fit is bounded to30minutes.

Deliverables: matching R43/R44 back/three-quarter comparisons, the R42 target
comparison, a complete R44 press video and R43/R44 motion video, raw native
measurements, logs, tests and a short candidate report. Owner visual review is
required; no claim of approval is made.
