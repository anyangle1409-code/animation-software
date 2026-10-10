#!/usr/bin/env python3
"""Claude-owned, stdlib-only geometry for the two pinned NLM 3 mm CT windows.

Scope (and only this scope):
  * validate PRIVATE, externally stored original NLM PNG + scanner-header files
    against the SHA-256 pins, failing closed on any mismatch;
  * parse ONLY an allowlist of numeric scanner-geometry fields (never patient or
    operator fields) and build each slice's plane in original scanner RAS mm;
  * map an image pixel (row, col) to scanner RAS with an explicit, conservative
    uncertainty envelope that keeps the unverified pixel-origin convention open;
  * decode the 16-bit grayscale PNG and write a windowed 8-bit DISPLAY copy for
    Blender, only into a private directory outside the repository.

Non-goals (all remain UNVERIFIED and are asserted False in every result):
  * no anatomical identification, no bone segmentation, no 3-D surface;
  * no Hounsfield calibration (stored PNG values are never called HU);
  * no scanner -> Home Gym PT world transform.  The display axis mapping in
    `scanner_ras_to_display_m` is a fixed rotation for viewing only.

Assumption stated, not verified: GE "R/A/S" header names mean +R = patient
right, +A = anterior, +S = superior.  Image laterality (which side of the
picture is the patient's right) MUST be confirmed visually by the reviewer from
an unambiguous laterality cue before any left/right label is recorded.

No raw CT pixels, raw headers or windowed derivatives may live inside the git
worktree; `assert_private_location` refuses such paths.
"""
import argparse
import hashlib
import json
import math
import re
import struct
import sys
import zlib
from array import array
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

TRIPLETS = ((1749, 1752, 1755), (1797, 1800, 1803))
ALL_IDS = tuple(i for t in TRIPLETS for i in t)
EXPECTED_PIXEL_SPACING_MM = 0.898438
EXPECTED_THICKNESS_MM = 3.0
GRID = 512
MAX_PNG_BYTES = 2_000_000
MAX_HEADER_BYTES = 64 * 1024
SPACING_TOL = 1e-6

# Fixed display-only rotation scanner RAS -> project Blender axes
# (+X anatomical left, -Y anterior, +Z superior).  det = +1, no mirroring.
DISPLAY_AXIS_SIGNS = (-1.0, -1.0, 1.0)

HEADER_KEYS = {
    "Image matrix size - X": "width_pixels",
    "Image matrix size - Y": "height_pixels",
    "Image pixel size - X": "pixel_spacing_x_mm",
    "Image pixel size - Y": "pixel_spacing_y_mm",
    "Slice Thickness (mm)": "slice_thickness_mm",
    "Spacing Between scans(mm)": "series_nominal_slice_spacing_mm",
    "Image location": "image_location_mm",
    "Center R coord of plane image": "scanner_R_centre_mm",
    "Center A coord of plane image": "scanner_A_centre_mm",
    "Center S coord of Plane image": "scanner_S_centre_mm",
    "R Coord of Top Left Hand Corner": "R_TL_mm",
    "A Coord of Top Left Hand Corner": "A_TL_mm",
    "S Coord of Top Left Hand Corner": "S_TL_mm",
    "R Coord of Top Right Hand Corner": "R_TR_mm",
    "A Coord of Top Right Hand Corner": "A_TR_mm",
    "S Coord of Top Right Hand Corner": "S_TR_mm",
    "R Coord of Bottom Right Hand Corner": "R_BR_mm",
    "A Coord of Bottom Right Hand Corner": "A_BR_mm",
    "S Coord of Bottom Right Hand Corner": "S_BR_mm",
    "Normal R coord": "normal_R",
    "Normal A coord": "normal_A",
    "Normal S coord": "normal_S",
}
INTEGER_FIELDS = {"width_pixels", "height_pixels"}

CONVENTIONS = ("outer_edge", "first_pixel_centre")

FALSE_FLAGS = {
    "anatomical_region_identified": False,
    "bone_surface_segmentation_verified": False,
    "original_CT_pixel_HU_verified": False,
    "voxel_index_to_physical_sample_centre_convention_verified": False,
    "image_laterality_verified": False,
    "HomeGymPT_world_transform_applied": False,
    "canonical_promotion_allowed": False,
}


