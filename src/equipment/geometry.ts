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

/**
 * Where the incline bench's backrest hinges: the seat's top (0.395 + half its
 * 0.09 thickness) at its back edge (-0.35 + half its 0.28 depth) — the point
 * the backrest's face meets the seat, whatever angle it is set to.
 */
const INCLINE_HINGE = { y: 0.44, z: -0.21 };

/** Half the back pad's thickness and length, metres — its own local frame. */
const INCLINE_PAD = { halfThickness: 0.045, halfLength: 0.4 };

/**
 * The back pad, rotated about the hinge above so its face stays flush with a
 * body reclined at the same `backAngle` (see `curl.ts`'s `inclineGeometry`,
 * which pitches the body by the same amount). At 45° this is exactly today's
 * hand-placed box — `[0, 0.691, 0.105]` rotated `-Math.PI / 4` — kept as a
 * literal because floating-point trig does not reliably round-trip to those
 * exact numbers; every other angle is this one hinge, solved generically.
 */
function inclineBackPad(backAngle: number): Part {
  if (backAngle === 45) return box([0.32, 0.09, 0.8], [0, 0.691, 0.105], 'pad', [-Math.PI / 4, 0, 0]);
  const phi = (-backAngle * Math.PI) / 180;
  const cos = Math.cos(phi);
  const sin = Math.sin(phi);
  const { halfThickness: t, halfLength: L } = INCLINE_PAD;
  // The pad's top-near corner, (y = t, z = -L) before rotation, is the point
  // that sits at the hinge for any angle; solving that fixes the box's centre.
  const yLocal = t * cos + L * sin;
  const zLocal = t * sin - L * cos;
  return box(
    [0.32, 0.09, 0.8],
    [0, INCLINE_HINGE.y - yLocal, INCLINE_HINGE.z - zLocal],
    'pad',
    [phi, 0, 0],
  );
}

/** The incline bench's parts at a given back angle; every other part is fixed. */
function inclineBenchParts(backAngle: number): Part[] {
  return [
    inclineBackPad(backAngle),
    box([0.32, 0.09, 0.28], [0, 0.395, -0.35], 'pad'),
    box([0.08, 0.36, 0.08], [0, 0.18, -0.45]),
    box([0.08, 0.96, 0.08], [0, 0.48, 0.4]),
    box([0.5, 0.05, 0.06], [0, 0.03, -0.45]),
    box([0.5, 0.05, 0.06], [0, 0.03, 0.4]),
  ];
}

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

  // Shaped the way a real adjustable bench is, which the first exercise to lie
  // on it (the incline curl) found it was not. The backrest hinges where its
  // face meets the seat's top at the seat's back edge; it used to sit 15 cm
  // lower, its lower end under the seat, where no seated back could reach it.
  // The seat is 44 cm high and 28 cm deep rather than 48.5 and 42: a seated
  // thigh slopes down from the hip to the knee, and the higher, longer seat's
  // front edge sank 40 mm into it. The rear post now reaches up to hold the
  // backrest.
  //
  // The back angle is a per-instance parameter (`EquipmentInstance.backAngle`,
  // default 45°); `inclineBenchParts` below derives every angle's pad from the
  // same hinge, and this entry is exactly its 45° output — see `equipmentParts`.
  incline_bench: inclineBenchParts(45),

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

  // A single-column cable station, authored facing −Z: whoever uses it stands
  // on its −Z side. The high pulley hangs off an arm reaching 36 cm out over
  // them, so a cable from it drops in front of the body rather than down the
  // column; the weight stack sits between the uprights, out of reach. A mid
  // pulley at chest height faces the user straight on.
  cable_tower: [
    box([0.7, 0.04, 0.6], [0, 0.02, 0.1]),
    box([0.06, 2.2, 0.06], [-0.28, 1.12, 0.2]),
    box([0.06, 2.2, 0.06], [0.28, 1.12, 0.2]),
    box([0.62, 0.08, 0.08], [0, 2.22, 0.2]),
    box([0.3, 0.8, 0.12], [0, 0.46, 0.2], 'dark'),
    box([0.06, 0.06, 0.36], [0, 2.18, 0.02]),
    {
      shape: 'torus',
      radius: 0.045,
      tube: 0.012,
      position: [0, 2.12, -0.14],
      rotation: [0, HALF_TURN, 0],
      material: 'metal',
    },
    // A second pulley at chest height on a crossbar between the uprights, for
    // cables that pull sideways or straight out rather than down.
    box([0.56, 0.06, 0.06], [0, 1.25, 0.2]),
    box([0.06, 0.06, 0.16], [0, 1.25, 0.11], 'dark'),
    {
      shape: 'torus',
      radius: 0.035,
      tube: 0.01,
      position: [0, 1.25, 0.02],
      rotation: [0, HALF_TURN, 0],
      material: 'metal',
    },
  ],

  // A 50 cm straight bar with sleeves where the hands go, clipped to the cable
  // at its middle.
  cable_bar: [
    bar(0.014, 0.5),
    bar(0.017, 0.12, [0, 0, -0.2], 'rubber'),
    bar(0.017, 0.12, [0, 0, 0.2], 'rubber'),
    box([0.03, 0.05, 0.03], [0, 0.035, 0], 'dark'),
    { shape: 'sphere', radius: 0.014, position: [0, 0.065, 0], material: 'metal' },
  ],

  // One metre of cable along local +Y from the origin. It is stretched to
  // length along Y alone, so its thickness never changes; see
  // `EquipmentTransform.scale`.
  cable: [
    { shape: 'cylinder', radius: 0.0035, length: 1, position: [0, 0.5, 0], segments: 8, material: 'dark' },
  ],
};

/**
 * A kind's parts, at an instance's own back angle where one applies.
 *
 * This is the one place any consumer — the viewport, the GLB export, the
 * collision envelope, the body-clearance measurement — asks for equipment
 * geometry when a `backAngle` might be in play, so none of them can hold a
 * copy that drifts from what the others draw or measure. Every kind but the
 * incline bench ignores the angle and returns its fixed `EQUIPMENT_PARTS`.
 */
export function equipmentParts(kind: EquipmentKind, backAngle?: number): Part[] {
  if (kind === 'incline_bench') return inclineBenchParts(backAngle ?? 45);
  return EQUIPMENT_PARTS[kind];
}
