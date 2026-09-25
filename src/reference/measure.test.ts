import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import {
  measureBilateralRotationError,
  measureJointAxis,
  measurePhaseTiming,
  measureRootAxis,
} from './measure';

describe('reference calibration measurements', () => {
  const clip = generateClip(canonicalSkeleton, bicepCurl);

  it('measures joint ranges without knowing the reference envelope', () => {
    const elbow = measureJointAxis(clip, 'forearm_l', 'x');
    expect(elbow.min).toBeCloseTo(16, 6);
    expect(elbow.max).toBeCloseTo(126, 6);
    expect(elbow.excursion).toBeCloseTo(110, 6);

    const grip = measureJointAxis(clip, 'forearm_l', 'y');
    expect(grip.min).toBeCloseTo(72, 6);
    expect(grip.max).toBeCloseTo(80, 6);
  });

  it('measures semantic phase timing', () => {
    const phases = measurePhaseTiming(clip);
    expect(phases.map((phase) => phase.id)).toEqual(['concentric', 'squeeze', 'eccentric', 'reset']);
    expect(phases.reduce((total, phase) => total + phase.fraction, 0)).toBeCloseTo(1, 8);
  });

  it('measures root and bilateral agreement independently', () => {
    const root = measureRootAxis(clip, 'x');
    expect(root.min).toBeCloseTo(0, 8);
    expect(root.max).toBeCloseTo(0, 8);

    const symmetry = measureBilateralRotationError(clip, 'forearm_l', 'forearm_r', 'y');
    expect(symmetry.worst).toBeCloseTo(0, 8);
  });
});
