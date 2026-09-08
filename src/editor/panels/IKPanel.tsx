import { useMemo } from 'react';
import { IK_CHAINS, IK_CHAIN_IDS } from '../../ik/chains';
import { sampleClip } from '../../animation/clip';
import { useStudio } from '../store';

/** IK targets, pole targets and the locks that hold contacts in place. */
export function IKPanel() {
  const clip = useStudio((state) => state.document.clip);
  const time = useStudio((state) => state.time);
  const toggleIK = useStudio((state) => state.toggleIK);
  const selectHandle = useStudio((state) => state.selectHandle);
  const selection = useStudio((state) => state.selection.handle);
  const setLockEnabled = useStudio((state) => state.setLockEnabled);
  const showIkHandles = useStudio((state) => state.showIkHandles);
  const toggle = useStudio((state) => state.toggle);

  const sample = useMemo(() => sampleClip(clip, time), [clip, time]);

  return (
    <section className="panel">
      <h2>Inverse kinematics</h2>

      <label className="field field--check">
        <input
          type="checkbox"
          checked={showIkHandles}
          onChange={() => toggle('showIkHandles')}
        />
        <span>Show handles in viewport</span>
      </label>

      {IK_CHAIN_IDS.map((chainId) => {
        const chain = IK_CHAINS[chainId];
        const goal = sample.ik[chainId];
        const active = Boolean(goal?.enabled);
        return (
          <div key={chainId} className={`ik-chain ${active ? 'is-active' : ''}`}>
            <div className="ik-chain__head">
              <label className="field field--check">
                <input type="checkbox" checked={active} onChange={() => toggleIK(chainId)} />
                <span>{chain.label}</span>
              </label>
            </div>
            {active && goal && (
              <div className="ik-chain__body">
                <button
                  type="button"
                  className={
                    selection?.chain === chainId && selection.kind === 'target' ? 'is-active' : ''
                  }
                  onClick={() => selectHandle({ chain: chainId, kind: 'target' })}
                >
                  Target&nbsp;
                  <code>
                    {goal.target.x.toFixed(2)}, {goal.target.y.toFixed(2)},{' '}
                    {goal.target.z.toFixed(2)}
                  </code>
                </button>
                <button
                  type="button"
                  className={
                    selection?.chain === chainId && selection.kind === 'pole' ? 'is-active' : ''
                  }
                  onClick={() => selectHandle({ chain: chainId, kind: 'pole' })}
                >
                  {chain.poleLabel} pole&nbsp;
                  <code>
                    {goal.pole.x.toFixed(2)}, {goal.pole.y.toFixed(2)}, {goal.pole.z.toFixed(2)}
                  </code>
                </button>
              </div>
            )}
          </div>
        );
      })}

      <h3>Locks</h3>
      {clip.locks.length === 0 && <p className="panel__empty">This exercise defines no locks.</p>}
      {clip.locks.map((lock) => (
        <label key={lock.id} className="field field--check">
          <input
            type="checkbox"
            checked={lock.enabled}
            onChange={(event) => setLockEnabled(lock.id, event.target.checked)}
          />
          <span>
            {IK_CHAINS[lock.chain].label} — {lockDescription(lock.mode)}
          </span>
        </label>
      ))}
    </section>
  );
}

const lockDescription = (mode: string): string => {
  if (mode === 'floor') return 'planted where it starts';
  if (mode === 'equipment') return 'held to equipment';
  return 'held at a fixed point';
};