class PinError(ValueError):
    """A private source file does not match the pinned manifest."""


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def load_pinned_manifest(source):
    """Validate and normalise the six-frame pinned manifest.

    `source` is a path or an already-parsed dict.  The manifest must keep every
    anatomy/promotion flag False; a manifest that claims otherwise is rejected.
    Returns {source_id: {...}} plus the raw groups under key 'groups'.
    """
    m = json.loads(Path(source).read_text()) if not isinstance(source, dict) else source
    if (m.get("schema_version") != 1
            or m.get("kind") != "PINNED_NLM_SIX_ADJACENT_ORIGINAL_CT_FRAMES"):
        raise PinError("unexpected pinned manifest schema/kind")
    for flag in ("anatomical_features_identified", "canonical_promotion_allowed",
                 "patient_scanner_to_HGPT_world_verified",
                 "source_CT_HU_calibration_verified",
                 "source_segmented_bone_surfaces_verified",
                 "pixels_or_original_headers_committed",
                 "patient_identifiers_exported"):
        if m.get(flag) is not False:
            raise PinError(f"pinned manifest must keep {flag} false")
    if (m.get("pixel_spacing_xy_mm") != [EXPECTED_PIXEL_SPACING_MM] * 2
            or m.get("slice_thickness_mm") != EXPECTED_THICKNESS_MM
            or m.get("nominal_spacing_mm") != EXPECTED_THICKNESS_MM):
        raise PinError("pinned manifest grid does not match 0.898438 mm / 3 mm")
    rows = m.get("exact_png_and_scanner_header_sha256")
    if not isinstance(rows, list) or len(rows) != 6:
        raise PinError("six pinned source identities required")
    by_id = {}
    for r in rows:
        sid = r.get("source_id")
        if sid in by_id or sid not in ALL_IDS:
            raise PinError("unexpected or duplicate pinned source id")
        if not (_HEX64.match(str(r.get("png_sha256", "")))
                and _HEX64.match(str(r.get("scanner_header_sha256", "")))):
            raise PinError("pinned SHA-256 must be 64 lowercase hex characters")
        if (type(r.get("png_bytes")) is not int
                or not 0 < r["png_bytes"] <= MAX_PNG_BYTES):
            raise PinError("pinned PNG byte count invalid")
        by_id[sid] = dict(r)
    if set(by_id) != set(ALL_IDS):
        raise PinError("pinned manifest does not cover the exact six ids")
    groups = m.get("groups")
    if not isinstance(groups, list) or len(groups) != 2:
        raise PinError("two pinned windows required")
    for g, ids in zip(groups, TRIPLETS):
        if tuple(g.get("source_ids", ())) != ids:
            raise PinError("pinned window ids differ from the reviewed triplets")
        s = g.get("scanner_S_mm")
        if (not isinstance(s, list) or len(s) != 3
                or [by_id[i]["scanner_S_mm"] for i in ids] != s):
            raise PinError("pinned scanner S disagrees between window and rows")
        if any(abs((a - b) - EXPECTED_THICKNESS_MM) > 1e-9 for a, b in zip(s, s[1:])):
            raise PinError("pinned window is not a contiguous 3 mm sequence")
    out = {"by_id": by_id, "groups": groups}
    return out


def frame_name(source_id, ext):
    return f"cvm{int(source_id)}f.{ext}"


# --------------------------------------------------------------------------
# Private storage guards and hashing
# --------------------------------------------------------------------------
def assert_private_location(path, repo_root=REPO_ROOT):
    """Refuse any path inside the git worktree (raw CT must stay untracked)."""
    p = Path(path).resolve()
    root = Path(repo_root).resolve()
    if p == root or root in p.parents:
        raise PinError("private CT paths must be outside the repository worktree")
    return p


def sha256_regular_file(path, max_bytes):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise PinError(f"{p.name}: not a regular file")
    size = p.stat().st_size
    if size > max_bytes:
        raise PinError(f"{p.name}: exceeds size limit")
    h = hashlib.sha256()
    n = 0
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            n += len(chunk)
            if n > max_bytes:
                raise PinError(f"{p.name}: exceeds size limit")
            h.update(chunk)
    return h.hexdigest(), n


