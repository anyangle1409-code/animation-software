import { Quaternion, Vector3 } from 'three';
import type { BoneName, Side } from '../rig/boneNames';
import { PoseEvaluation } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import { restPose } from '../rig/pose';
import type { Vec3 } from '../rig/types';
import { vec3 } from '../rig/types';
import type { MuscleGroupId } from './groups';

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
  /** Flattening across the muscle's own X, for sheets like the lats and pecs. */
  flatten?: number;
  /** Widening across the muscle's own Z. */
  spread?: number;
}

const at = (bone: BoneName, x: number, y: number, z: number) => ({ bone, offset: vec3(x, y, z) });

/**
 * Left-side and centre-line muscles. The right side is mirrored, which for a
 * bone-local offset means negating x — the two bone frames are reflections of
 * one another.
 */
const LEFT_MUSCLES: MuscleDefinition[] = [
  // --- arm ---------------------------------------------------------------
  {
    group: 'biceps',
    origin: at('upperarm_l', -0.005, 0.07, 0.03),
    insertion: at('forearm_l', -0.004, 0.055, 0.026),
    thickness: 0.041,
    bulge: 0.55,
  },
  {
    group: 'triceps',
    origin: at('upperarm_l', 0.004, 0.05, -0.036),
    insertion: at('forearm_l', 0.002, 0.04, -0.03),
    thickness: 0.044,
    bulge: 0.35,
  },
  {
    group: 'forearm_flexors',
    origin: at('forearm_l', -0.004, 0.03, 0.03),
    insertion: at('forearm_l', -0.002, 0.2, 0.012),
    thickness: 0.031,
    bulge: 0.2,
  },
  {
    group: 'forearm_extensors',
    origin: at('forearm_l', 0.006, 0.03, -0.03),
    insertion: at('forearm_l', 0.003, 0.2, -0.012),
    thickness: 0.029,
    bulge: 0.2,
  },

  // --- shoulder ----------------------------------------------------------
  {
    group: 'deltoid_anterior',
    origin: at('clavicle_l', 0.018, 0.1, 0.032),
    insertion: at('upperarm_l', 0.012, 0.15, 0.03),
    thickness: 0.036,
    bulge: 0.3,
  },
  {
    group: 'deltoid_medial',
    origin: at('clavicle_l', 0.03, 0.135, 0),
    insertion: at('upperarm_l', 0.042, 0.15, 0),
    thickness: 0.038,
    bulge: 0.3,
  },
  {
    group: 'deltoid_posterior',
    origin: at('clavicle_l', 0.014, 0.115, -0.035),
    insertion: at('upperarm_l', 0.012, 0.15, -0.032),
    thickness: 0.034,
    bulge: 0.3,
  },

  // --- chest and back ----------------------------------------------------
  {
    group: 'pectoralis',
    origin: at('spine_03', -0.055, 0.045, 0.098),
    insertion: at('upperarm_l', 0.018, 0.055, 0.03),
    thickness: 0.05,
    bulge: 0.35,
    flatten: 0.55,
    spread: 1.5,
  },
  {
    group: 'latissimus',
    origin: at('spine_01', -0.062, 0.015, -0.082),
    insertion: at('upperarm_l', 0.016, 0.07, -0.022),
    thickness: 0.05,
    bulge: 0.3,
    flatten: 0.5,
    spread: 1.4,
  },
  {
    group: 'trapezius_upper',
    origin: at('neck', -0.028, 0.02, -0.03),
    insertion: at('clavicle_l', 0.012, 0.105, -0.012),
    thickness: 0.03,
    bulge: 0.25,
    spread: 1.3,
  },
  {
    group: 'trapezius_mid',
    origin: at('spine_03', -0.03, 0.1, -0.072),
    insertion: at('clavicle_l', 0, 0.085, -0.024),
    thickness: 0.033,
    bulge: 0.2,
    spread: 1.4,
  },
  {
    group: 'erector_lower',
    origin: at('pelvis', -0.032, 0.015, -0.088),
    insertion: at('spine_01', -0.03, 0.105, -0.082),
    thickness: 0.027,
  },
  {
    group: 'erector_mid',
    origin: at('spine_01', -0.03, 0.02, -0.082),
    insertion: at('spine_02', -0.028, 0.105, -0.084),
    thickness: 0.026,
  },
  {
    group: 'erector_upper',
    origin: at('spine_02', -0.028, 0.02, -0.084),
    insertion: at('spine_03', -0.028, 0.115, -0.078),
    thickness: 0.025,
  },
  {
    group: 'obliques',
    origin: at('pelvis', -0.082, 0.01, 0.03),
    insertion: at('spine_02', -0.078, 0.085, 0.025),
    thickness: 0.038,
    flatten: 0.5,
    spread: 1.2,
  },

  // --- legs --------------------------------------------------------------
  {
    group: 'gluteus',
    origin: at('pelvis', -0.072, 0.005, -0.062),
    insertion: at('thigh_l', 0.03, 0.1, -0.045),
    thickness: 0.062,
    bulge: 0.3,
    spread: 1.2,
  },
  {
    group: 'quadriceps',
    origin: at('thigh_l', 0, 0.06, 0.052),
    insertion: at('shin_l', 0, 0.035, 0.042),
    thickness: 0.064,
    bulge: 0.4,
    spread: 1.15,
  },
  {
    group: 'hamstrings',
    origin: at('thigh_l', 0, 0.045, -0.052),
    insertion: at('shin_l', 0, 0.055, -0.04),
    thickness: 0.054,
    bulge: 0.35,
  },
  {
    group: 'hip_adductors',
    origin: at('pelvis', -0.035, 0, 0),
    insertion: at('thigh_l', -0.038, 0.2, 0),
    thickness: 0.04,
    bulge: 0.25,
  },
  {
    group: 'hip_abductors',
    origin: at('pelvis', -0.098, 0.02, 0),
    insertion: at('thigh_l', 0.048, 0.13, 0),
    thickness: 0.034,
    bulge: 0.25,
  },
  {
    group: 'calves',
    origin: at('shin_l', 0, 0.05, -0.046),
    insertion: at('foot_l', 0, -0.028, -0.03),
    thickness: 0.05,
    bulge: 0.35,
  },
];

