# c003 and acromion exact-reproduction diagnosis — 11 October 2026

This is a regression diagnosis, not new anatomical evidence or permission to
alter a003/c001–c004. The inherited full suite remains red. No tests, solver,
source data, numeric tolerances, candidate records or canonical assets changed.

Source checkout: `66bba1b3258c45acb5795ce1a310dde595f97241` on isolated
`codex/windows-c001-source-paths-20261010`. Private Python 3.12 dependencies:
SciPy 1.18.1 and NumPy 2.5.4, imported from
`work/private-source-skeleton-20261010/dependencies-python312/` outside Git.

## Corrected c003 reconstruction

The earlier missing-SciPy invocation ran 16 tests (15 pass, one import error),
130.610 seconds. One environment-corrected run completed **16 unchanged tests:
15 pass, one failure**, 159.474 seconds. The failing case remains
`test_shoulder_thorax_c003.Identity.test_reproduces`.

Its complete comparison reports **139 differences**, including:

- Windows source-path strings and hash-key separators.
- Solver-generated coordinates beyond the existing report comparator's
  relative `1e-9` / absolute `1e-12` tolerance. For example, trunk IJ y is
  `-0.016278594617760225` versus `-0.016278594550899562` metres; the left
  scapula landmark x is `144.68631139332183` versus `144.68631155043445` mm.
- Collision-report pair ordering/operand ordering, including the first
  metacarpal-3/trapezoid pair switching from right to left and later ties
  exchanging order.

These differences are small numerically but are **not solely paths**, unlike
the proven c001/c002 defect. Their exact cause has not been isolated between
optimizer/library/platform effects and tie ordering. Do not claim an anatomical
change or medical significance from this report; do not widen tolerances,
round geometry, rewrite frozen records or adjust pair ordering just to pass.

Frozen c003 record SHA-256:
`3eb4fa1e2f7d815ec664af93fc4ece89db87a36a5201452447b161fbdcc46f3a`.

## Independent related acromion audit

The unchanged `test_shoulder_ansur_acromion_audit` module completes **9 tests:
8 pass, one failure**, 1.979 seconds, in the same private dependency environment.
Its reproduction test reports six differences: one platform-dependent input
hash-key set and five rounded scapula-angle outputs. Examples include
`5.7023` versus `5.7024`, `1.8394` versus `1.8393`, and `30.4773` versus
`30.4774` degrees. Existing candidate preservation, infeasibility, geometric
crossing and manifest-hash tests pass. No anatomical acceptance follows.

Frozen acromion audit SHA-256:
`c637304510c0f17480faface2c90873e608a780c9c14cc0ba96698239a5e130f`.

## Resume

Both corrected diagnostic runs are complete; do not poll their old sessions or
rerun expensive c003 optimization. Source/producer numerical-environment pins
would be needed for a bounded future determinism investigation; they are not
verified by this checkpoint. Preserve unresolved findings and continue the
separate source-ordered pelvic CT candidate review using the existing private
82-frame Blender viewer. Anatomical identity, landmarks, segmentation,
registration, physiological motion and canonical promotion remain unaccepted.

Existing master checkpoint CI at `ea732b5a6c6bd01676043bbb01aceaeaf5914ed2`
passed all three jobs in run `38093962974`. PR #45's verified 31 c001/c002 tests
remain separately bound to source head `66bba1b3` and CI run `38093010487`;
those successful checks do not erase the c003/acromion failures recorded here.
