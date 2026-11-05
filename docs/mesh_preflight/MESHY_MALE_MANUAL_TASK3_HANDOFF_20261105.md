# Home Gym PT — Meshy Male Manual Retopology: Task 3 checkpoint audit (2026-11-05)

**Status: PARTIAL / NOT APPROVED.** This records a separate, read-only checkpoint inspection. It does not alter any Blender asset, rig, production branch, Claude work, PT-App, or source image/geometry. The **approved 1.82 m male Meshy source** controls exterior appearance; the verified Home Gym PT canonical skeleton controls anatomy and motion.

## Source and checkpoint (not stored in this public repository)

- Locked original high-detail source: `HGPT_Meshy_Male_Pro_1.82m_Clean_Unrigged.blend`, SHA-256 `b41518437550a6aa57df65c80c05fbc7955053619d94efa83f6587f54efe4e9f`.
- Last male retopology WIP: `HGPT_Male_Retopo_03_TorsoHead_WIP.blend`, SHA-256 `d5de4b71c5bdafc19b8ea342a2cf435ed12586b48ad587cc6c63c9a6bcecd6c6`.
- Original relative linked source path embedded in checkpoint: `//../source/HGPT_Meshy_Male_Pro_1.82m_Clean_Unrigged.blend`. Preserve `manual_retopology/source/` and `manual_retopology/work/` as adjacent subfolders.
- The files and read-only Python diagnostic are held in the owner's ChatGPT Library and downloadable portable checkpoint ZIP. **Do not add paid/licensed Meshy 3D geometry, textures or .blend/.glb to this public GitHub repo.**

## Independently inspected Blender 4.3 binary arrays

| Field | Stored WIP mesh |
|---|---:|
| Explicitly stored production mesh datablocks | 1 |
| Vertices | 324 |
| Edges | 545 |
| Quad faces | 224 |
| Face corners | 896 |
| Face-boundary edges | 122 |
| Edges not used by any face | 36 |
| Edges used by >2 faces | 0 |
| Embedded armatures | 0 |

These counts refer to the **unmodified local mesh data before modifier evaluation**. The scaffold covers one half of the head/torso (X=0 to 0.195 m, Z=0.82 to 1.81 m); bilateral appearance in the preview cannot be treated as separately completed full-body topology. Component analysis reveals multiple loose construction components. The source body is library-linked, not embedded. The WIP is a **construction scaffold only**; no production skin weights, corrective shapes, exercise deformations or runtime GLB have been approved.

Visual previews inspected: `topology_wip_front.png`, `topology_wip_back.png`, `topology_wip_three_quarter.png`. Source visual remains approved; WIP topology and silhouette **not yet accepted**.

## Next actions in Blender — do not skip or auto-mark complete

1. Open the portable WIP with its relative linked source; independently verify the source hash and external reference resolution. Do not edit or overwrite the locked source.
2. Preserve WIP snapshot, then finish **manual** head, eye/mouth loops, neck, chest/back, and clavicle/shoulder-socket quad edge flow. Ensure the posterior deltoid/armpit transition is designed for 105° and 170° shoulder elevation. Do not use auto-remesh/QuadriFlow/decimation as production topology.
3. Check face identity, shoulder width, chest/lat, waist/abdomen from approved front/back/side/three-quarter views against source. The initial scaffold is not ready to pass silhouette matching.
4. Triage all 122 face-boundary edges, 36 face-unused edges and isolated vertex components. Retain only clearly documented intentional limb/pelvis openings during the open-stage gate. Work on production copy only.
5. Save **new** `HGPT_Male_Retopo_03_TorsoHead.blend` only when Task 3 is genuinely complete; include fresh topology audit and detailed face, back shoulder and armpit comparison renders.
6. Then manual Task 4 arms/hands, Task 5 pelvis/legs, Task 6 closed anatomical body + UV/bake, Task 7 separate clothing/hair, Task 8 verified canonical skeleton fit, Task 9 controlled weights, Task 10 shoulder-press/squat/curl/push-up/pull-up deformation, Task 11 iPhone GLB audit. Female follows separately **only after male passes all gates**.

## Testing policy

- Do not confuse numerical face counts, Blender file creation or passing syntax checks with successful anatomical deformation.
- Gate 1 must prove **source-matched silhouette and anatomy**, useful joint topology, correct neutral pose, and deliberate planned openings at intermediate stage.
- Gate 2 must verify bone registry, hierarchy, bone roll, canonical source and landmark fit. Do not silently use unverified W8/body_v2.
- Gate 3 must test isolated shoulder (45°, 90°, 105°, 135°, 170°), scapula/clavicle, elbows, forearm twists, pelvis, knees, feet and fingers before correctives.
- Gate 4 must test full exercise phases, independent forward raise and shoulder press top/mid with front/back/side evidence, with no rear-shoulder fold or groin collapse.
- Gate 5 must measure actual iPhone runtime performance in the first-party app.

No production completion or readiness claim is authorized until a full verified Blender session, model exercise renders, and owner review. This audit could not run the `bpy` checker in the originating session (no Blender runtime), but direct binary-structure data and SHA hashes were verified.
