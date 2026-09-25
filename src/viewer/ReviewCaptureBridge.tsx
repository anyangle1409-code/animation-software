import { useEffect } from 'react';
import { useThree } from '@react-three/fiber';
import { Color, Matrix4, MeshBasicMaterial, PerspectiveCamera, Quaternion, Vector3, WebGLRenderTarget } from 'three';
import { useCharacter } from '../editor/characterStore';
import { skeleton, useStudio } from '../editor/store';
import type { Backdrop, Selection, ViewMode } from '../editor/store';
import type { CameraPresetId } from './cameraTypes';
import { installBrowserReviewCaptureAdapter } from '../reference/browserCapture';
import type { ReviewCaptureAdapter } from '../reference/captureController';
import type { ReviewCaptureRequest } from '../reference/evidence';
import { sampleLandmarks } from '../reference/landmarks';
import { resolveReviewCamera } from '../reference/reviewCamera';
import type { ReferenceReviewView } from '../reference/types';
import { analyseSilhouetteRgba, silhouetteSanity } from '../reference/silhouette';

interface ViewportSnapshot {
  studio: {
    time: number;
    playing: boolean;
    camera: CameraPresetId;
    viewMode: ViewMode;
    showEquipment: boolean;
    showIkHandles: boolean;
    showGrid: boolean;
    backdrop: Backdrop;
    selection: Selection;
  };
  character: {
    correctivesPreview: boolean;
  };
  camera: {
    position: Vector3;
    quaternion: Quaternion;
    fov: number;
    aspect: number;
    near: number;
    far: number;
  };
}

const nextFrame = () =>
  new Promise<void>((resolve) => {
    requestAnimationFrame(() => resolve());
  });

async function waitForVisibleCharacter(maxFrames = 180): Promise<void> {
  for (let frame = 0; frame < maxFrames; frame += 1) {
    if (useCharacter.getState().active) return;
    await nextFrame();
  }
  throw new Error('The active character did not become ready for review capture.');
}

function reviewLandmarks(request: ReviewCaptureRequest) {
  const bones =
    request.camera.target === 'hands'
      ? (['hand_l', 'hand_r'] as const)
      : request.camera.target === 'shoulders'
        ? (['upperarm_l', 'upperarm_r'] as const)
        : request.camera.target === 'feet'
          ? (['foot_l', 'foot_r', 'shin_l', 'shin_r'] as const)
          : ([] as const);

  if (bones.length === 0) return {};

  const state = useStudio.getState();
  const canonical = sampleLandmarks(skeleton, state.document.clip, request.time, [...bones]);
  const character = useCharacter.getState().active;
  if (!character) return canonical;

  // The capture is taken after CharacterFigure has applied the requested pose.
  // Prefer the visible character's own bones so close-up framing follows its
  // proportions rather than the canonical mannequin.
  character.object.updateMatrixWorld(true);
  const result = { ...canonical };
  const point = new Vector3();

  for (const bone of bones) {
    const visible = character.boneByName.get(bone);
    if (!visible) continue;
    visible.getWorldPosition(point);
    result[bone] = { x: point.x, y: point.y, z: point.z };
  }

  // Preserved imports may expose a calibrated hand frame that is more accurate
  // for held equipment than the imported wrist bone itself.
  if (request.camera.target === 'hands' && character.handMatrix) {
    const matrix = new Matrix4();
    for (const side of ['l', 'r'] as const) {
      const hand = character.handMatrix(side, matrix);
      if (!hand) continue;
      point.setFromMatrixPosition(hand);
      result[`hand_${side}`] = { x: point.x, y: point.y, z: point.z };
    }
  }

  return result;
}

function reviewView(request: ReviewCaptureRequest): ReferenceReviewView {
  return {
    id: request.viewId,
    label: request.viewId,
    preset: request.camera.preset,
    target: request.camera.target,
  };
}

async function canvasPng(
  pixels: Uint8Array,
  width: number,
  height: number,
): Promise<Blob> {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('2D canvas context is unavailable for review capture.');

  const flipped = new Uint8ClampedArray(pixels.length);
  const rowBytes = width * 4;
  for (let y = 0; y < height; y += 1) {
    const source = (height - 1 - y) * rowBytes;
    const destination = y * rowBytes;
    flipped.set(pixels.subarray(source, source + rowBytes), destination);
  }
  context.putImageData(new ImageData(flipped, width, height), 0, 0);

  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error('Could not encode review capture as PNG.'));
    }, 'image/png');
  });
}

/**
 * Browser-side bridge between the pure reference capture controller and the
 * existing R3F viewport.
 *
 * It mounts no visible UI. When no capture is requested it is inert.
 */
