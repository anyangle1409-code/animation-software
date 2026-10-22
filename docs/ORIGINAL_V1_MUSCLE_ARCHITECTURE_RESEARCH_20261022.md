# ORIGINAL_v1 — Muscle architecture, interactions & deformation research handoff
**Date:** 2026-10-22 | **Status:** Research / engineering specification, NOT accepted anatomical or production geometry.  
**Owner goal:** original anatomically plausible male exercise demonstrator, with selectable subcutaneous muscles, natural whole-body deformation, no displayed genitals, and efficient first-party mobile playback. Target canonical skeleton is the verified ~1.82 m adult male, **not** an AI picture.  
**Read alongside:** \`docs/HOME_GYM_PT_SHARED_AUTONOMOUS_MASTER_PLAN.md\` on \`codex/shared-autonomous-master-plan-20261011\`, \`docs/SKELETON_FIRST_PRODUCTION_POLICY_20261008.md\` on \`codex/whole-body-biomechanics-audit-20261007\`, latest native ORIGINAL_v1 Blender/Claude branch, and PR #107 / #113. Confirm live HEADs; don't overwrite another lane.

## 0. Decision in one paragraph
Author a **real anatomical semantic layer** of individual muscles / muscle heads / tendons and their osseous attachments. Let joint transforms update each muscle-tendon path (including via points/wrapping) while separate activation channels control *visual* contraction. Drive a **single continuous final skin mesh** using good joint skinning, carefully scoped muscle/cage displacement and pose-space/contact corrective shapes. Do complex muscle/soft-tissue simulation offline in Blender when justified; for mobile, export verified joint animation plus morph targets or baked deformations if and only if the in-house GLB/WebGL2 path supports them. **Do not** assume simply nesting 3 meshes causes physical interaction. Do not import a third-party commercial character/mesh or ship an external runtime. Do not treat muscle visualization as measured muscle force.

## 1. Scientific basis, scope, and uncertainty
- Bone-to-bone joints define skeletal kinematics; muscle-tendon units span one or more joints and originate/insert on skeletal surfaces or fascia. Joint motion changes paths, length, leverage (moment arm), tendon tension and potential force. Multiple muscles can share an action; antagonists may co-contract to stabilize a joint. Muscles do not *push* joints; they pull through tensile force.
- Force depends on activation (not simply joint angle), muscle fibre force–length, force–velocity, passive fibre tension, tendon elasticity, pennation and individual physiology. Reference OpenSim Millard and Rajagopal. Typical \`F_tendon ≈ (F_active(a,l,v)+F_passive(l))cos(alpha)\` subject to tendon equilibrium; for an angular coordinate \`q\`, a moment-arm convention can be \`r(q)=-∂L_MT/∂q\`. Do not hardcode muscle force / EMG from pose. Anatomical activation and visible bulge are distinct channels.
- Fibre shortening generally changes transverse muscle dimensions; bodies are near incompressible but overall visible contours are modified by tendons, fascial constraints, fat, neighboring tissue, gravity and contact. "Contracting" a single muscle is not equivalent to uniformly scaling one Blender object. Tendons are much less bulky than contractile bellies.
- Surfaces/fascial planes can move relative to each other (especially scapula over rib cage; lats/teres/deltoid/pectoralis at axilla; glutes/adductors/iliopsoas around hip). Muscles can be adjacent, layered, intersect in projected view or share broad aponeuroses without being allowed to penetrate arbitrarily. Contact must not be confused with mesh self-intersection.
- Real forces cannot be inferred uniquely from the moving pose: multiple muscle coordination patterns produce similar joint torques; EMG is not direct muscle force. *Visually plausible teaching highlighting* is possible; quantitative claims require separate validated physiology/loading models.
- The AI-generated mannequin reference is for artistic silhouette only. Confirm origins/insertions against primary anatomy, bone landmarks and real movement references. No universal "correct" navel-to-groin length derived from image percentages. Never move verified joint centres to make mesh fit. Preserve smoothly genital-neutral mannequin skin with anatomical inguinal folds.
- OpenSim **engine** is Apache 2.0 but third-party example/model/mesh/data assets have separate rights. May use scientific geometry/properties as *reference with verified permissions*; do not ship their mesh or runtime. Keep licenses/provenance per source.
- All anatomy below is a **prioritised starting registry**, not an exhaustive attachment-site atlas or validated numerical parameter database. Annotate sources/confidence; verify detailed insertions, wrapping and axes before using them to drive original character.

## 2. Relationships that MUST be represented
**Shared actions and synergy:** deltoid+supraspinatus raise arm; upper/lower trapezius+serratus anterior upwardly rotate scapula; gluteus maximus+adductor magnus (posterior)+hamstrings extend hip; quadriceps extend knee; gastrocnemius+soleus plantarflex; biceps/brachialis/brachioradialis flex elbow.
**Antagonism / co-activation:** elbow flexors vs triceps; quadriceps vs hamstrings; hip flexors vs gluteal extensors; anterior/posterior deltoid and pec/lats across shoulder. Antagonists may activate together for stabilization and joint compressive stiffness.
**Multiple-joint constraints:** biceps long head crosses shoulder and elbow; rectus femoris crosses hip and knee; hamstrings except biceps short head cross hip and knee; gastrocnemius crosses knee and ankle; sartorius crosses hip and knee; triceps long head crosses shoulder and elbow. A joint-only length/volume driver is insufficient.
**Proximal stabilization:** scapular muscles, rotator cuff, abdominal wall and spinal extensors help establish force-transfer platforms. They don't necessarily produce large visible bulges.
**Wrap paths:** pectoral/deltoid edges across humeral head, rotator cuff around joint, latissimus/teres major forming posterior axillary fold, iliopsoas crossing anterior hip, gluteals over greater trochanter, quadriceps via patella to tibia, Achilles around posterior ankle, forearm tendons and digit pulleys. Use landmark-checked path control points/primitive wrap objects; reject "straight string between endpoints" where it cuts through bones or skin.
**Tissue surface mapping:** deep tissue -> superficial tissue -> dermis; avoid every muscle individually pulling the identical skin vertices at full weight (double-bulges). An explicit influence and blending strategy is necessary.

## 3. Prioritised muscle registry (bilateral unless midline)
Each line: **muscle / subdivision** — **major attachments & function** — **critical visual or interaction consideration**.
Detailed origin/insertion vertex anchors must be sourced, measured and mapped to the *actual rig*, not fabricated here.

### Tier A: shoulder, scapula, chest, armpit (first visible pilot)
- **Deltoid: anterior, middle, posterior** — lateral clavicle/acromion/scapular spine -> humeral deltoid tuberosity; flexion/abduction/extension, rotations vary by fibres; three distinct volumes wrapping humeral head, not one rigid shoulder cap.
- **Supraspinatus** — supraspinous fossa -> greater tubercle; assists elevation and stabilizes humeral head; deep under acromion/deltoid.
- **Infraspinatus** — infraspinous fossa -> greater tubercle; external rotation and cuff stability; deep to trapezius/rear deltoid.
- **Teres minor** — lateral scapular border -> greater tubercle; external rotation; border at posterior axilla.
- **Subscapularis** — anterior scapula -> lesser tubercle; internal rotation/cuff stability; front of scapula adjacent rib cage, not a superficial bulge.
- **Trapezius: superior/middle/inferior** — skull/cervicothoracic spine -> clavicle/acromion/scapular spine; elevation/retraction/upward rotation with segment-specific roles; move with scapula and clavicle, not static upper back.
- **Serratus anterior: upper/lower bundles** — lateral ribs -> anterior medial scapular border; protraction/upward rotation/posterior tilt; visible saw-tooth strips lateral ribs and essential shoulder blade control.
- **Rhomboid major/minor; levator scapulae** — spine/upper cervical -> scapular medial/superior borders; retraction/elevation/downward rotation control; deep to trapezius.
- **Pectoralis major: clavicular, sternocostal/abdominal contributions** — clavicle/sternum/costal cartilage -> proximal humerus; adduction/flexion/internal rotation depending arm position; folds into *anterior* armpit, slides/deforms on overhead reach and press.
- **Pectoralis minor** — ribs 3-5 -> coracoid; scapular anterior tilt/depression/stabilization; deep to pec major, not separate skin bulge.
- **Latissimus dorsi** — thoracolumbar fascia/iliac crest/lower ribs -> proximal humerus; extension/adduction/internal rotation, contributes *posterior axillary fold*, path wraps side of chest.
- **Teres major** — inferior/lateral scapula -> proximal humerus; extension/adduction/internal rotation, adjacent latissimus posterior axillary fold.
- **Subclavius, coracobrachialis** — small but stabilizing/anterior upper-arm; consider semantic proxy first.
- **Triceps: long/lateral/medial heads** — scapula (long)/humerus (other heads) -> olecranon; elbow extension; long head involved at shoulder and posterior axilla.
- **Biceps brachii: long/short heads** — scapular supraglenoid/coracoid -> radial tuberosity/aponeurosis; supination+elbow flexion, shoulder influence; muscle belly shortens and bulges in curl.
- **Brachialis and brachioradialis** — humerus -> ulna / distal radius; major elbow-flexion contributors; brachialis deep under biceps, brachioradialis visible forearm.
- **Forearm pronator teres, pronator quadratus, supinator, major wrist/finger flexors/extensors** — radius/ulna/humeral epicondyle origins to distal forearm/hand; wrist orientation, pronation/supination and grip, tendon paths must not intersect wrist skin.

### Tier A: pelvis, groin, buttocks and thighs (second pilot; current visible defect)
- **Iliacus + psoas major (iliopsoas)** — iliac fossa/lumbar vertebrae -> femoral lesser trochanter; powerful hip flexion; *deep*, should not be drawn as large groin surface bulge.
- **Gluteus maximus** — posterior ilium/sacrum -> IT band/gluteal tuberosity; powerful hip extension/external rotation; large superficial posterior contour, flattening/stretch changes under deep squat. Gluteal fold/crease is not a rigid welded seam.
- **Gluteus medius/minimus** — ilium -> greater trochanter; pelvic frontal-plane stabilization/abduction, fibre-specific rotations; medius partly under maximus and fascia, deep minimus.
- **Tensor fasciae latae + iliotibial tract** — anterior iliac crest/ASIS -> IT tract to lateral tibia; contributes hip flexion/abduction/rotation and lateral fascia tension. **IT tract is fascia, not a muscle belly.**
- **Sartorius** — ASIS -> medial proximal tibia (pes anserinus); flexes/abducts/externally rotates hip and flexes knee; oblique *superficial ribbon* crossing quadriceps/adductors (important overlapping appearance without intersection).
- **Rectus femoris** — AIIS/above acetabulum -> patella via quadriceps tendon, then tibial tuberosity via patellar ligament; hip flexion + knee extension; hip/knee combined shape.
- **Vastus lateralis/medialis/intermedius** — proximal/anterior femur -> common quadriceps tendon/patella; knee extension; intermedius deep to rectus femoris; shape of front thigh/cap around knee.
- **Pectineus** — pubis -> proximal femur; hip adduction/assists flexion; small upper anterior-medial hip.
- **Adductor longus/brevis/magnus** — pubis/ischiopubic region -> medial/posterior femur; adduction; magnus posterior portion also strong hip extension especially flexed position; create distinct planes/inner-thigh volumes without centerline pinching.
- **Gracilis** — pubic region -> pes anserinus at medial proximal tibia; adduction and knee flexion; slim medial-thigh sheet.
- **Deep external rotators (piriformis, obturator internus/externus, superior/inferior gemelli, quadratus femoris)** — pelvis -> proximal femur; hip stabilization/rotation; generally invisible on final skin; semantic/deep geometry LOD.
- **Hamstrings: biceps femoris long/short, semitendinosus, semimembranosus** — ischial tuberosity (except short biceps from femur) -> fibula/lateral knee or medial tibia; hip extension (except short head) and knee flexion. Tendons emerge from gluteal region; glute-max overlying them, no abrupt "butt shelf."
- **Deep hip structures:** hip capsule, inguinal ligament, fascial compartments/soft tissue: these are NOT contractile muscles but strongly affect appearance/hip clearance. Central crotch is a *skin transition*, not a single muscle origin; keep genital-neutral mannequin surface. The anterior inguinal crease travels diagonally from iliac region toward pubic region, not a horizontal belt seam.

### Tier B: core, neck, distal legs and feet (needed for whole-body exercises)
- **Rectus abdominis; external/internal oblique; transversus abdominis** — ribs/xiphoid/pubis/iliac crest/fascia/linea alba; trunk flexion/rotation/pressure/stabilization; layer abdominal wall (transversus deepest), don't animate abs solely from flexion angle.
- **Erector spinae subdivisions, multifidus, quadratus lumborum** — spine/pelvis/ribs; spinal extension, segmental support, lateral flexion and postural endurance; lumbar curve and trunk twist matter more than six-pack sculpt.
- **Diaphragm & intercostal groups** — respiratory expansion; small controlled chest/rib deformation optional, not inferred from exercise intensity without physiology.
- **Gastrocnemius (medial/lateral) and soleus** — femur/tibia-fibula -> calcaneus through Achilles; plantarflexion, gastrocnemius also knee flexion. Calf shape/length depends knee bend and ankle.
- **Tibialis anterior; tibialis posterior; fibularis longus/brevis; extensor/flexor hallucis and digitorum longus** — leg to foot/toes; dorsiflexion/inversion/eversion/arch and toe control; preserve foot-ground contact.
- **Intrinsic plantar muscles** — shape/toe support and gripping, lower visual priority than correct forefoot and Achilles.
- **Cervical sternocleidomastoid, scalenes, deep neck stabilizers** — head/neck pose and clavicle contours; avoid aggressive volume effects.

### Tier C: hand precision, education and future progression
- **Thenar group** (abductor/flexor/opponens pollicis; plus adductor pollicis), **hypothenar group**, **dorsal/palmar interossei**, **lumbricals** — complex thumb opposition, MCP flexion/IP extension, fine grip. Extrinsic digital flexor tendons arise in forearm and travel through hand. First fix actual thumb opposition and bilateral finger-axis signs (PR #113) before sculpting intrinsic muscle bulbs.
- Jaw/facial/sole minor muscles can follow once Tier A/B deformation passes; must not block release.

## 4. Movement relationship matrix (role is context-specific, not quantified activation)
| Motion & phase | Primary movement producers | Coupled/stabilizing groups | Critical surface changes / collision |
|---|---|---|---|
| Shoulder press upward | anterior/middle deltoid, triceps, supraspinatus | upper/lower trap + serratus scapular upward rotation; rotator cuff joint centring; trunk stabilizers | scapula upward-rotates/posterior tilts, deltoid/pec/lats redistribute around axilla, avoid shoulder-top collapse |
| Overhead reach / dead hang | elevation/reach uses deltoid/scapular rotators; *passive hang* may be low agonist drive | cuff + scapular stabilizers variable with active/passive hang | lat and pec lengthen, axillary folds reorient, scapula translates/rotates, skin stretches without opening seams |
| Push-up / bench press | pec major, anterior deltoid, triceps | serratus anterior protraction; rotator cuff; torso brace | front armpit fold across shoulder horizontal adduction; avoid chest/deltoid ballooning |
| Row | lat, middle trap/rhomboids, posterior deltoid, biceps/brachialis | cuff, spinal extensors, legs depend posture | retract scapulae, contract lats, elbow flexion, back/axilla contours |
| Pull-up | lat/teres major, elbow flexors | scapular depressors/retractors, cuff, grip | posterior axillary fold thickens as arm lowers, scapula moves; avoid static shoulder blades |
| Biceps curl | biceps, brachialis, brachioradialis | wrist stabilizers, antagonistic triceps variable | biceps belly fullness and elbow crease, forearm proximal bulge; supination variation |
| Squat lowering / rising | quadriceps, glute max, adductor magnus posterior, varying hamstrings | glute med/min and trunk stabilization, calf/ankle | hip flexion folds groin/abdomen, buttocks reshape, quad length/contour, thigh-calf compression; pelvic tilt |
| Hip hinge/deadlift | glute max, hamstrings, adductor magnus extensor | erector spinae / abdominals brace, lats stabilize, grip | hamstring lengthening, glute/upper-thigh transition, torso shifts rather than weld deformation |
| Lunge/step-up | quadriceps, glute max/adductor magnus, calves | glute med pelvic control, trunk brace | asymmetric femoral flexion, groin folds, contact, lateral pelvis |
| Calf raise | gastrocnemius, soleus | tibialis posterior/peroneals foot stability | calf shortening, Achilles path; maintain toes/forefoot contact |
| Trunk rotation / plank | abdominals/obliques, multifidus/erectors | scapular/hip stabilizers | skin/fascia shearing, ribcage/pelvis rotation, avoid torso candy-wrapper twist |
| Bar/dumbbell grip | flexor digitorum superficialis/profundus, thumb flexors/opponens, wrist stabilizers | lumbricals/interossei modulate finger joints | thumb opposition, tendon/wrist clearance, each digit direction calibrated |

**Contraction types:** Concentric = muscle-tendon shortening during active torque generation; eccentric = active lengthening while resisting torque; isometric = activation with little macroscopic length change. "Exercise target muscle" ≠ every frame of actual positive shortening. Load/direction and posture distinguish them.

## 5. Rig and skin workflow: proposed hybrid
1. **Input contract**: locked/approved bone coordinate IDs and rest transforms; separately labelled *anatomical surface guides* (not straight rig rods). Derive all local landmarks from actual anatomical skeleton; never fake missing CT landmarks.
2. **Muscle registry**: stable IDs; side; region; origin/insertion bone/landmark; path via-points; wrap geometry; joint crossings; tendon vs belly proportions; superficial/deep visibility; antagonists/synergists; skin influence mask; source URLs/rights/confidence; tests; runtime LOD status. Bilateral symmetry checks but do not assume local bone axes are mirror images.
3. **Rest geometry**: original custom authoring: tendon paths + fusiform/pennate, flat/fan/segmental bellies; deep muscles do not penetrate bones; upper layer envelope fits **inside** existing skin with appropriate fat/fascial gap. Avoid layering full-scale muscle bulges atop already muscled external mesh (double counting). Rest silhouette should be stable; deform from correct anatomical volumes, not thicken character.
4. **Kinematic update**: track origin/insertion and all via-points as segments move; enforce finite/continuous muscle length, anatomical wrap and shortest viable path; account for cross-joint muscles.
5. **Contraction parameter**: independent \`activation\` (0..1) and pose-dependent fibre length; conservative belly volume compensation constrained by anatomy and neighbouring layers; not per-frame random swelling. Infer scripted *qualitative* educational state from defined exercise phase, but don't claim to solve exact muscle activations.
6. **Skin transfer**: baseline original mesh with improved influence weights; pose-space morphs at hip flex/abduction, knee flex, shoulder reach/horizontal adduction, elbow, torso; optional cage or simulated musculature displacement only where demonstrably improves paired real-render comparison. Avoid overdriving/deep-to-skin artefacts.
7. **Sliding / contact**: constrain superficial and deep soft tissue to follow tangential movement, maintain minimum bone clearance, recover shape at rest. Distinguish expected soft-tissue contact from illegal triangle intersections. Prevent gluteal shelf, upper-thigh horizontal banding, shoulder-top folding, armpit punctures. Favor region-specific masks.
8. **Evaluation order**: (a) rig only; (b) muscles visible, hide skin; (c) skin only; (d) skin with activated deformation; (e) overlay side-by-side identical cameras; (f) mobile import parity. Toggle layers independently for diagnosis and future app anatomy lessons.
9. **Export reality**: GLB expresses joints, skinned mesh, morph-target deltas/weights and their animations; it does not natively encode arbitrary Blender muscle physics, surface deform modifiers, drivers, tendon wrapping solvers or subcutaneous contact simulation. Bake to supported channels; validate normals, target names, mesh ordering and rest/bind parity. Do **not** ship hidden high-poly muscle meshes in default mobile runtime merely for educational visibility; use explicit lightweight optional anatomy view asset/LOD. First-party renderer must implement and test supported morphs and fallback if absent.

## 6. Pilot implementation and hard gates
**P0 inventory, DO NOT EDIT GEOMETRY:** fetch current latest Claude Blender checkpoint, PR #107 rejected native DQ volume trial, PR #113 nine movement benchmarks, shape/rigger/export branch status, first-party GLB importer. Confirm exact 67-joint source and what metadata exists; list every pre-existing deformation defect. Record SHA and no overwrite.
**P1 machine-readable scientific catalogue (no Blender required):** start with tier-A 24+ named region/head definitions per side, all referenced from verifiable anatomy. JSON schema with landmarks, origin/insertion, path, joint crossings, neighbouring/overlying muscles, intended impact, source ID and confidence, and explicit \`not_implemented\` status. Add tests for missing sources, unique names, bilateral field completeness, bone ID validity. Don't copy assets.
**P2 shoulder pilot (Blender):** trapezius 3 subdivisions, serratus, deltoid 3, 4 cuff muscles, pec major, lat, teres major, biceps long/triceps long (progressively). Show neutral, 45°, 90°, 120°, 150–160° overhead, front/back/side/45°. Measure anatomical scapula/clavicle/GH coupling and paths. Do not reuse the rejected global DQ solution. Deep muscles may be simple proxies.
**P3 pelvis pilot (Blender):** glute max/med/min, iliopsoas (deep), TFL, adductor longus/magnus, sartorius, rectus femoris, hamstrings; inspect 0, 45, 90, 110° hip flexion, hip abduction/extension and deep squat plus front/side/back. Prior screenshot indicates upper-thigh horizontal bands and pinched midline; FIRST isolate topology, normals, overlapping surfaces, modifier order and weights. Don't claim cause before checking.
**P4 other groups**: core and neck, quadriceps/calf/Achilles, forearm/hand, foot, lower-priority stabilizers. Never block high-priority defect fix on modelling microscopic deep anatomy.
**P5 runtime**: agree on a small, semantic, first-party deformation contract with Lane G, versioned separately from PT_MODEL_VERSION=1.0; export *one* shoulder and one hip morph proof. Import and compare Blender vs native WebGL2 frame by frame; static GLB mesh/rig weights alone does not imply morph support. Preserve fallback skin if unsupported.
**P6 whole-body regression**: existing nine benchmarks plus push-up, active/passive hang, curl, overhead reach, hinge at multiple loads; compare multiple frames not just extremes. Bilateral symmetry (coordinate-aware), continuous derivatives/no pops, no reversed normals or cracks, no new 0.1x collapsed face or >2x stretch growth vs recorded baseline, self-intersections separated by expected contact, surface volume trend, no finger/foot ground penetration. Thresholds are engineering diagnostics **not physiological acceptance**. Record actual before/after counts and phone-view renders.
**P7 review and promotion**: source linkage + peer review + actual Blender executed tests + mobile parity + screenshot pairs + owner approval; no auto-merge, no deploy, no silent source replacement. Mark PROVISIONAL until all accepted. Cache results and avoid repeating old experiments.

## 7. Cost/performance/usage optimization
- First build **one region at a time**: shoulder then pelvis; animate under skin only after its neutral anatomy/path is plausible. Do not model all ~600 muscles first, do not force finite-element whole-body solve.
- Progressive semantic LOD: LOD0 superficial muscle envelopes used for visuals/skin; LOD1 multi-bundle anatomy (education mode); LOD2 full detailed research-only/offline. Skip unseen detailed muscles in mobile default draw.
- Run batch scripted 9-frame verification initially; on failure capture exact pose/metric/pairs rather than rerendering entire atlas. Reuse already measured PR #107/#113 numerical baselines.
- One source, one JSON muscle entry, one rig mapping, one automated pose test per item. Save reusable source/review ledger and mark \`verified\`, \`inferred\`, \`blocked\`, \`approximation\` explicitly.
- Shape-key corrective authoring should not break rigged neutral pose. Use local masks, grouped blends/conditional drivers; gate at low/high angles and endpoints to avoid discontinuities.
- Keep producer/editor and runtime contracts separated; prefer offline authoring and sparse GPU morphs over per-frame CPU muscle simulation.
- Do not change validated skeletal lengths or joint axes for surface fit. Do not copy training images as final meshes. Preserve owner no-genitals design.
- Claude should automate all independent scientific/schema/planning tasks without waiting for laptop, then use actual Blender where needed; never claim execution unless actually performed.

## 8. Source ledger (authoritative supporting research / technical docs)
A. OpenSim official model overview: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53088473  
B. OpenSim tutorial on geometry, moment arms, force: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53088700/Tutorial+1+  
C. OpenSim Millard muscle models: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53090555  
D. Rajagopal et al. 2016 80 lower-limb MTUs, 37 DoF: https://pmc.ncbi.nlm.nih.gov/articles/PMC5507211/  
E. Lai et al. 2017 high-flexion/coactivation modifications: https://pmc.ncbi.nlm.nih.gov/articles/PMC5989715/  
F. OpenSim sample model notes (not an asset redistribution license): https://github.com/opensim-org/opensim-models/blob/master/Models/Rajagopal/README.txt  
G. Seth et al. independent scapular motion/thoracoscapular model: https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2019.00090/full  
H. Scapular 3D motion variability (2025 review): https://pmc.ncbi.nlm.nih.gov/articles/PMC12398250/  
I. Shoulder rotator cuff biomechanics: https://pmc.ncbi.nlm.nih.gov/articles/PMC8111677/  
J. NCBI anatomy shoulder origins/insertions: https://www.ncbi.nlm.nih.gov/sites/books/NBK482410/  
K. NCBI detailed hip muscle origins/insertions: https://www.ncbi.nlm.nih.gov/books/NBK526019/  
L. NCBI sartorius and hip antagonists: https://www.ncbi.nlm.nih.gov/sites/books/NBK532889/  
M. NCBI anterior thigh: https://www.ncbi.nlm.nih.gov/sites/books/NBK482445/  
N. NCBI posterior femur/hamstring: https://www.ncbi.nlm.nih.gov/books/NBK500008/  
O. NCBI calf: https://www.ncbi.nlm.nih.gov/books/NBK459362/  
P. NCBI abdominal wall/fascial layers: https://www.ncbi.nlm.nih.gov/sites/books/NBK553137/  
Q. NCBI hand function: https://www.ncbi.nlm.nih.gov/books/NBK539810/  
R. 2024 consensus limitations of EMG to force: https://www.sciencedirect.com/science/article/pii/S1050641124000543  
S. Squat mechanics review: https://pmc.ncbi.nlm.nih.gov/articles/PMC10987311/  
T. NCBI latissimus path/actions: https://www.ncbi.nlm.nih.gov/sites/books/NBK448120/  
U. Khronos GLTF morphs/skin/animation specification: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html  
V. Blender official animation drivers and shape keys: https://www.blender.org/features/animation/  
W. Blender glTF exporter settings: https://github.com/KhronosGroup/glTF-Blender-IO/blob/main/docs/blender_docs/scene_gltf2.rst  
X. Blender surface deform (an authoring technique; not automatically exported): https://docs.staging.blender.org/manual/en/latest/modeling/modifiers/deform/surface_deform.html  
Y. OpenSim code license and model-license warning: https://github.com/opensim-org/opensim-core  

**Cautions:** educational StatPearls can be imprecise on small muscle innervation; rely on primary clinical atlases / original studies for any high-risk landmark or quantitative claim. OpenSim lower-limb gait parameters do NOT establish shoulder exercise activation or individual user's forces. GLB support must be validated in Home Gym PT first-party engine. No research here proves exact 3D muscle surfaces/weights or a clinically accurate character.

## 9. Immediate deliverables for Claude (next bounded session)
1. Fetch HEADs and read this document + PR #107/#113, report missing records as missing.
2. Publish source-backed machine-readable Tier-A muscle registry and loader/validation tests without touching production geometry; include shoulder and pelvis attachments, crossings, layer ordering, neighbor links.
3. Produce region-specific shape/deformation candidate plan and source geometry requirements, with explicit authoring-vs-app distinction.
4. Once actual Blender available, implement **reversible** shoulder and hip pilots one at a time with generated diagnostic assets, automated measurement and no changes to accepted skeleton.
5. Hand Lane G precise minimal GLB morph/skeletal contract for app parity. No merge/deploy/production approval.
