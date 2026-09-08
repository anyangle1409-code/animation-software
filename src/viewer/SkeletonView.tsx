import { useMemo } from 'react';
import type { ThreeEvent } from '@react-three/fiber';
import type { BoneName } from '../rig/boneNames';
import { isFingerBone } from '../rig/boneNames';
import { skeleton, useStudio } from '../editor/store';
import { BoneGroups } from './BoneGroups';

const BONE_COLOUR = '#8fa3bf';
const SELECTED_COLOUR = '#ffb43a';
const JOINT_COLOUR = '#cfe0ff';

export interface SkeletonViewProps {
  /** Dim the skeleton when it sits behind the muscle or character layer. */
  ghosted?: boolean;
  includeFingers?: boolean;
}

/**
 * The skeleton itself: a tapered shaft per bone and a sphere at every joint.
 * Joints are the click targets, which is what makes individual bones
 * selectable and rotatable rather than the whole figure.
 */
export function SkeletonView({ ghosted = false, includeFingers = false }: SkeletonViewProps) {
  const selected = useStudio((state) => state.selection.bone);
  const selectBone = useStudio((state) => state.selectBone);
  const showJoints = useStudio((state) => state.showJoints);

  const bones = useMemo(
    () => skeleton.names.filter((name) => includeFingers || !isFingerBone(name)),
    [includeFingers],
  );

  const pick = (name: BoneName) => (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    selectBone(name);
  };

  return (
    <BoneGroups bones={bones}>
      {(name, length, radius) => {
        const isSelected = name === selected;
        const shaftRadius = Math.max(0.008, Math.min(0.022, radius * 0.28));
        const jointRadius = Math.max(0.012, Math.min(0.032, radius * 0.4));
        return (
          <>
            {length > 0.001 && (
              <mesh position={[0, length / 2, 0]} raycast={() => null}>
                <cylinderGeometry args={[shaftRadius * 0.6, shaftRadius, length, 6]} />
                <meshStandardMaterial
                  color={isSelected ? SELECTED_COLOUR : BONE_COLOUR}
                  transparent={ghosted}
                  opacity={ghosted ? 0.35 : 1}
                  roughness={0.55}
                  metalness={0.1}
                />
              </mesh>
            )}
            {showJoints && (
              <mesh onPointerDown={pick(name)}>
                <sphereGeometry args={[jointRadius, 12, 10]} />
                <meshStandardMaterial
                  color={isSelected ? SELECTED_COLOUR : JOINT_COLOUR}
                  emissive={isSelected ? SELECTED_COLOUR : '#000000'}
                  emissiveIntensity={isSelected ? 0.45 : 0}
                  transparent={ghosted}
                  opacity={ghosted ? 0.5 : 1}
                  roughness={0.4}
                />
              </mesh>
            )}
          </>
        );
      }}
    </BoneGroups>
  );
}
