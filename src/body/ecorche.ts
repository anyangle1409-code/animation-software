import { BufferAttribute, Color, Matrix4, MeshStandardMaterial, Vector3 } from 'three';
import type { BufferGeometry, SkinnedMesh } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import { vec3 } from '../rig/types';
import type { Side } from '../rig/boneNames';
import { MUSCLE_GROUP_IDS } from '../muscles/groups';
import type { MuscleGroupId } from '../muscles/groups';
import {
  MUSCLES,
  createMuscleTransform,
  mirrorMuscle,
  muscleInstance,
  resolveMuscle,
} from '../muscles/model';
import type { MuscleDefinition, MuscleInstance } from '../muscles/model';
import { activationMap, activationOf } from '../muscles/activation';
import type { ActivationLevel } from '../muscles/activation';
import type { MuscleInvolvement } from '../exercises/types';
import { buildBodyGeometry } from './mesh';
import { refineRegion } from './refine';
import { boneInfluence, smoothstep } from './skinning';
import { blendElbowWeights } from './elbow';

export { boneInfluence };
import { ANATOMICAL_PALETTE } from './anatomical';

/**
 * The anatomy view: the same skinned body, read as an écorché.
 *
 * Nothing here adds geometry. The body already carries real anatomical relief,
 * and `muscles/model.ts` already knows where each belly sits under the skin in
 * any pose. This turns that knowledge into a *continuous field* on the surface
 * itself — one scalar per vertex per muscle, smooth everywhere — and then uses
 * the one field for both jobs:
 *
 *   - the bind-pose surface is displaced by it, so a muscle has form; and
 *   - the activation colour is thresholded on it, so the coloured border is a
 *     contour of the same shape rather than a staircase along triangle edges.
 *
 * That single origin is the point. A categorical map can only put its border on
 * an edge of the mesh; a field crosses its threshold in the middle of a
 * triangle, where the muscle actually ends.
 */

/** No muscle claims this vertex. Real groups are their index in MUSCLE_GROUP_IDS. */
export const ECORCHE_UNMAPPED = 255;

/**
 * The hardest the surface may ever be pushed, metres. An absolute ceiling, not
 * a working value: every field is authored well under it and the union is
 * bounded below it, so this is the number a test can hold the whole system to.
 */
export const ECORCHE_SAFE_MAX = 0.024;

/**
 * The furthest any bind-pose vertex may end up from where the character has it,
 * metres. Larger than the relief ceiling because the anatomy build also settles
 * the arm surface before sculpting it, and the two add.
 */
export const ECORCHE_SAFE_MOVE = 0.032;

/**
 * How strongly each activation level lights the surface, 0..1.
 *
 * The curl lists the forearm flexors and the front delt as secondary, and the
 * shader would take any value here — but this round is about whether the
 * *geometry* carries the arm, and a shoulder and forearm tinted orange would
 * answer a different question. So secondaries stay dark and only the working
 * muscle is coloured.
 */
export const ECORCHE_ACTIVATION: Record<ActivationLevel, number> = {
  primary: 1,
  secondary: 0,
  stabiliser: 0,
  inactive: 0,
};

/** The working muscle, in the reference's orange-red. */
export const ECORCHE_ACTIVE_COLOUR = '#ff4f1f';

/**
 * Anatomy mode renders in grey alone for now.
 *
 * Colour was answering a different question than the one being asked. What has
 * to be judged here is whether the arm is anatomically right and whether it
 * deforms correctly through the lift, and an orange muscle both hides the form
 * underneath it and draws the eye away from everything else. The activation
 * path below is left working and wired up — the field it reads is still built
 * every frame — but this flag holds its output at zero, so the surface is read
 * by its shading alone.
 */
export const ECORCHE_GREYSCALE = true;

/**
 * Where the colour stops, as a value of the activated field. The relief runs
 * all the way out to zero, so the colour is strictly inside the form: the
 * muscle keeps swelling for a few millimetres past its own border and melts
 * into the arm, instead of ending in a crease exactly where the orange ends.
 */
export const ECORCHE_COLOUR_THRESHOLD = 0.42;

/**
 * The écorché palette. Muscle is a warm light grey so that shading, not hue,
 * carries the form.
 *
 * The eyes are restated in grey rather than kept from the character. At the
 * character's own values the pupil is nearly black and the socket around it
 * reads as a hole punched in the head — the first thing the eye goes to in
 * every anatomy render, which is not what this view is for. Greyed and lifted,
 * they still read as eyes and stop competing with the arm. The face geometry is
 * untouched, and the character's own palette is untouched with it.
 */
export const ECORCHE_PALETTE = {
  muscle: '#a9a49b',
  shorts: '#15161a',
  sclera: '#9d9891',
  iris: '#7c7871',
  pupil: '#55524e',
} as const;

/**
 * The vertex colours are stored as pre-linearised bytes, the convention
 * `scripts/generate-anatomical-body.mjs` writes them in. Matching a colour
 * therefore means comparing against the same conversion rather than against the
 * sRGB hex.
 */
function linearBytes(hex: string): [number, number, number] {
  const value = Number.parseInt(hex.slice(1), 16);
  return [16, 8, 0].map((shift) => {
    const channel = ((value >> shift) & 255) / 255;
    const linear = channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    return Math.round(linear * 255);
  }) as [number, number, number];
}

/** Which part of the character a vertex colour belongs to. */
const PALETTE_PARTS = ['skin', 'shorts', 'sclera', 'iris', 'pupil'] as const;
type PalettePart = (typeof PALETTE_PARTS)[number];

