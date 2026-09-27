import { useEffect, useMemo } from 'react';
import {
  BufferGeometry,
  Float32BufferAttribute,
  LineBasicMaterial,
  LineSegments,
} from 'three';
import { buildHgReferenceGridBuffers } from './referenceGrid';

interface ReferenceGridViewProps {
  cellColor: string;
  sectionColor: string;
}

function lineSegments(positions: Float32Array, color: string, opacity: number) {
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

/** Existing-renderer adapter for the project-owned finite reference grid. */
export function ReferenceGridView({ cellColor, sectionColor }: ReferenceGridViewProps) {
  const resources = useMemo(() => {
    const buffers = buildHgReferenceGridBuffers();
    return {
      minor: lineSegments(buffers.minor, cellColor, 0.55),
      major: lineSegments(buffers.major, sectionColor, 0.9),
    };
  }, [cellColor, sectionColor]);

  useEffect(() => () => {
    resources.minor.geometry.dispose();
    resources.minor.material.dispose();
    resources.major.geometry.dispose();
    resources.major.material.dispose();
  }, [resources]);

  return (
    <group name="hgpt-reference-grid">
      <primitive object={resources.minor} />
      <primitive object={resources.major} />
    </group>
  );
}
