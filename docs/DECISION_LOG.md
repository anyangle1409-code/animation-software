# Frozen decision log

These decisions remain in force until deliberately reopened with new evidence and an explicit update to this file.

## Product boundary

- Required target: distributable/runtime independence, not total independence from development tools.
- Blender, Git/GitHub, Python, Node/npm, TypeScript/Vite/Vitest/Playwright, GPT, and Claude may be used as development tools if their implementation/content is not shipped as prohibited production runtime or creative content.

## Character and provenance

- V15f is finished as a legacy/reference benchmark only. Do not resume production development on it.
- The imported/high-detail V5-V15f/CORNER_FINAL lineage is not eligible as the final first-party production character.
- MakeHuman-derived built-in anatomical body data is not eligible for the final first-party production path.
- ORIGINAL v1 is the clean-room first-party production character line.
- ORIGINAL v1 must originate independently; no legacy geometry, topology, UV, weights, materials, bind matrices, or projection transfer.
- The O1 procedural scaffold is a starting scaffold/evidence item, not finished production anatomy.
- `hgpt_canonical_v4_original` is the independent first-party production rig target.
- Preserve the project-owned 63-bone hierarchy/names/semantics, but use independently authored v4 rest dimensions rather than legacy-fit numerical transforms.

## Runtime

- The operational product has no declared third-party runtime dependencies.
- Zustand is replaced by the project-owned observable state system.
- React/ReactDOM, R3F/Drei and Three are removed from the live source and package
  graph; their guarded source-import ceilings are zero.
- Three is also removed from tests/development dependencies. Project-owned math,
  scene graph, skinning, GLB handling and WebGL rendering are the live path.
- Removed runtime frameworks/renderers may not be restored as compatibility
  shortcuts without deliberately reopening this frozen decision with new
  evidence and equivalent first-party/release gates.
- Development tools remain outside the distributable/runtime boundary as
  defined above; zero runtime dependency does not mean replacing Node,
  TypeScript, Vite, Vitest, Playwright, Blender, Git or AI development tools.
- Exercise mechanics, contacts, thresholds and authored biomechanics must not
  be altered to hide renderer/model/runtime defects.
- Dependency and import anti-creep gates remain mandatory even though migration
  is complete.

## Push-up contact / surface boundary

- The standard push-up keeps its accepted hand target at **z = 1.295 m**.
  The z = 1.34 m wrist-relief trial is rejected unless deliberately reopened
  with new evidence: it made each bottom forearm 95 mm off vertical against the
  frozen 60 mm maximum.
- Palm presentation is an engine/contact responsibility: hand locks explicitly
  aim the palm at the floor, and the floor grip must keep finger segments from
  hyperextending backward.
- Loaded flat-palm push-ups permit 90° of wrist extension on the anatomical extension side only. The previous 70° range stays inside the new range; deviation/twist limits are unchanged. This is a reviewed anatomical limit change, not a relaxed technique threshold.
- Forearm axial rotation may share an explicitly opted-in world hand-contact aim with the wrist. Use the bounded coarse/fine/step-halving search in `src/ik/solve.ts`; do not restore the dense 0.001° full sweep or increase test timeouts to compensate for it.
- Toe contact remains root-authored for the standard push-up. Do not add a
  second leg/on-ball IK lock as a cosmetic toe fix; that trial created
  unreachable targets, contact drift and regression failures.
- A toe-bone centre-line is not the production sole surface. Measured attempts
  to make that bone line flat required about 50–62 mm of whole-body lowering
  even when foot and toe rotation shared the correction. Do not re-author the
  whole push-up merely to make that internal bone line visually horizontal.
- Final toe/sole silhouette and optional shoes are production-character asset
  concerns. They may be solved in ORIGINAL v1 with independently authored
  foot/footwear geometry only after the relevant topology is stable, and must
  pass provenance, deformation, contact and promotion gates. Footwear must not
  be used to hide an actual kinematic/contact failure.

## Release / provenance boundary

- `npm run audit:standalone` is the pre-promotion operational gate; it must keep
  proving that unapproved ORIGINAL-v1 production assets are dormant.
- `npm run audit:release` is the final-mode release gate and must be capable of
  passing only after approved ORIGINAL-v1 promotion and active runtime cutover;
  it must not depend on a guard whose success requires promotion to remain
  blocked.
- The only supported future runtime activation mode is
  `original_v1_active`. It requires approved promotion, the exact dressed
  bundled ORIGINAL-v1 source to be reachable/registered/default, and retention
  of the procedural source as a diagnostic fallback.
- Release packaging remains deny-by-default. Before final asset promotion, only
  the verified first-party software shell (`index.html`, hashed JS and CSS) is
  approved. Production character GLBs require explicit exact-path/hash
  promotion.
- Operational exercise animation data is first-party project-authored source
  data. Its release approval is conditional on the executable provenance gate:
  no prerecorded/external animation assets, remote reads, bare third-party
  imports or legacy character implementation identities may enter
  `src/exercises`.
- Before final model approval, the only permitted pending **required** release
  components are the ORIGINAL character, ORIGINAL shorts, canonical v4 rig and
  final equipment/body fit. Any additional pending required component is a CI
  failure.

## Verification

- Physical visual/input parity remains a real gate; unit tests do not substitute for it.
- Blender materialisation and subjective anatomy review must not be claimed from a cloud-only run.
- Release remains deny-by-default until first-party assets/runtime are genuinely approved.
- No guard, threshold, test, or allowlist may be weakened merely to obtain a pass.

## AI collaboration

- The repository is authoritative, not GPT memory, Claude memory, or chat history.
- GPT and Claude follow the same operating contract, reference rules, quality stack, and tests.
- Old branches and historical handoffs are non-authoritative unless the current handoff explicitly names them.
