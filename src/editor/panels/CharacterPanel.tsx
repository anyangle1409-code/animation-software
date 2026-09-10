import { useRef } from 'react';
import type { BoneName } from '../../rig/boneNames';
import { boneLabel } from '../../rig/boneNames';
import { REQUIRED_BONES } from '../../retargeting/boneMap';
import { useCharacter } from '../characterStore';
import { characterSources } from '../../character';
import { useStudio } from '../store';

/**
 * Import a rigged GLB and map its bones onto the canonical rig. The mapping is
 * saved separately from any exercise, so one character serves the whole
 * library.
 */
export function CharacterPanel() {
  const input = useRef<HTMLInputElement | null>(null);
  const {
    name,
    character,
    mapping,
    report,
    rebind,
    status,
    sourceId,
    sourceStatus,
    bindMode,
    setSource,
    setBindMode,
    load,
    setBone,
    clear,
    persist,
  } = useCharacter();
  const setViewMode = useStudio((state) => state.setViewMode);
  const sources = characterSources();

  return (
    <section className="panel">
      <h2>Character</h2>
      <p className="panel__note">
        Animation is authored on the canonical skeleton and driven onto
        whichever character is selected, so an exercise never has to be
        re-animated per model.
      </p>

      <label className="mapping-row">
        <span className="mapping-row__name">Character</span>
        <select value={sourceId} onChange={(event) => setSource(event.target.value)}>
          {sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.label}
            </option>
          ))}
        </select>
      </label>
      {sourceStatus.kind === 'error' && <div className="status is-warn">{sourceStatus.message}</div>}

      <label className="mapping-row">
        <span className="mapping-row__name">Imports bind by</span>
        <select value={bindMode} onChange={(event) => setBindMode(event.target.value as 'rebind' | 'retarget')}>
          <option value="rebind">Rebinding onto the studio rig</option>
          <option value="retarget">Retargeting its own skeleton</option>
        </select>
      </label>

      <input
        ref={input}
        type="file"
        accept=".glb,.gltf,model/gltf-binary"
        style={{ display: 'none' }}
        onChange={async (event) => {
          const file = event.target.files?.[0];
          if (!file) return;
          await load(file);
          setViewMode('character');
          event.target.value = '';
        }}
      />

      <div className="button-row">
        <button type="button" className="primary" onClick={() => input.current?.click()}>
          Import rigged GLB
        </button>
        {character && (
          <button type="button" onClick={clear}>
            Remove
          </button>
        )}
      </div>

      {status.kind === 'loading' && <div className="status is-ok">{status.message}</div>}
      {status.kind === 'error' && <div className="status is-warn">{status.message}</div>}

      {rebind && rebind.length > 0 && (
        <div className="status is-ok">
          <strong>{name}</strong>
          <div className="status__row">
            {rebind.reduce((total, part) => total + part.vertices, 0)} vertices rebound onto{' '}
            {rebind[0].mappedBones.length} mapped bones, scaled ×{rebind[0].scale.toFixed(2)}.
          </div>
          {rebind.some((part) => part.orphaned > 0) && (
            <div className="status__row">
              {rebind.reduce((total, part) => total + part.orphaned, 0)} vertices had no mapped
              bone and were pinned to the pelvis.
            </div>
          )}
        </div>
      )}

      {!character && !rebind && (
        <p className="panel__empty">
          No character imported — the viewport shows the selected built-in character.
        </p>
      )}

      {character && mapping && report && (
        <>
          <div className={`status ${report.missingRequired.length === 0 ? 'is-ok' : 'is-warn'}`}>
            <strong>{name}</strong>
            <div className="status__row">
              {character.bones.size} bones, {character.height.toFixed(2)} m tall.
            </div>
            <div className="status__row">
              {report.mapped.length} bones mapped
              {report.missingRequired.length > 0
                ? `, ${report.missingRequired.length} required bones still unmapped`
                : ' — ready to retarget'}
              .
            </div>
          </div>

          <div className="button-row">
            <button type="button" onClick={persist}>
              Save mapping for reuse
            </button>
          </div>

          <h3>Bone mapping</h3>
          <p className="panel__note">
            Anything the guesser could not identify is left blank rather than
            matched to something that merely looks right.
          </p>
          <div className="mapping-list">
            {REQUIRED_BONES.map((bone: BoneName) => (
              <label key={bone} className="mapping-row">
                <span className="mapping-row__name">{boneLabel(bone)}</span>
                <select
                  value={mapping.bones[bone] ?? ''}
                  onChange={(event) => setBone(bone, event.target.value || null)}
                  className={mapping.bones[bone] ? '' : 'is-missing'}
                >
                  <option value="">— unmapped —</option>
                  {character.boneNames.map((target) => (
                    <option key={target} value={target}>
                      {target}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
