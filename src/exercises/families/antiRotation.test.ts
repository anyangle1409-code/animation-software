import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { anatomicalGripOffset, socketWorldPoint } from '../../equipment/attach';
import { measureTwoHandFit } from '../../equipment/gripDiagnostics';
import { EXERCISES } from '../library';
import { pallofPress } from '../definitions/pallofPress';

/**
 * The anti-rotation family: the arms press a cable handle straight out while
 * nothing above the feet turns towards the pull. These hold the trunk square,
 * the hands on their line, the handle in both hands and the cable on the pulley.
 */
const rig = canonicalSkeleton;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, pallofPress);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);
const byId = (id: string) => clip.equipment.find((instance) => instance.id === id)!;
const frames = Array.from({ length: 41 }, (_, step) => {
  const frame = resolveFrame(rig, evaluation, clip, (step / 40) * clip.duration, { anchors });
  evaluation.apply(frame.pose);
  const degrees = (bone: 'pelvis' | 'spine_01' | 'spine_02' | 'spine_03') =>
    ((frame.pose.rotations[bone]?.y ?? 0) * 180) / Math.PI;
  return {
    frame,
    twist: Math.max(...(['pelvis', 'spine_01', 'spine_02', 'spine_03'] as const).map((bone) => Math.abs(degrees(bone)))),
    upper: evaluation.localToWorld('hand_l', anatomicalGripOffset('l'), new Vector3()),
    lower: evaluation.localToWorld('hand_r', anatomicalGripOffset('r'), new Vector3()),
    fit: measureTwoHandFit(evaluation, byId('handle'), frame.equipment.get('handle')!)!,
    elbows: [frame.pose.rotations.forearm_l!.x, frame.pose.rotations.forearm_r!.x].map((x) => (x * 180) / Math.PI),
  };
});

describe('the anti-rotation family', () => {
  it('keeps the hips and trunk square while the arms press', () => {
    for (const { twist } of frames) expect(twist).toBeLessThan(0.5);
  });

  it('presses the clasped hands straight out along the midline', () => {
    for (const { upper, lower, fit } of frames) {
      // The wrists are blended in straight lines and the hands turn a little on
      // the way, so the grips bow off the midline mid-press: 9.7 mm at most,
      // measured over 400 samples, on a 34 cm press.
      expect(Math.abs(upper.x)).toBeLessThan(0.011);
      expect(Math.abs(lower.x)).toBeLessThan(0.011);
      // The handle is rigid in both hands: exact at the chest and at the hold,
      // 1.09 mm at most in between, where the hands' spacing drifts slightly.
      expect(Math.max(fit.leftError, fit.rightError)).toBeLessThan(0.0015);
    }
    const depth = frames.map(({ upper }) => upper.z);
    // The upper grip, 1 cm ahead of the handle's middle: from 18 cm to 52 cm.
    expect(Math.min(...depth)).toBeCloseTo(0.18, 2);
    expect(Math.max(...depth)).toBeCloseTo(0.52, 2);
  });

  it('reaches long at the hold', () => {
    const hold = frames.reduce((a, b) => (b.upper.z > a.upper.z ? b : a));
    // Measured: 21° and 10°.
    for (const elbow of hold.elbows) expect(elbow).toBeLessThan(25);
  });

  it('runs the cable from the chest-height pulley to the handle, which faces it', () => {
    for (const { frame } of frames) {
      const pulley = socketWorldPoint(byId('tower'), 'pulley_mid', frame.equipment.get('tower')!.matrix)!;
      const clipPoint = socketWorldPoint(byId('handle'), 'clip', frame.equipment.get('handle')!.matrix)!;
      const cable = frame.equipment.get('cable')!;
      expect(new Vector3(0, 0, 0).applyMatrix4(cable.matrix).distanceTo(pulley)).toBeLessThan(1e-9);
      expect(new Vector3(0, 1, 0).applyMatrix4(cable.matrix).distanceTo(clipPoint)).toBeLessThan(1e-9);
      const grips = frame.equipment.get('handle')!.position;
      // The clip is on the pulley's side of the handle: 9 cm of its 11, the
      // handle being tipped forward a little.
      expect(grips.x - clipPoint.x).toBeGreaterThan(0.08);
      expect(Math.abs(pulley.y - 1.25)).toBeLessThan(1e-9);
    }
  });

  it('has one registered variant', () => {
    expect(EXERCISES.filter((exercise) => exercise.category === 'core').map((exercise) => exercise.id))
      .toEqual(['cable_pallof_press']);
  });
});
