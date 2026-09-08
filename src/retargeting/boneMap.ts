import type { BoneName } from '../rig/boneNames';
import { ALL_BONES, CORE_BONES } from '../rig/boneNames';

/**
 * A reusable mapping from the canonical rig onto a character's own bone names.
 *
 * Mappings are stored separately from exercises on purpose: a character is
 * mapped once, and every exercise in the library then retargets onto it
 * without any per-exercise work.
 */
export interface BoneMapping {
  id: string;
  label: string;
  /** Which rig this mapping was built for, e.g. "Meshy male v2". */
  sourceRig: string;
  /** Canonical bone name -> the character's bone name. */
  bones: Partial<Record<BoneName, string>>;
  /** Height of the character in metres, for scaling root motion. */
  characterHeight?: number;
  createdAt: string;
}

export const createMapping = (label: string, sourceRig: string): BoneMapping => ({
  id: `map_${label.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`,
  label,
  sourceRig,
  bones: {},
  createdAt: new Date().toISOString(),
});

/**
 * Naming conventions the studio recognises. Most rigged characters — Mixamo,
 * Meshy, Rigify, Unreal, VRM — use one of a small number of naming styles, so
 * a first-pass mapping can nearly always be guessed and then corrected by hand.
 */
const SYNONYMS: Partial<Record<BoneName, string[]>> = {
  root: ['root', 'armature', 'reference', 'hips_root'],
  pelvis: ['pelvis', 'hips', 'hip', 'mixamorighips', 'bip01pelvis', 'j_bip_c_hips'],
  spine_01: ['spine', 'spine1', 'spine_01', 'mixamorigspine', 'j_bip_c_spine', 'abdomen'],
  spine_02: ['spine2', 'spine_02', 'chest', 'mixamorigspine1', 'j_bip_c_chest'],
  spine_03: ['spine3', 'spine_03', 'upperchest', 'chest2', 'mixamorigspine2', 'j_bip_c_upperchest'],
  neck: ['neck', 'mixamorigneck', 'j_bip_c_neck'],
  head: ['head', 'mixamorighead', 'j_bip_c_head'],
  clavicle_l: ['leftshoulder', 'clavicle_l', 'shoulder_l', 'l_clavicle', 'mixamorigleftshoulder'],
  upperarm_l: ['leftarm', 'upperarm_l', 'arm_l', 'l_upperarm', 'mixamorigleftarm', 'upper_arm_l'],
  forearm_l: ['leftforearm', 'lowerarm_l', 'forearm_l', 'l_forearm', 'mixamorigleftforearm'],
  hand_l: ['lefthand', 'hand_l', 'l_hand', 'mixamoriglefthand'],
  clavicle_r: ['rightshoulder', 'clavicle_r', 'shoulder_r', 'r_clavicle', 'mixamorigrightshoulder'],
  upperarm_r: ['rightarm', 'upperarm_r', 'arm_r', 'r_upperarm', 'mixamorigrightarm', 'upper_arm_r'],
  forearm_r: ['rightforearm', 'lowerarm_r', 'forearm_r', 'r_forearm', 'mixamorigrightforearm'],
  hand_r: ['righthand', 'hand_r', 'r_hand', 'mixamorigrighthand'],
  thigh_l: ['leftupleg', 'thigh_l', 'upperleg_l', 'l_thigh', 'mixamorigleftupleg'],
  shin_l: ['leftleg', 'calf_l', 'shin_l', 'lowerleg_l', 'l_calf', 'mixamorigleftleg'],
  foot_l: ['leftfoot', 'foot_l', 'l_foot', 'mixamorigleftfoot'],
  toe_l: ['lefttoebase', 'ball_l', 'toe_l', 'l_toe', 'mixamoriglefttoebase'],
  thigh_r: ['rightupleg', 'thigh_r', 'upperleg_r', 'r_thigh', 'mixamorigrightupleg'],
  shin_r: ['rightleg', 'calf_r', 'shin_r', 'lowerleg_r', 'r_calf', 'mixamorigrightleg'],
  foot_r: ['rightfoot', 'foot_r', 'r_foot', 'mixamorigrightfoot'],
  toe_r: ['righttoebase', 'ball_r', 'toe_r', 'r_toe', 'mixamorigrighttoebase'],
};

