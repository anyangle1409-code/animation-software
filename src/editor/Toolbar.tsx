import { EXERCISES, EXERCISE_BY_ID } from '../exercises/library';
import { CAMERA_LABELS } from '../viewer/cameras';
import { CAMERA_PRESET_IDS } from '../viewer/cameraTypes';
import type { ViewLayers } from './store';
import { useStudio } from './store';
import { useCharacter } from './characterStore';

const LAYERS: { id: keyof ViewLayers; label: string }[] = [
  { id: 'skeleton', label: 'Skeleton' },
  { id: 'muscles', label: 'Muscles' },
  { id: 'character', label: 'Character' },
];

export function Toolbar() {
  const exerciseId = useStudio((state) => state.document.exercise.id);
  const exerciseName = useStudio((state) => state.document.exercise.name);
  // A generated candidate under review is not in the library; it is listed on
  // its own so the selector does not claim a library exercise is showing.
  const candidate = !EXERCISE_BY_ID.has(exerciseId);
  const loadExercise = useStudio((state) => state.loadExercise);
  const layers = useStudio((state) => state.layers);
  const toggleLayer = useStudio((state) => state.toggleLayer);
  const characterStyle = useStudio((state) => state.characterStyle);
  const setCharacterStyle = useStudio((state) => state.setCharacterStyle);
  const characterOpacity = useStudio((state) => state.characterOpacity);
  const setCharacterOpacity = useStudio((state) => state.setCharacterOpacity);
  const characterStatus = useCharacter((state) => state.status);
  const camera = useStudio((state) => state.camera);
  const setCamera = useStudio((state) => state.setCamera);
  const backdrop = useStudio((state) => state.backdrop);
  const setBackdrop = useStudio((state) => state.setBackdrop);
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
          {candidate && <option value={exerciseId}>Candidate: {exerciseName}</option>}
          {EXERCISES.map((exercise) => (
            <option key={exercise.id} value={exercise.id}>
              {exercise.name}
            </option>
          ))}
        </select>
      </label>

      <div className="layers" role="group" aria-label="Show layers">
        <span className="field__label">Show</span>
        <div className="layers__toggles">
          {LAYERS.map((layer) => (
            <button
              key={layer.id}
              type="button"
              aria-pressed={layers[layer.id]}
              className={`layer-toggle ${layers[layer.id] ? 'is-active' : ''}`}
              onClick={() => toggleLayer(layer.id)}
            >
              <span className="layer-toggle__box" aria-hidden="true">{layers[layer.id] ? '✓' : ''}</span>
              {layer.label}
            </button>
          ))}
        </div>
      </div>

      {layers.character && (
        <div className="layers layers--character">
          <label className="field">
            <span className="field__label">Surface</span>
            <select value={characterStyle} onChange={(event) => setCharacterStyle(event.target.value as never)}>
              <option value="skin">Skin</option>
              <option value="anatomy">Anatomy</option>
            </select>
          </label>
          <label className="field field--slider">
            <span className="field__label">See-through {Math.round((1 - characterOpacity) * 100)}%</span>
            <input
              type="range"
              min={0.05}
              max={1}
              step={0.05}
              value={characterOpacity}
              onChange={(event) => setCharacterOpacity(Number(event.target.value))}
            />
          </label>
          {characterStatus.kind !== 'idle' && (
            <span className={`layer-status layer-status--${characterStatus.kind}`}>
              {characterStatus.kind === 'loading' ? 'Loading character…' : `Character failed to load: ${characterStatus.message ?? 'unknown error'}`}
            </span>
          )}
        </div>
      )}

      <label className="field">
        <span className="field__label">Backdrop</span>
        <select value={backdrop} onChange={(event) => setBackdrop(event.target.value as never)}>
          <option value="studio">Studio</option>
          <option value="light">Light</option>
          <option value="void">Void</option>
          <option value="study">Study</option>
        </select>
      </label>

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
