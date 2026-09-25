import type { GenerationStatus } from '../generation/generate';
import type { ReferenceReport, ReferenceSpec } from './types';

export type VisualReviewStatus = 'not_run' | 'draft_evidence' | 'passed' | 'failed';

export type AutomaticCertificationStatus =
  | 'mechanical_blocked'
  | 'mechanical_failed'
  | 'mechanical_unverified'
  | 'reference_draft'
  | 'reference_incomplete'
  | 'reference_failed'
  | 'visual_not_certified'
  | 'visual_failed'
  | 'certified';

export interface AutomaticCertificationInput {
  mechanicalStatus: GenerationStatus;
  reference: ReferenceSpec;
  report: ReferenceReport;
  visualStatus: VisualReviewStatus;
}

export interface AutomaticCertificationDecision {
  status: AutomaticCertificationStatus;
  eligible: boolean;
  reasons: string[];
}

/**
 * Single policy boundary for future automatic certification.
 *
 * This intentionally makes it impossible for a draft reference pack, skipped
 * reference measurement, or advisory visual evidence to promote a generated
 * candidate. Current HOME GYM PT references are draft, so today's expected
 * result is reference_draft.
 *
 * The generator, reference evaluator and visual reviewer remain separate. This
 * function only decides whether all independently certified gates have supplied
 * enough evidence for automatic approval.
 */
export function decideAutomaticCertification(
  input: AutomaticCertificationInput,
): AutomaticCertificationDecision {
  if (input.mechanicalStatus === 'blocked') {
    return {
      status: 'mechanical_blocked',
      eligible: false,
      reasons: ['The request was blocked before a candidate could be validated.'],
    };
  }
  if (input.mechanicalStatus === 'failed') {
    return {
      status: 'mechanical_failed',
      eligible: false,
      reasons: ['Existing mechanical/contact/collision validation still fails.'],
    };
  }
  if (input.mechanicalStatus === 'unverified') {
    return {
      status: 'mechanical_unverified',
      eligible: false,
      reasons: ['Required production-character mechanical checks were not measured.'],
    };
  }

  if (input.reference.status !== 'certified') {
    return {
      status: 'reference_draft',
      eligible: false,
      reasons: [
        `Reference ${input.reference.id} v${input.reference.referenceVersion} is ${input.reference.status}; draft evidence cannot certify a candidate.`,
      ],
    };
  }

  if (input.report.skipped.length > 0) {
    return {
      status: 'reference_incomplete',
      eligible: false,
      reasons: [
        `Independent reference QA did not measure: ${input.report.skipped.join(', ')}.`,
      ],
    };
  }

  if (!input.report.passed || input.report.failed.length > 0) {
    return {
      status: 'reference_failed',
      eligible: false,
      reasons: [
        `Independent reference QA failed: ${input.report.failed.join(', ') || 'one or more checks'}.`,
      ],
    };
  }

  if (input.visualStatus === 'failed') {
    return {
      status: 'visual_failed',
      eligible: false,
      reasons: ['Certified visual/deformation review failed.'],
    };
  }

  if (input.visualStatus !== 'passed') {
    return {
      status: 'visual_not_certified',
      eligible: false,
      reasons: [
        input.visualStatus === 'draft_evidence'
          ? 'Visual evidence exists, but the visual reviewer is not certified for automatic decisions.'
          : 'Certified visual/deformation review has not run.',
      ],
    };
  }

  return {
    status: 'certified',
    eligible: true,
    reasons: ['Mechanical, independent reference and certified visual gates all pass.'],
  };
}
