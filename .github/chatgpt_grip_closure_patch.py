from pathlib import Path

# 1) Store action: edit the exercise definition and regenerate through the same
# deterministic pipeline used by tempo edits. The existing default is untouched.
path = Path('src/editor/store.ts')
text = path.read_text(encoding='utf-8')
old = "  setTempo: (tempo: Partial<Tempo>) => void;\n  setLockEnabled: (lockId: string, enabled: boolean) => void;"
new = "  setTempo: (tempo: Partial<Tempo>) => void;\n  setGripClosure: (closure: number) => void;\n  setLockEnabled: (lockId: string, enabled: boolean) => void;"
if old not in text:
    raise SystemExit('store interface anchor not found')
text = text.replace(old, new, 1)
old = "    setTempo: (tempo) =>\n      commit((document) => {\n        const exercise = { ...document.exercise, tempo: { ...document.exercise.tempo, ...tempo } };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      }),\n\n    setLockEnabled:"
new = "    setTempo: (tempo) =>\n      commit((document) => {\n        const exercise = { ...document.exercise, tempo: { ...document.exercise.tempo, ...tempo } };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      }),\n\n    setGripClosure: (closure) =>\n      commit((document) => {\n        const normalized = Math.max(0, Math.min(1, closure));\n        const exercise = {\n          ...document.exercise,\n          hands: { ...document.exercise.hands, closure: normalized },\n        };\n        return { exercise, clip: generateClip(skeleton, exercise) };\n      }),\n\n    setLockEnabled:"
if old not in text:
    raise SystemExit('store implementation anchor not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 2) Exercise panel: live bounded slider + exact percentage readout.
path = Path('src/editor/panels/ExercisePanel.tsx')
text = path.read_text(encoding='utf-8')
old = "  const setTempo = useStudio((state) => state.setTempo);"
new = "  const setTempo = useStudio((state) => state.setTempo);\n  const setGripClosure = useStudio((state) => state.setGripClosure);"
if old not in text:
    raise SystemExit('panel action anchor not found')
text = text.replace(old, new, 1)
old = "        <dt>Hand width</dt>\n        <dd>{exercise.hands.width ? `${(exercise.hands.width * 100).toFixed(0)} cm` : '—'}</dd>"
new = "        <dt>Grip closure</dt>\n        <dd>\n          <label className=\"grip-closure\">\n            <input\n              type=\"range\"\n              min={0}\n              max={1}\n              step={0.05}\n              value={exercise.hands.closure}\n              aria-label=\"Grip closure\"\n              onChange={(event) => setGripClosure(Number(event.target.value))}\n            />\n            <span>{Math.round(exercise.hands.closure * 100)}%</span>\n          </label>\n        </dd>\n        <dt>Hand width</dt>\n        <dd>{exercise.hands.width ? `${(exercise.hands.width * 100).toFixed(0)} cm` : '—'}</dd>"
if old not in text:
    raise SystemExit('panel grip anchor not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# 3) Tiny layout rule; existing range styling supplies the visual treatment.
path = Path('src/editor/styles.css')
text = path.read_text(encoding='utf-8')
anchor = "/* ---------- panels ---------- */"
rule = ".grip-closure {\n  display: grid;\n  grid-template-columns: minmax(90px, 1fr) 38px;\n  align-items: center;\n  gap: 8px;\n}\n\n.grip-closure span {\n  color: var(--muted);\n  font-variant-numeric: tabular-nums;\n  text-align: right;\n}\n\n"
if anchor not in text:
    raise SystemExit('styles anchor not found')
if '.grip-closure {' not in text:
    text = text.replace(anchor, rule + anchor, 1)
path.write_text(text, encoding='utf-8')

# 4) Regression coverage for regeneration, clamp and undo.
Path('src/editor/store.test.ts').write_text("""import { beforeEach, describe, expect, it } from 'vitest';
import { useStudio } from './store';

const radians = (degrees: number) => (degrees * Math.PI) / 180;

describe('live grip closure tuning', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('regenerates the deterministic grip while leaving the authored default available to undo', () => {
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0.85);

    useStudio.getState().setGripClosure(0.5);
    const tuned = useStudio.getState().document;
    expect(tuned.exercise.hands.closure).toBe(0.5);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_l?.z).toBeCloseTo(radians(78 * 0.5), 8);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_r?.z).toBeCloseTo(-radians(78 * 0.5), 8);

    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0.85);
  });

  it('clamps editor input to the grip generator range', () => {
    useStudio.getState().setGripClosure(2);
    expect(useStudio.getState().document.exercise.hands.closure).toBe(1);
    useStudio.getState().setGripClosure(-1);
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0);
  });
});
""", encoding='utf-8')
