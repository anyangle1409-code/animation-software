import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { EffectorLock } from '../../constraints/types';
import { vec3 } from '../../rig/types';
import { bilateralJoints } from '../mirror';
import { BALL_HEIGHT, flatFootAim } from '../stance';

/**
 * The lunge family: a split stance.
 *
 * The seventh family, and the first whose legs do different things. Everything
 * before it is authored for the left side and mirrored to the right; a lunge
 * cannot be, because one leg is in front with its foot flat and the other is
 * behind, up on the ball of its foot. So the legs, their locks and their rules
 * are written out side by side, and only the arms are mirrored.
 *
 * ## The reference variant is the split squat
 *
 * A lunge that steps would need a foot to leave the floor and land again, and a
 * floor lock that holds it for the whole repetition cannot express that yet. A
 * split squat is the lunge with the step taken away: both feet stay where they
 * are and the body sinks straight down between them. It is what every lunge
 * variant's bottom position is, and what a stepping lunge will be built from.
 *
 * ## The feet
 *
 * Both are pinned outright, position and orientation, because the opening frame
 * is a split stance no standing frame supplies. The front foot is flat. The back
 * foot stands on its ball with the heel raised 40° and the toes bent back flat
 * to the floor, which puts its ankle 13 cm up; its shin pivots over a foot that
 * does not move, as a real back foot's does. Each knee is aimed along its foot,
 * and the leg solver turns the shin to keep the foot where it is pinned, as it
 * does for the squat.
 */

export interface LungeVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Distance between the heels front to back and side to side, metres. */
  stance?: LungeStance;
  /** Pelvis joint height at the top and bottom, metres. */
  depth?: { top: number; bottom: number };
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

export interface LungeStance {
  /** Front ankle, forward of the root, metres. */
  front: number;
  /** Back foot's ball, behind the root, metres. */
  back: number;
  /** Distance between the two feet side to side, metres. */
  width: number;
  /**
   * The back ankle's angle, degrees, held while the heel rises and falls about
   * the ball of the foot. Positive is dorsiflexion.
   */
  backAnkle: number;
}

/**
 * 80 cm from the front ankle to the back foot's ball, hip width apart. The back
 * ankle holds 25°: at 15° the heel had to rise past what the toes can bend back
 * under, and at 30° the ankle ran out at the bottom.
 */
const STANCE: LungeStance = { front: 0.32, back: 0.48, width: 0.2, backAnkle: 25 };

/**
 * From the split stance, front knee bent 43°, down to the front thigh parallel
 * and the back knee 9 cm off the floor. Higher at the top, the back hip runs
 * out of extension (25°): the back leg reaches 48 cm behind the pelvis.
 */
const DEPTH = { top: 0.78, bottom: 0.54 };

/** The pelvis sits this far behind the midpoint of the root, metres. */
const PELVIS_Z = -0.08;

/** The pelvis joint's height above the root; see `families/hinge.ts`. */
const PELVIS_HEIGHT = 0.95;

const ARMS = bilateralJoints({ upperarm_l: { x: 8, z: -8 }, forearm_l: { x: 12 } });
const TRUNK = { pelvis: { x: 0 }, spine_01: { x: 2 }, spine_02: { x: 0 }, spine_03: { x: -1 }, neck: { x: -2 } };

