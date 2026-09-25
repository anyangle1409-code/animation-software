import { useGeneration } from '../generationStore';
import type { Candidate } from '../generationStore';
import type { GenerationStatus } from '../../generation/generate';
import { CHECK_LABELS } from '../../generation/validate';
import type { CheckId } from '../../generation/validate';

const EXAMPLES = [
  'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.',
  'Create an incline dumbbell curl at 45 degrees with 8 kg dumbbells.',
  'Create a seated dumbbell shoulder press with 10 kg dumbbells.',
];

const STATUS: Record<GenerationStatus, { label: string; tone: string; note: string }> = {
  passed: {
    label: 'READY FOR REVIEW',
    tone: 'is-ready',
    note: 'Every automatic check passes. Watch the full repetition before approving it.',
  },
  unverified: {
    label: 'UNVERIFIED',
    tone: 'is-blocked',
    note: 'No failures, but the body checks could not run without the production character.',
  },
  failed: {
    label: 'FAILED',
    tone: 'is-blocked',
    note: 'Checks still fail after the bounded correction loop. The failures are listed below.',
  },
  blocked: {
    label: 'NEEDS A DECISION',
    tone: 'is-blocked',
    note: 'The request cannot be built as asked. Nothing was generated.',
  },
};

/** The variant as the source a definition file would pass to its family builder. */
function variantSource(candidate: Candidate): string {
  const { result } = candidate;
  if (!result.variant || !result.family) return '';
  return `${result.family.builder}(${JSON.stringify(result.variant, null, 2)})`;
}

