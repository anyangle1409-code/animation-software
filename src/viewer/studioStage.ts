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
import { buildHgReferenceGridBuffers } from './referenceGrid';

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

function createReferenceGrid(cellColor: string, sectionColor: string): Group {
  const buffers = buildHgReferenceGridBuffers();
  const grid = new Group();
  grid.name = 'hgpt-reference-grid';
  grid.add(
    gridLineSegments(buffers.minor, cellColor, 0.55),
    gridLineSegments(buffers.major, sectionColor, 0.9),
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
  const root = new Group();
  root.name = 'hgpt-studio-stage';

  const hemisphere = new HemisphereLight('#f0f4fb', backdrop.ground, backdrop.lighting.ambient);
  hemisphere.name = 'hgpt-stage-ambient';

  const key = new DirectionalLight('#ffffff', backdrop.lighting.key);
  key.name = 'hgpt-stage-key';
  key.position.set(3, 5, 4);
  key.castShadow = !backdrop.floorless;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.left = -3;
  key.shadow.camera.right = 3;
  key.shadow.camera.top = 3;
  key.shadow.camera.bottom = -3;

  const rim = new DirectionalLight(backdrop.lighting.rimColour, backdrop.lighting.rim);
  rim.name = 'hgpt-stage-rim';
  rim.position.set(-3, 2.5, -2);

  root.add(hemisphere, key, rim);

  let grid: Group | null = null;
  let floor: Mesh<PlaneGeometry, MeshStandardMaterial> | null = null;

  if (!backdrop.floorless) {
    if (showGrid) {
      grid = createReferenceGrid(backdrop.cell, backdrop.section);
      root.add(grid);
    }

    floor = new Mesh(
      new PlaneGeometry(24, 24),
      new MeshStandardMaterial({ color: backdrop.ground, roughness: 0.95 }),
    );
    floor.name = 'hgpt-stage-floor';
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    root.add(floor);
  }

  let disposed = false;
  return {
    root,
    background: new Color(backdrop.background),
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
