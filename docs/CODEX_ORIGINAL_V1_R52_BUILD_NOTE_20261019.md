# R52 independent temporal surface study: source/build note

Owner approved the written R52 proposal19October2026 07:59 Europe/London. This is
an unsaved, unaccepted study. No R52 Blender model exists at this source checkpoint.
The latest saved baseline remains R41. R47's actual overall outline is the approved
shape reference; its rejected surface is not accepted anatomy.

## Implementation and protections

The existing71 integer-degree native S7 samples previously came from seven cubic
source vectors. R52 fits their added increments independently, with a zero95-degree
ghost sample, while retaining the original R41 baseline interpolation exactly.
The decoder identifies each active interval from the complete original coefficient
vector; negative/cancelling weights are not reduced to a scalar sum. All83 stored
response coefficient arrays decoded successfully in the local integration check.

The editable material union is exactly the original approved R47 union. Every
original source knot keeps its original per-knot allowed mask.95/110/166 increments,
anchors and the any-angle distal-arm mask remain zero. All72 source/ghost increments
must remain within45mm vector norm. No frozen skeleton, Basis, weights, topology,
HGPT_SHOULDER/non-S7 key or production asset is edited. Original source response
arrays are copied byte-identically and hash-checked.

The matrix-free finite-iteration primal-dual calculation uses the original full
press affine response and original back-motion mask. It targets the original0.5mm
motion limit with an internal0.45mm margin,3mm adjacent-integer-degree material
step bounds and no added early outward motion. Spatial mesh adjacency and temporal
second differences regularize the field. A local marked-envelope projection is
attempted while currently active marked support vertices are pinned. An additional
0.2mm internal envelope margin is conservative; exact actual outline measurement,
against the unchanged1mm guard, independently decides retention. Alternating local
projection is not a guarantee of global feasibility or solver optimality.

The retained state prioritizes simultaneous study feasibility over a smaller motion
number. This fixes a review finding that an infeasible state could overwrite a
feasible checkpoint. If no feasible state exists, a bounded outline-preserving
unsafe checkpoint can still be retained and rendered as failed evidence. Never
equate that with a passed hard constraint, a repaired model or owner visual approval.

## Tests and measured discarded probes

14 local tests pass (temporal decoding/adjoint/invalid data/90mm oscillation;
mask/cap/pin projection; motion and outward-halfspace adjoints; envelope clipping;
honest study status and feasible-first retention; actual-data dense preservation).
New tests were observed failing before their implementations; red/green logs are
retained in docs/r52_local_evidence_20261019/. An independent review found one
Important checkpoint-retention defect, fixed with a failing-then-passing regression.
It also prompted clearer envelope wording and removal of a duplicate artifact
download. Native Blender integration cannot run locally and remains pending CI.

The first75-iteration motion/space probe reduced motion but lost the outline;
its original R51 fallback was retained. An attempted boundary projection reduced
motion while holding the outline at early iterations, then escaped at later
iterations. Those later states were not retained. The tighter internal envelope
margin retains exact measured outline checks; it does not change the owner guard.
An integration slicing bug initially produced an empty single-frame mapping;
it was corrected before any source publication. A local test-suite invocation
initially omitted the preservation test's environment variables; rerunning with
the actual source/solution passed. These are harness failures, not geometry passes.

The first local100-iteration full outward-constraint trial still had0.753797mm
motion excess,3.186222mm adjacent-control change and0.232295mm early outward
increment at its final iterate, while keeping the actual approved-outline error
0.949999mm. None of these remaining motion/step/outward failures is described as
a repair. The final source uses the reviewed feasible-first retention policy.

## Native evidence pipeline

New workflow original-review-r52.yml pins NumPy2.3.5/SciPy1.17.0 and the same
checksum-pinned Blender5.2.1. It checks immutable R41 and R51 inputs, repeats a
bounded preflight and allows at most600seconds main fitting, recording timeout,
failure, retained main progress or preflight-only fallback honestly.

All83 original native area/contact/orientation/affine checks and all13 original
benchmarks run on actual independent dense geometry. Native affine error must
remain<=0.01mm. A separate161-pose native full-press comparison against R41 adds
temporal coverage: second-difference excess is normalized to the original40-step
grid by the squared interval ratio16, with guard0.5mm. The new step limit is3mm
per integer-degree material increment; additional early outward increment before
110degrees is limited to0.05mm for numerical tolerance. These are additional
checks; no original numerical threshold is relaxed.

Original R47 scope, R43 motion/back-surface and R48 marked-normal/actual-outline
tests run unchanged on the explicitly labeled seven-knot projection. Their input
interface cannot express independent intermediate controls, so those legacy
results alone cannot certify R52. Additional tests apply the original thresholds
directly to actual dense native positions and all72 material controls. All five
historical contour/front tests use actual native R52 probes. Every outcome,
including old projection failures, is retained. No original test is edited,
replaced or deleted. This study has no model-save or promotion step.

Render actual R51/R52 matched full-outline and both shoulder close-ups, a matched
press video and R52 press video. A separate native R47/R51/R52 panel keeps the
approved outline visible. No private reference photo/trace is used. All output
goes to a new immutable codex_review_r52_study_20261019 folder. Workflow green
means evidence completed; any folds, contacts, stretch, motion or outline failure
must be reported, and owner visual review remains separate.

## Immutable input hashes

- Source response SHA256:2a6c01cf7eacd3d1ceb47ae9f131f76dd0487fce5d3518d5cd1df65bc059fa8d.
- R51 retained seed SHA256:45b17ecc0f9261c3af9c08c44f7cdff0c054076015a3f0cd62d92c7d5bc83fc1.
- R41 model SHA256:4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e.
- Blender tar SHA256:a31f524fa99a527d3d52b7f5aaa68c34e1a19d5a1c9473f79c5cc610fd5b10e9.

Source/fit progress is not completion. Inspect the actual native reports and media
before telling the owner whether the bulge or arm-to-body repair improved.

Native decoder uses a first-party NumPy-only clamped-cubic basis, numerically equivalent to the original SciPy basis within2e-15. A failing-then-passing regression disables SciPy to reproduce Blender dependency availability. No extra Blender runtime package is required. The final reviewed100-iteration preflight retained0.854765mm motion excess,3.271742mm adjacent-control change,0.062665mm early outward increment and0.949999mm outline error. It remains failed/unsafe; do not label it repaired.
