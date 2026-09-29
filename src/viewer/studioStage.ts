import {
  BufferGeometry,
  Color,
  DirectionalLight,
  Float32BufferAttribute,
  Group,
  HemisphereLight,
  LineBasicMaterial,
  LineSegments,
  Mesh,
  MeshStandardMaterial,
  PlaneGeometry,
} from './threeSceneBoundary';
import type { BackdropStyle } from '../editor/storeCore';
import { buildHgStageModel } from './studioStageModel';

export interface StudioStageResources {
  root: Group;
  background: Color;
  hemisphere: HemisphereLight;
  key: DirectionalLight;
  rim: DirectionalLight;
  floor: Mesh<PlaneGeometry, MeshStandardMaterial> | null;
  grid: Group | null;
  dispose(): void;
}

function gridLineSegments(positions: Float32Array, color: string, opacity: number): LineSegments {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.computeBoundingSphere();
  const material = new LineBasicMaterial({
    color,
    transparent: true,
    opacity,
    depthWrite: false,
    toneMapped: false,
  });
  const segments = new LineSegments(geometry, material);
  segments.frustumCulled = false;
  segments.renderOrder = 1;
  return segments;
}

function createReferenceGrid(
  buffers: { minor: Float32Array; major: Float32Array },
  cellColor: string,
  sectionColor: string,
  cellOpacity: number,
  sectionOpacity: number,
): Group {
  const grid = new Group();
  grid.name = 'hgpt-reference-grid';
  grid.add(
    gridLineSegments(buffers.minor, cellColor, cellOpacity),
    gridLineSegments(buffers.major, sectionColor, sectionOpacity),
  );
  return grid;
}

function disposeGrid(grid: Group | null): void {
  if (!grid) return;
  for (const child of grid.children) {
    if (!(child instanceof LineSegments)) continue;
    child.geometry.dispose();
    if (Array.isArray(child.material)) child.material.forEach((material) => material.dispose());
    else child.material.dispose();
  }
}

/**
 * Build the static Studio scene independently of React/R3F.
 *
 * Dynamic figures/equipment remain separate consumers. This owns only the
 * backdrop, lighting, floor and finite reference grid that currently belong to
 * the viewport host.
 */
export function createStudioStage(backdrop: BackdropStyle, showGrid: boolean): StudioStageResources {
  const model = buildHgStageModel(backdrop, showGrid);
  const root = new Group();
  root.name = 'hgpt-studio-stage';

  const hemisphere = new HemisphereLight(
    model.hemisphere.sky,
    model.hemisphere.ground,
    model.hemisphere.intensity,
  );
  hemisphere.name = 'hgpt-stage-ambient';

  const key = new DirectionalLight(model.key.colour, model.key.intensity);
  key.name = 'hgpt-stage-key';
  key.position.set(...model.key.position);
  key.castShadow = model.key.castShadow;
  key.shadow.mapSize.set(...model.key.shadowMapSize);
  key.shadow.camera.left = model.key.shadowBounds.left;
  key.shadow.camera.right = model.key.shadowBounds.right;
  key.shadow.camera.top = model.key.shadowBounds.top;
  key.shadow.camera.bottom = model.key.shadowBounds.bottom;

  const rim = new DirectionalLight(model.rim.colour, model.rim.intensity);
  rim.name = 'hgpt-stage-rim';
  rim.position.set(...model.rim.position);

  root.add(hemisphere, key, rim);

  let grid: Group | null = null;
  let floor: Mesh<PlaneGeometry, MeshStandardMaterial> | null = null;

  if (model.grid) {
    grid = createReferenceGrid(
      model.grid.buffers,
      model.grid.cellColour,
      model.grid.sectionColour,
      model.grid.cellOpacity,
      model.grid.sectionOpacity,
    );
    root.add(grid);
  }

  if (model.floor) {
    floor = new Mesh(
      new PlaneGeometry(...model.floor.size),
      new MeshStandardMaterial({
        color: model.floor.colour,
        roughness: model.floor.roughness,
      }),
    );
    floor.name = 'hgpt-stage-floor';
    floor.rotation.x = model.floor.rotationX;
    floor.receiveShadow = model.floor.receiveShadow;
    root.add(floor);
  }

  let disposed = false;
  return {
    root,
    background: new Color(model.background),
    hemisphere,
    key,
    rim,
    floor,
    grid,
    dispose() {
      if (disposed) return;
      disposed = true;
      disposeGrid(grid);
      floor?.geometry.dispose();
      if (floor) {
        if (Array.isArray(floor.material)) floor.material.forEach((material) => material.dispose());
        else floor.material.dispose();
      }
      root.clear();
    },
  };
}
