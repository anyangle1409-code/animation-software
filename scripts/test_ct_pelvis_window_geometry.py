"""Tests for the Claude-owned pelvic CT window geometry module.

All CT bytes here are SYNTHETIC.  No original NLM data is used or required;
the real six-frame hash manifest is only checked for structure and identity.
"""
import contextlib
import copy
import hashlib
import io
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
import ct_pelvis_window_geometry as g  # noqa: E402

AUDIT = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/claude_pelvis_ct_review_20261009"
PINNED = AUDIT / "pinned_six_frames_from_pr15_4680b49.json"
PROVENANCE = AUDIT / "PINNED_INPUTS_PROVENANCE.json"

S_BY_ID = {1749: -357, 1752: -360, 1755: -363, 1797: -405, 1800: -408, 1803: -411}
SECRET = "SECRET-DO-NOT-ECHO"


def header_text(s, spacing=0.898438, thickness=3.0, drop=None, dup=None, **override):
    """Synthetic radiological-style header: TL=(+230,+230), TR=(-230,+230), BR=(-230,-230)."""
    v = {
        "width_pixels": 512, "height_pixels": 512,
        "pixel_spacing_x_mm": spacing, "pixel_spacing_y_mm": spacing,
        "slice_thickness_mm": thickness, "series_nominal_slice_spacing_mm": thickness,
        "image_location_mm": s, "scanner_R_centre_mm": 0.0, "scanner_A_centre_mm": 0.0,
        "scanner_S_centre_mm": s,
        "R_TL_mm": 230.0, "A_TL_mm": 230.0, "S_TL_mm": s,
        "R_TR_mm": -230.0, "A_TR_mm": 230.0, "S_TR_mm": s,
        "R_BR_mm": -230.0, "A_BR_mm": -230.0, "S_BR_mm": s,
        "normal_R": 0.0, "normal_A": 0.0, "normal_S": 1.0,
    }
    v.update(override)
    text = "Reading file: /redacted\n"
    text += f"Patient ID............................: {SECRET}\n"
    text += f"Patient Name..........................: {SECRET}-NAME\n"
    for key, alias in g.HEADER_KEYS.items():
        if alias == drop:
            continue
        text += key + "." * max(2, 44 - len(key)) + f": {v[alias]}\n"
        if alias == dup:
            text += key + "." * max(2, 44 - len(key)) + f": {v[alias]}\n"
    return text


# ---- independent reference PNG encoder (forward filters, per the PNG spec) ----
def png_chunk(tag, body):
    return (struct.pack(">I", len(body)) + tag + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF))


def reference_png16(pixels, w=512, h=512, filters=(0, 1, 2, 3, 4)):
    stride = w * 2
    rows = []
    for r in range(h):
        row = b"".join(struct.pack(">H", pixels[r * w + c]) for c in range(w))
        rows.append(row)
    out = bytearray()
    prev = bytes(stride)
    for r, row in enumerate(rows):
        ft = filters[r % len(filters)]
        out.append(ft)
        for i in range(stride):
            a = row[i - 2] if i >= 2 else 0
            b = prev[i]
            c = prev[i - 2] if i >= 2 else 0
            if ft == 0:
                pred = 0
            elif ft == 1:
                pred = a
            elif ft == 2:
                pred = b
            elif ft == 3:
                pred = (a + b) // 2
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            out.append((row[i] - pred) & 255)
        prev = row
    return (g._PNG_SIG + png_chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 16, 0, 0, 0, 0))
            + png_chunk(b"IDAT", zlib.compress(bytes(out), 6)) + png_chunk(b"IEND", b""))


def pattern(seed=0):
    px = []
    for i in range(512 * 512):
        px.append((i * 2654435761 + seed * 40503) % 65536)
    px[0], px[1], px[-1] = 0, 65535, 65535
    return px


_PNG_CACHE = {}


def cached_png(k, filters):
    """Encoding 512x512 PNGs in pure Python is slow; reuse them across tests."""
    key = (k, filters)
    if key not in _PNG_CACHE:
        _PNG_CACHE[key] = reference_png16(pattern(k), filters=filters)
    return _PNG_CACHE[key]


