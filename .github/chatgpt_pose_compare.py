from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:120]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


# -------------------------------------------------------------------------
# Pure comparison helpers: front-view skeleton projection and snapshots.
# -------------------------------------------------------------------------
Path('src/editor/comparison.ts').write_text(r'''import { Vector3 } from 'three';
import { CORE_BONES } from '../rig/boneNames';
import type { CoreBoneName } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Pose } from '../rig/types';
import type { PoseMarkerKind } from '../animation/clip';

export interface PoseSnapshot {
  pose: Pose;
  time: number;
  marker?: PoseMarkerKind;
  label?: string;
}

export interface DiagramSegment {
  bone: CoreBoneName;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

/**
 * Project the canonical rig into a normalised front-view diagram. This is an
 * inspection aid only; no camera or projection state is written back to the clip.
 */
export function frontPoseDiagram(pose: Pose): DiagramSegment[] {
  const evaluation = new PoseEvaluation(canonicalSkeleton).apply(pose);
  const raw = CORE_BONES.filter((bone) => bone !== 'root').map((bone) => {
    const head = evaluation.head(bone, new Vector3());
    const tail = evaluation.tail(bone, new Vector3());
    return { bone, x1: head.x, y1: head.y, x2: tail.x, y2: tail.y };
  });

  const xs = raw.flatMap((line) => [line.x1, line.x2]);
  const ys = raw.flatMap((line) => [line.y1, line.y2]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Math.max(1e-6, maxX - minX);
  const height = Math.max(1e-6, maxY - minY);
  const padding = 0.06;
  const usable = 1 - 2 * padding;

  return raw.map((line) => ({
    bone: line.bone,
    x1: padding + ((line.x1 - minX) / width) * usable,
    y1: padding + (1 - (line.y1 - minY) / height) * usable,
    x2: padding + ((line.x2 - minX) / width) * usable,
    y2: padding + (1 - (line.y2 - minY) / height) * usable,
  }));
}
''', encoding='utf-8')