def validate_private_inputs(ct_dir, manifest, repo_root=REPO_ROOT):
    """Hash every PNG/header in `ct_dir` against the pins; raise on ANY mismatch.

    Returns one record per frame.  Nothing from the files' contents is returned
    except hashes and byte counts.
    """
    base = assert_private_location(ct_dir, repo_root)
    if not base.is_dir():
        raise PinError("CT directory missing")
    pins = manifest["by_id"] if "by_id" in manifest else manifest
    records = []
    for sid in ALL_IDS:
        pin = pins[sid]
        png = base / frame_name(sid, "png")
        hdr = base / frame_name(sid, "txt")
        png_sha, png_n = sha256_regular_file(png, MAX_PNG_BYTES)
        hdr_sha, hdr_n = sha256_regular_file(hdr, MAX_HEADER_BYTES)
        if png_n != pin["png_bytes"]:
            raise PinError(f"{png.name}: byte count differs from pin")
        if png_sha != pin["png_sha256"]:
            raise PinError(f"{png.name}: SHA-256 differs from pin")
        if hdr_sha != pin["scanner_header_sha256"]:
            raise PinError(f"{hdr.name}: SHA-256 differs from pin")
        records.append({
            "source_id": sid,
            "png_filename": png.name,
            "png_sha256": png_sha,
            "png_bytes": png_n,
            "header_filename": hdr.name,
            "header_sha256": hdr_sha,
            "matches_pin": True,
        })
    return records


# --------------------------------------------------------------------------
# Scanner header (allowlist only)
# --------------------------------------------------------------------------
_NUMBER = re.compile(r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)")


def _sub(a, b):
    return [x - y for x, y in zip(a, b)]


def _norm(a):
    return math.sqrt(sum(x * x for x in a))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _axis_label(vec):
    names = (("R", "L"), ("A", "P"), ("S", "I"))
    i = max(range(3), key=lambda k: abs(vec[k]))
    return names[i][0 if vec[i] > 0 else 1]