def make_private_dir(parent, filters=(0,)):
    """Synthetic six-frame private dir + a manifest whose pins match it.

    Filter type 0 keeps the pipeline tests fast; every filter type is exercised
    separately by PngAndDisplay.test_decoder_matches_independent_encoder_for_every_filter.
    """
    d = Path(parent) / "ct"
    d.mkdir()
    manifest = json.loads(PINNED.read_text())
    rows = []
    for k, sid in enumerate(g.ALL_IDS):
        png = cached_png(k, filters)
        hdr = header_text(S_BY_ID[sid]).encode()
        (d / g.frame_name(sid, "png")).write_bytes(png)
        (d / g.frame_name(sid, "txt")).write_bytes(hdr)
        rows.append({"source_id": sid, "scanner_S_mm": S_BY_ID[sid],
                     "png_sha256": hashlib.sha256(png).hexdigest(),
                     "scanner_header_sha256": hashlib.sha256(hdr).hexdigest(),
                     "png_bytes": len(png)})
    manifest["exact_png_and_scanner_header_sha256"] = rows
    return d, manifest


class RealPinnedManifest(unittest.TestCase):
    def test_copy_is_the_recorded_byte_identical_upstream_blob(self):
        prov = json.loads(PROVENANCE.read_text())
        data = PINNED.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), prov["copy_sha256"])
        blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        self.assertEqual(blob, prov["copy_git_blob"])
        self.assertEqual(blob, prov["upstream"]["git_blob"])
        self.assertFalse(prov["claude_session_reproduced_source_hashes"])
        self.assertFalse(prov["canonical_promotion_allowed"])

    def test_loads_and_covers_exact_six_frames_and_levels(self):
        m = g.load_pinned_manifest(PINNED)
        self.assertEqual(sorted(m["by_id"]), sorted(S_BY_ID))
        for sid, s in S_BY_ID.items():
            self.assertEqual(m["by_id"][sid]["scanner_S_mm"], s)

    def test_all_anatomy_and_promotion_flags_false_in_the_pin(self):
        raw = json.loads(PINNED.read_text())
        for flag in ("anatomical_features_identified", "canonical_promotion_allowed",
                     "patient_scanner_to_HGPT_world_verified",
                     "source_CT_HU_calibration_verified",
                     "source_segmented_bone_surfaces_verified"):
            self.assertIs(raw[flag], False, flag)

    def test_rejects_manifests_that_overclaim_or_drift(self):
        raw = json.loads(PINNED.read_text())
        for mutate, why in [
            (lambda m: m.update(anatomical_features_identified=True), "anatomy flag"),
            (lambda m: m.update(canonical_promotion_allowed=True), "promotion flag"),
            (lambda m: m.update(source_CT_HU_calibration_verified=True), "HU flag"),
            (lambda m: m.update(slice_thickness_mm=1), "thickness"),
            (lambda m: m.update(pixel_spacing_xy_mm=[0.488281, 0.488281]), "spacing"),
            (lambda m: m["exact_png_and_scanner_header_sha256"].pop(), "five rows"),
            (lambda m: m["exact_png_and_scanner_header_sha256"][0].update(source_id=1752), "dup id"),
            (lambda m: m["exact_png_and_scanner_header_sha256"][0].update(png_sha256="XYZ"), "bad hex"),
            (lambda m: m["exact_png_and_scanner_header_sha256"][0].update(png_sha256="A" * 64), "upper hex"),
            (lambda m: m["groups"][0]["scanner_S_mm"].__setitem__(1, -361), "window S"),
            (lambda m: m["exact_png_and_scanner_header_sha256"][1].update(scanner_S_mm=-359), "row S"),
        ]:
            m = copy.deepcopy(raw)
            mutate(m)
            with self.assertRaises(g.PinError, msg=why):
                g.load_pinned_manifest(m)


class PrivateInputValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ctpriv_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_matching_files_validate(self):
        d, m = make_private_dir(self.tmp)
        recs = g.validate_private_inputs(d, g.load_pinned_manifest(m))
        self.assertEqual([r["source_id"] for r in recs], list(g.ALL_IDS))
        self.assertTrue(all(r["matches_pin"] for r in recs))

    def test_one_flipped_png_byte_fails_closed(self):
        d, m = make_private_dir(self.tmp)
        p = d / "cvm1800f.png"
        b = bytearray(p.read_bytes())
        b[len(b) // 2] ^= 1
        p.write_bytes(bytes(b))
        with self.assertRaisesRegex(g.PinError, "cvm1800f.png: SHA-256 differs"):
            g.validate_private_inputs(d, g.load_pinned_manifest(m))

    def test_changed_header_fails_closed_without_echoing_content(self):
        d, m = make_private_dir(self.tmp)
        (d / "cvm1752f.txt").write_bytes((header_text(-360) + "tampered\n").encode())
        with self.assertRaises(g.PinError) as cm:
            g.validate_private_inputs(d, g.load_pinned_manifest(m))
        self.assertIn("cvm1752f.txt", str(cm.exception))
        self.assertNotIn(SECRET, str(cm.exception))

    def test_missing_file_and_wrong_size_and_symlink_fail(self):
        d, m = make_private_dir(self.tmp)
        manifest = g.load_pinned_manifest(m)
        (d / "cvm1749f.png").unlink()
        with self.assertRaises(g.PinError):
            g.validate_private_inputs(d, manifest)
        d2 = Path(self.tmp) / "ct2"
        d2.mkdir()
        shutil.copytree(d, d2, dirs_exist_ok=True)
        real, link = d / "cvm1752f.png", d2 / "cvm1749f.png"
        link.symlink_to(real)
        with self.assertRaisesRegex(g.PinError, "not a regular file"):
            g.validate_private_inputs(d2, manifest)

    def test_png_byte_count_pin_enforced(self):
        d, m = make_private_dir(self.tmp)
        m["exact_png_and_scanner_header_sha256"][0]["png_bytes"] += 1
        with self.assertRaisesRegex(g.PinError, "byte count"):
            g.validate_private_inputs(d, g.load_pinned_manifest(m))

    def test_paths_inside_the_repository_are_refused(self):
        with self.assertRaisesRegex(g.PinError, "outside the repository"):
            g.assert_private_location(ROOT / "scratch_ct")
        with self.assertRaisesRegex(g.PinError, "outside the repository"):
            g.assert_private_location(ROOT)
        self.assertTrue(g.assert_private_location(self.tmp))


class HeaderParsing(unittest.TestCase):
    def test_extracts_plane_and_never_returns_patient_fields(self):
        geom = g.parse_scanner_header(header_text(-360))
        self.assertEqual(geom["plane_TL_RAS_mm"], [230.0, 230.0, -360])
        self.assertEqual(geom["plane_BL_RAS_mm"], [230.0, -230.0, -360])
        self.assertEqual(geom["scanner_S_mm"], -360)
        self.assertNotIn(SECRET, json.dumps(geom))
        self.assertTrue(geom["patient_identifiers_excluded_by_allowlist"])

    def test_orientation_is_derived_from_corners_not_assumed(self):
        geom = g.parse_scanner_header(header_text(-360))
        self.assertEqual(geom["column_direction_RAS"], [-1.0, 0.0, 0.0])
        self.assertEqual(geom["row_direction_RAS"], [0.0, -1.0, 0.0])
        self.assertEqual(geom["increasing_column_points_toward_scanner_axis"], "L")
        self.assertEqual(geom["increasing_row_points_toward_scanner_axis"], "P")
        self.assertEqual(geom["header_normal_sign_vs_u_cross_v"], 1)
        flipped = header_text(-360, R_TL_mm=-230.0, R_TR_mm=230.0, R_BR_mm=230.0)
        gf = g.parse_scanner_header(flipped)
        self.assertEqual(gf["increasing_column_points_toward_scanner_axis"], "R")
        self.assertEqual(gf["header_normal_sign_vs_u_cross_v"], -1)

    def test_rejects_wrong_grid_spacing_thickness_and_structure(self):
        cases = [
            (dict(spacing=0.488281), "spacing"),
            (dict(thickness=1.0), "thickness"),
            (dict(width_pixels=256), "matrix"),
            (dict(drop="normal_S"), "absent"),
            (dict(dup="R_TL_mm"), "duplicate"),
            (dict(S_TR_mm=-359.0), "axial"),
            (dict(image_location_mm=-357.0), "location"),
            (dict(normal_S=-1.0, normal_A=0.5), "normal"),
            (dict(R_BR_mm=-200.0), "corners"),
            (dict(A_BR_mm=-100.0), "corners|orthogonal"),
        ]
        for kw, why in cases:
            with self.assertRaises(ValueError, msg=why):
                g.parse_scanner_header(header_text(-360, **kw))

    def test_nonfinite_and_garbage_values_rejected(self):
        for bad in ("nan", "inf", "abc", "1e999", "--5"):
            with self.assertRaises(ValueError, msg=bad):
                g.parse_scanner_header(header_text(-360, normal_S=bad))

    def test_oversized_and_wrong_type_input_rejected(self):
        with self.assertRaises(ValueError):
            g.parse_scanner_header(b"x" * (g.MAX_HEADER_BYTES + 1))
        with self.assertRaises(ValueError):
            g.parse_scanner_header(123)

    def test_three_mm_contiguity_enforced(self):
        a, b, c = (g.parse_scanner_header(header_text(s)) for s in (-357, -360, -363))
        self.assertTrue(g.check_contiguity([a, b, c]))
        far = g.parse_scanner_header(header_text(-366))
        with self.assertRaisesRegex(ValueError, "3 mm contiguous"):
            g.check_contiguity([a, far])
        shifted = g.parse_scanner_header(header_text(-360, R_TL_mm=231.0, R_TR_mm=-229.0,
                                                     R_BR_mm=-229.0))
        with self.assertRaisesRegex(ValueError, "corner grid"):
            g.check_contiguity([a, shifted])


class PixelToScannerRas(unittest.TestCase):
    def setUp(self):
        self.geom = g.parse_scanner_header(header_text(-360))
        self.step = 460.0 / 512  # exact corner-derived step, 0.8984375

    def test_known_corner_pixels_under_both_conventions(self):
        r = g.pixel_to_scanner_ras(self.geom, 0, 0)
        c = r["candidate_centre_RAS_mm_by_convention"]
        self.assertAlmostEqual(c["first_pixel_centre"][0], 230.0)
        self.assertAlmostEqual(c["first_pixel_centre"][1], 230.0)
        self.assertAlmostEqual(c["outer_edge"][0], 230.0 - self.step / 2)
        self.assertAlmostEqual(c["outer_edge"][1], 230.0 - self.step / 2)
        self.assertEqual(c["outer_edge"][2], -360)
        last = g.pixel_to_scanner_ras(self.geom, 511, 511)["candidate_centre_RAS_mm_by_convention"]
        self.assertAlmostEqual(last["outer_edge"][0], 230.0 - 511.5 * self.step)
        self.assertAlmostEqual(last["first_pixel_centre"][1], 230.0 - 511 * self.step)

    def test_row_and_column_map_to_distinct_axes(self):
        r0 = g.pixel_to_scanner_ras(self.geom, 100, 100)["candidate_centre_RAS_mm"]
        rc = g.pixel_to_scanner_ras(self.geom, 100, 101)["candidate_centre_RAS_mm"]
        rr = g.pixel_to_scanner_ras(self.geom, 101, 100)["candidate_centre_RAS_mm"]
        self.assertAlmostEqual(rc[0] - r0[0], -self.step)
        self.assertAlmostEqual(rc[1] - r0[1], 0)
        self.assertAlmostEqual(rr[1] - r0[1], -self.step)
        self.assertAlmostEqual(rr[0] - r0[0], 0)

    def test_conventions_differ_by_exactly_half_a_pixel(self):
        c = g.pixel_to_scanner_ras(self.geom, 200, 300)["candidate_centre_RAS_mm_by_convention"]
        d = [a - b for a, b in zip(c["outer_edge"], c["first_pixel_centre"])]
        self.assertAlmostEqual(d[0], -self.step / 2)
        self.assertAlmostEqual(d[1], -self.step / 2)
        self.assertEqual(d[2], 0)

    def test_envelope_components_slab_and_false_flags(self):
        r = g.pixel_to_scanner_ras(self.geom, 10, 10, picking_px=2.0)
        e = r["uncertainty_envelope"]
        spacing = 0.898438
        self.assertAlmostEqual(e["components_mm"]["pixel_origin_convention"], spacing / 2)
        self.assertAlmostEqual(e["components_mm"]["pixel_cell_half_width"], spacing / 2)
        self.assertAlmostEqual(e["components_mm"]["picking_allowance"], 2 * spacing)
        self.assertAlmostEqual(e["in_plane_half_width_mm"], 3 * spacing)
        self.assertEqual(e["scanner_S_range_mm"], [-361.5, -358.5])
        self.assertEqual(e["slice_thickness_mm"], 3.0)
        self.assertIn("NOT_A_CONFIDENCE_INTERVAL", e["kind"])
        for flag, value in g.FALSE_FLAGS.items():
            self.assertIs(r[flag], value, flag)
        self.assertFalse(any(r[f] for f in g.FALSE_FLAGS))

    def test_translation_invariance(self):
        shifted = g.parse_scanner_header(header_text(
            -360, R_TL_mm=240.0, R_TR_mm=-220.0, R_BR_mm=-220.0,
            A_TL_mm=215.0, A_TR_mm=215.0, A_BR_mm=-245.0,
            scanner_R_centre_mm=10.0, scanner_A_centre_mm=-15.0))
        a = g.pixel_to_scanner_ras(self.geom, 77, 33)["candidate_centre_RAS_mm"]
        b = g.pixel_to_scanner_ras(shifted, 77, 33)["candidate_centre_RAS_mm"]
        self.assertAlmostEqual(b[0] - a[0], 10.0)
        self.assertAlmostEqual(b[1] - a[1], -15.0)
        self.assertAlmostEqual(b[2] - a[2], 0.0)

    def test_invalid_indices_and_conventions_rejected(self):
        for row, col in [(-1, 0), (0, 512), (512, 0), (1.0, 3), (True, 3), ("1", 2)]:
            with self.assertRaises(ValueError, msg=(row, col)):
                g.pixel_to_scanner_ras(self.geom, row, col)
        with self.assertRaises(ValueError):
            g.pixel_to_scanner_ras(self.geom, 1, 1, convention="centre")
        with self.assertRaises(ValueError):
            g.pixel_to_scanner_ras(self.geom, 1, 1, picking_px=-1)
        with self.assertRaises(ValueError):
            g.pixel_to_scanner_ras(self.geom, 1, 1, picking_px=50)

    def test_display_mapping_is_a_proper_rotation_and_preserves_winding(self):
        sx, sy, sz = g.DISPLAY_AXIS_SIGNS
        self.assertEqual(sx * sy * sz, 1.0)
        p = g.scanner_ras_to_display_m([100.0, 50.0, -360.0], (0.3, 0.0, 0.0))
        self.assertAlmostEqual(p[0], -0.1 + 0.3)
        self.assertAlmostEqual(p[1], -0.05)
        self.assertAlmostEqual(p[2], -0.36)
        tl, tr, br, bl = g.plane_corners_display_m(self.geom)
        u = [b - a for a, b in zip(tl, tr)]
        v = [b - a for a, b in zip(tr, br)]
        n = g._cross(u, v)
        self.assertGreater(n[2], 0)                  # scanner +S stays +Z
        self.assertAlmostEqual(math.hypot(*u[:2]), 0.46, places=4)
        for a, b in zip(bl, [tl[i] + br[i] - tr[i] for i in range(3)]):
            self.assertAlmostEqual(a, b)


class PngAndDisplay(unittest.TestCase):
    def test_decoder_matches_independent_encoder_for_every_filter(self):
        px = pattern(3)
        for filters in [(0,), (1,), (2,), (3,), (4,), (0, 1, 2, 3, 4), (4, 3, 2, 1, 0)]:
            w, h, out = g.decode_png_gray16(reference_png16(px, filters=filters))
            self.assertEqual((w, h), (512, 512))
            self.assertEqual(list(out), px, filters)

    def test_extremes_survive_roundtrip(self):
        px = [0, 65535] * (512 * 256)
        self.assertEqual(list(g.decode_png_gray16(reference_png16(px))[2]), px)

    def test_rejects_corruption_and_wrong_formats(self):
        good = reference_png16(pattern(1))
        bad_crc = bytearray(good)
        bad_crc[40] ^= 0xFF
        with self.assertRaises(ValueError):
            g.decode_png_gray16(bytes(bad_crc))
        for cut in (0, 7, 9, 20, 33, 40, 100, 5000, len(good) - 20, len(good) - 13, len(good) - 1):
            with self.assertRaises(ValueError, msg=f"truncated at {cut}"):
                g.decode_png_gray16(good[:cut])
        with self.assertRaises(ValueError):
            g.decode_png_gray16(b"not a png at all")
        eight = (g._PNG_SIG + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 512, 512, 8, 0, 0, 0, 0))
                 + png_chunk(b"IDAT", zlib.compress(bytes(513 * 512))) + png_chunk(b"IEND", b""))
        with self.assertRaises(ValueError):
            g.decode_png_gray16(eight)
        small = (g._PNG_SIG + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 16, 0, 0, 0, 0))
                 + png_chunk(b"IDAT", zlib.compress(bytes(129 * 64))) + png_chunk(b"IEND", b""))
        with self.assertRaises(ValueError):
            g.decode_png_gray16(small)

    def test_oversize_decompression_is_rejected(self):
        bomb = (g._PNG_SIG + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 512, 512, 16, 0, 0, 0, 0))
                + png_chunk(b"IDAT", zlib.compress(bytes(1025 * 512 * 4), 9))
                + png_chunk(b"IEND", b""))
        with self.assertRaisesRegex(ValueError, "IDAT size mismatch"):
            g.decode_png_gray16(bomb)

    def test_window_and_8bit_writer(self):
        px = [0, 1000, 1500, 2000, 65535]
        self.assertEqual(list(g.window_to_8bit(px, 1000, 2000)), [0, 0, 128, 255, 255])
        with self.assertRaises(ValueError):
            g.window_to_8bit(px, 5, 5)
        data = bytes(range(256)) * 1024
        png = g.encode_png_gray8(512, 512, data)
        chunks = dict((t, b) for t, b in g._chunks(png))
        raw = zlib.decompress(chunks[b"IDAT"])
        self.assertEqual(struct.unpack(">IIBBBBB", chunks[b"IHDR"]), (512, 512, 8, 0, 0, 0, 0))
        self.assertEqual(b"".join(raw[1 + r * 513:(r + 1) * 513] for r in range(512)), data)
        with self.assertRaises(ValueError):
            g.encode_png_gray8(512, 512, b"short")

    def test_raw_statistics_never_claim_hounsfield(self):
        s = g.raw_stored_statistics(array_of([5, 1, 9, 3, 7]))
        self.assertEqual((s["min"], s["max"]), (1, 9))
        self.assertIs(s["values_are_calibrated_HU"], False)


