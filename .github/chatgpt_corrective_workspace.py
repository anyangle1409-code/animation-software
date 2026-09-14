from pathlib import Path


def read(path): return Path(path).read_text()
def write(path, text): Path(path).write_text(text)
def replace_once(text, old, new, label):
    if old not in text: raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old, new, 1)

# Pure morph/corrective inspection utilities.
write('src/character/correctiveDiagnostics.ts', r'''import { Vector3 } from 'three';
import type { BufferAttribute, InterleavedBufferAttribute, SkinnedMesh } from 'three';

export interface CorrectiveDiagnostic {
  mesh: string;
  name: string;
  influence: number;
  affectedVertices: number;
  maxDisplacement: number;
  liveMaxDisplacement: number;
}

const isCorrective = (name: string): boolean => name.startsWith('homeGymPT_');

/** Inspect Studio-authored morph correctives without changing the character. */
export function correctiveDiagnostics(meshes: SkinnedMesh[]): CorrectiveDiagnostic[] {
  const out: CorrectiveDiagnostic[] = [];
  for (const mesh of meshes) {
    const dictionary = mesh.morphTargetDictionary ?? {};
    const influences = mesh.morphTargetInfluences ?? [];
    const base = mesh.geometry.getAttribute('position');
    const morphs = mesh.geometry.morphAttributes.position ?? [];
    if (!base) continue;
    for (const [name, index] of Object.entries(dictionary)) {
      if (!isCorrective(name)) continue;
      const morph = morphs[index];
      if (!morph) continue;
      const measurement = measureMorph(base, morph, mesh.geometry.morphTargetsRelative);
      const influence = influences[index] ?? 0;
      out.push({
        mesh: mesh.name || 'character',
        name,
        influence,
        affectedVertices: measurement.affectedVertices,
        maxDisplacement: measurement.maxDisplacement,
        liveMaxDisplacement: measurement.maxDisplacement * Math.abs(influence),
      });
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name));
}

/** Viewport-only bypass: exporter/samplers remain untouched. */
export function suppressCorrectives(meshes: SkinnedMesh[]): void {
  for (const mesh of meshes) {
    const dictionary = mesh.morphTargetDictionary ?? {};
    const influences = mesh.morphTargetInfluences;
    if (!influences) continue;
    for (const [name, index] of Object.entries(dictionary)) {
      if (isCorrective(name)) influences[index] = 0;
    }
  }
}

function measureMorph(
  base: BufferAttribute | InterleavedBufferAttribute,
  morph: BufferAttribute | InterleavedBufferAttribute,
  relative: boolean,
): { affectedVertices: number; maxDisplacement: number } {
  const delta = new Vector3();
  let affectedVertices = 0;
  let maxDisplacement = 0;
  const count = Math.min(base.count, morph.count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    delta.set(morph.getX(vertex), morph.getY(vertex), morph.getZ(vertex));
    if (!relative) {
      delta.x -= base.getX(vertex);
      delta.y -= base.getY(vertex);
      delta.z -= base.getZ(vertex);
    }
    const distance = delta.length();
    if (distance > 1e-7) affectedVertices += 1;
    if (distance > maxDisplacement) maxDisplacement = distance;
  }
  return { affectedVertices, maxDisplacement };
}
''')

write('src/character/correctiveDiagnostics.test.ts', r'''import { BufferAttribute, BufferGeometry, SkinnedMesh } from 'three';
import { describe, expect, it } from 'vitest';
import { correctiveDiagnostics, suppressCorrectives } from './correctiveDiagnostics';

function mesh(relative = true): SkinnedMesh {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(new Float32Array([0, 0, 0, 1, 0, 0]), 3));
  geometry.morphTargetsRelative = relative;
  const values = relative
    ? new Float32Array([0.008, 0, 0, 0, 0, 0])
    : new Float32Array([0.008, 0, 0, 1, 0, 0]);
  const corrective = new BufferAttribute(values, 3);
  corrective.name = 'homeGymPT_elbow_l';
  const face = new BufferAttribute(new Float32Array([0, 0, 0, 0, 0, 0]), 3);
  face.name = 'smile';
  geometry.morphAttributes.position = [corrective, face];
  const skinned = new SkinnedMesh(geometry);
  skinned.name = 'Body';
  skinned.morphTargetDictionary = { homeGymPT_elbow_l: 0, smile: 1 };
  skinned.morphTargetInfluences = [0.5, 0.75];
  return skinned;
}

describe('corrective diagnostics', () => {
  it('measures relative corrective displacement and live influence', () => {
    const diagnostic = correctiveDiagnostics([mesh(true)])[0];
    expect(diagnostic.name).toBe('homeGymPT_elbow_l');
    expect(diagnostic.affectedVertices).toBe(1);
    expect(diagnostic.maxDisplacement).toBeCloseTo(0.008, 6);
    expect(diagnostic.liveMaxDisplacement).toBeCloseTo(0.004, 6);
  });

  it('preserves absolute morph convention when measuring', () => {
    expect(correctiveDiagnostics([mesh(false)])[0].maxDisplacement).toBeCloseTo(0.008, 6);
  });

  it('bypasses only Studio correctives and leaves unrelated morphs alone', () => {
    const target = mesh(true);
    suppressCorrectives([target]);
    expect(target.morphTargetInfluences).toEqual([0, 0.75]);
  });
});
''')

