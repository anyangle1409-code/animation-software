import type { HgPrimitiveGeometryData } from '../core/primitiveGeometry';
import { boxPrimitiveData } from '../core/primitiveGeometry';
import { HgGroup } from '../core/sceneGraph';
import { HgPrimitiveMaterial, HgPrimitiveMesh } from '../core/sceneMesh';
import type { BackdropStyle } from '../editor/storeCore';
import { buildHgStageModel } from './studioStageModel';

export interface HgStudioStageResources {
  readonly root: HgGroup;
  readonly background: string;
  readonly floor: HgPrimitiveMesh | null;
  readonly grid: HgGroup | null;
  dispose(): void;
}

const lineRibbonGeometry = (
  packed: Float32Array,
  width: number,
): HgPrimitiveGeometryData => {
  const geometry: HgPrimitiveGeometryData = {
    positions: [],
    normals: [],
    uvs: [],
    indices: [],
  };
  for (let offset = 0; offset + 5 < packed.length; offset += 6) {
    const ax = packed[offset];
    const ay = packed[offset + 1];
    const az = packed[offset + 2];
    const bx = packed[offset + 3];
    const by = packed[offset + 4];
    const bz = packed[offset + 5];
    const dx = bx - ax;
    const dz = bz - az;
    const length = Math.hypot(dx, dz);
    if (length < 1e-12) continue;
    const nx = -dz / length * width * 0.5;
    const nz = dx / length * width * 0.5;
    const start = geometry.positions.length / 3;
    geometry.positions.push(
      ax + nx, ay, az + nz,
      ax - nx, ay, az - nz,
      bx - nx, by, bz - nz,
      bx + nx, by, bz + nz,
    );
    geometry.normals.push(
      0, 1, 0,
      0, 1, 0,
      0, 1, 0,
      0, 1, 0,
    );
    geometry.uvs.push(0, 0, 0, 1, 1, 1, 1, 0);
    geometry.indices.push(
      start, start + 1, start + 2,
      start, start + 2, start + 3,
    );
  }
  return geometry;
};

const gridMesh = (
  packed: Float32Array,
  colour: string,
  opacity: number,
  width: number,
  name: string,
): HgPrimitiveMesh => {
  const mesh = new HgPrimitiveMesh(
    lineRibbonGeometry(packed, width),
    new HgPrimitiveMaterial(colour, 'flat', {
      depthWrite: false,
    }).setOpacity(opacity),
  );
  mesh.name = name;
  return mesh;
};

/** First-party static Studio stage matching the authoritative stage model. */
export function createHgStudioStage(
  backdrop: BackdropStyle,
  showGrid: boolean,
): HgStudioStageResources {
  const model = buildHgStageModel(backdrop, showGrid);
  const root = new HgGroup();
  root.name = 'hgpt-studio-stage';

  let floor: HgPrimitiveMesh | null = null;
  if (model.floor) {
    floor = new HgPrimitiveMesh(
      boxPrimitiveData([model.floor.size[0], 0.002, model.floor.size[1]]),
      new HgPrimitiveMaterial(model.floor.colour, 'lit', {
        roughness: model.floor.roughness,
      }),
    );
    floor.name = 'hgpt-stage-floor';
    floor.position.y = -0.001;
    root.add(floor);
  }

  let grid: HgGroup | null = null;
  if (model.grid) {
    grid = new HgGroup();
    grid.name = 'hgpt-reference-grid';
    grid.add(
      gridMesh(
        model.grid.buffers.minor,
        model.grid.cellColour,
        model.grid.cellOpacity,
        0.003,
        'hgpt-reference-grid-minor',
      ),
      gridMesh(
        model.grid.buffers.major,
        model.grid.sectionColour,
        model.grid.sectionOpacity,
        0.006,
        'hgpt-reference-grid-major',
      ),
    );
    root.add(grid);
  }

  let disposed = false;
  return {
    root,
    background: model.background,
    floor,
    grid,
    dispose() {
      if (disposed) return;
      disposed = true;
      root.clear();
      grid?.clear();
    },
  };
}
