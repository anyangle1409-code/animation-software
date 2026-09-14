import { useMemo } from 'react';
import { reviewExercise } from '../review';
import { skeleton, useStudio } from '../store';
import { useCharacter } from '../characterStore';

export function ReviewPanel() {
  const document = useStudio((state) => state.document);
  const visualReview = useStudio((state) => state.visualReview);
  const markVisualReview = useStudio((state) => state.markVisualReview);
  const clearVisualReview = useStudio((state) => state.clearVisualReview);
  const sourceId = useCharacter((state) => state.sourceId);
  const sourceStatus = useCharacter((state) => state.sourceStatus);

  const review = useMemo(
    () => reviewExercise(skeleton, document.exercise, document.clip),
    [document],
  );
  const visualPassed =
    visualReview?.document === document && visualReview.characterSourceId === sourceId;
  const approved = review.automatedPass && visualPassed;

  return (
    <section className="panel review-panel">
      <h2>Review</h2>
      <div className={`review-status ${approved ? 'is-approved' : review.automatedPass ? 'is-ready' : 'is-blocked'}`}>
        <strong>{approved ? 'APPROVED' : review.automatedPass ? 'READY FOR VISUAL REVIEW' : 'BLOCKED'}</strong>
        <span>
          {approved
            ? 'Automated gates and visual sign-off both pass for this exact clip and character.'
            : review.automatedPass
              ? 'Measured gates pass. Inspect the full rep before signing it off.'
              : 'One or more measurable authoring gates still fail.'}
        </span>
      </div>

      <div className="review-gates">
        {review.gates.map((gate) => (
          <article key={gate.id} className={gate.passed ? 'is-pass' : 'is-fail'}>
            <div>
              <strong>{gate.label}</strong>
              {gate.applicable === false && <small>not applicable</small>}
            </div>
            <span>{gate.passed ? 'Pass' : 'Block'}</span>
            <p>{gate.detail}</p>
          </article>
        ))}
      </div>

      <h3>Visual sign-off</h3>
      <p className="panel__hint">
        This remains a human decision: normal-speed and slow-motion movement, joint silhouette,
        grip contact, equipment stability and overall naturalness. Any document edit or character
        change invalidates the sign-off automatically.
      </p>
      <div className="button-row">
        <button
          type="button"
          disabled={!review.automatedPass || sourceStatus.kind !== 'idle'}
          className={visualPassed ? 'is-active' : ''}
          onClick={() => (visualPassed ? clearVisualReview() : markVisualReview(sourceId))}
        >
          {visualPassed ? 'Clear visual sign-off' : 'Mark visual review passed'}
        </button>
      </div>
      <p className="panel__note">Automated review sampled {review.sampledFrames} frames.</p>
    </section>
  );
}
