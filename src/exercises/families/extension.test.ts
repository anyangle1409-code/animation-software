import { describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { canonicalSkeleton, PoseEvaluation } from '../../rig/skeleton';
import { generateClip } from '../../animation/generate';
import { resolveFrame } from '../../animation/pipeline';
import { lockAnchors } from '../../constraints/locks';
import { sampleClip } from '../../animation/clip';
import { EXERCISES } from '../library';
import { overheadExtension } from '../definitions/overheadExtension';
import { cablePushdown } from '../definitions/cablePushdown';
import { measureTwoHandFit } from '../../equipment/gripDiagnostics';
import { socketWorldPoint } from '../../equipment/attach';

/**
 * The elbow-extension family: the upper arm points at the ceiling and holds
 * still, and the forearm folds down behind the head and back up. These hold
 * both halves, and the one new thing the family does — load passing behind
 * the head — to a clear gap between the two dumbbells.
 */
const rig = canonicalSkeleton;
const evaluation = new PoseEvaluation(rig);
const clip = generateClip(rig, overheadExtension);
const anchors = lockAnchors(evaluation, sampleClip(clip, 0).pose, clip.locks);

function at(time: number) {
  const frame = resolveFrame(rig, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);
  const shoulder = evaluation.head('upperarm_l', new Vector3());
  const elbow = evaluation.head('forearm_l', new Vector3());
  return {
    upperArm: (elbow.clone().sub(shoulder).normalize().angleTo(new Vector3(0, 1, 0)) * 180) / Math.PI,
    elbow,
    hand: evaluation.head('hand_l', new Vector3()),
    head: evaluation.head('head', new Vector3()),
    gap: frame.equipment.get('dumbbell_l')!.position.distanceTo(frame.equipment.get('dumbbell_r')!.position),
  };
}

describe('the extension family', () => {
  it('holds the upper arm still, pointing at the ceiling', () => {
    const first = at(0);
    // 11.2° off vertical, measured: elbows up and a little forward.
    expect(first.upperArm).toBeLessThan(15);
    for (let step = 0; step <= 40; step += 1) {
      const frame = at((step / 40) * clip.duration);
      expect(Math.abs(frame.upperArm - first.upperArm), `step ${step}`).toBeLessThan(1);
      expect(frame.elbow.distanceTo(first.elbow), `elbow at step ${step}`).toBeLessThan(1e-6);
    }
  });

  it('folds the forearm down behind the head, and keeps the dumbbells apart', () => {
    const stretch = at(overheadExtension.tempo.eccentric + overheadExtension.tempo.pauseStretched / 2);
    expect(stretch.hand.z).toBeLessThan(stretch.head.z - 0.2);
    expect(stretch.hand.y).toBeLessThan(stretch.elbow.y);
    for (let step = 0; step <= 40; step += 1) {
      // Two 48 mm plates side by side need 96 mm; 380 mm measured at the closest.
      expect(at((step / 40) * clip.duration).gap, `step ${step}`).toBeGreaterThan(0.25);
    }
  });

  it('has its two registered variants', () => {
    expect(EXERCISES.filter((exercise) => exercise.clipName.includes('triceps')).map((exercise) => exercise.id))
      .toEqual(['dumbbell_overhead_triceps_extension', 'cable_triceps_pushdown']);
  });
});

/**
 * The pushdown: the first cable, and the first bar held in both hands. These
 * hold the three things that make it work — the cable meets both its ends on
 * every frame, the rigid bar stays in the hands, and the elbows stay put.
 */
describe('the cable pushdown', () => {
  const pushClip = generateClip(rig, cablePushdown);
  const pushEvaluation = new PoseEvaluation(rig);
  const pushAnchors = lockAnchors(pushEvaluation, sampleClip(pushClip, 0).pose, pushClip.locks);
  const byId = (id: string) => pushClip.equipment.find((instance) => instance.id === id)!;
  const frames = Array.from({ length: 41 }, (_, step) => {
    const frame = resolveFrame(rig, pushEvaluation, pushClip, (step / 40) * pushClip.duration, { anchors: pushAnchors });
    pushEvaluation.apply(frame.pose);
    return {
      frame,
      elbow: pushEvaluation.head('forearm_l', new Vector3()),
      shoulder: pushEvaluation.head('upperarm_l', new Vector3()),
      fit: measureTwoHandFit(pushEvaluation, byId('bar'), frame.equipment.get('bar')!)!,
    };
  });

  it('runs the cable from the pulley to the bar on every frame', () => {
    const lengths: number[] = [];
    for (const { frame } of frames) {
      const pulley = socketWorldPoint(byId('tower'), 'pulley', frame.equipment.get('tower')!.matrix)!;
      const clip = socketWorldPoint(byId('bar'), 'clip', frame.equipment.get('bar')!.matrix)!;
      const cable = frame.equipment.get('cable')!;
      // The cable's own ends, from its unit length along +Y.
      expect(new Vector3(0, 0, 0).applyMatrix4(cable.matrix).distanceTo(pulley)).toBeLessThan(1e-9);
      expect(new Vector3(0, 1, 0).applyMatrix4(cable.matrix).distanceTo(clip)).toBeLessThan(1e-9);
      // Stretched along its length only: its thickness never changes.
      expect(cable.scale!.x).toBe(1);
      expect(cable.scale!.z).toBe(1);
      lengths.push(cable.scale!.y);
    }
    // Measured: 0.80 m with the bar up, 1.27 m at lockout.
    expect(Math.min(...lengths)).toBeGreaterThan(0.75);
    expect(Math.max(...lengths)).toBeLessThan(1.32);
    expect(Math.max(...lengths) - Math.min(...lengths)).toBeGreaterThan(0.4);
  });

  it('keeps the bar rigid in both hands', () => {
    for (const { fit } of frames) {
      // Measured: 0.67 mm at each hand, hands 1.3 mm closer than the grips.
      expect(Math.max(fit.leftError, fit.rightError)).toBeLessThan(0.001);
      expect(Math.abs(fit.separationError)).toBeLessThan(0.002);
    }
  });

  it('keeps the elbows at the sides while the forearms move', () => {
    const first = frames[0];
    for (const { elbow, shoulder } of frames) {
      expect(elbow.distanceTo(first.elbow)).toBeLessThan(1e-6);
      // 7° forward of vertical, measured.
      const upperArm = (elbow.clone().sub(shoulder).normalize().angleTo(new Vector3(0, -1, 0)) * 180) / Math.PI;
      expect(upperArm).toBeLessThan(10);
      expect(elbow.z).toBeGreaterThan(shoulder.z);
    }
  });

  it('pushes the bar down to the thighs and lets it rise to the chest', () => {
    const heights = frames.map(({ frame }) => frame.equipment.get('bar')!.position.y);
    // Measured: 0.78 m at lockout, 1.20 m at the top.
    expect(Math.min(...heights)).toBeLessThan(0.8);
    expect(Math.max(...heights)).toBeGreaterThan(1.15);
  });
});
