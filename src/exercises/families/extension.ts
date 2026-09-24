import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { EquipmentInstance } from '../../equipment/types';
import type { TechniqueRule } from '../../constraints/types';
import type { Vec3 } from '../../rig/types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralRule, mirrorPosition } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, heelDown, plantedStance } from '../stance';
import { hingeRoot } from './hinge';
import { FOOT_L } from './row';

/**
 * The elbow-extension family: the triceps.
 *
 * The sixth family, and the curl turned inside out. A curl flexes the elbow
 * against a load hanging from it; an extension straightens the elbow against a
 * load that wants to fold it. The reference variant does it overhead, which is
 * what makes it a family rather than a curl with the sign changed: with the
 * upper arm pointing at the ceiling, the forearm folds *behind the head*, and
 * the triceps' long head, which crosses the shoulder, is stretched as far as it
 * goes.
 *
 * ## What it asks that nothing before it did
 *
 * The load travels past the head. Every other exercise keeps its equipment in
 * front of the body or beside it; this one lowers two dumbbells into the space
 * behind the skull and the neck, so the clearance gate measuring the head
 * (`spine006` on the production character) is what decides the range, not the
 * joint limit.
 *
 * The upper arm is the thing that has to stay still, as in the curl: the elbow
 * points up and in, and the shoulder does not help by swinging the arm forward
 * as the weight comes up.
 *
 * ## The pushdown: the first cable
 *
 * The same elbow, turned the other way up: the upper arms hang at the sides,
 * and the forearms push a bar down against a cable from a high pulley. What is
 * new is the equipment. The bar is held in both hands (`hands`, the first
 * exercise to use it), and the cable is an item of its own that runs from the
 * tower's pulley to the bar's clip and stretches as the bar travels
 * (`attachment.mode: 'cable'`). The load does not change the motion, so
 * nothing in the solve knows the cable is there; it is drawn, exported and
 * measured against the body like any other item.
 *
 * A rigid bar needs hands that stay the same distance apart through the whole
 * repetition. They do when the upper arms hang with no abduction at all: the
 * elbow then bends in a plane parallel to the body's midline, and the hands
 * travel straight up and down it, 40 cm apart. Any abduction and they would
 * swing in or out as the elbow bends.
 *
 * The lifter leans a little over the bar, as one does at a cable stack, so the
 * pushdown stands in the hinge's pinned stance (`FOOT_L`) for the same reason
 * the row does: an opening frame that is not upright cannot supply the feet.
 */

export interface ExtensionVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Overhead with dumbbells, or pushing a bar down on a cable. */
  position?: ExtensionPosition;
  /** Load per hand, kilograms. Dumbbells only. */
  mass?: number;
  /** Elbow flexion at lockout and at the stretch, degrees. */
  elbow?: { start: number; peak: number };
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

export type ExtensionPosition = 'overhead' | 'pushdown';

/** Nearly locked out overhead, down to the forearm folded behind the head. */
const ELBOW = { start: 8, peak: 120 };

/** The upper arm points up at the ceiling and stays there. */
const UPPER_ARM = { flexion: 172, abduction: 5 };

/**
 * The pushdown. Locked out with the bar in front of the thighs, up to the
 * forearms just above parallel; the upper arms hang at the sides with no
 * abduction (see the header), 4° back from the trunk so that, with the trunk
 * leaning 12°, the elbows sit just forward of the ribs. Palms down on the bar:
 * −80° is near the end of the forearm's 85°, which turns the grip axis to
 * within 3° of the bar's.
 */
const PUSHDOWN = {
  elbow: { start: 6, peak: 100 },
  upperArm: { flexion: 20, abduction: 0 },
  pronation: -80,
  posture: { pitch: 12, pelvis: { y: 0.93, z: -0.03 } },
  /** Where the tower stands: its pulley 14 cm nearer the lifter than this. */
  tower: vec3(0, 0, 0.62),
};

const BRACED = {
  pelvis: { x: 2 },
  spine_01: { x: 2 },
  spine_02: { x: -1 },
  spine_03: { x: -1 },
  neck: { x: 4 },
};

/**
 * Leaning a little over the bar. The whole body pitches 12° from the ankles
 * (`PUSHDOWN.posture`); the spine stays long and the eyes come back to level.
 */
const LEANING = {
  spine_01: { x: 0 },
  spine_02: { x: 0 },
  spine_03: { x: 1 },
  neck: { x: -8 },
  head: { x: -4 },
};

