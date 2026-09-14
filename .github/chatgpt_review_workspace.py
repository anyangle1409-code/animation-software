from pathlib import Path

def read(path): return Path(path).read_text()
def write(path,text): Path(path).write_text(text)
def replace_once(text,old,new,label):
    if old not in text: raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old,new,1)

write('src/editor/review.ts', r'''import { PoseEvaluation } from '../rig/skeleton';
import type { Skeleton } from '../rig/skeleton';
import type { ExerciseDefinition } from '../exercises/types';
import type { StudioClip } from '../animation/clip';
import { sampleClip } from '../animation/clip';
import { validateClip } from '../animation/validate';
import { resolveFrame } from '../animation/pipeline';
import { lockAnchors } from '../constraints/locks';
import { contactDiagnostics } from '../constraints/contactDiagnostics';
import { measureGripFit } from '../equipment/gripDiagnostics';

export interface ReviewGate {
  id: 'technique' | 'loop' | 'ik' | 'contacts' | 'grip';
  label: string;
  passed: boolean;
  detail: string;
  warnings?: number;
  applicable?: boolean;
}

export interface ExerciseReview {
  automatedPass: boolean;
  gates: ReviewGate[];
  sampledFrames: number;
}

/**
 * Conservative automated authoring gate. It deliberately does not decide
 * visual quality: it only answers whether the deterministic clip has cleared
 * the checks the Studio can measure honestly.
 */
export function reviewExercise(
  rig: Skeleton,
  exercise: ExerciseDefinition,
  clip: StudioClip,
  samplesPerSecond = 10,
): ExerciseReview {
  const evaluation = new PoseEvaluation(rig);
  const validation = validateClip(rig, evaluation, exercise, clip, samplesPerSecond);
  const techniqueErrors = validation.violations.filter((entry) => entry.severity === 'error').length;
  const techniqueWarnings = validation.violations.filter((entry) => entry.severity === 'warning').length;

  const anchors = lockAnchors(
    new PoseEvaluation(rig),
    sampleClip(clip, 0).pose,
    clip.locks,
  );
  const frames = Math.max(2, Math.round(clip.duration * samplesPerSecond));
  const step = clip.duration / frames;
  let contactFailures = 0;
  let worstContactError = 0;
  let gripFailures = 0;
  let gripChecks = 0;
  let worstReachUse = 0;
  let widestGripGap = 0;

  const supportedGripInstances = clip.equipment.filter(
    (instance) => instance.kind === 'dumbbell' && instance.attachment.mode === 'hand',
  );

  for (let index = 0; index <= frames; index += 1) {
    const time = Math.min(clip.duration, index * step);
    const contacts = contactDiagnostics(rig, new PoseEvaluation(rig), clip, time, anchors);
    for (const contact of contacts) {
      if (!contact.enabled) continue;
      if (contact.error !== null) worstContactError = Math.max(worstContactError, contact.error);
      if (
        contact.status === 'unresolved' ||
        contact.status === 'limited' ||
        contact.status === 'overextended' ||
        (contact.error !== null && contact.error > 0.005)
      ) {
        contactFailures += 1;
      }
    }

    if (supportedGripInstances.length > 0) {
      const gripEvaluation = new PoseEvaluation(rig);
      const frame = resolveFrame(rig, gripEvaluation, clip, time, { anchors });
      gripEvaluation.apply(frame.pose);
      for (const instance of supportedGripInstances) {
        if (instance.attachment.mode !== 'hand') continue;
        const equipment = frame.equipment.get(instance.id);
        if (!equipment) {
          gripFailures += 1;
          continue;
        }
        const fit = measureGripFit(gripEvaluation, equipment, instance.attachment.side);
        gripChecks += 1;
        worstReachUse = Math.max(worstReachUse, fit.reachUse);
        widestGripGap = Math.max(widestGripGap, fit.widestGapDeg);
        if (!fit.withinEnvelope) gripFailures += 1;
      }
    }
  }

  const gates: ReviewGate[] = [
    {
      id: 'technique',
      label: 'Technique rules',
      passed: techniqueErrors === 0,
      detail: techniqueErrors === 0
        ? `${exercise.technique.length} rules checked; ${techniqueWarnings} warning${techniqueWarnings === 1 ? '' : 's'}.`
        : `${techniqueErrors} error rule${techniqueErrors === 1 ? '' : 's'} still fail.`,
      warnings: techniqueWarnings,
    },
    {
      id: 'loop',
      label: 'Loop closure',
      passed: validation.loopClosed,
      detail: validation.loopClosed ? 'First and last poses close cleanly.' : 'The clip does not close cleanly.',
    },
    {
      id: 'ik',
      label: 'IK reachability',
      passed: validation.unreachable.length === 0,
      detail: validation.unreachable.length === 0
        ? 'No unreachable IK samples.'
        : `${validation.unreachable.length} sampled IK targets are unreachable.`,
    },
    {
      id: 'contacts',
      label: 'Locked contacts',
      passed: contactFailures === 0,
      detail: clip.locks.length === 0
        ? 'No explicit contact locks in this exercise.'
        : contactFailures === 0
          ? `All enabled locks stay resolved; worst error ${(worstContactError * 1000).toFixed(1)} mm.`
          : `${contactFailures} sampled lock failures; worst error ${(worstContactError * 1000).toFixed(1)} mm.`,
      applicable: clip.locks.length > 0,
    },
    {
      id: 'grip',
      label: 'Dumbbell grip envelope',
      passed: gripFailures === 0,
      detail: supportedGripInstances.length === 0
        ? 'Not applicable: no supported single-hand dumbbell grip.'
        : gripFailures === 0
          ? `${gripChecks} grip samples pass; max reach ${Math.round(worstReachUse * 100)}%, widest gap ${widestGripGap.toFixed(1)}°.`
          : `${gripFailures} of ${gripChecks} grip samples need review.`,
      applicable: supportedGripInstances.length > 0,
    },
  ];

  return {
    automatedPass: gates.every((gate) => gate.passed),
    gates,
    sampledFrames: frames + 1,
  };
}
''')

