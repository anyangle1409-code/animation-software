from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text()


def write(path: str, text: str) -> None:
    Path(path).write_text(text)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)


Path('src/editor/gripReview.ts').write_text(r'''import { resolveFrame } from '../animation/pipeline';
import type { StudioClip } from '../animation/clip';
import { measureGripFit } from '../equipment/gripDiagnostics';
import { FINGERS, type Finger, type Side } from '../rig/boneNames';
import { PoseEvaluation, type Skeleton } from '../rig/skeleton';

export interface GripDigitWorstPoint {
  reachUse: number;
  time: number;
}

export interface GripWorstPointSweep {
  instanceId: string;
  side: Side;
  digits: Record<Finger, GripDigitWorstPoint>;
  overall: GripDigitWorstPoint & { finger: Finger };
}

const emptyDigits = (): Record<Finger, GripDigitWorstPoint> => ({
  thumb: { reachUse: -Infinity, time: 0 },
  index: { reachUse: -Infinity, time: 0 },
  middle: { reachUse: -Infinity, time: 0 },
  ring: { reachUse: -Infinity, time: 0 },
  pinky: { reachUse: -Infinity, time: 0 },
});

/**
 * Scan every authored animation frame and retain the worst contact-reach point
 * for each digit on each single-hand equipment instance.
 *
 * This deliberately reuses the production frame pipeline and the established
 * grip envelope. It is an authoring diagnostic only: it never edits the grip,
 * equipment transform, wrist or accepted animation.
 */
export function scanGripWorstCases(
  skeleton: Skeleton,
  clip: StudioClip,
): GripWorstPointSweep[] {
  const handInstances = clip.equipment.filter((instance) => instance.attachment.mode === 'hand');
  if (handInstances.length === 0) return [];

  const sweeps = new Map<string, GripWorstPointSweep>();
  for (const instance of handInstances) {
    if (instance.attachment.mode !== 'hand') continue;
    sweeps.set(instance.id, {
      instanceId: instance.id,
      side: instance.attachment.side,
      digits: emptyDigits(),
      overall: { finger: 'thumb', reachUse: -Infinity, time: 0 },
    });
  }

  const evaluation = new PoseEvaluation(skeleton);
  const fps = clip.fps > 0 ? clip.fps : 30;
  const lastFrame = Math.max(1, Math.ceil(clip.duration * fps));

  for (let frameIndex = 0; frameIndex <= lastFrame; frameIndex += 1) {
    const time = Math.min(clip.duration, frameIndex / fps);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);

    for (const instance of handInstances) {
      if (instance.attachment.mode !== 'hand') continue;
      const transform = frame.equipment.get(instance.id);
      const sweep = sweeps.get(instance.id);
      if (!transform || !sweep) continue;

      const fit = measureGripFit(evaluation, transform, instance.attachment.side);
      for (const finger of FINGERS) {
        const reachUse = fit.digitReachUse[finger];
        if (reachUse > sweep.digits[finger].reachUse) {
          sweep.digits[finger] = { reachUse, time };
        }
        if (reachUse > sweep.overall.reachUse) {
          sweep.overall = { finger, reachUse, time };
        }
      }
    }
  }

  return [...sweeps.values()].filter((sweep) => Number.isFinite(sweep.overall.reachUse));
}
''')

Path('src/editor/gripReview.test.ts').write_text(r'''import { describe, expect, it } from 'vitest';
import { generateClip } from '../animation/generate';
import { resolveFrame } from '../animation/pipeline';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { FINGERS } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { measureGripFit } from '../equipment/gripDiagnostics';
import { scanGripWorstCases } from './gripReview';

const skeleton = canonicalSkeleton;

describe('whole-rep grip review', () => {
  it('records each digit worst point at an authored animation frame', () => {
    const clip = generateClip(skeleton, bicepCurl);
    const sweeps = scanGripWorstCases(skeleton, clip);

    expect(sweeps).toHaveLength(2);
    for (const sweep of sweeps) {
      expect(sweep.overall.time).toBeGreaterThanOrEqual(0);
      expect(sweep.overall.time).toBeLessThanOrEqual(clip.duration);
      expect(Math.abs(sweep.overall.time * clip.fps - Math.round(sweep.overall.time * clip.fps))).toBeLessThan(1e-8);

      const evaluation = new PoseEvaluation(skeleton);
      for (const finger of FINGERS) {
        const worst = sweep.digits[finger];
        expect(worst.reachUse).toBeGreaterThan(0);
        expect(worst.time).toBeGreaterThanOrEqual(0);
        expect(worst.time).toBeLessThanOrEqual(clip.duration);

        const frame = resolveFrame(skeleton, evaluation, clip, worst.time);
        evaluation.apply(frame.pose);
        const transform = frame.equipment.get(sweep.instanceId);
        expect(transform).toBeDefined();
        const fit = measureGripFit(evaluation, transform!, sweep.side);
        expect(fit.digitReachUse[finger]).toBeCloseTo(worst.reachUse, 10);
      }

      expect(sweep.overall.reachUse).toBeCloseTo(
        Math.max(...FINGERS.map((finger) => sweep.digits[finger].reachUse)),
        10,
      );
    }
  });
});
''')

