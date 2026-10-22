"""Exclusive byte-copy preparation; no Blender import or source modifications."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def copy_experiment(source,destination,expected_sha256):
    source,destination=Path(source),Path(destination)
    if destination.is_symlink() or source.resolve()==destination.resolve():
        raise ValueError('Source/destination alias is forbidden')
    before=digest(source)
    if before!=expected_sha256: raise ValueError('Source hash mismatch')
    with source.open('rb') as f:
        header=f.read(7)
        # Blender supports compressed files. Hash pins identity; magic is only
        # a pointer/obvious-input guard, never a claim of native validity.
        if not (header==b'BLENDER' or header.startswith(bytes.fromhex('28b52ffd')) or header.startswith(b'\x1f\x8b')):
            raise ValueError('Not recognized Blender/container header; resolve LFS first')
    # x mode rejects all existing files, including hardlinks and dangling symlinks.
    with destination.open('xb') as out, source.open('rb') as inp:
        for block in iter(lambda:inp.read(1024*1024),b''): out.write(block)
    after=digest(source)
    copied=digest(destination)
    if before!=after or copied!=before:
        raise RuntimeError('Source changed during copy or destination differs; do not use candidate')
    return {'source':str(source.resolve()),'experiment':str(destination.resolve()),
            'source_sha256':before,'experiment_sha256':copied,
            'source_unchanged':True,'blender_executed':False,'status':'byte_copy_only'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--sha256',required=True)
    a=p.parse_args()
    print(json.dumps(copy_experiment(a.source,a.out,a.sha256),indent=2))

if __name__=='__main__': main()
