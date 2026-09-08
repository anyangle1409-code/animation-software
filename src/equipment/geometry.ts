import type { EquipmentKind } from './types';

/**
 * Equipment shapes as data.
 *
 * The viewport and the GLB exporter both build from this one list, so what you
 * see in the studio is exactly what lands in the exported file — there is no
 * second, drifting copy of each item's geometry.
 *
 * Parts are authored in the same frame as the sockets: the grip axis runs along
 * local +Z.
 */
export type Part =
  | {
      shape: 'cylinder';
      /** Radius at the top and bottom, and the length along the part's own Y. */
      radius: number;
      radiusTop?: number;
      length: number;
      segments?: number;
      position?: [number, number, number];
      rotation?: [number, number, number];
      material: MaterialId;
    }
  | {
      shape: 'box';
      size: [number, number, number];
      position?: [number, number, number];
      rotation?: [number, number, number];
      material: MaterialId;
    }
  | {
      shape: 'sphere';
      radius: number;
      position?: [number, number, number];
      material: MaterialId;
    }
  | {
      shape: 'torus';
      radius: number;
      tube: number;
      arc?: number;
      position?: [number, number, number];
      rotation?: [number, number, number];
      material: MaterialId;
    };

export type MaterialId = 'metal' | 'dark' | 'rubber' | 'pad' | 'frame' | 'rope' | 'band';

export interface SurfaceSpec {
  color: string;
  roughness: number;
  metalness: number;
}

export const MATERIALS: Record<MaterialId, SurfaceSpec> = {
  metal: { color: '#8d949c', roughness: 0.35, metalness: 0.85 },
  dark: { color: '#2b2f36', roughness: 0.6, metalness: 0.3 },
  rubber: { color: '#1d2025', roughness: 0.9, metalness: 0.05 },
  pad: { color: '#23262d', roughness: 0.85, metalness: 0.02 },
  frame: { color: '#3c4551', roughness: 0.5, metalness: 0.6 },
  rope: { color: '#4a4038', roughness: 0.95, metalness: 0.02 },
  band: { color: '#7a3b8f', roughness: 0.9, metalness: 0.02 },
};

const HALF_TURN = Math.PI / 2;

/** A cylinder lying along local Z, which is how every grip is authored. */
const bar = (
  radius: number,
  length: number,
  position: [number, number, number] = [0, 0, 0],
  material: MaterialId = 'metal',
  segments = 16,
): Part => ({ shape: 'cylinder', radius, length, position, rotation: [HALF_TURN, 0, 0], segments, material });

const disc = (
  radius: number,
  thickness: number,
  position: [number, number, number],
  material: MaterialId = 'rubber',
  segments = 28,
): Part => ({
  shape: 'cylinder',
  radius,
  length: thickness,
  position,
  rotation: [HALF_TURN, 0, 0],
  segments,
  material,
});

const box = (
  size: [number, number, number],
  position: [number, number, number],
  material: MaterialId = 'frame',
  rotation?: [number, number, number],
): Part => ({ shape: 'box', size, position, material, ...(rotation ? { rotation } : {}) });

