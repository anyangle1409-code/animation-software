from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


Path('src/editor/coordinationDiagnostics.ts').write_text(r'''import { sampleClip, type StudioClip } from '../animation/clip';
import type { BoneName } from '../rig/boneNames';
import { boneRotation } from '../rig/pose';
import { AXES } from '../rig/types';
import { toDeg } from '../core/math';

export interface JointSegmentTimingDiagnostic {
  bone: BoneName;
  excursionDeg: number;
  onsetTime: number | null;
  onsetPercent: number | null;
  finishTime: number | null;
  finishPercent: number | null;
}

export interface JointCoordinationDiagnostic {
  segmentStart: number;
  segmentEnd: number;
  lead: JointSegmentTimingDiagnostic;
  support: JointSegmentTimingDiagnostic;
  /** support onset minus lead onset. Positive means the selected/lead joint starts first. */
  onsetLagSeconds: number | null;
}

const shortestAngleDelta = (from: number, to: number): number =>
  Math.atan2(Math.sin(to - from), Math.cos(to - from));

function distanceDeg(
  clip: StudioClip,
  bone: BoneName,
  baseTime: number,
  time: number,
): number {
  const base = boneRotation(sampleClip(clip, baseTime).pose, bone);
  const current = boneRotation(sampleClip(clip, time).pose, bone);
  let squared = 0;
  for (const axis of AXES) {
    const degrees = toDeg(shortestAngleDelta(base[axis], current[axis]));
    squared += degrees * degrees;
  }
  return Math.sqrt(squared);
}

function measureBone(
  clip: StudioClip,
  bone: BoneName,
  segmentStart: number,
  segmentEnd: number,
): JointSegmentTimingDiagnostic {
  const duration = Math.max(1e-9, segmentEnd - segmentStart);
  const fps = clip.fps > 0 ? clip.fps : 30;
  const firstFrame = Math.floor(segmentStart * fps);
  const lastFrame = Math.ceil(segmentEnd * fps);
  const samples: { time: number; distance: number }[] = [];

  for (let frame = firstFrame; frame <= lastFrame; frame += 1) {
    const time = Math.min(segmentEnd, Math.max(segmentStart, frame / fps));
    if (samples.length && Math.abs(time - samples[samples.length - 1].time) < 1e-10) continue;
    samples.push({ time, distance: distanceDeg(clip, bone, segmentStart, time) });
  }
  if (!samples.length || samples[0].time > segmentStart + 1e-10) {
    samples.unshift({ time: segmentStart, distance: 0 });
  }
  if (samples[samples.length - 1].time < segmentEnd - 1e-10) {
    samples.push({ time: segmentEnd, distance: distanceDeg(clip, bone, segmentStart, segmentEnd) });
  }

  const excursionDeg = Math.max(...samples.map((sample) => sample.distance));
  if (excursionDeg < 0.25) {
    return { bone, excursionDeg, onsetTime: null, onsetPercent: null, finishTime: null, finishPercent: null };
  }

  // Ignore tiny floating-point/keyframe noise while still detecting deliberately
  // small support motion. Five percent works across both 126° elbow flexion and
  // the curl's subtle 4° upper-arm contribution; 0.1° is the absolute floor.
  const onsetThreshold = Math.max(0.1, excursionDeg * 0.05);
  const finishThreshold = excursionDeg * 0.95;
  const onset = samples.find((sample) => sample.distance >= onsetThreshold) ?? null;
  const finish = samples.find((sample) => sample.distance >= finishThreshold) ?? null;

  const percent = (time: number | null): number | null =>
    time === null ? null : Math.max(0, Math.min(1, (time - segmentStart) / duration));

  return {
    bone,
    excursionDeg,
    onsetTime: onset?.time ?? null,
    onsetPercent: percent(onset?.time ?? null),
    finishTime: finish?.time ?? null,
    finishPercent: percent(finish?.time ?? null),
  };
}

/**
 * Compare movement timing for a selected joint and a support/parent joint in
 * one authored keyframe segment. This reports coordination; it never labels a
 * lag as good/bad because sequencing is exercise-specific.
 */
export function measureJointCoordination(
  clip: StudioClip,
  leadBone: BoneName,
  supportBone: BoneName,
  segmentStart: number,
  segmentEnd: number,
): JointCoordinationDiagnostic {
  const lead = measureBone(clip, leadBone, segmentStart, segmentEnd);
  const support = measureBone(clip, supportBone, segmentStart, segmentEnd);
  return {
    segmentStart,
    segmentEnd,
    lead,
    support,
    onsetLagSeconds:
      lead.onsetTime !== null && support.onsetTime !== null
        ? support.onsetTime - lead.onsetTime
        : null,
  };
}
''')

