import { useMemo } from 'react';
import { toDeg } from '../../core/math';
import { boneLabel } from '../../rig/boneNames';
import type { BoneName } from '../../rig/boneNames';
import type { Pose } from '../../rig/types';
import { frontPoseDiagram, type PoseSnapshot } from '../comparison';
import { useStudio } from '../store';

function PoseDiagram({ snapshot, title }: { snapshot: PoseSnapshot | null; title: string }) {
  const lines = useMemo(() => (snapshot ? frontPoseDiagram(snapshot.pose) : []), [snapshot]);
  return (
    <div className="comparison-card">
      <div className="comparison-card__head">
        <strong>{title}</strong>
        {snapshot && (
          <span>
            {snapshot.time.toFixed(2)}s{snapshot.marker ? ` · ${snapshot.marker}` : ''}
          </span>
        )}
      </div>
      {snapshot ? (
        <svg className="comparison-card__diagram" viewBox="0 0 160 220" role="img" aria-label={`${title} pose`}>
          {lines.map((line) => (
            <line
              key={line.bone}
              x1={line.x1 * 160}
              y1={line.y1 * 220}
              x2={line.x2 * 160}
              y2={line.y2 * 220}
            />
          ))}
        </svg>
      ) : (
        <div className="comparison-card__empty">Capture a pose at the playhead.</div>
      )}
    </div>
  );
}

const rotation = (pose: Pose, bone: BoneName) => pose.rotations[bone] ?? { x: 0, y: 0, z: 0 };

export function ComparisonPanel() {
  const comparison = useStudio((state) => state.comparison);
  const captureComparison = useStudio((state) => state.captureComparison);
  const clearComparison = useStudio((state) => state.clearComparison);
  const selectedBone = useStudio((state) => state.selection.bone);

  const a = comparison.a;
  const b = comparison.b;
  const angles = selectedBone && a && b
    ? { a: rotation(a.pose, selectedBone), b: rotation(b.pose, selectedBone) }
    : null;

  return (
    <section className="panel comparison-panel">
      <h2>Pose A/B</h2>
      <p className="muted">
        Reference and candidate snapshots are review-only. Capturing them never edits the clip or its undo history.
      </p>

      <div className="button-row">
        <button type="button" onClick={() => captureComparison('a')}>Capture A</button>
        <button type="button" onClick={() => captureComparison('b')}>Capture B</button>
        <button type="button" onClick={() => clearComparison()} disabled={!a && !b}>Clear both</button>
      </div>

      <div className="comparison-grid">
        <PoseDiagram snapshot={a} title="A · Reference" />
        <PoseDiagram snapshot={b} title="B · Candidate" />
      </div>

      {angles && selectedBone && (
        <div className="comparison-delta">
          <h3>{boneLabel(selectedBone)} angles</h3>
          <div className="comparison-delta__grid">
            <span>Axis</span><span>A</span><span>B</span><span>Δ</span>
            {(['x', 'y', 'z'] as const).map((axis) => {
              const aDeg = toDeg(angles.a[axis]);
              const bDeg = toDeg(angles.b[axis]);
              return (
                <div className="comparison-delta__row" key={axis}>
                  <span>{axis.toUpperCase()}</span>
                  <span>{aDeg.toFixed(1)}°</span>
                  <span>{bDeg.toFixed(1)}°</span>
                  <span>{(bDeg - aDeg).toFixed(1)}°</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!selectedBone && a && b && (
        <p className="muted">Select a joint to see exact A/B angle differences.</p>
      )}
    </section>
  );
}
