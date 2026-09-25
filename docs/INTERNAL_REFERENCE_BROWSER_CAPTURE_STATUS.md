# Browser review capture bridge — status

## Branch

`work/internal-reference-browser-capture-20260925`

Built on:

`work/internal-reference-engine-r2-scaffold-20260925`

Live source remains untouched.

## Implemented

### Browser capture registry
- `src/reference/browserCapture.ts`
- `src/reference/browserCapture.test.ts`

The pure reference layer can detect whether a browser capture bridge is mounted
and route deterministic capture requests through it.

### High-level review session
- `src/reference/reviewSession.ts`
- `src/reference/reviewSession.test.ts`

Given a known `ReferenceSpec`, exercise and clip it builds the semantic review
manifest, deterministic capture requests and local evidence batch.

### Actual R3F browser bridge
- `src/viewer/ReviewCaptureBridge.tsx`
- mounted inertly inside `Viewport.tsx`

The bridge:

1. snapshots Studio state;
2. pauses playback and seeks to the requested semantic time;
3. switches to character view, light backdrop, equipment visible and editor
   overlays hidden;
4. waits for the visible character and two render frames;
5. resolves the exact review camera;
6. renders to an offscreen `WebGLRenderTarget` at the requested size;
7. reads pixels locally;
8. vertically flips them;
9. encodes PNG using an in-memory canvas;
10. restores the renderer/camera and all captured Studio state.

No server, cloud API or network service is involved.

The grip close-up uses the visible character's own `handMatrix` when available,
falling back to canonical hand landmarks.

## Important safety property

The bridge is evidence-only. It does not:
- alter exercise mechanics;
- alter generator status;
- approve a candidate;
- change validation thresholds;
- write assets;
- save files automatically.

## Validation required

Run:

```
npm run typecheck
npm test -- src/reference/browserCapture.test.ts src/reference/reviewSession.test.ts
npm run build
npm test
```

Then manually open a curl candidate and verify the 20 image capture batch:
- 5 semantic moments;
- front, side, three-quarter and grip-close-up;
- 960x960 PNG;
- no grid/gizmos/IK handles;
- equipment visible;
- user viewport state restored after capture.

If the PNG is unexpectedly dark/light, inspect render-target colour space before
changing reference logic.
