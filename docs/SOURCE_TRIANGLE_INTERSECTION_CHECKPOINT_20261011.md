# Closed-triangle intersection prerequisite — mathematical candidate only

Stacked on PR50 `c74f34de50ab89bebcb03b09067408f687ae10e8`, all3 exact-head
checks SUCCESS in [run38134171190](https://github.com/anyangle1409-code/animation-software/actions/runs/38134171190).
Branch `codex/source-triangle-intersection-20261011`; shared PR48 plan unchanged.

New bounded two-triangle predicate uses exact `Fraction` arithmetic for finite
Python int/float coordinates within +/-1000000. Face normals, nine edge-cross
axes and six in-plane edge-normal axes; the last group handles coplanar disjoint
triangles with overlapping axis-aligned boxes. Strict separation means equality
is closed boundary contact. Degenerate or invalid inputs raise rather than
reporting clear surfaces. Tiny valid triangles and the smallest positive float
gap are not rounded into degeneracy/contact. No numerical epsilon introduced.

Exactness refers to input binary values, NOT physical source certainty. The
function does not enumerate a complete source mesh, classify articular patches,
measure global minimum distance, register HGPT, interpret units, approve anatomy
or give clinical contact meaning. All three acceptance flags remain false.
No integration into candidate source scenes, no patient inference, no asset
changes. No downloaded bytes or private native output added to Git.

## Local verification

Crossing-face fixture observed FAIL for missing feature, then PASS. Eleven
mathematical tests PASS (0.683s), including all36 corner orders in both argument
orders for intersecting and coplanar-separated fixtures. Twelve existing witness
tests PASS (0.010s);18 existing shell/CLI tests PASS (0.400s). Actual laptop
Blender5.2.1LTS factory/2threads: one test, three independent native synthetic
crossing/separated comparisons PASS (0.028s). Mesh coordinates read back exactly;
temporary synthetic meshes removed. BVH boundary/coplanar/epsilon semantics
are NOT used as exact authority. No full source rerun or image acquisition.

Historical inherited full1097 suite remains non-green (20failures,41errors,1skip),
not rerun under owner instruction to prefer targeted checks. Region readiness
remains0READY/9PARTIAL/3BLOCKED, original authority SHA256
`461927ae811a3572946bf8ae2f6a502cc85949890594b2ce26b7b63fedcfffea`.
Independent read-only review found no Critical/Important/Minor issues and reran
all11+12+18 tests and native1PASS. A separate exact barycentric feasibility oracle
(Gaussian elimination/basic feasible solution enumeration, not SAT) matched421
additional arbitrary3D, tilted-coplanar and1e-200-scale pairs;29degenerate pairs
refused. This is independent mathematical testing, not independent anatomy.
Review declined remote CI/private source/global mesh completeness/registration.
New Windows/Linux exact-predicate and native Blender CI configured; check the
newest pushed head before describing remote checks as passing.

Next executable action: newest exact-head CI (independent review complete).
Then a bounded completeness-checked native broad-phase candidate enumeration
before any real source intersection inference. Require a common query frame,
original triangle identity, no hidden island/degenerate removal, and independent
candidate completeness tests. Do not blindly trust native BVH overlap, repeat
69707 completed witnesses or call non-intersection a positive-clearance result.
W1A independent pelvic registration/qualified seven landmarks remain open.