/**
 * A cable tower in front of the lifter, a straight bar in both hands, and the
 * cable between the tower's high pulley and the bar's clip.
 */
function cableStation(): EquipmentInstance[] {
  const still = { position: vec3(0, 0, 0), rotation: vec3(0, 0, 0), visible: true };
  return [
    {
      id: 'tower',
      kind: 'cable_tower',
      label: 'Cable tower',
      mass: 0,
      ...still,
      position: PUSHDOWN.tower,
      attachment: { mode: 'static' },
    },
    {
      id: 'bar',
      kind: 'cable_bar',
      label: 'Straight bar',
      mass: 2,
      ...still,
      attachment: { mode: 'hands', leftSocket: 'grip_l', rightSocket: 'grip_r' },
    },
    {
      id: 'cable',
      kind: 'cable',
      label: 'Cable',
      mass: 0,
      ...still,
      attachment: {
        mode: 'cable',
        from: { equipment: 'tower', socket: 'pulley' },
        to: { equipment: 'bar', socket: 'clip' },
      },
    },
  ];
}

function pushdownTechnique(stance: TechniqueRule[]): TechniqueRule[] {
  return [
    ...stance,
    ...heelDown(),
    {
      kind: 'segmentAngle',
      id: 'torso_lean',
      label: 'Torso holds a slight lean — not folding over the bar',
      bone: 'spine_02',
      reference: 'vertical',
      max: 20,
      severity: 'error',
    },
    {
      kind: 'jointAngle',
      id: 'neutral_spine',
      label: 'Lower back stays neutral, not rounded over the bar',
      bone: 'spine_01',
      axis: 'x',
      min: -4,
      max: 10,
      severity: 'error',
    },
    // The upper arm is the pivot, pinned at the side; if it swings, the
    // shoulder and the lats are pushing the bar.
    ...bilateralRule({
      kind: 'segmentAngle',
      id: 'elbow_pinned_l',
      label: 'Left elbow stays at the side',
      bone: 'upperarm_l',
      reference: 'vertical',
      max: 15,
      severity: 'error',
    }),
    {
      kind: 'distance',
      id: 'elbows_in',
      label: 'Elbows stay in, not flared out to the sides',
      from: { bone: 'forearm_l' },
      to: { bone: 'forearm_r' },
      axis: 'x',
      max: 0.5,
    },
    ...bilateralRule({
      kind: 'jointAngle',
      id: 'lockout_l',
      label: 'Left elbow straightens fully at the bottom',
      bone: 'forearm_l',
      axis: 'x',
      max: 15,
      phases: ['lockout'],
      severity: 'error',
    }),
    ...bilateralRule({
      kind: 'jointAngle',
      id: 'full_range_l',
      label: 'Left forearm comes up to parallel',
      bone: 'forearm_l',
      axis: 'x',
      min: 90,
      phases: ['stretch'],
      severity: 'error',
    }),
    ...bilateralRule({
      kind: 'jointAngle',
      id: 'grip_held_l',
      label: 'Left palm stays facing down on the bar',
      bone: 'forearm_l',
      axis: 'y',
      min: -88,
      max: -65,
    }),
    ...bilateralRule({
      kind: 'jointAngle',
      id: 'wrist_neutral_l',
      label: 'Left wrist stays neutral',
      bone: 'hand_l',
      axis: 'z',
      min: -12,
      max: 15,
    }),
    evenSides({
      id: 'bar_level',
      label: 'The bar stays level',
      point: { bone: 'hand_l', along: 1 },
      tolerance: 0.03,
    }),
  ];
}

const PUSHDOWN_ERRORS: CommonError[] = [
  {
    id: 'elbow_drift',
    label: 'Elbows drifting forward',
    description: 'The upper arms swing forward as the bar rises, so the shoulders and lats take over the push.',
    ruleId: 'elbow_pinned_l',
    correction: 'Keep the elbows at the ribs; only the forearms move.',
  },
  {
    id: 'elbow_flare',
    label: 'Flaring the elbows',
    description: 'The elbows wing out to the sides and the push turns into a press.',
    ruleId: 'elbows_in',
    correction: 'Keep the elbows tucked in by the sides.',
  },
  {
    id: 'folding_over',
    label: 'Folding over the bar',
    description: 'The trunk bends forward to push the bar down with bodyweight.',
    ruleId: 'torso_lean',
    correction: 'Hold a slight lean and let the triceps move the bar.',
  },
  {
    id: 'soft_lockout',
    label: 'Stopping short of lockout',
    description: 'The elbows never straighten at the bottom, so the triceps never fully contracts.',
    ruleId: 'lockout_l',
    correction: 'Push until the arms are straight and pause there.',
  },
];