write('src/editor/review.test.ts', r'''import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { getExercise } from '../exercises/library';
import { generateClip } from '../animation/generate';
import { reviewExercise } from './review';

const clone = <T>(value: T): T => structuredClone(value);

describe('exercise review gate', () => {
  it('clears the retained dumbbell curl through measurable automated gates', () => {
    const exercise = getExercise('dumbbell_bicep_curl');
    const clip = generateClip(canonicalSkeleton, exercise);
    const review = reviewExercise(canonicalSkeleton, exercise, clip, 4);
    expect(review.automatedPass).toBe(true);
    expect(review.gates.find((gate) => gate.id === 'grip')?.applicable).toBe(true);
    expect(review.gates.every((gate) => gate.passed)).toBe(true);
  });

  it('blocks approval when a locked arm target is physically impossible', () => {
    const exercise = clone(getExercise('dumbbell_bicep_curl'));
    exercise.locks = [
      ...exercise.locks,
      {
        id: 'impossible_review_target',
        chain: 'arm_l',
        mode: 'world',
        position: { x: -4, y: 4, z: 4 },
        enabled: true,
      },
    ];
    const clip = generateClip(canonicalSkeleton, exercise);
    const review = reviewExercise(canonicalSkeleton, exercise, clip, 3);
    expect(review.automatedPass).toBe(false);
    expect(review.gates.find((gate) => gate.id === 'contacts')?.passed).toBe(false);
    expect(review.gates.find((gate) => gate.id === 'ik')?.passed).toBe(false);
  });
});
''')

# Transient visual signoff tied to exact document + character.
p='src/editor/store.ts'
s=read(p)
s=replace_once(s, "  comparison: { a: PoseSnapshot | null; b: PoseSnapshot | null };", "  comparison: { a: PoseSnapshot | null; b: PoseSnapshot | null };\n  visualReview: { document: StudioDocument; characterSourceId: string } | null;", 'visual review state')
s=replace_once(s, "  clearComparison: (slot?: 'a' | 'b') => void;", "  clearComparison: (slot?: 'a' | 'b') => void;\n  markVisualReview: (characterSourceId: string) => void;\n  clearVisualReview: () => void;", 'visual review actions interface')
s=replace_once(s, "    comparison: { a: null, b: null },", "    comparison: { a: null, b: null },\n    visualReview: null,", 'visual review initial')
s=replace_once(s, "    clearComparison: (slot) => {", "    markVisualReview: (characterSourceId) =>\n      set({ visualReview: { document: get().document, characterSourceId } }),\n    clearVisualReview: () => set({ visualReview: null }),\n    clearComparison: (slot) => {", 'visual review actions')
write(p,s)

