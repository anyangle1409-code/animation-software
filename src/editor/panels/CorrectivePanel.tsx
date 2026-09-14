import { correctiveDiagnostics } from '../../character/correctiveDiagnostics';
import { useCharacter } from '../characterStore';
import { useStudio } from '../store';

const mm = (metres: number): string => `${(metres * 1000).toFixed(1)} mm`;

export function CorrectivePanel() {
  // Time subscription makes the panel refresh while playback mutates morph influences.
  useStudio((state) => state.time);
  const active = useCharacter((state) => state.active);
  const enabled = useCharacter((state) => state.correctivesPreview);
  const setEnabled = useCharacter((state) => state.setCorrectivesPreview);
  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];

  return (
    <section className="panel corrective-panel">
      <h2>Correctives</h2>
      <p className="panel__note">
        Mesh-specific joint correctives at the current playhead. The bypass below is viewport-only;
        it never changes the clip, source mesh or exported animation.
      </p>

      <div className="corrective-ab">
        <button type="button" className={enabled ? 'is-active' : ''} onClick={() => setEnabled(true)}>
          Correctives on
        </button>
        <button type="button" className={!enabled ? 'is-active' : ''} onClick={() => setEnabled(false)}>
          Raw skinning
        </button>
      </div>

      {!active && <p className="panel__empty">No active character is mounted.</p>}
      {active && diagnostics.length === 0 && (
        <p className="panel__empty">This character exposes no Home Gym PT corrective morphs.</p>
      )}

      <div className="corrective-list">
        {diagnostics.map((item) => (
          <article key={`${item.mesh}-${item.name}`} className="corrective-card">
            <div className="corrective-card__head">
              <strong>{item.name.replace('homeGymPT_', '').replaceAll('_', ' ')}</strong>
              <span>{Math.round(item.influence * 100)}%</span>
            </div>
            <div className="corrective-metrics">
              <span>Live displacement <strong>{mm(item.liveMaxDisplacement)}</strong></span>
              <span>Authored maximum <strong>{mm(item.maxDisplacement)}</strong></span>
              <span>Affected vertices <strong>{item.affectedVertices}</strong></span>
              <span>Mesh <strong>{item.mesh}</strong></span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