# Viewport-only preview flag in character store.
p='src/editor/characterStore.ts'
s=read(p)
s=replace_once(s, "  active: CharacterBuild | null;\n\n  name", "  active: CharacterBuild | null;\n  /** Viewport-only A/B switch; export remains production-correct. */\n  correctivesPreview: boolean;\n\n  name", 'corrective preview state')
s=replace_once(s, "  setActive: (build: CharacterBuild | null) => void;\n  setBindMode", "  setActive: (build: CharacterBuild | null) => void;\n  setCorrectivesPreview: (enabled: boolean) => void;\n  setBindMode", 'corrective preview setter type')
s=replace_once(s, "  active: null,\n\n  name", "  active: null,\n  correctivesPreview: true,\n\n  name", 'corrective preview initial')
s=replace_once(s, "  setActive: (active) => set({ active }),\n\n  setBindMode", "  setActive: (active) => set({ active }),\n  setCorrectivesPreview: (correctivesPreview) => set({ correctivesPreview }),\n\n  setBindMode", 'corrective preview setter')
write(p,s)

# Apply normal deformation first, then optionally suppress only Studio correctives in viewport.
p='src/viewer/CharacterFigure.tsx'
s=read(p)
s=replace_once(s, "import type { CharacterBuild, CharacterVariant } from '../character';", "import type { CharacterBuild, CharacterVariant } from '../character';\nimport { suppressCorrectives } from '../character/correctiveDiagnostics';", 'character figure suppress import')
s=replace_once(s, "  const build = useCharacterBuild(sourceId, variant);", "  const build = useCharacterBuild(sourceId, variant);\n  const correctivesPreview = useCharacter((state) => state.correctivesPreview);", 'character figure preview flag')
s=replace_once(s, "    applyCharacterPose(build, skeleton, pose, scene.evaluation, { contacts: scene.frame?.contacts });", "    applyCharacterPose(build, skeleton, pose, scene.evaluation, { contacts: scene.frame?.contacts });\n    if (!correctivesPreview) suppressCorrectives(build.meshes);", 'suppress after deformation')
write(p,s)

# Correctives panel.
write('src/editor/panels/CorrectivePanel.tsx', r'''import { correctiveDiagnostics } from '../../character/correctiveDiagnostics';
import { useCharacter } from '../characterStore';
import { useStudio } from '../store';

const mm = (metres: number): string => `${(metres * 1000).toFixed(1)} mm`;

export function CorrectivePanel() {
  // Time subscription makes the panel refresh while playback mutates morph influences.
  useStudio((state) => state.time);
  const active = useCharacter((state) => state.active);
  const enabled = useCharacter((state) => state.correctivesPreview);
  const setEnabled = useCharacter((state) => state.setCorrectivesPreview);
  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];

  return (
    <section className="panel corrective-panel">
      <h2>Correctives</h2>
      <p className="panel__note">
        Mesh-specific joint correctives at the current playhead. The bypass below is viewport-only;
        it never changes the clip, source mesh or exported animation.
      </p>

      <div className="corrective-ab">
        <button type="button" className={enabled ? 'is-active' : ''} onClick={() => setEnabled(true)}>
          Correctives on
        </button>
        <button type="button" className={!enabled ? 'is-active' : ''} onClick={() => setEnabled(false)}>
          Raw skinning
        </button>
      </div>

      {!active && <p className="panel__empty">No active character is mounted.</p>}
      {active && diagnostics.length === 0 && (
        <p className="panel__empty">This character exposes no Home Gym PT corrective morphs.</p>
      )}

      <div className="corrective-list">
        {diagnostics.map((item) => (
          <article key={`${item.mesh}-${item.name}`} className="corrective-card">
            <div className="corrective-card__head">
              <strong>{item.name.replace('homeGymPT_', '').replaceAll('_', ' ')}</strong>
              <span>{Math.round(item.influence * 100)}%</span>
            </div>
            <div className="corrective-metrics">
              <span>Live displacement <strong>{mm(item.liveMaxDisplacement)}</strong></span>
              <span>Authored maximum <strong>{mm(item.maxDisplacement)}</strong></span>
              <span>Affected vertices <strong>{item.affectedVertices}</strong></span>
              <span>Mesh <strong>{item.mesh}</strong></span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
''')

