import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { Vec3 } from '../../rig/types';
import { vec3 } from '../../rig/types';
import { bilateralJointTarget, bilateralJoints, bilateralRule, bilateralTiming, mirrorPosition } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells, heelDown, plantedStance } from '../stance';
import { hingeRoot } from './hinge';

/**
 * The horizontal-pull family.
 *
 * The fifth family, and the first built mostly out of another one. A bent-over
 * row is a hinge that stops halfway and holds, with the arms doing the work:
 * the trunk pitches forward over planted feet exactly as the hinge's does — the
 * same root-derived pelvis placement, the same flat feet, the same knee pole —
 * and then stays there while the elbows drive back past the ribs.
 *
 * ## What the hinge gave it, and the one thing it could not
 *
 * The posture needed nothing new: `hingeRoot` places the pelvis, the stance holds
 * the feet flat and the knees on a pole. What is new is that the repetition
 * *starts* bent over. Every other standing exercise opens upright, and a floor
 * lock takes its anchor from the opening frame, so it anchors where an upright
 * body's feet are. A row's opening frame is its bent-over posture, whose feet
 * are wherever the authored leg angles happen to put them. So the row pins its
 * feet explicitly, to where the hinge's stand (`FOOT_L`), and the legs are
 * solved to them from the first frame. `row.test.ts` holds the two together.
 *
 * ## The pull
 *
 * The elbows travel back, close to the ribs, until the upper arm passes the
 * line of the back; the forearm stays close to vertical under the dumbbell,
 * because a forearm that tips forward is curling the weight and one that tips
 * back is pushing it. The grip is neutral — palms facing, the forearm's own
 * neutral — which keeps the elbows in and the lats working rather than the
 * rear delts. Nothing drives the shoulder blades: scapular rhythm stays off.
 */

export interface RowVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Load per hand, kilograms. */
  mass?: number;
  /** How far the trunk pitches forward, degrees, and where the pelvis sits. */
  posture?: RowPosture;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

export interface RowPosture {
  /** Whole-body pitch, degrees forward. Held for the whole repetition. */
  pitch: number;
  /** Pelvis joint position, metres: height, and forward of the feet. */
  pelvis: { y: number; z: number };
}

/**
 * Torso about 50° from vertical: well bent over, but short of parallel, where
 * a lifter without a bench to lean on can still hold a flat back for a set.
 */
const POSTURE: RowPosture = { pitch: 50, pelvis: { y: 0.9, z: -0.15 } };

/**
 * How the left foot stands: the hinge's planted left foot, in the stance both
 * families share (30 cm, 5° toe-out) — where its ankle is, and which way the
 * foot bone points. Measured from the Romanian deadlift's opening frame;
 * `row.test.ts` holds the two together.
 */
export const FOOT_L: { position: Vec3; aim: { direction: Vec3; forward: Vec3 } } = {
  position: vec3(-0.1418, 0.0818, -0.0147),
  aim: { direction: vec3(-0.1758, -0.3985, 0.9001), forward: vec3(-0.0345, 0.9163, 0.3989) },
};

/** Arms hanging straight down from the shoulders, under the load. */
const ARMS_HANGING = bilateralJoints({
  clavicle_l: { z: 0 },
  upperarm_l: { x: 48, z: -8 },
  forearm_l: { x: 6, y: 0 },
  hand_l: { z: 4 },
});
/**
 * Elbows driven back past the ribs, forearms near vertical. Measured: the
 * forearm hangs 3.9° off vertical at the squeeze and the elbow finishes level
 * with the back. A shallower pull (−25°, 88°) leaves the forearm tipped 12°
 * forward, curling the dumbbell; a deeper one (−35°, 80°) starts to push it back.
 */
const ARMS_PULLED = bilateralJoints({
  clavicle_l: { z: 3 },
  upperarm_l: { x: -30, z: -16 },
  forearm_l: { x: 85, y: 6 },
  hand_l: { z: 2 },
});

