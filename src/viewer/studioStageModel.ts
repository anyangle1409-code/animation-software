import type { BackdropStyle } from '../editor/storeCore';
import { buildHgReferenceGridBuffers, type HgGridBuffers } from './referenceGrid';

export interface HgStageDirectionalLight {
  colour: string;
  intensity: number;
  position: readonly [number, number, number];
  castShadow: boolean;
  shadowMapSize: readonly [number, number];
  shadowBounds: {
    left: number;
    right: number;
    top: number;
    bottom: number;
  };
}

export interface HgStageModel {
  background: string;
  hemisphere: {
    sky: string;
    ground: string;
    intensity: number;
  };
  key: HgStageDirectionalLight;
  rim: {
    colour: string;
    intensity: number;
    position: readonly [number, number, number];
  };
  floor: {
    colour: string;
    size: readonly [number, number];
    rotationX: number;
    roughness: number;
    receiveShadow: boolean;
  } | null;
  grid: {
    buffers: HgGridBuffers;
    cellColour: string;
    sectionColour: string;
    cellOpacity: number;
    sectionOpacity: number;
  } | null;
}

/**
 * Renderer-neutral description of the static Studio stage.
 *
 * This is the authoritative stage configuration. Renderer adapters only
 * materialise this data; they do not decide lighting, floor or grid behaviour.
 */
export function buildHgStageModel(
  backdrop: BackdropStyle,
  showGrid: boolean,
): HgStageModel {
  const floorless = backdrop.floorless === true;
  return {
    background: backdrop.background,
    hemisphere: {
      sky: '#f0f4fb',
      ground: backdrop.ground,
      intensity: backdrop.lighting.ambient,
    },
    key: {
      colour: '#ffffff',
      intensity: backdrop.lighting.key,
      position: [3, 5, 4],
      castShadow: !floorless,
      shadowMapSize: [1024, 1024],
      shadowBounds: {
        left: -3,
        right: 3,
        top: 3,
        bottom: -3,
      },
    },
    rim: {
      colour: backdrop.lighting.rimColour,
      intensity: backdrop.lighting.rim,
      position: [-3, 2.5, -2],
    },
    floor: floorless
      ? null
      : {
          colour: backdrop.ground,
          size: [24, 24],
          rotationX: -Math.PI / 2,
          roughness: 0.95,
          receiveShadow: true,
        },
    grid: !floorless && showGrid
      ? {
          buffers: buildHgReferenceGridBuffers(),
          cellColour: backdrop.cell,
          sectionColour: backdrop.section,
          cellOpacity: 0.55,
          sectionOpacity: 0.9,
        }
      : null,
  };
}
