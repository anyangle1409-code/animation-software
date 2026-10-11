# W1C closed-box candidates and two native source wrist checks

Branch `codex/source-triangle-broadphase-20261011`, isolated and stacked on
PR52 `217959a39b5a0bf45aad1638bb5056244dab6b5f`: all3 exact-head checks PASS,
[run38134592190](https://github.com/anyangle1409-code/animation-software/actions/runs/38134592190).
Shared PR48 plan at517596207 unchanged. Source geometry governs; no promotion.

Bounded design under owner autonomous authorization: exact rational closed
axis-aligned triangle-box sweep in original supplied coordinates. Keep original
indices, every island, duplicate and degenerate face; no local rebasing or BVH
rounding. Expire only boxes strictly left of a new start; each active cross-set
pair visited once, inclusiveY/Z comparisons. Box candidates are not intersections.
Input limit100000triangles per set; comparisons default250000/max2000000. Exceeded
limits raise without returning partial candidates. Shared exact coordinate
validation with intersection helper; no source-frame compatibility inferred.

## Tests, review and actual execution

Missing-feature test observed FAIL then8new tests PASS0.147s. Independent
exhaustive oracle over25seeded9x7sets, both argument orders; duplicates/degenerate
islands, closed contacts, smallest positive float gap, malformed inputs and
exact work-limit boundary.11intersection+12witness+18component PASS. Actual
Blender5.2.1LTS native synthetic original vertex/face-ID/common-frame test1PASS
0.021s, zero and1000offset representable fixtures, no patient laterality proof.

Independent read-only review: no Critical/Important findings. Minor CI dependency
path omission fixed: changes to imported intersection validator now trigger this
workflow. Reviewer independently tested46656box pairs: all17576overlaps exactly
once;30mixed int/float/subnormal sets and limit boundaries also PASS. Declined
anatomical/source-frame registration, private evidence, whole-mesh scope and
remote CI: local execution below is artifact/geometry evidence only.

Reused BOTH existing native nominal wrist scenes read-only; no scene rebuilding,
new rendering, medical downloads or repeated69707point queries. Each raw STL
SHA/size checked, every native polygon compared to its same-index original
triangle and all raw coordinates verified exactly. Native object matrices identity;
source and scene hashes unchanged after execution. Private files outsideGit.
Frozen source revisionac8de2b38f5ae1a0996053ca0639dd6ae43358f1, same donor source,
LPS header remains a declaration, NOT accepted units/laterality/HGPT registration.

| Nominal source pair | Raw faces | Cross-set comparisons | Complete box candidates | Exact intersections / refused candidates | Probe seconds |
| --- | --- | --- | --- | --- | --- |
| Lunate-left / scaphoid-left | 3204 /4156 | 246817 | 12 | 0 /0 | 1.601 |
| Lunate-right / scaphoid-right | 3220 /4244 | 290450 | 3 | 0 /0 | 1.621 |

All15conservative candidate pairs resolved by exact supplied-input triangle
predicates. This establishes no triangle intersection for these two supplied
raw pair lists, NOT accepted anatomical clearance, cartilage gap or normal joint
contact, whole-body nonintersection, independent donor imaging or physical
source-to-HGPT registration. No distance/clinical inference or source repair.
Source triangles and all native vertices preserved; all acceptance flags false.
Safe source SHA/scene/report hashes and scalar results:
`SOURCE_WRIST_EXACT_CANDIDATES_20261011.json`. Private reports include only source
face indices and metrics, not modified geometry. Do not rerun these two checks.

Historical full1097suite remains non-green20failures/41errors/1skip, not rerun.
Canonical readiness unchanged0READY/9PARTIAL/3BLOCKED. New Windows/Linux/native
CI requires newest exact pushed-head check. Other Work/Claude/GPT branches clean
and preserved; no renderer or canonical asset edits.

Next: verify newest CI; choose bounded original foot candidate enumeration only
with an explicit work budget and conservative handling of the known38left talus
degenerates (never silently remove them). Reuse saved source/native scenes.
For anatomy, source units/registration and independent articular patch or seven
qualified pelvic landmarks remain gates. Do not promote nonintersection into
anatomical readiness or repeat completed CT/source/witness processing.
