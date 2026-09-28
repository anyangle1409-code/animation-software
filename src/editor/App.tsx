import { useEffect } from 'react';
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
import { bindStudioKeyboard } from './keyboardController';
import { useStudioLayout } from './layoutState';

export function App() {
  const leftTab = useStudioLayout((state) => state.leftTab);
  const rightTab = useStudioLayout((state) => state.rightTab);
  const panelsOpen = useStudioLayout((state) => state.panelsOpen);
  const setLeftTab = useStudioLayout((state) => state.setLeftTab);
  const setRightTab = useStudioLayout((state) => state.setRightTab);
  const togglePanels = useStudioLayout((state) => state.togglePanels);

  useEffect(() => bindStudioKeyboard(window), []);

  return (
    <div className={`studio ${panelsOpen ? '' : 'studio--focus'}`}>
      <Toolbar />

      <div className="studio__body">
        <aside className="studio__side studio__side--left">
          <nav className="tabs">
            <button
              type="button"
              className={leftTab === 'joint' ? 'is-active' : ''}
              onClick={() => setLeftTab('joint')}
            >
              Joint
            </button>
            <button
              type="button"
              className={leftTab === 'grip' ? 'is-active' : ''}
              onClick={() => setLeftTab('grip')}
            >
              Grip
            </button>
            <button
              type="button"
              className={leftTab === 'ik' ? 'is-active' : ''}
              onClick={() => setLeftTab('ik')}
            >
              IK &amp; locks
            </button>
            <button
              type="button"
              className={leftTab === 'contacts' ? 'is-active' : ''}
              onClick={() => setLeftTab('contacts')}
            >
              Contacts
            </button>
            <button
              type="button"
              className={leftTab === 'equipment' ? 'is-active' : ''}
              onClick={() => setLeftTab('equipment')}
            >
              Equipment
            </button>
            <button
              type="button"
              className={leftTab === 'character' ? 'is-active' : ''}
              onClick={() => setLeftTab('character')}
            >
              Character
            </button>
          </nav>
          <div className="studio__side-body">
            {leftTab === 'joint' && <JointPanel />}
            {leftTab === 'grip' && <GripPanel />}
            {leftTab === 'ik' && <IKPanel />}
            {leftTab === 'contacts' && <ContactPanel />}
            {leftTab === 'equipment' && <EquipmentPanel />}
            {leftTab === 'character' && <CharacterPanel />}
          </div>
        </aside>

        <main className="studio__viewport">
          <Viewport />
          <button
            type="button"
            className="studio__panel-toggle"
            onClick={togglePanels}
          >
            {panelsOpen ? 'Hide panels' : 'Show panels'}
          </button>
        </main>

        <aside className="studio__side studio__side--right">
          <nav className="tabs">
            <button
              type="button"
              className={rightTab === 'generate' ? 'is-active' : ''}
              onClick={() => setRightTab('generate')}
            >
              Generate
            </button>
            <button
              type="button"
              className={rightTab === 'exercise' ? 'is-active' : ''}
              onClick={() => setRightTab('exercise')}
            >
              Exercise
            </button>
            <button
              type="button"
              className={rightTab === 'muscles' ? 'is-active' : ''}
              onClick={() => setRightTab('muscles')}
            >
              Muscles
            </button>
            <button
              type="button"
              className={rightTab === 'technique' ? 'is-active' : ''}
              onClick={() => setRightTab('technique')}
            >
              Technique
            </button>
            <button
              type="button"
              className={rightTab === 'correctives' ? 'is-active' : ''}
              onClick={() => setRightTab('correctives')}
            >
              Correctives
            </button>
            <button
              type="button"
              className={rightTab === 'compare' ? 'is-active' : ''}
              onClick={() => setRightTab('compare')}
            >
              Compare
            </button>
            <button
              type="button"
              className={rightTab === 'review' ? 'is-active' : ''}
              onClick={() => setRightTab('review')}
            >
              Review
            </button>
            <button
              type="button"
              className={rightTab === 'export' ? 'is-active' : ''}
              onClick={() => setRightTab('export')}
            >
              Export
            </button>
          </nav>
          <div className="studio__side-body">
            {rightTab === 'generate' && <GeneratePanel />}
            {rightTab === 'exercise' && <ExercisePanel />}
            {rightTab === 'muscles' && <MusclePanel />}
            {rightTab === 'technique' && <TechniquePanel />}
            {rightTab === 'correctives' && <CorrectivePanel />}
            {rightTab === 'compare' && <ComparisonPanel />}
            {rightTab === 'review' && <ReviewPanel />}
            {rightTab === 'export' && <ExportPanel />}
          </div>
        </aside>
      </div>

      <Timeline />
    </div>
  );
}