def array_of(vals):
    from array import array
    return array("H", vals)


class DisplayCopies(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ctpriv_")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_writes_private_display_copies_and_leaves_sources_untouched(self):
        d, m = make_private_dir(self.tmp)
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in d.iterdir()}
        cache = Path(self.tmp) / "cache"
        out = g.write_display_copies(d, g.load_pinned_manifest(m), cache, 1000, 50000)
        self.assertEqual(len(out), 6)
        for rec in out:
            f = cache / rec["display_filename"]
            self.assertTrue(f.is_file())
            self.assertEqual((rec["window_stored_low"], rec["window_stored_high"]), (1000, 50000))
            self.assertFalse(rec["raw_stored_statistics"]["values_are_calibrated_HU"])
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in d.iterdir()}
        self.assertEqual(before, after)

    def test_display_pixels_follow_the_stored_values(self):
        d, m = make_private_dir(self.tmp)
        cache = Path(self.tmp) / "cache"
        g.write_display_copies(d, g.load_pinned_manifest(m), cache, 1000, 50000)
        k = list(g.ALL_IDS).index(1749)
        src = pattern(k)
        png = (cache / "cvm1749f_display8.png").read_bytes()
        raw = zlib.decompress(dict(g._chunks(png))[b"IDAT"])
        got = b"".join(raw[1 + r * 513:(r + 1) * 513] for r in range(512))
        self.assertEqual(got, g.window_to_8bit(src, 1000, 50000))

    def test_cache_inside_repository_and_bad_pins_refused(self):
        d, m = make_private_dir(self.tmp)
        manifest = g.load_pinned_manifest(m)
        with self.assertRaisesRegex(g.PinError, "outside the repository"):
            g.write_display_copies(d, manifest, ROOT / "display_cache")
        self.assertFalse((ROOT / "display_cache").exists())
        (d / "cvm1803f.png").write_bytes(b"corrupt")
        cache = Path(self.tmp) / "cache2"
        with self.assertRaises(g.PinError):
            g.write_display_copies(d, manifest, cache)
        self.assertFalse(cache.exists())


