from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected one match, found {count}: {old[:120]!r}')
    file.write_text(text.replace(old, new, 1), encoding='utf-8')


Path('src/constraints/contactDiagnostics.ts').write_text(r'''import { Vector3 } from 'three';
import { resolveFrame } from '../animation/pipeline';
import type { StudioClip } from '../animation/clip';
import { IK_CHAINS } from '../ik/chains';
import type { IKChainId, IKResult } from '../ik/types';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import type { Vec3 } from '../rig/types';
import type { LockMode } from './types';

export type ContactStatus = 'disabled' | 'unresolved' | 'reached' | 'limited' | 'overextended';

export interface ContactDiagnostic {
  id: string;
  chain: IKChainId;
  mode: LockMode;
  enabled: boolean;
  equipmentId?: string;
  socket?: string;
  target: Vec3 | null;
  actual: Vec3 | null;
  /** Final effector-to-target distance in metres. */
  error: number | null;
  reached: boolean | null;
  overExtended: boolean | null;
  status: ContactStatus;
}

const asVec3 = (point: Vector3): Vec3 => ({ x: point.x, y: point.y, z: point.z });

/**
 * Inspect the production contact solution at one playhead time.
 *
 * This deliberately calls the same `resolveFrame` pipeline as the viewport. It
 * does not run a second reach model or modify the clip: the target, final
 * effector position, solver `reached` flag and over-extension result are exactly
 * the values that produced the displayed pose.
 */
export function contactDiagnostics(
  skeleton: Skeleton,
  evaluation: PoseEvaluation,
  clip: StudioClip,
  time: number,
  anchors?: Map<string, Vec3>,
): ContactDiagnostic[] {
  const frame = resolveFrame(skeleton, evaluation, clip, time, { anchors });
  evaluation.apply(frame.pose);

  const finalResults = new Map<IKChainId, IKResult>();
  for (const result of frame.ikResults) finalResults.set(result.chain, result);

  return clip.locks.map((lock) => {
    const common = {
      id: lock.id,
      chain: lock.chain,
      mode: lock.mode,
      enabled: lock.enabled,
      ...(lock.equipmentId ? { equipmentId: lock.equipmentId } : {}),
      ...(lock.socket ? { socket: lock.socket } : {}),
    };

    if (!lock.enabled) {
      return {
        ...common,
        target: null,
        actual: null,
        error: null,
        reached: null,
        overExtended: null,
        status: 'disabled' as const,
      };
    }

    const contact = [...frame.contacts]
      .reverse()
      .find((candidate) => candidate.chain === lock.chain && candidate.mode === lock.mode);
    if (!contact) {
      return {
        ...common,
        target: null,
        actual: null,
        error: null,
        reached: null,
        overExtended: null,
        status: 'unresolved' as const,
      };
    }

    const actualPoint = evaluation.head(IK_CHAINS[lock.chain].end, new Vector3());
    const targetPoint = new Vector3(contact.target.x, contact.target.y, contact.target.z);
    const result = finalResults.get(lock.chain);
    const error = actualPoint.distanceTo(targetPoint);
    const status: ContactStatus = result?.overExtended
      ? 'overextended'
      : result?.reached
        ? 'reached'
        : 'limited';

    return {
      ...common,
      target: { ...contact.target },
      actual: asVec3(actualPoint),
      error,
      reached: result?.reached ?? error < 1e-6,
      overExtended: result?.overExtended ?? false,
      status,
    };
  });
}
''', encoding='utf-8')

