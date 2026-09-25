import type { ReferenceReport } from './types';

export function formatReferenceReport(report: ReferenceReport): string {
  const header = report.passed ? 'REFERENCE QA: PASS' : 'REFERENCE QA: REVIEW';
  const lines = report.checks.map((check) => {
    const mark = check.status === 'pass' ? 'PASS' : check.status === 'fail' ? 'FAIL' : 'SKIP';
    return `${mark.padEnd(4)}  ${check.label}: ${check.detail}`;
  });
  return [
    header,
    `Reference: ${report.referenceId} v${report.referenceVersion}`,
    `Exercise: ${report.exerciseId}`,
    ...lines,
  ].join('\n');
}
