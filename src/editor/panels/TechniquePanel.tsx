import { useEffect } from 'react';
import { useStudio } from '../store';

/**
 * The exercise's technique rules and how the current clip measures against
 * them. Rules are shown exactly as the definition states them, so what the
 * checker enforces and what the coach reads are the same thing.
 */
export function TechniquePanel() {
  const exercise = useStudio((state) => state.document.exercise);
  const clip = useStudio((state) => state.document.clip);
  const validation = useStudio((state) => state.validation);
  const runValidation = useStudio((state) => state.runValidation);

  useEffect(() => {
    // Re-check whenever the clip changes; it is fast enough to be automatic.
    const handle = window.setTimeout(runValidation, 120);
    return () => window.clearTimeout(handle);
  }, [clip, runValidation]);

  const failing = new Map(validation?.violations.map((entry) => [entry.ruleId, entry]) ?? []);

  return (
    <section className="panel">
      <h2>Technique</h2>

      {validation && (
        <div className={`status ${validation.violations.length === 0 ? 'is-ok' : 'is-warn'}`}>
          {validation.violations.length === 0
            ? `All ${exercise.technique.length} rules pass across ${validation.frames} sampled frames.`
            : `${validation.violations.length} of ${exercise.technique.length} rules break.`}
          <div className="status__row">
            Loop closes: <strong>{validation.loopClosed ? 'yes' : 'no'}</strong>
          </div>
          {validation.unreachable.length > 0 && (
            <div className="status__row">
              {validation.unreachable.length} frames have an IK target the body cannot reach.
            </div>
          )}
        </div>
      )}

      <ul className="rule-list">
        {exercise.technique.map((rule) => {
          const violation = failing.get(rule.id);
          return (
            <li key={rule.id} className={violation ? 'is-failing' : 'is-passing'}>
              <span className="rule-list__dot" />
              <div>
                <div className="rule-list__label">{rule.label}</div>
                <div className="rule-list__detail">
                  {violation
                    ? `${violation.message} at ${violation.time.toFixed(2)}s`
                    : describeRule(rule)}
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      <h3>Common errors</h3>
      <ul className="error-list">
        {exercise.commonErrors.map((error) => (
          <li key={error.id}>
            <strong>{error.label}</strong>
            <div>{error.description}</div>
            <div className="error-list__fix">{error.correction}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}

function describeRule(rule: { kind: string } & Record<string, unknown>): string {
  switch (rule.kind) {
    case 'jointAngle':
      return `${rule.bone} ${String(rule.axis).toUpperCase()} between ${rule.min ?? '−∞'}° and ${rule.max ?? '∞'}°`;
    case 'segmentAngle':
      return `${rule.bone} within ${rule.max ?? '∞'}° of ${rule.reference}`;
    case 'stationary':
      return `stays within ${((rule.tolerance as number) * 100).toFixed(1)} cm of its start`;
    case 'distance':
      return `separation ${(((rule.min as number) ?? 0) * 100).toFixed(0)}–${(((rule.max as number) ?? 0) * 100).toFixed(0)} cm`;
    case 'relativePosition':
      return `offset on ${rule.axis} kept in range`;
    case 'symmetry':
      return `sides match within ${((rule.tolerance as number) * 100).toFixed(1)} cm`;
    case 'alignment':
      return `three points stay in line within ${((rule.tolerance as number) * 100).toFixed(1)} cm`;
    default:
      return '';
  }
}
