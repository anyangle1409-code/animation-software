# ORIGINAL v1 O2 — Blender branch log

Branch: `claude/original-v1-blender-o2-20260929`, created from
`work/standalone-first-party-audit-20260927` at
`d924c89e3dc9cacc988b9f2fd09ce6f6a942b20e` (2026-09-29).

Purpose: keep all ORIGINAL v1 Blender/model work off the standalone
software-migration branch. This branch is **not** merged back automatically.
Runtime/package/allowlist/renderer files are deliberately untouched.

## Environment (laptop)

- Blender 5.2.1 LTS at `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`.
- Python gates run with Blender's bundled Python 3.13 (no separate Python install).
- Git for Windows 2.55 and Node.js 24 LTS installed on 2026-09-29; `npm ci` run.
- The clone uses `core.autocrlf=false`. With Git's default CRLF conversion,
  `node scripts/export-original-v4-rig.mjs --check` reports a false "stale"
  payload because the committed JSON is LF.
- The user's normal Blender preferences enable the MPFB (MakeHuman) add-on.
  It must never touch this asset. Every guarded/audit Blender process below
  runs with `--factory-startup` and all add-ons disabled.

## O1 source

`ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend` was copied from the
laptop's verified O1 working copy. SHA-256
`33f67e42fb8f5bb524b72bfb7b0aee6e3656f853e1c54e6a53034881161f21bf` equals
`ORIGINAL_V1_WORK/ORIGINAL_V1_PROVENANCE.json`. `PREPARE_ORIGINAL_V1_O2.bat`
then materialised the unbound 63-bone `hgpt_canonical_v4_original`
(payload SHA-256 `13bea1a6…f768`); v4 and boundary audits passed.

## Guard/launcher corrections (evidence-backed)

1. **Branch check.** `PREPARE_`, `OPEN_` and `AUDIT_ORIGINAL_V1_O2*.bat` also
   accept `claude/original-v1-blender-*`. Approved by the project owner so O2
   work stays off the standalone branch. No other check changed.
2. **Bundled add-ons.** Blender 5.2 `--factory-startup` still enables
   `io_anim_bvh, io_curve_svg, io_mesh_uv_layout, io_scene_fbx,
   io_scene_gltf2, cycles, pose_library, bl_pkg`. The guard treats any enabled
   add-on as a blocker, so the unmodified `OPEN_ORIGINAL_V1_O2_GUARDED.bat`
   would taint every session at the first depsgraph update.
   `scripts/disable_addons_for_guarded_session.py` now disables all add-ons for
   the session *before* the guard starts. This is stricter; the guard code is
   unchanged.
3. **Audit process add-ons.** After a guarded save,
   `audit_original_v1_authoring_boundary_blender.py` also lists the *auditing*
   process's add-ons (the user's MPFB and others) as blockers. That is not
   evidence about the authoring session, which the live guard records. The
   boundary audits now run in a clean factory process with add-ons disabled.
4. **Factory audits.** The v4 and mesh audits also open the production Blend
   with `--factory-startup`, so no user add-on (such as MPFB) ever loads with it.
