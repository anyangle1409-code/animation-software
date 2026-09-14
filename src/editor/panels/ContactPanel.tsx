import { useMemo } from 'react';
import { contactDiagnostics, type ContactDiagnostic } from '../../constraints/contactDiagnostics';
import { IK_CHAINS } from '../../ik/chains';
import { PoseEvaluation } from '../../rig/skeleton';
import type { Vec3 } from '../../rig/types';
import { currentAnchors, skeleton, useStudio } from '../store';

const point = (value: Vec3 | null): string =>
  value ? `${value.x.toFixed(3)}, ${value.y.toFixed(3)}, ${value.z.toFixed(3)}` : '—';

const statusLabel = (diagnostic: ContactDiagnostic): string => {
  if (diagnostic.status === 'disabled') return 'Disabled';
  if (diagnostic.status === 'unresolved') return 'Target unresolved';
  if (diagnostic.status === 'overextended') return 'Over-extended';
  if (diagnostic.status === 'limited') return 'Limited by solve';
  return 'Reached';
};

export function ContactPanel() {
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);
  const setLockEnabled = useStudio((state) => state.setLockEnabled);

  const diagnostics = useMemo(
    () =>
      contactDiagnostics(
        skeleton,
        new PoseEvaluation(skeleton),
        clip,
        time,
        currentAnchors(clip),
      ),
    [clip, time],
  );

  return (
    <section className="panel contact-panel">
      <h2>Contacts</h2>
      <p className="panel__note">
        Live production-solver inspection at {time.toFixed(2)}s. These readouts do not add hidden
        corrections or change the animation.
      </p>

      {diagnostics.length === 0 && (
        <p className="panel__empty">This exercise defines no contact locks.</p>
      )}

      {diagnostics.map((diagnostic) => (
        <article
          key={diagnostic.id}
          className={`contact-card contact-card--${diagnostic.status}`}
        >
          <div className="contact-card__head">
            <label className="field field--check">
              <input
                type="checkbox"
                checked={diagnostic.enabled}
                onChange={(event) => setLockEnabled(diagnostic.id, event.target.checked)}
              />
              <span>{IK_CHAINS[diagnostic.chain].label}</span>
            </label>
            <strong>{statusLabel(diagnostic)}</strong>
          </div>

          <dl className="contact-metrics">
            <dt>Lock</dt>
            <dd>{diagnostic.mode}</dd>
            {diagnostic.mode === 'equipment' && (
              <>
                <dt>Socket</dt>
                <dd>
                  <code>{diagnostic.equipmentId ?? '?'}:{diagnostic.socket ?? '?'}</code>
                </dd>
              </>
            )}
            <dt>Target</dt>
            <dd><code>{point(diagnostic.target)}</code></dd>
            <dt>Effector</dt>
            <dd><code>{point(diagnostic.actual)}</code></dd>
            <dt>Error</dt>
            <dd>
              {diagnostic.error === null ? '—' : `${(diagnostic.error * 1000).toFixed(2)} mm`}
            </dd>
            <dt>Reachability</dt>
            <dd>
              {diagnostic.reached === null
                ? '—'
                : diagnostic.overExtended
                  ? 'Outside physical reach'
                  : diagnostic.reached
                    ? 'Solver reached target'
                    : 'Joint limits prevented exact reach'}
            </dd>
          </dl>
        </article>
      ))}

      <p className="panel__hint">
        Error is the final world-space distance from the resolved hand/foot effector to its lock
        target. Reachability is reported by the existing analytical IK solver.
      </p>
    </section>
  );
}