const SOURCE_BYTES: Record<PalettePart, [number, number, number]> = {
  skin: linearBytes(ANATOMICAL_PALETTE.skin),
  shorts: linearBytes(ANATOMICAL_PALETTE.shorts),
  sclera: linearBytes(ANATOMICAL_PALETTE.sclera),
  iris: linearBytes(ANATOMICAL_PALETTE.iris),
  pupil: linearBytes(ANATOMICAL_PALETTE.pupil),
};

const ECORCHE_BYTES: Record<PalettePart, [number, number, number]> = {
  skin: linearBytes(ECORCHE_PALETTE.muscle),
  shorts: linearBytes(ECORCHE_PALETTE.shorts),
  sclera: linearBytes(ECORCHE_PALETTE.sclera),
  iris: linearBytes(ECORCHE_PALETTE.iris),
  pupil: linearBytes(ECORCHE_PALETTE.pupil),
};

/**
 * Restate the body's colours in the écorché palette. Flesh becomes muscle grey;
 * clothing, sclera, iris and pupil keep their role. A colour that matches
 * nothing is left as it is rather than guessed at.
 */
export function ecorcheColours(geometry: BufferGeometry): Uint8Array {
  const colour = geometry.getAttribute('color');
  const out = new Uint8Array(colour.count * 3);
  for (let index = 0; index < colour.count; index += 1) {
    const r = Math.round(colour.getX(index) * 255);
    const g = Math.round(colour.getY(index) * 255);
    const b = Math.round(colour.getZ(index) * 255);
    let replacement: [number, number, number] = [r, g, b];
    for (const part of PALETTE_PARTS) {
      const [sr, sg, sb] = SOURCE_BYTES[part];
      if (Math.abs(r - sr) <= 1 && Math.abs(g - sg) <= 1 && Math.abs(b - sb) <= 1) {
        replacement = ECORCHE_BYTES[part];
        break;
      }
    }
    out.set(replacement, index * 3);
  }
  return out;
}

const at = (bone: string, x: number, y: number, z: number) =>
  ({ bone, offset: vec3(x, y, z) }) as MuscleDefinition['origin'];

/**
 * Two bellies the studio's muscle model does not carry.
 *
 * The model is deliberately pitched at the level a trainer talks about, so it
 * has a biceps and a triceps and no brachialis. An arm sculpted from that alone
 * has a hole in it: the brachialis is most of the distal upper arm's width, and
 * the brachioradialis is the whole shape of the proximal forearm. They exist
 * here as *shape only* — no group id, no activation row, never a belly in the
 * muscle overlay — because adding them to `MUSCLE_GROUP_IDS` would change the
 * exercise data, the activation readout and the overlay for every view.
 *
 * `group` below is set to the neighbour they lie against purely because the
 * shared definition type requires one; the field's own `group: null` is what
 * decides that they are never coloured.
 */
const BRACHIALIS: MuscleDefinition = {
  group: 'biceps',
  origin: at('upperarm_l', 0.009, 0.148, 0.011),
  insertion: at('forearm_l', 0.005, 0.03, 0.012),
  thickness: 0.026,
  bulge: 0.25,
  taper: 0.82,
};

const BRACHIORADIALIS: MuscleDefinition = {
  group: 'forearm_flexors',
  origin: at('upperarm_l', 0.017, 0.245, 0.007),
  insertion: at('forearm_l', 0.011, 0.15, 0.013),
  thickness: 0.022,
  bulge: 0.2,
  taper: 0.85,
};

/**
 * How a belly is read as a field on the skin.
 *
 * Everything is a multiple of the belly's own half-length, so a field scales
 * with the muscle it comes from rather than with a hard-coded distance.
 */
interface FieldSpec {
  id: string;
  /** The group whose activation colours this field, or null for shape only. */
  group: MuscleGroupId | null;
  /** Present for the bellies the muscle model does not carry. */
  definition?: MuscleDefinition;
  /** Metres at the crown. */
  amplitude: number;
  /** Reach along and around the belly, as multiples of its half-length. */
  along: number;
  radius: number;
  /** Half-angle of the arc it claims, degrees, at its middle and at its ends. */
  arcMiddle: number;
  arcEnd: number;
  /**
   * Axial falloff exponents. +Y runs origin to insertion, so `distal` is the
   * end the muscle inserts on: a biceps rises gently out from under the deltoid
   * and draws in hard to its tendon, which is `proximal` low and `distal` high.
   */
  proximal: number;
  distal: number;
  /**
   * Skin-weight gate. Bone stems, suffixed with the side, and the band over
   * which influence from them fades the field in. A band rather than a
   * threshold: a hard cut draws a step along the edge of a weight island, and
   * that step is exactly the staircase this round is here to remove.
   */
  gate: { bones: readonly string[]; low: number; high: number };
}

/**
 * The arm cluster. Amplitudes are the working numbers, all far below
 * `ECORCHE_SAFE_MAX`: the biceps is the only one meant to read as a distinct
 * muscle, and everything else is there so that it sits in an arm instead of on
 * a tube.
 *
 * The deltoid gates on the humerus alone. Its own belly runs from the clavicle,
 * and gating on clavicle weight would let the field walk out across the chest
 * and the trapezius — a shoulder cap that keeps going is not a shoulder cap.
 */
