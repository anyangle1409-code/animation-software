import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import type { ReactNode } from 'react';
import { Group } from 'three';
import type { BoneName } from '../rig/boneNames';
import { skeleton } from '../editor/store';
import { useSceneState } from './sceneState';

export interface BoneGroupsProps {
  /** Bones to create groups for; defaults to every bone in the rig. */
  bones?: BoneName[];
  children: (bone: BoneName, length: number, radius: number) => ReactNode;
}

/**
 * One group per bone, its matrix driven straight from the pose evaluation.
 *
 * Children are authored in bone-local space — +Y runs along the bone from its
 * joint — so a capsule at `y = length / 2` fills the bone exactly, for any bone.
 */
export function BoneGroups({ bones, children }: BoneGroupsProps) {
  const scene = useSceneState();
  const names = useMemo(() => bones ?? skeleton.names, [bones]);
  const groups = useRef(new Map<BoneName, Group>());

  useFrame(() => {
    for (const [name, group] of groups.current) {
      group.matrix.copy(scene.evaluation.matrix(name));
      group.matrixWorldNeedsUpdate = true;
    }
  });

  return (
    <>
      {names.map((name) => {
        const bone = skeleton.bone(name);
        return (
          <group
            key={name}
            matrixAutoUpdate={false}
            ref={(group) => {
              if (group) groups.current.set(name, group);
              else groups.current.delete(name);
            }}
          >
            {children(name, bone.length, bone.definition.radius)}
          </group>
        );
      })}
    </>
  );
}
