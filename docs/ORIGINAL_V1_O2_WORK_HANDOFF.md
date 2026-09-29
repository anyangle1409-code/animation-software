# ORIGINAL v1 O2 neutral anatomy — Work to Blender handoff

> **Status on `claude/original-v1-blender-o2-20260929` (2026-09-29).** All ten
> regions are checkpointed, and the strict numeric O2 gate passed on the
> laptop. The owner's neutral-anatomy review is pending. Method, launcher
> fixes, hashes and next steps are in
> `docs/ORIGINAL_V1_O2_BLENDER_BRANCH_LOG.md`.

## Identity and source boundary

Work only on `work/standalone-first-party-audit-20260927`. The asset is `HomeGymPT_Male_ORIGINAL_v1`; its unbound production rig target is `hgpt_canonical_v4_original`. The O1 profile scaffold is 1.75 m historical clean geometry, whereas the independently re-authored v4 target is **1.82 m**. The older `ORIGINAL_V1_DIMENSION_SPEC.json` records the scaffold, not a competing final v4 height. Do not scale the armature to 1.75 m or copy v3 rest coordinates. V15f is a visual benchmark only.

The committed `ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json` is generated from `src/rig/canonicalV4Original.ts`, not manually edited. It defines all 63 bone names, parents and rest endpoints. The Python validator independently checks exact hierarchy, mirroring, finite lengths, shoulder/hip breadth, limb/palm, metacarpal and every finger segment dimension. Numeric passing does **not** approve anatomy.

## Exact laptop entry

From the repository root on the requested branch, with the existing local O1 Blend present and development packages installed (`npm ci` if needed):

```bat
PREPARE_ORIGINAL_V1_O2.bat
OPEN_ORIGINAL_V1_O2_GUARDED.bat
```

The launcher checks the branch, Node.js and local `esbuild` installation before editing the Blend. The Blender script then compares the untouched O1 Blend SHA-256 to `ORIGINAL_V1_WORK/ORIGINAL_V1_PROVENANCE.json` and checks blank-source/scaffold provenance flags before any change. If `BLENDER_EXE` is needed, set it to Blender's full `blender.exe` path before running. The command checks the committed rig export, backs up the Blend to `ORIGINAL_V1_WORK/checkpoints/PRE_V4_<UTC>.blend`, creates the unbound v4 armature, and writes `reports/original_v4_blender_audit.json`. Do **not** open `ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend` directly for production modelling; use `OPEN_ORIGINAL_V1_O2_GUARDED.bat` so the live first-party authoring guard is active. It deliberately fails on rerun or on a modified O1 baseline; never delete objects merely to make it pass. The old `HGPT_CLEAN_HISTORICAL_REFERENCE_RIG` remains hidden and reference-only: its O1 armature modifier and historical skin groups are removed from the scaffold after the backup. `ORIGINAL_V1_WORK/O2_RIG_PROVENANCE.json` records both Blend hashes and the v4 payload hash. The v4 armature must remain unbound throughout O2.

If the local O1 Blend is missing, recover the verified O1 checkpoint on the laptop or rerun `PREPARE_ORIGINAL_V1_CLEAN_ROOM.bat` after checking the O1 provenance and evidence. Never manufacture a replacement from a legacy Blend.

## Guarded first-party authoring

Every O2 production modelling session must enter through `OPEN_ORIGINAL_V1_O2_GUARDED.bat`. The launcher first reruns the v4/scene boundary checks, then installs a live Blender guard. The guard keeps a sticky taint record if an unexpected object, mesh/armature datablock, material, collection, enabled add-on, linked/overridden datablock, image or other external media, action, UV layer, shape key, vertex group, modifier or constraint appears — even if it is renamed or deleted later.