const ARM_FIELDS: readonly FieldSpec[] = [
  {
    id: 'biceps',
    group: 'biceps',
    amplitude: 0.017,
    along: 1.12,
    radius: 0.62,
    arcMiddle: 71,
    arcEnd: 30,
    // Both ends draw in, the distal harder. Left gentler than this the belly
    // creeps up into the armpit and the muscle reads as a flame hanging off the
    // shoulder rather than as a spindle on the humerus.
    proximal: 1.5,
    distal: 1.95,
    gate: { bones: ['upperarm', 'forearm'], low: 0.1, high: 0.3 },
  },
  {
    id: 'brachialis',
    group: null,
    definition: BRACHIALIS,
    amplitude: 0.009,
    along: 1.24,
    radius: 0.9,
    arcMiddle: 80,
    arcEnd: 38,
    proximal: 1.6,
    distal: 1.35,
    gate: { bones: ['upperarm'], low: 0.1, high: 0.3 },
  },
  {
    id: 'triceps',
    group: 'triceps',
    amplitude: 0.0138,
    along: 1.24,
    radius: 0.62,
    arcMiddle: 76,
    arcEnd: 34,
    proximal: 1.1,
    distal: 1.85,
    gate: { bones: ['upperarm'], low: 0.1, high: 0.3 },
  },
  {
    id: 'deltoid_anterior',
    group: 'deltoid_anterior',
    amplitude: 0.012,
    along: 1.42,
    radius: 1.15,
    arcMiddle: 60,
    arcEnd: 28,
    proximal: 1.7,
    distal: 1.5,
    gate: { bones: ['upperarm'], low: 0.12, high: 0.34 },
  },
  {
    id: 'deltoid_medial',
    group: 'deltoid_medial',
    amplitude: 0.0152,
    along: 1.42,
    radius: 1.15,
    arcMiddle: 72,
    arcEnd: 32,
    proximal: 1.6,
    distal: 1.4,
    gate: { bones: ['upperarm'], low: 0.12, high: 0.34 },
  },
  {
    id: 'deltoid_posterior',
    group: 'deltoid_posterior',
    amplitude: 0.012,
    along: 1.42,
    radius: 1.15,
    arcMiddle: 60,
    arcEnd: 28,
    proximal: 1.7,
    distal: 1.5,
    gate: { bones: ['upperarm'], low: 0.12, high: 0.34 },
  },
  {
    id: 'brachioradialis',
    group: null,
    definition: BRACHIORADIALIS,
    amplitude: 0.0095,
    along: 1.05,
    radius: 0.8,
    arcMiddle: 62,
    arcEnd: 28,
    proximal: 1.2,
    distal: 2.2,
    gate: { bones: ['upperarm', 'forearm'], low: 0.12, high: 0.32 },
  },
  {
    id: 'forearm_flexors',
    group: 'forearm_flexors',
    amplitude: 0.008,
    along: 1.1,
    radius: 0.95,
    arcMiddle: 70,
    arcEnd: 30,
    proximal: 0.9,
    distal: 2.6,
    // Forearm weight only, and a high band: the wrist blends into the hand, and
    // the hands are not this round's to touch.
    gate: { bones: ['forearm'], low: 0.3, high: 0.55 },
  },
  {
    id: 'forearm_extensors',
    group: 'forearm_extensors',
    amplitude: 0.007,
    along: 1.1,
    radius: 0.95,
    arcMiddle: 66,
    arcEnd: 28,
    proximal: 0.95,
    distal: 2.6,
    gate: { bones: ['forearm'], low: 0.3, high: 0.55 },
  },
];

/** The groups the surface can classify and colour. Shape-only fields are not here. */
export const ECORCHE_GROUPS: readonly MuscleGroupId[] = [
  ...new Set(ARM_FIELDS.map((field) => field.group).filter((group): group is MuscleGroupId => group !== null)),
];

const SIDES: readonly Side[] = ['l', 'r'];

/** A field spec bound to one side, with the belly it reads. */
interface BoundField {
  spec: FieldSpec;
  muscle: MuscleInstance;
  gate: ReadonlySet<string>;
}

function bindFields(): BoundField[] {
  const bound: BoundField[] = [];
  for (const spec of ARM_FIELDS) {
    for (const side of SIDES) {
      const definition = spec.definition
        ? side === 'l'
          ? spec.definition
          : mirrorMuscle(spec.definition)
        : undefined;
      const muscle = definition
        ? muscleInstance(definition, side)
        : MUSCLES.find((entry) => entry.group === spec.group && entry.side === side);
      if (!muscle) continue;
      bound.push({
        spec,
        muscle,
        gate: new Set(spec.gate.bones.map((stem) => `${stem}_${side}`)),
      });
    }
  }
  return bound;
}

/**
 * A muscle is a spindle, not a slab: widest at the belly, drawing in to a tendon
 * at each end. Both the arc it claims around the bone and how far out from the
 * axis it reaches close down towards the ends, on an elliptical profile, so the
 * field has a muscle's outline instead of a rectangle's.
 */
function spindle(spec: FieldSpec, fraction: number): { arcCos: number; radiusScale: number } {
  const taper = Math.sqrt(Math.max(0, 1 - fraction * fraction));
  const arc = spec.arcEnd + (spec.arcMiddle - spec.arcEnd) * taper;
  return { arcCos: Math.cos((arc * Math.PI) / 180), radiusScale: 0.4 + 0.6 * taper };
}

