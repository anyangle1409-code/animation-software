# Final first-party operational build path

## Requirement

Development tools may be third-party.

The **finished operational package** may not contain or require third-party
runtime implementation or creative assets.

This means a development tool is acceptable only if its output does not inject a
third-party runtime into the distributed application.

## During migration

It is acceptable to continue using:
- TypeScript;
- Vite;
- Vitest;
- Playwright;
- npm/Node;
- Blender;
- Git/GitHub.

They are development/test tools.

## Final production path

After React/R3F/Drei/Three are removed, prefer the smallest transparent build:

1. project-owned application modules;
2. browser-native ES modules;
3. project-owned CSS;
4. project-owned shaders;
5. project-owned ORIGINAL v1 GLB/assets;
6. a project-owned deterministic copy/package script.

A bundler is not required merely because the development environment used one.

### TypeScript

TypeScript may remain an authoring tool if compilation targets modern browser
JavaScript and introduces no required runtime library/helper.

Before final release:
- target modern native ECMAScript;
- no imported tslib/runtime helpers;
- no source-map/vendor payload in production unless explicitly approved;
- scan the emitted JavaScript as part of the production-output audit.

Moving the final operational source to plain modern JavaScript is also valid if
that becomes simpler after the UI/renderer migration.

### Vite

Vite is permitted for development.

Do not assume a Vite production build is first-party merely because Vite itself
is not shipped as a package. If the emitted bundle contains Vite-generated
runtime/polyfill/helper implementation, that output does not meet the strict
target.

The final release should therefore either:
- use native ES modules/project-owned packaging; or
- prove through the production-output audit that any compiler/build output
  contains only transformed Home Gym PT code and approved platform-facing code.

## Platform features are allowed

Using browser/OS standards does not add a bundled third-party library:
- DOM;
- Canvas;
- WebGL2/WebGPU;
- requestAnimationFrame;
- fetch for packaged relative assets;
- localStorage;
- JSON;
- GLB/glTF format;
- system fonts.

The product must not contact external hosts for those features.

## Final evidence

The actual distributed folder—not just source—must pass:
1. source first-party/provenance audit;
2. runtime dependency count = 0;
3. production-output third-party scan;
4. deny-by-default release allowlist;
5. runtime network/API gate;
6. ORIGINAL v1 provenance/clean-room gates;
7. full behavioural test suite;
8. offline standalone acceptance.

No build tool is grandfathered into the product simply because it was useful
during development.