const normalise = (name: string): string =>
  name.toLowerCase().replace(/[\s._:-]/g, '').replace(/^mixamorig/, 'mixamorig');

/**
 * Guess a mapping from a list of the character's bone names.
 *
 * Exact synonym matches first, then finger bones by pattern, then anything left
 * over by direct name equality. Whatever it cannot work out is left blank for
 * the user rather than mapped to something plausible-looking and wrong.
 */
export function guessMapping(characterBones: string[]): Partial<Record<BoneName, string>> {
  const bones: Partial<Record<BoneName, string>> = {};
  const byNormalised = new Map<string, string>();
  for (const name of characterBones) {
    const key = normalise(name);
    if (!byNormalised.has(key)) byNormalised.set(key, name);
  }
  const taken = new Set<string>();

  const claim = (canonical: BoneName, candidate: string | undefined) => {
    if (!candidate || taken.has(candidate)) return false;
    bones[canonical] = candidate;
    taken.add(candidate);
    return true;
  };

  for (const canonical of CORE_BONES) {
    const options = SYNONYMS[canonical] ?? [canonical];
    for (const option of options) {
      if (claim(canonical, byNormalised.get(normalise(option)))) break;
    }
  }

  for (const canonical of ALL_BONES) {
    if (bones[canonical]) continue;
    const match = matchFinger(canonical, characterBones, taken);
    if (match) claim(canonical, match);
  }

  return bones;
}

/** Finger bones vary wildly between rigs, so match on side, digit and index. */
function matchFinger(canonical: BoneName, candidates: string[], taken: Set<string>): string | null {
  const parts = /^(thumb|index|middle|ring|pinky)_0(\d)_(l|r)$/.exec(canonical);
  if (!parts) return null;
  const [, finger, segment, side] = parts;
  const alternates: Record<string, string[]> = {
    pinky: ['pinky', 'little'],
    thumb: ['thumb'],
    index: ['index'],
    middle: ['middle'],
    ring: ['ring'],
  };

  for (const candidate of candidates) {
    if (taken.has(candidate)) continue;
    const key = normalise(candidate);
    const namesFinger = alternates[finger].some((alias) => key.includes(alias));
    if (!namesFinger) continue;
    const sideMatches =
      key.includes(side === 'l' ? 'left' : 'right') ||
      new RegExp(`(^|[^a-z])${side}([^a-z]|$)`).test(key) ||
      key.endsWith(side);
    if (!sideMatches) continue;
    if (!key.includes(segment)) continue;
    return candidate;
  }
  return null;
}

export interface MappingReport {
  mapped: BoneName[];
  missing: BoneName[];
  /** Bones the studio needs before it can retarget at all. */
  missingRequired: BoneName[];
}

/** Bones without which a retarget is not worth attempting. */
export const REQUIRED_BONES: BoneName[] = [
  'pelvis',
  'spine_01',
  'spine_03',
  'neck',
  'head',
  'upperarm_l',
  'forearm_l',
  'hand_l',
  'upperarm_r',
  'forearm_r',
  'hand_r',
  'thigh_l',
  'shin_l',
  'foot_l',
  'thigh_r',
  'shin_r',
  'foot_r',
];

export function reportMapping(mapping: BoneMapping): MappingReport {
  const mapped = ALL_BONES.filter((bone) => Boolean(mapping.bones[bone]));
  const missing = ALL_BONES.filter((bone) => !mapping.bones[bone]);
  return {
    mapped,
    missing,
    missingRequired: REQUIRED_BONES.filter((bone) => !mapping.bones[bone]),
  };
}

export const isMappingUsable = (mapping: BoneMapping): boolean =>
  reportMapping(mapping).missingRequired.length === 0;
