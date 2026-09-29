interface AttributeLike {
  readonly count: number;
  getX(index: number): number;
  getY(index: number): number;
  getZ(index: number): number;
}

interface CorrectiveGeometryLike {
  getAttribute(name: string): AttributeLike | undefined;
  readonly morphAttributes: { readonly position?: AttributeLike[] };
  readonly morphTargetsRelative: boolean;
}

interface CorrectiveMeshLike {
  readonly name: string;
  readonly geometry: CorrectiveGeometryLike;
  readonly morphTargetDictionary?: Record<string, number>;
  readonly morphTargetInfluences?: number[];
}

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
export function correctiveDiagnostics(meshes: CorrectiveMeshLike[]): CorrectiveDiagnostic[] {
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
export function suppressCorrectives(meshes: CorrectiveMeshLike[]): void {
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
  base: AttributeLike,
  morph: AttributeLike,
  relative: boolean,
): { affectedVertices: number; maxDisplacement: number } {
  let affectedVertices = 0;
  let maxDisplacement = 0;
  const count = Math.min(base.count, morph.count);
  for (let vertex = 0; vertex < count; vertex += 1) {
    const dx = morph.getX(vertex) - (relative ? 0 : base.getX(vertex));
    const dy = morph.getY(vertex) - (relative ? 0 : base.getY(vertex));
    const dz = morph.getZ(vertex) - (relative ? 0 : base.getZ(vertex));
    const distance = Math.hypot(dx, dy, dz);
    if (distance > 1e-7) affectedVertices += 1;
    if (distance > maxDisplacement) maxDisplacement = distance;
  }
  return { affectedVertices, maxDisplacement };
}