# Add panel to right-side diagnostics tabs.
p='src/editor/App.tsx'
s=read(p)
s=replace_once(s, "import { EquipmentPanel } from './panels/EquipmentPanel';", "import { EquipmentPanel } from './panels/EquipmentPanel';\nimport { CorrectivePanel } from './panels/CorrectivePanel';", 'corrective panel import')
s=s.replace("type RightTab = 'exercise' | 'muscles' | 'technique' | 'compare' | 'export';", "type RightTab = 'exercise' | 'muscles' | 'technique' | 'correctives' | 'compare' | 'export';")
marker='''            <button
              type="button"
              className={rightTab === 'compare' ? 'is-active' : ''}
              onClick={() => setRightTab('compare')}
            >
              Compare
            </button>'''
addition='''            <button
              type="button"
              className={rightTab === 'correctives' ? 'is-active' : ''}
              onClick={() => setRightTab('correctives')}
            >
              Correctives
            </button>
'''+marker
s=replace_once(s, marker, addition, 'corrective tab button')
s=replace_once(s, "            {rightTab === 'compare' && <ComparisonPanel />}", "            {rightTab === 'correctives' && <CorrectivePanel />}\n            {rightTab === 'compare' && <ComparisonPanel />}", 'corrective panel body')
write(p,s)

p='src/editor/styles.css'
s=read(p)
s += r'''

.corrective-ab {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin: 8px 0 12px;
}

.corrective-list {
  display: grid;
  gap: 7px;
}

.corrective-card {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 8px;
}

.corrective-card__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.corrective-card__head span {
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}

.corrective-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px 8px;
  font-size: 10px;
  color: var(--muted);
}

.corrective-metrics strong {
  display: block;
  margin-top: 2px;
  color: var(--text);
}
'''
write(p,s)

# Roadmap + handoff.
p='docs/STUDIO_CAPABILITY_ROADMAP.md'
s=read(p)
needle='''## 6. Corrective deformation workspace

- Joint-angle-driven corrective shapes for elbow, shoulder, hip, knee and wrist when skinning alone is insufficient.
- Safe displacement caps and zero-at-neutral guarantees.
- Before/after A/B view plus mesh-strain diagnostics.
- No destructive rebinding of imported characters.'''
replacement=needle+'''\n\n### Implemented corrective inspection foundation\n\n- Dedicated Correctives workspace discovers mesh-specific `homeGymPT_*` morph correctives on the active character.\n- Live driver influence, affected-vertex count, authored maximum displacement and current maximum displacement are shown at the playhead.\n- `Correctives on` / `Raw skinning` is a viewport-only A/B bypass; the accepted clip, source mesh, deformation sampler and export remain untouched.\n- Relative and absolute source morph conventions are measured correctly, and unrelated expression/body morphs are never suppressed by the A/B control.'''
s=replace_once(s, needle, replacement, 'roadmap corrective inspection')
write(p,s)

p='AI_CHANGELOG.md'
s=read(p)
entry='''### ChatGPT — 2026-09-14 — corrective-deformation inspection workspace\n\nAdded a dedicated Correctives workspace for judging mesh-specific joint deformation without modifying the accepted animation. `src/character/correctiveDiagnostics.ts` discovers Studio-authored `homeGymPT_*` morphs on the active character and reports their live morph influence, affected vertex count, authored maximum displacement and current influence-scaled maximum displacement. Measurement respects the geometry's existing relative/absolute morph convention.\n\nAdded a viewport-only **Correctives on / Raw skinning** A/B switch. Normal `applyCharacterPose` and the character's deformation stack still run first; when Raw skinning is selected the viewport then zeros only `homeGymPT_*` influences. The Studio document, source geometry, deformation sampler and export path are not changed, and unrelated morphs such as facial expressions remain untouched. This provides a safe way to judge whether elbow/shoulder correctives genuinely improve the moving silhouette before promoting or tuning them. Regression coverage checks relative and absolute displacement measurement plus selective suppression.\n\n'''
s=replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n'+entry, 'changelog corrective entry')
write(p,s)

print('Applied corrective deformation inspection workspace')