/**
 * Softness of the union between two overlapping fields, metres.
 *
 * The union has to be smooth — a plain `max` leaves a crease where the deltoid
 * meets the biceps — but it must not *add*. This blend rises above the stronger
 * of the two by at most `k · ln 2`, under a millimetre, and the result is capped
 * again below, so an arm covered by three overlapping fields is still an arm and
 * not an inflated one.
 */
const UNION_SOFTNESS = 0.0028;
/** How far the union may stand above the strongest single field, metres. */
const UNION_CEILING = 0.0035;
/** How far relaxation may lift a vertex above its own field value, metres. */
const RELAX_HEADROOM = 0.0025;

function softUnion(a: number, b: number): number {
  if (a <= 0) return b;
  if (b <= 0) return a;
  const high = Math.max(a, b);
  const low = Math.min(a, b);
  return high + UNION_SOFTNESS * Math.log1p(Math.exp(-(high - low) / UNION_SOFTNESS));
}

export interface MuscleMap {
  /** One byte per vertex: a MUSCLE_GROUP_IDS index, or ECORCHE_UNMAPPED. */
  group: Uint8Array;
  /** Bind-pose fibre direction per vertex, unit length. */
  fibre: Float32Array;
  /**
   * The field of each colourable group, per vertex, 0..1. Activation is read
   * from these and never from `group`: two fields overlap, and if the colour
   * followed whichever field happened to be strongest, a brachialis or deltoid
   * crossing the biceps would punch a grey hole through the middle of it.
   */
  groupField: Record<string, Float32Array>;
  /** Union relief height per vertex, metres, before relaxation. */
  height: Float32Array;
  /** The largest single field height at each vertex, metres — the union's cap. */
  peak: Float32Array;
  /** How strongly any field covers each vertex, 0..1. */
  mask: Float32Array;
}

/**
 * Read every arm field onto the surface, in the bind pose.
 *
 * The belly is the primary signal — the same `resolveMuscle` the overlay calls
 * every frame, so the surface and the anatomical model cannot drift apart in
 * intent. Distances are measured in metres against the belly's own axis and
 * deliberately *not* in its unit-sphere space: the fitting pass inside
 * `resolveMuscle` shrinks a belly's width and depth until it clears the skin, so
 * unit-sphere radius measures how far the fit had to pull in, and normalising by
 * it turns a snugly fitted muscle into a thin strip on the skin.
 *
 * Skin weight gates rather than selects. A vertex must carry real influence from
 * the muscle's own bones — not an exact single-bone match, or nothing near the
 * elbow could belong to the biceps — and the gate is a band, so the field fades
 * in across it instead of stepping.
 */
export function buildMuscleMap(geometry: BufferGeometry, rig: Skeleton = canonicalSkeleton): MuscleMap {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const count = position.count;

  const group = new Uint8Array(count).fill(ECORCHE_UNMAPPED);
  const fibre = new Float32Array(count * 3);
  // An unclaimed vertex still needs a finite, unit-length direction.
  for (let index = 0; index < count; index += 1) fibre[index * 3 + 1] = 1;

  const groupField: Record<string, Float32Array> = {};
  for (const id of ECORCHE_GROUPS) groupField[id] = new Float32Array(count);
  const height = new Float32Array(count);
  const peak = new Float32Array(count);
  const mask = new Float32Array(count);
  const best = new Float32Array(count);

  const guard = armGuard(geometry, rig);
  const evaluation = new PoseEvaluation(rig).apply(restPose());
  const transform = createMuscleTransform();
  const point = new Vector3();
  const offset = new Vector3();
  const across = new Vector3();
  const axis = new Vector3();
  const face = new Vector3();

  for (const { spec, muscle, gate } of bindFields()) {
    resolveMuscle(evaluation, muscle, transform);
    // The belly's own axes: +Y is the direction its fibres run, +Z the face it
    // presents to the skin.
    axis.set(0, 1, 0).applyQuaternion(transform.quaternion).normalize();
    face.set(0, 0, 1).applyQuaternion(transform.quaternion).normalize();
    const halfLength = transform.scale.y;
    const alongLimit = halfLength * spec.along;
    const radiusLimit = halfLength * spec.radius;
    const id = spec.group === null ? -1 : MUSCLE_GROUP_IDS.indexOf(spec.group);
    const field = spec.group === null ? null : groupField[spec.group];

    for (let index = 0; index < count; index += 1) {
      if (guard[index] <= 0) continue;
      point.fromBufferAttribute(position, index);
      offset.subVectors(point, transform.position);
      const along = offset.dot(axis);
      const span = along / alongLimit;
      if (Math.abs(span) >= 1) continue;

      across.copy(offset).addScaledVector(axis, -along);
      const radius = across.length();
      if (radius < 1e-6) continue;

      const { arcCos, radiusScale } = spindle(spec, Math.abs(span));
      const reach = radiusLimit * radiusScale;
      if (radius >= reach) continue;
      // Radial is a soft cut-off rather than a shape: the skin sits at roughly
      // one distance from the belly, so shaping on radius would only dim the
      // whole patch. Along and around the muscle is where the form comes from.
      const radial = 1 - smoothstep(0.78 * reach, reach, radius);

      const facing = across.dot(face) / radius;
      if (facing <= arcCos) continue;
      const angular = smoothstep(arcCos, 1, facing);

      const taper = Math.cos((Math.abs(span) * Math.PI) / 2);
      const axial = taper ** (span < 0 ? spec.proximal : spec.distal);

      const influence = boneInfluence(skinIndex, skinWeight, index, gate, rig);
      const gated = smoothstep(spec.gate.low, spec.gate.high, influence);
      if (gated <= 0) continue;

      const value = axial * radial * angular * gated * guard[index];
      if (value <= 0) continue;

      if (field) field[index] = Math.max(field[index], value);

      const raised = spec.amplitude * value;
      mask[index] = Math.max(mask[index], value);
      peak[index] = Math.max(peak[index], raised);
      height[index] = softUnion(height[index], raised);

      // Classification and fibre ownership go to the strongest field that has a
      // group at all: a shape-only belly is not a classification, and letting
      // one win here would leave the vertex reading as whichever coloured group
      // happened to be tried first.
      if (id >= 0 && value > best[index]) {
        best[index] = value;
        group[index] = id;
        fibre[index * 3] = axis.x;
        fibre[index * 3 + 1] = axis.y;
        fibre[index * 3 + 2] = axis.z;
      }
    }
  }

  for (let index = 0; index < count; index += 1) {
    // Bounded: smooth where fields overlap, but never the sum of them.
    height[index] = Math.min(height[index], peak[index] + UNION_CEILING, ECORCHE_SAFE_MAX);
  }

  return { group, fibre, groupField, height, peak, mask };
}

