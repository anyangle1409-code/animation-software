import type { ObservableStore } from '../../core/observableStore';
import { repetitionDuration, type Tempo } from '../../exercises/types';
import { ACTIVATION_STYLES } from '../../muscles/activation';
import { MUSCLE_GROUPS } from '../../muscles/groups';
import { studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type ExerciseStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface ExercisePanelDom {
  element: HTMLElement;
  dispose(): void;
}

const TEMPO_FIELDS: ReadonlyArray<{ key: keyof Tempo; label: string }> = [
  { key: 'eccentric', label: 'Eccentric (lower)' },
  { key: 'pauseStretched', label: 'Pause stretched' },
  { key: 'concentric', label: 'Concentric (lift)' },
  { key: 'pauseContracted', label: 'Pause contracted' },
];

const heading = (documentRef: DocumentPort, text: string): HTMLHeadingElement => {
  const element = documentRef.createElement('h3');
  element.textContent = text;
  return element;
};

/** React-free Exercise metadata/editor surface backed by the existing Studio store. */
export function createExercisePanelDom(
  documentRef: DocumentPort = document,
  store: ExerciseStorePort = studioStore,
): ExercisePanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'exercise-first-party';

  const render = () => {
    const exercise = store.getState().document.exercise;
    const children: HTMLElement[] = [];

    const title = documentRef.createElement('h2');
    title.textContent = exercise.name;
    children.push(title);

    if (exercise.description) {
      const description = documentRef.createElement('p');
      description.className = 'panel__note';
      description.textContent = exercise.description;
      children.push(description);
    }

    children.push(heading(documentRef, 'Tempo'));
    const tempoGrid = documentRef.createElement('div');
    tempoGrid.className = 'tempo-grid';
    for (const field of TEMPO_FIELDS) {
      const label = documentRef.createElement('label');
      label.className = 'field';
      const labelText = documentRef.createElement('span');
      labelText.className = 'field__label';
      labelText.textContent = field.label;
      const input = documentRef.createElement('input');
      input.type = 'number';
      input.min = '0';
      input.max = '10';
      input.step = '0.1';
      input.value = String(exercise.tempo[field.key]);
      input.addEventListener('input', () => {
        store.getState().setTempo({ [field.key]: Number(input.value) });
      });
      label.append(labelText, input);
      tempoGrid.append(label);
    }
    children.push(tempoGrid);

    const duration = documentRef.createElement('p');
    duration.className = 'panel__note';
    duration.textContent = `One repetition takes ${repetitionDuration(exercise).toFixed(2)}s.`;
    children.push(duration);

    children.push(heading(documentRef, 'Muscles worked'));
    const muscleList = documentRef.createElement('ul');
    muscleList.className = 'muscle-list';
    for (const level of ['primary', 'secondary', 'stabilisers'] as const) {
      const style = ACTIVATION_STYLES[level === 'stabilisers' ? 'stabiliser' : level];
      for (const group of exercise.muscles[level]) {
        const item = documentRef.createElement('li');
        const swatch = documentRef.createElement('span');
        swatch.className = 'swatch';
        swatch.style.background = style.colour;
        const name = documentRef.createElement('span');
        name.className = 'muscle-list__name';
        name.textContent = MUSCLE_GROUPS[group].label;
        const levelText = documentRef.createElement('span');
        levelText.className = 'muscle-list__level';
        levelText.textContent = style.label;
        item.append(swatch, name, levelText);
        muscleList.append(item);
      }
    }
    children.push(muscleList);

    children.push(heading(documentRef, 'Breathing'));
    const breathing = documentRef.createElement('p');
    breathing.className = 'panel__note';
    breathing.textContent = exercise.breathing.cue;
    children.push(breathing);

    children.push(heading(documentRef, 'Grip and stance'));
    const specs = documentRef.createElement('dl');
    specs.className = 'spec-list';
    const appendSpec = (label: string, value: string): void => {
      const term = documentRef.createElement('dt');
      term.textContent = label;
      const detail = documentRef.createElement('dd');
      detail.textContent = value;
      specs.append(term, detail);
    };
    appendSpec('Grip', `${exercise.hands.grip}, ${exercise.hands.orientation}`);

    const closureTerm = documentRef.createElement('dt');
    closureTerm.textContent = 'Grip closure';
    const closureDetail = documentRef.createElement('dd');
    const closureLabel = documentRef.createElement('label');
    closureLabel.className = 'grip-closure';
    const closureInput = documentRef.createElement('input');
    closureInput.type = 'range';
    closureInput.min = '0';
    closureInput.max = '1';
    closureInput.step = '0.05';
    closureInput.value = String(exercise.hands.closure);
    closureInput.setAttribute('aria-label', 'Grip closure');
    closureInput.addEventListener('input', () => {
      store.getState().setGripClosure(Number(closureInput.value));
    });
    const closureValue = documentRef.createElement('span');
    closureValue.textContent = `${Math.round(exercise.hands.closure * 100)}%`;
    closureLabel.append(closureInput, closureValue);
    closureDetail.append(closureLabel);
    specs.append(closureTerm, closureDetail);

    appendSpec(
      'Hand width',
      exercise.hands.width ? `${(exercise.hands.width * 100).toFixed(0)} cm` : '—',
    );
    appendSpec('Stance width', `${(exercise.feet.width * 100).toFixed(0)} cm`);
    appendSpec('Toe-out', `${exercise.feet.toeOut}°`);
    children.push(specs);

    children.push(heading(documentRef, 'Equipment'));
    const equipment = documentRef.createElement('ul');
    equipment.className = 'plain-list';
    for (const instance of exercise.equipment.instances) {
      const item = documentRef.createElement('li');
      item.textContent =
        `${instance.label ?? instance.kind}${instance.mass ? ` — ${instance.mass} kg` : ''}`;
      equipment.append(item);
    }
    if (exercise.equipment.instances.length === 0) {
      const item = documentRef.createElement('li');
      item.textContent = 'Bodyweight';
      equipment.append(item);
    }
    children.push(equipment);

    root.replaceChildren(...children);
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
    },
  };
}
