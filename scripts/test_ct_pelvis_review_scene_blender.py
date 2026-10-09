"""Contract tests for the Blender scene-setup script using a FAKE bpy.

The fake models only the API surface the script uses.  These tests prove the
script's logic (plan, orientation, non-destruction guard, no packing, create-only
outputs, fail-closed pins) but NOT Blender's own behaviour: a real Blender run
is a separate, documented laptop check.  All CT data here is synthetic.
"""
import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE / "anatomy_fit"))
sys.path.insert(0, str(HERE))
import ct_pelvis_window_geometry as geo  # noqa: E402
import ct_pelvis_skeleton_vs_source_report as skel  # noqa: E402
import ct_pelvis_review_scene_blender as sc  # noqa: E402
import test_ct_pelvis_window_geometry as gt  # noqa: E402

BPY_WAS_IMPORTED_BY_MODULE = "bpy" in sys.modules


# ----------------------------------------------------------------------------
# Fake bpy
# ----------------------------------------------------------------------------
class FakeMatrix:
    def __init__(self, tx=0.0, ty=0.0, tz=0.0):
        self.rows = [[1.0, 0.0, 0.0, tx], [0.0, 1.0, 0.0, ty], [0.0, 0.0, 1.0, tz], [0.0, 0.0, 0.0, 1.0]]

    def __iter__(self):
        return iter(self.rows)

    @property
    def translation(self):
        return (self.rows[0][3], self.rows[1][3], self.rows[2][3])

    def __matmul__(self, v):
        return tuple(v[i] + self.rows[i][3] for i in range(3))


class FakeProps(dict):
    pass


class FakeObject:
    def __init__(self, name, data=None):
        self.name, self.data = name, data
        self.type = "EMPTY" if data is None else getattr(data, "kind", "MESH")
        self.matrix_world = FakeMatrix()
        self.parent = None
        self.props = FakeProps()
        self.empty_display_type = None
        self.empty_display_size = None
        self._loc = (0.0, 0.0, 0.0)

    @property
    def location(self):
        return self._loc

    @location.setter
    def location(self, v):
        self._loc = tuple(v)
        self.matrix_world = FakeMatrix(*self._loc)

    def __setitem__(self, k, v):
        self.props[k] = v

    def __getitem__(self, k):
        return self.props[k]


class FakeVert:
    def __init__(self, co):
        self.co = co


class FakeUV:
    uv = None


class FakeMesh:
    kind = "MESH"

    def __init__(self, name):
        self.name, self.vertices, self.faces, self.edges = name, [], [], []
        self.materials = []
        self.uv_layers = types.SimpleNamespace(new=self._new_uv)
        self._uv = None

    def from_pydata(self, verts, edges, faces):
        self.vertices = [FakeVert(v) for v in verts]
        self.edges, self.faces = edges, faces

    def update(self):
        pass

    def _new_uv(self, name):
        n = sum(len(f) for f in self.faces)
        self._uv = types.SimpleNamespace(name=name, data=[FakeUV() for _ in range(n)])
        return self._uv


class FakeBone:
    def __init__(self, name, head, tail):
        self.name, self.head_local, self.tail_local = name, head, tail


class FakeArmature:
    kind = "ARMATURE"

    def __init__(self, bones):
        self.bones = bones


class FakeImage:
    def __init__(self, path):
        self.name = Path(path).name
        self.filepath = path
        self.packed_file = None
        self.colorspace_settings = types.SimpleNamespace(name="sRGB")


class FakeNodes(list):
    def new(self, kind):
        n = types.SimpleNamespace(kind=kind, image=None,
                                  inputs=types.SimpleNamespace(), outputs=types.SimpleNamespace())
        n.inputs = {"Color": object(), "Surface": object()}
        n.outputs = {"Color": object(), "Emission": object()}
        self.append(n)
        return n


class FakeMaterial:
    def __init__(self, name):
        self.name = name
        self.use_nodes = False
        self.node_tree = types.SimpleNamespace(nodes=FakeNodes(), links=types.SimpleNamespace(
            new=lambda a, b: (a, b)))
        self.node_tree.nodes.clear = lambda: self.node_tree.nodes.__init__()


class Registry:
    def __init__(self, factory):
        self.items, self.factory = {}, factory

    def new(self, name, *args):
        item = self.factory(name, *args)
        self.items[name] = item
        return item

    def get(self, name):
        return self.items.get(name)

    def __iter__(self):
        return iter(list(self.items.values()))

    def __getitem__(self, k):
        return self.items[k]

    def __len__(self):
        return len(self.items)