Path('src/editor/coordinationDiagnostics.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import type { StudioClip } from '../animation/clip';
import { restPose } from '../rig/pose';
import { vec3 } from '../rig/types';
import { measureJointCoordination } from './coordinationDiagnostics';

const delayedSupportClip = (): StudioClip => {
  const start = restPose();
  start.rotations.forearm_l = vec3(0, 0, 0);
  start.rotations.upperarm_l = vec3(0, 0, 0);
  const end = restPose();
  end.rotations.forearm_l = vec3(Math.PI / 2, 0, 0);
  end.rotations.upperarm_l = vec3((20 * Math.PI) / 180, 0, 0);
  return {
    id: 'coordination-diagnostic',
    name: 'coordination_diagnostic',
    exerciseId: 'diagnostic',
    duration: 1,
    fps: 30,
    loop: false,
    keyframes: [
      {
        id: 'start',
        time: 0,
        pose: start,
        ik: {},
        easing: 'linear',
        jointTiming: { upperarm_l: { delay: 0.5, finish: 1, easing: 'linear' } },
      },
      { id: 'end', time: 1, pose: end, ik: {}, easing: 'hold' },
    ],
    locks: [],
    equipment: [],
  };
};

describe('joint coordination diagnostics', () => {
  it('shows a delayed parent/support joint starting after the lead elbow', () => {
    const result = measureJointCoordination(delayedSupportClip(), 'forearm_l', 'upperarm_l', 0, 1);
    expect(result.lead.excursionDeg).toBeCloseTo(90, 6);
    expect(result.support.excursionDeg).toBeCloseTo(20, 6);
    expect(result.lead.onsetPercent).not.toBeNull();
    expect(result.support.onsetPercent).not.toBeNull();
    expect(result.onsetLagSeconds).not.toBeNull();
    expect(result.onsetLagSeconds!).toBeGreaterThan(0.45);
    expect(result.support.onsetPercent!).toBeGreaterThan(0.5);
  });

  it('reports near-isometric support without inventing an onset', () => {
    const clip = delayedSupportClip();
    clip.keyframes[1].pose.rotations.upperarm_l = vec3(0, 0, 0);
    const result = measureJointCoordination(clip, 'forearm_l', 'upperarm_l', 0, 1);
    expect(result.support.excursionDeg).toBeLessThan(0.25);
    expect(result.support.onsetTime).toBeNull();
    expect(result.onsetLagSeconds).toBeNull();
  });
});
''')

p = 'src/editor/panels/JointPanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import { measureJointMotion } from '../motionDiagnostics';\n",
    "import { measureJointMotion } from '../motionDiagnostics';\nimport { measureJointCoordination } from '../coordinationDiagnostics';\n",
    'coordination import',
)
s = replace_once(
    s,
    "  const timing = selected && segmentFrom ? segmentFrom.jointTiming?.[selected] : undefined;\n",
    "  const timing = selected && segmentFrom ? segmentFrom.jointTiming?.[selected] : undefined;\n  const parentBone = selected ? skeleton.bone(selected).parent : null;\n  const coordination = useMemo(\n    () =>\n      selected && parentBone && segmentFrom && segmentTo\n        ? measureJointCoordination(clip, selected, parentBone, segmentFrom.time, segmentTo.time)\n        : null,\n    [clip, parentBone, segmentFrom, segmentTo, selected],\n  );\n",
    'coordination memo',
)
s = replace_once(
    s,
    "      <h3>Segment timing</h3>\n",
    "      <h3>Joint coordination</h3>\n      {selected && parentBone && coordination ? (\n        <div className=\"joint-coordination\">\n          <p className=\"panel__hint\">\n            Current segment · <strong>{boneLabel(selected)}</strong> compared with its parent\n            <strong> {boneLabel(parentBone)}</strong>. Onset is the first meaningful movement, not\n            a pass/fail judgement.\n          </p>\n          <dl className=\"spec-list\">\n            <dt>{boneLabel(selected)} excursion</dt>\n            <dd>{coordination.lead.excursionDeg.toFixed(1)}°</dd>\n            <dt>{boneLabel(selected)} onset</dt>\n            <dd>{coordination.lead.onsetPercent === null ? 'Near-isometric' : `${Math.round(coordination.lead.onsetPercent * 100)}% · ${coordination.lead.onsetTime!.toFixed(2)}s`}</dd>\n            <dt>{boneLabel(parentBone)} excursion</dt>\n            <dd>{coordination.support.excursionDeg.toFixed(1)}°</dd>\n            <dt>{boneLabel(parentBone)} onset</dt>\n            <dd>{coordination.support.onsetPercent === null ? 'Near-isometric' : `${Math.round(coordination.support.onsetPercent * 100)}% · ${coordination.support.onsetTime!.toFixed(2)}s`}</dd>\n            <dt>Parent onset lag</dt>\n            <dd>{coordination.onsetLagSeconds === null ? '—' : `${coordination.onsetLagSeconds >= 0 ? '+' : ''}${coordination.onsetLagSeconds.toFixed(2)}s`}</dd>\n          </dl>\n          <div className=\"button-row\">\n            <button type=\"button\" onClick={() => selectBone(parentBone)}>\n              Select parent to tune timing\n            </button>\n            {coordination.support.onsetTime !== null && (\n              <button type=\"button\" onClick={() => setTime(coordination.support.onsetTime!)}>\n                Jump to parent onset\n              </button>\n            )}\n          </div>\n          <p className=\"panel__note\">\n            For a curl, selecting the forearm compares elbow flexion with upper-arm contribution.\n            Use Segment timing on the parent to delay or soften that secondary movement.\n          </p>\n        </div>\n      ) : (\n        <p className=\"panel__empty\">Select a non-root joint before the final keyframe to compare its timing with its parent.</p>\n      )}\n\n      <h3>Segment timing</h3>\n",
    'coordination UI',
)
write(p, s)

p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
s = replace_once(
    s,
    '- Selected-joint frame-by-frame motion diagnostics report worst angular speed and acceleration with exact timestamps and jump-to-frame controls, giving elbow/shoulder timing review an objective signal without imposing a universal movement threshold.\n',
    '- Selected-joint frame-by-frame motion diagnostics report worst angular speed and acceleration with exact timestamps and jump-to-frame controls, giving elbow/shoulder timing review an objective signal without imposing a universal movement threshold.\n- Segment-local joint coordination compares the selected joint against its anatomical parent, reporting excursion, meaningful-motion onset and onset lag; the parent can be selected directly for timing edits, making elbow-led/shoulder-follow sequencing explicit without extra stop/start keys.\n',
    'roadmap coordination',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — parent/child joint coordination diagnostics\n\nAdded `src/editor/coordinationDiagnostics.ts` to measure selected-joint versus anatomical-parent sequencing inside the current keyframe segment. It samples the actual generated clip at authored FPS, measures 3-axis shortest-path excursion from the segment start, identifies the first meaningful motion (5% of excursion with a 0.1° floor), records 95% finish timing, and reports parent-onset lag. A joint moving less than 0.25° is treated as near-isometric rather than being assigned a fake onset. There is deliberately no universal good/bad lag threshold because sequencing depends on the exercise.\n\nThe Joint workspace now shows selected/parent excursion and onset, parent onset lag, a direct `Select parent to tune timing` action, and `Jump to parent onset`. For the bicep curl this means selecting the forearm makes elbow flexion versus upper-arm/shoulder contribution directly inspectable, while the existing Segment timing controls remain the one place that changes delay/finish/easing. Regression coverage proves a synthetic upper-arm support motion with a 50% authored delay begins materially after an immediately moving forearm, and proves a truly stationary parent is reported as near-isometric.\n\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'changelog insertion')
write(p, s)

print('Applied parent/child joint coordination diagnostics')