/**
 * Vertices that sit at the same point but are stored separately.
 *
 * The source surface is split along a few seams — 36 of them run round the
 * upper arm — and a split is invisible until something averages across the
 * mesh. Then it becomes a hard ring: smoothing cannot cross it, normals are
 * averaged on each side independently, and the arm gets a shading crease that
 * looks like a sleeve. Welding by position gives every pass one vertex where
 * the surface has one point, and the copies are kept in step behind it.
 */
function buildWeld(geometry: BufferGeometry): Int32Array {
  const position = geometry.getAttribute('position');
  const count = position.count;
  const representative = new Int32Array(count);
  const seen = new Map<string, number>();
  const round = (value: number) => Math.round(value * 1e5);
  for (let vertex = 0; vertex < count; vertex += 1) {
    const key = `${round(position.getX(vertex))},${round(position.getY(vertex))},${round(position.getZ(vertex))}`;
    const first = seen.get(key);
    if (first === undefined) {
      seen.set(key, vertex);
      representative[vertex] = vertex;
    } else {
      representative[vertex] = first;
    }
  }
  return representative;
}

/** Average the normals of welded copies, so a seam stops shading like an edge. */
function weldNormals(geometry: BufferGeometry, weld: Int32Array): void {
  const normal = geometry.getAttribute('normal');
  const count = normal.count;
  const sum = new Float32Array(count * 3);
  for (let vertex = 0; vertex < count; vertex += 1) {
    const owner = weld[vertex] * 3;
    sum[owner] += normal.getX(vertex);
    sum[owner + 1] += normal.getY(vertex);
    sum[owner + 2] += normal.getZ(vertex);
  }
  const scratch = new Vector3();
  for (let vertex = 0; vertex < count; vertex += 1) {
    const owner = weld[vertex] * 3;
    scratch.set(sum[owner], sum[owner + 1], sum[owner + 2]);
    if (scratch.lengthSq() < 1e-12) continue;
    scratch.normalize();
    normal.setXYZ(vertex, scratch.x, scratch.y, scratch.z);
  }
  normal.needsUpdate = true;
}

/**
 * Nothing that belongs to the torso, the neck, the head or the hands.
 *
 * The gates on the individual fields are about which muscle owns a vertex; this
 * is about which *limb* it belongs to at all. A vertex in the armpit carries a
 * little humerus weight and a lot of ribcage, and one at the wrist carries a
 * little forearm and a lot of hand — enough for a loose gate to let a muscle
 * claim it, which is how relief ends up on a chest or a knuckle. Weight on a
 * bone the arm round has no business touching closes the vertex off entirely.
 */
function armGuard(geometry: BufferGeometry, rig: Skeleton): Float32Array {
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const count = skinIndex.count;
  const blocked = new Set<string>([
    'head',
    'neck',
    'spine_01',
    'spine_02',
    'spine_03',
    'pelvis',
  ]);
  for (const side of SIDES) blocked.add(`hand_${side}`);

  const guard = new Float32Array(count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    guard[vertex] = 1 - smoothstep(0.08, 0.3, boneInfluence(skinIndex, skinWeight, vertex, blocked, rig));
  }
  return guard;
}

/**
 * The arm, as a smooth 0..1 region of the surface: shoulder cap to wrist.
 *
 * Deliberately not the muscle fields. Those leave gaps — between the deltoid's
 * distal fade and the biceps' proximal one there is a ring the fields barely
 * cover, and that ring is exactly where the source mesh's own horizontal band
 * sits. Smoothing scaled by field strength therefore cannot reach the one place
 * that needs it. Humerus and forearm weight give a region with no holes in it,
 * and it falls away on its own at the shoulder and at the wrist, where the
 * weight passes to the torso and to the hand.
 */
function armRegion(geometry: BufferGeometry, rig: Skeleton): Float32Array {
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const count = skinIndex.count;
  const bones = new Set<string>();
  for (const side of SIDES) bones.add(`upperarm_${side}`).add(`forearm_${side}`);

  const guard = armGuard(geometry, rig);
  const region = new Float32Array(count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    region[vertex] =
      smoothstep(0.3, 0.7, boneInfluence(skinIndex, skinWeight, vertex, bones, rig)) * guard[vertex];
  }
  return region;
}

