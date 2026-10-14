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
