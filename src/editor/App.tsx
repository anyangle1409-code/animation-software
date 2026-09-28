import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Viewport } from '../viewer/Viewport';
import { JointPanel } from './panels/JointPanel';
import { ExportPanel } from './panels/ExportPanel';
import { CharacterPanel } from './panels/CharacterPanel';
import { GripPanel } from './panels/GripPanel';
import { CorrectivePanel } from './panels/CorrectivePanel';
import { ReviewPanel } from './panels/ReviewPanel';
import { GeneratePanel } from './panels/GeneratePanel';
import type { StudioAppShellDom } from './appShellDom';
import { bindStudioKeyboard } from './keyboardController';
import { useStudioLayout } from './layoutState';

export interface AppProps {
  shell: StudioAppShellDom;
}

/**
 * Temporary React child-surface bridge.
 *
 * The outer editor DOM is project-owned by appShellDom. React remains only
 * for active panels and the viewport adapter while those surfaces are
 * migrated independently.
 */
export function App({ shell }: AppProps) {
  const leftTab = useStudioLayout((state) => state.leftTab);
  const rightTab = useStudioLayout((state) => state.rightTab);

  useEffect(() => bindStudioKeyboard(window), []);

  const leftPanel = (
    <>
      {leftTab === 'joint' && <JointPanel />}
      {leftTab === 'grip' && <GripPanel />}
      {leftTab === 'character' && <CharacterPanel />}
    </>
  );

  const rightPanel = (
    <>
      {rightTab === 'generate' && <GeneratePanel />}
      {rightTab === 'correctives' && <CorrectivePanel />}
      {rightTab === 'review' && <ReviewPanel />}
      {rightTab === 'export' && <ExportPanel />}
    </>
  );

  return (
    <>
      {createPortal(leftPanel, shell.slots.leftPanel)}
      {createPortal(<Viewport />, shell.slots.viewport)}
      {createPortal(rightPanel, shell.slots.rightPanel)}
    </>
  );
}