/**
 * Settle the surface itself, inside the arm fields and nowhere else.
 *
 * The character's arm arrives with a horizontal band across the upper arm — a
 * ring of the source scan's own topology, visible in Character mode too. Muscle
 * relief laid over it reads as bulges stacked on a segmented tube rather than
 * as one arm, so a few weak Laplacian passes take it out first.
 *
 * The step each vertex takes is scaled by how strongly the muscle fields cover
 * it, which is what keeps this honest: it is zero outside the arm, so the torso
 * and the hands are untouched, and it fades to nothing at the field's own edge
 * rather than ending in a new seam of its own.
 */
function settleSurface(
  geometry: BufferGeometry,
  mask: Float32Array,
  weld: Int32Array,
  iterations = 4,
  lambda = 0.48,
): void {
  const index = geometry.getIndex();
  if (!index) return;
  const position = geometry.getAttribute('position');
  const count = position.count;

  const owned = new Float32Array(count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    owned[weld[vertex]] = Math.max(owned[weld[vertex]], mask[vertex]);
  }

  const sum = new Float32Array(count * 3);
  const degree = new Uint16Array(count);
  const corner = [0, 0, 0];

  for (let pass = 0; pass < iterations; pass += 1) {
    sum.fill(0);
    degree.fill(0);
    for (let triangle = 0; triangle < index.count; triangle += 3) {
      corner[0] = weld[index.getX(triangle)];
      corner[1] = weld[index.getX(triangle + 1)];
      corner[2] = weld[index.getX(triangle + 2)];
      for (let self = 0; self < 3; self += 1) {
        const vertex = corner[self];
        if (owned[vertex] <= 0) continue;
        for (let other = 0; other < 3; other += 1) {
          if (other === self || corner[other] === vertex) continue;
          const neighbour = corner[other];
          sum[vertex * 3] += position.getX(neighbour);
          sum[vertex * 3 + 1] += position.getY(neighbour);
          sum[vertex * 3 + 2] += position.getZ(neighbour);
          degree[vertex] += 1;
        }
      }
    }
    for (let vertex = 0; vertex < count; vertex += 1) {
      const strength = owned[vertex];
      if (strength <= 0 || degree[vertex] === 0 || weld[vertex] !== vertex) continue;
      const step = lambda * Math.min(1, strength);
      const inverse = 1 / degree[vertex];
      position.setXYZ(
        vertex,
        position.getX(vertex) + step * (sum[vertex * 3] * inverse - position.getX(vertex)),
        position.getY(vertex) + step * (sum[vertex * 3 + 1] * inverse - position.getY(vertex)),
        position.getZ(vertex) + step * (sum[vertex * 3 + 2] * inverse - position.getZ(vertex)),
      );
    }
    // The copies follow their owner, so the seam never opens.
    for (let vertex = 0; vertex < count; vertex += 1) {
      const owner = weld[vertex];
      if (owner === vertex) continue;
      position.setXYZ(vertex, position.getX(owner), position.getY(owner), position.getZ(owner));
    }
  }
  position.needsUpdate = true;
  geometry.computeVertexNormals();
  weldNormals(geometry, weld);
}

/**
 * Smooth the relief across the mesh, without letting it walk off the muscle.
 *
 * The surface is coarse enough that a field sampled per vertex shows the
 * triangles it was sampled on. A few Laplacian passes over the *height scalar*
 * settle that. The danger is that Laplacian smoothing follows mesh adjacency,
 * which does not care about anatomy — left alone it would carry the deltoid's
 * relief onto the chest and the flexors' onto the hand. So every pass is clamped
 * back to what the field itself supports: zero where there is no support at all,
 * and a hair above its own value where there is.
 */
function relaxHeight(
  geometry: BufferGeometry,
  height: Float32Array,
  peak: Float32Array,
  weld: Int32Array,
  iterations = 6,
  lambda = 0.5,
): void {
  const index = geometry.getIndex();
  if (!index) return;
  const count = height.length;

  // One height per point on the surface, not per stored copy.
  for (let vertex = 0; vertex < count; vertex += 1) {
    const owner = weld[vertex];
    if (owner === vertex) continue;
    height[owner] = Math.max(height[owner], height[vertex]);
    peak[owner] = Math.max(peak[owner], peak[vertex]);
  }

  const ceiling = new Float32Array(count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    ceiling[vertex] = peak[vertex] > 0 ? Math.min(peak[vertex] + RELAX_HEADROOM, ECORCHE_SAFE_MAX) : 0;
  }

  const sum = new Float32Array(count);
  const degree = new Uint16Array(count);
  const corner = [0, 0, 0];

  for (let pass = 0; pass < iterations; pass += 1) {
    sum.fill(0);
    degree.fill(0);
    for (let triangle = 0; triangle < index.count; triangle += 3) {
      corner[0] = weld[index.getX(triangle)];
      corner[1] = weld[index.getX(triangle + 1)];
      corner[2] = weld[index.getX(triangle + 2)];
      for (let self = 0; self < 3; self += 1) {
        for (let other = 0; other < 3; other += 1) {
          if (other === self || corner[other] === corner[self]) continue;
          sum[corner[self]] += height[corner[other]];
          degree[corner[self]] += 1;
        }
      }
    }
    for (let vertex = 0; vertex < count; vertex += 1) {
      if (weld[vertex] !== vertex) continue;
      if (ceiling[vertex] <= 0) {
        height[vertex] = 0;
        continue;
      }
      if (degree[vertex] === 0) continue;
      const mean = sum[vertex] / degree[vertex];
      const value = height[vertex] + lambda * (mean - height[vertex]);
      height[vertex] = Math.min(Math.max(0, value), ceiling[vertex]);
    }
  }

  for (let vertex = 0; vertex < count; vertex += 1) {
    if (weld[vertex] !== vertex) height[vertex] = height[weld[vertex]];
  }
}

