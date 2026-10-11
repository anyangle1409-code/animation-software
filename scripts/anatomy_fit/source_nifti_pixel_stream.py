"""Private hash-bound unsigned16 NIfTI-1 voxel reads; NOT verified HU.

Observed subset only:3D, single-file gzip,352-byte unextended header.
No image/world registration, automatic thresholds, geometry or pixel writes.
"""
import gzip
import hashlib
import itertools
import math
from pathlib import Path
import re
import struct
import zlib

from source_surface_component_geometry import require_private


def digest(path):
    with path.open('rb') as fp:
        return hashlib.file_digest(fp,'sha256').hexdigest()


def sample(path,expected_sha256,queries,*,chunk_bytes=524288):
    original=Path(path)
    src=require_private(original)
    if original.is_symlink() or src.stat().st_size>500_000_000:
        raise ValueError('Unsupported source path/compressed size')
    if not re.fullmatch('[0-9a-f]{64}',expected_sha256) or digest(src)!=expected_sha256:
        raise ValueError('Full source SHA256 mismatch')
    if type(chunk_bytes)!=int or not 2<=chunk_bytes<=1048576 or chunk_bytes%2:
        raise ValueError('Pixel chunks require bounded even byte counts')
    queries=list(itertools.islice(queries,100001))
    if len(queries)>100000:
        raise ValueError('Too many diagnostic samples')
    try:
        with gzip.open(src,'rb') as stream:
            h=stream.read(352)
            if len(h)!=352 or h[344:348]!=b'n+1\0' or h[348:352]!=b'\0'*4:
                raise ValueError('Unsupported NIfTI single-file header/extensions')
            endian='<' if struct.unpack_from('<i',h)[0]==348 else '>'
            if struct.unpack_from(endian+'i',h)[0]!=348:
                raise ValueError('Invalid NIfTI header size')
            dims=struct.unpack_from(endian+'8h',h,40)
            if dims[0]!=3 or any(d<=0 for d in dims[1:4]):
                raise ValueError('Unsupported dimensions')
            nx,ny,nz=dims[1:4]
            if struct.unpack_from(endian+'2h',h,70)!=(512,16):
                raise ValueError('Only observed unsigned16 source datatype supported')
            offset,slope,intercept=struct.unpack_from(endian+'3f',h,108)
            if offset!=352 or not all(math.isfinite(v) for v in (slope,intercept)):
                raise ValueError('Unsupported data offset/scalar declaration')
            expected=nx*ny*nz*2
            if expected>1_100_000_000:
                raise ValueError('Decoded pixel budget exceeded')
            ordered=[]
            for i,q in enumerate(queries):
                if not isinstance(q,(tuple,list)) or len(q)!=3 or any(type(x)!=int for x in q):
                    raise ValueError('Samples require integer XYZ indices')
                x,y,z=q
                if not(0<=x<nx and 0<=y<ny and 0<=z<nz):
                    raise ValueError('Sample outside source grid')
                ordered.append((2*(x+nx*(y+ny*z)),i))
            ordered.sort()
            values=[None]*len(queries)
            position=0
            next_sample=0
            while True:
                chunk=stream.read(min(chunk_bytes,expected-position+1))
                if not chunk:
                    break
                if position+len(chunk)>expected:
                    raise ValueError('Extra decoded pixel bytes')
                while next_sample<len(ordered) and ordered[next_sample][0]+2<=position+len(chunk):
                    byte_offset,i=ordered[next_sample]
                    values[i]=struct.unpack_from(endian+'H',chunk,byte_offset-position)[0]
                    next_sample+=1
                position+=len(chunk)
            if position!=expected or any(v is None for v in values):
                raise ValueError('Truncated decoded pixel grid')
    except (OSError,EOFError,zlib.error,struct.error) as exc:
        raise ValueError('Invalid source gzip/header/payload') from exc
    if digest(src)!=expected_sha256:
        raise ValueError('Source bytes changed during pixel reading')
    return {'kind':'PRIVATE_HASH_BOUND_UNREGISTERED_SOURCE_PIXEL_SAMPLES',
            'input_sha256':expected_sha256,'stored_values':values,
            'header_scaled_values':[v*slope+intercept if slope!=0 else v for v in values],
            'source_dimensions':[nx,ny,nz],'source_datatype':'UINT16',
            'source_declared_slope':slope,'source_declared_intercept':intercept,
            'decoded_pixel_bytes_verified':position,'gzip_crc_and_decoded_length_verified':True,
            'hounsfield_units_verified':False,'image_to_surface_registration_verified':False,
            'canonical_promotion_allowed':False,'source_pixels_modified':False}