export function lungeFamily(variant: LungeVariant): ExerciseDefinition {
  const stance = variant.stance ?? STANCE;
  const depth = variant.depth ?? DEPTH;
  const half = stance.width / 2;

  // Front (left) foot flat; back (right) foot standing on its ball.
  const frontAnkle = vec3(-half, 0.08, stance.front);
  const backBall = vec3(half, BALL_HEIGHT, -stance.back);
  const locks: EffectorLock[] = [
    {
      id: 'foot_l',
      chain: 'leg_l',
      mode: 'floor',
      position: frontAnkle,
      aim: flatFootAim(0),
      pole: vec3(-half, 1.5, 2),
      enabled: true,
    },
    {
      id: 'foot_r',
      chain: 'leg_r',
      mode: 'floor',
      position: backBall,
      onBall: { ankle: stance.backAnkle },
      pole: vec3(half, 0.3, 2),
      enabled: true,
    },
  ];
  const root = (pelvis: number) => ({ position: { y: pelvis - PELVIS_HEIGHT, z: PELVIS_Z } });
  const legs = {
    thigh_l: { x: 40 },
    shin_l: { x: -40 },
    thigh_r: { x: -10 },
    shin_r: { x: -40 },
    foot_r: { x: -40 },
    // The back toes bend up to lie flat on the floor under a raised heel.
    toe_r: { x: 40 },
  };

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'legs',
    description: variant.description,

    equipment: { required: [], instances: [] },

    startPose: { label: 'Split stance', joints: { ...TRUNK, ...ARMS, ...legs }, root: root(depth.top) },
    peakPose: {
      label: 'Bottom',
      joints: { ...TRUNK, ...ARMS, ...legs, thigh_l: { x: 90 }, shin_l: { x: -90 }, thigh_r: { x: 10 }, shin_r: { x: -95 } },
      root: root(depth.bottom),
    },

    // Outputs of the solve, as in the squat: the root places the pelvis, the
    // feet are pinned, and the legs fill in. Recorded so the definition says
    // what it plays; `lunge.test.ts` holds them to it.
    jointTargets: [
      { bone: 'thigh_l', axis: 'x', start: 53, peak: 89, role: 'prime' },
      { bone: 'shin_l', axis: 'x', start: -43, peak: -91, role: 'prime' },
      { bone: 'thigh_r', axis: 'x', start: -14, peak: 4, role: 'support' },
      { bone: 'shin_r', axis: 'x', start: -50, peak: -106, role: 'support' },
    ],

    phases: [
      { id: 'eccentric', label: 'Lower', to: 'peak', easing: 'lift', contraction: 'eccentric' },
      { id: 'bottom', label: 'Bottom', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'concentric', label: 'Drive up', to: 'start', easing: 'lift', contraction: 'concentric' },
      { id: 'top', label: 'Reset', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 1.8, pauseStretched: 0.3, concentric: 1.4, pauseContracted: 0.4 },

    hands: { grip: 'none', orientation: 'neutral', closure: 0.15 },
    feet: { width: stance.width, toeOut: 0, planted: true },
    locks,

    muscles: {
      primary: ['quadriceps', 'gluteus'],
      secondary: ['hamstrings', 'hip_adductors', 'calves'],
      stabilisers: ['hip_abductors', 'rectus_abdominis', 'obliques', 'erector_lower'],
      ...variant.muscles,
    },

    technique: [
      {
        kind: 'stationary',
        id: 'front_foot_planted',
        label: 'Front foot stays planted',
        point: { bone: 'foot_l' },
        tolerance: 0.015,
        severity: 'error',
      },
      // The back foot pivots on its ball, so the ball is what must not move.
      {
        kind: 'stationary',
        id: 'back_ball_planted',
        label: 'Back foot stays planted on its ball',
        point: { bone: 'toe_r' },
        tolerance: 0.01,
        severity: 'error',
      },
      {
        kind: 'stationary',
        id: 'front_heel_down',
        label: 'Front heel stays on the floor',
        point: { bone: 'foot_l', offset: { x: 0, y: -0.04, z: 0 } },
        tolerance: 0.02,
        severity: 'error',
      },
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Torso stays upright, not pitched over the front knee',
        bone: 'spine_02',
        reference: 'vertical',
        max: 12,
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'front_knee_over_foot',
        label: 'Front knee tracks over the front foot, not caving in',
        point: { bone: 'shin_l' },
        relativeTo: { bone: 'foot_l' },
        axis: 'x',
        min: -0.05,
        max: 0.05,
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'front_knee_not_past_toes',
        label: 'Front knee stays roughly over the ankle, not far past the toes',
        point: { bone: 'shin_l' },
        relativeTo: { bone: 'foot_l' },
        axis: 'z',
        max: 0.12,
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'depth',
        label: 'Back knee lowers to just above the floor',
        point: { bone: 'shin_r' },
        // Against the front ankle, which is 8 cm off the floor and never moves.
        relativeTo: { bone: 'foot_l' },
        axis: 'y',
        max: 0.1,
        phases: ['bottom'],
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'hips_square',
        label: 'Hips stay square to the front',
        bone: 'pelvis',
        axis: 'y',
        min: -6,
        max: 6,
        severity: 'error',
      },
      {
        kind: 'jointAngle',
        id: 'neutral_spine',
        label: 'Lower back stays neutral',
        bone: 'spine_01',
        axis: 'x',
        min: -4,
        max: 10,
        severity: 'error',
      },
    ],

    commonErrors: [
      {
        id: 'knee_cave',
        label: 'Front knee caving in',
        description: 'The front knee collapses towards the midline as the body lowers.',
        ruleId: 'front_knee_over_foot',
        correction: 'Push the front knee out over the middle of the foot.',
      },
      {
        id: 'forward_knee',
        label: 'Front knee shooting forward',
        description: 'The weight rolls onto the front toes and the knee travels far past them.',
        ruleId: 'front_knee_not_past_toes',
        correction: 'Sink straight down between the feet, with the weight through the front heel.',
      },
      {
        id: 'leaning',
        label: 'Leaning over the front leg',
        description: 'The torso pitches forward and the lower back takes the load.',
        ruleId: 'torso_upright',
        correction: 'Keep the chest tall and the shoulders stacked over the hips.',
      },
      {
        id: 'shallow',
        label: 'Cutting the depth',
        description: 'Stopping well above the floor, so the front thigh never reaches parallel.',
        ruleId: 'depth',
        correction: 'Lower until the back knee is just above the floor.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in as you sink, out as you drive back up through the front heel.',
    },

    camera: {
      preset: 'right',
      position: vec3(2.8, 0.9, 0.1),
      target: vec3(0, 0.6, -0.05),
      fov: 42,
      note: 'Side view shows both knees, the depth and the upright torso together.',
      ...variant.camera,
    },
  };
}
