import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { decideAutomaticCertification } from './certification';
import { evaluateReference } from './evaluate';
import { curlReferenceFor } from './specs/curl';

function evidence() {
  const reference = curlReferenceFor(bicepCurl);
  const report = evaluateReference(
    reference,
    bicepCurl,
    generateClip(canonicalSkeleton, bicepCurl),
    { rig: canonicalSkeleton, samples: 101 },
  );
  return { reference, report };
}

describe('automatic certification policy', () => {
  it('never lets a draft reference certify a mechanically passed candidate', () => {
    const { reference, report } = evidence();
    const decision = decideAutomaticCertification({
      mechanicalStatus: 'passed',
      reference,
      report,
      visualStatus: 'draft_evidence',
    });
    expect(decision.eligible).toBe(false);
    expect(decision.status).toBe('reference_draft');
  });

  it.each([
    ['blocked', 'mechanical_blocked'],
    ['failed', 'mechanical_failed'],
    ['unverified', 'mechanical_unverified'],
  ] as const)('mechanical status %s blocks automatic certification first', (mechanicalStatus, status) => {
    const { reference, report } = evidence();
    const decision = decideAutomaticCertification({
      mechanicalStatus,
      reference: { ...reference, status: 'certified' },
      report,
      visualStatus: 'passed',
    });
    expect(decision.eligible).toBe(false);
    expect(decision.status).toBe(status);
  });

  it('requires every certified reference measurement to have run', () => {
    const { reference, report } = evidence();
    const decision = decideAutomaticCertification({
      mechanicalStatus: 'passed',
      reference: { ...reference, status: 'certified' },
      report: { ...report, passed: false, skipped: ['hand_path'] },
      visualStatus: 'passed',
    });
    expect(decision.status).toBe('reference_incomplete');
    expect(decision.eligible).toBe(false);
  });

  it('requires a certified reference pass', () => {
    const { reference, report } = evidence();
    const decision = decideAutomaticCertification({
      mechanicalStatus: 'passed',
      reference: { ...reference, status: 'certified' },
      report: { ...report, passed: false, failed: ['elbow_rom'] },
      visualStatus: 'passed',
    });
    expect(decision.status).toBe('reference_failed');
    expect(decision.eligible).toBe(false);
  });

  it('does not treat advisory visual evidence as a certified visual gate', () => {
    const { reference, report } = evidence();
    const decision = decideAutomaticCertification({
      mechanicalStatus: 'passed',
      reference: { ...reference, status: 'certified' },
      report,
      visualStatus: 'draft_evidence',
    });
    expect(decision.status).toBe('visual_not_certified');
    expect(decision.eligible).toBe(false);
  });

  it('only certifies when mechanical, certified reference and certified visual gates all pass', () => {
    const { reference, report } = evidence();
    const decision = decideAutomaticCertification({
      mechanicalStatus: 'passed',
      reference: { ...reference, status: 'certified' },
      report,
      visualStatus: 'passed',
    });
    expect(decision).toMatchObject({ status: 'certified', eligible: true });
  });
});
