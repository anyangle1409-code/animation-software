# Third-party / legacy reference-only inventory

Nothing listed here may be included in a first-party standalone release package or treated as an active implementation source.

## Preserved recovery checkpoint

`archive/pre-makehuman-removal-20260928` preserves the exact pre-removal state at:

`502adedc9fd5c7ddbee1b74cd0472879de6fb047`

It exists only for recovery/audit history. Do not develop from it or copy legacy/derived production content back into the standalone branch.

## Legacy character lineage

All imported-source-derived Home Gym PT male assets, including V5–V15f/CORNER_FINAL and related experimental descendants, are historical reference only. The active standalone branch no longer carries the old mesh handoff/review bundles or the hard-wired V8 runtime path.

## MakeHuman-derived anatomical body

The MakeHuman-derived anatomical source/data lineage has been removed from the active standalone branch. Its pre-removal state is recoverable from the archive checkpoint above.

Do not restore its geometry, encoded positions/indices/weights/colours, character-specific repairs, or generator into the active production path. Generic project-authored biomechanics that were independently useful must live in first-party modules, not in restored legacy files.

## Review imagery

Rendered comparisons and diagnostic boards produced from legacy/reference assets are engineering evidence only and must not enter the distributable product.

## Runtime dependency removal status

The runtime migration is complete on the active standalone branch.

- declared runtime dependencies: **0**
- React / ReactDOM imports and packages: **0**
- R3F / Drei imports and packages: **0**
- Zustand imports and package: **0**
- Three imports in operational source and tests: **0**
- Three and @types/three packages: **removed**

Do not restore any removed framework/renderer as a compatibility shortcut. Physical
desktop/iPhone parity remains a release-quality acceptance gate, not permission
to reintroduce a third-party runtime dependency.

## Development tooling

Development tools may be used without being shipped as product content. Current examples include:

- Blender
- Git/GitHub
- Python
- Node/npm
- TypeScript compiler
- Vite
- Vitest
- Playwright
- GPT/Claude development assistance

If the project later chooses Level-2 source/build independence, this list becomes a separate migration target. It is not required merely to achieve a first-party shipped runtime.

## Rule

Reference-only material can inform explicitly authorised abstract measurements, tests, failure cases and acceptance criteria. It must not be copied into first-party production geometry, code, assets, weights, bind data, materials or other implementation content.
