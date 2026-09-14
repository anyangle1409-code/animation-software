from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


Path('src/editor/strainReview.ts').write_text(r'''import { resolveFrame } from '../animation/pipeline';
import type { StudioClip } from '../animation/clip';
import { applyCharacterPose } from '../character';
import type { CharacterBuild } from '../character';
import { suppressCorrectives } from '../character/correctiveDiagnostics';
import { meshStrainDiagnostics } from '../character/meshStrain';
import { PoseEvaluation, type Skeleton } from '../rig/skeleton';

export interface TimedStrainValue {
  value: number;
  time: number;
}

export interface MeshStrainWorstPoint {
  mesh: string;
  p95: TimedStrainValue;
  p99: TimedStrainValue;
  max: TimedStrainValue;
  severeCompression: TimedStrainValue;
  severeStretch: TimedStrainValue;
  sampledEdges: number;
}

const updateWorst = (current: TimedStrainValue, value: number, time: number): TimedStrainValue =>
  value > current.value ? { value, time } : current;

function applyAtTime(
  character: CharacterBuild,
  rig: Skeleton,
  clip: StudioClip,
  time: number,
  correctivesEnabled: boolean,
  evaluation: PoseEvaluation,
): void {
  const frame = resolveFrame(rig, evaluation, clip, time);
  evaluation.apply(frame.pose);
  applyCharacterPose(character, rig, frame.pose, evaluation, { contacts: frame.contacts });
  if (!correctivesEnabled) suppressCorrectives(character.meshes);
}

/**
 * Scan strain across every authored animation frame, then restore the character
 * to the playhead pose that was active before the scan.
 *
 * The edge budget is deliberately bounded because this is an interactive
 * authoring locator, not an offline finite-element analysis. Values reuse the
 * same bind-vs-posed edge metric as the live Correctives panel.
 */
export function scanMeshStrainWorstCases(
  character: CharacterBuild,
  rig: Skeleton,
  clip: StudioClip,
  correctivesEnabled: boolean,
  restoreTime: number,
  maxEdgesPerMesh = 1200,
): MeshStrainWorstPoint[] {
  const evaluation = new PoseEvaluation(rig);
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));
  const out = new Map<string, MeshStrainWorstPoint>();

  try {
    for (let frameIndex = 0; frameIndex <= lastFrame; frameIndex += 1) {
      const time = Math.min(clip.duration, frameIndex / fps);
      applyAtTime(character, rig, clip, time, correctivesEnabled, evaluation);
      for (const diagnostic of meshStrainDiagnostics(character.meshes, maxEdgesPerMesh)) {
        const current = out.get(diagnostic.mesh) ?? {
          mesh: diagnostic.mesh,
          p95: { value: -Infinity, time },
          p99: { value: -Infinity, time },
          max: { value: -Infinity, time },
          severeCompression: { value: -Infinity, time },
          severeStretch: { value: -Infinity, time },
          sampledEdges: diagnostic.sampledEdges,
        };
        current.p95 = updateWorst(current.p95, diagnostic.p95, time);
        current.p99 = updateWorst(current.p99, diagnostic.p99, time);
        current.max = updateWorst(current.max, diagnostic.max, time);
        current.severeCompression = updateWorst(
          current.severeCompression,
          diagnostic.severeCompression,
          time,
        );
        current.severeStretch = updateWorst(current.severeStretch, diagnostic.severeStretch, time);
        current.sampledEdges = diagnostic.sampledEdges;
        out.set(diagnostic.mesh, current);
      }
    }
  } finally {
    applyAtTime(character, rig, clip, restoreTime, correctivesEnabled, evaluation);
  }

  return [...out.values()].filter((item) => Number.isFinite(item.max.value));
}
''')

