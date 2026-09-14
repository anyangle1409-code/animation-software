import { useMemo } from 'react';
import { reviewExercise } from '../review';
import { skeleton, useStudio } from '../store';
import { useCharacter } from '../characterStore';
import { boneLabel, type BoneName } from '../../rig/boneNames';
import {
  measureBilateralMotionSymmetry,
  measureJointMotion,
  measureJointPath,
  measureJointTransitions,
} from '../motionDiagnostics';

export function ReviewPanel() {
  const document = useStudio((state) => state.document);
  const visualReview = useStudio((state) => state.visualReview);
  const markVisualReview = useStudio((state) => state.markVisualReview);
  const clearVisualReview = useStudio((state) => state.clearVisualReview);
  const selectedBone = useStudio((state) => state.selection.bone);
  const selectBone = useStudio((state) => state.selectBone);
  const setCamera = useStudio((state) => state.setCamera);
  const setTime = useStudio((state) => state.setTime);
  const sourceId = useCharacter((state) => state.sourceId);
  const sourceStatus = useCharacter((state) => state.sourceStatus);
  const correctivesPreview = useCharacter((state) => state.correctivesPreview);
  const deformationRevision = useCharacter((state) => state.deformationRevision);

  const review = useMemo(
    () => reviewExercise(skeleton, document.exercise, document.clip),
    [document],
  );
  const visualPassed =
    visualReview?.document === document &&
    visualReview.characterSourceId === sourceId &&
    visualReview.deformationRevision === deformationRevision;
  const approved = review.automatedPass && visualPassed && correctivesPreview;
  const reviewBone: BoneName | null =
    selectedBone ?? (document.exercise.id === 'dumbbell_bicep_curl' ? 'forearm_l' : null);
  const movement = useMemo(() => {
    if (!reviewBone) return null;
    return {
      bone: reviewBone,
      motion: measureJointMotion(document.clip, reviewBone),
      transitions: measureJointTransitions(document.clip, reviewBone),
      bilateral: measureBilateralMotionSymmetry(document.clip, skeleton, reviewBone),
      path: measureJointPath(document.clip, skeleton, reviewBone),
    };
  }, [document.clip, reviewBone]);

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

      <h3>Movement review</h3>
      {movement ? (
        <div className="joint-motion-diagnostic">
          <p className="panel__hint">
            Reviewing <strong>{boneLabel(movement.bone)}</strong>
            {!selectedBone && document.exercise.id === 'dumbbell_bicep_curl'
              ? ' — default elbow review joint for the dumbbell curl.'
              : '.'}{' '}
            These values locate frames for visual inspection; they do not add automatic approval thresholds.
          </p>
          <dl className="spec-list">
            <dt>Highest angular speed</dt>
            <dd>{movement.motion.maxSpeed.value.toFixed(1)}°/s · {movement.motion.maxSpeed.time.toFixed(2)}s</dd>
            <dt>Highest angular acceleration</dt>
            <dd>{movement.motion.maxAcceleration.value.toFixed(0)}°/s² · {movement.motion.maxAcceleration.time.toFixed(2)}s</dd>
            <dt>Largest keyframe velocity jump</dt>
            <dd>{movement.transitions.maxJump ? `${movement.transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${movement.transitions.maxJump.time.toFixed(2)}s` : '—'}</dd>
            {movement.bilateral && (
              <>
                <dt>Bilateral mirror mismatch</dt>
                <dd>{movement.bilateral.maxError.value.toFixed(2)}° max · {movement.bilateral.rmsErrorDeg.toFixed(2)}° RMS · {movement.bilateral.maxError.time.toFixed(2)}s</dd>
              </>
            )}
            {movement.path && (
              <>
                <dt>Joint drift from parent</dt>
                <dd>{(movement.path.maxDriftMetres * 1000).toFixed(1)} mm · {movement.path.maxDriftTime.toFixed(2)}s</dd>
                <dt>Return error</dt>
                <dd>{(movement.path.returnErrorMetres * 1000).toFixed(1)} mm</dd>
              </>
            )}
          </dl>
          <div className="button-row">
            <button
              type="button"
              onClick={() => {
                selectBone(movement.bone);
                setCamera('focus');
              }}
            >
              Focus review joint
            </button>
            <button type="button" onClick={() => setTime(movement.motion.maxAcceleration.time)}>
              Sharpest change
            </button>
            {movement.transitions.maxJump && (
              <button type="button" onClick={() => setTime(movement.transitions.maxJump!.time)}>
                Worst transition
              </button>
            )}
            {movement.bilateral && (
              <button type="button" onClick={() => setTime(movement.bilateral!.maxError.time)}>
                Worst bilateral mismatch
              </button>
            )}
            {movement.path && (
              <button type="button" onClick={() => setTime(movement.path!.maxDriftTime)}>
                Maximum joint drift
              </button>
            )}
          </div>
        </div>
      ) : (
        <p className="panel__empty">
          Select a joint in the viewport or Joint workspace to add movement diagnostics to this review.
        </p>
      )}

      <h3>Visual sign-off</h3>
      <p className="panel__hint">
        This remains a human decision: normal-speed and slow-motion movement, joint silhouette,
        grip contact, equipment stability and overall naturalness. Any document edit, character
        change or export-aware deformation tuning change invalidates the sign-off automatically. Raw
        skinning is diagnostic only and cannot be signed off because export uses production correctives.
      </p>
      <div className="button-row">
        <button
          type="button"
          disabled={!review.automatedPass || sourceStatus.kind !== 'idle' || !correctivesPreview}
          className={visualPassed ? 'is-active' : ''}
          onClick={() =>
            visualPassed
              ? clearVisualReview()
              : markVisualReview(sourceId, deformationRevision)
          }
        >
          {visualPassed ? 'Clear visual sign-off' : 'Mark visual review passed'}
        </button>
      </div>
      {!correctivesPreview && (
        <p className="panel__note">Enable Correctives on before production visual sign-off.</p>
      )}
      <p className="panel__note">Automated review sampled {review.sampledFrames} frames.</p>
    </section>
  );
}
