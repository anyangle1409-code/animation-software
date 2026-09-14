import { Vector3 } from 'three';
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
