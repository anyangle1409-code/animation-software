import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { airSquat } from '../exercises/definitions/airSquat';
import { romanianDeadlift } from '../exercises/definitions/romanianDeadlift';
import { bentOverRow } from '../exercises/definitions/bentOverRow';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { evaluateReference } from './evaluate';
import type { ReferenceSpec } from './types';

const evaluate = (exercise: typeof airSquat, checks: ReferenceSpec['checks']) =>
  evaluateReference(
    {
      schemaVersion: 1,
      id: 'test.reference.v1',
      referenceVersion: 1,
      family: 'squat',
      status: 'draft',
      applicability: {},
      provenance: 'unit-test-only',
      checks,
    },
    exercise,
    generateClip(canonicalSkeleton, exercise),
    { rig: canonicalSkeleton, samples: 101 },
  );

describe('body-relative reference checks', () => {
  it('measures normalized root position at squat depth', () => {
    const report = evaluate(airSquat, [
      {
        kind: 'rootPositionEnvelope',
        id: 'root_depth',
        label: 'Root descends',
        axis: 'y',
        phases: ['bottom'],
        normalizeBy: 'standingHeight',
        envelope: { min: -0.4, max: -0.1 },
      },
    ]);
    expect(report.failed).toEqual([]);
    expect(report.skipped).toEqual([]);
  });

  it('measures relative body landmarks in normalized units', () => {
    const report = evaluateReference(
      {
        schemaVersion: 1,
        id: 'test.hinge.v1',
        referenceVersion: 1,
        family: 'hinge',
        status: 'draft',
        applicability: {},
        provenance: 'unit-test-only',
        checks: [
          {
            kind: 'relativeLandmarkEnvelope',
            id: 'hips_back',
            label: 'Hips travel behind the front foot',
            point: 'pelvis',
            relativeTo: 'foot_l',
            axis: 'z',
            phases: ['bottom'],
            normalizeBy: 'standingHeight',
            envelope: { min: -0.2, max: -0.04 },
          },
        ],
      },
      romanianDeadlift,
      generateClip(canonicalSkeleton, romanianDeadlift),
      { rig: canonicalSkeleton, samples: 101 },
    );
    expect(report.failed).toEqual([]);
  });

  it('measures segment angle to the world vertical', () => {
    const report = evaluateReference(
      {
        schemaVersion: 1,
        id: 'test.hinge.angle.v1',
        referenceVersion: 1,
        family: 'hinge',
        status: 'draft',
        applicability: {},
        provenance: 'unit-test-only',
        checks: [
          {
            kind: 'segmentAngleEnvelope',
            id: 'hinge_depth',
            label: 'Torso is well hinged',
            bone: 'spine_02',
            worldAxis: 'y',
            phases: ['bottom'],
            envelope: { min: 50, max: 90 },
          },
        ],
      },
      romanianDeadlift,
      generateClip(canonicalSkeleton, romanianDeadlift),
      { rig: canonicalSkeleton, samples: 101 },
    );
    expect(report.failed).toEqual([]);
  });

  it('detects a landmark that should remain stationary', () => {
    const report = evaluateReference(
      {
        schemaVersion: 1,
        id: 'test.row.still.v1',
        referenceVersion: 1,
        family: 'row',
        status: 'draft',
        applicability: {},
        provenance: 'unit-test-only',
        checks: [
          {
            kind: 'landmarkStationary',
            id: 'torso_still',
            label: 'Upper torso stays still',
            bone: 'spine_03',
            normalizeBy: 'standingHeight',
            tolerance: 0.01,
          },
        ],
      },
      bentOverRow,
      generateClip(canonicalSkeleton, bentOverRow),
      { rig: canonicalSkeleton, samples: 101 },
    );
    expect(report.failed).toEqual([]);
  });

  it('measures normalized landmark separation', () => {
    const report = evaluateReference(
      {
        schemaVersion: 1,
        id: 'test.curl.width.v1',
        referenceVersion: 1,
        family: 'curl',
        status: 'draft',
        applicability: {},
        provenance: 'unit-test-only',
        checks: [
          {
            kind: 'landmarkDistanceEnvelope',
            id: 'hand_width',
            label: 'Hands remain within a useful width',
            from: 'hand_l',
            to: 'hand_r',
            axis: 'x',
            normalizeBy: 'shoulderWidth',
            envelope: { min: 0.5, max: 2.5 },
          },
        ],
      },
      bicepCurl,
      generateClip(canonicalSkeleton, bicepCurl),
      { rig: canonicalSkeleton, samples: 101 },
    );
    expect(report.failed).toEqual([]);
  });

  it('reports an impossible normalized root envelope as a failure', () => {
    const report = evaluate(airSquat, [
      {
        kind: 'rootPositionEnvelope',
        id: 'impossible',
        label: 'Impossible root',
        axis: 'y',
        phases: ['bottom'],
        normalizeBy: 'standingHeight',
        envelope: { min: 0.5, max: 0.8 },
      },
    ]);
    expect(report.failed).toEqual(['impossible']);
  });
});
