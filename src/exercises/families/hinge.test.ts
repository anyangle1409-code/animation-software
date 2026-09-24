import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { blendPoses, poseFromDegrees } from '../../rig/pose';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { romanianDeadlift } from '../definitions/romanianDeadlift';
import { airSquat } from '../definitions/airSquat';
import { hingeFamily, hingeRoot, PELVIS_HEIGHT } from './hinge';
import type { ExerciseDefinition } from '../types';

/**
 * The hinge family, and the three things it needed from the engine.
 *
 * A hinge tips the whole body 70° forward over planted feet. Doing that
 * convincingly asked for a pivot for the root's rotation (so the hips travel
 * in a line instead of swinging up and out), feet that hold their orientation
 * as well as their position (so the toes stay out of the floor while the shins
 * rock), and an explicit knee direction (so a straight standing leg does not
 * pick an arbitrary twist). Each is checked here where it matters, and each is
 * opt-in, so the rest of the library is unchanged by them.
 */
const rig = canonicalSkeleton;
const deg = (radians: number | undefined) => ((radians ?? 0) * 180) / Math.PI;

function playback(exercise: ExerciseDefinition, samples = 60) {
  const evaluation = new PoseEvaluation(rig);
  const clip = generateClip(rig, exercise);
  const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
  return Array.from({ length: samples + 1 }, (_, step) => {
    const time = (step / samples) * clip.duration;
    const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
    evaluation.apply(frame.pose);
    return {
      time,
      pose: frame.pose,
      pelvis: evaluation.head('pelvis', new Vector3()),
      knee: evaluation.head('shin_l', new Vector3()),
      toe: evaluation.tail('toe_l', new Vector3()),
      foot: new Vector3(0, 1, 0).applyQuaternion(evaluation.quaternion('foot_l')),
    };
  });
}

/** The bottom hold: the eccentric phase has ended and the stretch has begun. */
function atBottom(exercise: ExerciseDefinition) {
  const frames = playback(exercise, 200);
  const bottom = exercise.tempo.eccentric + exercise.tempo.pauseStretched / 2;
  return frames.reduce((best, frame) =>
    Math.abs(frame.time - bottom) < Math.abs(best.time - bottom) ? frame : best,
  );
}