p = 'src/editor/panels/GripPanel.tsx'
s = read(p)
s = replace_once(
    s,
    "import { skeleton, useStudio } from '../store';\n",
    "import { skeleton, useStudio } from '../store';\nimport { scanGripWorstCases } from '../gripReview';\n",
    'GripPanel import',
)
s = replace_once(
    s,
    "  const time = useStudio((state) => state.time);\n",
    "  const time = useStudio((state) => state.time);\n  const setTime = useStudio((state) => state.setTime);\n",
    'GripPanel setTime',
)
s = replace_once(
    s,
    "  const twoHandMeasurements = useMemo(() => {\n",
    "  const wholeRepById = useMemo(\n    () => new Map(scanGripWorstCases(skeleton, clip).map((sweep) => [sweep.instanceId, sweep])),\n    [clip],\n  );\n\n  const twoHandMeasurements = useMemo(() => {\n",
    'GripPanel whole-rep memo',
)
s = replace_once(
    s,
    "              </dl>\n            </div>\n          ))}\n",
    "              </dl>\n              {wholeRepById.get(id) && (\n                <>\n                  <h4>Worst points in rep</h4>\n                  <div className=\"button-row grip-worst-points\">\n                    {FINGERS.map((finger) => {\n                      const worst = wholeRepById.get(id)!.digits[finger];\n                      return (\n                        <button\n                          type=\"button\"\n                          key={`worst-${id}-${finger}`}\n                          className={worst.reachUse >= 1 ? 'status-warn' : undefined}\n                          onClick={() => setTime(worst.time)}\n                          title={`Jump to ${finger} worst point`}\n                        >\n                          {finger.charAt(0).toUpperCase() + finger.slice(1)} · {Math.round(worst.reachUse * 100)}% · {worst.time.toFixed(2)}s\n                        </button>\n                      );\n                    })}\n                  </div>\n                  <p className=\"panel__note\">\n                    Frame-by-frame at {clip.fps} fps. Tap a digit to inspect its worst measured frame.\n                  </p>\n                </>\n              )}\n            </div>\n          ))}\n",
    'GripPanel worst-point UI',
)
s = replace_once(
    s,
    "        contact-reach and wrap geometry as the Studio's grip regression. A digit above 100% has exceeded that authored geometric envelope; this is not a literal mesh-penetration, force or injury-safety score.\n",
    "        contact-reach and wrap geometry as the Studio's grip regression. Whole-rep worst points scan every authored animation frame at the clip FPS. A digit above 100% has exceeded that authored geometric envelope; this is not a literal mesh-penetration, force or injury-safety score.\n",
    'GripPanel diagnostic note',
)
write(p, s)

p = 'docs/STUDIO_CAPABILITY_ROADMAP.md'
s = read(p)
s = replace_once(
    s,
    '- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in.\n',
    '- Per-digit closure trims can independently adjust thumb/index/middle/ring/pinky on top of the active grip profile while unspecified digits continue to follow global closure. Defaults are absent, so accepted grips remain byte-for-byte generator-compatible until an author opts in.\n- Live per-digit grip reach plus whole-rep frame-by-frame worst-point review identifies which digit exceeds the authored envelope, records the exact worst timestamp, and can jump the playhead directly to that frame without modifying the animation.\n',
    'roadmap grip review',
)
write(p, s)

p = 'AI_CHANGELOG.md'
s = read(p)
entry = '''### ChatGPT — 2026-09-14 — whole-rep grip worst-point review\n\nAdded `src/editor/gripReview.ts` to scan every authored animation frame at `clip.fps` through the same production `resolveFrame()` pipeline used by the viewport. For each single-hand equipment instance it records the worst contact-reach value and exact timestamp for thumb/index/middle/ring/pinky, plus the overall worst digit. The scan reuses the established `measureGripFit()` envelope and is diagnostic only: it never edits finger closure, equipment placement, wrist/arm pose or the accepted clip.\n\nThe Grip workspace now shows one jump button per digit with its whole-rep worst percentage and timestamp. Selecting it moves the playhead directly to the measured frame so localized thumb/pinky problems can be inspected without blind scrubbing. Regression coverage proves both retained curl dumbbells are scanned, worst points lie on authored frame times, re-measuring each recorded timestamp reproduces the stored digit value, and the overall value equals the maximum digit worst case.\n\n\n'''
s = replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n' + entry, 'changelog insertion')
write(p, s)

print('Applied whole-rep grip worst-point review')
