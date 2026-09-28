import { EXERCISES, EXERCISE_BY_ID } from '../exercises/library';
import { CAMERA_LABELS } from '../viewer/cameras';
import { CAMERA_PRESET_IDS, type CameraPresetId } from '../viewer/cameraTypes';
import type { StudioState, ViewMode } from './storeCore';
import { studioStore } from './storeCore';

export const TOOLBAR_VIEW_MODES: ReadonlyArray<{ id: ViewMode; label: string }> = [
  { id: 'skeleton', label: 'Skeleton' },
  { id: 'muscles', label: 'Muscles' },
  { id: 'combined', label: 'Combined' },
  { id: 'character', label: 'Character' },
  { id: 'anatomy', label: 'Anatomy' },
];

export const TOOLBAR_BACKDROPS: ReadonlyArray<{
  id: StudioState['backdrop'];
  label: string;
}> = [
  { id: 'studio', label: 'Studio' },
  { id: 'light', label: 'Light' },
  { id: 'void', label: 'Void' },
  { id: 'study', label: 'Study' },
];

export interface ToolbarStoreState {
  document: { exercise: { id: string; name: string } };
  history: { past: readonly unknown[]; future: readonly unknown[] };
  viewMode: ViewMode;
  backdrop: StudioState['backdrop'];
  camera: CameraPresetId;
  loadExercise(id: string): void;
  setViewMode(mode: ViewMode): void;
  setBackdrop(backdrop: StudioState['backdrop']): void;
  setCamera(camera: CameraPresetId): void;
  regenerate(): void;
  undo(): void;
  redo(): void;
}

export interface ToolbarStorePort {
  getState(): ToolbarStoreState;
  subscribe(listener: () => void): () => void;
}

export interface StudioToolbarControls {
  exerciseSelect: HTMLSelectElement;
  viewModes: Record<ViewMode, HTMLButtonElement>;
  backdropSelect: HTMLSelectElement;
  cameraSelect: HTMLSelectElement;
  regenerate: HTMLButtonElement;
  undo: HTMLButtonElement;
  redo: HTMLButtonElement;
}

export interface StudioToolbarDom {
  element: HTMLElement;
  controls: StudioToolbarControls;
  dispose(): void;
}

const appendOption = (
  documentRef: Pick<Document, 'createElement'>,
  select: HTMLSelectElement,
  value: string,
  label: string,
): void => {
  const option = documentRef.createElement('option');
  option.value = value;
  option.textContent = label;
  select.append(option);
};

const createSelectField = (
  documentRef: Pick<Document, 'createElement'>,
  labelText: string,
): { label: HTMLLabelElement; select: HTMLSelectElement } => {
  const label = documentRef.createElement('label');
  label.className = 'field';
  const text = documentRef.createElement('span');
  text.className = 'field__label';
  text.textContent = labelText;
  const select = documentRef.createElement('select');
  label.append(text, select);
  return { label, select };
};

const createButton = (
  documentRef: Pick<Document, 'createElement'>,
  text: string,
  title?: string,
): HTMLButtonElement => {
  const button = documentRef.createElement('button');
  button.type = 'button';
  button.textContent = text;
  if (title) button.title = title;
  return button;
};

/**
 * React-free Toolbar DOM/controller backed directly by the framework-neutral
 * Studio store. It is prepared and parity-tested before replacing Toolbar.tsx.
 */
