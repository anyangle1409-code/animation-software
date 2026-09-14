import { MUSCLE_GROUPS } from '../../muscles/groups';
import { ACTIVATION_STYLES } from '../../muscles/activation';
import { repetitionDuration } from '../../exercises/types';
import { useStudio } from '../store';

export function ExercisePanel() {
  const exercise = useStudio((state) => state.document.exercise);
  const setTempo = useStudio((state) => state.setTempo);
  const setGripClosure = useStudio((state) => state.setGripClosure);

  const tempoFields = [
    { key: 'eccentric' as const, label: 'Eccentric (lower)' },
    { key: 'pauseStretched' as const, label: 'Pause stretched' },
    { key: 'concentric' as const, label: 'Concentric (lift)' },
    { key: 'pauseContracted' as const, label: 'Pause contracted' },
  ];

  return (
    <section className="panel">
      <h2>{exercise.name}</h2>
      {exercise.description && <p className="panel__note">{exercise.description}</p>}

      <h3>Tempo</h3>
      <div className="tempo-grid">
        {tempoFields.map((field) => (
          <label key={field.key} className="field">
            <span className="field__label">{field.label}</span>
            <input
              type="number"
              min={0}
              max={10}
              step={0.1}
              value={exercise.tempo[field.key]}
              onChange={(event) => setTempo({ [field.key]: Number(event.target.value) })}
            />
          </label>
        ))}
      </div>
      <p className="panel__note">
        One repetition takes {repetitionDuration(exercise).toFixed(2)}s.
      </p>

      <h3>Muscles worked</h3>
      <ul className="muscle-list">
        {(['primary', 'secondary', 'stabilisers'] as const).map((level) => {
          const style =
            ACTIVATION_STYLES[level === 'stabilisers' ? 'stabiliser' : level];
          return exercise.muscles[level].map((group) => (
            <li key={`${level}-${group}`}>
              <span className="swatch" style={{ background: style.colour }} />
              <span className="muscle-list__name">{MUSCLE_GROUPS[group].label}</span>
              <span className="muscle-list__level">{style.label}</span>
            </li>
          ));
        })}
      </ul>

      <h3>Breathing</h3>
      <p className="panel__note">{exercise.breathing.cue}</p>

      <h3>Grip and stance</h3>
      <dl className="spec-list">
        <dt>Grip</dt>
        <dd>
          {exercise.hands.grip}, {exercise.hands.orientation}
        </dd>
        <dt>Grip closure</dt>
        <dd>
          <label className="grip-closure">
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={exercise.hands.closure}
              aria-label="Grip closure"
              onChange={(event) => setGripClosure(Number(event.target.value))}
            />
            <span>{Math.round(exercise.hands.closure * 100)}%</span>
          </label>
        </dd>
        <dt>Hand width</dt>
        <dd>{exercise.hands.width ? `${(exercise.hands.width * 100).toFixed(0)} cm` : '—'}</dd>
        <dt>Stance width</dt>
        <dd>{(exercise.feet.width * 100).toFixed(0)} cm</dd>
        <dt>Toe-out</dt>
        <dd>{exercise.feet.toeOut}°</dd>
      </dl>

      <h3>Equipment</h3>
      <ul className="plain-list">
        {exercise.equipment.instances.map((instance) => (
          <li key={instance.id}>
            {instance.label ?? instance.kind}
            {instance.mass ? ` — ${instance.mass} kg` : ''}
          </li>
        ))}
        {exercise.equipment.instances.length === 0 && <li>Bodyweight</li>}
      </ul>
    </section>
  );
}