class SliceIndexAndRanges(unittest.TestCase):
    def setUp(self):
        self.m = g.load_pinned_manifest(PINNED)

    def test_index_rows_are_derived_from_pins_and_all_unverified(self):
        rows = g.slice_index_rows(self.m)
        self.assertEqual([r["source_id"] for r in rows], list(g.ALL_IDS))
        self.assertEqual({r["region_status"] for r in rows}, {"UNVERIFIED"})
        r = rows[1]
        self.assertEqual((r["png_filename"], r["scanner_S_mm"]), ("cvm1752f.png", -360))
        self.assertEqual(r["slab_S_range_mm"], [-361.5, -358.5])

    def test_gap_between_windows_is_thirty_nine_mm(self):
        self.assertAlmostEqual(g.window_gap_mm(self.m), 39.0)

    def test_both_windows_sit_on_one_three_mm_lattice(self):
        for s in S_BY_ID.values():
            self.assertEqual((s + 360) % 3, 0)

    def test_required_range_snaps_to_the_lattice_and_counts_frames(self):
        r = g.required_contiguous_range([-390.0, -372.0], margin_mm=6.0)
        self.assertEqual(r["requested_S_range_mm"], [-396.0, -366.0])
        self.assertEqual(r["frame_centres_S_mm"][0], -396.0)
        self.assertEqual(r["frame_centres_S_mm"][-1], -366.0)
        self.assertEqual(r["frame_count"], 11)
        for s in r["frame_centres_S_mm"]:
            self.assertEqual((s + 360) % 3, 0)
        r2 = g.required_contiguous_range([-401.0, -372.5], margin_mm=0.0)
        self.assertEqual(r2["frame_centres_S_mm"][0], -402.0)
        self.assertEqual(r2["frame_centres_S_mm"][-1], -372.0)
        with self.assertRaises(ValueError):
            g.required_contiguous_range([-390.0])
        with self.assertRaises(ValueError):
            g.required_contiguous_range([-390.0, -380.0], margin_mm=-1)


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ctpriv_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.d, m = make_private_dir(self.tmp)
        self.manifest_path = Path(self.tmp) / "pins.json"
        self.manifest_path.write_text(json.dumps(m))

    def run_cli(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = g._cli(list(args))
        return code, buf.getvalue()

    def test_validate_prints_hashes_only(self):
        code, out = self.run_cli("validate", "--ct-dir", str(self.d),
                                 "--manifest", str(self.manifest_path))
        self.assertEqual(code, 0)
        self.assertIn("ALL_SIX_PNG_AND_HEADER_SHA256_MATCH_PINS", out)
        self.assertNotIn(SECRET, out)
        self.assertEqual(len(json.loads(out)["frames"]), 6)

    def test_place_validates_first_then_reports_envelope(self):
        code, out = self.run_cli("place", "--ct-dir", str(self.d),
                                 "--manifest", str(self.manifest_path),
                                 "--source-id", "1752", "--row", "256", "--col", "128")
        res = json.loads(out)
        self.assertEqual(res["source_id"], 1752)
        self.assertEqual(res["uncertainty_envelope"]["scanner_S_range_mm"], [-361.5, -358.5])
        self.assertFalse(res["anatomical_region_identified"])
        self.assertNotIn(SECRET, out)

    def test_place_on_tampered_source_fails_before_any_coordinate(self):
        p = self.d / "cvm1752f.txt"
        p.write_bytes(p.read_bytes() + b"x")
        with self.assertRaises(g.PinError):
            self.run_cli("place", "--ct-dir", str(self.d), "--manifest",
                         str(self.manifest_path), "--source-id", "1752", "--row", "1", "--col", "1")

    def test_cli_refuses_repo_internal_ct_dir(self):
        with self.assertRaises(g.PinError):
            self.run_cli("validate", "--ct-dir", str(ROOT / "ORIGINAL_V1_WORK"),
                         "--manifest", str(self.manifest_path))


if __name__ == "__main__":
    unittest.main()
