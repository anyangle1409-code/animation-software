import { useEffect, useState } from 'react';
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
import { useStudio } from './store';

type LeftTab = 'joint' | 'ik' | 'character';
type RightTab = 'exercise' | 'muscles' | 'technique' | 'export';

export function App() {
  const [leftTab, setLeftTab] = useState<LeftTab>('joint');
  const [rightTab, setRightTab] = useState<RightTab>('exercise');
  const [panelsOpen, setPanelsOpen] = useState(true);

  const undo = useStudio((state) => state.undo);
  const redo = useStudio((state) => state.redo);
  const togglePlay = useStudio((state) => state.togglePlay);
  const setKeyframe = useStudio((state) => state.setKeyframe);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target && /^(INPUT|SELECT|TEXTAREA)$/.test(target.tagName)) return;
      const meta = event.ctrlKey || event.metaKey;
      if (meta && event.key.toLowerCase() === 'z') {
        event.preventDefault();
        if (event.shiftKey) redo();
        else undo();
      } else if (meta && event.key.toLowerCase() === 'y') {
        event.preventDefault();
        redo();
      } else if (event.code === 'Space') {
        event.preventDefault();
        togglePlay();
      } else if (event.key.toLowerCase() === 'k') {
        setKeyframe();
      } else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        const store = useStudio.getState();
        const direction = event.key === 'ArrowLeft' ? -1 : 1;
        const frames = event.shiftKey ? 5 : 1;
        store.pause();
        store.setTime(store.time + (direction * frames) / store.document.clip.fps);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [undo, redo, togglePlay, setKeyframe]);

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
              className={leftTab === 'ik' ? 'is-active' : ''}
              onClick={() => setLeftTab('ik')}
            >
              IK &amp; locks
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
            {leftTab === 'ik' && <IKPanel />}
            {leftTab === 'character' && <CharacterPanel />}
          </div>
        </aside>

        <main className="studio__viewport">
          <Viewport />
          <button
            type="button"
            className="studio__panel-toggle"
            onClick={() => setPanelsOpen((open) => !open)}
          >
            {panelsOpen ? 'Hide panels' : 'Show panels'}
          </button>
        </main>

        <aside className="studio__side studio__side--right">
          <nav className="tabs">
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
              className={rightTab === 'export' ? 'is-active' : ''}
              onClick={() => setRightTab('export')}
            >
              Export
            </button>
          </nav>
          <div className="studio__side-body">
            {rightTab === 'exercise' && <ExercisePanel />}
            {rightTab === 'muscles' && <MusclePanel />}
            {rightTab === 'technique' && <TechniquePanel />}
            {rightTab === 'export' && <ExportPanel />}
          </div>
        </aside>
      </div>

      <Timeline />
    </div>
  );
}
