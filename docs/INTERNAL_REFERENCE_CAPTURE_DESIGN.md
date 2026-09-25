# R2 local review capture — implementation design

This file removes the need to rediscover how review images should be captured from the current React/Three viewer.

## Existing pieces

- `src/reference/reviewManifest.ts` already chooses semantic times and camera ids.
- `src/viewer/cameras.ts` already resolves front/right/three-quarter presets.
- `src/viewer/Viewport.tsx` already owns the R3F `Canvas`, camera, scene and playback frame.
- `useStudio` already exposes time and camera selection.

Do not create a second renderer unless the current canvas proves unsuitable.

## First implementation

Add a small capture controller inside the existing viewport tree.

It should:

1. receive one `ReviewCapture`;
2. pause playback;
3. set the studio time to the capture's semantic time;
4. move the camera to the requested preset;
5. wait until both the frame and camera have settled;
6. render one deterministic frame;
7. copy the WebGL canvas to a PNG blob/data URL;
8. return the image with metadata from the manifest.

Do not save images to a server. Keep them in memory/session state unless the user explicitly exports them.

## Determinism

For automated comparison, capture should temporarily force:

- fixed canvas pixel dimensions;
- fixed DPR;
- fixed backdrop;
- grid off;
- gizmos/IK handles off;
- selection cleared;
- animation paused;
- fixed camera preset;
- same character/view mode for reference and candidate.

Restore the user's viewport state after the capture batch.

## Focus/grip close-up

The current `focus` camera depends on selected bone and animated interpolation, so it is not deterministic enough for automated evidence.

For the first curl implementation, replace the manifest's `grip_closeup` capture at runtime with an explicit camera setup computed from the midpoint of `hand_l` and `hand_r`:

- target = midpoint of the two hand joints;
- camera offset = approximately (0.7, 0.25, 0.9) in world coordinates;
- FOV around 30–34°.

The exact values should be calibrated once and then stored as reference-view data, not guessed on every capture.

## Suggested code boundaries

```
src/reference/
  reviewManifest.ts      # already implemented
  captureTypes.ts        # image/evidence records
  captureController.ts   # state machine; no React
src/viewer/
  ReviewCaptureBridge.tsx # R3F access to camera/gl/scene
```

Keep capture scheduling/reference semantics out of `Viewport.tsx`; the viewport should expose the rendering capability, not own reference policy.

## Evidence record

Each captured image should carry:

```ts
interface ReviewImageEvidence {
  referenceId: string;
  exerciseId: string;
  captureId: string;
  momentId: string;
  time: number;
  normalizedTime: number;
  viewId: string;
  width: number;
  height: number;
  mimeType: 'image/png';
  image: Blob;
}
```

Later R3 can consume this without knowing anything about React or the Studio store.

## Test strategy

Unit tests:
- manifest ordering;
- state save/restore;
- explicit camera setup;
- capture ids and metadata.

Browser/Playwright test:
- open a known curl;
- capture the same review frame twice;
- assert dimensions and metadata match;
- use a tolerant pixel/hash metric only after deterministic lighting/camera is proven.

Do not make a screenshot golden image the sole biomechanical truth.
