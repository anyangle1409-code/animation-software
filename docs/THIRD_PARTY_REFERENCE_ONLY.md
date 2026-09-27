# Third-party / legacy reference-only inventory

Nothing listed here may be included in a first-party standalone release package.

## Legacy character lineage
All imported-source-derived Home Gym PT male assets, including:
- V5/V6/V7 production/reference ancestors;
- V8 body/knee baseline;
- CORNER_FINAL variants;
- V9–V14 hand experiments/review candidates;
- V13e hand source;
- V15a–V15f descendants;
- correspondence files derived from those assets;
- Blender files/checkpoints based on those assets.

These may remain in engineering/review storage as reference benchmarks.

## Review imagery
Rendered comparisons and diagnostic boards produced from legacy/reference assets are engineering evidence only and must not enter the distributable product.

## Third-party runtime libraries currently present during migration
Until replaced:
- react
- react-dom
- three
- @react-three/fiber
- @react-three/drei
- zustand

These are migration dependencies, not approved components of the target standalone distributable.

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
Reference-only material can inform abstract measurements, tests, failure cases and acceptance criteria where appropriate. It must not be copied into first-party production geometry/code/assets.
