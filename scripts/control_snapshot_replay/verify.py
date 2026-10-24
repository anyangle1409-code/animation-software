"""Verify pinned frozen-snapshot bytes for cloud render replay; no model opening."""
import argparse
import hashlib
import json
from pathlib import Path

W8_SHA = '2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c'
CONDITIONS = ('observed', 'S5_muted', 'S7_muted', 'all_nonbasis_keys_muted')


def verify(manifest_raw, directory, expected_manifest_sha256):
    digest = hashlib.sha256(manifest_raw).hexdigest()
    if digest != expected_manifest_sha256:
        raise ValueError('pinned native render manifest hash mismatch')
    manifest = json.loads(manifest_raw)
    if (manifest.get('source_sha256') != W8_SHA
            or manifest.get('status') != 'ACTUAL_BLENDER_RENDER_OF_FROZEN_EVALUATED_GEOMETRY_NOT_REPAIR'
            or any(manifest.get(k) is not False for k in
                   ('anatomical_approval', 'saved_blend', 'original_blend_opened_by_renderer'))):
        raise ValueError('unapproved frozen W8 provenance required')
    samples = manifest.get('samples', [])
    if len(samples) != 2 or [row.get('sample') for row in samples] != [0, 6]:
        raise ValueError('exact native samples0/6 required')
    expected_names = {f'sample{i:02d}__{c}.npz' for i in (0, 6) for c in CONDITIONS}
    directory = Path(directory)
    if {p.name for p in directory.glob('*.npz')} != expected_names:
        raise ValueError('snapshot inventory mismatch')
    files = []
    for sample in samples:
        rows = sample.get('conditions', [])
        if len(rows) != 4 or {r.get('condition') for r in rows} != set(CONDITIONS):
            raise ValueError('exact four native conditions required')
        for row in rows:
            name = f"sample{sample['sample']:02d}__{row['condition']}.npz"
            observed = hashlib.sha256((directory/name).read_bytes()).hexdigest()
            if observed != row.get('snapshot_npz_sha256'):
                raise ValueError('snapshot hash mismatch: '+name)
            files.append({'file': name, 'sha256': observed})
    return {'status': 'HASH_VERIFIED_FROZEN_W8_SNAPSHOT_BYTES_NOT_ANATOMICAL_APPROVAL',
            'source_sha256': W8_SHA, 'pinned_manifest_sha256': digest,
            'anatomical_approval': False, 'native_npz_geometry_revalidated': False,
            'verified_files': files,
            'limitation': 'Byte identity only; renderer separately checks NPZ geometry/topology. No new movement or source repair.'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--snapshots',type=Path,required=True)
    parser.add_argument('--expected-manifest-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.manifest.read_bytes(),args.snapshots,args.expected_manifest_sha256)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'],len(result['verified_files']),flush=True)


if __name__ == '__main__':
    main()
