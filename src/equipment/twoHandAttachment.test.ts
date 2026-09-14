import { describe, expect, it } from 'vitest';
import { Matrix4, Vector3 } from 'three';
import { resolveEquipment, twoHandAttachmentMatrix, twoHandGripOffsets } from './attach';
import { measureTwoHandFit } from './gripDiagnostics';
import { withTwoHandGripWidth } from './library';
import type { EquipmentInstance } from './types';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { restPose } from '../rig/pose';

const base: EquipmentInstance = {
  id: 'test_bar',
  kind: 'barbell',
  position: { x: 0, y: 0, z: 0 },
  rotation: { x: 0, y: 0, z: 0 },
  attachment: {
    mode: 'hands',
    leftSocket: 'grip_l',
    rightSocket: 'grip_r',
  },
  visible: true,
};

const evaluation = () => {
  const result = new PoseEvaluation(canonicalSkeleton);
  result.apply(restPose());
  return result;
};

describe('rigid two-hand equipment attachment', () => {
  it('uses the authored equipment sockets and exposes a real spacing residual', () => {
    const pose = evaluation();
    const transform = resolveEquipment(pose, [base]).get(base.id)!;
    const fit = measureTwoHandFit(pose, base, transform)!;
    expect(fit.socketSeparation).toBeCloseTo(0.8, 8);
    expect(fit.leftError).toBeCloseTo(fit.rightError, 8);
    expect(fit.leftError).toBeCloseTo(Math.abs(fit.separationError) / 2, 8);
  });

  it('can calibrate socket width to the hands without scaling the rigid item', () => {
    const pose = evaluation();
    const first = resolveEquipment(pose, [base]).get(base.id)!;
    const target = measureTwoHandFit(pose, base, first)!.targetSeparation;
    const calibrated = withTwoHandGripWidth(base, target);
    const transform = resolveEquipment(pose, [calibrated]).get(base.id)!;
    const fit = measureTwoHandFit(pose, calibrated, transform)!;
    expect(fit.leftError).toBeLessThan(1e-8);
    expect(fit.rightError).toBeLessThan(1e-8);
    expect(fit.withinEnvelope).toBe(true);
    expect(transform.matrix.determinant()).toBeCloseTo(1, 8);
  });

  it('applies roll around the grip axis without changing either socket position', () => {
    const pose = evaluation();
    const first = resolveEquipment(pose, [base]).get(base.id)!;
    const target = measureTwoHandFit(pose, base, first)!.targetSeparation;
    const calibrated = withTwoHandGripWidth(base, target);
    if (calibrated.attachment.mode !== 'hands') throw new Error('Expected two-hand attachment');
    const rolled: EquipmentInstance = {
      ...calibrated,
      attachment: { ...calibrated.attachment, gripRoll: 17 },
    };
    const before = resolveEquipment(pose, [calibrated]).get(base.id)!;
    const after = resolveEquipment(pose, [rolled]).get(base.id)!;
    const afterFit = measureTwoHandFit(pose, rolled, after)!;
    expect(afterFit.leftError).toBeLessThan(1e-8);
    expect(afterFit.rightError).toBeLessThan(1e-8);
    expect(after.quaternion.angleTo(before.quaternion)).toBeGreaterThan(0.1);
  });

  it('works from arbitrary hand matrices for preserved-source imported characters', () => {
    const left = new Matrix4().makeTranslation(-0.31, 1.15, 0.22);
    const right = new Matrix4().makeTranslation(0.31, 1.15, 0.22);
    const calibrated = withTwoHandGripWidth(base, 0.62);
    const matrix = twoHandAttachmentMatrix(left, right, calibrated)!;
    const offsets = twoHandGripOffsets(calibrated)!;
    const centre = new Vector3().setFromMatrixPosition(matrix);
    expect(centre.y).toBeCloseTo(1.15 + offsets.left.y, 8);
    expect(centre.z).toBeCloseTo(0.22 + offsets.left.z, 8);
  });
});
