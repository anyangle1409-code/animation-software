from pathlib import Path


def replace(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f"missing anchor in {path}: {old[:90]!r}")
    p.write_text(text.replace(old, new, 1))

# Whole-rep sweep helper: visit explicit control values, reuse the existing
# production strain scan, and restore both the control and the playhead pose.
replace(
    "src/editor/strainReview.ts",
    "import type { CharacterBuild } from '../character';",
    "import type { CharacterBuild, DeformationControl } from '../character';",
)
p = Path("src/editor/strainReview.ts")
text = p.read_text()
addition = r'''

export interface CorrectiveSweepWorstPoint extends TimedStrainValue {
  mesh: string;
}

export interface CorrectiveSweepPoint {
  value: number;
  p99: CorrectiveSweepWorstPoint | null;
  max: CorrectiveSweepWorstPoint | null;
  items: MeshStrainWorstPoint[];
}

function worstAcross(
  items: MeshStrainWorstPoint[],
  metric: 'p99' | 'max',
): CorrectiveSweepWorstPoint | null {
  let worst: CorrectiveSweepWorstPoint | null = null;
  for (const item of items) {
    const value = item[metric];
    if (!worst || value.value > worst.value) {
      worst = { mesh: item.mesh, value: value.value, time: value.time };
    }
  }
  return worst;
}

/**
 * Compare a bounded character-level deformation control at explicit values.
 *
 * This is deliberately an authoring measurement, not an optimiser: it never
 * chooses a winner or changes the accepted value. Every point reuses the same
 * whole-rep production pose/strain path, then the original control value and
 * playhead pose are restored even if a scan throws.
 */
export function scanDeformationControlSweep(
  character: CharacterBuild,
  control: DeformationControl,
  rig: Skeleton,
  clip: StudioClip,
  correctivesEnabled: boolean,
  restoreTime: number,
  values: readonly number[] = [0, 0.25, 0.5, 0.75, 1],
  maxEdgesPerMesh = 600,
): CorrectiveSweepPoint[] {
  const original = control.value;
  const result: CorrectiveSweepPoint[] = [];
  try {
    for (const requested of values) {
      control.set(requested);
      const value = control.value;
      const items = scanMeshStrainWorstCases(
        character,
        rig,
        clip,
        correctivesEnabled,
        restoreTime,
        maxEdgesPerMesh,
      );
      result.push({ value, p99: worstAcross(items, 'p99'), max: worstAcross(items, 'max'), items });
    }
  } finally {
    control.set(original);
    const evaluation = new PoseEvaluation(rig);
    applyAtTime(character, rig, clip, restoreTime, correctivesEnabled, evaluation);
  }
  return result;
}
'''
text += addition
p.write_text(text)

# Correctives UI: one-click objective sweep, review any measured preset at its
# worst P99 frame, but never automatically select a permanent value.
p = Path("src/editor/panels/CorrectivePanel.tsx")
text = p.read_text()
text = text.replace(
    "import { scanMeshStrainWorstCases, type MeshStrainWorstPoint } from '../strainReview';",
    "import {\n  scanDeformationControlSweep,\n  scanMeshStrainWorstCases,\n  type CorrectiveSweepPoint,\n  type MeshStrainWorstPoint,\n} from '../strainReview';",
    1,
)
text = text.replace(
    "  const [wholeRep, setWholeRep] = useState<{ enabled: boolean; items: MeshStrainWorstPoint[] } | null>(null);",
    "  const [wholeRep, setWholeRep] = useState<{ enabled: boolean; items: MeshStrainWorstPoint[] } | null>(null);\n  const [sweep, setSweep] = useState<{ controlId: string; points: CorrectiveSweepPoint[] } | null>(null);",
    1,
)
text = text.replace(
    "  useEffect(() => setWholeRep(null), [active, clip, enabled]);",
    "  useEffect(() => {\n    setWholeRep(null);\n    setSweep(null);\n  }, [active, clip, enabled]);",
    1,
)
old = """              <div className=\"button-row\">\n                <button\n                  type=\"button\"\n                  disabled={Math.abs(control.value - control.defaultValue) < 1e-9}\n                  onClick={() => {\n                    control.set(control.defaultValue);\n                    refreshControls((value) => value + 1);\n                    setWholeRep(null);\n                  }}\n                >\n                  Reset authored value\n                </button>\n              </div>\n            </div>\n"""
new = """              <div className=\"button-row\">\n                <button\n                  type=\"button\"\n                  disabled={Math.abs(control.value - control.defaultValue) < 1e-9}\n                  onClick={() => {\n                    control.set(control.defaultValue);\n                    refreshControls((value) => value + 1);\n                    setWholeRep(null);\n                    setSweep(null);\n                  }}\n                >\n                  Reset authored value\n                </button>\n                <button\n                  type=\"button\"\n                  disabled={!active || !enabled}\n                  onClick={() => {\n                    if (!active) return;\n                    const points = scanDeformationControlSweep(\n                      active,\n                      control,\n                      skeleton,\n                      clip,\n                      enabled,\n                      time,\n                    );\n                    setSweep({ controlId: control.id, points });\n                    refreshControls((value) => value + 1);\n                  }}\n                >\n                  Compare 0–100%\n                </button>\n              </div>\n              {!enabled && (\n                <small>Enable Correctives on before comparing candidate strengths.</small>\n              )}\n              {sweep?.controlId === control.id && (\n                <div className=\"strain-list\">\n                  {sweep.points.map((point) => (\n                    <div className=\"strain-card\" key={`sweep-${control.id}-${point.value}`}>\n                      <strong>{Math.round(point.value * 100)}%</strong>\n                      <span>Worst P99 {point.p99 ? `${(point.p99.value * 100).toFixed(1)}% · ${point.p99.time.toFixed(2)}s` : '—'}</span>\n                      <span>Worst edge {point.max ? `${(point.max.value * 100).toFixed(1)}% · ${point.max.time.toFixed(2)}s` : '—'}</span>\n                      <button\n                        type=\"button\"\n                        disabled={!point.p99}\n                        onClick={() => {\n                          control.set(point.value);\n                          refreshControls((value) => value + 1);\n                          setWholeRep(null);\n                          if (point.p99) setTime(point.p99.time);\n                        }}\n                      >\n                        Review this value at worst P99\n                      </button>\n                    </div>\n                  ))}\n                </div>\n              )}\n              {sweep?.controlId === control.id && (\n                <small>The sweep restores the value that was active before scanning. Results measure strain only; silhouette and natural motion still require visual review.</small>\n              )}\n            </div>\n"""
if old not in text:
    raise SystemExit("missing corrective control button anchor")
