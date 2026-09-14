import { useMemo, useState } from 'react';
import { resolveFrame } from '../../animation/pipeline';
import { PoseEvaluation } from '../../rig/skeleton';
import { ACTIVATION_STYLES } from '../../muscles/activation';
import {
  diagnoseMuscles,
  MUSCLE_ACTIVATION_ORDER,
  type MuscleReading,
} from '../../muscles/diagnostics';
import { skeleton, useStudio } from '../store';

const REGIONS = ['all', 'chest', 'shoulders', 'arms', 'back', 'core', 'legs'] as const;
type RegionFilter = (typeof REGIONS)[number];

const sideLabel = (reading: MuscleReading): string =>
  reading.side === 'l' ? 'L' : reading.side === 'r' ? 'R' : 'C';

const stateLabel = (reading: MuscleReading): string =>
  reading.state === 'shortened'
    ? 'Shortened'
    : reading.state === 'lengthened'
      ? 'Lengthened'
      : 'Near rest';

const deltaLabel = (reading: MuscleReading): string => {
  const value = reading.deltaPercent;
  const sign = value > 0.05 ? '+' : value < -0.05 ? '−' : '';
  return `${sign}${Math.abs(value).toFixed(1)}%`;
};

/**
 * Live biomechanics inspection for the finished canonical frame at the
 * playhead. Activation answers "what is the exercise targeting?" while the
 * length readout answers "what is the joint-spanning muscle path doing now?".
 */
export function MusclePanel() {
  const clip = useStudio((state) => state.document.clip);
  const exercise = useStudio((state) => state.document.exercise);
  const time = useStudio((state) => state.time);
  const [activeOnly, setActiveOnly] = useState(false);
  const [region, setRegion] = useState<RegionFilter>('all');

  const diagnostics = useMemo(() => {
    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);
    return diagnoseMuscles(evaluation, exercise.muscles);
  }, [clip, exercise.muscles, time]);

  const visible = useMemo(
    () =>
      diagnostics
        .filter((entry) => !activeOnly || entry.activation !== 'inactive')
        .filter((entry) => region === 'all' || entry.region === region)
        .sort((a, b) => {
          const role = MUSCLE_ACTIVATION_ORDER[a.activation] - MUSCLE_ACTIVATION_ORDER[b.activation];
          return role || a.label.localeCompare(b.label);
        }),
    [activeOnly, diagnostics, region],
  );

  const activeCount = diagnostics.filter((entry) => entry.activation !== 'inactive').length;

  return (
    <section className="panel">
      <h2>Muscle diagnostics</h2>
      <div className="panel__hint">
        Live functional path length at {time.toFixed(2)}s. Length is geometric, not a force or EMG estimate:
        a stabiliser can work hard while remaining near-isometric.
      </div>

      <div className="muscle-diagnostics__summary">
        <strong>{activeCount}</strong> active groups · <strong>{diagnostics.length}</strong> modelled groups
      </div>

      <div className="muscle-diagnostics__filters">
        <label className="field field--check">
          <input
            type="checkbox"
            checked={activeOnly}
            onChange={(event) => setActiveOnly(event.target.checked)}
          />
          <span>Active only</span>
        </label>
        <label className="field">
          <span className="field__label">Region</span>
          <select value={region} onChange={(event) => setRegion(event.target.value as RegionFilter)}>
            {REGIONS.map((value) => (
              <option key={value} value={value}>
                {value === 'all' ? 'All regions' : value[0].toUpperCase() + value.slice(1)}
              </option>
            ))}
          </select>
        </label>
      </div>

      <ul className="muscle-diagnostics">
        {visible.map((entry) => {
          const style = ACTIVATION_STYLES[entry.activation];
          return (
            <li key={entry.id} className="muscle-diagnostic">
              <div className="muscle-diagnostic__head">
                <span className="swatch" style={{ background: style.colour }} />
                <span className="muscle-diagnostic__name">{entry.label}</span>
                <span className="muscle-diagnostic__role">{style.label}</span>
              </div>
              <div className="muscle-diagnostic__readings">
                {entry.readings.map((reading) => (
                  <span
                    key={reading.side ?? 'centre'}
                    className={`muscle-reading muscle-reading--${reading.state}`}
                    title={`${(reading.stretch * 100).toFixed(1)}% of rest length`}
                  >
                    <b>{sideLabel(reading)}</b> {deltaLabel(reading)} · {stateLabel(reading)}
                    {reading.pathPoints > 2 ? ' · wrapped path' : ''}
                  </span>
                ))}
              </div>
            </li>
          );
        })}
      </ul>

      {visible.length === 0 && <p className="panel__empty">No muscle groups match this filter.</p>}
    </section>
  );
}
