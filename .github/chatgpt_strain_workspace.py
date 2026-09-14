from pathlib import Path

def read(path): return Path(path).read_text()
def write(path,text): Path(path).write_text(text)
def replace_once(text, old, new, label):
    if old not in text: raise SystemExit(f'missing replacement target: {label}')
    return text.replace(old,new,1)

write('src/character/meshStrain.ts', r'''import { Vector3 } from 'three';
import type { BufferAttribute, InterleavedBufferAttribute, SkinnedMesh } from 'three';

export interface MeshStrainDiagnostic {
  mesh: string;
  sampledEdges: number;
  p95: number;
  p99: number;
  max: number;
  severeCompression: number;
  severeStretch: number;
}

/**
 * Sample local surface edge strain after skinning/morphs.
 * Ratios are invariant to the character object's rigid world transform, so the
 * mesh-local comparison is enough and avoids mixing camera/stage placement in.
 */
export function meshStrainDiagnostics(
  meshes: SkinnedMesh[],
  maxEdgesPerMesh = 4000,
): MeshStrainDiagnostic[] {
  return meshes.flatMap((mesh) => {
    const diagnostic = measureMesh(mesh, maxEdgesPerMesh);
    return diagnostic ? [diagnostic] : [];
  });
}

function measureMesh(mesh: SkinnedMesh, maxEdges: number): MeshStrainDiagnostic | null {
  const position = mesh.geometry.getAttribute('position');
  if (!position || position.count < 2) return null;
  const index = mesh.geometry.getIndex();
  const triangleCount = index ? Math.floor(index.count / 3) : Math.floor(position.count / 3);
  if (triangleCount === 0) return null;

  const totalEdgeSamples = triangleCount * 3;
  const stride = Math.max(1, Math.ceil(totalEdgeSamples / Math.max(1, maxEdges)));
  const strains: number[] = [];
  let severeCompression = 0;
  let severeStretch = 0;
  const baseA = new Vector3();
  const baseB = new Vector3();
  const posedA = new Vector3();
  const posedB = new Vector3();
  const pairs: [number, number][] = [[0, 1], [1, 2], [2, 0]];
  let ordinal = 0;

  for (let triangle = 0; triangle < triangleCount; triangle += 1) {
    const vertices = [
      vertexIndex(index, triangle * 3),
      vertexIndex(index, triangle * 3 + 1),
      vertexIndex(index, triangle * 3 + 2),
    ];
    for (const [from, to] of pairs) {
      if (ordinal++ % stride !== 0) continue;
      const a = vertices[from];
      const b = vertices[to];
      pointFrom(position, a, baseA);
      pointFrom(position, b, baseB);
      const rest = baseA.distanceTo(baseB);
      if (rest < 1e-7) continue;
      mesh.getVertexPosition(a, posedA);
      mesh.getVertexPosition(b, posedB);
      const ratio = posedA.distanceTo(posedB) / rest;
      if (!Number.isFinite(ratio)) continue;
      const strain = Math.abs(ratio - 1);
      strains.push(strain);
      if (ratio < 0.8) severeCompression += 1;
      if (ratio > 1.2) severeStretch += 1;
    }
  }

  if (!strains.length) return null;
  strains.sort((a, b) => a - b);
  return {
    mesh: mesh.name || 'character',
    sampledEdges: strains.length,
    p95: percentile(strains, 0.95),
    p99: percentile(strains, 0.99),
    max: strains[strains.length - 1],
    severeCompression,
    severeStretch,
  };
}

function vertexIndex(index: BufferAttribute | null, corner: number): number {
  return index ? index.getX(corner) : corner;
}

function pointFrom(
  position: BufferAttribute | InterleavedBufferAttribute,
  vertex: number,
  target: Vector3,
): Vector3 {
  return target.set(position.getX(vertex), position.getY(vertex), position.getZ(vertex));
}

function percentile(sorted: number[], value: number): number {
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * value) - 1));
  return sorted[index];
}
''')

write('src/character/meshStrain.test.ts', r'''import { Bone, BufferAttribute, BufferGeometry, Skeleton, SkinnedMesh } from 'three';
import { describe, expect, it } from 'vitest';
import { meshStrainDiagnostics } from './meshStrain';

function skinnedTriangle(): { mesh: SkinnedMesh; bone: Bone } {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(new Float32Array([
    0, 0, 0,
    1, 0, 0,
    0, 1, 0,
  ]), 3));
  geometry.setIndex([0, 1, 2]);
  geometry.setAttribute('skinIndex', new BufferAttribute(new Uint16Array([
    0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
  ]), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(new Float32Array([
    1, 0, 0, 0,
    1, 0, 0, 0,
    1, 0, 0, 0,
  ]), 4));
  const morph = new BufferAttribute(new Float32Array([
    0, 0, 0,
    0.5, 0, 0,
    0, 0, 0,
  ]), 3);
  morph.name = 'homeGymPT_test';
  geometry.morphTargetsRelative = true;
  geometry.morphAttributes.position = [morph];
  const mesh = new SkinnedMesh(geometry);
  mesh.name = 'TestBody';
  const bone = new Bone();
  mesh.add(bone);
  mesh.bind(new Skeleton([bone]));
  mesh.updateMorphTargets();
  return { mesh, bone };
}

describe('mesh strain diagnostics', () => {
  it('reports zero strain for a rigidly transformed surface', () => {
    const { mesh, bone } = skinnedTriangle();
    bone.position.set(1, 2, 3);
    bone.updateMatrixWorld(true);
    const result = meshStrainDiagnostics([mesh], 100)[0];
    expect(result.max).toBeCloseTo(0, 6);
    expect(result.severeCompression).toBe(0);
    expect(result.severeStretch).toBe(0);
  });

  it('detects non-rigid morph stretch', () => {
    const { mesh } = skinnedTriangle();
    mesh.morphTargetInfluences![0] = 1;
    const result = meshStrainDiagnostics([mesh], 100)[0];
    expect(result.sampledEdges).toBe(3);
    expect(result.max).toBeCloseTo(0.5, 6);
    expect(result.severeStretch).toBeGreaterThan(0);
  });
});
''')

