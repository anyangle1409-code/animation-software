import { HgVec3 } from '../core/linearMath';
import type { PosedCharacterMeshLike } from './posedMesh';
import { posedLocalVertexPoint } from './posedMesh';

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
  meshes: readonly PosedCharacterMeshLike[],
  maxEdgesPerMesh = 4000,
): MeshStrainDiagnostic[] {
  return meshes.flatMap((mesh) => {
    const diagnostic = measureMesh(mesh, maxEdgesPerMesh);
    return diagnostic ? [diagnostic] : [];
  });
}

function measureMesh(mesh: PosedCharacterMeshLike, maxEdges: number): MeshStrainDiagnostic | null {
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
  const posedA = new HgVec3();
  const posedB = new HgVec3();
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
      const rest = Math.hypot(
        position.getX(a) - position.getX(b),
        position.getY(a) - position.getY(b),
        position.getZ(a) - position.getZ(b),
      );
      if (rest < 1e-7) continue;
      posedLocalVertexPoint(mesh, a, posedA);
      posedLocalVertexPoint(mesh, b, posedB);
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

function vertexIndex(index: { getX(corner: number): number } | null, corner: number): number {
  return index ? index.getX(corner) : corner;
}

function percentile(sorted: number[], value: number): number {
  const index = Math.min(sorted.length - 1, Math.max(0, Math.ceil(sorted.length * value) - 1));
  return sorted[index];
}