def parse_scanner_header(raw):
    """Return plane geometry from allowlisted numeric fields only."""
    if not isinstance(raw, (bytes, str)):
        raise ValueError("invalid header input")
    blob = raw.encode("utf-8") if isinstance(raw, str) else raw
    if len(blob) > MAX_HEADER_BYTES:
        raise ValueError("scanner header too large")
    vals = {}
    for line in blob.decode("utf-8", "replace").splitlines():
        if ":" not in line:
            continue
        head, rest = line.split(":", 1)
        key = re.sub(r"\.{2,}", "", head).strip()
        alias = HEADER_KEYS.get(key)
        if alias is None:
            continue
        if alias in vals:
            raise ValueError("duplicate registered scanner geometry field")
        m = _NUMBER.match(rest)
        if not m:
            raise ValueError("invalid registered scanner geometry scalar")
        v = float(m.group(1))
        if not math.isfinite(v):
            raise ValueError("nonfinite registered scanner geometry scalar")
        if alias in INTEGER_FIELDS:
            if v != int(v):
                raise ValueError("noninteger scanner pixel dimensions")
            v = int(v)
        vals[alias] = v
    if set(vals) != set(HEADER_KEYS.values()):
        raise ValueError("required scanner geometry fields absent")
    if vals["width_pixels"] != GRID or vals["height_pixels"] != GRID:
        raise ValueError("unexpected image matrix size")
    sx, sy = vals["pixel_spacing_x_mm"], vals["pixel_spacing_y_mm"]
    if (abs(sx - EXPECTED_PIXEL_SPACING_MM) > SPACING_TOL
            or abs(sy - EXPECTED_PIXEL_SPACING_MM) > SPACING_TOL):
        raise ValueError("pixel spacing is not the pinned 0.898438 mm")
    if (abs(vals["slice_thickness_mm"] - EXPECTED_THICKNESS_MM) > SPACING_TOL
            or abs(vals["series_nominal_slice_spacing_mm"] - EXPECTED_THICKNESS_MM) > SPACING_TOL):
        raise ValueError("slice thickness/spacing is not the pinned 3 mm")

    def pt(tag):
        return [vals[f"R_{tag}_mm"], vals[f"A_{tag}_mm"], vals[f"S_{tag}_mm"]]

    tl, tr, br = pt("TL"), pt("TR"), pt("BR")
    dx, dy = _sub(tr, tl), _sub(br, tr)
    lenx, leny = _norm(dx), _norm(dy)
    if abs(lenx - GRID * sx) > 0.01 or abs(leny - GRID * sy) > 0.01:
        raise ValueError("scanner corners inconsistent with pixel spacing")
    if abs(_dot(dx, dy)) > 0.001 * lenx * leny:
        raise ValueError("scanner image axes are not orthogonal")
    normal = [vals["normal_R"], vals["normal_A"], vals["normal_S"]]
    if not 0.99 < _norm(normal) < 1.01:
        raise ValueError("scanner normal has wrong magnitude")
    if abs(vals["image_location_mm"] - vals["scanner_S_centre_mm"]) > 0.01:
        raise ValueError("image location and plane-centre S differ")
    if abs(tl[2] - vals["scanner_S_centre_mm"]) > 0.01 or abs(tr[2] - tl[2]) > 0.01 \
            or abs(br[2] - tr[2]) > 0.01:
        raise ValueError("slice is not axial in scanner S")
    u = [v / lenx for v in dx]          # increasing column
    v_ = [v / leny for v in dy]         # increasing row
    n_uv = _cross(u, v_)
    agreement = _dot(n_uv, normal)
    if abs(agreement) < 0.999:
        raise ValueError("header normal disagrees with the corner-derived normal")
    return {
        "kind": "CLAUDE_CT_WINDOW_SCANNER_GEOMETRY_ALLOWLISTED_FIELDS_ONLY",
        "scanner_frame": "GE_RAS_MM_NOT_HOMEGYMPT_WORLD",
        "image_dimensions": [GRID, GRID],
        "pixel_spacing_mm": [sx, sy],
        "slice_thickness_mm": vals["slice_thickness_mm"],
        "scanner_S_mm": vals["image_location_mm"],
        "plane_TL_RAS_mm": tl,
        "plane_TR_RAS_mm": tr,
        "plane_BR_RAS_mm": br,
        "plane_BL_RAS_mm": [tl[i] + (br[i] - tr[i]) for i in range(3)],
        "column_direction_RAS": u,
        "row_direction_RAS": v_,
        "header_normal_RAS": normal,
        "corner_derived_normal_RAS": n_uv,
        "header_normal_sign_vs_u_cross_v": 1 if agreement > 0 else -1,
        "increasing_column_points_toward_scanner_axis": _axis_label(u),
        "increasing_row_points_toward_scanner_axis": _axis_label(v_),
        "patient_identifiers_excluded_by_allowlist": True,
    }


def check_contiguity(geoms):
    """Adjacent frames must share a grid and step exactly 3 mm in scanner S."""
    for a, b in zip(geoms, geoms[1:]):
        for k in ("plane_TL_RAS_mm", "plane_TR_RAS_mm", "plane_BR_RAS_mm"):
            if any(abs(a[k][i] - b[k][i]) > 0.01 for i in (0, 1)):
                raise ValueError("in-plane corner grid changes between adjacent frames")
        if abs(abs(a["scanner_S_mm"] - b["scanner_S_mm"]) - EXPECTED_THICKNESS_MM) > 0.01:
            raise ValueError("frames are not 3 mm contiguous in scanner S")
    return True


