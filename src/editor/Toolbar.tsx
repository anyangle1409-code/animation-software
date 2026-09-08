import { EXERCISES } from '../exercises/library';
import { CAMERA_LABELS } from '../viewer/cameras';
import { CAMERA_PRESET_IDS } from '../viewer/cameraTypes';
import type { ViewMode } from './store';
import { useStudio } from './store';

const VIEW_MODES: { id: ViewMode; label: string }[] = [
  { id: 'skeleton', label: 'Skeleton' },
  { id: 'muscles', label: 'Muscles' },
  { id: 'combined', label: 'Combined' },
  { id: 'character', label: 'Character' },
];

export function Toolbar() {
  const exerciseId = useStudio((state) => state.document.exercise.id);
  const loadExercise = useStudio((state) => state.loadExercise);
  const viewMode = useStudio((state) => state.viewMode);
  const setViewMode = useStudio((state) => state.setViewMode);
  const camera = useStudio((state) => state.camera);
  const setCamera = useStudio((state) => state.setCamera);
  const undo = useStudio((state) => state.undo);
  const redo = useStudio((state) => state.redo);
  const canUndo = useStudio((state) => state.history.past.length > 0);
  const canRedo = useStudio((state) => state.history.future.length > 0);
  const regenerate = useStudio((state) => state.regenerate);

  return (
    <header className="toolbar">
      <div className="toolbar__brand">
        <span className="toolbar__title">Home Gym PT</span>
        <span className="toolbar__subtitle">Animation Studio</span>
      </div>

      <label className="field">
        <span className="field__label">Exercise</span>
        <select value={exerciseId} onChange={(event) => loadExercise(event.target.value)}>
          {EXERCISES.map((exercise) => (
            <option key={exercise.id} value={exercise.id}>
              {exercise.name}
            </option>
          ))}
        </select>
      </label>

      <div className="segmented" role="group" aria-label="View mode">
        {VIEW_MODES.map((mode) => (
          <button
            key={mode.id}
            type="button"
            className={viewMode === mode.id ? 'is-active' : ''}
            onClick={() => setViewMode(mode.id)}
          >
            {mode.label}
          </button>
        ))}
      </div>

      <label className="field">
        <span className="field__label">Camera</span>
        <select value={camera} onChange={(event) => setCamera(event.target.value as never)}>
          {CAMERA_PRESET_IDS.map((preset) => (
            <option key={preset} value={preset}>
              {CAMERA_LABELS[preset]}
            </option>
          ))}
        </select>
      </label>

      <div className="toolbar__spacer" />

      <button type="button" onClick={regenerate} title="Rebuild the clip from the exercise definition">
        Regenerate
      </button>
      <button type="button" onClick={undo} disabled={!canUndo} title="Undo (Ctrl+Z)">
        Undo
      </button>
      <button type="button" onClick={redo} disabled={!canRedo} title="Redo (Ctrl+Shift+Z)">
        Redo
      </button>
    </header>
  );
}