export function rowFamily(variant: RowVariant): ExerciseDefinition {
  const posture = variant.posture ?? POSTURE;
  const root = hingeRoot(posture.pitch, posture.pelvis);
  const stance = plantedStance({
    width: 0.3,
    toeOut: 5,
    tolerance: 0.015,
    kneePole: vec3(-0.04, 0.5, 1.5),
  });
  const trunk = {
    spine_01: { x: 0 },
    spine_02: { x: 0 },
    spine_03: { x: 2 },
    // Eyes on the floor a metre or so ahead, neck in line with the back.
    neck: { x: -14 },
    head: { x: -6 },
  };
  const placement = { position: { y: root.y, z: root.z }, rotation: { x: posture.pitch } };

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'upper_pull',
    description: variant.description,

    equipment: { required: ['dumbbell'], instances: handDumbbells(variant.mass ?? 14) },

    startPose: { label: 'Arms long', joints: { ...ARMS_HANGING, ...trunk }, root: placement },
    peakPose: { label: 'Elbows back', joints: { ...ARMS_PULLED, ...trunk }, root: placement },

    jointTargets: [
      // The pull: the shoulder extends and the elbow bends together.
      ...bilateralJointTarget({
        bone: 'upperarm_l', axis: 'x', start: 48, peak: -30, role: 'prime',
        range: { min: -30, max: 60 },
      }),
      ...bilateralJointTarget({
        bone: 'forearm_l', axis: 'x', start: 6, peak: 85, role: 'prime',
        range: { min: 0, max: 110 },
      }),
      ...bilateralJointTarget({ bone: 'forearm_l', axis: 'y', start: 0, peak: 6, role: 'support' }),
      // The hinge the pull is made from, held still: outputs, as in the hinge.
      ...bilateralJointTarget({ bone: 'thigh_l', axis: 'x', start: 75, peak: 75, role: 'stabilise' }),
      ...bilateralJointTarget({ bone: 'shin_l', axis: 'x', start: -27, peak: -27, role: 'stabilise' }),
    ],

    phases: [
      {
        id: 'concentric', label: 'Row', to: 'peak', easing: 'lift', contraction: 'concentric',
        // The elbow leads and the upper arm follows a moment later, so the pull
        // starts from the back rather than as a curl.
        jointTiming: bilateralTiming({ forearm_l: { delay: 0.1 } }),
      },
      { id: 'squeeze', label: 'Squeeze', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'stretch', label: 'Stretch', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 2, pauseStretched: 0.4, concentric: 1.2, pauseContracted: 0.6 },

    hands: { grip: 'dumbbell', orientation: 'neutral', closure: 0.85, width: 0.46 },
    feet: stance.feet,
    // Pinned to the hinge's standing feet rather than to the opening frame,
    // position and orientation both; see the header.
    locks: stance.locks.map((lock) => {
      const left = lock.id.endsWith('_l');
      const side = (vector: Vec3) => (left ? { ...vector } : mirrorPosition(vector));
      return {
        ...lock,
        position: side(FOOT_L.position),
        aim: { direction: side(FOOT_L.aim.direction), forward: side(FOOT_L.aim.forward) },
      };
    }),

    muscles: {
      primary: ['latissimus', 'trapezius_mid'],
      secondary: ['deltoid_posterior', 'biceps', 'forearm_flexors'],
      stabilisers: ['erector_lower', 'erector_mid', 'hamstrings', 'gluteus', 'rectus_abdominis', 'obliques'],
      ...variant.muscles,
    },

    technique: [
      ...stance.technique,
      ...heelDown(),
      {
        kind: 'jointAngle',
        id: 'neutral_spine',
        label: 'Lower back stays neutral, not rounded',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 8,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'upper_back_flat',
        label: 'Upper back stays flat, not hunched',
        bone: 'spine_03',
        axis: 'x',
        min: -4,
        max: 8,
        severity: 'error',
      },
      {
        kind: 'segmentAngle',
        id: 'torso_bent_over',
        label: 'Torso stays bent well forward',
        bone: 'spine_02',
        reference: 'vertical',
        min: 40,
        max: 65,
        severity: 'error',
      },
      // Rowing with the body instead of the arms: the chest heaves up to meet
      // the dumbbells.
      {
        kind: 'stationary',
        id: 'torso_still',
        label: 'Torso stays still; the arms do the rowing',
        point: { bone: 'spine_03', along: 1 },
        tolerance: 0.02,
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'hips_high',
        label: 'Hips stay high, well above the knees',
        point: { bone: 'pelvis' },
        relativeTo: { bone: 'shin_l' },
        axis: 'y',
        min: 0.3,
        severity: 'error',
      },
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'soft_knee_l',
        label: 'Left knee stays soft: unlocked, but not squatting',
        bone: 'shin_l',
        axis: 'x',
        min: -35,
        max: -5,
        severity: 'error',
      }),
      // The elbow finishes level with the back or higher; short of that, the
      // lats never reach full contraction.
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'elbow_past_back_l',
        label: 'Left elbow drives back past the ribs',
        bone: 'upperarm_l',
        axis: 'x',
        // −30° at the squeeze puts the elbow level with the back.
        max: -20,
        phases: ['squeeze'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'elbows_in_l',
        label: 'Left elbow stays close to the body, not flared',
        bone: 'upperarm_l',
        axis: 'z',
        min: -30,
        max: -4,
      }),
      ...bilateralRule({
        kind: 'segmentAngle',
        id: 'forearm_vertical_l',
        label: 'Left forearm hangs close to vertical under the weight',
        bone: 'forearm_l',
        reference: 'vertical',
        max: 30,
        phases: ['squeeze'],
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'shoulder_relaxed_l',
        label: 'Left shoulder stays down, not shrugged',
        bone: 'clavicle_l',
        axis: 'z',
        min: -2,
        max: 8,
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

    commonErrors: [
      {
        id: 'body_english',
        label: 'Heaving with the torso',
        description: 'The chest lifts to meet the dumbbells, so the back muscles do less of the pull.',
        ruleId: 'torso_still',
        correction: 'Hold the torso still and reduce the load until the arms can row it alone.',
      },
      {
        id: 'rounding',
        label: 'Rounding the back',
        description: 'The spine flexes under the hanging load.',
        ruleId: 'neutral_spine',
        correction: 'Brace, keep the chest proud and the back flat; hinge less if it cannot hold.',
      },
      {
        id: 'short_pull',
        label: 'Stopping short',
        description: 'The elbows stop in front of the ribs, so the lats never fully contract.',
        ruleId: 'elbow_past_back_l',
        correction: 'Drive the elbows back until they pass the line of the back, then squeeze.',
      },
      {
        id: 'flaring',
        label: 'Flaring the elbows',
        description: 'The elbows swing out wide, moving the work to the rear delts.',
        ruleId: 'elbows_in_l',
        correction: 'Keep the elbows close to the ribs and pull towards the hips.',
      },
      {
        id: 'shrugging',
        label: 'Shrugging the weight up',
        description: 'The shoulders lift towards the ears instead of the elbows driving back.',
        ruleId: 'shoulder_relaxed_l',
        correction: 'Keep the shoulders down and think of pulling with the elbows.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as you row, in as the dumbbells lower.',
    },

    camera: {
      preset: 'three_quarter',
      position: vec3(2.4, 1.1, 1.6),
      target: vec3(0, 0.85, 0.1),
      fov: 40,
      note: 'Three-quarter view shows the flat back, the elbow path and the forearm angle together.',
      ...variant.camera,
    },
  };
}
