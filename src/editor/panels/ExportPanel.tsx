import { useState } from 'react';
import { exportGlb } from '../../export/glb';
import { exportRetargetedGlb } from '../../export/retargeted';
import { exportAnimationJson, exportMetadataJson } from '../../export/json';
import { downloadBlob, downloadJson } from '../../export/download';
import { skeleton, useStudio } from '../store';
import { useCharacter } from '../characterStore';

type Status = { kind: 'idle' | 'busy' | 'done' | 'error'; message?: string };

export function ExportPanel() {
  const clip = useStudio((state) => state.document.clip);
  const exercise = useStudio((state) => state.document.exercise);
  const [fps, setFps] = useState(30);
  const [includeEquipment, setIncludeEquipment] = useState(true);
  const [status, setStatus] = useState<Status>({ kind: 'idle' });
  const characterName = useCharacter((state) => state.name);
  const binding = useCharacter((state) => state.binding);
  const mappingReport = useCharacter((state) => state.report);

  const run = async (label: string, task: () => Promise<void> | void) => {
    setStatus({ kind: 'busy', message: `Building ${label}…` });
    try {
      await task();
      setStatus({ kind: 'done', message: `${label} downloaded.` });
    } catch (error) {
      setStatus({ kind: 'error', message: (error as Error).message });
    }
  };

  return (
    <section className="panel">
      <h2>Export</h2>
      <p className="panel__note">
        Clip name <code>{clip.name}</code>, {clip.duration.toFixed(2)}s, looping.
      </p>

      <label className="field">
        <span className="field__label">Sample rate</span>
        <select value={fps} onChange={(event) => setFps(Number(event.target.value))}>
          {[24, 30, 60].map((value) => (
            <option key={value} value={value}>
              {value} fps
            </option>
          ))}
        </select>
      </label>

      <label className="field field--check">
        <input
          type="checkbox"
          checked={includeEquipment}
          onChange={(event) => setIncludeEquipment(event.target.checked)}
        />
        <span>Include equipment in the GLB</span>
      </label>

      <h3>Animated GLB</h3>
      <p className="panel__note">
        Rig, animation clip and equipment in one file, ready to drop into the app.
      </p>
      <button
        type="button"
        className="primary"
        onClick={() =>
          run('GLB', async () => {
            const blob = await exportGlb(clip, exercise, { fps, includeEquipment });
            downloadBlob(blob, `${clip.name}.glb`);
          })
        }
      >
        Export {clip.name}.glb
      </button>

      <h3>Imported character GLB</h3>
      <p className="panel__note">
        Bakes this clip onto the loaded character's own skeleton and positions
        equipment from that character's hands.
      </p>
      <button
        type="button"
        disabled={!binding || Boolean(mappingReport?.missingRequired.length)}
        onClick={() =>
          binding &&
          run('character GLB', async () => {
            const blob = await exportRetargetedGlb(clip, binding, { fps, includeEquipment });
            const safeName = (characterName ?? 'character').replace(/[^a-z0-9_-]+/gi, '_');
            downloadBlob(blob, `${clip.name}.${safeName}.glb`);
          })
        }
      >
        {binding ? `Export ${characterName ?? 'character'}` : 'Import a character first'}
      </button>
      {binding && mappingReport && mappingReport.missingRequired.length > 0 && (
        <p className="panel__note is-warn">
          Map every required body bone before exporting this character.
        </p>
      )}

      <h3>Clip only</h3>
      <p className="panel__note">
        The skeleton and animation without the character mesh, so many exercises
        can share one downloaded character.
      </p>
      <div className="button-row">
        <button
          type="button"
          onClick={() =>
            run('clip GLB', async () => {
              const blob = await exportGlb(clip, exercise, { fps, clipOnly: true });
              downloadBlob(blob, `${clip.name}.anim.glb`);
            })
          }
        >
          GLB
        </button>
        <button
          type="button"
          onClick={() =>
            run('clip JSON', () => {
              downloadJson(
                exportAnimationJson(clip, exercise, skeleton, fps),
                `${clip.name}.anim.json`,
              );
            })
          }
        >
          JSON
        </button>
      </div>

      <h3>Exercise metadata</h3>
      <p className="panel__note">
        The full definition — phases, muscles, technique rules, camera and common
        errors — for the Home Gym PT exercise database.
      </p>
      <button
        type="button"
        onClick={() =>
          run('metadata', () => {
            downloadJson(exportMetadataJson(exercise), `${exercise.id}.json`);
          })
        }
      >
        Export {exercise.id}.json
      </button>

      {status.kind !== 'idle' && (
        <div className={`status ${status.kind === 'error' ? 'is-warn' : 'is-ok'}`}>
          {status.message}
        </div>
      )}
    </section>
  );
}
