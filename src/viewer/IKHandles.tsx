import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import { Mesh, Vector3 } from 'three';
import { IK_CHAINS, IK_CHAIN_IDS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import { useStudio } from '../editor/store';
import { useSceneState } from './sceneState';
import { sampleClip } from '../animation/clip';

const TARGET_COLOUR = '#4fd6a0';
const POLE_COLOUR = '#6aa9ff';
const SELECTED_COLOUR = '#ffb43a';

/**
 * Draggable handles for each limb: a target the effector reaches for, and a
 * pole that decides which way the elbow or knee points.
 */
export function IKHandles() {
  const scene = useSceneState();
  const time = useStudio((state) => state.time);
  const clip = useStudio((state) => state.document.clip);
  const selection = useStudio((state) => state.selection.handle);
  const selectHandle = useStudio((state) => state.selectHandle);
  const handles = useRef(new Map<string, Mesh>());

  useFrame(() => {
    const sample = sampleClip(clip, time);
    for (const chain of IK_CHAIN_IDS) {
      const goal = sample.ik[chain];
      const target = handles.current.get(`${chain}:target`);
      const pole = handles.current.get(`${chain}:pole`);
      const active = Boolean(goal?.enabled);
      if (target) {
        target.visible = active;
        if (goal) target.position.set(goal.target.x, goal.target.y, goal.target.z);
      }
      if (pole) {
        pole.visible = active;
        if (goal) pole.position.set(goal.pole.x, goal.pole.y, goal.pole.z);
      }
      if (!active && target) {
        // Park an inactive target on the effector so switching IK on is seamless.
        const effector = scene.evaluation.head(IK_CHAINS[chain].end, new Vector3());
        target.position.copy(effector);
      }
    }
  });

  const handle = (chain: IKChainId, kind: 'target' | 'pole') => {
    const key = `${chain}:${kind}`;
    const isSelected = selection?.chain === chain && selection.kind === kind;
    return (
      <mesh
        key={key}
        visible={false}
        ref={(mesh) => {
          if (mesh) handles.current.set(key, mesh);
          else handles.current.delete(key);
        }}
        onPointerDown={(event) => {
          event.stopPropagation();
          selectHandle({ chain, kind });
        }}
      >
        {kind === 'target' ? (
          <boxGeometry args={[0.045, 0.045, 0.045]} />
        ) : (
          <octahedronGeometry args={[0.032]} />
        )}
        <meshStandardMaterial
          color={isSelected ? SELECTED_COLOUR : kind === 'target' ? TARGET_COLOUR : POLE_COLOUR}
          emissive={isSelected ? SELECTED_COLOUR : '#000000'}
          emissiveIntensity={isSelected ? 0.5 : 0}
          transparent
          opacity={0.9}
          depthTest={false}
        />
      </mesh>
    );
  };

  return (
    <>
      {IK_CHAIN_IDS.flatMap((chain) => [handle(chain, 'target'), handle(chain, 'pole')])}
    </>
  );
}