/** Muscles on the centre line, which are not mirrored. */
const CENTRE_MUSCLES: MuscleDefinition[] = [
  {
    group: 'rectus_abdominis',
    origin: at('pelvis', 0, 0.02, 0.088),
    insertion: at('spine_03', 0, 0.05, 0.098),
    thickness: 0.048,
    flatten: 0.45,
    spread: 1.5,
  },
];

const mirrorOffset = (offset: Vec3): Vec3 => vec3(-offset.x, offset.y, offset.z);
const mirrorBone = (bone: BoneName): BoneName =>
  bone.endsWith('_l') ? (`${bone.slice(0, -2)}_r` as BoneName) : bone;

function mirrorMuscle(muscle: MuscleDefinition): MuscleDefinition {
  return {
    ...muscle,
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
}

function build(): MuscleInstance[] {
  const evaluation = new PoseEvaluation(canonicalSkeleton).apply(restPose());
  const origin = new Vector3();
  const insertion = new Vector3();

  const withRest = (muscle: MuscleDefinition, side: Side | null): MuscleInstance => {
    evaluation.localToWorld(muscle.origin.bone, muscle.origin.offset, origin);
    evaluation.localToWorld(muscle.insertion.bone, muscle.insertion.offset, insertion);
    return {
      ...muscle,
      id: side ? `${muscle.group}_${side}` : muscle.group,
      side,
      restLength: Math.max(0.02, origin.distanceTo(insertion)),
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

const Y_AXIS = new Vector3(0, 1, 0);
const originScratch = new Vector3();
const insertionScratch = new Vector3();
const directionScratch = new Vector3();

/**
 * Place one muscle for the currently evaluated pose. A shortened muscle
 * thickens and a stretched one thins, which is what makes the overlay read as
 * muscle rather than as coloured tubing.
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
  out.quaternion.setFromUnitVectors(Y_AXIS, directionScratch.divideScalar(length));
  // The belly is drawn as a unit sphere, so the Y scale is the half-length.
  out.scale.set(
    muscle.thickness * bulge * (1 - (muscle.flatten ?? 0)),
    length / 2,
    muscle.thickness * bulge * (muscle.spread ?? 1),
  );
  out.stretch = stretch;
  return out;
}

export const createMuscleTransform = (): MuscleTransform => ({
  position: new Vector3(),
  quaternion: new Quaternion(),
  scale: new Vector3(1, 1, 1),
  stretch: 1,
});