export const EQUIPMENT_PARTS: Record<EquipmentKind, Part[]> = {
  dumbbell: [
    bar(0.015, 0.12),
    disc(0.048, 0.035, [0, 0, -0.075], 'rubber', 32),
    disc(0.048, 0.035, [0, 0, 0.075], 'rubber', 32),
  ],

  barbell: [
    bar(0.0145, 1.32),
    ...[-1, 1].flatMap((side) => [
      bar(0.025, 0.42, [0, 0, side * 0.87]),
      disc(0.225, 0.032, [0, 0, side * 0.72]),
      disc(0.225, 0.032, [0, 0, side * 0.765]),
    ]),
  ],

  ez_curl_bar: [
    bar(0.014, 0.16),
    ...[-1, 1].flatMap((side): Part[] => [
      {
        shape: 'cylinder',
        radius: 0.014,
        length: 0.17,
        position: [0, 0.022, side * 0.15],
        rotation: [HALF_TURN, 0, side * 0.42],
        segments: 12,
        material: 'metal',
      },
      {
        shape: 'cylinder',
        radius: 0.014,
        length: 0.14,
        position: [0, 0.006, side * 0.3],
        rotation: [HALF_TURN, 0, -side * 0.42],
        segments: 12,
        material: 'metal',
      },
      bar(0.024, 0.22, [0, 0, side * 0.45]),
      disc(0.16, 0.03, [0, 0, side * 0.42], 'rubber', 24),
    ]),
  ],

  weight_plate: [disc(0.225, 0.034, [0, 0, 0], 'rubber', 32), bar(0.028, 0.05, [0, 0, 0])],

  flat_bench: [
    box([0.32, 0.09, 1.25], [0, 0.415, 0], 'pad'),
    box([0.08, 0.4, 0.08], [0, 0.2, 0.52]),
    box([0.08, 0.4, 0.08], [0, 0.2, -0.52]),
    box([0.5, 0.05, 0.06], [0, 0.03, 0.52]),
    box([0.5, 0.05, 0.06], [0, 0.03, -0.52]),
  ],

  incline_bench: [
    box([0.32, 0.09, 0.8], [0, 0.62, 0.22], 'pad', [-Math.PI / 4, 0, 0]),
    box([0.32, 0.09, 0.42], [0, 0.44, -0.42], 'pad'),
    box([0.08, 0.42, 0.08], [0, 0.21, -0.58]),
    box([0.08, 0.44, 0.08], [0, 0.22, 0.4]),
    box([0.5, 0.05, 0.06], [0, 0.03, -0.58]),
    box([0.5, 0.05, 0.06], [0, 0.03, 0.4]),
  ],

  squat_rack: [
    ...[-0.62, 0.62].flatMap((x) =>
      [-0.5, 0.5].map((z) => box([0.07, 2.1, 0.07], [x, 1.05, z])),
    ),
    ...[-0.62, 0.62].map((x) => box([0.08, 0.06, 1.1], [x, 0.03, 0])),
    ...[-0.62, 0.62].map((x) => box([0.1, 0.12, 0.16], [x, 1.42, 0.5], 'dark')),
    box([1.3, 0.06, 0.06], [0, 0.85, 0.5], 'dark'),
    box([1.3, 0.06, 0.06], [0, 2.05, 0]),
  ],

  cable_handle: [
    bar(0.014, 0.12, [0, 0, 0], 'dark'),
    {
      shape: 'torus',
      radius: 0.045,
      tube: 0.008,
      arc: Math.PI,
      position: [0, 0.06, 0],
      rotation: [0, HALF_TURN, 0],
      material: 'metal',
    },
    { shape: 'sphere', radius: 0.014, position: [0, 0.11, 0], material: 'metal' },
  ],

  cable_rope: [
    ...[-1, 1].flatMap((side): Part[] => [
      {
        shape: 'cylinder',
        radius: 0.016,
        length: 0.34,
        position: [0, 0.14, side * 0.12],
        rotation: [side > 0 ? -0.25 : 0.25, 0, 0],
        segments: 10,
        material: 'rope',
      },
      { shape: 'sphere', radius: 0.024, position: [0, -0.02, side * 0.08], material: 'rubber' },
    ]),
    { shape: 'sphere', radius: 0.018, position: [0, 0.3, 0], material: 'metal' },
  ],

  lat_pulldown_bar: [
    bar(0.017, 0.86),
    ...[-1, 1].map((side): Part => ({
      shape: 'cylinder',
      radius: 0.017,
      length: 0.24,
      position: [0, -0.06, side * 0.52],
      rotation: [HALF_TURN, 0, side * 0.55],
      segments: 12,
      material: 'metal',
    })),
    box([0.03, 0.09, 0.03], [0, 0.05, 0], 'dark'),
  ],

  resistance_band: [
    bar(0.011, 0.9, [0, 0, 0], 'band'),
    disc(0.019, 0.1, [0, 0, -0.45], 'rubber', 12),
    disc(0.019, 0.1, [0, 0, 0.45], 'rubber', 12),
  ],

  kettlebell: [
    { shape: 'sphere', radius: 0.095, position: [0, -0.13, 0], material: 'rubber' },
    {
      shape: 'torus',
      radius: 0.062,
      tube: 0.016,
      arc: Math.PI * 1.1,
      position: [0, -0.05, 0],
      rotation: [0, HALF_TURN, 0],
      material: 'dark',
    },
  ],
};