class FakeCollection:
    def __init__(self, name):
        self.name = name
        self.objects = types.SimpleNamespace(link=lambda o: self._objs.append(o))
        self._objs = []
        self.children = types.SimpleNamespace(link=lambda c: self._kids.append(c))
        self._kids = []


class FakeBpy:
    def __init__(self):
        self.saved = []
        self.data = types.SimpleNamespace(
            objects=Registry(FakeObject), meshes=Registry(FakeMesh),
            collections=Registry(FakeCollection), materials=Registry(FakeMaterial),
            images=Registry(lambda n: FakeImage(n)), filepath="")
        self.data.images.load = lambda path, check_existing=True: self._load(path)
        scene_coll = FakeCollection("Scene Collection")
        self.context = types.SimpleNamespace(scene=types.SimpleNamespace(collection=scene_coll))
        self.path = types.SimpleNamespace(abspath=lambda p: p)
        self.app = types.SimpleNamespace(version_string="FAKE-0")
        self.ops = types.SimpleNamespace(wm=types.SimpleNamespace(
            save_as_mainfile=self._save, read_factory_settings=self._factory))

    def _load(self, path):
        im = FakeImage(path)
        self.data.images.items[im.name] = im
        return im

    def _save(self, filepath, copy=False):
        Path(filepath).write_bytes(b"FAKE-BLEND")
        self.saved.append((filepath, copy))

    def _factory(self, use_empty=False):
        self.data.objects.items.clear()

    # helpers to build a pre-existing "accepted skeleton"
    def add_existing_skeleton(self, record, perturb_mm=None):
        s = skel.extract_pelvic_set(record)
        bones = []
        for k, b in s["bones"].items():
            head = tuple(v / 1000 for v in b["head_mm"])
            tail = tuple(v / 1000 for v in b["tail_mm"])
            if perturb_mm and k == "sacrum":
                tail = (tail[0], tail[1], tail[2] + perturb_mm / 1000)
            bones.append(FakeBone("anat_" + k, head, tail))
        arm = self.data.objects.new(sc.MASTER_ARMATURE, FakeArmature(bones))
        arm.type = "ARMATURE"
        for k, m in s["markers"].items():
            ob = self.data.objects.new("HGPT_JOINT_" + k)
            ob.location = tuple(v / 1000 for v in m["centre_mm"])
        # an unrelated mesh the script must leave alone
        mesh = self.data.meshes.new("body_mesh")
        mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
        self.data.objects.new("a003_body", mesh)


def make_args(tmp, d=None, skip_ct=False, **kw):
    ns = dict(manifest=gt.PINNED, ct_dir=d, cache_dir=Path(tmp) / "cache", skip_ct=skip_ct,
              skeleton_label="a003", display_offset=list(sc.DEFAULT_DISPLAY_OFFSET_M),
              window_low=1000, window_high=50000, fresh=False,
              report_out=Path(tmp) / "report.json", save_as=None)
    ns.update(kw)
    return types.SimpleNamespace(**ns)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="scene_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.d, self.synthetic_manifest = gt.make_private_dir(self.tmp)
        self.manifest_file = self.tmp / "pins.json"
        self.manifest_file.write_text(json.dumps(self.synthetic_manifest))
        self.docs, _ = skel.load_inputs(ROOT)

    def args(self, **kw):
        kw.setdefault("manifest", self.manifest_file)
        return make_args(self.tmp, self.d, **kw)


class ModuleHygiene(unittest.TestCase):
    def test_importing_the_script_does_not_import_bpy(self):
        self.assertFalse(BPY_WAS_IMPORTED_BY_MODULE)
        self.assertNotIn("bpy", sys.modules)

    def test_no_private_ct_or_blend_artifacts_are_tracked(self):
        try:
            out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                                 text=True, check=True).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git unavailable")
        import re
        bad = [p for p in out if re.search(r"cvm\d+f\.(png|txt)$", p)
               or p.endswith("_display8.png") or re.search(r"CT_?PRIVATE.*\.blend1?$", p, re.I)]
        self.assertEqual(bad, [])

    def test_default_display_offset_is_not_a_hip_level_alignment(self):
        hjc_z = skel.derive(skel.load_inputs(ROOT)[0]["a003"])["HJC_midpoint_mm"][2] / 1000
        for s in (-357, -360, -363, -405, -408, -411):
            z = s / 1000 + sc.DEFAULT_DISPLAY_OFFSET_M[2]
            self.assertGreater(abs(z - hjc_z), 0.4, "CT display bay must not look registered to the hips")


