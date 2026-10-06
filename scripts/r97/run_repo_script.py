"""Run a repository Blender script (written for `blender file.blend --python script -- args`) under the bpy module."""
import sys, bpy, runpy
argv = sys.argv[sys.argv.index('--')+1:]
blend, script, rest = argv[0], argv[1], argv[2:]
bpy.ops.wm.open_mainfile(filepath=blend)
sys.argv = [script, '--'] + rest
runpy.run_path(script, run_name='__main__')
