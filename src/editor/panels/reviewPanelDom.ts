import type { ObservableStore } from '../../core/observableStore';
import { boneLabel, type BoneName } from '../../rig/boneNames';
import {
  characterStore,
  type CharacterState,
} from '../characterStoreCore';
import {
  measureBilateralMotionSymmetry,
  measureJointMotion,
  measureJointPath,
  measureJointTransitions,
} from '../motionDiagnostics';
import { reviewExercise, type ExerciseReview } from '../review';
import {
  skeleton,
  studioStore,
  type StudioDocument,
  type StudioState,
} from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type StudioPort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;
type CharacterPort = Pick<ObservableStore<CharacterState>, 'getState' | 'subscribe'>;

export interface ReviewPanelDom {
  element: HTMLElement;
  dispose(): void;
}

interface MovementReview {
  bone: BoneName;
  motion: ReturnType<typeof measureJointMotion>;
  transitions: ReturnType<typeof measureJointTransitions>;
  bilateral: ReturnType<typeof measureBilateralMotionSymmetry>;
  path: ReturnType<typeof measureJointPath>;
}

const element = (
  documentRef: DocumentPort,
  tag: string,
  className?: string,
  text?: string,
): HTMLElement => {
  const node = documentRef.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const reviewButton = (
  documentRef: DocumentPort,
  label: string,
  control: string,
  action: () => void,
): HTMLButtonElement => {
  const button = documentRef.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.dataset.hgptReviewControl = control;
  button.addEventListener('click', action);
  return button;
};

const spec = (
  documentRef: DocumentPort,
  list: HTMLDListElement,
  label: string,
  value: string,
): void => {
  const term = documentRef.createElement('dt');
  term.textContent = label;
  const detail = documentRef.createElement('dd');
  detail.textContent = value;
  list.append(term, detail);
};

/**
 * React-free review surface. The expensive deterministic review/motion scans
 * are cached by document/clip identity, matching the old React useMemo
 * semantics while playback and sign-off state continue to update live.
 */
export function createReviewPanelDom(
  documentRef: DocumentPort = document,
  studio: StudioPort = studioStore,
  characters: CharacterPort = characterStore,
): ReviewPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel review-panel';
  root.dataset.hgptPanel = 'review-first-party';

  let cachedDocument: StudioDocument | null = null;
  let cachedReview: ExerciseReview | null = null;
  let cachedMovementClip: StudioDocument['clip'] | null = null;
  let cachedMovementBone: BoneName | null = null;
  let cachedMovement: MovementReview | null = null;
  let disposed = false;

  const reviewFor = (document: StudioDocument): ExerciseReview => {
    if (cachedDocument !== document || !cachedReview) {
      cachedDocument = document;
      cachedReview = reviewExercise(skeleton, document.exercise, document.clip);
    }
    return cachedReview;
  };

  const movementFor = (
    document: StudioDocument,
    bone: BoneName | null,
  ): MovementReview | null => {
    if (!bone) {
      cachedMovementClip = document.clip;
      cachedMovementBone = null;
      cachedMovement = null;
      return null;
    }
    if (
      cachedMovementClip !== document.clip ||
      cachedMovementBone !== bone ||
      !cachedMovement
    ) {
      cachedMovementClip = document.clip;
      cachedMovementBone = bone;
      cachedMovement = {
        bone,
        motion: measureJointMotion(document.clip, bone),
        transitions: measureJointTransitions(document.clip, bone),
        bilateral: measureBilateralMotionSymmetry(document.clip, skeleton, bone),
        path: measureJointPath(document.clip, skeleton, bone),
      };
    }
    return cachedMovement;
  };

  const render = () => {
    if (disposed) return;
    const state = studio.getState();
    const character = characters.getState();
    const document = state.document;
    const review = reviewFor(document);
    const visualPassed =
      state.visualReview?.document === document &&
      state.visualReview.characterSourceId === character.sourceId &&
      state.visualReview.deformationRevision === character.deformationRevision;
    const approved = review.automatedPass && visualPassed && character.correctivesPreview;
    const reviewBone: BoneName | null =
      state.selection.bone ??
      (document.exercise.id === 'dumbbell_bicep_curl' ? 'forearm_l' : null);
    const movement = movementFor(document, reviewBone);

    const children: HTMLElement[] = [element(documentRef, 'h2', undefined, 'Review')];

    const status = element(
      documentRef,
      'div',
      `review-status ${approved ? 'is-approved' : review.automatedPass ? 'is-ready' : 'is-blocked'}`,
    );
    status.append(
      element(
        documentRef,
        'strong',
        undefined,
        approved
          ? 'APPROVED'
          : review.automatedPass
            ? 'READY FOR VISUAL REVIEW'
            : 'BLOCKED',
      ),
      element(
        documentRef,
        'span',
        undefined,
        approved
          ? 'Automated gates and visual sign-off both pass for this exact clip and character.'
          : review.automatedPass
            ? 'Measured gates pass. Inspect the full rep before signing it off.'
            : 'One or more measurable authoring gates still fail.',
      ),
    );
    children.push(status);

    const gates = element(documentRef, 'div', 'review-gates');
    for (const gate of review.gates) {
      const card = element(
        documentRef,
        'article',
        gate.passed ? 'is-pass' : 'is-fail',
      );
      const head = documentRef.createElement('div');
      head.append(element(documentRef, 'strong', undefined, gate.label));
      if (gate.applicable === false) {
        head.append(element(documentRef, 'small', undefined, 'not applicable'));
      }
      card.append(
        head,
        element(documentRef, 'span', undefined, gate.passed ? 'Pass' : 'Block'),
        element(documentRef, 'p', undefined, gate.detail),
      );
      gates.append(card);
    }
    children.push(gates, element(documentRef, 'h3', undefined, 'Movement review'));

    if (movement) {
      const diagnostic = element(documentRef, 'div', 'joint-motion-diagnostic');
      const hint = element(documentRef, 'p', 'panel__hint');
      const prefix = documentRef.createElement('span');
      prefix.textContent = 'Reviewing ';
      const strong = element(documentRef, 'strong', undefined, boneLabel(movement.bone));
      const suffix = documentRef.createElement('span');
      suffix.textContent =
        !state.selection.bone && document.exercise.id === 'dumbbell_bicep_curl'
          ? ' — default elbow review joint for the dumbbell curl. These values locate frames for visual inspection; they do not add automatic approval thresholds.'
          : '. These values locate frames for visual inspection; they do not add automatic approval thresholds.';
      hint.append(prefix, strong, suffix);

      const specs = documentRef.createElement('dl');
      specs.className = 'spec-list';
      spec(
        documentRef,
        specs,
        'Highest angular speed',
        `${movement.motion.maxSpeed.value.toFixed(1)}°/s · ${movement.motion.maxSpeed.time.toFixed(2)}s`,
      );
      spec(
        documentRef,
        specs,
        'Highest angular acceleration',
        `${movement.motion.maxAcceleration.value.toFixed(0)}°/s² · ${movement.motion.maxAcceleration.time.toFixed(2)}s`,
      );
      spec(
        documentRef,
        specs,
        'Largest keyframe velocity jump',
        movement.transitions.maxJump
          ? `${movement.transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${movement.transitions.maxJump.time.toFixed(2)}s`
          : '—',
      );
      if (movement.bilateral) {
        spec(
          documentRef,
          specs,
          'Bilateral mirror mismatch',
          `${movement.bilateral.maxError.value.toFixed(2)}° max · ${movement.bilateral.rmsErrorDeg.toFixed(2)}° RMS · ${movement.bilateral.maxError.time.toFixed(2)}s`,
        );
      }
      if (movement.path) {
        spec(
          documentRef,
          specs,
          'Joint drift from parent',
          `${(movement.path.maxDriftMetres * 1000).toFixed(1)} mm · ${movement.path.maxDriftTime.toFixed(2)}s`,
        );
        spec(
          documentRef,
          specs,
          'Return error',
          `${(movement.path.returnErrorMetres * 1000).toFixed(1)} mm`,
        );
      }

      const actions = element(documentRef, 'div', 'button-row');
      actions.append(
        reviewButton(documentRef, 'Focus review joint', 'focus', () => {
          studio.getState().selectBone(movement.bone);
          studio.getState().setCamera('focus');
        }),
        reviewButton(documentRef, 'Sharpest change', 'sharpest', () => {
          studio.getState().setTime(movement.motion.maxAcceleration.time);
        }),
      );
      if (movement.transitions.maxJump) {
        actions.append(
          reviewButton(documentRef, 'Worst transition', 'transition', () => {
            studio.getState().setTime(movement.transitions.maxJump!.time);
          }),
        );
      }
      if (movement.bilateral) {
        actions.append(
          reviewButton(documentRef, 'Worst bilateral mismatch', 'bilateral', () => {
            studio.getState().setTime(movement.bilateral!.maxError.time);
          }),
        );
      }
      if (movement.path) {
        actions.append(
          reviewButton(documentRef, 'Maximum joint drift', 'drift', () => {
            studio.getState().setTime(movement.path!.maxDriftTime);
          }),
        );
      }
      diagnostic.append(hint, specs, actions);
      children.push(diagnostic);
    } else {
      children.push(
        element(
          documentRef,
          'p',
          'panel__empty',
          'Select a joint in the viewport or Joint workspace to add movement diagnostics to this review.',
        ),
      );
    }

    children.push(
      element(documentRef, 'h3', undefined, 'Visual sign-off'),
      element(
        documentRef,
        'p',
        'panel__hint',
        'This remains a human decision: normal-speed and slow-motion movement, joint silhouette, grip contact, equipment stability and overall naturalness. Any document edit, character change or export-aware deformation tuning change invalidates the sign-off automatically. Raw skinning is diagnostic only and cannot be signed off because export uses production correctives.',
      ),
    );

    const signoffRow = element(documentRef, 'div', 'button-row');
    const signoff = reviewButton(
      documentRef,
      visualPassed ? 'Clear visual sign-off' : 'Mark visual review passed',
      'visual-signoff',
      () => {
        if (visualPassed) studio.getState().clearVisualReview();
        else {
          studio
            .getState()
            .markVisualReview(character.sourceId, character.deformationRevision);
        }
      },
    );
    signoff.disabled =
      !review.automatedPass ||
      character.sourceStatus.kind !== 'idle' ||
      !character.correctivesPreview;
    signoff.className = visualPassed ? 'is-active' : '';
    signoffRow.append(signoff);
    children.push(signoffRow);

    if (!character.correctivesPreview) {
      children.push(
        element(
          documentRef,
          'p',
          'panel__note',
          'Enable Correctives on before production visual sign-off.',
        ),
      );
    }
    children.push(
      element(
        documentRef,
        'p',
        'panel__note',
        `Automated review sampled ${review.sampledFrames} frames.`,
      ),
    );

    root.replaceChildren(...children);
  };

  const unsubscribeStudio = studio.subscribe(render);
  const unsubscribeCharacter = characters.subscribe(render);
  render();

  return {
    element: root,
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribeStudio();
      unsubscribeCharacter();
    },
  };
}