export function extensionFamily(variant: ExtensionVariant): ExerciseDefinition {
  const pushdown = variant.position === 'pushdown';
  const elbow = variant.elbow ?? (pushdown ? PUSHDOWN.elbow : ELBOW);
  const upperArm = pushdown ? PUSHDOWN.upperArm : UPPER_ARM;
  const twist = pushdown ? PUSHDOWN.pronation : 2;
  const planted = pushdown
    ? plantedStance({ width: 0.3, toeOut: 5, tolerance: 0.015, kneePole: vec3(-0.04, 0.5, 1.5) })
    : plantedStance();
  const stance = pushdown
    ? {
        ...planted,
        // Pinned to the hinge's standing feet, as the row's are; see the header.
        locks: planted.locks.map((lock) => {
          const side = (vector: Vec3) => (lock.id.endsWith('_l') ? { ...vector } : mirrorPosition(vector));
          return {
            ...lock,
            position: side(FOOT_L.position),
            aim: { direction: side(FOOT_L.aim.direction), forward: side(FOOT_L.aim.forward) },
          };
        }),
      }
    : planted;
  const arms = (flexion: number) =>
    bilateralJoints({
      upperarm_l: { x: upperArm.flexion, z: -upperArm.abduction },
      forearm_l: { x: flexion, y: twist },
      hand_l: { z: 0 },
    });
  const trunk = pushdown ? LEANING : BRACED;
  const root = pushdown ? hingeRoot(PUSHDOWN.posture.pitch, PUSHDOWN.posture.pelvis) : undefined;
  const placement = root
    ? { position: { y: root.y, z: root.z }, rotation: { x: PUSHDOWN.posture.pitch } }
    : undefined;

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'arms',
    description: variant.description,

    equipment: pushdown
      ? { required: ['cable_tower', 'cable_bar', 'cable'], instances: cableStation() }
      : { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 8) },

    startPose: {
      label: 'Locked out',
      joints: { ...trunk, ...arms(elbow.start) },
      ...(placement ? { root: placement } : {}),
    },
    peakPose: {
      label: pushdown ? 'Bar up' : 'Behind the head',
      joints: { ...trunk, ...arms(elbow.peak) },
      ...(placement ? { root: placement } : {}),
    },

    jointTargets: [
      ...bilateralJointTarget({
        bone: 'forearm_l', axis: 'x', start: elbow.start, peak: elbow.peak, role: 'prime',
        range: { min: 0, max: 135 },
      }),
      ...bilateralJointTarget({
        bone: 'upperarm_l', axis: 'x', start: upperArm.flexion, peak: upperArm.flexion, role: 'stabilise',
      }),
    ],

    phases: pushdown
      ? [
          { id: 'eccentric', label: 'Let the bar rise', to: 'peak', easing: 'lift', contraction: 'eccentric' },
          { id: 'stretch', label: 'Top', to: 'peak', easing: 'hold', contraction: 'isometric' },
          { id: 'concentric', label: 'Push down', to: 'start', easing: 'lift', contraction: 'concentric' },
          { id: 'lockout', label: 'Lockout', to: 'start', easing: 'hold', contraction: 'isometric' },
        ]
      : [
          { id: 'eccentric', label: 'Lower behind the head', to: 'peak', easing: 'lift', contraction: 'eccentric' },
          { id: 'stretch', label: 'Stretch', to: 'peak', easing: 'hold', contraction: 'isometric' },
          { id: 'concentric', label: 'Extend', to: 'start', easing: 'lift', contraction: 'concentric' },
          { id: 'lockout', label: 'Lockout', to: 'start', easing: 'hold', contraction: 'isometric' },
        ],

    tempo: variant.tempo ?? (pushdown
      ? { eccentric: 1.8, pauseStretched: 0.3, concentric: 1.2, pauseContracted: 0.6 }
      : { eccentric: 2.2, pauseStretched: 0.4, concentric: 1.4, pauseContracted: 0.5 }),

    // Overhead, palms facing, which keeps the elbows pointing forward rather
    // than flared. On the bar, palms down.
    hands: pushdown
      ? { grip: 'bar', orientation: 'pronated', closure: 0.85, width: 0.4 }
      : { grip: 'dumbbell', orientation: 'neutral', closure: 0.85 },
    feet: stance.feet,
    locks: stance.locks,

    muscles: {
      primary: ['triceps'],
      secondary: pushdown ? ['forearm_flexors'] : ['forearm_extensors'],
      stabilisers: pushdown
        ? ['latissimus', 'deltoid_posterior', 'rectus_abdominis', 'obliques', 'erector_lower']
        : ['deltoid_anterior', 'trapezius_upper', 'rectus_abdominis', 'obliques', 'erector_lower'],
      ...variant.muscles,
    },

    technique: pushdown ? pushdownTechnique(stance.technique) : [
      ...stance.technique,
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays upright — no leaning back under the weight',
        bone: 'spine_02',
        reference: 'vertical',
        max: 8,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'no_arch',
        label: 'Lower back does not arch to get the arms overhead',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 10,
        severity: 'error',
      },
      // The upper arm is the pivot; if it swings forward the shoulder is doing
      // the lifting.
      ...bilateralRule({
        kind: 'segmentAngle',
        id: 'upper_arm_vertical_l',
        label: 'Left upper arm stays pointing at the ceiling',
        bone: 'upperarm_l',
        reference: 'vertical',
        max: 20,
        severity: 'error',
      }),
      {
        kind: 'distance',
        id: 'elbows_in',
        label: 'Elbows stay in, not flared out to the sides',
        from: { bone: 'forearm_l' },
        to: { bone: 'forearm_r' },
        axis: 'x',
        max: 0.5,
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'lockout_l',
        label: 'Left elbow straightens fully at the top',
        bone: 'forearm_l',
        axis: 'x',
        max: 15,
        phases: ['lockout'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'full_stretch_l',
        label: 'Left elbow bends past 100° behind the head',
        bone: 'forearm_l',
        axis: 'x',
        min: 100,
        phases: ['stretch'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'grip_held_l',
        label: 'Left palm stays neutral, facing in',
        bone: 'forearm_l',
        axis: 'y',
        min: -12,
        max: 15,
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'wrist_neutral_l',
        label: 'Left wrist stays neutral',
        bone: 'hand_l',
        axis: 'z',
        min: -12,
        max: 15,
      }),
      evenSides({
        id: 'dumbbells_aligned',
        label: 'Both dumbbells stay level with one another',
        point: { bone: 'hand_l', along: 1 },
        tolerance: 0.03,
      }),
    ],

    commonErrors: pushdown ? [...PUSHDOWN_ERRORS, ...(variant.commonErrors ?? [])] : [
      {
        id: 'elbow_flare',
        label: 'Flaring the elbows',
        description: 'The elbows drift out to the sides, taking the long head of the triceps out of its stretch.',
        ruleId: 'elbows_in',
        correction: 'Keep the elbows pointing forward and close to the head.',
      },
      {
        id: 'shoulder_swing',
        label: 'Swinging from the shoulder',
        description: 'The upper arm travels forward as the weight comes up, turning it into a pullover.',
        ruleId: 'upper_arm_vertical_l',
        correction: 'Hold the upper arms still; only the forearms move.',
      },
      {
        id: 'arching',
        label: 'Arching the lower back',
        description: 'The ribs flare and the lower back arches to get the arms overhead.',
        ruleId: 'no_arch',
        correction: 'Brace the abdominals and squeeze the glutes before the first rep.',
      },
      {
        id: 'short_range',
        label: 'Stopping short',
        description: 'The dumbbells stop above the head, so the triceps never works from length.',
        ruleId: 'full_stretch_l',
        correction: 'Lower until the forearms are past horizontal behind the head.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: pushdown
        ? 'Breathe in as the bar rises, out as you push it down.'
        : 'Breathe in as the weights lower, out as you straighten the arms.',
    },

    camera: pushdown
      ? {
          preset: 'three_quarter',
          position: vec3(-2.4, 1.5, 1.6),
          target: vec3(0, 1.2, 0.2),
          fov: 42,
          note: 'Three-quarter view from the side shows the elbows at the ribs and the cable to the pulley.',
          ...variant.camera,
        }
      : {
          preset: 'three_quarter',
          position: vec3(2.2, 1.7, 2.2),
          target: vec3(0, 1.45, 0),
          fov: 42,
          note: 'High three-quarter view keeps the dumbbells in shot behind the head.',
          ...variant.camera,
        },
  };
}
