# Work cloud integration — 14 October 2026

Independent software lane from PR103 `94e066b9`. No Claude branches, frozen
models, production clips or geometry changed. Reviewed PR48/26, software
PR101–103, PT PR2–6 and Claude PR111–113 plus master-execution checkpoint.

## Export milestone

Blender 5.2.1 on the actual unchanged a003 source reproduces an **importer
display aid**, not a GLB leak: the serialized GLB contains one body mesh;
default import creates Icosphere (42 vertices), while
`disable_bone_shape=True` imports one body and one rig. Do not delete geometry
by name or suppress rig controls in the exporter. Claude's round-trip script
ran unchanged apart from printing serialized inventory: five poses PASS,
max 0.0007 mm, 67 joints, 17,946 vertices, 35,888 triangles, six zero morphs.

The existing candidate receipt now rejects orphan, missing or shared mesh
payloads as well as extra mesh nodes. 14 receipt tests PASS; the orphan test
failed before the guard. Actual native provenance regression PASS. Full
studio baseline: 201 files / 1,125 tests PASS, 62 skipped. No movement approval.

## Next queue

Opt-in versioned provisional rig extension (helpers, individual toes,
knee/elbow morphs); bounded morph-before-skin and pose compatibility;
reuse existing intent/parser/playback; app preflight; controlled native GPU
experiments; dependency audit. Keep all production gates closed.

The environment exposes no usage meter or reset-resume control. Resume from
this independent branch after fetching its live HEAD and rechecking PR26.

## Rig and morph milestone

PR114 at `becd210f85f97f197b14318e0187b7b3be8a5778` has three successful
PR workflow runs, including native Blender run `38538184716`.

The separate `work/cloud-rig-extension-20261014` lane introduces v2
review-only metadata and complete authored pose packing: baseline 67 joints
stay in order, appended shoulder helpers/individual toes stay under 128,
explicit morph names stay under 16. No helper driver is synthesized.
The existing SHA-pinned original parser/rest viewer remain untouched.
These metadata declarations are **not source-byte verification**.

Sparse POSITION/NORMAL correctives now apply before existing first-party
LBS in a bounded opt-in diagnostic path. Input snapshots and output copies
prevent caller mutation. No K1 or W3 corrective is selected or approved.

Reconciled existing PR65/66 intent/binding modules into this software lane;
reused their tests and extracted a shared synthetic fixture. Browser test:
79-joint palette, 11 frames, position/normal GPU versus CPU max error
1.1921e-7; command→source SHA→three authored pose samples→GPU error 0;
equipment mismatch rejected; no vendor module requests/WebGL errors.
This is nonhuman synthetic evidence only. 312 Node tests PASS; full studio
suite retains 1,125 PASS / 62 skipped. Build/typecheck PASS.

## Exact compatibility requirements for Claude

- Keep base joint names/order from the original 67 skin entries. Append
  explicitly named controls with a preceding parent; do not move source centres.
- Supply full rest/inverse-bind matrices and **full authored world matrices**
  for every helper and toe at every sample. No assumed halfway shoulder drive.
- Preserve side-specific digit axes; equal local signs are not bilateral flexion.
- Version the source GLB SHA and pose set SHA after any rig, weight or morph change.
- For each named morph supply sorted unique sparse POSITION/NORMAL indices,
  additive deltas in glTF metre/Y-up source space and explicit [0,1] weights.
  Rest is zero; no auto activation. Software caps are not physiological limits.
- A new extended real GLB still needs dedicated bounded accessor/hierarchy/
  bind/source-digest verification and actual-source GPU parity before loading
  through the approved original path. Existing original profiles remain strict.
- Owner visual, motion, rights and release approval remain separately required;
  trial compatibility does not close W3/F5/K1 production acceptance.

## Audit limitations