export function ReviewCaptureBridge() {
  const { gl, scene, camera } = useThree();

  useEffect(() => {
    if (!(camera instanceof PerspectiveCamera)) {
      return installBrowserReviewCaptureAdapter({
        snapshot: () => ({}),
        apply: () => {
          throw new Error('Review capture requires the Studio perspective camera.');
        },
        settle: () => undefined,
        capturePng: () => {
          throw new Error('Review capture requires the Studio perspective camera.');
        },
        restore: () => undefined,
      });
    }

    const adapter: ReviewCaptureAdapter<unknown> = {
      snapshot() {
        const studio = useStudio.getState();
        const character = useCharacter.getState();
        const snapshot: ViewportSnapshot = {
          studio: {
            time: studio.time,
            playing: studio.playing,
            camera: studio.camera,
            viewMode: studio.viewMode,
            showEquipment: studio.showEquipment,
            showIkHandles: studio.showIkHandles,
            showGrid: studio.showGrid,
            backdrop: studio.backdrop,
            selection: {
              ...studio.selection,
              handle: studio.selection.handle ? { ...studio.selection.handle } : null,
            },
          },
          character: {
            correctivesPreview: character.correctivesPreview,
          },
          camera: {
            position: camera.position.clone(),
            quaternion: camera.quaternion.clone(),
            fov: camera.fov,
            aspect: camera.aspect,
            near: camera.near,
            far: camera.far,
          },
        };
        return snapshot;
      },

      apply(request) {
        const studio = useStudio.getState();
        if (studio.document.exercise.id !== request.exerciseId) {
          throw new Error(
            `Review capture requested "${request.exerciseId}" but the viewport currently shows "${studio.document.exercise.id}".`,
          );
        }

        useStudio.setState({
          time: Math.max(0, Math.min(studio.document.clip.duration, request.time)),
          playing: false,
          camera: 'free',
          viewMode: 'character',
          showEquipment: true,
          showIkHandles: false,
          showGrid: false,
          backdrop: 'light',
          selection: { bone: null, handle: null, equipmentId: null, socketId: null },
        });
        useCharacter.setState({ correctivesPreview: true });
      },

      async settle() {
        await waitForVisibleCharacter();
        // One frame applies the new store state; a second lets FrameDriver,
        // CharacterFigure and EquipmentView consume the resolved frame.
        await nextFrame();
        await nextFrame();
      },

      async capturePng(request) {
        const studio = useStudio.getState();
        const view = reviewView(request);
        const landmarks = reviewLandmarks(request);
        const setup = resolveReviewCamera(view, studio.document.exercise.camera, landmarks);

        const width = Math.max(1, Math.round(request.viewport.width * request.viewport.dpr));
        const height = Math.max(1, Math.round(request.viewport.height * request.viewport.dpr));
        const previousTarget = gl.getRenderTarget();
        const previousPosition = camera.position.clone();
        const previousQuaternion = camera.quaternion.clone();
        const previousFov = camera.fov;
        const previousAspect = camera.aspect;
        const previousNear = camera.near;
        const previousFar = camera.far;
        const previousOverrideMaterial = scene.overrideMaterial;
        const previousBackground = scene.background;
        const previousClearColor = gl.getClearColor(new Color()).clone();
        const previousClearAlpha = gl.getClearAlpha();
        let silhouetteMaterial: MeshBasicMaterial | null = null;

        const target = new WebGLRenderTarget(width, height, {
          depthBuffer: true,
          stencilBuffer: false,
        });
        target.texture.colorSpace = gl.outputColorSpace;

        try {
          camera.position.set(setup.position.x, setup.position.y, setup.position.z);
          camera.near = 0.05;
          camera.far = 100;
          camera.fov = setup.fov;
          camera.aspect = request.viewport.width / request.viewport.height;
          camera.lookAt(setup.target.x, setup.target.y, setup.target.z);
          camera.updateProjectionMatrix();
          camera.updateMatrixWorld(true);

          if (request.renderMode === 'silhouette') {
            silhouetteMaterial = new MeshBasicMaterial({ color: 0xffffff });
            scene.overrideMaterial = silhouetteMaterial;
            scene.background = new Color(0x000000);
            gl.setClearColor(0x000000, 1);
          }

          gl.setRenderTarget(target);
          gl.clear(true, true, true);
          gl.render(scene, camera);

          const pixels = new Uint8Array(width * height * 4);
          gl.readRenderTargetPixels(target, 0, 0, width, height, pixels);
          const blob = await canvasPng(pixels, width, height);

          if (request.renderMode === 'silhouette') {
            const metrics = analyseSilhouetteRgba(pixels, width, height);
            return {
              bytes: blob,
              width,
              height,
              silhouette: { metrics, sanity: silhouetteSanity(metrics) },
            };
          }

          return { bytes: blob, width, height };
        } finally {
          gl.setRenderTarget(previousTarget);
          scene.overrideMaterial = previousOverrideMaterial;
          scene.background = previousBackground;
          gl.setClearColor(previousClearColor, previousClearAlpha);
          silhouetteMaterial?.dispose();
          target.dispose();
          camera.position.copy(previousPosition);
          camera.quaternion.copy(previousQuaternion);
          camera.fov = previousFov;
          camera.aspect = previousAspect;
          camera.near = previousNear;
          camera.far = previousFar;
          camera.updateProjectionMatrix();
          camera.updateMatrixWorld(true);
        }
      },

      restore(value) {
        const snapshot = value as ViewportSnapshot;
        useStudio.setState({
          time: snapshot.studio.time,
          playing: snapshot.studio.playing,
          camera: snapshot.studio.camera,
          viewMode: snapshot.studio.viewMode,
          showEquipment: snapshot.studio.showEquipment,
          showIkHandles: snapshot.studio.showIkHandles,
          showGrid: snapshot.studio.showGrid,
          backdrop: snapshot.studio.backdrop,
          selection: snapshot.studio.selection,
        });
        useCharacter.setState({
          correctivesPreview: snapshot.character.correctivesPreview,
        });

        camera.position.copy(snapshot.camera.position);
        camera.quaternion.copy(snapshot.camera.quaternion);
        camera.fov = snapshot.camera.fov;
        camera.aspect = snapshot.camera.aspect;
        camera.near = snapshot.camera.near;
        camera.far = snapshot.camera.far;
        camera.updateProjectionMatrix();
        camera.updateMatrixWorld(true);
      },
    };

    return installBrowserReviewCaptureAdapter(adapter);
  }, [camera, gl, scene]);

  return null;
}
