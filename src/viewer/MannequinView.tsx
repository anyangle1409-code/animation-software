import { useMemo } from 'react';
import type { BoneName } from '../rig/boneNames';
import { isFingerBone } from '../rig/boneNames';
import { skeleton } from '../editor/store';
import { BoneGroups } from './BoneGroups';

/** Bones drawn as a solid body segment, with how far the segment is padded. */
const SEGMENT_SCALE: Partial<Record<BoneName, number>> = {
  head: 0.62,
  neck: 0.9,
  pelvis: 1.35,
  spine_01: 1.1,
  spine_02: 1.1,
  spine_03: 1.05,
};

export interface MannequinViewProps {
  opacity?: number;
  colour?: string;
  /**
   * A ghosted body must not write depth, or it hides the muscles inside it —
   * which is the one thing the muscle view exists to show.
   */
  depthWrite?: boolean;
}

/**
 * A plain anatomical mannequin: one capsule per bone, sized from the rig's own
 * soft-tissue radii. Deliberately simple — the point of this stage is that the
 * movement is right, and a mannequin makes joint positions easy to read.
 */
export function MannequinView({
  opacity = 1,
  colour = '#c9d3e0',
  depthWrite = true,
}: MannequinViewProps) {
  const bones = useMemo(() => skeleton.names.filter((name) => name !== 'root'), []);

  return (
    <BoneGroups bones={bones}>
      {(name, length, radius) => {
        if (length < 0.004) return null;
        const isFinger = isFingerBone(name);
        const scale = SEGMENT_SCALE[name] ?? 1;
        const capsuleLength = Math.max(0.001, length * scale - radius * 0.6);
        return (
          <mesh position={[0, length / 2, 0]} castShadow receiveShadow raycast={() => null}>
            <capsuleGeometry args={[radius, capsuleLength, isFinger ? 2 : 4, isFinger ? 6 : 12]} />
            <meshStandardMaterial
              color={colour}
              transparent={opacity < 1}
              opacity={opacity}
              depthWrite={depthWrite}
              roughness={0.72}
              metalness={0.04}
            />
          </mesh>
        );
      }}
    </BoneGroups>
  );
}
