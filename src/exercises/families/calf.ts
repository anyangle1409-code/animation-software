import type {
  CameraRecommendation,
  CommonError,
  ExerciseDefinition,
  MuscleInvolvement,
  Tempo,
} from '../types';
import type { EffectorLock, TechniqueRule } from '../../constraints/types';
import { vec3 } from '../../rig/types';
import { bilateralJoints, bilateralLock, bilateralRule } from '../mirror';
import { evenSides } from '../presets';
import { handDumbbells } from '../stance';

/**
 * The calf family: the body lifted onto the balls of the feet.
 *
 * The ninth family. The ankle is the prime mover and the knees stay soft and
 * still, so the whole body rises and falls as one piece over a pivot that does
 * not move: the ball of each foot. That pivot is the lunge's back-foot contact
 * (`EffectorLock.onBall`), held for the whole movement. Given no fixed ankle,
 * the contact lifts each heel about its ball only as far as keeps the knee at
 * its authored 6°, so the body's rise drives the heel and the leg never bends
 * or straightens on the way; the toes stay flat on the floor.
 *
 * The rise is authored where that pivot puts the body. The rig's foot runs
 * 15 cm from ankle to ball, pitched 21° down at rest; turning it a further 35°
 * about the ball lifts the ankle 7 cm and carries it 5.7 cm forward, so the body
 * goes up 7 cm and forward 5.7 cm over the balls of the feet.
 *
 * Two earlier drafts are recorded so they are not repeated. Driving the heel
 * from an authored ankle angle found a second solution, heel up on a bent
 * knee, as often as the straight-legged one. Driving it from an authored heel
 * lift moved the ankle on an arc while the body moved on a straight line, and
 * the knee bent 12° mid-rise to make up the 7 mm between them.
 */

export interface CalfVariant {
  id: string;
  name: string;
  clipName: string;
  description: string;
  /** Dumbbells held at the sides, kilograms each. Bodyweight when absent. */
  mass?: number;
  /** How far each foot turns about its ball at the top, degrees. */
  rise?: number;
  tempo?: Tempo;
  muscles?: Partial<MuscleInvolvement>;
  commonErrors?: CommonError[];
  camera?: Partial<CameraRecommendation>;
}

/** Up onto the balls of the feet, short of the ankle's 45° limit. */
const RISE = 35;

/** The foot from ankle to ball: length and its downward pitch at rest. */
const FOOT = { length: Math.hypot(0.14, 0.055), pitch: Math.atan2(0.055, 0.14) };

/** Knee bend held through the repetition, degrees. */
const SOFT_KNEE = 6;

/** Feet hip width, straight ahead. */
const HALF_WIDTH = 0.1;

const UPRIGHT = {
  pelvis: { x: 0 },
  spine_01: { x: 1 },
  spine_02: { x: 0 },
  spine_03: { x: -1 },
  neck: { x: -1 },
};

/**
 * Where the body goes when each foot turns `rise` degrees further about its
 * ball: up and forward by the ankle's travel on its arc.
 */
export function calfRoot(rise: number): { y: number; z: number } {
  const turned = FOOT.pitch + (rise * Math.PI) / 180;
  return {
    y: FOOT.length * (Math.sin(turned) - Math.sin(FOOT.pitch)),
    z: FOOT.length * (Math.cos(FOOT.pitch) - Math.cos(turned)),
  };
}

