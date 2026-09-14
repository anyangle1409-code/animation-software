import { useEffect, useState } from 'react';
import { correctiveDiagnostics } from '../../character/correctiveDiagnostics';
import { meshStrainDiagnostics, type MeshStrainDiagnostic } from '../../character/meshStrain';
import { useCharacter } from '../characterStore';
import { skeleton, useStudio } from '../store';
import { scanMeshStrainWorstCases, type MeshStrainWorstPoint } from '../strainReview';

const mm = (metres: number): string => `${(metres * 1000).toFixed(1)} mm`;

export function CorrectivePanel() {
  // Time subscription makes the panel refresh while playback mutates morph influences.
  const time = useStudio((state) => state.time);
  const setTime = useStudio((state) => state.setTime);
  const clip = useStudio((state) => state.document.clip);
  const active = useCharacter((state) => state.active);
  const enabled = useCharacter((state) => state.correctivesPreview);
  const setEnabled = useCharacter((state) => state.setCorrectivesPreview);
  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];
  const controls = active?.deformation?.controls ?? [];
  const [, refreshControls] = useState(0);
  const [strain, setStrain] = useState<MeshStrainDiagnostic[]>([]);
  const [wholeRep, setWholeRep] = useState<{ enabled: boolean; items: MeshStrainWorstPoint[] } | null>(null);

  useEffect(() => {
    if (!active) {
      setStrain([]);
      return;
    }
    const update = () => setStrain(meshStrainDiagnostics(active.meshes));
    update();
    const timer = window.setInterval(update, 200);
    return () => window.clearInterval(timer);
  }, [active, enabled]);

  useEffect(() => setWholeRep(null), [active, clip, enabled]);

  const scanWholeRep = () => {
    if (!active) return;
    const items = scanMeshStrainWorstCases(active, skeleton, clip, enabled, time);
    setWholeRep({ enabled, items });
  };

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

      {controls.length > 0 && (
        <>
          <h3>Corrective tuning</h3>
          <p className="panel__hint">
            Character-specific and export-aware. These controls change neither the exercise clip nor
            the source skin weights; the active character and GLB export share the same value.
          </p>
          {controls.map((control) => (
            <div className="strain-card" key={control.id}>
              <strong>{control.label} · {Math.round(control.value * 100)}%</strong>
              <input
                type="range"
                min={control.min}
                max={control.max}
                step={control.step}
                value={control.value}
                onChange={(event) => {
                  control.set(Number(event.target.value));
                  refreshControls((value) => value + 1);
                  setWholeRep(null);
                }}
              />
              {control.note && <small>{control.note}</small>}
              <div className="button-row">
                <button
                  type="button"
                  disabled={Math.abs(control.value - control.defaultValue) < 1e-9}
                  onClick={() => {
                    control.set(control.defaultValue);
                    refreshControls((value) => value + 1);
                    setWholeRep(null);
                  }}
                >
                  Reset authored value
                </button>
              </div>
            </div>
          ))}
        </>
      )}

      {!active && <p className="panel__empty">No active character is mounted.</p>}
      {active && diagnostics.length === 0 && (
        <p className="panel__empty">This character exposes no Home Gym PT corrective morphs.</p>
      )}

      <h3>Surface strain</h3>
      <p className="panel__hint">
        Sampled edge-length change versus bind geometry. P95/P99 are robust whole-surface signals;
        severe counts are edges compressed or stretched by more than 20%.
      </p>
      <div className="button-row">
        <button type="button" disabled={!active} onClick={scanWholeRep}>
          Scan full rep
        </button>
      </div>
      {wholeRep && (
        <div className="strain-list">
          {wholeRep.items.map((item) => (
            <div key={`whole-rep-${item.mesh}`} className="strain-card">
              <strong>{item.mesh} · {wholeRep.enabled ? 'Correctives on' : 'Raw skinning'}</strong>
              <span>Worst P99 {(item.p99.value * 100).toFixed(1)}% · {item.p99.time.toFixed(2)}s</span>
              <span>Worst max {(item.max.value * 100).toFixed(1)}% · {item.max.time.toFixed(2)}s</span>
              <span>Worst compression count · {item.severeCompression.value.toFixed(0)} · {item.severeCompression.time.toFixed(2)}s</span>
              <span>Worst stretch count · {item.severeStretch.value.toFixed(0)} · {item.severeStretch.time.toFixed(2)}s</span>
              <div className="button-row">
                <button type="button" onClick={() => setTime(item.p99.time)}>Jump to worst P99</button>
                <button type="button" onClick={() => setTime(item.max.time)}>Jump to worst edge</button>
              </div>
              <small>{item.sampledEdges} sampled edges per frame</small>
            </div>
          ))}
        </div>
      )}
      <p className="panel__hint">
        Full-rep scan runs only when requested, follows the clip FPS, restores the current playhead pose, and uses a bounded edge sample so it remains an authoring locator rather than a simulation.
      </p>
      <div className="strain-list">
        {strain.map((item) => (
          <div key={item.mesh} className="strain-card">
            <strong>{item.mesh}</strong>
            <span>P95 {(item.p95 * 100).toFixed(1)}%</span>
            <span>P99 {(item.p99 * 100).toFixed(1)}%</span>
            <span>Max {(item.max * 100).toFixed(1)}%</span>
            <span>Compression &gt;20% · {item.severeCompression}</span>
            <span>Stretch &gt;20% · {item.severeStretch}</span>
            <small>{item.sampledEdges} sampled edges</small>
          </div>
        ))}
      </div>

      <h3>Corrective morphs</h3>
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