# --------------------------------------------------------------------------
# Pixel -> scanner RAS with an explicit uncertainty envelope
# --------------------------------------------------------------------------
def pixel_to_scanner_ras(geom, row, col, convention="outer_edge", picking_px=2.0):
    """Candidate scanner-RAS centre of image pixel (row, col) plus envelope.

    The headline point uses one named convention; the alternative convention is
    always returned too, so the 0.5-pixel origin ambiguity stays visible.  The
    bounds are conservative linear sums, not a statistical confidence interval.
    """
    if convention not in CONVENTIONS:
        raise ValueError("unknown pixel-origin convention")
    if type(row) is not int or type(col) is not int \
            or not 0 <= row < GRID or not 0 <= col < GRID:
        raise ValueError("row and col must be integers 0..511")
    if not (isinstance(picking_px, (int, float)) and 0 <= picking_px <= 20):
        raise ValueError("picking_px must be between 0 and 20")
    tl = geom["plane_TL_RAS_mm"]
    cs = [c / GRID for c in _sub(geom["plane_TR_RAS_mm"], tl)]
    rs = [c / GRID for c in _sub(geom["plane_BR_RAS_mm"], geom["plane_TR_RAS_mm"])]

    def place(off):
        return [tl[i] + (col + off) * cs[i] + (row + off) * rs[i] for i in range(3)]

    centres = {"outer_edge": place(0.5), "first_pixel_centre": place(0.0)}
    step = geom["pixel_spacing_mm"][0]
    conv_mm = 0.5 * step
    cell_mm = 0.5 * step
    pick_mm = float(picking_px) * step
    in_plane = conv_mm + cell_mm + pick_mm
    s = geom["scanner_S_mm"]
    half_slab = geom["slice_thickness_mm"] / 2.0
    out = {
        "schema_version": 1,
        "kind": "CT_PIXEL_TO_SCANNER_RAS_BOUNDED_OBSERVATION",
        "pixel_row_col": [row, col],
        "convention_used_for_headline": convention,
        "candidate_centre_RAS_mm": centres[convention],
        "candidate_centre_RAS_mm_by_convention": centres,
        "uncertainty_envelope": {
            "in_plane_half_width_mm": in_plane,
            "components_mm": {"pixel_origin_convention": conv_mm,
                              "pixel_cell_half_width": cell_mm,
                              "picking_allowance": pick_mm},
            "picking_allowance_px": float(picking_px),
            "scanner_S_range_mm": [s - half_slab, s + half_slab],
            "slice_thickness_mm": geom["slice_thickness_mm"],
            "kind": "CONSERVATIVE_LINEAR_BOUND_NOT_A_CONFIDENCE_INTERVAL",
        },
    }
    out.update(FALSE_FLAGS)
    return out


def scanner_ras_to_display_m(p_mm, display_offset_m=(0.0, 0.0, 0.0)):
    """Fixed rotation (R,A,S)mm -> project axes in metres. DISPLAY ONLY."""
    return [DISPLAY_AXIS_SIGNS[i] * p_mm[i] / 1000.0 + display_offset_m[i] for i in range(3)]


def plane_corners_display_m(geom, display_offset_m=(0.0, 0.0, 0.0)):
    """TL, TR, BR, BL of the image plane in display metres (row/col order kept)."""
    return [scanner_ras_to_display_m(geom[k], display_offset_m)
            for k in ("plane_TL_RAS_mm", "plane_TR_RAS_mm",
                      "plane_BR_RAS_mm", "plane_BL_RAS_mm")]


# --------------------------------------------------------------------------
# 16-bit grayscale PNG decode and 8-bit display copy
# --------------------------------------------------------------------------
_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _chunks(data):
    if data[:8] != _PNG_SIG:
        raise ValueError("not a PNG")
    pos = 8
    while pos + 12 <= len(data):
        length, = struct.unpack(">I", data[pos:pos + 4])
        if pos + 12 + length > len(data):
            raise ValueError("PNG chunk extends past end of data")
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        crc, = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        if zlib.crc32(tag + body) & 0xFFFFFFFF != crc:
            raise ValueError("PNG chunk CRC error")
        yield tag, body
        pos += 12 + length
        if tag == b"IEND":
            return
    raise ValueError("PNG missing IEND")