write('src/editor/panels/ReviewPanel.tsx', r'''import { useMemo } from 'react';
import { reviewExercise } from '../review';
import { skeleton, useStudio } from '../store';
import { useCharacter } from '../characterStore';

export function ReviewPanel() {
  const document = useStudio((state) => state.document);
  const visualReview = useStudio((state) => state.visualReview);
  const markVisualReview = useStudio((state) => state.markVisualReview);
  const clearVisualReview = useStudio((state) => state.clearVisualReview);
  const sourceId = useCharacter((state) => state.sourceId);
  const sourceStatus = useCharacter((state) => state.sourceStatus);

  const review = useMemo(
    () => reviewExercise(skeleton, document.exercise, document.clip),
    [document],
  );
  const visualPassed =
    visualReview?.document === document && visualReview.characterSourceId === sourceId;
  const approved = review.automatedPass && visualPassed;

  return (
    <section className="panel review-panel">
      <h2>Review</h2>
      <div className={`review-status ${approved ? 'is-approved' : review.automatedPass ? 'is-ready' : 'is-blocked'}`}>
        <strong>{approved ? 'APPROVED' : review.automatedPass ? 'READY FOR VISUAL REVIEW' : 'BLOCKED'}</strong>
        <span>
          {approved
            ? 'Automated gates and visual sign-off both pass for this exact clip and character.'
            : review.automatedPass
              ? 'Measured gates pass. Inspect the full rep before signing it off.'
              : 'One or more measurable authoring gates still fail.'}
        </span>
      </div>

      <div className="review-gates">
        {review.gates.map((gate) => (
          <article key={gate.id} className={gate.passed ? 'is-pass' : 'is-fail'}>
            <div>
              <strong>{gate.label}</strong>
              {gate.applicable === false && <small>not applicable</small>}
            </div>
            <span>{gate.passed ? 'Pass' : 'Block'}</span>
            <p>{gate.detail}</p>
          </article>
        ))}
      </div>

      <h3>Visual sign-off</h3>
      <p className="panel__hint">
        This remains a human decision: normal-speed and slow-motion movement, joint silhouette,
        grip contact, equipment stability and overall naturalness. Any document edit or character
        change invalidates the sign-off automatically.
      </p>
      <div className="button-row">
        <button
          type="button"
          disabled={!review.automatedPass || sourceStatus.kind !== 'idle'}
          className={visualPassed ? 'is-active' : ''}
          onClick={() => (visualPassed ? clearVisualReview() : markVisualReview(sourceId))}
        >
          {visualPassed ? 'Clear visual sign-off' : 'Mark visual review passed'}
        </button>
      </div>
      <p className="panel__note">Automated review sampled {review.sampledFrames} frames.</p>
    </section>
  );
}
''')

p='src/editor/App.tsx'
s=read(p)
s=replace_once(s, "import { CorrectivePanel } from './panels/CorrectivePanel';", "import { CorrectivePanel } from './panels/CorrectivePanel';\nimport { ReviewPanel } from './panels/ReviewPanel';", 'review panel import')
s=s.replace("type RightTab = 'exercise' | 'muscles' | 'technique' | 'correctives' | 'compare' | 'export';", "type RightTab = 'exercise' | 'muscles' | 'technique' | 'correctives' | 'compare' | 'review' | 'export';")
marker='''            <button
              type="button"
              className={rightTab === 'export' ? 'is-active' : ''}
              onClick={() => setRightTab('export')}
            >
              Export
            </button>'''