Path('src/constraints/contactDiagnostics.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { sampleClip } from '../animation/clip';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { pullUp } from '../exercises/definitions/pullUp';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { vec3 } from '../rig/types';
import { lockAnchors } from './locks';
import { contactDiagnostics } from './contactDiagnostics';

const skeleton = canonicalSkeleton;

const anchorsFor = (clip: ReturnType<typeof generateClip>) =>
  lockAnchors(new PoseEvaluation(skeleton), sampleClip(clip, 0).pose, clip.locks);

describe('live contact diagnostics', () => {
  it('reports the curl floor locks from the same resolved frame used by the viewport', () => {
    const clip = generateClip(skeleton, bicepCurl);
    const diagnostics = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      clip,
      clip.duration * 0.5,
      anchorsFor(clip),
    );

    expect(diagnostics).toHaveLength(2);
    for (const diagnostic of diagnostics) {
      expect(diagnostic.mode).toBe('floor');
      expect(diagnostic.target).not.toBeNull();
      expect(diagnostic.actual).not.toBeNull();
      expect(Number.isFinite(diagnostic.error)).toBe(true);
      expect(diagnostic.error!).toBeLessThan(0.01);
      expect(diagnostic.status).not.toBe('unresolved');
    }
  });

  it('resolves pull-up hand contacts through the rack sockets', () => {
    const clip = generateClip(skeleton, pullUp);
    const diagnostics = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      clip,
      clip.duration * 0.45,
    );

    expect(diagnostics).toHaveLength(2);
    for (const diagnostic of diagnostics) {
      expect(diagnostic.mode).toBe('equipment');
      expect(diagnostic.equipmentId).toBe('rack');
      expect(diagnostic.socket).toMatch(/^pullup_[lr]$/);
      expect(diagnostic.target).not.toBeNull();
      expect(diagnostic.actual).not.toBeNull();
      expect(Number.isFinite(diagnostic.error)).toBe(true);
    }
  });

  it('surfaces a physically over-extended target instead of hiding it', () => {
    const clip = generateClip(skeleton, bicepCurl);
    const impossible = {
      ...clip,
      locks: [
        {
          id: 'far_arm',
          chain: 'arm_l' as const,
          mode: 'world' as const,
          position: vec3(8, 8, 8),
          enabled: true,
        },
      ],
    };
    const [diagnostic] = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      impossible,
      0,
    );

    expect(diagnostic.status).toBe('overextended');
    expect(diagnostic.reached).toBe(false);
    expect(diagnostic.overExtended).toBe(true);
    expect(diagnostic.error).not.toBeNull();
    expect(diagnostic.error!).toBeGreaterThan(1);
  });
});
''', encoding='utf-8')

Path('src/editor/panels/ContactPanel.tsx').write_text(r'''import { useMemo } from 'react';
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
''', encoding='utf-8')

replace_once(
    'src/editor/App.tsx',
    "import { GripPanel } from './panels/GripPanel';",
    "import { GripPanel } from './panels/GripPanel';\nimport { ContactPanel } from './panels/ContactPanel';",
)
replace_once(
    'src/editor/App.tsx',
    "type LeftTab = 'joint' | 'grip' | 'ik' | 'character';",
    "type LeftTab = 'joint' | 'grip' | 'ik' | 'contacts' | 'character';",
)
replace_once(
    'src/editor/App.tsx',
    "            <button\n              type=\"button\"\n              className={leftTab === 'character' ? 'is-active' : ''}\n              onClick={() => setLeftTab('character')}\n            >\n              Character\n            </button>",
    "            <button\n              type=\"button\"\n              className={leftTab === 'contacts' ? 'is-active' : ''}\n              onClick={() => setLeftTab('contacts')}\n            >\n              Contacts\n            </button>\n            <button\n              type=\"button\"\n              className={leftTab === 'character' ? 'is-active' : ''}\n              onClick={() => setLeftTab('character')}\n            >\n              Character\n            </button>",
)
replace_once(
    'src/editor/App.tsx',
    "            {leftTab === 'ik' && <IKPanel />}\n            {leftTab === 'character' && <CharacterPanel />}",
    "            {leftTab === 'ik' && <IKPanel />}\n            {leftTab === 'contacts' && <ContactPanel />}\n            {leftTab === 'character' && <CharacterPanel />}",
)

styles = Path('src/editor/styles.css')
styles.write_text(styles.read_text(encoding='utf-8') + r'''

/* ---------- live contact / reachability diagnostics ---------- */

.contact-card {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 10px;
  margin: 8px 0;
}

.contact-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.contact-card__head .field {
  margin: 0;
}

.contact-card__head strong {
  font-size: 11px;
  white-space: nowrap;
}

.contact-card--reached .contact-card__head strong {
  color: var(--good, #78d49a);
}

.contact-card--limited .contact-card__head strong,
.contact-card--overextended .contact-card__head strong,
.contact-card--unresolved .contact-card__head strong {
  color: var(--warning, #e6b86f);
}

.contact-metrics {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 5px 10px;
  margin: 10px 0 0;
  font-size: 11px;
}

.contact-metrics dt {
  color: var(--muted);
}

.contact-metrics dd {
  margin: 0;
  min-width: 0;
  overflow-wrap: anywhere;
  font-variant-numeric: tabular-nums;
}
''', encoding='utf-8')

roadmap = Path('docs/STUDIO_CAPABILITY_ROADMAP.md')
roadmap_text = roadmap.read_text(encoding='utf-8')
old = "## 6. Corrective deformation workspace"
new = """### Implemented equipment/contact foundation

- Dedicated Contacts workspace inspects every floor / world / equipment lock at the live playhead.
- Target and actual effector positions, millimetre contact error, solver reachability and physical over-extension are reported from the same production frame pipeline used by the viewport.
- Contact inspection is non-destructive; lock enable/disable still uses normal undoable clip editing.

## 6. Corrective deformation workspace"""
if roadmap_text.count(old) != 1:
    raise SystemExit('roadmap section marker missing')
roadmap.write_text(roadmap_text.replace(old, new, 1), encoding='utf-8')

changelog = Path('AI_CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
heading = '### ChatGPT — 2026-09-14 — live contact and reachability workspace'
entry = r'''

### ChatGPT — 2026-09-14 — live contact and reachability workspace

Added a dedicated Contacts tab that inspects floor, world and equipment locks at the current playhead using the **same `resolveFrame` production pipeline and analytical IK result used by the viewport**. Each lock now has a live target position, final hand/foot effector position, world-space error in millimetres, solver `reached` state and explicit physical over-extension state. Equipment locks also show the equipment/socket pair they resolve through. This is diagnostic-only: it does not add a second solver, hidden correction, safety score or movement change.

`src/constraints/contactDiagnostics.ts` is the pure inspection layer. Regression coverage verifies the bicep-curl floor contacts, pull-up rack socket contacts and a deliberately impossible world-space arm target; the impossible target must surface as `overextended` rather than being silently presented as a valid contact. Lock enable/disable remains the existing undoable clip edit. The Studio roadmap now records the contact-inspection foundation as implemented; equipment move/rotate authoring remains the next separate step.
'''
if heading not in text:
    marker = '## Unreleased\n'
    if marker not in text:
        raise SystemExit('AI_CHANGELOG.md: Unreleased marker missing')
    changelog.write_text(text.replace(marker, marker + entry, 1), encoding='utf-8')

print('Applied live contact and reachability workspace')