export function calfFamily(variant: CalfVariant): ExerciseDefinition {
  const rise = variant.rise ?? RISE;
  const loaded = variant.mass !== undefined;
  const top = calfRoot(rise);
  // Knees soft and held: the contact lifts each heel only as far as keeps this
  // bend while the body rises (`onBall` without an ankle). Thigh and foot take
  // the knee's angle back out, so the foot's authored direction is its rest
  // direction, which is the one the contact rebuilds the ankle from.
  const legs = bilateralJoints({
    thigh_l: { x: SOFT_KNEE / 2 },
    shin_l: { x: -SOFT_KNEE },
    foot_l: { x: SOFT_KNEE / 2 },
  });
  const arms = bilateralJoints(
    loaded
      ? { upperarm_l: { x: 2, z: -6 }, forearm_l: { x: 6, y: 0 }, hand_l: { z: 0 } }
      : { upperarm_l: { x: 4, z: -8 }, forearm_l: { x: 10 } },
  );
  const locks: EffectorLock[] = [
    ...bilateralLock({
      id: 'foot_l',
      chain: 'leg_l',
      mode: 'floor',
      // No fixed ankle: it follows the authored plantarflexion.
      onBall: {},
      pole: vec3(-HALF_WIDTH, 0.5, 2),
      enabled: true,
    }),
  ];

  return {
    id: variant.id,
    name: variant.name,
    clipName: variant.clipName,
    category: 'legs',
    description: variant.description,

    equipment: loaded ? { required: ['dumbbell'], instances: handDumbbells(variant.mass!) } : { required: [], instances: [] },

    startPose: { label: 'Heels down', joints: { ...UPRIGHT, ...arms, ...legs } },
    peakPose: {
      label: 'On the toes',
      joints: { ...UPRIGHT, ...arms, ...legs },
      root: { position: { y: top.y, z: top.z } },
    },

    jointTargets: [],

    phases: [
      { id: 'concentric', label: 'Rise', to: 'peak', easing: 'lift', contraction: 'concentric' },
      { id: 'top', label: 'Squeeze', to: 'peak', easing: 'hold', contraction: 'isometric' },
      { id: 'eccentric', label: 'Lower', to: 'start', easing: 'lift', contraction: 'eccentric' },
      { id: 'stretch', label: 'Heels down', to: 'start', easing: 'hold', contraction: 'isometric' },
    ],

    tempo: variant.tempo ?? { concentric: 1, pauseContracted: 0.8, eccentric: 1.6, pauseStretched: 0.4 },

    hands: loaded
      ? { grip: 'dumbbell', orientation: 'neutral', closure: 0.85 }
      : { grip: 'none', orientation: 'neutral', closure: 0.15 },
    feet: { width: HALF_WIDTH * 2, toeOut: 0, planted: true },
    locks,

    muscles: {
      primary: ['calves'],
      secondary: [],
      stabilisers: ['quadriceps', 'gluteus', 'rectus_abdominis', 'erector_lower'],
      ...variant.muscles,
    },

    technique: [
      // The balls of the feet are the pivot; they do not move.
      ...bilateralRule({
        kind: 'stationary',
        id: 'balls_planted_l',
        label: 'Left foot stays planted on its ball',
        point: { bone: 'toe_l' },
        tolerance: 0.004,
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'full_rise_l',
        label: 'Left heel rises high, onto the ball of the foot',
        bone: 'foot_l',
        axis: 'x',
        max: -25,
        phases: ['top'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'heels_down_l',
        label: 'Left heel comes all the way back down',
        bone: 'foot_l',
        axis: 'x',
        min: -5,
        phases: ['stretch'],
        severity: 'error',
      }),
      ...bilateralRule({
        kind: 'jointAngle',
        id: 'knees_straight_l',
        label: 'Left knee stays straight — the ankle does the lifting',
        bone: 'shin_l',
        axis: 'x',
        min: -10,
        max: 2,
        severity: 'error',
      }),
      {
        kind: 'segmentAngle',
        id: 'torso_upright',
        label: 'Body stays tall — no leaning forward to get onto the toes',
        bone: 'spine_02',
        reference: 'vertical',
        max: 6,
        severity: 'error',
      },
      evenSides({
        id: 'heels_level',
        label: 'Both heels rise level',
        point: { bone: 'foot_l' },
        tolerance: 0.01,
      }),
    ] satisfies TechniqueRule[],

    commonErrors: [
      {
        id: 'bouncing',
        label: 'Bouncing through the bottom',
        description: 'The heels drop and rebound without a pause, so the tendon does the work rather than the calf.',
        ruleId: 'heels_down_l',
        correction: 'Lower all the way and pause for a moment before rising.',
      },
      {
        id: 'short_range',
        label: 'Half reps',
        description: 'The heels only leave the floor a little.',
        ruleId: 'full_rise_l',
        correction: 'Rise as high as the ankles allow and squeeze at the top.',
      },
      {
        id: 'knee_bend',
        label: 'Bending the knees',
        description: 'The knees bend and straighten to help the body up.',
        ruleId: 'knees_straight_l',
        correction: 'Keep the legs straight; only the ankles move.',
      },
      ...(variant.commonErrors ?? []),
    ],

    breathing: {
      inhale: 'eccentric',
      exhale: 'concentric',
      cue: 'Breathe out as you rise, in as the heels come down.',
    },

    camera: {
      preset: 'right',
      position: vec3(2.4, 0.6, 0.6),
      target: vec3(0, 0.45, 0.05),
      fov: 42,
      note: 'Low side view shows the heels leaving the floor and the balls of the feet staying put.',
      ...variant.camera,
    },
  };
}
