import { useRef } from 'react';
import type { BoneName } from '../../rig/boneNames';
import { ALL_BONES, boneLabel } from '../../rig/boneNames';
import { REQUIRED_BONES } from '../../retargeting/boneMap';
import { useCharacter } from '../characterStore';
import { useStudio } from '../store';

/**
 * Import a rigged GLB and map its bones onto the canonical rig. The mapping is
 * saved separately from any exercise, so one character serves the whole
 * library.
 */
export function CharacterPanel() {
  const input = useRef<HTMLInputElement | null>(null);
  const { name, character, mapping, report, status, load, clear, persist } =
    useCharacter();
  const setViewMode = useStudio((state) => state.setViewMode);

  return (
    <section className="panel">
      <h2>Character</h2>
      <p className="panel__note">
        Animation is authored on the canonical skeleton and retargeted onto
        whichever character you load, so an exercise never has to be re-animated
        per model.
      </p>

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

      {!character && (
        <p className="panel__empty">
          No character loaded — the viewport shows the standard mannequin.
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
          <MappingRows bones={REQUIRED_BONES} />

          <details>
            <summary>
              Optional bones and fingers ({report.mapped.length - REQUIRED_BONES.filter((bone) => mapping.bones[bone]).length}
              /{ALL_BONES.length - REQUIRED_BONES.length} mapped)
            </summary>
            <p className="panel__note">
              Map these when the automatic match misses fingers, toes, clavicles
              or intermediate spine bones. Finger mapping is required for a
              convincing equipment grip.
            </p>
            <MappingRows bones={ALL_BONES.filter((bone) => !REQUIRED_BONES.includes(bone))} />
          </details>
        </>
      )}
    </section>
  );
}

function MappingRows({ bones }: { bones: readonly BoneName[] }) {
  const character = useCharacter((state) => state.character);
  const mapping = useCharacter((state) => state.mapping);
  const setBone = useCharacter((state) => state.setBone);
  if (!character || !mapping) return null;

  return (
    <div className="mapping-list">
      {bones.map((bone) => (
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
  );
}