/**
 * Push the surface out over the arm so its muscles have form rather than
 * colour.
 *
 * Displacing the *bind pose* rather than shading it means the relief is real
 * geometry: it skins with the arm, catches light from any direction, and shows
 * on the silhouette.
 */
export function sculptRelief(
  geometry: BufferGeometry,
  map: MuscleMap,
  weld: Int32Array,
  rig: Skeleton = canonicalSkeleton,
): void {
  const position = geometry.getAttribute('position');
  const normal = geometry.getAttribute('normal');
  const point = new Vector3();
  const direction = new Vector3();

  settleSurface(geometry, armRegion(geometry, rig), weld);
  relaxHeight(geometry, map.height, map.peak, weld);

  for (let index = 0; index < position.count; index += 1) {
    const height = map.height[index];
    if (height <= 0) continue;
    point.fromBufferAttribute(position, index);
    // The welded normal, so copies of one point move together.
    direction.set(normal.getX(index), normal.getY(index), normal.getZ(index));
    point.addScaledVector(direction, height);
    position.setXYZ(index, point.x, point.y, point.z);
  }
  position.needsUpdate = true;
  // The form only reads if the lighting knows about it.
  geometry.computeVertexNormals();
  weldNormals(geometry, weld);
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
}

/** The per-group fields carried on an écorché geometry. */
export const ecorcheFields = (geometry: BufferGeometry): Record<string, Float32Array> =>
  (geometry.userData.muscleFields ?? {}) as Record<string, Float32Array>;

/** The relief height applied to each vertex, metres. */
export const ecorcheHeight = (geometry: BufferGeometry): Float32Array =>
  (geometry.userData.muscleHeight ?? new Float32Array(0)) as Float32Array;

/**
 * Write the per-vertex activation scalar the shader interpolates.
 *
 * Taken from each group's own field and combined by strength, so a vertex the
 * biceps field covers stays lit however many other shape fields overlap it
 * there. The value is continuous, which is the point: the shader thresholds it,
 * and a threshold on an interpolated field lands inside a triangle rather than
 * on its edge.
 */
export function applyActivation(geometry: BufferGeometry, involvement: MuscleInvolvement): void {
  const activation = geometry.getAttribute('muscleActivation');
  const fields = ecorcheFields(geometry);
  const levels = activationMap(involvement);

  const lit: [Float32Array, number][] = [];
  for (const id of ECORCHE_GREYSCALE ? [] : ECORCHE_GROUPS) {
    const strength = ECORCHE_ACTIVATION[activationOf(levels, id)];
    const field = fields[id];
    if (strength > 0 && field) lit.push([field, strength]);
  }

  for (let index = 0; index < activation.count; index += 1) {
    let value = 0;
    for (const [field, strength] of lit) value = Math.max(value, field[index] * strength);
    activation.setX(index, value);
  }
  activation.needsUpdate = true;
}

/**
 * Off. Local refinement is written and works, but the elbow re-weighting is
 * being judged on the character's own topology first, so that what the weights
 * alone are worth can be seen without more triangles confusing the picture.
 */
const REFINE_ARM = false;

/**
 * More surface, only where the arm needs it.
 *
 * Two passes. The first covers the whole limb, from the shoulder cap to the
 * wrist, which is what carries the anatomical contours. The second covers the
 * blend zone at the elbow alone — the ring of vertices influenced by both the
 * humerus and the forearm — because that is the ring that has to fold, and at
 * the character's own density it folds to a wedge with a visible polygon edge
 * in it.
 *
 * Everything outside those regions keeps the character's own triangles.
 */
function refineArm(geometry: BufferGeometry, rig: Skeleton): BufferGeometry {
  const arm = new Set<string>();
  for (const side of SIDES) arm.add(`upperarm_${side}`).add(`forearm_${side}`);

  const limb = refineRegion(geometry, (vertex) =>
    boneInfluence(
      geometry.getAttribute('skinIndex'),
      geometry.getAttribute('skinWeight'),
      vertex,
      arm,
      rig,
    ) > 0.25,
  );

  const skinIndex = limb.getAttribute('skinIndex');
  const skinWeight = limb.getAttribute('skinWeight');
  return refineRegion(limb, (vertex) =>
    SIDES.some((side) => {
      const upper = boneInfluence(skinIndex, skinWeight, vertex, new Set([`upperarm_${side}`]), rig);
      const lower = boneInfluence(skinIndex, skinWeight, vertex, new Set([`forearm_${side}`]), rig);
      return upper > 0.12 && lower > 0.12;
    }),
  );
}

/** The écorché body: the character's own geometry, read as fields, sculpted and repainted. */
export function buildEcorcheGeometry(rig: Skeleton = canonicalSkeleton): BufferGeometry {
  const source = buildBodyGeometry(rig).geometry;
  const geometry = REFINE_ARM ? refineArm(source, rig) : source;
  blendElbowWeights(geometry, rig);
  const weld = buildWeld(geometry);
  const map = buildMuscleMap(geometry, rig);
  sculptRelief(geometry, map, weld, rig);
  const count = geometry.getAttribute('position').count;

  // Categorical, so explicitly not normalised: these are ids, not colours.
  geometry.setAttribute('muscleGroup', new BufferAttribute(map.group, 1, false));
  geometry.setAttribute('muscleFibre', new BufferAttribute(map.fibre, 3));
  geometry.setAttribute('muscleActivation', new BufferAttribute(new Float32Array(count), 1));
  geometry.setAttribute('color', new BufferAttribute(ecorcheColours(geometry), 3, true));
  geometry.userData.muscleFields = map.groupField;
  geometry.userData.muscleHeight = map.height;
  return geometry;
}