class CtPlan(Base):
    def setUp(self):
        super().setUp()
        self.manifest = geo.load_pinned_manifest(self.synthetic_manifest)
        self.geoms, self.display = sc.prepare_ct(self.args(), self.manifest)
        self.plan = sc.build_ct_plan(self.manifest, self.geoms, self.display, (1.2, 0.0, 1.5))

    def test_six_planes_with_header_corners_and_status_flags(self):
        self.assertEqual(len(self.plan["planes"]), 6)
        for p in self.plan["planes"]:
            props = p["props"]
            self.assertEqual(props["region_status"], "UNVERIFIED")
            self.assertIs(props["display_only_not_registered"], True)
            self.assertIs(props["stored_values_are_calibrated_HU"], False)
            self.assertIs(props["image_laterality_verified"], False)
            g = self.geoms[props["source_id"]]
            self.assertEqual(p["corners_m"]["TL"], geo.plane_corners_display_m(g, (1.2, 0, 1.5))[0])
            self.assertEqual(props["slab_S_max_mm"] - props["slab_S_min_mm"], 3.0)

    def test_uv_maps_image_top_left_to_top_left_corner(self):
        uv = self.plan["planes"][0]["uv"]
        self.assertEqual((uv["TL"], uv["TR"], uv["BR"], uv["BL"]),
                         ((0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)))

    def test_orientation_follows_header_corners_and_winding_faces_plus_z(self):
        p = self.plan["planes"][1]
        c = p["corners_m"]
        u = [b - a for a, b in zip(c["TL"], c["TR"])]
        v = [b - a for a, b in zip(c["TR"], c["BR"])]
        n = geo._cross(u, v)
        self.assertGreater(n[2], 0)
        self.assertAlmostEqual(abs(u[0]), 0.46, places=4)     # columns run along display X
        self.assertAlmostEqual(abs(v[1]), 0.46, places=4)     # rows run along display Y
        self.assertAlmostEqual(c["TL"][2], -0.360 + 1.5)

    def test_adjacent_planes_are_three_mm_apart_in_display_z(self):
        zs = [p["corners_m"]["TL"][2] for p in self.plan["planes"]]
        self.assertAlmostEqual(zs[0] - zs[1], 0.003, places=9)
        self.assertAlmostEqual(zs[1] - zs[2], 0.003, places=9)
        self.assertAlmostEqual(zs[3] - zs[4], 0.003, places=9)
        self.assertAlmostEqual(zs[2] - zs[3], 0.042, places=9)      # -363 -> -405

    def test_images_live_under_the_private_cache_and_corner_markers_exist(self):
        cache = (self.tmp / "cache").resolve()
        for p in self.plan["planes"]:
            self.assertEqual(Path(p["image_path"]).resolve().parent, cache)
            self.assertTrue(Path(p["image_path"]).is_file())
        self.assertEqual(len(self.plan["corner_markers"]), 18)
        self.assertTrue(all("outer_edge" in k for m in self.plan["corner_markers"]
                            for k in m["props"] if k.startswith("image_row_col")))

    def test_headers_with_a_wrong_pinned_s_are_rejected(self):
        bad = copy.deepcopy(self.synthetic_manifest)
        bad["exact_png_and_scanner_header_sha256"][1]["scanner_S_mm"] = -359
        bad["groups"][0]["scanner_S_mm"][1] = -359
        with self.assertRaises(geo.PinError):
            sc.prepare_ct(self.args(), geo.load_pinned_manifest(bad))


class SkeletonPlan(Base):
    def test_points_sticks_and_governing_flags(self):
        plan = sc.build_skeleton_plan(self.docs["a003"], "a003", self.docs["s1_frame_p1"])
        names = {p["name"] for p in plan["points"]}
        self.assertEqual(len(plan["points"]), len(skel.MARKERS) + 1)
        self.assertIn("SKELINSP_a003__hip_left", names)
        self.assertIn("SKELINSP_a003__disc_l4_l5", names)
        stick_names = {s["name"] for s in plan["sticks"]}
        for k in ("sacrum", "l4", "l5", "hip_bone_left", "femur_right"):
            self.assertIn(f"SKELINSP_a003__bone_{k}", stick_names)
        for item in plan["points"] + [s for s in plan["sticks"] if "P1" not in s["name"]]:
            self.assertIs(item["props"]["geometry_governs"], True)
            self.assertEqual(item["props"]["status"], "SOURCE_SKELETON_RECORD_NOT_CT_VERIFIED")
        for item in plan["p1_points"] + [s for s in plan["sticks"] if "P1" in s["name"]]:
            self.assertIs(item["props"]["geometry_governs"], False)
            self.assertIn("PROVISIONAL", item["props"]["status"])
        self.assertEqual(len(plan["sticks"]), len(skel.BONES) + 1 + 4)

    def test_coordinates_are_the_record_values_in_metres(self):
        plan = sc.build_skeleton_plan(self.docs["a003"], "a003")
        hip = next(p for p in plan["points"] if p["name"].endswith("__hip_left"))
        self.assertEqual(hip["location_m"],
                         [v / 1000 for v in skel.extract_pelvic_set(self.docs["a003"])
                          ["markers"]["hip_left"]["centre_mm"]])
        self.assertAlmostEqual(hip["location_m"][0], 0.08330584416194597, places=12)
        self.assertEqual(plan["p1_points"], [])

    def test_c004_plan_has_identical_geometry_to_a003_plan(self):
        a = sc.build_skeleton_plan(self.docs["a003"], "x")
        c = sc.build_skeleton_plan(self.docs["c004"], "x")
        self.assertEqual(a, c)