Path('src/editor/strainReview.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { builtinCharacter } from '../character/builtin';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { canonicalSkeleton } from '../rig/skeleton';
import { scanMeshStrainWorstCases } from './strainReview';

const skeleton = canonicalSkeleton;

describe('whole-rep deformation review', () => {
  it('finds finite worst strain frames and restores a bounded diagnostic scan', async () => {
    const character = await builtinCharacter.build(skeleton);
    try {
      const clip = generateClip(skeleton, bicepCurl);
      clip.fps = 4; // Keep the regression cheap; production uses the authored clip FPS.
      const result = scanMeshStrainWorstCases(character, skeleton, clip, true, 1.25, 80);
      expect(result.length).toBeGreaterThan(0);
      for (const item of result) {
        expect(item.sampledEdges).toBeGreaterThan(0);
        for (const metric of [item.p95, item.p99, item.max]) {
          expect(Number.isFinite(metric.value)).toBe(true);
          expect(metric.value).toBeGreaterThanOrEqual(0);
          expect(metric.time).toBeGreaterThanOrEqual(0);
          expect(metric.time).toBeLessThanOrEqual(clip.duration);
        }
      }
    } finally {
      character.dispose();
    }
  });
});
''')

p = 'src/editor/panels/CorrectivePanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import { useEffect, useState } from 'react';\n",
    "import { useEffect, useState } from 'react';\n",
    'CorrectivePanel react import',
)
s = replace_once(
    s,
    "import { useStudio } from '../store';\n",
    "import { skeleton, useStudio } from '../store';\nimport { scanMeshStrainWorstCases, type MeshStrainWorstPoint } from '../strainReview';\n",
    'CorrectivePanel strain review import',
)
s = replace_once(
    s,
    "  // Time subscription makes the panel refresh while playback mutates morph influences.\n  useStudio((state) => state.time);\n",
    "  // Time subscription makes the panel refresh while playback mutates morph influences.\n  const time = useStudio((state) => state.time);\n  const setTime = useStudio((state) => state.setTime);\n  const clip = useStudio((state) => state.document.clip);\n",
    'CorrectivePanel studio state',
)
s = replace_once(
    s,
    "  const [strain, setStrain] = useState<MeshStrainDiagnostic[]>([]);\n",
    "  const [strain, setStrain] = useState<MeshStrainDiagnostic[]>([]);\n  const [wholeRep, setWholeRep] = useState<{ enabled: boolean; items: MeshStrainWorstPoint[] } | null>(null);\n",
    'CorrectivePanel scan state',
)
s = replace_once(
    s,
    "  }, [active, enabled]);\n\n  return (\n",
    "  }, [active, enabled]);\n\n  useEffect(() => setWholeRep(null), [active, clip, enabled]);\n\n  const scanWholeRep = () => {\n    if (!active) return;\n    const items = scanMeshStrainWorstCases(active, skeleton, clip, enabled, time);\n    setWholeRep({ enabled, items });\n  };\n\n  return (\n",
    'CorrectivePanel scan action',
)
s = replace_once(
    s,
    "      <div className=\"strain-list\">\n",
    "      <div className=\"button-row\">\n        <button type=\"button\" disabled={!active} onClick={scanWholeRep}>\n          Scan full rep\n        </button>\n      </div>\n      {wholeRep && (\n        <div className=\"strain-list\">\n          {wholeRep.items.map((item) => (\n            <div key={`whole-rep-${item.mesh}`} className=\"strain-card\">\n              <strong>{item.mesh} · {wholeRep.enabled ? 'Correctives on' : 'Raw skinning'}</strong>\n              <span>Worst P99 {(item.p99.value * 100).toFixed(1)}% · {item.p99.time.toFixed(2)}s</span>\n              <span>Worst max {(item.max.value * 100).toFixed(1)}% · {item.max.time.toFixed(2)}s</span>\n              <span>Worst compression count · {item.severeCompression.value.toFixed(0)} · {item.severeCompression.time.toFixed(2)}s</span>\n              <span>Worst stretch count · {item.severeStretch.value.toFixed(0)} · {item.severeStretch.time.toFixed(2)}s</span>\n              <div className=\"button-row\">\n                <button type=\"button\" onClick={() => setTime(item.p99.time)}>Jump to worst P99</button>\n                <button type=\"button\" onClick={() => setTime(item.max.time)}>Jump to worst edge</button>\n              </div>\n              <small>{item.sampledEdges} sampled edges per frame</small>\n            </div>\n          ))}\n        </div>\n      )}\n      <p className=\"panel__hint\">\n        Full-rep scan runs only when requested, follows the clip FPS, restores the current playhead pose, and uses a bounded edge sample so it remains an authoring locator rather than a simulation.\n      </p>\n      <div className=\"strain-list\">\n",
    'CorrectivePanel full-rep UI',
)
write(p, s)

p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
s = replace_once(
    s,
    '- Live surface-strain diagnostics sample posed mesh edges against bind geometry and report P95/P99/max strain plus >20% compression/stretch counts; rigid transforms correctly read as zero strain.\n',
    '- Live surface-strain diagnostics sample posed mesh edges against bind geometry and report P95/P99/max strain plus >20% compression/stretch counts; rigid transforms correctly read as zero strain.\n- On-demand whole-rep strain review scans the active character at the authored clip FPS, records worst P99/max deformation timestamps for each mesh, restores the current playhead pose, and can jump directly to the worst frame in either Correctives-on or Raw-skinning mode.\n',
    'roadmap whole-rep strain',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — whole-rep deformation worst-point review\n\nAdded `src/editor/strainReview.ts`, an on-demand authoring scan that poses the active character through every authored clip frame using the same `resolveFrame()` + `applyCharacterPose()` production path, measures the existing bind-vs-posed edge-strain diagnostic, and records worst P95/P99/max strain plus severe compression/stretch-count timestamps per mesh. The scan respects the current Correctives-on/Raw-skinning viewport mode and always restores the character to the pre-scan playhead pose in a `finally` block. Its per-frame edge budget is bounded so this remains an interactive locator, not a force or finite-element model.\n\nThe Correctives workspace now exposes `Scan full rep` and shows the mode that was scanned, worst P99/max values and timestamps, severe-count worst points, and jump-to-frame controls. This gives elbow/shoulder corrective review a direct route to the frame where surface deformation is objectively worst before comparing the silhouette. Regression coverage builds the real built-in character, runs a deliberately low-FPS/low-edge-budget scan for CI cost, and verifies finite bounded worst-frame results.\n\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'changelog insertion')
write(p, s)

print('Applied whole-rep deformation worst-point review')