def decode_png_gray16(data):
    """Return (width, height, array('H')) of 16-bit grayscale, non-interlaced."""
    if len(data) > MAX_PNG_BYTES:
        raise ValueError("PNG too large")
    ihdr = None
    idat = bytearray()
    for tag, body in _chunks(data):
        if tag == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat += body
    if ihdr is None:
        raise ValueError("PNG missing IHDR")
    w, h, depth, ctype, comp, filt, inter = ihdr
    if (depth, ctype, comp, filt, inter) != (16, 0, 0, 0, 0):
        raise ValueError("expected non-interlaced 16-bit grayscale PNG")
    if w != GRID or h != GRID:
        raise ValueError("unexpected PNG dimensions")
    stride = w * 2
    expected = (stride + 1) * h
    d = zlib.decompressobj()
    raw = d.decompress(bytes(idat), expected + 1)
    if len(raw) != expected or d.unconsumed_tail or not d.eof:
        raise ValueError("PNG IDAT size mismatch")
    out = bytearray(stride * h)
    prev = bytearray(stride)
    pos = 0
    for r in range(h):
        ft = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ft == 0:
            pass
        elif ft == 1:
            for i in range(2, stride):
                line[i] = (line[i] + line[i - 2]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                left = line[i - 2] if i >= 2 else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - 2] if i >= 2 else 0
                b = prev[i]
                c = prev[i - 2] if i >= 2 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        else:
            raise ValueError("invalid PNG filter type")
        out[r * stride:(r + 1) * stride] = line
        prev = line
    px = array("H")
    px.frombytes(bytes(out))
    if sys.byteorder == "little":
        px.byteswap()
    return w, h, px


def raw_stored_statistics(px):
    """Intensity-only summary of STORED values (explicitly not Hounsfield)."""
    s = sorted(px)
    n = len(s)
    pct = lambda q: s[min(n - 1, int(q * (n - 1)))]
    return {"min": s[0], "p1": pct(0.01), "p50": pct(0.50), "p99": pct(0.99),
            "p99_8": pct(0.998), "max": s[-1], "values_are_calibrated_HU": False}


def window_to_8bit(px, low, high):
    """Linear stored-value window [low, high] -> 0..255 (display only)."""
    if not (isinstance(low, (int, float)) and isinstance(high, (int, float))) or high <= low:
        raise ValueError("window requires high > low")
    scale = 255.0 / (high - low)
    return bytes(0 if v <= low else 255 if v >= high else int((v - low) * scale + 0.5)
                 for v in px)