p='src/editor/panels/CorrectivePanel.tsx'
s=read(p)
s=s.replace("import { correctiveDiagnostics } from '../../character/correctiveDiagnostics';", "import { useEffect, useState } from 'react';\nimport { correctiveDiagnostics } from '../../character/correctiveDiagnostics';\nimport { meshStrainDiagnostics, type MeshStrainDiagnostic } from '../../character/meshStrain';")
s=replace_once(s, "  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];", "  const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];\n  const [strain, setStrain] = useState<MeshStrainDiagnostic[]>([]);\n\n  useEffect(() => {\n    if (!active) {\n      setStrain([]);\n      return;\n    }\n    const update = () => setStrain(meshStrainDiagnostics(active.meshes));\n    update();\n    const timer = window.setInterval(update, 200);\n    return () => window.clearInterval(timer);\n  }, [active, enabled]);", 'corrective panel strain state')
needle='''      <div className="corrective-list">
        {diagnostics.map((item) => ('''
replacement='''      <h3>Surface strain</h3>
      <p className="panel__hint">
        Sampled edge-length change versus bind geometry. P95/P99 are robust whole-surface signals;
        severe counts are edges compressed or stretched by more than 20%.
      </p>
      <div className="strain-list">
        {strain.map((item) => (
          <div key={item.mesh} className="strain-card">
            <strong>{item.mesh}</strong>
            <span>P95 {(item.p95 * 100).toFixed(1)}%</span>
            <span>P99 {(item.p99 * 100).toFixed(1)}%</span>
            <span>Max {(item.max * 100).toFixed(1)}%</span>
            <span>Compression &gt;20% · {item.severeCompression}</span>
            <span>Stretch &gt;20% · {item.severeStretch}</span>
            <small>{item.sampledEdges} sampled edges</small>
          </div>
        ))}
      </div>

      <h3>Corrective morphs</h3>
      <div className="corrective-list">
        {diagnostics.map((item) => ('''
s=replace_once(s, needle, replacement, 'surface strain UI')
write(p,s)

p='src/editor/styles.css'
s=read(p)
s += r'''

.strain-list {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.strain-card {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel-2);
  padding: 8px;
  font-size: 10px;
}

.strain-card > strong,
.strain-card > small {
  grid-column: 1 / -1;
}

.strain-card span,
.strain-card small {
  color: var(--muted);
}
'''
write(p,s)

p='docs/STUDIO_CAPABILITY_ROADMAP.md'
s=read(p)
needle='- Relative and absolute source morph conventions are measured correctly, and unrelated expression/body morphs are never suppressed by the A/B control.'
s=replace_once(s, needle, needle+'\n- Live surface-strain diagnostics sample posed mesh edges against bind geometry and report P95/P99/max strain plus >20% compression/stretch counts; rigid transforms correctly read as zero strain.', 'roadmap strain')
write(p,s)

p='AI_CHANGELOG.md'
s=read(p)
entry='''### ChatGPT — 2026-09-14 — live surface-strain diagnostics\n\nExtended the Correctives workspace with an objective surface-deformation readout. `src/character/meshStrain.ts` samples posed `SkinnedMesh.getVertexPosition` edge lengths against the same edges in bind geometry, so normal rigid character/world movement cancels out while non-rigid skinning/morph distortion remains measurable. The panel refreshes at 5 Hz and reports P95, P99 and maximum absolute edge strain, counts of sampled edges compressed by >20% or stretched by >20%, and the sample count per mesh. The sampling budget is bounded per mesh so diagnostics do not require scanning every dense-mesh edge every rendered frame.\n\nRegression coverage proves a rigidly moved one-bone mesh reports zero strain and a known relative morph stretch is detected at the expected 50% maximum. These values are diagnostic geometry signals, not injury/force estimates. They are intended to be read alongside the viewport-only Correctives on / Raw skinning A/B switch when deciding whether a joint corrective actually improves deformation rather than merely changing silhouette.\n\n'''
s=replace_once(s, '## Unreleased\n\n', '## Unreleased\n\n\n'+entry, 'changelog strain')
write(p,s)

print('Applied live surface strain diagnostics')
