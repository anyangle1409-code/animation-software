# R45: fit by distance along skin, without expanding editable material

The R43 local constraint audit identifies posterior-crease limits as the main
barrier in the coarse field. At its stalled state, the linearized problem kept
normalized profile slack15.3676 with all families. Removing only the posterior
family in a read-only diagnostic allowed zero slack; removing front, motion or
area alone did not. No such removal is used in any candidate or acceptance test.
These are local linearized diagnostics, not proof of global feasibility.

The fitting field used Euclidean distance for shared controls and the boundary
fade. This couples opposing skin surfaces that are near through space but far
along the surface. At measured junction material points, boundary distances
were10.1–38.8mm through space versus24.5–90.4mm along mesh edges. All measured
junction points are already free at110..156, so no added free vertices are
needed to test this cause.

R45 uses shortest-path distances on the rest mesh, both for boundary fading and
compact C2 control weights. Left/right fields stay separate. It retains R44's
25mm control spacing,70mm support and25mm boundary fade. Actual control count
changes with the material metric (R44:2421 scalar controls; R45:3162), within
the same27483 free scalar source coordinates. A folded-ribbon regression has
opposing surfaces2mm apart through space but far along the surface. The old
field shares6 scalar controls across them and fails the regression; the new
field shares none and passes. Additional checks preserve nonnegative bounded
weights, separate hemispheres and fixed material coordinates.

After field projection, constraints are rescaled with their right-hand sides
and slack coefficients together. This is the identical linear program with
better row scaling. The new LP regression preserves hard small-coefficient
rows. Source/dense45mm bounds,0.5mm motion,2degree crease, front, contact, area,
owner junction and all earlier tests are unchanged. No checker is loosened.
An attempted no-crossover solver mode did not resolve reliably and is not used.

R44's corrected area ceiling is reused. R45 uses the exact R43/R44 free/frozen
masks, rest geometry and faces, fixed by hash tests. Original arm/elbow source
coordinates,166, anchors, canonical bones, weights, Basis, topology,
HGPT_SHOULDER and non-S7 keys remain protected. No private owner photo is stored.

R44 runs to completion and keeps its own evidence. R45 gets separately named
source, candidate/study folder, tests, native comparisons and press videos.
Only native83-sample gates,13 benchmarks, fixed shape tests and original saved-
model identity/guards can permit a new blend. Local predicted results are not
acceptance. Fit failure retains the unsaved study and its measurements. Owner
visual approval remains pending even after numerical success.

The minimum-step subproblem also gets an explicit0.001mm normalized profile-
objective allowance around Phase I's optimum, instead of demanding near-exact
placement on a degenerate LP vertex. This is an optimizer precision setting,
not a model acceptance tolerance. Only rows already labelled profile have this
allowance; area, crease, motion, front, contact and coordinate bounds remain
hard. The original default precision remains1e-7. New tests explicitly verify
that this profile-objective budget does not relax a hard row. All prior model
acceptance tests retain their original thresholds. Diagnostic proposals that
bypass minimum-step optimization are not used in the candidate.

The cloud continuation starts with R44's retained body increment, rather than
throwing that fitting progress away. All native geometry still evaluates from
immutable R41 plus the cumulative candidate increment, and all original limits
still compare against R41. The equivalent minimum-L1 problem uses nonnegative
positive/negative control parts, eliminating two absolute-value rows per
control. Moderate accepted backtracking can grow the next trial window; exact
nonlinear and native gates still decide what may be retained or saved.

R44 native outcome: all83 area/contact/orientation/motion/crease responses
passed;13 benchmarks passed; the owner-junction test failed. Its pre-save test
harness also hit a missing legacy /tmp/r42-response directory before running
its contour tests. R45 has a separately named pre-save harness that creates
/tmp/r45-response and runs the same unchanged five tests there. This changes
only staging/log paths, not tests or thresholds. R44 remains a rejected study
with no saved blend, retained at commit961de0f5 and artifact12131744259.
