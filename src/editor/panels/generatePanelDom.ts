import type { ObservableStore } from '../../core/observableStore';
import type { GenerationStatus } from '../../generation/generate';
import { CHECK_LABELS, type CheckId } from '../../generation/validate';
import {
  generationStore,
  type Candidate,
  type GenerationState,
} from '../generationStoreCore';

type DocumentPort = Pick<Document, 'createElement'>;
type GenerationPort = Pick<
  ObservableStore<GenerationState>,
  'getState' | 'setState' | 'subscribe'
>;

export interface GeneratePanelDom {
  element: HTMLElement;
  dispose(): void;
}

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

const variantSource = (candidate: Candidate): string => {
  const { result } = candidate;
  if (!result.variant || !result.family) return '';
  return `${result.family.builder}(${JSON.stringify(result.variant, null, 2)})`;
};

const node = (
  documentRef: DocumentPort,
  tag: string,
  className?: string,
  text?: string,
): HTMLElement => {
  const element = documentRef.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

const appendText = (
  documentRef: DocumentPort,
  parent: HTMLElement,
  text: string,
): void => {
  const span = documentRef.createElement('span');
  span.textContent = text;
  parent.append(span);
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

const actionButton = (
  documentRef: DocumentPort,
  label: string,
  onClick: () => void,
  control: string,
  className = '',
): HTMLButtonElement => {
  const button = documentRef.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.dataset.hgptGenerateControl = control;
  button.className = className;
  button.addEventListener('click', onClick);
  return button;
};

const candidateDetail = (
  documentRef: DocumentPort,
  candidate: Candidate,
  store: GenerationPort,
): HTMLElement => {
  const { result } = candidate;
  const status = STATUS[result.status];
  const root = node(documentRef, 'div', 'generate-candidate');

  const review = node(
    documentRef,
    'div',
    `review-status ${candidate.approved ? 'is-approved' : status.tone}`,
  );
  review.append(
    node(
      documentRef,
      'strong',
      undefined,
      candidate.approved ? 'APPROVED FOR PROMOTION' : status.label,
    ),
    node(
      documentRef,
      'span',
      undefined,
      candidate.approved
        ? 'Approved for this session. Adding it to the library is still a code change: the variant below, in a definition file.'
        : status.note,
    ),
  );
  root.append(review);

  if (result.exercise) {
    const note = node(documentRef, 'p', 'panel__note');
    note.append(node(documentRef, 'strong', undefined, result.exercise.name));
    appendText(
      documentRef,
      note,
      ` — built by the ${result.family?.label.toLowerCase() ?? ''} family, checked against the library's `,
    );
    note.append(node(documentRef, 'code', undefined, result.reference ?? ''));
    appendText(
      documentRef,
      note,
      `${result.report?.character ? ` on ${result.report.character}` : ''}. ${result.validations} validation${result.validations === 1 ? '' : 's'}.`,
    );
    root.append(note);
  }

  if (result.parsed.issues.length > 0) {
    root.append(node(documentRef, 'h3', undefined, 'Why'));
    const list = node(documentRef, 'ul', 'plain-list generate-issues');
    for (const issue of result.parsed.issues) {
      list.append(node(documentRef, 'li', undefined, issue.message));
    }
    root.append(list);
  }

  if (result.intent) {
    root.append(node(documentRef, 'h3', undefined, 'Understood as'));
    const list = documentRef.createElement('dl');
    list.className = 'spec-list';
    spec(documentRef, list, 'Family', result.family?.label ?? '');
    if (result.intent.grip) spec(documentRef, list, 'Grip', result.intent.grip);
    spec(
      documentRef,
      list,
      'Support',
      `${result.intent.support}${result.intent.benchAngle ? `, ${result.intent.benchAngle}°` : ''}${result.intent.step ? `, stepping ${result.intent.step}` : ''}`,
    );
    if (result.intent.equipment === 'dumbbell') {
      spec(documentRef, list, 'Load', `${result.intent.load} kg per hand`);
    } else {
      spec(documentRef, list, 'Equipment', 'Bodyweight');
    }
    spec(
      documentRef,
      list,
      'Tempo',
      'explicit' in result.intent.tempo
        ? Object.values(result.intent.tempo.explicit).join('-')
        : result.intent.tempo.profile === 'family'
          ? "family's own"
          : result.intent.tempo.profile,
    );
    root.append(list);

    if (result.parsed.assumptions.length > 0) {
      root.append(node(documentRef, 'h3', undefined, 'Assumed'));
      const assumptions = node(documentRef, 'ul', 'plain-list');
      for (const assumption of result.parsed.assumptions) {
        assumptions.append(node(documentRef, 'li', undefined, assumption));
      }
      root.append(assumptions);
    }
  }

  if (result.initial) {
    root.append(node(documentRef, 'h3', undefined, 'Corrections'));
    if (result.corrections.length === 0) {
      root.append(
        node(
          documentRef,
          'p',
          'panel__note',
          result.initial.failed.length === 0
            ? 'None needed: it passed on the first validation.'
            : 'No lever could resolve the failures.',
        ),
      );
    } else {
      const corrections = node(documentRef, 'ul', 'plain-list');
      for (const correction of result.corrections) {
        corrections.append(node(documentRef, 'li', undefined, correction));
      }
      root.append(corrections);
    }

    if (result.initial.failed.length > 0) {
      const details = node(documentRef, 'details', 'generate-attempts');
      const summary = node(
        documentRef,
        'summary',
        undefined,
        `First validation failed: ${result.initial.failed
          .map((check) => CHECK_LABELS[check].toLowerCase())
          .join(', ')}. ${result.attempts.length} attempt${result.attempts.length === 1 ? '' : 's'}`,
      );
      const attempts = documentRef.createElement('ol');
      for (const attempt of result.attempts) {
        const item = documentRef.createElement('li');
        appendText(
          documentRef,
          item,
          `${attempt.label} ${attempt.from}° → ${attempt.to}°: ${attempt.outcome}`,
        );
        for (const [check, measured] of Object.entries(attempt.measured)) {
          appendText(
            documentRef,
            item,
            ` · ${CHECK_LABELS[check as CheckId].toLowerCase()} ${((measured as number) * 1000).toFixed(2)} mm`,
          );
        }
        attempts.append(item);
      }
      details.append(summary, attempts);
      root.append(details);
    }
  }

  if (result.report) {
    root.append(node(documentRef, 'h3', undefined, 'Checks'));
    const gates = node(documentRef, 'div', 'review-gates');
    for (const check of result.report.checks) {
      const card = node(
        documentRef,
        'article',
        check.status === 'pass' ? 'is-pass' : 'is-fail',
      );
      const head = documentRef.createElement('div');
      head.append(node(documentRef, 'strong', undefined, check.label));
      card.append(
        head,
        node(
          documentRef,
          'span',
          undefined,
          check.status === 'pass' ? 'Pass' : check.status === 'skipped' ? 'Not run' : 'Fail',
        ),
        node(documentRef, 'p', undefined, check.detail),
      );
      gates.append(card);
    }
    root.append(gates);
  }

  if (result.variant) {
    const details = node(documentRef, 'details', 'generate-source');
    details.append(
      node(documentRef, 'summary', undefined, 'Generated source'),
      node(documentRef, 'pre', undefined, variantSource(candidate)),
    );
    root.append(details);
  }

  const actions = node(documentRef, 'div', 'button-row');
  if (result.exercise) {
    actions.append(
      actionButton(
        documentRef,
        'Preview',
        () => store.getState().preview(candidate.key),
        `preview-${candidate.key}`,
      ),
    );
  }
  if (result.status === 'passed' && !candidate.approved) {
    actions.append(
      actionButton(
        documentRef,
        'Approve',
        () => store.getState().approve(candidate.key),
        `approve-${candidate.key}`,
        'primary',
      ),
    );
  }
  actions.append(
    actionButton(
      documentRef,
      'Discard',
      () => store.getState().discard(candidate.key),
      `discard-${candidate.key}`,
    ),
  );
  root.append(actions);
  return root;
};

/**
 * React-free Generate surface backed by the framework-neutral generation
 * session store. The prompt/form nodes stay stable while progress and candidate
 * output rerender, preserving typing and focus behavior during async work.
 */
export function createGeneratePanelDom(
  documentRef: DocumentPort = document,
  store: GenerationPort = generationStore,
): GeneratePanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel generate-panel';
  root.dataset.hgptPanel = 'generate-first-party';

  const title = node(documentRef, 'h2', undefined, 'Generate');
  const hint = node(
    documentRef,
    'p',
    'panel__hint',
    'Describe an exercise. It is built from a certified movement family, validated, corrected where a bounded fix exists, and opened for review. Candidates stay in this session; nothing is added to the library.',
  );

  const form = documentRef.createElement('form');
  form.className = 'generate-form';
  const prompt = documentRef.createElement('textarea');
  prompt.rows = 3;
  prompt.setAttribute('aria-label', 'Exercise request');
  prompt.dataset.hgptGenerateControl = 'prompt';
  const buttonRow = node(documentRef, 'div', 'button-row');
  const generate = documentRef.createElement('button');
  generate.type = 'submit';
  generate.className = 'primary';
  generate.dataset.hgptGenerateControl = 'generate';
  buttonRow.append(generate);
  form.append(prompt, buttonRow);

  const examples = node(documentRef, 'div', 'generate-examples');
  const exampleButtons = EXAMPLES.map((example, index) => {
    const button = documentRef.createElement('button');
    button.type = 'button';
    button.dataset.hgptGenerateControl = `example-${index}`;
    button.textContent = example.replace(/^Create an? /, '').replace(/\.$/, '');
    button.addEventListener('click', () => store.getState().setPrompt(example));
    examples.append(button);
    return button;
  });

  const dynamic = node(documentRef, 'div', 'generate-dynamic');
  dynamic.dataset.hgptGenerateRegion = 'dynamic';
  root.append(title, hint, form, examples, dynamic);

  const onPrompt = () => store.getState().setPrompt(prompt.value);
  const onSubmit = (event: Event) => {
    event.preventDefault();
    void store.getState().generate();
  };
  prompt.addEventListener('input', onPrompt);
  form.addEventListener('submit', onSubmit);

  const render = () => {
    const state = store.getState();
    if (prompt.value !== state.prompt) prompt.value = state.prompt;
    prompt.disabled = state.running;
    generate.disabled = state.running || !state.prompt.trim();
    generate.textContent = state.running ? 'Generating…' : 'Generate';
    for (const button of exampleButtons) button.disabled = state.running;

    const children: HTMLElement[] = [];
    if (state.running) {
      const progress = node(documentRef, 'ol', 'generate-progress');
      for (const line of state.progress.slice(-4)) {
        progress.append(node(documentRef, 'li', undefined, line));
      }
      children.push(progress);
    }

    const current =
      state.candidates.find((candidate) => candidate.key === state.selected) ?? null;
    if (current) children.push(candidateDetail(documentRef, current, store));

    if (state.candidates.length > 1) {
      children.push(node(documentRef, 'h3', undefined, 'This session'));
      const list = node(documentRef, 'ul', 'plain-list generate-list');
      for (const candidate of state.candidates) {
        const item = documentRef.createElement('li');
        const button = documentRef.createElement('button');
        button.type = 'button';
        button.className = candidate.key === state.selected ? 'is-active' : '';
        button.dataset.hgptGenerateControl = `session-${candidate.key}`;
        button.textContent =
          `${candidate.result.exercise?.name ?? candidate.prompt} · ${STATUS[candidate.result.status].label.toLowerCase()}${candidate.approved ? ' · approved' : ''}`;
        button.addEventListener('click', () => {
          if (candidate.result.exercise) store.getState().preview(candidate.key);
          else store.setState({ selected: candidate.key });
        });
        item.append(button);
        list.append(item);
      }
      children.push(list);
    }
    dynamic.replaceChildren(...children);
  };

  const unsubscribe = store.subscribe(render);
  render();

  let disposed = false;
  return {
    element: root,
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      prompt.removeEventListener('input', onPrompt);
      form.removeEventListener('submit', onSubmit);
    },
  };
}