Animation studio still declares runtime `three`; standalone release audit
correctly fails its release-readiness gate. No working dependency removed.
PT App package has zero runtime/dev npm dependencies but protected temporary
clips remain. Its source was read through GitHub into a partial checkout;
actual clip bytes are unavailable there, so full media/offline-video checks
are not claimed. PT smoke: 631/631 in UTC; 630/631 in Europe/London and the
environment timezone (existing midnight date-key regression). No app date
semantics or historical keys were changed by this integration lane.

## Sampled playback milestone and restart

`work/cloud-diagnostic-playback-20261014` builds on PR115
`d4950f2515603e5b1ed685ff40d1e17efa0d0daf`. First-party playback supports
play/pause/resume/seek/dispose with one scheduled frame, stale callback
cancellation, finite monotonic clock checks, copied pose outputs and cleanup
after draw/scheduler failures. It holds exact authored samples, with no
matrix interpolation. This is deliberately diagnostic sampled playback.

317 Node tests PASS, including five new playback regressions; studio remains
1,125 PASS / 62 skipped; build/typecheck PASS. Actual Chromium RAF playback
draws source samples [0,1,2], completes and stops. Synthetic GPU tests retain
1.1921e-7 max error and command path error 0. Actual a003 Blend SHA remains
`670a37bfd206d702928de721032e2b942725389dc6906df0d866eba8d8cbbe56`.

Cloud Chromium mobile-shell experiment at 390×844, DPR2: no horizontal
overflow, all four setup inputs 16px, service-worker-controlled offline
reload preserves the rendered setup, no page errors. Partial checkout lacks
real icon/media bytes; this is shell evidence, not exercise-video or iPhone
hardware acceptance.

Published prior milestones:
- Animation PR114 `becd210f85f97f197b14318e0187b7b3be8a5778`, three successful
  PR runs; native source CI `38538184716`.
- Animation PR115 `d4950f2515603e5b1ed685ff40d1e17efa0d0daf`, three successful
  PR runs; full suite/build/synthetic GPU CI `38539940214`.
- PT PR7 `49c46e7ad1b6515379a2bc0b6db73acbd1d22796`, two successful PR runs;
  contract/full UTC smoke/build CI `38540126407`.
- This playback branch: check its current remote SHA and exact-head workflow
  result before reuse. All PRs stay draft; none is merged or production approved.

Resume on the playback branch, fetch live HEADs for PR26/48, software
PR101–103/114–116, PT2–7 and Claude111–113/master ledger. Preserve all other
lanes. Start with actual extended GLB intake once Claude supplies a versioned
trial export; otherwise advance source-bound scene/material/parity tests and
the existing PT timezone regression in a separate reversible branch.
Do not rerun completed scientific/Blender shape programmes or create a helper
driver on Claude's behalf. No automatic reawakening/usage meter is exposed.

## End-to-end accepted-character checks still required

| Check | Required evidence / refusal behavior |
| --- | --- |
| Export components | SHA-pinned serialized mesh inventory; no orphan/display meshes; real rig, material, animation and intended morph data retained |
| Extended rig | Base67 order and joint centres unchanged; appended controls and explicit side axes; correct rest hierarchy/inverse-bind residuals; strict bounded source accessor decode |
| Corrective playback | Actual source deltas and driven weights at all supplied poses; before-skin order; native→GLB→native pose error below existing 0.5 mm round-trip threshold; GPU/CPU parity measured |
| Exercise identity | Command equipment/side/posture/grip match the source pose declaration and exact PT exercise map; unknown or conflicting requests refused |
| Human movement | Owner-approved real multi-frame whole-body references, floor/equipment contacts, joint ranges and shoulder/knee/elbow/grip deformation; synthetic tests cannot close this gate |
| Lifecycle/security | Cancellation, source mutation refusal, bounded palettes/morphs/buffers, context loss/disposal and no unexpected network/vendor requests |
| App/offline/mobile | Actual accepted model and approved replacement media; real device sizing/performance/memory; cached shell and used media play offline; uncached media gives explicit fallback |
| Release | Independent rights/provenance and owner acceptance; no third-party shipped runtime/assets; protected temporary clips replaced only by separately approved outputs |