Path('src/editor/comparison.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { frontPoseDiagram } from './comparison';

const clip = generateClip(canonicalSkeleton, bicepCurl);

describe('pose comparison diagram', () => {
  it('keeps every projected core-bone endpoint inside the normalised viewport', () => {
    const diagram = frontPoseDiagram(clip.keyframes[0].pose);
    expect(diagram.length).toBeGreaterThan(15);
    for (const line of diagram) {
      for (const value of [line.x1, line.y1, line.x2, line.y2]) {
        expect(value).toBeGreaterThanOrEqual(0);
        expect(value).toBeLessThanOrEqual(1);
      }
    }
  });

  it('shows the curl peak as a different forearm shape from the start pose', () => {
    const start = frontPoseDiagram(clip.keyframes[0].pose).find((line) => line.bone === 'forearm_l')!;
    const peak = frontPoseDiagram(clip.keyframes[1].pose).find((line) => line.bone === 'forearm_l')!;
    const distance = Math.hypot(start.x2 - peak.x2, start.y2 - peak.y2);
    expect(distance).toBeGreaterThan(0.08);
  });
});
''', encoding='utf-8')

# -------------------------------------------------------------------------
# Store: snapshots are transient review state, outside StudioDocument/history.
# -------------------------------------------------------------------------
replace_once(
    'src/editor/store.ts',
    "import { normalizeLoopRange, type LoopRange } from './playback';",
    "import { normalizeLoopRange, type LoopRange } from './playback';\nimport type { PoseSnapshot } from './comparison';",
)
replace_once(
    'src/editor/store.ts',
    "  loopRange: LoopRange | null;\n\n  selection: Selection;",
    "  loopRange: LoopRange | null;\n  comparison: { a: PoseSnapshot | null; b: PoseSnapshot | null };\n\n  selection: Selection;",
)
replace_once(
    'src/editor/store.ts',
    "  setLoopRange: (range: LoopRange | null) => void;\n\n  // --- selection and display",
    "  setLoopRange: (range: LoopRange | null) => void;\n  captureComparison: (slot: 'a' | 'b') => void;\n  clearComparison: (slot?: 'a' | 'b') => void;\n\n  // --- selection and display",
)
replace_once(
    'src/editor/store.ts',
    "    loopRange: null,\n\n    selection:",
    "    loopRange: null,\n    comparison: { a: null, b: null },\n\n    selection:",
)
replace_once(
    'src/editor/store.ts',
    "    setLoopRange: (range) => {\n      const clip = get().document.clip;\n      set({ loopRange: normalizeLoopRange(range, clip.duration, clip.fps) });\n    },\n\n    selectBone:",
    "    setLoopRange: (range) => {\n      const clip = get().document.clip;\n      set({ loopRange: normalizeLoopRange(range, clip.duration, clip.fps) });\n    },\n    captureComparison: (slot) => {\n      const state = get();\n      const sample = sampleClip(state.document.clip, state.time);\n      const frame = keyframeAt(state.document.clip, state.time);\n      const snapshot: PoseSnapshot = {\n        pose: clonePose(sample.pose),\n        time: state.time,\n        ...(frame?.marker ? { marker: frame.marker } : {}),\n        ...(frame?.label ? { label: frame.label } : {}),\n      };\n      set({ comparison: { ...state.comparison, [slot]: snapshot } });\n    },\n    clearComparison: (slot) => {\n      const comparison = get().comparison;\n      set({\n        comparison: slot\n          ? { ...comparison, [slot]: null }\n          : { a: null, b: null },\n      });\n    },\n\n    selectBone:",
)
replace_once(
    'src/editor/store.ts',
    "        loopRange: null,\n        validation: null,",
    "        loopRange: null,\n        comparison: { a: null, b: null },\n        validation: null,",
)

# -------------------------------------------------------------------------
# Side-by-side comparison panel.
# -------------------------------------------------------------------------
Path('src/editor/panels/ComparisonPanel.tsx').write_text(r'''import { useMemo } from 'react';
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
''', encoding='utf-8')

# The grid header and each data row need a shared four-column layout. Keep the
# DOM simple by making each row contents participate as a sub-grid.
styles = Path('src/editor/styles.css')
styles.write_text(styles.read_text(encoding='utf-8') + r'''

/* ---------- non-destructive pose A/B comparison ---------- */

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 10px 0 12px;
}

.comparison-card {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 8px;
}

.comparison-card__head {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  align-items: baseline;
  font-size: 11px;
}

.comparison-card__head span {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}

.comparison-card__diagram {
  display: block;
  width: 100%;
  height: 210px;
  margin-top: 6px;
}

.comparison-card__diagram line {
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
  opacity: 0.82;
}

.comparison-card__empty {
  min-height: 210px;
  display: grid;
  place-items: center;
  text-align: center;
  color: var(--muted);
  font-size: 11px;
}

.comparison-delta {
  border-top: 1px solid var(--line);
  padding-top: 10px;
}