class ExistingSkeletonComparison(Base):
    def test_matching_scene_reports_zero_and_perturbation_is_measured(self):
        for perturb, expected in ((None, 0.0), (2.5, 2.5)):
            bpy = FakeBpy()
            bpy.add_existing_skeleton(self.docs["a003"], perturb)
            bones, markers = sc.read_existing_skeleton(bpy, self.docs["a003"])
            rep = sc.compare_existing_skeleton(self.docs["a003"], bones, markers)
            self.assertEqual(rep["items_missing"], 0)
            self.assertAlmostEqual(rep["max_delta_mm"], expected, places=6)

    def test_missing_items_are_reported_not_invented(self):
        rep = sc.compare_existing_skeleton(self.docs["a003"], {}, {"hip_left": (0.0, 0.0, 0.0)})
        self.assertEqual(rep["items_found"], 1)
        self.assertEqual(rep["items_missing"], len(skel.BONES) + len(skel.MARKERS) - 1)


class ApplyAndRun(Base):
    def test_run_with_ct_creates_only_new_objects_and_never_packs(self):
        bpy = FakeBpy()
        bpy.add_existing_skeleton(self.docs["a003"])
        pre = set(bpy.data.objects.items)
        rep = sc.run(bpy, self.args(save_as=self.tmp / "review_CT_PRIVATE.blend"))
        new = set(bpy.data.objects.items) - pre
        self.assertEqual(set(rep["created"]["objects"]), new)
        self.assertTrue(pre.isdisjoint(rep["created"]["objects"]))
        self.assertTrue(rep["preexisting_objects_unchanged"])
        self.assertIs(rep["ct_images_packed"], False)
        self.assertEqual(len(rep["created"]["images"]), 6)
        for im in bpy.data.images.items.values():
            self.assertIsNone(im.packed_file)
            self.assertEqual(im.colorspace_settings.name, "Non-Color")
        self.assertEqual(len(rep["planes"]), 6)
        self.assertEqual(rep["existing_skeleton_comparison"]["items_missing"], 0)
        self.assertAlmostEqual(rep["existing_skeleton_comparison"]["max_delta_mm"], 0.0, places=6)
        self.assertEqual(bpy.saved[0][1], True)               # copy=True: session file untouched
        for flag in ("anatomical_region_identified", "HomeGymPT_world_transform_applied",
                     "canonical_promotion_allowed", "skeleton_geometry_modified"):
            self.assertIs(rep[flag], False)

    def test_report_contains_hashes_and_geometry_but_never_header_text(self):
        bpy = FakeBpy()
        sc.run(bpy, self.args())
        text = (self.tmp / "report.json").read_text()
        self.assertNotIn(gt.SECRET, text)
        self.assertIn(self.synthetic_manifest["exact_png_and_scanner_header_sha256"][0]["png_sha256"], text)
        json.loads(text)

    def test_skip_ct_needs_no_ct_directory(self):
        bpy = FakeBpy()
        rep = sc.run(bpy, make_args(self.tmp, None, skip_ct=True, manifest=self.manifest_file))
        self.assertFalse(rep["ct_included"])
        self.assertEqual(rep["created"]["images"], [])
        self.assertEqual(rep["planes"], [])
        self.assertFalse(bpy.data.images.items)

    def test_tampered_source_aborts_before_any_scene_change(self):
        (self.d / "cvm1803f.png").write_bytes(b"tampered")
        bpy = FakeBpy()
        bpy.add_existing_skeleton(self.docs["a003"])
        count = len(bpy.data.objects)
        with self.assertRaises(geo.PinError):
            sc.run(bpy, self.args())
        self.assertEqual(len(bpy.data.objects), count)
        self.assertEqual(len(bpy.data.collections), 0)
        self.assertFalse((self.tmp / "report.json").exists())

    def test_any_change_to_a_preexisting_object_is_fatal(self):
        bpy = FakeBpy()
        bpy.add_existing_skeleton(self.docs["a003"])
        real_apply = sc.apply_plan

        def evil(bpy_, *a, **k):
            out = real_apply(bpy_, *a, **k)
            bpy_.data.objects["HGPT_JOINT_hip_left"].location = (9.0, 9.0, 9.0)
            return out

        sc.apply_plan = evil
        self.addCleanup(setattr, sc, "apply_plan", real_apply)
        with self.assertRaisesRegex(sc.SceneSafetyError, "pre-existing objects changed"):
            sc.run(bpy, self.args(skip_ct=True))
        self.assertFalse((self.tmp / "report.json").exists())

    def test_mesh_vertex_edit_of_existing_geometry_is_detected(self):
        bpy = FakeBpy()
        bpy.add_existing_skeleton(self.docs["a003"])
        before = sc.snapshot_objects(bpy)
        bpy.data.meshes["body_mesh"].vertices[0].co = (0.5, 0, 0)
        with self.assertRaises(sc.SceneSafetyError):
            sc.assert_unchanged(before, sc.snapshot_objects(bpy))

    def test_packed_or_outside_cache_images_are_rejected(self):
        bpy = FakeBpy()
        sc.run(bpy, self.args())
        name = next(iter(bpy.data.images.items))
        bpy.data.images.items[name].packed_file = object()
        with self.assertRaisesRegex(sc.SceneSafetyError, "packed"):
            sc.verify_images_external(bpy, [name], self.tmp / "cache")
        bpy.data.images.items[name].packed_file = None
        with self.assertRaisesRegex(sc.SceneSafetyError, "private cache"):
            sc.verify_images_external(bpy, [name], self.tmp / "elsewhere")

    def test_outputs_are_create_only_and_private(self):
        bpy = FakeBpy()
        (self.tmp / "report.json").write_text("keep")
        with self.assertRaises(FileExistsError):
            sc.run(bpy, self.args())
        (self.tmp / "report.json").unlink()
        (self.tmp / "existing.blend").write_bytes(b"x")
        with self.assertRaises(FileExistsError):
            sc.run(bpy, self.args(save_as=self.tmp / "existing.blend"))
        with self.assertRaises(geo.PinError):
            sc.run(bpy, self.args(save_as=ROOT / "should_not_exist_CT_PRIVATE.blend"))
        self.assertFalse((ROOT / "should_not_exist_CT_PRIVATE.blend").exists())
        bpy.data.filepath = str(self.tmp / "ghost.blend")       # opened file no longer on disk
        with self.assertRaisesRegex(sc.SceneSafetyError, "overwrite the opened"):
            sc.run(bpy, self.args(save_as=self.tmp / "ghost.blend"))
        self.assertFalse((self.tmp / "report.json").exists())

    def test_cache_directory_inside_the_repo_is_refused(self):
        with self.assertRaises(geo.PinError):
            sc.prepare_ct(self.args(cache_dir=ROOT / "scratch_cache"),
                          geo.load_pinned_manifest(self.synthetic_manifest))
        self.assertFalse((ROOT / "scratch_cache").exists())

    def test_fresh_flag_resets_the_scene_before_snapshotting(self):
        bpy = FakeBpy()
        bpy.add_existing_skeleton(self.docs["a003"])
        rep = sc.run(bpy, self.args(skip_ct=True, fresh=True))
        self.assertEqual(rep["preexisting_object_count"], 0)
        self.assertEqual(rep["existing_skeleton_comparison"]["items_found"], 0)


class CommandLine(unittest.TestCase):
    def test_ct_dir_and_cache_dir_required_unless_skip_ct(self):
        with contextlib.redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit):
                sc.parse_args(["--report-out", "r.json"])
        self.assertIn("--ct-dir and --cache-dir are required", err.getvalue())
        a = sc.parse_args(["--skip-ct", "--report-out", "r.json", "--skeleton-label", "c004"])
        self.assertTrue(a.skip_ct)
        self.assertEqual(a.skeleton_label, "c004")
        self.assertEqual(tuple(a.display_offset), sc.DEFAULT_DISPLAY_OFFSET_M)

    def test_report_out_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                sc.parse_args(["--skip-ct"])


if __name__ == "__main__":
    unittest.main()
