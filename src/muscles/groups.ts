import type { BoneName } from '../rig/boneNames';

/**
 * Major muscle groups the studio can show and highlight. Deliberately at the
 * level a trainer talks about rather than a dissection: each entry is a group
 * a person would recognise on a workout card.
 */
export const MUSCLE_GROUP_IDS = [
  'pectoralis',
  'deltoid_anterior',
  'deltoid_medial',
  'deltoid_posterior',
  'biceps',
  'triceps',
  'forearm_flexors',
  'forearm_extensors',
  'trapezius_upper',
  'trapezius_mid',
  'latissimus',
  'erector_upper',
  'erector_mid',
  'erector_lower',
  'rectus_abdominis',
  'obliques',
  'gluteus',
  'quadriceps',
  'hamstrings',
  'calves',
  'hip_adductors',
  'hip_abductors',
] as const;

export type MuscleGroupId = (typeof MUSCLE_GROUP_IDS)[number];

export interface MuscleGroupMeta {
  id: MuscleGroupId;
  label: string;
  region: 'chest' | 'shoulders' | 'arms' | 'back' | 'core' | 'legs';
  /** True when the group exists on both sides of the body. */
  paired: boolean;
  /** Bones whose motion the group produces — used for the activation readout. */
  actsOn: BoneName[];
}

const meta = (
  id: MuscleGroupId,
  label: string,
  region: MuscleGroupMeta['region'],
  paired: boolean,
  actsOn: BoneName[],
): MuscleGroupMeta => ({ id, label, region, paired, actsOn });

export const MUSCLE_GROUPS: Record<MuscleGroupId, MuscleGroupMeta> = {
  pectoralis: meta('pectoralis', 'Pectorals', 'chest', true, ['upperarm_l', 'upperarm_r']),
  deltoid_anterior: meta('deltoid_anterior', 'Front delts', 'shoulders', true, ['upperarm_l', 'upperarm_r']),
  deltoid_medial: meta('deltoid_medial', 'Side delts', 'shoulders', true, ['upperarm_l', 'upperarm_r']),
  deltoid_posterior: meta('deltoid_posterior', 'Rear delts', 'shoulders', true, ['upperarm_l', 'upperarm_r']),
  biceps: meta('biceps', 'Biceps', 'arms', true, ['forearm_l', 'forearm_r']),
  triceps: meta('triceps', 'Triceps', 'arms', true, ['forearm_l', 'forearm_r']),
  forearm_flexors: meta('forearm_flexors', 'Forearm flexors', 'arms', true, ['hand_l', 'hand_r']),
  forearm_extensors: meta('forearm_extensors', 'Forearm extensors', 'arms', true, ['hand_l', 'hand_r']),
  trapezius_upper: meta('trapezius_upper', 'Upper traps', 'back', true, ['clavicle_l', 'clavicle_r']),
  trapezius_mid: meta('trapezius_mid', 'Mid traps', 'back', true, ['clavicle_l', 'clavicle_r']),
  latissimus: meta('latissimus', 'Lats', 'back', true, ['upperarm_l', 'upperarm_r']),
  erector_upper: meta('erector_upper', 'Upper back', 'back', true, ['spine_03']),
  erector_mid: meta('erector_mid', 'Mid back', 'back', true, ['spine_02']),
  erector_lower: meta('erector_lower', 'Lower back', 'back', true, ['spine_01']),
  rectus_abdominis: meta('rectus_abdominis', 'Abdominals', 'core', false, ['spine_01', 'spine_02']),
  obliques: meta('obliques', 'Obliques', 'core', true, ['spine_01', 'spine_02']),
  gluteus: meta('gluteus', 'Glutes', 'legs', true, ['thigh_l', 'thigh_r']),
  quadriceps: meta('quadriceps', 'Quadriceps', 'legs', true, ['shin_l', 'shin_r']),
  hamstrings: meta('hamstrings', 'Hamstrings', 'legs', true, ['shin_l', 'shin_r']),
  calves: meta('calves', 'Calves', 'legs', true, ['foot_l', 'foot_r']),
  hip_adductors: meta('hip_adductors', 'Adductors', 'legs', true, ['thigh_l', 'thigh_r']),
  hip_abductors: meta('hip_abductors', 'Abductors', 'legs', true, ['thigh_l', 'thigh_r']),
};

export const isMuscleGroupId = (value: string): value is MuscleGroupId =>
  (MUSCLE_GROUP_IDS as readonly string[]).includes(value);