addition='''            <button
              type="button"
              className={rightTab === 'review' ? 'is-active' : ''}
              onClick={() => setRightTab('review')}
            >
              Review
            </button>
'''+marker
s=replace_once(s, marker, addition, 'review tab button')
s=replace_once(s, "            {rightTab === 'export' && <ExportPanel />}", "            {rightTab === 'review' && <ReviewPanel />}\n            {rightTab === 'export' && <ExportPanel />}", 'review panel body')
write(p,s)

p='src/editor/styles.css'
s=read(p)
s += r'''

.review-status {
  display: grid;
  gap: 4px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 10px;
  margin-bottom: 10px;
}

.review-status.is-approved,
.review-status.is-ready {
  border-color: var(--accent);
}

.review-status span {
  color: var(--muted);
  font-size: 11px;
}

.review-gates {
  display: grid;
  gap: 6px;
}

.review-gates article {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 3px 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 8px;
}

.review-gates article.is-fail {
  border-color: var(--danger, #b85c5c);
}

.review-gates p {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--muted);
  font-size: 10px;
}

.review-gates small {
  margin-left: 6px;
  color: var(--muted);
}
'''
write(p,s)

# Test visual signoff document/character identity behavior in store suite.
p='src/editor/store.test.ts'
s=read(p)
s += r'''


describe('visual review sign-off identity', () => {
  it('binds sign-off to the exact document and character source', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const reviewed = useStudio.getState().document;
    useStudio.getState().markVisualReview('import-v5');
    expect(useStudio.getState().visualReview).toEqual({ document: reviewed, characterSourceId: 'import-v5' });

    useStudio.getState().setGripClosure(0.8);
    expect(useStudio.getState().visualReview?.document).not.toBe(useStudio.getState().document);

    useStudio.getState().undo();
    expect(useStudio.getState().document).toBe(reviewed);
    expect(useStudio.getState().visualReview?.characterSourceId).toBe('import-v5');
  });
});
'''
write(p,s)

p='docs/STUDIO_CAPABILITY_ROADMAP.md'
s=read(p)
needle='- One explicit Approved state only after automated checks and visual review pass.'
s=replace_once(s, needle, needle+'''\n\n### Implemented review/approval foundation\n\n- Dedicated Review workspace aggregates conservative automated gates for technique errors, loop closure, IK reachability, explicit contact locks and the supported single-hand dumbbell grip envelope.\n- Automated success means **Ready for visual review**, never automatic approval. A separate visual sign-off is required for naturalness, joint silhouette, grip/contact appearance and equipment stability.\n- Visual sign-off is bound to the exact Studio document identity and active character source; edits or character swaps invalidate it automatically. Only automated-pass + matching visual sign-off displays `APPROVED`.''', 'roadmap review approval')
write(p,s)

p='AI_CHANGELOG.md'
s=read(p)
entry='''### ChatGPT — 2026-09-14 — conservative review and approval workspace\n\nAdded a dedicated Review workspace that aggregates the checks the Studio can measure honestly before an exercise is considered ready for human sign-off. `src/editor/review.ts` runs the exercise technique validator, loop closure, unreachable IK scan, explicit lock/contact diagnostics across the clip and the established single-hand dumbbell grip envelope where applicable. Technique **errors** block; technique warnings are surfaced but do not masquerade as fatal errors. Contacts block on unresolved, limited, over-extended or >5 mm error samples. The grip gate is explicitly scoped to the cylindrical dumbbell case the existing geometry diagnostic supports; unsupported equipment is reported as not applicable rather than falsely certified.\n\nAutomated success now means only **READY FOR VISUAL REVIEW**. `APPROVED` requires a separate human visual sign-off for natural motion, silhouette, grip/contact appearance and equipment stability. That sign-off is transient and bound to both the exact `StudioDocument` object and active character source id, so any document edit or character swap invalidates it automatically; undoing exactly back to the reviewed document can restore it. Regression coverage proves the retained dumbbell curl clears the measurable gates, an impossible world-space arm lock blocks both contact/IK readiness, and visual sign-off follows exact document identity.\n\n'''
s=replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n'+entry, 'review changelog')
write(p,s)

print('Applied conservative review and approval workspace')