text = text.replace(old, new, 1)
p.write_text(text)

# Regression keeps the scan cheap while proving every requested value is visited
# and the source-level control is restored afterwards.
p = Path("src/editor/strainReview.test.ts")
text = p.read_text()
text = text.replace(
    "import { scanMeshStrainWorstCases } from './strainReview';",
    "import { scanDeformationControlSweep, scanMeshStrainWorstCases } from './strainReview';\nimport type { DeformationControl } from '../character';",
    1,
)
addition = r'''

  it('sweeps explicit corrective values and restores the original source value', async () => {
    const character = await builtinCharacter.build(skeleton);
    try {
      const clip = generateClip(skeleton, bicepCurl);
      clip.fps = 2;
      let value = 0.37;
      const visited: number[] = [];
      const control: DeformationControl = {
        id: 'testCorrective',
        label: 'Test corrective',
        min: 0,
        max: 1,
        step: 0.25,
        defaultValue: 0,
        get value() {
          return value;
        },
        set(next) {
          value = Math.min(1, Math.max(0, next));
          visited.push(value);
        },
      };

      const result = scanDeformationControlSweep(
        character,
        control,
        skeleton,
        clip,
        true,
        1.25,
        [0, 0.5, 1],
        40,
      );
      expect(result.map((point) => point.value)).toEqual([0, 0.5, 1]);
      expect(visited).toEqual(expect.arrayContaining([0, 0.5, 1, 0.37]));
      expect(control.value).toBeCloseTo(0.37, 8);
      for (const point of result) {
        expect(point.p99).not.toBeNull();
        expect(point.max).not.toBeNull();
        expect(point.p99!.time).toBeGreaterThanOrEqual(0);
        expect(point.p99!.time).toBeLessThanOrEqual(clip.duration);
      }
    } finally {
      character.dispose();
    }
  });
'''
pos = text.rfind("\n});")
if pos < 0:
    raise SystemExit("missing strain review suite end")
text = text[:pos] + addition + text[pos:]
p.write_text(text)

replace(
    "docs/STUDIO_CAPABILITY_ROADMAP.md",
    "- Imported elbow outer-smoothing is now a bounded 0–100% character-level control. The retained radial volume morph remains separate, the measured candidate morph stays capped at 8 mm, and the active viewport plus GLB export sampler share the exact same source-level tuning value.",
    "- Imported elbow outer-smoothing is now a bounded 0–100% character-level control. The retained radial volume morph remains separate, the measured candidate morph stays capped at 8 mm, and the active viewport plus GLB export sampler share the exact same source-level tuning value.\n- Corrective tuning can run an on-demand 0/25/50/75/100% whole-rep strain sweep, report worst P99/max frame for each value, restore the pre-scan tuning and pose, and jump to any measured value for visual review without automatically choosing a winner.",
)

p = Path("AI_CHANGELOG.md")
text = p.read_text()
entry = r'''
### ChatGPT — 2026-09-14 — whole-rep corrective candidate sweep

Added an on-demand deformation-control sweep on top of the export-aware elbow tuning. The Correctives workspace can now evaluate 0/25/50/75/100% outer-elbow smoothing through the existing production whole-rep strain path and reports the worst P99 and maximum-edge strain frame for every candidate value. Each result can be loaded directly at its worst P99 frame for close visual inspection.

The sweep is deliberately diagnostic rather than an optimiser: it never chooses or permanently changes a corrective value. A `finally` restoration returns both the source-level control and the mounted character to the pre-scan playhead pose even if a scan fails. Raw-skinning mode disables the sweep because candidate-strength comparisons would otherwise all be suppressed. The default per-mesh edge budget is lower than a single full review to keep the five-point comparison interactive while preserving identical samples across candidates.

Regression coverage uses a low-FPS/low-edge-budget character scan, proves the requested values are all visited, confirms finite worst-frame results, and verifies the exact pre-scan source value is restored afterwards.

'''
marker = "## Unreleased\n\n"
if marker not in text:
    raise SystemExit("missing changelog marker")
text = text.replace(marker, marker + entry, 1)
p.write_text(text)

print("Applied whole-rep corrective candidate sweep")