describe('the hinge family', () => {
  it('authors hip, knee and ankle angles that agree with what the solver produces', () => {
    // All three are outputs: the root places the hips, the locks place the feet
    // and hold them flat, and the solver fills in the legs. The definition's
    // numbers are what a coach reads, so they must describe what plays.
    const solved = atBottom(romanianDeadlift).pose.rotations;
    const asked = (bone: string) =>
      romanianDeadlift.jointTargets.find((target) => target.bone === bone && target.axis === 'x')!.peak;
    for (const [bone, value] of [
      ['thigh_l', solved.thigh_l?.x],
      ['shin_l', solved.shin_l?.x],
      ['foot_l', solved.foot_l?.x],
    ] as const) {
      expect(Math.abs(deg(value) - asked(bone)), `${bone}: asked ${asked(bone)}, solved ${deg(value).toFixed(1)}`)
        .toBeLessThan(1.5);
    }
  });

  it('places the pelvis exactly where it asks, from the root it derives', () => {
    expect(rig.bone('pelvis').restHead.y).toBe(PELVIS_HEIGHT);
    const bottom = atBottom(romanianDeadlift);
    expect(bottom.pelvis.y).toBeCloseTo(0.9, 6);
    expect(bottom.pelvis.z).toBeCloseTo(-0.17, 6);
    expect(hingeRoot(0, { y: PELVIS_HEIGHT, z: 0 })).toEqual({ y: 0, z: 0 });
  });

  it('moves the hips in a straight line, which the root pivot is for', () => {
    // Back 17 cm and down 5 cm, on a line. Blending the root about its own
    // origin on the floor instead swings the hips 12 cm up mid-descent, which
    // is what straightened the legs and lifted the feet on the first attempt.
    const frames = playback(romanianDeadlift).filter((frame) => frame.time <= romanianDeadlift.tempo.eccentric);
    const start = frames[0].pelvis;
    const end = frames[frames.length - 1].pelvis;
    const line = end.clone().sub(start).normalize();
    const worst = Math.max(
      ...frames.map((frame) => {
        const offset = frame.pelvis.clone().sub(start);
        return offset.addScaledVector(line, -offset.dot(line)).length();
      }),
    );
    expect(worst).toBeLessThan(1e-6);

    const unpivoted = hingeFamily({ id: 'probe', name: 'probe', clipName: 'probe', description: 'probe' });
    delete unpivoted.rootPivot;
    const midway = playback(unpivoted, 4)[1];
    expect(midway.pelvis.y - start.y).toBeGreaterThan(0.1);
  });

  it('keeps the feet flat while the shins rock above them', () => {
    // The shins lean forward 7° mid-descent and back 4° at the bottom. With
    // orientation held, the ankle takes that and the foot does not move.
    const frames = playback(romanianDeadlift);
    const first = frames[0];
    for (const frame of frames) {
      expect(frame.foot.angleTo(first.foot), `foot at ${frame.time.toFixed(2)}s`).toBeLessThan(1e-4);
      expect(Math.abs(frame.toe.y - first.toe.y), `toe at ${frame.time.toFixed(2)}s`).toBeLessThan(0.001);
    }
    const ankles = frames.map((frame) => deg(frame.pose.rotations.foot_l?.x));
    expect(Math.max(...ankles) - Math.min(...ankles)).toBeGreaterThan(8);
  });

  it('stays a hinge: the hips stay high where a squat takes them low', () => {
    // The same measurement in both families, held to opposite sides of a line.
    const height = (exercise: ExerciseDefinition) => {
      const bottom = atBottom(exercise);
      return bottom.pelvis.y - bottom.knee.y;
    };
    expect(height(romanianDeadlift)).toBeGreaterThan(0.35);
    expect(height(airSquat)).toBeLessThan(0.1);
  });

  it('shares the heel rule with the squat, and nothing it only resembles', () => {
    const rule = (exercise: ExerciseDefinition, id: string) =>
      exercise.technique.find((entry) => entry.id === id);
    expect(rule(romanianDeadlift, 'heel_down_l')).toEqual(rule(airSquat, 'heel_down_l'));
    expect(rule(romanianDeadlift, 'heel_down_r')).toEqual(rule(airSquat, 'heel_down_r'));
    // Knee tracking is the squat's: a knee bent 20° has nowhere to cave to.
    expect(rule(romanianDeadlift, 'knee_tracking_l')).toBeUndefined();
  });

  it('opts into the new engine behaviour; nothing else in the library does', () => {
    for (const exercise of EXERCISES) {
      const hinge = exercise.id === romanianDeadlift.id;
      expect(!!exercise.rootPivot, exercise.id).toBe(hinge);
      expect(exercise.locks.some((lock) => lock.holdOrientation), exercise.id).toBe(hinge);
    }
  });

  it('has exactly one registered variant, the reference Romanian deadlift', () => {
    expect(EXERCISES.filter((exercise) => exercise.rootPivot).map((exercise) => exercise.id))
      .toEqual(['dumbbell_romanian_deadlift']);
  });
});

describe('blending the root about a pivot', () => {
  const standing = poseFromDegrees({}, { position: { y: 0, z: 0 } });
  const hinged = poseFromDegrees({}, { position: { y: 0.2, z: -0.9 }, rotation: { x: 60 } });

  it('changes nothing without one', () => {
    const plain = blendPoses(standing, hinged, 0.5);
    expect(plain.rootPosition).toEqual({ x: 0, y: 0.1, z: -0.45 });
  });

  it('agrees with the plain blend at both ends and moves the pivot in a line between', () => {
    const pivot = { x: 0, y: 0.95, z: 0 };
    const at = (t: number) => {
      const pose = blendPoses(standing, hinged, t, pivot);
      const evaluation = new PoseEvaluation(rig).apply(pose);
      return { pose, pelvis: evaluation.head('pelvis', new Vector3()) };
    };
    for (const t of [0, 1]) {
      const plain = blendPoses(standing, hinged, t);
      const pivoted = at(t).pose;
      for (const axis of ['x', 'y', 'z'] as const) {
        expect(pivoted.rootPosition[axis]).toBeCloseTo(plain.rootPosition[axis], 12);
      }
    }
    const a = at(0).pelvis;
    const b = at(1).pelvis;
    for (const t of [0.25, 0.5, 0.75]) {
      expect(at(t).pelvis.distanceTo(a.clone().lerp(b, t)), `t = ${t}`).toBeLessThan(1e-9);
    }
  });
});
