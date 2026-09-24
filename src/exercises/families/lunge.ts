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
 * A split squat is the lunge with the step taken away: both feet stay where
 * they are and the body sinks straight down between them. It is what every
 * lunge variant's bottom position is, and what the stepping lunge below
 * (`step: true`) is built from.
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
  /** Step forward into the lunge from standing, and back out of it. */
  step?: boolean;
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
  if (variant.step) return steppingLunge(variant);
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

// ------------------------------------------------------- The stepping lunge

/**
 * The forward lunge: from standing, one long step forward with the left foot
 * into the split squat's bottom position, then a push back to standing.
 *
 * The first exercise in which a foot leaves the floor. Everything it is made
 * from was already here except timing:
 *
 * * **The stepping foot is a keyframe target, not a lock.** Its ankle is a
 *   pose-level IK target (`PoseSpec.ik`), aimed flat, at the standing foot in
 *   the start pose and at the split squat's front foot in the bottom pose. Left
 *   to the phase's blend it would slide along the floor and only arrive as the
 *   body did. The phase times it instead (`MovementPhase.ikTiming`): on the way
 *   down it travels in the first 65% of the phase, rising 7 cm on the way, and
 *   is planted for the rest; on the way back it waits for the first 35%, while
 *   the front leg pushes the body back over the back foot, and then steps home.
 *   Landing earlier, at 45%, the hips were still too far back for the leg to
 *   reach it.
 * * **The back foot is the split squat's**, on its ball at a fixed 25° of ankle
 *   (`onBall.ankle`), where the ball of the standing right foot already is. The
 *   heel's bracket starts flat, so at standing the foot is flat; as the body
 *   travels forward the shin tips over it, and once the ankle has bent to 25°
 *   the heel rises instead. Holding the knee instead, as the calf raise does,
 *   asked the back thigh for more than its 25° of extension mid-step, and the
 *   ball slid 8 cm.
 * * **The bottom is the split squat's bottom**, carried forward to where the
 *   step lands: everything 62 cm further on, so the back foot's ball is where it
 *   stood.
 */

/** Standing feet: hip width, straight ahead, flat. */
const STEP_HALF_WIDTH = STANCE.width / 2;

/** How far the split squat's stance is carried forward: its back ball onto the standing one. */
const STEP_SHIFT = 0.14 + STANCE.back;

/** Share of the lowering phase the step takes, and how high the foot lifts on it. */
const STEP = { finish: 0.65, lift: 0.07 };

