"""Additional normal-theme gestures, using the original procedural character.
Blender -b -P assets/render_companion.py -- [--preview] [--force]
"""
import math
import runpy
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.argv.append('--scene-only')
base = runpy.run_path(str(ROOT / 'assets/render_avatar.py'))
sys.argv.remove('--scene-only')
scene = base['scene']
root, arms, eyes, glints = (base[n] for n in ('root', 'arms', 'eyes', 'glints'))
mouth, opened = base['mouth'], base['openmouth']
scene.frame_set(1)
for ob in scene.objects:
    ob.animation_data_clear()
defaults = [(ob, ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy())
            for ob in [root, *arms, *eyes, *glints, opened]]
OUT = ROOT / 'assets/rendered-companion'
OUT.mkdir(parents=True, exist_ok=True)

# Nine true 3D gaze directions followed by four eased, finite gestures.
clips = [('gaze', 9), ('smile', 32), ('cuddle', 32), ('hug', 40), ('tickle', 32)]
index = 0
preview_frames = []
for name, count in clips:
    preview_frames.append(index + (4 if name == 'gaze' else count // 2) + 1)
    for f in range(count):
        index += 1
        for ob, loc, rot, scale in defaults:
            ob.location, ob.rotation_euler, ob.scale = loc.copy(), rot.copy(), scale.copy()
        mouth.hide_render, opened.hide_render = False, True
        for glint in glints: glint.hide_render = False
        t = f / (count - 1)
        ease = math.sin(math.pi * t) ** 2
        if name == 'gaze':
            x, y = f % 3 - 1, 1 - f // 3
            root.rotation_euler = (.025 * y, .018 * x, -.045 * x)
            for ob in [*eyes, *glints]:
                ob.location.x += .047 * x
                ob.location.z += .037 * y
        else:
            root.location.z += (.025 if name != 'hug' else .04) * ease
            root.rotation_euler[1] = .035 * math.sin(t * math.tau) * ease
            root.scale.z = 1 + .012 * ease
            if name == 'smile':
                for eye in eyes: eye.scale.z = .05 - .024 * ease
                arms[0].rotation_euler[1] += .2 * ease
                arms[1].rotation_euler[1] -= .2 * ease
            if name in ('cuddle', 'hug', 'tickle'):
                for eye in eyes: eye.scale.z = .05 - .043 * ease
                for glint in glints: glint.hide_render = ease > .3
                root.rotation_euler[2] = .09 * math.sin(t * math.tau * (3 if name == 'tickle' else 1)) * ease
            if name == 'cuddle':
                root.rotation_euler[0] = .06 * ease
                arms[0].rotation_euler[1] += .35 * ease
                arms[1].rotation_euler[1] -= .35 * ease
            if name == 'hug':
                root.scale = (1 + .10 * ease, 1 + .08 * ease, 1 + .10 * ease)
                # Open the arms and reach towards the viewer, then return.
                arms[0].rotation_euler = (-.55 * ease, .12 + 1.05 * ease, 0)
                arms[1].rotation_euler = (-.55 * ease, -.12 - 1.05 * ease, 0)
            if name == 'tickle':
                root.location.z += .06 * abs(math.sin(t * math.tau * 3)) * ease
                arms[0].rotation_euler[1] += .7 * ease
                arms[1].rotation_euler[1] -= .7 * ease
                mouth.hide_render, opened.hide_render = ease > .4, ease <= .4
                opened.scale.z = .04
        for ob, *_ in defaults:
            for prop in ('location', 'rotation_euler', 'scale'):
                ob.keyframe_insert(data_path=prop, frame=index)
        for ob in [mouth, opened, *glints]:
            ob.keyframe_insert(data_path='hide_render', frame=index)
scene.frame_start, scene.frame_end = 1, index
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'assets/companion.blend'))
for frame in (preview_frames if '--preview' in sys.argv else range(1, index + 1)):
    path = OUT / f'{frame:04}.png'
    if path.exists() and '--force' not in sys.argv: continue
    scene.frame_set(frame)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
print('COMPANION_RENDER_COMPLETE', flush=True)