Use only the existing `HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD`, the committed v4 dimensions/rest payload, stock Blender modelling/edit/sculpt tools and committed project scripts. Do not use Import/Append/Link, external or legacy meshes, image planes/photos/scans/videos, Asset Browser content, shrinkwrap, surface/mesh deform, data transfer, projection/nearest-surface fitting, third-party Blender add-ons/scripts, or any weight/UV/material/bind-data transfer. The production O2 Blend must retain only the body, hidden clean historical reference rig, v4 target rig and existing scaffold material.

After each region, close Blender and run `CHECKPOINT_ORIGINAL_V1_O2.bat <region_name>`. It reruns provenance/rig/mesh audits before copying the Blend to the checkpoint folder and appending the Blend SHA-256 plus Git HEAD to `ORIGINAL_V1_WORK/O2_AUTHORING_LOG.jsonl`. At final O2 completion use `CHECKPOINT_ORIGINAL_V1_O2.bat neck_head strict`.

## Modelling stages

Work on the `HGPT_ORIGINAL_V1_CLEAN_SCAFFOLD` geometry as a clean starting volume. Save a named checkpoint after every region. First region: **torso/chest/back**; adjust its neutral silhouette and 1.82 m rebaseline around the new pelvis/spine/neck/shoulder/hip joints, then review front, side and three-quarter views before continuing.

| Order | Region | O2 neutral outcome and later deformation preparation |
|---|---|---|
| 1 | Torso/chest/back | Ribcage, waist, lumbar and scapular surface volumes; continuous spine and shoulder flow. |
| 2 | Shoulder/clavicle/axilla | Deltoid centered on humeral axis; axillary folds and scapular space for overhead reach. |
| 3 | Upper arm/elbow | Smooth taper, elbow landmarks, circumferential loops on both sides of hinge. |
| 4 | Forearm/wrist | Extensor/flexor volume and wrist narrowing; loops for pronation and loaded extension. |
| 5 | Hands/fingers | New palm, thenar/web, metacarpals, MCP/PIP/DIP loops and rounded tips; no projected legacy hand. |
| 6 | Pelvis/glutes | Hip crease, glute/thigh junction and groin clearance for deep flexion. |
| 7 | Thigh/knee | Patella/front and popliteal/back volume with bending loops. |
| 8 | Calf/ankle | Gastrocnemius/Achilles contour, malleoli and ankle bend loops. |
| 9 | Feet | Heel, sole plane, arch, ball and toes; bilateral grounded neutral contact. |
| 10 | Neck/head | Cervical transition, cranium, face/ears from original shape decisions. |

Do not bind, transfer weights, UV unwrap, add texture images, or make shorts during O2. Do not create duplicate/reference meshes or saved helper objects in the guarded production Blend. Any disposable deformation experiment that needs copies belongs in a separate file made from a passing checkpoint and must never be merged back into the production Blend.

## Objective gates after each region

