import { useMemo, useState } from 'react';
import { useAlignment } from '../alignmentStore';
import { useCharacter } from '../characterStore';
import { useStudio } from '../store';
import { ZERO_CORRECTION, isZeroCorrection } from '../../character/alignment';
import type { BoneCorrection } from '../../character/alignment';

const ROTATE: { key: keyof BoneCorrection; label: string }[] = [
  { key: 'rx', label: 'Rotate X' },
  { key: 'ry', label: 'Rotate Y' },
  { key: 'rz', label: 'Rotate Z' },
];
const MOVE: { key: keyof BoneCorrection; label: string }[] = [
  { key: 'tx', label: 'Move X' },
  { key: 'ty', label: 'Move Y' },
  { key: 'tz', label: 'Move Z' },
];

/**
 * Bone alignment: nudge a character bone that does not sit where the body
 * needs it, and watch the deformation change on the playing animation.
 */
export function AlignPanel() {
  const build = useCharacter((state) => state.active);
  const corrections = useAlignment((state) => state.corrections);
  const selected = useAlignment((state) => state.selected);
  const select = useAlignment((state) => state.select);
  const setValue = useAlignment((state) => state.setValue);
  const resetBone = useAlignment((state) => state.resetBone);
  const resetAll = useAlignment((state) => state.resetAll);
  const showBones = useAlignment((state) => state.showCharacterBones);
  const toggleBones = useAlignment((state) => state.toggleCharacterBones);
  const exportText = useAlignment((state) => state.exportText);
  const importText = useAlignment((state) => state.importText);
  const rigBone = useStudio((state) => state.selection.bone);
  const characterOn = useStudio((state) => state.layers.character);
  const toggleLayer = useStudio((state) => state.toggleLayer);
  const [filter, setFilter] = useState('');
  const [paste, setPaste] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const names = useMemo(() => (build?.bones ?? []).map((bone) => bone.name), [build]);
  const shown = names.filter((name) => name.toLowerCase().includes(filter.trim().toLowerCase()));
  const edited = Object.keys(corrections).filter((name) => !isZeroCorrection(corrections[name]));
  const value = selected ? corrections[selected] ?? ZERO_CORRECTION : ZERO_CORRECTION;
  const rigMatch = rigBone && names.includes(rigBone) ? rigBone : null;

  if (!build) {
    return (
      <section className="panel align-panel">
        <h2>Bone alignment</h2>
        <p className="panel__hint">Turn on the Character layer to align its bones.</p>
        {!characterOn && (
          <div className="button-row">
            <button type="button" className="primary" onClick={() => toggleLayer('character')}>
              Show character
            </button>
          </div>
        )}
      </section>
    );
  }

  return (
    <section className="panel align-panel">
      <h2>Bone alignment</h2>
      <p className="panel__hint">
        Pick a bone, then rotate or move it until the body sits right on it. Changes show live on the animation and are
        saved on this device for this character.
      </p>

      <label className="field field--check">
        <input type="checkbox" checked={showBones} onChange={toggleBones} />
        <span>Show the character's bones (tap a joint to pick it)</span>
      </label>

      <label className="field">
        <span className="field__label">Bone ({names.length})</span>
        <input type="search" placeholder="Filter, e.g. upperarm" value={filter} onChange={(event) => setFilter(event.target.value)} />
      </label>
      <select
        className="align-panel__list"
        size={6}
        value={selected ?? ''}
        onChange={(event) => select(event.target.value || null)}
      >
        {shown.map((name) => (
          <option key={name} value={name}>
            {isZeroCorrection(corrections[name]) ? name : `● ${name}`}
          </option>
        ))}
      </select>
      {rigMatch && rigMatch !== selected && (
        <div className="button-row">
          <button type="button" onClick={() => select(rigMatch)}>
            Use selected joint ({rigMatch})
          </button>
        </div>
      )}

      {selected ? (
        <>
          <h3>{selected}</h3>
          {ROTATE.map(({ key, label }) => (
            <label key={key} className="field field--slider">
              <span className="field__label">
                {label} <strong>{value[key].toFixed(1)}°</strong>
              </span>
              <input type="range" min={-45} max={45} step={0.5} value={value[key]} onChange={(event) => setValue(selected, key, Number(event.target.value))} />
            </label>
          ))}
          {MOVE.map(({ key, label }) => (
            <label key={key} className="field field--slider">
              <span className="field__label">
                {label} <strong>{value[key].toFixed(1)} cm</strong>
              </span>
              <input type="range" min={-5} max={5} step={0.1} value={value[key]} onChange={(event) => setValue(selected, key, Number(event.target.value))} />
            </label>
          ))}
          <div className="button-row">
            <button type="button" onClick={() => resetBone(selected)} disabled={isZeroCorrection(corrections[selected])}>
              Reset this bone
            </button>
          </div>
        </>
      ) : (
        <p className="panel__empty">No bone picked.</p>
      )}

      <h3>Corrected bones ({edited.length})</h3>
      {edited.length > 0 ? (
        <>
          <p className="muted">{edited.join(', ')}</p>
          <div className="button-row">
            <button type="button" onClick={resetAll}>
              Reset all
            </button>
            <button
              type="button"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(exportText());
                  setMessage('Copied. Paste it to Claude to bake these into the model.');
                } catch {
                  setPaste(exportText());
                  setMessage('Copy the text below.');
                }
              }}
            >
              Copy corrections
            </button>
          </div>
        </>
      ) : (
        <p className="panel__empty">None yet.</p>
      )}

      <label className="field">
        <span className="field__label">Paste corrections</span>
        <textarea rows={3} value={paste} onChange={(event) => setPaste(event.target.value)} placeholder='{"upperarm_l": {"rx": 0, ...}}' />
      </label>
      <div className="button-row">
        <button
          type="button"
          disabled={!paste.trim()}
          onClick={() => {
            const error = importText(paste);
            setMessage(error ? `Not applied: ${error}` : 'Applied.');
          }}
        >
          Apply pasted
        </button>
      </div>
      {message && <p className="panel__note">{message}</p>}
    </section>
  );
}
