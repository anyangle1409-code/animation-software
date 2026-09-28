import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Viewport } from '../viewer/Viewport';
import { Toolbar } from './Toolbar';
import { Timeline } from './Timeline';
import { JointPanel } from './panels/JointPanel';
import { IKPanel } from './panels/IKPanel';
import { ExercisePanel } from './panels/ExercisePanel';
import { MusclePanel } from './panels/MusclePanel';
import { TechniquePanel } from './panels/TechniquePanel';
import { ExportPanel } from './panels/ExportPanel';
import { CharacterPanel } from './panels/CharacterPanel';
import { ComparisonPanel } from './panels/ComparisonPanel';
import { GripPanel } from './panels/GripPanel';
import { ContactPanel } from './panels/ContactPanel';
import { EquipmentPanel } from './panels/EquipmentPanel';
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
 * for the toolbar, active panels, viewport adapter and timeline while those
 * surfaces are migrated independently.
 */
export function App({ shell }: AppProps) {
  const leftTab = useStudioLayout((state) => state.leftTab);
  const rightTab = useStudioLayout((state) => state.rightTab);

  useEffect(() => bindStudioKeyboard(window), []);

  const leftPanel = (
    <>
      {leftTab === 'joint' && <JointPanel />}
      {leftTab === 'grip' && <GripPanel />}
      {leftTab === 'ik' && <IKPanel />}
      {leftTab === 'contacts' && <ContactPanel />}
      {leftTab === 'equipment' && <EquipmentPanel />}
      {leftTab === 'character' && <CharacterPanel />}
    </>
  );

  const rightPanel = (
    <>
      {rightTab === 'generate' && <GeneratePanel />}
      {rightTab === 'exercise' && <ExercisePanel />}
      {rightTab === 'muscles' && <MusclePanel />}
      {rightTab === 'technique' && <TechniquePanel />}
      {rightTab === 'correctives' && <CorrectivePanel />}
      {rightTab === 'compare' && <ComparisonPanel />}
      {rightTab === 'review' && <ReviewPanel />}
      {rightTab === 'export' && <ExportPanel />}
    </>
  );

  return (
    <>
      {createPortal(<Toolbar />, shell.slots.toolbar)}
      {createPortal(leftPanel, shell.slots.leftPanel)}
      {createPortal(<Viewport />, shell.slots.viewport)}
      {createPortal(rightPanel, shell.slots.rightPanel)}
      {createPortal(<Timeline />, shell.slots.timeline)}
    </>
  );
}