5. **Headless guarded runner.** `RUN_ORIGINAL_V1_O2_GUARDED_SCRIPT.bat
   scripts\x.py` mirrors the GUI launcher's preflight and guard. It runs only
   committed, unmodified scripts under `scripts\`, and fails if a taint record
   appears.

## O2 method decision: project-authored body generator

The O1 scaffold is a 1.75 m primitive assembly with 492 open edges: separate
pelvis/shoulder/head/ear/nose/finger pieces. The v4 target is 1.82 m with a
430 mm shoulder-joint breadth, so the rig arms hang outside the scaffold.
Refining those vertices cannot produce deformation-ready anatomy.

The O2 body is therefore rebuilt inside the same mesh datablock
(`HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD_MESH`) by `scripts/original_v1_o2_body.py`:

- **Inputs:** only `ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json` and
  anatomical measurements authored in the script. It does not use O1 vertex
  positions, other meshes, projection, shrinkwrap, weights, UVs, materials or
  bind data.
- **Topology:** a quad control cage of joint-aligned rings with explicit split
  junctions:
  - axilla (a 60-vertex shoulder ring splits into torso 32 + two arms of 20);
  - crotch (torso 32 splits into two legs of 20);
  - neck base, closed by shoulder caps;
  - thumb web (palm 20 splits into palm 20 + thumb 8);
  - finger webs (palm 20 splits into four fingers of 8).

  Joints (elbow, knee, wrist, MCP/PIP/DIP, thumb MCP/IP, ankle) have rings at
  and on both sides of the centre. One Catmull-Clark level is applied in plain
  Python.
- **Symmetry:** the left limbs are built from the rig; the right side is an
  exact mirror.
- **Finishing:** the crown is set to 1.820 m and the soles to z = 0 exactly.
- **Gate:** `python -m unittest discover -s scripts -p test_original_v1_o2_body.py`
  checks the O2 numeric mesh gates, all-quads, grounding, determinism and the
  rig-payload input.

`scripts/apply_original_v1_o2_body_blender.py` writes the output into the
production Blend under the guard and records hashes in
`ORIGINAL_V1_WORK/O2_BODY_GENERATION.json`.
`scripts/render_original_v1_o2_review.py` renders review views from a
**disposable copy** only; it refuses the production Blend.

Additional read-only evidence: `scripts/audit_original_v1_o2_rig_fit_blender.py`
samples nine points along every v4 bone and requires each to lie inside the
closed body. Terminal fingertip, toe and head tails are reported but not
gated. `neutral_clearance()` in the generator gates the rest-pose hand-to-body
gap (≥ 5 mm) and arm-to-body gap (≥ 10 mm).

Laptop notes: agent shells may set `NoDefaultCurrentDirectoryInExePath=1`, so
`CHECKPOINT_ORIGINAL_V1_O2.bat` cannot `call` the audit by bare name. Unset it
in that shell; normal terminals are unaffected. `.git/info/attributes`
(local, uncommitted) checks out `*.bat` with CRLF.

## Region log

Entries are appended as regions are checkpointed (see
`ORIGINAL_V1_WORK/O2_AUTHORING_LOG.jsonl` for hashes).

### 1. Torso/chest/back — checkpoint `3178ac7e…46e6` (2026-09-29)

- **v4 fit.** Sagittal placement follows the v4 skeleton's plumb line:
  - the sternal notch sits just ahead of the clavicle heads (f ≈ +0.036 m);
  - the chest front is about +0.117 m at the nipple level;
  - the upper back reaches −0.155 m, covering the scapula bones (the scapula
    tip is 1.2 mm deep, the bone's interior 8–11 mm);
  - the lumbar lordosis sits at the waist.

  A first draft placed the torso about 5 cm too far forward. It was caught by
  the scapula bones protruding and corrected before checkpointing.
- **Shape.**
  - The back half of the thoracic cross-sections is broader and flatter than
    the front.
  - The pectoral and latissimus volume is modest.
  - The trapezius rises from the acromion (about 1.53 m) to the neck base
    (about 1.58 m).
  - The torso's vertical edge columns are steered into the anterior and
    posterior axillary folds, which removes the fold crease.
- **Gates.**
  - Authoring audit PASS, including the strict mesh gates: 0 mirror mismatches,
    boundary, non-manifold, winding, loose, degenerate or duplicate faces;
    height 1.820 m.
  - Rig-fit PASS for all 62 bones × 9 samples.
  - Hand-to-body clearance 5.6 mm; forearm-to-hip clearance 19 mm.
- **Topology.** The mesh has 14,682 vertices and 14,680 quads.
- **Rig finding (not changed).** The v4 rest thumb tip (thumb_03 tail
  lx 0.155, z 0.830, f +0.061) reaches the anterolateral upper thigh. The upper
  thigh was flattened anterolaterally to keep a 5 mm gap. If a fuller thigh is
  wanted, the rest thumb needs a rig-level review.
- The log has two entries for this hash: a direct diagnostic run and the
  wrapper run.
- **Open for this region.** It is a soft, neutral base without muscular
  detail. Abdominal and oblique definition is deferred to sculpt/normal
  detail after O3. Human neutral-anatomy review is pending.

### 2. Shoulder/clavicle/axilla — checkpoint `5b873a0c…6aab` (2026-09-29)

- **Deltoid.** It wraps the humeral head across four 60-vertex cage rings
  (about eight after subdivision) from the axilla (1.39–1.42 m) to the
  acromion (about 1.53 m), and tapers continuously into the arm with no ledge.
- **Pectoral.** Added pectoral mass with a lower border, a sternal groove and
  a rounder anterior axillary fold. The posterior fold covers the scapula bone.
- **Accepted crease.** A ~5 mm crease remains at the anterior fold apex, where
  arm and chest meet in the arms-down rest pose. It is accepted for O2 and must
  be rechecked under abduction and flexion at O5.
- **Gates.** Authoring audit PASS; rig-fit PASS; clearance gate PASS.

### 3+4. Upper arm/elbow + forearm/wrist — checkpoint `74ed9055…5a9d` (2026-09-29)

Both regions were refined in one pass and recorded as one checkpoint.

- **Arm.** Twenty-vertex cage rings (40 after subdivision) run along the
  vertical v4 humerus/forearm line (lx 0.215, f −0.03). The neutral hang has
  the palm medial and the thumb forward.
- **Muscles.** Added biceps (front, peak z ≈ 1.285), triceps (back, 1.33),
  deltoid insertion, and the brachioradialis/extensor/flexor mass in the upper
  forearm, tapering to the distal forearm.
- **Elbow.** Cage rings sit at 1.21, 1.19 (joint centre) and 1.17, with the
  epicondyles and olecranon widened.
- **Wrist.** Oval section (≈ 62 × 39 mm) matching the forearm, widening into
  the palm over three rings (`palm_ring(..., arch=)`). This removed a
  "bracelet" step from the first draft.
- **Gates.** Authoring audit PASS; rig-fit PASS; clearance PASS.
- **Open.** Pronation/supination and loaded-wrist deformation checks belong to
  O4–O5.