def encode_png_gray8(width, height, data):
    if len(data) != width * height:
        raise ValueError("pixel buffer size mismatch")
    rows = b"".join(b"\x00" + data[r * width:(r + 1) * width] for r in range(height))

    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))

    return (_PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def write_display_copies(ct_dir, manifest, cache_dir, low=None, high=None,
                         repo_root=REPO_ROOT):
    """Validate pins, then write windowed 8-bit copies into a PRIVATE cache dir.

    If low/high are None, a per-frame percentile window (p1..p99.8 of stored
    values) is used and recorded; it is a viewing aid, not a bone threshold.
    """
    records = validate_private_inputs(ct_dir, manifest, repo_root)
    cache = assert_private_location(cache_dir, repo_root)
    cache.mkdir(parents=True, exist_ok=True)
    base = Path(ct_dir).resolve()
    result = []
    for rec in records:
        w, h, px = decode_png_gray16((base / rec["png_filename"]).read_bytes())
        stats = raw_stored_statistics(px)
        lo = stats["p1"] if low is None else low
        hi = stats["p99_8"] if high is None else high
        if hi <= lo:
            hi = lo + 1
        out_name = rec["png_filename"].replace(".png", "_display8.png")
        (cache / out_name).write_bytes(encode_png_gray8(w, h, window_to_8bit(px, lo, hi)))
        result.append({**rec, "display_filename": out_name,
                       "window_stored_low": lo, "window_stored_high": hi,
                       "raw_stored_statistics": stats})
    return result


# --------------------------------------------------------------------------
# Physical slice-to-region index
# --------------------------------------------------------------------------
def slice_index_rows(manifest):
    """One row per pinned frame, derived only from the pinned manifest."""
    pins = manifest["by_id"] if "by_id" in manifest else manifest
    rows = []
    for gi, ids in enumerate(TRIPLETS):
        for sid in ids:
            s = pins[sid]["scanner_S_mm"]
            rows.append({
                "window": "A" if gi == 0 else "B",
                "source_id": sid,
                "png_filename": frame_name(sid, "png"),
                "png_sha256": pins[sid]["png_sha256"],
                "header_sha256": pins[sid]["scanner_header_sha256"],
                "scanner_S_mm": s,
                "slab_S_range_mm": [s - 1.5, s + 1.5],
                "pixel_spacing_mm": EXPECTED_PIXEL_SPACING_MM,
                "slice_thickness_mm": EXPECTED_THICKNESS_MM,
                "region_status": "UNVERIFIED",
            })
    return rows


def window_gap_mm(manifest):
    """Uncovered physical gap between window A (upper) and window B (lower)."""
    pins = manifest["by_id"] if "by_id" in manifest else manifest
    a_low = pins[TRIPLETS[0][-1]]["scanner_S_mm"] - 1.5
    b_high = pins[TRIPLETS[1][0]]["scanner_S_mm"] + 1.5
    return a_low - b_high


def required_contiguous_range(z_values_mm, margin_mm=6.0, step_mm=EXPECTED_THICKNESS_MM):
    """Contiguous 3 mm run needed to bracket reviewer-identified landmark levels.

    `z_values_mm` are scanner S levels a human has identified (e.g. iliac crest
    top, ischial tuberosity bottom).  Returns the S range, slice count and the
    S of each requested frame centre, snapped to the pinned 3 mm lattice.
    """
    zs = [float(z) for z in z_values_mm]
    if len(zs) < 2 or margin_mm < 0:
        raise ValueError("need at least two landmark levels and a non-negative margin")
    lo, hi = min(zs) - margin_mm, max(zs) + margin_mm
    anchor = -360.0                       # a pinned frame centre defines the lattice
    first = anchor + step_mm * math.floor((lo - anchor) / step_mm)
    last = anchor + step_mm * math.ceil((hi - anchor) / step_mm)
    n = int(round((last - first) / step_mm)) + 1
    return {"requested_S_range_mm": [lo, hi],
            "frame_centres_S_mm": [first + step_mm * k for k in range(n)],
            "frame_count": n, "slice_step_mm": step_mm,
            "lattice_anchor_frame_S_mm": anchor}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _cli(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="hash private PNG/header files against the pins")
    v.add_argument("--ct-dir", required=True, type=Path)
    v.add_argument("--manifest", required=True, type=Path)
    d = sub.add_parser("derive-display", help="write windowed 8-bit copies to a private dir")
    d.add_argument("--ct-dir", required=True, type=Path)
    d.add_argument("--manifest", required=True, type=Path)
    d.add_argument("--cache-dir", required=True, type=Path)
    d.add_argument("--window-low", type=int)
    d.add_argument("--window-high", type=int)
    q = sub.add_parser("place", help="map a reviewed (row, col) to scanner RAS")
    q.add_argument("--ct-dir", required=True, type=Path)
    q.add_argument("--manifest", required=True, type=Path)
    q.add_argument("--source-id", required=True, type=int, choices=ALL_IDS)
    q.add_argument("--row", required=True, type=int)
    q.add_argument("--col", required=True, type=int)
    q.add_argument("--convention", choices=CONVENTIONS, default="outer_edge")
    q.add_argument("--picking-px", type=float, default=2.0)
    a = p.parse_args(argv)
    manifest = load_pinned_manifest(a.manifest)
    if a.cmd == "validate":
        out = {"status": "ALL_SIX_PNG_AND_HEADER_SHA256_MATCH_PINS",
               "frames": validate_private_inputs(a.ct_dir, manifest)}
    elif a.cmd == "derive-display":
        out = {"frames": write_display_copies(a.ct_dir, manifest, a.cache_dir,
                                              a.window_low, a.window_high)}
    else:
        validate_private_inputs(a.ct_dir, manifest)
        raw = (Path(a.ct_dir) / frame_name(a.source_id, "txt")).read_bytes()
        geom = parse_scanner_header(raw)
        out = pixel_to_scanner_ras(geom, a.row, a.col, a.convention, a.picking_px)
        out["source_id"] = a.source_id
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