/**
 * The fibre direction after skinning, on the CPU.
 *
 * The same weighted bone transform the shader builds — `bindMatrixInverse *
 * Σ(weight · boneMatrix) * bindMatrix`, applied as a direction — written out here
 * so the GPU's version has something to be checked against, and so the maths is
 * readable somewhere other than inside a string of GLSL.
 */
export function blendedSkinMatrix(mesh: SkinnedMesh, vertex: number, out: Matrix4): Matrix4 {
  const geometry = mesh.geometry;
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const skeleton = mesh.skeleton;

  for (let element = 0; element < 16; element += 1) out.elements[element] = 0;

  const bone = new Matrix4();
  for (let slot = 0; slot < 4; slot += 1) {
    const weight = skinWeight.getComponent(vertex, slot);
    if (weight === 0) continue;
    const index = skinIndex.getComponent(vertex, slot);
    bone.multiplyMatrices(skeleton.bones[index].matrixWorld, skeleton.boneInverses[index]);
    for (let element = 0; element < 16; element += 1) {
      out.elements[element] += bone.elements[element] * weight;
    }
  }

  return out.premultiply(mesh.bindMatrixInverse).multiply(mesh.bindMatrix);
}

export function skinnedFibre(mesh: SkinnedMesh, vertex: number, out: Vector3): Vector3 {
  const fibre = mesh.geometry.getAttribute('muscleFibre');
  const blended = blendedSkinMatrix(mesh, vertex, new Matrix4());
  out.set(fibre.getX(vertex), fibre.getY(vertex), fibre.getZ(vertex));
  // A direction, so the translation column plays no part.
  return out.transformDirection(blended);
}

// Striations stay off: the question this round asks is whether the geometry can
// carry the arm, so nothing is allowed to stand in for form.
const FIBRE_FREQUENCY = 520;
/** Half-width of the activation border, in field units. */
const EDGE = 0.07;

/**
 * The écorché material.
 *
 * Two things happen here that a stock material cannot do. The fibre direction is
 * skinned — three skins position and normal, and nothing else, so a custom
 * direction attribute would otherwise stay in its bind orientation while the arm
 * bends. And the activation field is turned into a border rather than a
 * gradient: it arrives as the muscle's own continuous field, and a narrow
 * smoothstep about the colour threshold picks out one contour of it, so the
 * biceps has an edge that follows its sculpted form instead of the mesh's
 * triangles.
 */
export function createEcorcheMaterial(): MeshStandardMaterial {
  const material = new MeshStandardMaterial({
    color: '#ffffff',
    vertexColors: true,
    roughness: 0.44,
    metalness: 0.0,
  });

  material.onBeforeCompile = (shader) => {
    shader.uniforms.uActiveColour = { value: new Color(ECORCHE_ACTIVE_COLOUR) };

    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        `#include <common>
        attribute float muscleActivation;
        attribute vec3 muscleFibre;
        varying float vActivation;
        varying float vFibrePhase;
        varying vec3 vFibreWorld;`,
      )
      .replace(
        '#include <skinnormal_vertex>',
        `#include <skinnormal_vertex>
        // The same weighted bone transform the position gets, built from the
        // matrices skinbase_vertex has already fetched. Directions carry no
        // translation, so the w is zero.
        vec3 ecorcheFibre = muscleFibre;
        #ifdef USE_SKINNING
          mat4 fibreMatrix = mat4( 0.0 );
          fibreMatrix += skinWeight.x * boneMatX;
          fibreMatrix += skinWeight.y * boneMatY;
          fibreMatrix += skinWeight.z * boneMatZ;
          fibreMatrix += skinWeight.w * boneMatW;
          fibreMatrix = bindMatrixInverse * fibreMatrix * bindMatrix;
          ecorcheFibre = ( fibreMatrix * vec4( muscleFibre, 0.0 ) ).xyz;
        #endif
        vFibreWorld = normalize( ( modelMatrix * vec4( ecorcheFibre, 0.0 ) ).xyz );
        // The stripe phase is measured in the bind pose, so the striations stay
        // painted on the muscle instead of swimming across it as the arm moves.
        vFibrePhase = dot( position, muscleFibre ) * ${FIBRE_FREQUENCY.toFixed(1)};
        vActivation = muscleActivation;`,
      );

    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
        uniform vec3 uActiveColour;
        varying float vActivation;`,
      )
      .replace(
        '#include <color_fragment>',
        `#include <color_fragment>
        float ecorcheActive = smoothstep(
          ${(ECORCHE_COLOUR_THRESHOLD - EDGE).toFixed(3)},
          ${(ECORCHE_COLOUR_THRESHOLD + EDGE).toFixed(3)},
          vActivation
        );
        diffuseColor.rgb = mix( diffuseColor.rgb, uActiveColour, ecorcheActive );`,
      );
  };

  // Two materials with different shaders must not share a compiled program.
  material.customProgramCacheKey = () => 'ecorche';
  return material;
}
