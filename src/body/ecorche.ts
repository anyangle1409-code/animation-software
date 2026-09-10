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
  hair: '#3a3833',
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
const PALETTE_PARTS = ['skin', 'hair', 'shorts', 'sclera', 'iris', 'pupil'] as const;
type PalettePart = (typeof PALETTE_PARTS)[number];

const SOURCE_BYTES: Record<PalettePart, [number, number, number]> = {
  skin: linearBytes(ANATOMICAL_PALETTE.skin),
  hair: linearBytes(ANATOMICAL_PALETTE.hair),
  shorts: linearBytes(ANATOMICAL_PALETTE.shorts),
  sclera: linearBytes(ANATOMICAL_PALETTE.sclera),
  iris: linearBytes(ANATOMICAL_PALETTE.iris),
  pupil: linearBytes(ANATOMICAL_PALETTE.pupil),
};

const ECORCHE_BYTES: Record<PalettePart, [number, number, number]> = {
  skin: linearBytes(ECORCHE_PALETTE.muscle),
  hair: linearBytes(ECORCHE_PALETTE.hair),
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
  /** Which limb guard applies — see `armGuard` and `torsoGuard`. */
  region: 'arm' | 'torso';
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
   * Fraction of that arc held at full strength before the field starts to fade,
   * 0 to 1. A spindle leaves this alone and peaks along one line, which is what
   * a biceps does. A sheet does not: a pectoral is the same thickness across
   * most of its width and only thins at its border, and without a plateau the
   * field would put its whole crown on the sheet's centre line and read as a
   * ridge instead of a plate.
   */
  plateau?: number;
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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
    region: 'arm',
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

/**
 * The upper body. Sheets rather than spindles: a pectoral or a latissimus lies
 * flat against the ribs and covers a wide arc, so these carry much wider arcs
 * and much lower crowns than the arm's fields. The point is that the torso stops
 * reading as one smooth slab, not that every muscle announces itself.
 *
 * The studio's model has no serratus, so the lateral rib contour is left to the
 * lower edge of the pectoral, the oblique's flank and the latissimus running
 * down to the waist. Nothing here invents a belly the model does not have.
 */
const TORSO_FIELDS: readonly FieldSpec[] = [
  {
    id: 'pectoralis',
    region: 'torso',
    group: 'pectoralis',
    amplitude: 0.0118,
    along: 1.02,
    radius: 1.05,
    // A sheet: nearly two thirds of the way round from its own face. The wide
    // plateau is what gives it a border — held flat across most of its width, the
    // field has somewhere to fall from, and the lower edge reads under flat light
    // instead of dissolving into the ribs.
    arcMiddle: 84,
    arcEnd: 34,
    plateau: 0.76,
    // +Y runs sternum to humerus, so the fuller end is the sternal one. Not too
    // full: left higher, the field runs up onto the collarbone and the chest
    // gets a bony shelf across the top of it.
    proximal: 1.3,
    distal: 1.55,
    gate: { bones: ['spine_03', 'clavicle', 'upperarm'], low: 0.3, high: 0.62 },
  },
  {
    id: 'trapezius_upper',
    region: 'torso',
    group: 'trapezius_upper',
    amplitude: 0.008,
    along: 3.2,
    radius: 2.6,
    arcMiddle: 80,
    arcEnd: 34,
    plateau: 0.6,
    proximal: 1.2,
    distal: 1.2,
    gate: { bones: ['neck', 'clavicle', 'spine_03'], low: 0.3, high: 0.6 },
  },
  {
    id: 'trapezius_mid',
    region: 'torso',
    group: 'trapezius_mid',
    amplitude: 0.0098,
    along: 2.6,
    radius: 2.4,
    arcMiddle: 82,
    arcEnd: 34,
    plateau: 0.6,
    proximal: 1.2,
    distal: 1.2,
    gate: { bones: ['clavicle', 'spine_03', 'spine_02'], low: 0.3, high: 0.6 },
  },
  {
    id: 'latissimus',
    region: 'torso',
    group: 'latissimus',
    amplitude: 0.0108,
    along: 1.02,
    radius: 0.62,
    arcMiddle: 76,
    arcEnd: 30,
    plateau: 0.58,
    // +Y runs from the lower back up to the armpit: broad below, drawn to a
    // tendon above, which is what gives the taper into the waist.
    proximal: 0.95,
    distal: 1.9,
    gate: { bones: ['spine_01', 'spine_02', 'spine_03', 'upperarm'], low: 0.3, high: 0.62 },
  },
  {
    id: 'obliques',
    region: 'torso',
    group: 'obliques',
    amplitude: 0.0072,
    along: 1.0,
    // The flank sits a good deal further out than the belly the model places
    // under it, so these reaches are wide on purpose.
    radius: 0.78,
    arcMiddle: 70,
    arcEnd: 28,
    plateau: 0.55,
    proximal: 1.35,
    distal: 1.15,
    gate: { bones: ['pelvis', 'spine_01', 'spine_02'], low: 0.3, high: 0.6 },
  },
  {
    id: 'rectus_abdominis',
    region: 'torso',
    group: 'rectus_abdominis',
    // Restrained on purpose: an abdominal wall that reads at all is enough, and
    // a defined six-pack on an otherwise smooth body looks stuck on.
    amplitude: 0.0076,
    along: 0.98,
    radius: 0.9,
    arcMiddle: 56,
    arcEnd: 24,
    plateau: 0.5,
    proximal: 1.35,
    distal: 1.2,
    gate: { bones: ['pelvis', 'spine_01', 'spine_02', 'spine_03'], low: 0.35, high: 0.65 },
  },
];

/** Every field the anatomy view sculpts. */
const FIELDS: readonly FieldSpec[] = [...ARM_FIELDS, ...TORSO_FIELDS];

/** The groups the surface can classify and colour. Shape-only fields are not here. */
export const ECORCHE_GROUPS: readonly MuscleGroupId[] = [
  ...new Set(FIELDS.map((field) => field.group).filter((group): group is MuscleGroupId => group !== null)),
];

const SIDES: readonly Side[] = ['l', 'r'];

/** A field spec bound to one side, with the belly it reads. */
interface BoundField {
  spec: FieldSpec;
  muscle: MuscleInstance;
  gate: ReadonlySet<string>;
}

const sided = new Set(['upperarm', 'forearm', 'hand', 'clavicle', 'thigh', 'shin', 'foot']);

function bindFields(): BoundField[] {
  const bound: BoundField[] = [];
  for (const spec of FIELDS) {
    for (const side of SIDES) {
      const definition = spec.definition
        ? side === 'l'
          ? spec.definition
          : mirrorMuscle(spec.definition)
        : undefined;
      const muscle = definition
        ? muscleInstance(definition, side)
        : MUSCLES.find(
            (entry) =>
              entry.group === spec.group && (entry.side === side || entry.side === null),
          );
      // A muscle on the centre line has no side, so it is bound once and the
      // second pass would otherwise sculpt it twice.
      if (!muscle || (muscle.side === null && side !== 'l')) continue;
      // A gate names bone stems. The paired ones take the side; the ones on the
      // centre line — spine, pelvis, neck — are already whole names.
      bound.push({
        spec,
        muscle,
        gate: new Set(
          spec.gate.bones.map((stem) => (sided.has(stem) ? `${stem}_${side}` : stem)),
        ),
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

  const guards = { arm: armGuard(geometry, rig), torso: torsoGuard(geometry, rig) };
  const evaluation = new PoseEvaluation(rig).apply(restPose());
  const transform = createMuscleTransform();
  const point = new Vector3();
  const offset = new Vector3();
  const across = new Vector3();
  const axis = new Vector3();
  const face = new Vector3();

  for (const { spec, muscle, gate } of bindFields()) {
    const guard = guards[spec.region];
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
      // Where the fade starts: at the crown for a spindle, part-way out for a
      // sheet.
      const plateauCos = spec.plateau ? Math.cos(Math.acos(arcCos) * (1 - spec.plateau)) : 1;
      const reach = radiusLimit * radiusScale;
      if (radius >= reach) continue;
      // Radial is a soft cut-off rather than a shape: the skin sits at roughly
      // one distance from the belly, so shaping on radius would only dim the
      // whole patch. Along and around the muscle is where the form comes from.
      const radial = 1 - smoothstep(0.78 * reach, reach, radius);

      const facing = across.dot(face) / radius;
      if (facing <= arcCos) continue;
      const angular = smoothstep(arcCos, plateauCos, facing);

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
 * Conservative proportion corrections to the upper body, in the bind pose.
 *
 * Muscle relief alone could not get this torso to read as athletic, because the
 * shapes underneath it are not athletic: the source surface carries soft breast
 * forms where a pectoral plate should be, and a rounded lower abdomen. Relief
 * laid over those reads as muscle drawn on a different body.
 *
 * Three corrections, each a smooth bounded pull with no hard edge anywhere, and
 * each at most 9 mm — small enough that the character is recognisably the same
 * person, large enough that the chest reads as a plate and the waist as a waist.
 * They are applied to the anatomy geometry only, before the fields are sampled,
 * so the muscle relief sits on the corrected shape.
 */
const TORSO_SHAPE = {
  /** Flattening across the breast, into a pectoral plate. */
  chest: 0.0085,
  /** Drawing in the lower abdomen. */
  belly: 0.011,
  /** Narrowing the flanks. */
  waist: 0.006,
};

/** A smooth 0 → 1 → 0 hat across a span. */
const hat = (value: number, low: number, high: number): number => {
  if (value <= low || value >= high) return 0;
  return Math.sin((Math.PI * (value - low)) / (high - low));
};

function shapeTorso(geometry: BufferGeometry, rig: Skeleton, weld: Int32Array): void {
  const position = geometry.getAttribute('position');
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const own = new Set<string>(['spine_01', 'spine_02', 'spine_03', 'pelvis']);
  const guard = torsoGuard(geometry, rig);
  const normal = geometry.getAttribute('normal');
  const pit = pitGuard(geometry, weld);
  const offset = new Float32Array(position.count * 3);
  const allowed = new Uint8Array(position.count);

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    const owned =
      smoothstep(0.45, 0.8, boneInfluence(skinIndex, skinWeight, vertex, own, rig)) * guard[vertex];
    if (owned <= 0) continue;
    allowed[vertex] = 1;

    const x = position.getX(vertex);
    const y = position.getY(vertex);
    const z = position.getZ(vertex);
    const side = Math.abs(x);

    // Only where the surface actually faces the way it is being pulled. The
    // navel is a pit: its rim faces sideways and inward, and drawing that back
    // along with the wall around it closes the dimple through itself.
    const facesFront = smoothstep(0.2, 0.55, normal.getZ(vertex));
    const facesSide = smoothstep(0.2, 0.55, Math.abs(normal.getX(vertex)));

    // The breast, pulled back towards the ribs. Peaks off the centre line so the
    // sternum is left where it is.
    const chest =
      TORSO_SHAPE.chest * hat(y, 1.215, 1.34) * hat(side, 0.005, 0.125) * smoothstep(0.07, 0.105, z);
    // The lower abdomen, drawn in but not hollowed.
    const belly =
      TORSO_SHAPE.belly * hat(y, 1.02, 1.215) * smoothstep(0.05, 0.09, z) * (1 - smoothstep(0.085, 0.14, side));
    // The flanks, for the taper into the waist.
    const waist = TORSO_SHAPE.waist * hat(y, 1.0, 1.25) * smoothstep(0.065, 0.1, side);

    offset[vertex * 3] = -Math.sign(x) * waist * owned * facesSide * pit[vertex];
    offset[vertex * 3 + 2] = -(chest + belly) * owned * facesFront * pit[vertex];
  }

  // Smooth the correction, not the surface. Ownership comes from skin weight,
  // and a weight boundary running across the belly makes neighbouring vertices
  // move by different amounts — enough, at the rim of something as small as the
  // navel, to turn a triangle inside out. Relaxing the offsets first keeps
  // neighbours moving together and leaves the detail where it is.
  relaxVectorField(geometry, offset, weld, allowed, 4);

  for (let vertex = 0; vertex < position.count; vertex += 1) {
    if (offset[vertex * 3] === 0 && offset[vertex * 3 + 2] === 0) continue;
    position.setXYZ(
      vertex,
      position.getX(vertex) + offset[vertex * 3],
      position.getY(vertex) + offset[vertex * 3 + 1],
      position.getZ(vertex) + offset[vertex * 3 + 2],
    );
  }
  position.needsUpdate = true;
  geometry.computeVertexNormals();
  weldNormals(geometry, weld);
}

/**
 * How much of a displacement a vertex can take before it turns its own
 * neighbourhood inside out.
 *
 * Offsetting a surface along its normals shrinks anything concave: a pit whose
 * radius of curvature is smaller than the offset closes through itself. The
 * navel is the clear case — a few millimetres across, and every field that
 * reaches the abdominal wall would push its rim past its floor. So each vertex
 * is measured against the centroid of its neighbours: where they sit outward of
 * it along its own normal, it is in a hollow, and its allowance falls away.
 */
function pitGuard(geometry: BufferGeometry, weld: Int32Array): Float32Array {
  const index = geometry.getIndex();
  const position = geometry.getAttribute('position');
  const normal = geometry.getAttribute('normal');
  const count = position.count;
  const guard = new Float32Array(count).fill(1);
  if (!index) return guard;

  const sum = new Float32Array(count * 3);
  const span = new Float32Array(count);
  const degree = new Uint32Array(count);
  const corner = [0, 0, 0];
  const here = new Vector3();
  const there = new Vector3();

  for (let triangle = 0; triangle < index.count; triangle += 3) {
    corner[0] = weld[index.getX(triangle)];
    corner[1] = weld[index.getX(triangle + 1)];
    corner[2] = weld[index.getX(triangle + 2)];
    for (let self = 0; self < 3; self += 1) {
      here.fromBufferAttribute(position, corner[self]);
      for (let other = 0; other < 3; other += 1) {
        if (other === self || corner[other] === corner[self]) continue;
        there.fromBufferAttribute(position, corner[other]);
        sum[corner[self] * 3] += there.x;
        sum[corner[self] * 3 + 1] += there.y;
        sum[corner[self] * 3 + 2] += there.z;
        span[corner[self]] += here.distanceTo(there);
        degree[corner[self]] += 1;
      }
    }
  }

  for (let vertex = 0; vertex < count; vertex += 1) {
    const owner = weld[vertex];
    if (degree[owner] === 0) continue;
    here.fromBufferAttribute(position, owner);
    there
      .set(sum[owner * 3], sum[owner * 3 + 1], sum[owner * 3 + 2])
      .divideScalar(degree[owner])
      .sub(here);
    const hollow = there.dot(
      new Vector3(normal.getX(owner), normal.getY(owner), normal.getZ(owner)),
    );
    const edge = span[owner] / degree[owner];
    guard[vertex] = 1 - smoothstep(0.02 * edge, 0.16 * edge, hollow);
  }
  return guard;
}

/**
 * Raise a surface out of its own hollows, in a named region.
 *
 * Smoothing was the first thing tried on the neck's notch and it is the wrong
 * tool: a Laplacian pass drags the trapezius ridge either side of the valley
 * down towards it, and at enough strength to close the notch it turns the ridge
 * inside out. This does the opposite — it moves outward, only where the surface
 * is concave, and by an amount that falls to nothing as the hollow does. A flat
 * or convex vertex is untouched, so nothing is added where nothing was missing,
 * and displacement away from a concavity cannot fold it.
 */

/** Laplacian smoothing of a per-vertex vector, over welded mesh adjacency. */
function relaxVectorField(
  geometry: BufferGeometry,
  field: Float32Array,
  weld: Int32Array,
  allowed: Uint8Array,
  iterations: number,
  lambda = 0.5,
): void {
  const index = geometry.getIndex();
  if (!index) return;
  const count = field.length / 3;
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
        for (let other = 0; other < 3; other += 1) {
          if (other === self || corner[other] === corner[self]) continue;
          for (let axis = 0; axis < 3; axis += 1) {
            sum[corner[self] * 3 + axis] += field[corner[other] * 3 + axis];
          }
          degree[corner[self]] += 1;
        }
      }
    }
    for (let vertex = 0; vertex < count; vertex += 1) {
      if (weld[vertex] !== vertex || degree[vertex] === 0) continue;
      // Outside the region that owns the correction the field stays at zero, so
      // smoothing cannot walk it onto a hip or a shoulder that was excluded.
      if (!allowed[vertex]) {
        field[vertex * 3] = 0;
        field[vertex * 3 + 1] = 0;
        field[vertex * 3 + 2] = 0;
        continue;
      }
      for (let axis = 0; axis < 3; axis += 1) {
        const mean = sum[vertex * 3 + axis] / degree[vertex];
        field[vertex * 3 + axis] += lambda * (mean - field[vertex * 3 + axis]);
      }
    }
    for (let vertex = 0; vertex < count; vertex += 1) {
      const owner = weld[vertex];
      if (owner === vertex) continue;
      for (let axis = 0; axis < 3; axis += 1) field[vertex * 3 + axis] = field[owner * 3 + axis];
    }
  }
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
  for (const side of SIDES) {
    blocked.add(`hand_${side}`).add(`thigh_${side}`).add(`shin_${side}`).add(`foot_${side}`);
  }

  const guard = new Float32Array(count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    guard[vertex] = 1 - smoothstep(0.08, 0.3, boneInfluence(skinIndex, skinWeight, vertex, blocked, rig));
  }
  return guard;
}

/**
 * The other half of the same idea: nothing that belongs to the head, the arms
 * below the shoulder, or the legs.
 *
 * The torso's own muscles legitimately reach onto the humerus — the pectoral and
 * the latissimus both insert there, and a sheet that stopped at the shoulder
 * joint would leave a seam across the armpit — so the humerus is allowed and it
 * is the forearm and beyond that are shut out.
 */
function torsoGuard(geometry: BufferGeometry, rig: Skeleton): Float32Array {
  const skinIndex = geometry.getAttribute('skinIndex');
  const skinWeight = geometry.getAttribute('skinWeight');
  const count = skinIndex.count;
  const blocked = new Set<string>(['head']);
  for (const side of SIDES) {
    blocked.add(`forearm_${side}`).add(`hand_${side}`);
    blocked.add(`thigh_${side}`).add(`shin_${side}`).add(`foot_${side}`);
  }

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
  const pit = pitGuard(geometry, weld);
  for (let vertex = 0; vertex < map.height.length; vertex += 1) {
    map.height[vertex] *= pit[vertex];
    map.peak[vertex] *= pit[vertex];
  }
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

/**
 * Pull back any displacement that turned a triangle over.
 *
 * Every stage here moves the surface along its own normals and each one guards
 * its own region, but a vertex can be moved by two of them — the neck levelling
 * and the torso, say — and neither sees the other's contribution. This is the
 * one check over the finished result: a triangle that ends up facing against the
 * way the character's own surface faced, or collapsed to a sliver of it, has the
 * *total* displacement of its corners halved, repeatedly, until it does not.
 *
 * Damping the corners rather than the last stage's contribution keeps it
 * independent of the order the stages ran in, and it costs relief only on the
 * triangles that were about to fold.
 */
function keepFacing(geometry: BufferGeometry, rest: Float32Array): number {
  const index = geometry.getIndex();
  if (!index) return 0;
  const position = geometry.getAttribute('position');
  const count = position.count;

  const move = new Float32Array(count * 3);
  for (let vertex = 0; vertex < count * 3; vertex += 1) {
    move[vertex] = (position.array as ArrayLike<number>)[vertex] - rest[vertex];
  }

  const first = new Vector3();
  const second = new Vector3();
  const third = new Vector3();
  const before = new Vector3();
  const after = new Vector3();
  const facing = (corner: number[], scale: number, out: Vector3) => {
    const at = (slot: number, point: Vector3) =>
      point.set(
        rest[corner[slot] * 3] + move[corner[slot] * 3] * scale,
        rest[corner[slot] * 3 + 1] + move[corner[slot] * 3 + 1] * scale,
        rest[corner[slot] * 3 + 2] + move[corner[slot] * 3 + 2] * scale,
      );
    at(0, first);
    at(1, second);
    at(2, third);
    return out.crossVectors(second.sub(first), third.sub(first));
  };

  let damped = 0;
  for (let pass = 0; pass < 14; pass += 1) {
    let touched = false;
    for (let triangle = 0; triangle < index.count; triangle += 3) {
      const corner = [index.getX(triangle), index.getX(triangle + 1), index.getX(triangle + 2)];
      if (!corner.some((vertex) => move[vertex * 3] || move[vertex * 3 + 1] || move[vertex * 3 + 2])) {
        continue;
      }
      facing(corner, 0, before);
      facing(corner, 1, after);
      if (before.lengthSq() < 1e-20 || after.lengthSq() < 1e-20) continue;
      // Facing the same way, and still a triangle rather than a sliver of one.
      if (after.dot(before) > 0 && after.length() / before.length() > 0.25) continue;
      for (const vertex of corner) {
        move[vertex * 3] *= 0.5;
        move[vertex * 3 + 1] *= 0.5;
        move[vertex * 3 + 2] *= 0.5;
      }
      touched = true;
      damped += 1;
    }
    if (!touched) break;
  }

  if (damped === 0) return 0;
  for (let vertex = 0; vertex < count; vertex += 1) {
    position.setXYZ(
      vertex,
      rest[vertex * 3] + move[vertex * 3],
      rest[vertex * 3 + 1] + move[vertex * 3 + 1],
      rest[vertex * 3 + 2] + move[vertex * 3 + 2],
    );
  }
  position.needsUpdate = true;
  geometry.computeVertexNormals();
  return damped;
}

/** The écorché body: the character's own geometry, read as fields, sculpted and repainted. */
export function buildEcorcheGeometry(rig: Skeleton = canonicalSkeleton): BufferGeometry {
  const source = buildBodyGeometry(rig).geometry;
  const geometry = REFINE_ARM ? refineArm(source, rig) : source;
  const rest = Float32Array.from(geometry.getAttribute('position').array as ArrayLike<number>);
  blendElbowWeights(geometry, rig);
  const weld = buildWeld(geometry);
  // Nothing to do at the junction any more. `buildAnatomicalBodyGeometry`
  // repairs both halves of it for every consumer — the head-to-neck binding and
  // the ledge the conversion transforms left at the nape — so the fields and the
  // relief below already sit on the corrected surface and read its corrected
  // weights. An Anatomy-only levelling pass used to run here; it was a second
  // correction for the same defect, applied to one mode only, and the shared fix
  // replaced it.
  shapeTorso(geometry, rig, weld);
  const map = buildMuscleMap(geometry, rig);
  sculptRelief(geometry, map, weld, rig);
  geometry.userData.unfolded = keepFacing(geometry, rest);
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
