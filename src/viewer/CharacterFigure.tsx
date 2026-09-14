import { useFrame } from '@react-three/fiber';
import { useEffect, useState } from 'react';
import { MeshStandardMaterial } from 'three';
import { skeleton, useStudio } from '../editor/store';
import { useCharacter } from '../editor/characterStore';
import { applyActivation } from '../body/ecorche';
import { applyCharacterPose, characterSource } from '../character';
import type { CharacterBuild, CharacterVariant } from '../character';
import { suppressCorrectives } from '../character/correctiveDiagnostics';
import { useSceneState } from './sceneState';

export interface CharacterFigureProps {
  opacity?: number;
  /** Multiplies the body's own vertex colours; white leaves them as authored. */
  colour?: string;
  /**
   * A ghosted body must not write depth, or it hides the muscles inside it —
   * which is the one thing the muscle view exists to show.
   */
  depthWrite?: boolean;
  variant?: CharacterVariant;
}

/**
 * The visible character: whichever source is active, bound to the canonical
 * bones and driven by the same pose everything else reads.
 *
 * The component knows nothing about which mesh it is showing. It asks the
 * registry for the active source, mounts what comes back and poses it — so
 * replacing the character is a registry change, not a viewport change.
 */
export function CharacterFigure({
  opacity = 1,
  colour = '#ffffff',
  depthWrite = true,
  variant = 'skin',
}: CharacterFigureProps) {
  const scene = useSceneState();
  const involvement = useStudio((state) => state.document.exercise.muscles);
  const sourceId = useCharacter((state) => state.sourceId);
  const build = useCharacterBuild(sourceId, variant);
  const correctivesPreview = useCharacter((state) => state.correctivesPreview);

  // Which muscles the exercise works is data, and it can change under the view,
  // so the scalar the shader reads is rebuilt rather than baked once.
  useEffect(() => {
    if (!build || variant !== 'ecorche' || !build.capabilities.anatomy) return;
    for (const mesh of build.meshes) applyActivation(mesh.geometry, involvement);
  }, [build, variant, involvement]);

  useEffect(() => {
    if (!build) return;
    for (const mesh of build.meshes) {
      const material = mesh.material as MeshStandardMaterial;
      if (!(material instanceof MeshStandardMaterial)) continue;
      material.color.set(colour);
      material.opacity = opacity;
      material.transparent = opacity < 1;
      material.depthWrite = depthWrite;
      material.needsUpdate = true;
    }
  }, [build, colour, opacity, depthWrite]);

  useFrame(() => {
    const pose = scene.frame?.pose;
    if (!pose || !build) return;
    applyCharacterPose(build, skeleton, pose, scene.evaluation, { contacts: scene.frame?.contacts });
    if (!correctivesPreview) suppressCorrectives(build.meshes);
  });

  if (!build) return null;
  return <primitive object={build.object} />;
}

/**
 * Build the active character, and rebuild it when the choice changes.
 *
 * Sources are asynchronous because the interesting ones load a file, so the
 * viewport renders nothing for the frame or two a build takes rather than
 * blocking. A build that finishes after the choice moved on is disposed.
 */
function useCharacterBuild(sourceId: string, variant: CharacterVariant): CharacterBuild | null {
  const [build, setBuild] = useState<CharacterBuild | null>(null);
  const setStatus = useCharacter((state) => state.setSourceStatus);
  const setActive = useCharacter((state) => state.setActive);

  useEffect(() => {
    let cancelled = false;
    const source = characterSource(sourceId);
    setBuild(null);
    setStatus({ kind: 'loading', message: `Building ${source.label}…` });

    source
      .build(skeleton, { variant })
      .then((next) => {
        if (cancelled) {
          next.dispose();
          return;
        }
        setBuild(next);
        // Published, so the systems that have to follow the character rather
        // than the rig — equipment, above all — can find it.
        setActive(next);
        setStatus({ kind: 'idle' });
      })
      .catch((error: Error) => {
        if (!cancelled) setStatus({ kind: 'error', message: error.message });
      });

    return () => {
      cancelled = true;
    };
  }, [sourceId, variant, setStatus, setActive]);

  useEffect(
    () => () => {
      if (!build) return;
      setActive(null);
      build.dispose();
    },
    [build, setActive],
  );

  return build;
}
