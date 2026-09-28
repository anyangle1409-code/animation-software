import type { ObservableStore } from '../../core/observableStore';
import type { StudioClip } from '../../animation/clip';
import { studioStore, type StudioState } from '../storeCore';

type TechniqueStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface TechniqueValidationScheduler {
  schedule(callback: () => void, delayMs: number): unknown;
  cancel(handle: unknown): void;
}

const browserScheduler: TechniqueValidationScheduler = {
  schedule(callback, delayMs) {
    return globalThis.setTimeout(callback, delayMs);
  },
  cancel(handle) {
    globalThis.clearTimeout(handle as ReturnType<typeof setTimeout>);
  },
};

export interface TechniquePanelElements {
  status: HTMLDivElement;
  ruleList: HTMLUListElement;
  errorList: HTMLUListElement;
}

export interface TechniquePanelDom {
  element: HTMLElement;
  elements: TechniquePanelElements;
  dispose(): void;
}

export function describeTechniqueRule(
  rule: { kind: string } & Record<string, unknown>,
): string {
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

/**
 * React-free Technique panel. It mirrors the current panel's 120 ms validation
 * debounce while rendering directly from the framework-neutral Studio store.
 */
export function createTechniquePanelDom(
  documentRef: Pick<Document, 'createElement'> = document,
  store: TechniqueStorePort = studioStore,
  scheduler: TechniqueValidationScheduler = browserScheduler,
): TechniquePanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'technique-first-party';

  const heading = documentRef.createElement('h2');
  heading.textContent = 'Technique';

  const status = documentRef.createElement('div');
  const ruleList = documentRef.createElement('ul');
  ruleList.className = 'rule-list';

  const errorsHeading = documentRef.createElement('h3');
  errorsHeading.textContent = 'Common errors';
  const errorList = documentRef.createElement('ul');
  errorList.className = 'error-list';

  root.append(heading, status, ruleList, errorsHeading, errorList);

  let pending: unknown = null;
  let validationClip: StudioClip | null = null;
  let renderedExercise: StudioState['document']['exercise'] | null = null;
  let renderedValidation: StudioState['validation'] | undefined;

  const cancelPending = () => {
    if (pending === null) return;
    scheduler.cancel(pending);
    pending = null;
  };

  const scheduleValidation = (state: StudioState) => {
    if (state.document.clip === validationClip) return;
    validationClip = state.document.clip;
    cancelPending();
    pending = scheduler.schedule(() => {
      pending = null;
      store.getState().runValidation();
    }, 120);
  };

  const render = (state: StudioState) => {
    const exercise = state.document.exercise;
    const validation = state.validation;

    status.hidden = !validation;
    status.className = validation
      ? `status ${validation.violations.length === 0 ? 'is-ok' : 'is-warn'}`
      : 'status';
    status.textContent = validation
      ? validation.violations.length === 0
        ? `All ${exercise.technique.length} rules pass across ${validation.frames} sampled frames.`
        : `${validation.violations.length} of ${exercise.technique.length} rules break.`
      : '';

    if (validation) {
      const loopRow = documentRef.createElement('div');
      loopRow.className = 'status__row';
      loopRow.textContent = `Loop closes: ${validation.loopClosed ? 'yes' : 'no'}`;
      status.append(loopRow);

      if (validation.unreachable.length > 0) {
        const unreachableRow = documentRef.createElement('div');
        unreachableRow.className = 'status__row';
        unreachableRow.textContent = `${validation.unreachable.length} frames have an IK target the body cannot reach.`;
        status.append(unreachableRow);
      }
    }

    const failing = new Map(
      validation?.violations.map((entry) => [entry.ruleId, entry]) ?? [],
    );
    const rules: HTMLLIElement[] = [];
    for (const rule of exercise.technique) {
      const violation = failing.get(rule.id);
      const item = documentRef.createElement('li');
      item.className = violation ? 'is-failing' : 'is-passing';

      const dot = documentRef.createElement('span');
      dot.className = 'rule-list__dot';

      const body = documentRef.createElement('div');
      const label = documentRef.createElement('div');
      label.className = 'rule-list__label';
      label.textContent = rule.label;
      const detail = documentRef.createElement('div');
      detail.className = 'rule-list__detail';
      detail.textContent = violation
        ? `${violation.message} at ${violation.time.toFixed(2)}s`
        : describeTechniqueRule(rule as { kind: string } & Record<string, unknown>);
      body.append(label, detail);
      item.append(dot, body);
      rules.push(item);
    }
    ruleList.replaceChildren(...rules);

    const errors: HTMLLIElement[] = [];
    for (const error of exercise.commonErrors) {
      const item = documentRef.createElement('li');
      const label = documentRef.createElement('strong');
      label.textContent = error.label;
      const description = documentRef.createElement('div');
      description.textContent = error.description;
      const correction = documentRef.createElement('div');
      correction.className = 'error-list__fix';
      correction.textContent = error.correction;
      item.append(label, description, correction);
      errors.push(item);
    }
    errorList.replaceChildren(...errors);
  };

  const sync = () => {
    const state = store.getState();
    scheduleValidation(state);
    if (
      state.document.exercise !== renderedExercise ||
      state.validation !== renderedValidation
    ) {
      renderedExercise = state.document.exercise;
      renderedValidation = state.validation;
      render(state);
    }
  };

  const unsubscribe = store.subscribe(sync);
  sync();

  let disposed = false;
  return {
    element: root,
    elements: { status, ruleList, errorList },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      cancelPending();
    },
  };
}
