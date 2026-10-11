"""Bounded read-only grid-index samples, NOT image/surface registration.

Supports the observed unsigned-char gzip LPS NRRD3D/list-first4D subset only.
Reads through the entire gzip stream for CRC and exact decoded-length checks;
retains only a bounded chunk plus requested labels, never a decoded volume.
"""
import gzip
import hashlib
import io
import itertools
import math
import re
import zlib


def sample(raw, queries, *, chunk_bytes=524288):
    if not isinstance(raw,bytes) or len(raw)>4_000_000:
        raise ValueError('Unsupported compressed input size/type')
    header,separator,payload=raw.partition(b'\n\n')
    if not separator or len(header)>131072 or not header.startswith(b'NRRD0004\n'):
        raise ValueError('Unsupported or missing NRRD header')
    fields={}
    try:
        for line in header.decode('ascii').splitlines()[1:]:
            if not line or line.startswith('#'):
                continue
            key,value=line.split(':',1)
            if key in fields:
                raise ValueError('Duplicate NRRD field')
            fields[key]=value.strip()
        if any(k in fields for k in ('data file','datafile','byte skip','byteskip','line skip','lineskip')):
            raise ValueError('Detached or skipped payload subset unsupported')
        dimension=int(fields['dimension'])
        sizes=[int(x) for x in fields['sizes'].split()]
        if dimension not in (3,4) or len(sizes)!=dimension or any(x<=0 for x in sizes):
            raise ValueError('Unsupported dimensions')
        layers=sizes[0] if dimension==4 else 1
        nx,ny,nz=sizes[-3:]
        expected=math.prod(sizes)
        if layers>16 or expected>1_100_000_000:
            raise ValueError('Decoded volume budget exceeded')
        if fields['type']!='unsigned char' or fields['encoding']!='gzip' or fields['space']!='left-posterior-superior':
            raise ValueError('Unsupported type/encoding/frame')
        if fields['kinds'].split()!=(['list'] if dimension==4 else [])+['domain']*3:
            raise ValueError('Unsupported axis kinds')
        if not re.fullmatch(r'(?:none|\([^()]+\))(?:\s+(?:none|\([^()]+\)))*',fields['space directions']):
            raise ValueError('Malformed direction field')
        directions=re.findall(r'none|\([^()]+\)',fields['space directions'])
        if len(directions)!=dimension or (dimension==4 and directions[0]!='none'):
            raise ValueError('Unsupported spatial axes')
        vectors=[tuple(float(v) for v in x[1:-1].split(',')) for x in directions[-3:]]
        if any(len(v)!=3 or not all(math.isfinite(x) for x in v) for v in vectors):
            raise ValueError('Invalid direction vector')
        if not re.fullmatch(r'\([^()]+\)',fields['space origin']):
            raise ValueError('Malformed origin field')
        origin=tuple(float(x) for x in fields['space origin'][1:-1].split(','))
        if len(origin)!=3 or not all(math.isfinite(x) for x in origin):
            raise ValueError('Invalid origin')
    except (KeyError,UnicodeError,TypeError) as exc:
        raise ValueError('Malformed source header') from exc
    if type(chunk_bytes)!=int or not 1<=chunk_bytes<=1048576:
        raise ValueError('Unsupported stream chunk')
    queries=list(itertools.islice(queries,100001))
    if len(queries)>100000:
        raise ValueError('Too many diagnostic samples')
    ordered=[]
    for i,q in enumerate(queries):
        if not isinstance(q,(tuple,list)) or len(q)!=4 or any(type(x)!=int for x in q):
            raise ValueError('Samples require integer XYZ/layer indices')
        x,y,z,layer=q
        if not(0<=x<nx and 0<=y<ny and 0<=z<nz and 0<=layer<layers):
            raise ValueError('Sample outside source grid/layer')
        ordered.append((layer+layers*(x+nx*(y+ny*z)),i))
    ordered.sort()
    values=[None]*len(queries)
    position=0
    next_sample=0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(payload),mode='rb') as stream:
            while True:
                chunk=stream.read(min(chunk_bytes,expected-position+1))
                if not chunk:
                    break
                if position+len(chunk)>expected:
                    raise ValueError('Extra decoded label bytes')
                while next_sample<len(ordered) and ordered[next_sample][0]<position+len(chunk):
                    offset,i=ordered[next_sample]
                    values[i]=chunk[offset-position]
                    next_sample+=1
                position+=len(chunk)
    except (OSError,EOFError,zlib.error) as exc:
        raise ValueError('Invalid gzip payload/trailer') from exc
    if position!=expected or any(v is None for v in values):
        raise ValueError('Truncated decoded label grid')
    return {'kind':'UNREGISTERED_SOURCE_GRID_INDEX_LABEL_SAMPLES',
            'input_sha256':hashlib.sha256(raw).hexdigest(),
            'label_values':values,'decoded_bytes_verified':position,
            'gzip_crc_and_decoded_length_verified':True,
            'source_spatial_sizes':[nx,ny,nz],'layers':layers,
            'source_declared_space':'LPS','source_space_directions':vectors,
            'source_space_origin':origin,'source_space_units':fields.get('space units'),
            'anatomical_identity_accepted':False,'surface_registration_verified':False,
            'canonical_promotion_allowed':False}