1. **Provenance:** only the O1 project-authored scaffold, original edits, and the exported v4 rest payload may contribute geometry/coordinates. No imports, shrinkwrap, projection, weight/UV/material transfer, imported bind matrices, linked Blend libraries, external image textures or legacy source rig. Record tools/operations and the checkpoint hash; scene markers alone cannot prove the full history.
2. **Rig:** `node scripts/export-original-v4-rig.mjs --check`; `python -m unittest discover -s scripts -p test_original_v4_payload.py`; `blender --background ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend --python scripts/audit_original_v4_blender.py`. Exact 63 names/parents, mirror error at most 1e-6 m in Blender, lengths at least 4 mm, head tail at 1.820 m, upper arm 325 mm, forearm 270 mm, femur 445 mm, tibia 430 mm. Joint centers must be visually inside the intended anatomical joints in front/side views; record offsets from visible joint landmarks, and require human review before freezing a center. No v3 numerical rest import.
3. **Neutral symmetry:** mirrored topology and vertex positions within 1 mm where a region is intended to be bilateral; explicit exception and reason for authored asymmetry. Joint centers and neutral foot contacts within 1 mm side to side. Measure after applying only intentional neutral symmetry operations, not by fitting a legacy surface.
4. **Topology health:** evaluated production surface manifold; zero nonmanifold/boundary edges except documented intentional openings; zero loose vertices, zero degenerate faces (<1e-10 m²), no duplicate coincident faces, consistently oriented normals, no inverted local sections. Count and inspect edge loops at shoulder, elbow, wrist, hip, knee, ankle and all finger joints. Require at least two supporting loops on either side of each intended bend center as an initial modelling check; visual deformation still decides adequacy.
5. **Proportion:** design target 1.82 m crown-to-floor, shoulder joint breadth 430 mm, hip joint breadth 184 mm, upper arm 325 mm, forearm 270 mm, wrist-to-palm axis 95 mm; design segment tolerance ±2 mm before bind. Outer chest/hip breadth and depth are new visual design decisions, not values to transplant from the 1.75 m scaffold.
6. **Movement envelopes:** at least the v4 rig limits recorded in `src/rig/canonicalV4Original.ts` (both minima and maxima on every defined axis), plus the category battery in `ORIGINAL_V1_MOVEMENT_ENVELOPE.json`: trunk flexion/extension/rotation/lateral flexion, hip hinge/deep squat/lunge, calf raise, push/pull/elevation, elbow and forearm, loaded wrist and thumb/finger grip. At O2 check neutral clearance and loop provision; full numerical deformation, contacts and silhouette evidence belong to O4–O6. Never claim pose acceptance from a rest-pose script.

`CHECKPOINT_ORIGINAL_V1_O2.bat <region_name>` is the required region gate. It includes the following numerical mesh audit, which may also be run directly for diagnostics:


```bat
blender --background ORIGINAL_V1_WORK/HomeGymPT_Male_ORIGINAL_v1.blend --python scripts/audit_original_o2_mesh_blender.py
```

It writes `reports/original_v1_o2_mesh_audit.json` with height, mirrored vertices, boundary/nonmanifold/winding errors, loose vertices and degenerate/duplicate faces. A draft region may leave other unfinished regions red; the command reports measurements and exits successfully during work. At O2 completion run the same command with `-- --strict` to require all numeric gates. It does not assess silhouette, joint landmarks, edge-loop quality or deformation. A deliberate open seam/asymmetry requires documented design review rather than a hidden threshold change.

The tolerances above are stage gates chosen for this original design, not measurements inherited from the legacy character. If a gate conflicts with sound anatomy, stop and document the proposed revision before changing the specification.

## Stop and recovery

If `ORIGINAL_V1_WORK/AUTHORING_TAINT.json` is created, stop the production session. Do not delete that file or clear the scene marker merely to make the audit pass. Inspect the recorded blocker, recover the latest passing checkpoint, rerun the guarded audits, and resume only from that clean checkpoint.

Stop on missing O1 Blend/provenance, an O1 Blend hash mismatch (do not simply edit the recorded hash; inspect/recover the verified O1 file and its evidence), failed rig export/audit, extra scene objects with unclear origin, any imported geometry or linked image, visible asymmetry outside the declared design, topology errors that cannot be explained by an intentional opening, or a need to fit to V15f/MakeHuman. Keep the last passing checkpoint. To recover, open the most recent checkpoint in `ORIGINAL_V1_WORK/checkpoints/`, rerun `node scripts/export-original-v4-rig.mjs --check` and the v4 Blender audit, record its SHA-256 and the discarded stage, then resume from the last approved region. Do not run the O1 count audit after editing geometry: its fixed 3,890/7,280 counts apply to the untouched scaffold only.

## O2 completion evidence

Record each region's before/after screenshots (front/side/three-quarter and bending views when relevant), topology counts/health, measurements, source-operation log, checkpoint SHA-256, and the Blender audit report. O2 ends only on human neutral-anatomy review; subsequent O3 topology, O4 binding and O5–O8 movement/contact/dressed/visual gates remain open.