function CandidateDetail({ candidate }: { candidate: Candidate }) {
  const { result } = candidate;
  const preview = useGeneration((state) => state.preview);
  const approve = useGeneration((state) => state.approve);
  const discard = useGeneration((state) => state.discard);
  const status = STATUS[result.status];

  return (
    <div className="generate-candidate">
      <div className={`review-status ${candidate.approved ? 'is-approved' : status.tone}`}>
        <strong>{candidate.approved ? 'APPROVED FOR PROMOTION' : status.label}</strong>
        <span>
          {candidate.approved
            ? 'Approved for this session. Adding it to the library is still a code change: the variant below, in a definition file.'
            : status.note}
        </span>
      </div>

      {result.exercise && (
        <p className="panel__note">
          <strong>{result.exercise.name}</strong> — built by the {result.family?.label.toLowerCase()} family, checked
          against the library's <code>{result.reference}</code>
          {result.report?.character ? ` on ${result.report.character}` : ''}. {result.validations} validation
          {result.validations === 1 ? '' : 's'}.
        </p>
      )}

      {result.parsed.issues.length > 0 && (
        <>
          <h3>Why</h3>
          <ul className="plain-list generate-issues">
            {result.parsed.issues.map((issue) => (
              <li key={issue.code + issue.message}>{issue.message}</li>
            ))}
          </ul>
        </>
      )}

      {result.intent && (
        <>
          <h3>Understood as</h3>
          <dl className="spec-list">
            <dt>Family</dt>
            <dd>{result.family?.label}</dd>
            {result.intent.grip && (
              <>
                <dt>Grip</dt>
                <dd>{result.intent.grip}</dd>
              </>
            )}
            <dt>Support</dt>
            <dd>
              {result.intent.support}
              {result.intent.benchAngle ? `, ${result.intent.benchAngle}°` : ''}
              {result.intent.step ? `, stepping ${result.intent.step}` : ''}
            </dd>
            {result.intent.equipment === 'dumbbell' ? (
              <>
                <dt>Load</dt>
                <dd>{result.intent.load} kg per hand</dd>
              </>
            ) : (
              <>
                <dt>Equipment</dt>
                <dd>Bodyweight</dd>
              </>
            )}
            <dt>Tempo</dt>
            <dd>
              {'explicit' in result.intent.tempo
                ? Object.values(result.intent.tempo.explicit).join('-')
                : result.intent.tempo.profile === 'family'
                  ? "family's own"
                  : result.intent.tempo.profile}
            </dd>
          </dl>
          {result.parsed.assumptions.length > 0 && (
            <>
              <h3>Assumed</h3>
              <ul className="plain-list">
                {result.parsed.assumptions.map((assumption) => (
                  <li key={assumption}>{assumption}</li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      {result.initial && (
        <>
          <h3>Corrections</h3>
          {result.corrections.length === 0 ? (
            <p className="panel__note">
              {result.initial.failed.length === 0 ? 'None needed: it passed on the first validation.' : 'No lever could resolve the failures.'}
            </p>
          ) : (
            <ul className="plain-list">
              {result.corrections.map((correction) => (
                <li key={correction}>{correction}</li>
              ))}
            </ul>
          )}
          {result.initial.failed.length > 0 && (
            <details className="generate-attempts">
              <summary>
                First validation failed: {result.initial.failed.map((check) => CHECK_LABELS[check].toLowerCase()).join(', ')}.{' '}
                {result.attempts.length} attempt
                {result.attempts.length === 1 ? '' : 's'}
              </summary>
              <ol>
                {result.attempts.map((attempt, index) => (
                  <li key={index}>
                    {attempt.label} {attempt.from}° → {attempt.to}°: {attempt.outcome}
                    {Object.entries(attempt.measured).map(([check, measured]) => (
                      <span key={check}>
                        {' '}
                        · {CHECK_LABELS[check as CheckId].toLowerCase()} {((measured as number) * 1000).toFixed(2)} mm
                      </span>
                    ))}
                  </li>
                ))}
              </ol>
            </details>
          )}
        </>
      )}

      {result.report && (
        <>
          <h3>Checks</h3>
          <div className="review-gates">
            {result.report.checks.map((check) => (
              <article key={check.id} className={check.status === 'pass' ? 'is-pass' : 'is-fail'}>
                <div>
                  <strong>{check.label}</strong>
                </div>
                <span>{check.status === 'pass' ? 'Pass' : check.status === 'skipped' ? 'Not run' : 'Fail'}</span>
                <p>{check.detail}</p>
              </article>
            ))}
          </div>
        </>
      )}

      {result.referenceQA && (
        <>
          <h3>Independent reference QA</h3>
          <p className="panel__note">
            Draft offline reference <code>{result.referenceQA.referenceId}</code>. This evidence does not change the
            generator's PASS/FAIL or approval state yet.
          </p>
          <div className="review-gates">
            {result.referenceQA.checks.map((check) => (
              <article key={check.id} className={check.status === 'pass' ? 'is-pass' : 'is-fail'}>
                <div>
                  <strong>{check.label}</strong>
                </div>
                <span>{check.status === 'pass' ? 'Pass' : check.status === 'skip' ? 'Not run' : 'Review'}</span>
                <p>{check.detail}</p>
              </article>
            ))}
          </div>
        </>
      )}

      {result.variant && (
        <details className="generate-source">
          <summary>Generated source</summary>
          <pre>{variantSource(candidate)}</pre>
        </details>
      )}

      <div className="button-row">
        {result.exercise && (
          <button type="button" onClick={() => preview(candidate.key)}>
            Preview
          </button>
        )}
        {result.status === 'passed' && !candidate.approved && (
          <button type="button" className="primary" onClick={() => approve(candidate.key)}>
            Approve
          </button>
        )}
        <button type="button" onClick={() => discard(candidate.key)}>
          Discard
        </button>
      </div>
    </div>
  );
}

export function GeneratePanel() {
  const prompt = useGeneration((state) => state.prompt);
  const setPrompt = useGeneration((state) => state.setPrompt);
  const generate = useGeneration((state) => state.generate);
  const running = useGeneration((state) => state.running);
  const progress = useGeneration((state) => state.progress);
  const candidates = useGeneration((state) => state.candidates);
  const selected = useGeneration((state) => state.selected);
  const preview = useGeneration((state) => state.preview);
  const current = candidates.find((candidate) => candidate.key === selected) ?? null;

  return (
    <section className="panel generate-panel">
      <h2>Generate</h2>
      <p className="panel__hint">
        Describe an exercise. It is built from a certified movement family, validated, corrected where a bounded fix
        exists, and opened for review. Candidates stay in this session; nothing is added to the library.
      </p>
      <form
        className="generate-form"
        onSubmit={(event) => {
          event.preventDefault();
          void generate();
        }}
      >
        <textarea
          value={prompt}
          rows={3}
          aria-label="Exercise request"
          onChange={(event) => setPrompt(event.target.value)}
          disabled={running}
        />
        <div className="button-row">
          <button type="submit" className="primary" disabled={running || !prompt.trim()}>
            {running ? 'Generating…' : 'Generate'}
          </button>
        </div>
      </form>
      <div className="generate-examples">
        {EXAMPLES.map((example) => (
          <button key={example} type="button" disabled={running} onClick={() => setPrompt(example)}>
            {example.replace(/^Create an? /, '').replace(/\.$/, '')}
          </button>
        ))}
      </div>

      {running && (
        <ol className="generate-progress">
          {progress.slice(-4).map((line, index) => (
            <li key={index}>{line}</li>
          ))}
        </ol>
      )}

      {current && <CandidateDetail candidate={current} />}

      {candidates.length > 1 && (
        <>
          <h3>This session</h3>
          <ul className="plain-list generate-list">
            {candidates.map((candidate) => (
              <li key={candidate.key}>
                <button
                  type="button"
                  className={candidate.key === selected ? 'is-active' : ''}
                  onClick={() => (candidate.result.exercise ? preview(candidate.key) : useGeneration.setState({ selected: candidate.key }))}
                >
                  {candidate.result.exercise?.name ?? candidate.prompt} · {STATUS[candidate.result.status].label.toLowerCase()}
                  {candidate.approved ? ' · approved' : ''}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