.comparison-delta__grid {
  display: grid;
  grid-template-columns: 0.7fr 1fr 1fr 1fr;
  gap: 5px 8px;
  align-items: center;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.comparison-delta__row {
  display: contents;
}
''', encoding='utf-8')

# -------------------------------------------------------------------------
# App: add the dedicated Compare tab.
# -------------------------------------------------------------------------
replace_once(
    'src/editor/App.tsx',
    "import { CharacterPanel } from './panels/CharacterPanel';",
    "import { CharacterPanel } from './panels/CharacterPanel';\nimport { ComparisonPanel } from './panels/ComparisonPanel';",
)
replace_once(
    'src/editor/App.tsx',
    "type RightTab = 'exercise' | 'muscles' | 'technique' | 'export';",
    "type RightTab = 'exercise' | 'muscles' | 'technique' | 'compare' | 'export';",
)
replace_once(
    'src/editor/App.tsx',
    "            <button\n              type=\"button\"\n              className={rightTab === 'export' ? 'is-active' : ''}\n              onClick={() => setRightTab('export')}\n            >\n              Export\n            </button>",
    "            <button\n              type=\"button\"\n              className={rightTab === 'compare' ? 'is-active' : ''}\n              onClick={() => setRightTab('compare')}\n            >\n              Compare\n            </button>\n            <button\n              type=\"button\"\n              className={rightTab === 'export' ? 'is-active' : ''}\n              onClick={() => setRightTab('export')}\n            >\n              Export\n            </button>",
)
replace_once(
    'src/editor/App.tsx',
    "            {rightTab === 'technique' && <TechniquePanel />}\n            {rightTab === 'export' && <ExportPanel />}",
    "            {rightTab === 'technique' && <TechniquePanel />}\n            {rightTab === 'compare' && <ComparisonPanel />}\n            {rightTab === 'export' && <ExportPanel />}",
)

# -------------------------------------------------------------------------
# Store tests: captures are detached from document history and exercise scope.
# -------------------------------------------------------------------------
store_test = Path('src/editor/store.test.ts')
store_text = store_test.read_text(encoding='utf-8')
store_text += r'''

describe('non-destructive pose comparison', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('captures A/B poses without touching the document or undo history', () => {
    const document = useStudio.getState().document;
    const historyCount = useStudio.getState().history.past.length;

    useStudio.getState().setTime(0);
    useStudio.getState().captureComparison('a');
    useStudio.getState().setTime(2);
    useStudio.getState().captureComparison('b');

    const state = useStudio.getState();
    expect(state.document).toBe(document);
    expect(state.history.past.length).toBe(historyCount);
    expect(state.comparison.a?.time).toBe(0);
    expect(state.comparison.b?.time).toBe(2);
    expect(state.comparison.a?.marker).toBe('start');
    expect(state.comparison.b?.marker).toBe('peak');
    expect(state.comparison.a?.pose.rotations.forearm_l?.x).not.toBe(
      state.comparison.b?.pose.rotations.forearm_l?.x,
    );
  });

  it('clears snapshots when a different exercise is loaded', () => {
    useStudio.getState().captureComparison('a');
    expect(useStudio.getState().comparison.a).not.toBeNull();
    useStudio.getState().loadExercise('back_squat');
    expect(useStudio.getState().comparison).toEqual({ a: null, b: null });
  });
});
'''
store_test.write_text(store_text, encoding='utf-8')

# -------------------------------------------------------------------------
# Roadmap and Claude handoff.
# -------------------------------------------------------------------------
replace_once(
    'docs/STUDIO_CAPABILITY_ROADMAP.md',
    "- Semantic Start / Transition / Peak / Return pose markers are generated deterministically and editable on keyframes.\n- Individual finger/thumb joint authoring remains available through the same joint workspace.",
    "- Semantic Start / Transition / Peak / Return pose markers are generated deterministically and editable on keyframes.\n- Non-destructive A/B pose snapshots provide side-by-side front-view comparison plus selected-joint angle deltas.\n- Individual finger/thumb joint authoring remains available through the same joint workspace.",
)

changelog = Path('AI_CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
heading = '### ChatGPT — 2026-09-14 — non-destructive A/B pose comparison'
entry = r'''

### ChatGPT — 2026-09-14 — non-destructive A/B pose comparison

Added transient Reference A / Candidate B pose snapshots to the Studio. `comparison` state lives outside `StudioDocument`, so capturing, clearing and viewing snapshots do **not** mutate the accepted clip, do not create undo-history entries and do not affect export. The new Compare panel renders both snapshots side by side as deterministic front-view projections of the canonical core skeleton and, when a joint is selected, shows exact X/Y/Z angles for A and B plus the signed delta. This is intended for judging shoulder/elbow/body-position refinements before deciding whether a clip edit should be kept.

`src/editor/comparison.ts` owns the pure front-view projection helper, with tests keeping all projected endpoints inside the normalised viewport and confirming that the curl peak visibly differs from the start at the forearm. Store regressions verify A/B capture leaves the document/history untouched and that loading another exercise clears stale snapshots. The capability roadmap now records non-destructive A/B pose comparison as implemented.
'''
if heading not in text:
    marker = '## Unreleased\n'
    if marker not in text:
        raise SystemExit('AI_CHANGELOG.md: Unreleased marker missing')
    changelog.write_text(text.replace(marker, marker + entry, 1), encoding='utf-8')

print('Applied non-destructive A/B pose comparison')
