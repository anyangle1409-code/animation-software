/**
 * Canonical bone naming for the studio.
 *
 * Every system in the app — IK, constraints, equipment sockets, muscles,
 * exercise definitions, export — refers to bones by these names. Imported
 * character rigs are mapped onto these names by the retargeting layer, so
 * animation data never depends on a particular character's own bone names.
 */

export const SIDES = ['l', 'r'] as const;
export type Side = (typeof SIDES)[number];

export const FINGERS = ['thumb', 'index', 'middle', 'ring', 'pinky'] as const;
export type Finger = (typeof FINGERS)[number];

export const FINGER_SEGMENTS = ['01', '02', '03'] as const;
export type FingerSegment = (typeof FINGER_SEGMENTS)[number];

/** Bones of the body proper — spine, limbs, head. */
export const CORE_BONES = [
  'root',
  'pelvis',
  'spine_01',
  'spine_02',
  'spine_03',
  'neck',
  'head',
  'clavicle_l',
  'scapula_l',
  'upperarm_l',
  'forearm_l',
  'hand_l',
  'clavicle_r',
  'scapula_r',
  'upperarm_r',
  'forearm_r',
  'hand_r',
  'thigh_l',
  'shin_l',
  'foot_l',
  'toe_l',
  'thigh_r',
  'shin_r',
  'foot_r',
  'toe_r',
] as const;

export type CoreBoneName = (typeof CORE_BONES)[number];
export type FingerBoneName = `${Finger}_${FingerSegment}_${Side}`;
export type BoneName = CoreBoneName | FingerBoneName;

export const FINGER_BONES: FingerBoneName[] = SIDES.flatMap((side) =>
  FINGERS.flatMap((finger) =>
    FINGER_SEGMENTS.map((segment): FingerBoneName => `${finger}_${segment}_${side}`),
  ),
);

export const ALL_BONES: BoneName[] = [...CORE_BONES, ...FINGER_BONES];

export const isFingerBone = (name: BoneName): name is FingerBoneName =>
  FINGERS.some((finger) => name.startsWith(`${finger}_`));

/**
 * The shoulder blades. Structural: they carry the arm from the clavicle but
 * nothing drives them yet, no imported character is expected to have them,
 * and views built from limb segments leave them out.
 */
export const isScapula = (name: BoneName): boolean => name === 'scapula_l' || name === 'scapula_r';

/** The side a bone belongs to, or null for centre-line bones. */
export function boneSide(name: BoneName): Side | null {
  if (name.endsWith('_l')) return 'l';
  if (name.endsWith('_r')) return 'r';
  return null;
}

export const otherSide = (side: Side): Side => (side === 'l' ? 'r' : 'l');

/** The same bone on the opposite side, or the bone itself if central. */
export function mirrorBoneName(name: BoneName): BoneName {
  const side = boneSide(name);
  if (!side) return name;
  return `${name.slice(0, -2)}_${otherSide(side)}` as BoneName;
}

/** Human-readable label, e.g. `upperarm_l` -> "Upper arm (L)". */
export function boneLabel(name: BoneName): string {
  const side = boneSide(name);
  const stem = side ? name.slice(0, -2) : name;
  const words = stem
    .split('_')
    .map((part) => (/^\d+$/.test(part) ? part.replace(/^0/, '') : part))
    .join(' ');
  const pretty = words.charAt(0).toUpperCase() + words.slice(1);
  return side ? `${pretty} (${side.toUpperCase()})` : pretty;
}
