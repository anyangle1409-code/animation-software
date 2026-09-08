import { Matrix4, Quaternion, Vector3 } from 'three';
import type { BoneName, Side } from '../rig/boneNames';
import { PoseEvaluation } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import type { Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import type { MuscleGroupId } from './groups';
import { probeDepth, skinProbe } from '../body/containment';
import type { SkinProbe } from '../body/containment';

/**
 * A muscle is defined by where it starts and where it ends, both given in bone
 * space. Because those two points ride their own bones, the muscle follows the
 * skeleton for free: bend the elbow and the biceps shortens and thickens, with
 * no separate rig to keep in sync.
 */
export interface MuscleDefinition {
  group: MuscleGroupId;
  origin: { bone: BoneName; offset: Vec3 };
  insertion: { bone: BoneName; offset: Vec3 };
  /** Radius at the belly, metres. */
  thickness: number;
  /** How much the belly thickens as the muscle shortens, 0 to 1. */
  bulge?: number;
  /**
   * How thin the belly is through the skin, 0 to 1. A sheet like the lats or
   * the abdominals is flattened against the body; the biceps is not.
   */
  flatten?: number;
  /** Widening across the body, for the same sheets. */
  spread?: number;
  /**
   * How much of the origin-to-insertion span the belly itself occupies. A real
   * muscle stops short of both attachments and finishes in tendon, and drawing
   * the belly all the way to the bone is what makes it cut the corner of a bent
   * joint and appear outside the skin.
   */
  taper?: number;
  /**
   * Which way the muscle faces, in the origin bone's own frame. Defaults to the
   * direction its origin already sits off the bone's axis — the biceps forward,
   * the triceps back, the lats out and behind — which is what makes the belly
   * lie along the body instead of spreading in whatever direction the maths
   * happened to pick.
   */
  outward?: Vec3;
}

const at = (bone: BoneName, x: number, y: number, z: number) => ({ bone, offset: vec3(x, y, z) });

/**
 * Left-side and centre-line muscles. The right side is mirrored, which for a
 * bone-local offset means negating x — the two bone frames are reflections of
 * one another.
 */
const LEFT_MUSCLES: MuscleDefinition[] = [
  // --- arm ---------------------------------------------------------------
  // Every belly is placed so that its outward face — the axis offset plus the
  // thickness, plus whatever the bulge adds at full contraction — stays inside
  // the skin the body profiles describe. `body/containment.ts` measures it, and
  // `muscles.test.ts` holds it there.
  {
    group: 'biceps',
    origin: at('upperarm_l', -0.004, 0.07, 0.014),
    insertion: at('forearm_l', -0.003, 0.022, 0.01),
    thickness: 0.03,
    bulge: 0.5,
    spread: 0.95,
  },
  {
    group: 'triceps',
    origin: at('upperarm_l', 0.003, 0.055, -0.018),
    insertion: at('forearm_l', 0.002, 0.018, -0.01),
    thickness: 0.031,
    bulge: 0.3,
  },
  {
    group: 'forearm_flexors',
    origin: at('forearm_l', -0.003, 0.035, 0.015),
    insertion: at('forearm_l', -0.002, 0.185, 0.005),
    thickness: 0.025,
    bulge: 0.2,
    spread: 1.1,
  },
  {
    group: 'forearm_extensors',
    origin: at('forearm_l', 0.004, 0.035, -0.015),
    insertion: at('forearm_l', 0.003, 0.185, -0.005),
    thickness: 0.023,
    bulge: 0.2,
    spread: 1.1,
  },

  // --- shoulder ----------------------------------------------------------
  // The three deltoid heads run from the shoulder girdle onto the humerus, so
  // they follow the girdle when it shrugs and the arm when it lifts.
  {
    group: 'deltoid_anterior',
    origin: at('clavicle_l', 0.01, 0.1, 0.022),
    insertion: at('upperarm_l', 0.006, 0.13, 0.024),
    thickness: 0.036,
    bulge: 0.3,
    flatten: 0.15,
  },
  {
    group: 'deltoid_medial',
    origin: at('clavicle_l', 0.016, 0.13, 0),
    insertion: at('upperarm_l', 0.026, 0.14, 0),
    thickness: 0.042,
    bulge: 0.3,
  },
  {
    group: 'deltoid_posterior',
    origin: at('clavicle_l', 0.008, 0.11, -0.024),
    insertion: at('upperarm_l', 0.006, 0.13, -0.026),
    thickness: 0.036,
    bulge: 0.3,
    flatten: 0.15,
  },

  // --- chest and back ----------------------------------------------------
  {
    group: 'pectoralis',
    origin: at('spine_03', -0.045, 0.04, 0.082),
    // The insertion sits at the head of the humerus rather than down its shaft:
    // with the arm overhead, a belly drawn to mid-humerus cuts straight across
    // the armpit and out through the skin.
    insertion: at('upperarm_l', 0.014, 0.028, 0.012),
    thickness: 0.032,
    bulge: 0.3,
    flatten: 0.6,
    spread: 1.6,
  },
  {
    group: 'latissimus',
    origin: at('spine_01', -0.055, 0.02, -0.06),
    insertion: at('upperarm_l', 0.014, 0.028, -0.014),
    thickness: 0.032,
    bulge: 0.25,
    flatten: 0.55,
    spread: 1.5,
  },
  {
    group: 'trapezius_upper',
    origin: at('neck', -0.03, 0.004, -0.026),
    insertion: at('clavicle_l', -0.006, 0.09, -0.012),
    thickness: 0.022,
    bulge: 0.25,
    flatten: 0.4,
    spread: 1.3,
  },
  {
    group: 'trapezius_mid',
    origin: at('spine_03', -0.035, 0.09, -0.075),
    insertion: at('clavicle_l', 0, 0.08, -0.02),
    thickness: 0.026,
    bulge: 0.2,
    flatten: 0.5,
    spread: 1.4,
  },
  {
    group: 'erector_lower',
    origin: at('pelvis', -0.03, 0.02, -0.082),
    insertion: at('spine_01', -0.028, 0.1, -0.078),
    thickness: 0.026,
    flatten: 0.25,
  },
  {
    group: 'erector_mid',
    origin: at('spine_01', -0.028, 0.02, -0.08),
    insertion: at('spine_02', -0.026, 0.1, -0.086),
    thickness: 0.024,
    flatten: 0.25,
  },
  {
    group: 'erector_upper',
    origin: at('spine_02', -0.026, 0.02, -0.088),
    insertion: at('spine_03', -0.026, 0.11, -0.092),
    thickness: 0.024,
    flatten: 0.25,
  },
  {
    group: 'obliques',
    origin: at('pelvis', -0.108, 0.02, 0.03),
    insertion: at('spine_02', -0.104, 0.08, 0.03),
    thickness: 0.032,
    flatten: 0.5,
    spread: 1.2,
  },

  // --- legs --------------------------------------------------------------
  {
    group: 'gluteus',
    origin: at('pelvis', -0.06, 0.01, -0.06),
    insertion: at('thigh_l', 0.025, 0.09, -0.04),
    thickness: 0.045,
    bulge: 0.3,
    flatten: 0.2,
    spread: 1.2,
  },
  {
    group: 'quadriceps',
    origin: at('thigh_l', 0, 0.07, 0.04),
    insertion: at('shin_l', 0, 0.03, 0.03),
    thickness: 0.045,
    bulge: 0.35,
    spread: 1.2,
  },
  {
    group: 'hamstrings',
    origin: at('thigh_l', 0, 0.06, -0.038),
    insertion: at('shin_l', 0, 0.03, -0.024),
    thickness: 0.038,
    bulge: 0.3,
  },
  {
    group: 'hip_adductors',
    origin: at('pelvis', -0.045, 0, 0.01),
    insertion: at('thigh_l', -0.048, 0.19, 0.008),
    thickness: 0.034,
    bulge: 0.2,
  },
  {
    group: 'hip_abductors',
    origin: at('pelvis', -0.125, 0.02, -0.01),
    insertion: at('thigh_l', 0.055, 0.14, -0.008),
    thickness: 0.032,
    bulge: 0.2,
  },
  {
    group: 'calves',
    origin: at('shin_l', 0, 0.07, -0.034),
    insertion: at('foot_l', 0, -0.006, -0.01),
    thickness: 0.03,
    bulge: 0.3,
    spread: 0.9,
  },
];

/** Muscles on the centre line, which are not mirrored. */
const CENTRE_MUSCLES: MuscleDefinition[] = [
  {
    group: 'rectus_abdominis',
    origin: at('pelvis', 0, 0.03, 0.075),
    insertion: at('spine_03', 0, 0.03, 0.085),
    thickness: 0.03,
    flatten: 0.55,
    spread: 1.5,
  },
];

const mirrorOffset = (offset: Vec3): Vec3 => vec3(-offset.x, offset.y, offset.z);
const mirrorBone = (bone: BoneName): BoneName =>
  bone.endsWith('_l') ? (`${bone.slice(0, -2)}_r` as BoneName) : bone;

function mirrorMuscle(muscle: MuscleDefinition): MuscleDefinition {
  return {
    ...muscle,
    ...(muscle.outward ? { outward: mirrorOffset(muscle.outward) } : {}),
    origin: { bone: mirrorBone(muscle.origin.bone), offset: mirrorOffset(muscle.origin.offset) },
    insertion: {
      bone: mirrorBone(muscle.insertion.bone),
      offset: mirrorOffset(muscle.insertion.offset),
    },
  };
}

export interface MuscleInstance extends MuscleDefinition {
  id: string;
  side: Side | null;
  /** Origin-to-insertion distance in the rest pose, for the bulge calculation. */
  restLength: number;
  /** Unit outward direction in the origin bone's frame. */
  outwardAxis: Vector3;
  /** Bones whose skin the belly is fitted against. */
  fitBones: ReadonlySet<string>;
}

function build(): MuscleInstance[] {
  const evaluation = new PoseEvaluation(canonicalSkeleton).apply(restPose());
  const origin = new Vector3();
  const insertion = new Vector3();

  const withRest = (muscle: MuscleDefinition, side: Side | null): MuscleInstance => {
    evaluation.localToWorld(muscle.origin.bone, muscle.origin.offset, origin);
    evaluation.localToWorld(muscle.insertion.bone, muscle.insertion.offset, insertion);
    const authored = muscle.outward ?? vec3(muscle.origin.offset.x, 0, muscle.origin.offset.z);
    const outwardAxis = new Vector3(authored.x, authored.y, authored.z);
    if (outwardAxis.lengthSq() < 1e-8) outwardAxis.set(0, 0, 1);
    const bones = new Set<string>([muscle.origin.bone, muscle.insertion.bone]);
    for (const bone of [muscle.origin.bone, muscle.insertion.bone]) {
      const parent = canonicalSkeleton.bone(bone).parent;
      if (parent && parent !== 'root') bones.add(parent);
    }
    return {
      ...muscle,
      id: side ? `${muscle.group}_${side}` : muscle.group,
      side,
      restLength: Math.max(0.02, origin.distanceTo(insertion)),
      outwardAxis: outwardAxis.normalize(),
      fitBones: bones,
    };
  };

  return [
    ...LEFT_MUSCLES.map((muscle) => withRest(muscle, 'l')),
    ...LEFT_MUSCLES.map((muscle) => withRest(mirrorMuscle(muscle), 'r')),
    ...CENTRE_MUSCLES.map((muscle) => withRest(muscle, null)),
  ];
}

export const MUSCLES: MuscleInstance[] = build();

export interface MuscleTransform {
  position: Vector3;
  quaternion: Quaternion;
  /** Radius, length and depth scale for the belly. */
  scale: Vector3;
  /** Current length divided by rest length. */
  stretch: number;
}

const originScratch = new Vector3();
const insertionScratch = new Vector3();
const directionScratch = new Vector3();
const outwardScratch = new Vector3();
const widthScratch = new Vector3();
const basisScratch = new Matrix4();
const fitScratch = new Vector3();
let probe: SkinProbe | undefined;

/**
 * Points on the belly's surface used to fit it under the skin: rings around its
 * widest section and either side of it, towards the tendons, which is where a
 * sheet muscle curves off the body.
 */
const BELLY_EDGES: [number, number, number][] = [0, -0.35, 0.35, -0.65, 0.65, -0.88, 0.88].flatMap((y) => {
  const radius = Math.sqrt(Math.max(0, 1 - y * y));
  const steps = Math.abs(y) < 0.6 ? 12 : 8;
  return Array.from({ length: steps }, (_, index): [number, number, number] => {
    const angle = (index / steps) * Math.PI * 2;
    return [radius * Math.cos(angle), y, radius * Math.sin(angle)];
  });
});

/**
 * Place one muscle for the currently evaluated pose. A shortened muscle thickens
 * and a stretched one thins, which is what makes the overlay read as muscle
 * rather than as coloured tubing.
 *
 * The belly is built on an explicit frame — length along the muscle, width
 * across the body, depth through the skin — so a sheet muscle lies flat against
 * the body instead of spreading in an arbitrary direction and pushing out
 * through the surface.
 */
export function resolveMuscle(
  evaluation: PoseEvaluation,
  muscle: MuscleInstance,
  out: MuscleTransform,
): MuscleTransform {
  evaluation.localToWorld(muscle.origin.bone, muscle.origin.offset, originScratch);
  evaluation.localToWorld(muscle.insertion.bone, muscle.insertion.offset, insertionScratch);
  directionScratch.subVectors(insertionScratch, originScratch);

  const length = Math.max(0.01, directionScratch.length());
  const stretch = length / muscle.restLength;
  const bulge = 1 + (muscle.bulge ?? 0.25) * Math.max(-0.5, Math.min(0.9, 1 / stretch - 1));

  out.position.copy(originScratch).addScaledVector(directionScratch, 0.5);
  directionScratch.divideScalar(length);

  // Outward, carried from the origin bone into the world and made square to the
  // muscle's own length.
  outwardScratch.copy(muscle.outwardAxis).applyQuaternion(evaluation.quaternion(muscle.origin.bone));
  outwardScratch.addScaledVector(directionScratch, -outwardScratch.dot(directionScratch));
  if (outwardScratch.lengthSq() < 1e-8) outwardScratch.set(0, 0, 1);
  outwardScratch.normalize();
  widthScratch.crossVectors(directionScratch, outwardScratch).normalize();

  basisScratch.makeBasis(widthScratch, directionScratch, outwardScratch);
  out.quaternion.setFromRotationMatrix(basisScratch);

  // The belly is drawn as a unit sphere: width across the body, half-length
  // along it, depth through the skin.
  const radius = muscle.thickness * bulge;
  const width = radius * (muscle.spread ?? 1);
  const depth = radius * (1 - (muscle.flatten ?? 0));

  // Fit the belly to the body it sits under. However carefully a muscle is
  // authored, a pose can bring the skin closer than the belly is wide — a
  // raised arm pulls the pectoral's line across the armpit — and a belly poking
  // through the surface is the one thing the overlay must never do. So the
  // sheet is measured at its own edges and pulled in until it fits.
  out.scale.set(width, (length / 2) * (muscle.taper ?? 0.86), depth);
  probe = skinProbe(evaluation, muscle.fitBones, canonicalSkeleton, probe);
  for (let pass = 0; pass < 3; pass += 1) {
    let overshoot = 0;
    for (const [u, y, v] of BELLY_EDGES) {
      fitScratch
        .set(u * out.scale.x, y * out.scale.y, v * out.scale.z)
        .applyQuaternion(out.quaternion)
        .add(out.position);
      overshoot = Math.max(overshoot, probeDepth(probe, fitScratch).depth);
    }
    // Aim a couple of millimetres clear rather than exactly flush, so the
    // directions between the samples stay inside too.
    if (overshoot <= -0.002) break;
    const shrink = Math.max(
      0.35,
      1 - (overshoot + 0.002) / Math.max(0.01, (out.scale.x + out.scale.z) / 2),
    );
    out.scale.x = Math.max(0.008, out.scale.x * shrink);
    out.scale.z = Math.max(0.006, out.scale.z * shrink);
  }

  out.stretch = stretch;
  return out;
}

export const createMuscleTransform = (): MuscleTransform => ({
  position: new Vector3(),
  quaternion: new Quaternion(),
  scale: new Vector3(1, 1, 1),
  stretch: 1,
});