export function createStudioToolbarDom(
  documentRef: Pick<Document, 'createElement'> = document,
  store: ToolbarStorePort = studioStore,
): StudioToolbarDom {
  const cleanups: Array<() => void> = [];

  const header = documentRef.createElement('header');
  header.className = 'toolbar';
  header.dataset.hgptToolbar = 'first-party';

  const brand = documentRef.createElement('div');
  brand.className = 'toolbar__brand';
  const title = documentRef.createElement('span');
  title.className = 'toolbar__title';
  title.textContent = 'Home Gym PT';
  const subtitle = documentRef.createElement('span');
  subtitle.className = 'toolbar__subtitle';
  subtitle.textContent = 'Animation Studio';
  brand.append(title, subtitle);

  const exerciseField = createSelectField(documentRef, 'Exercise');
  const viewGroup = documentRef.createElement('div');
  viewGroup.className = 'segmented';
  viewGroup.setAttribute('role', 'group');
  viewGroup.setAttribute('aria-label', 'View mode');

  const viewModes = {} as Record<ViewMode, HTMLButtonElement>;
  for (const mode of TOOLBAR_VIEW_MODES) {
    const button = createButton(documentRef, mode.label);
    const onClick = () => store.getState().setViewMode(mode.id);
    button.addEventListener('click', onClick);
    cleanups.push(() => button.removeEventListener('click', onClick));
    viewModes[mode.id] = button;
    viewGroup.append(button);
  }

  const backdropField = createSelectField(documentRef, 'Backdrop');
  for (const option of TOOLBAR_BACKDROPS) {
    appendOption(documentRef, backdropField.select, option.id, option.label);
  }

  const cameraField = createSelectField(documentRef, 'Camera');
  for (const preset of CAMERA_PRESET_IDS) {
    appendOption(documentRef, cameraField.select, preset, CAMERA_LABELS[preset]);
  }

  const spacer = documentRef.createElement('div');
  spacer.className = 'toolbar__spacer';

  const regenerate = createButton(
    documentRef,
    'Regenerate',
    'Rebuild the clip from the exercise definition',
  );
  const undo = createButton(documentRef, 'Undo', 'Undo (Ctrl+Z)');
  const redo = createButton(documentRef, 'Redo', 'Redo (Ctrl+Shift+Z)');

  const onExerciseChange = () =>
    store.getState().loadExercise(exerciseField.select.value);
  const onBackdropChange = () =>
    store.getState().setBackdrop(backdropField.select.value as StudioState['backdrop']);
  const onCameraChange = () =>
    store.getState().setCamera(cameraField.select.value as CameraPresetId);
  const onRegenerate = () => store.getState().regenerate();
  const onUndo = () => store.getState().undo();
  const onRedo = () => store.getState().redo();

  exerciseField.select.addEventListener('change', onExerciseChange);
  backdropField.select.addEventListener('change', onBackdropChange);
  cameraField.select.addEventListener('change', onCameraChange);
  regenerate.addEventListener('click', onRegenerate);
  undo.addEventListener('click', onUndo);
  redo.addEventListener('click', onRedo);
  cleanups.push(
    () => exerciseField.select.removeEventListener('change', onExerciseChange),
    () => backdropField.select.removeEventListener('change', onBackdropChange),
    () => cameraField.select.removeEventListener('change', onCameraChange),
    () => regenerate.removeEventListener('click', onRegenerate),
    () => undo.removeEventListener('click', onUndo),
    () => redo.removeEventListener('click', onRedo),
  );

  header.append(
    brand,
    exerciseField.label,
    viewGroup,
    backdropField.label,
    cameraField.label,
    spacer,
    regenerate,
    undo,
    redo,
  );

  let exerciseOptionsKey = '';
  const sync = () => {
    const state = store.getState();
    const exercise = state.document.exercise;
    const candidate = !EXERCISE_BY_ID.has(exercise.id);
    const nextExerciseOptionsKey = `${exercise.id}\u0000${exercise.name}\u0000${candidate}`;

    if (nextExerciseOptionsKey !== exerciseOptionsKey) {
      exerciseOptionsKey = nextExerciseOptionsKey;
      exerciseField.select.replaceChildren();
      if (candidate) {
        appendOption(
          documentRef,
          exerciseField.select,
          exercise.id,
          `Candidate: ${exercise.name}`,
        );
      }
      for (const libraryExercise of EXERCISES) {
        appendOption(
          documentRef,
          exerciseField.select,
          libraryExercise.id,
          libraryExercise.name,
        );
      }
    }

    exerciseField.select.value = exercise.id;
    for (const mode of TOOLBAR_VIEW_MODES) {
      viewModes[mode.id].classList.toggle('is-active', state.viewMode === mode.id);
    }
    backdropField.select.value = state.backdrop;
    cameraField.select.value = state.camera;
    undo.disabled = state.history.past.length === 0;
    redo.disabled = state.history.future.length === 0;
  };

  const unsubscribe = store.subscribe(sync);
  sync();

  let disposed = false;
  return {
    element: header,
    controls: {
      exerciseSelect: exerciseField.select,
      viewModes,
      backdropSelect: backdropField.select,
      cameraSelect: cameraField.select,
      regenerate,
      undo,
      redo,
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      for (const cleanup of cleanups.splice(0)) cleanup();
    },
  };
}