function steppingLunge(variant: LungeVariant): ExerciseDefinition {
  const half = STEP_HALF_WIDTH;
  const standingAnkle = vec3(-half, 0.08, 0);
  const landedAnkle = vec3(-half, 0.08, STANCE.front + STEP_SHIFT);
  // The standing right foot's ball: 14 cm ahead of its ankle, on the floor.
  const backBall = vec3(half, BALL_HEIGHT, 0.14);
  const aim = flatFootAim(0);
  // Each knee aimed along its foot, from 1.68 m ahead, as the split squat's is.
  const pole = (ankle: { x: number; z: number }) => vec3(ankle.x, 1.5, ankle.z + 1.68);
  const locks: EffectorLock[] = [
    {
      id: 'foot_r',
      chain: 'leg_r',
      mode: 'floor',
      position: backBall,
      onBall: { ankle: STANCE.backAnkle },
      pole: vec3(half, 0.3, 2),
      enabled: true,
    },
  ];
  // Starting guesses under the solve; the targets and the back lock decide the legs.
  const standing = {
    thigh_l: { x: 0 }, shin_l: { x: 0 }, foot_l: { x: 0 },
    thigh_r: { x: 0 }, shin_r: { x: -2 }, foot_r: { x: 0 }, toe_r: { x: 0 },
  };
  const bottom = {
    thigh_l: { x: 87 }, shin_l: { x: -90 }, foot_l: { x: 0 },
    thigh_r: { x: 4 }, shin_r: { x: -104 }, foot_r: { x: 25 }, toe_r: { x: 40 },
  };
  const depth = variant.depth ?? DEPTH;

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'legs',
    description: variant.description,

    equipment: { required: [], instances: [] },

    startPose: {
      label: 'Standing',
      joints: { ...TRUNK, ...ARMS, ...standing },
      ik: { leg_l: { target: standingAnkle, pole: pole(standingAnkle), aim } },
    },
    peakPose: {
      label: 'Bottom',
      joints: { ...TRUNK, ...ARMS, ...bottom },
      root: { position: { y: depth.bottom - PELVIS_HEIGHT, z: PELVIS_Z + STEP_SHIFT } },
      ik: { leg_l: { target: landedAnkle, pole: pole(landedAnkle), aim } },
    },

    jointTargets: [],

    phases: [
      {
        id: 'step',
        label: 'Step and lower',
        to: 'peak',
        easing: 'lift',
        contraction: 'eccentric',
        ikTiming: { leg_l: { finish: STEP.finish, lift: STEP.lift, easing: 'easeInOut' } },
      },
      { id: 'bottom', label: 'Bottom', to: 'peak', easing: 'hold', contraction: 'isometric' },
      {
        id: 'drive',
        label: 'Push back',
        to: 'start',
        easing: 'lift',
        contraction: 'concentric',
        ikTiming: { leg_l: { delay: 1 - STEP.finish, lift: STEP.lift, easing: 'easeInOut' } },
      },
      { id: 'stand', label: 'Stand', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { eccentric: 1.8, pauseStretched: 0.3, concentric: 1.6, pauseContracted: 0.5 },

    hands: { grip: 'none', orientation: 'neutral', closure: 0.15 },
    feet: { width: STANCE.width, toeOut: 0, planted: true },
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
        id: 'back_ball_planted',
        label: 'Back foot stays planted on its ball',
        point: { bone: 'toe_r' },
        tolerance: 0.01,
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'long_step',
        label: 'Steps long: the front ankle lands well ahead of the back foot',
        point: { bone: 'foot_l' },
        relativeTo: { bone: 'toe_r' },
        axis: 'z',
        min: 0.7,
        phases: ['bottom'],
        severity: 'error',
      },
      {
        kind: 'relativePosition',
        id: 'depth',
        label: 'Back knee lowers to just above the floor',
        point: { bone: 'shin_r' },
        // Against the front ankle, 8 cm off the floor once it has landed.
        relativeTo: { bone: 'foot_l' },
        axis: 'y',
        max: 0.1,
        phases: ['bottom'],
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
        phases: ['bottom'],
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
        phases: ['bottom'],
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
        kind: 'jointAngle',
        id: 'hips_square',
        label: 'Hips stay square to the front',
        bone: 'pelvis',
        axis: 'y',
        min: -6,
        max: 6,
        severity: 'error',
      },
    ],

    commonErrors: [
      {
        id: 'short_step',
        label: 'Stepping short',
        description: 'The front foot lands close, so the front knee shoots past the toes at the bottom.',
        ruleId: 'long_step',
        correction: 'Take a long step, so the front shin can stay near vertical at the bottom.',
      },
      {
        id: 'knee_cave',
        label: 'Front knee caving in',
        description: 'The front knee collapses towards the midline as the body lowers.',
        ruleId: 'front_knee_over_foot',
        correction: 'Land with the foot straight ahead and push the knee out over it.',
      },
      {
        id: 'shallow',
        label: 'Cutting the depth',
        description: 'Stopping well above the floor after the step.',
        ruleId: 'depth',
        correction: 'Lower until the back knee is just above the floor.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe in as you step and sink, out as you push back to standing.',
    },

    camera: {
      preset: 'right',
      position: vec3(3, 1, 0.4),
      target: vec3(0, 0.7, 0.35),
      fov: 44,
      note: 'Side view shows the step, the depth at the bottom and the push back to standing.',
      ...variant.camera,
    },
  };
}
