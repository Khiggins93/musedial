"""Reproducible original 3D interpretation for MuseDial. Run with Blender -b -P.
No Meta model or animation assets are used. All geometry is generated here.
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/rendered-v2.1'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.threads_mode = 'FIXED'
scene.render.threads = 8
scene.render.resolution_x = scene.render.resolution_y = 192
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.fps = 20
scene.world.color = (0.025, 0.025, 0.025)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = .55

def material(name, color, rough=.5, texture=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        bs = m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        output = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(bs.outputs['BSDF'], output.inputs['Surface'])
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    if texture:
        noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 100
        bump = m.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .06
        bump.inputs['Distance'].default_value = .015
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], bs.inputs['Normal'])
    return m

cream = material('warm ivory plush', (.87,.82,.59), rough=.82, texture=True)
face = material('pale cream face', (.94,.76,.46), rough=.85)
dark = material('small dark eyes', (.008,.005,.002), .82)
next(n for n in dark.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value=.12
pink = material('subtle peach blush', (.91,.55,.39), .9)
white = material('tiny eye catchlights', (.95,.9,.74), .3)
root = bpy.data.objects.new('Character', None)
scene.collection.objects.link(root)

def sphere(name, loc, scale, mat, parent=root):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=24, location=loc)
    ob=bpy.context.object; ob.name=name; ob.scale=scale
    ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth=True
    ob.parent=parent
    return ob

# One uninterrupted hood/body silhouette: no separate head, belly or accessories.
verts=[]; faces=[]; rings=64; sides=64
for j in range(rings+1):
    v=-1+2*j/rings
    radius=max(.0001,1-abs(v)**2.8)**(1/2.8)
    width=.72-.10*max(0,v)
    for i in range(sides):
        angle=2*math.pi*i/sides
        verts.append((width*radius*math.cos(angle),.43*radius*math.sin(angle),1.55+1.13*v))
for j in range(rings):
    for i in range(sides):
        k=j*sides+i; n=j*sides+(i+1)%sides
        faces.append((k,n,n+sides,k+sides))
mesh=bpy.data.meshes.new('continuous plush shell'); mesh.from_pydata(verts,[],faces); mesh.update()
body=bpy.data.objects.new('continuous hood and body',mesh); scene.collection.objects.link(body); body.parent=root
body.data.materials.append(cream)
for poly in mesh.polygons: poly.use_smooth=True

# Rounded-rectangle inset framed by a narrow lip, like the supplied Charm photo.
def face_panel(name, loc, scale, mat):
    ob=sphere(name,loc,scale,mat)
    for v in ob.data.vertices:
        # Superellipse in the face plane, retaining a softly rounded depth.
        v.co.x=math.copysign(abs(v.co.x)**.74,v.co.x)
        v.co.z=math.copysign(abs(v.co.z)**.74,v.co.z)
        v.co.y += (.08*v.co.x**2 + .035*v.co.z**2)/scale[1]
    return ob
face_panel('small face window',(0,-.438,2.17),(.465,.025,.335),face)
# A continuous rolled lip follows the shell curvature, surrounding the inset.
# Unlike a second solid panel it leaves a real opening and a soft inner shadow.
lip_verts=[]; lip_faces=[]
for i in range(128):
    a=2*math.pi*i/128
    u=math.copysign(abs(math.cos(a))**.74,math.cos(a))
    v=math.copysign(abs(math.sin(a))**.74,math.sin(a))
    for j in range(12):
        b=2*math.pi*j/12
        lip_verts.append(((.48+.025*math.cos(b))*u,
                          -.450+.08*u*u+.035*v*v-.022*math.sin(b),
                          2.17+(.35+.025*math.cos(b))*v))
for i in range(128):
    for j in range(12):
        lip_faces.append((i*12+j,((i+1)%128)*12+j,
                          ((i+1)%128)*12+(j+1)%12,i*12+(j+1)%12))
lip_mesh=bpy.data.meshes.new('rolled hood lip'); lip_mesh.from_pydata(lip_verts,[],lip_faces); lip_mesh.update()
lip=bpy.data.objects.new('soft hood opening',lip_mesh); scene.collection.objects.link(lip); lip.parent=root
lip.data.materials.append(cream)
for p in lip_mesh.polygons: p.use_smooth=True
for x in [-.28,.28]:
    foot=sphere('short foot',(x,-.005,.36),(.22,.235,.18),cream)
    for v in foot.data.vertices:
        v.co.x=math.copysign(abs(v.co.x)**.70,v.co.x)
        v.co.z=math.copysign(abs(v.co.z)**.70,v.co.z)
arms=[]
for side in [-1,1]:
    pivot=bpy.data.objects.new('arm pivot',None); scene.collection.objects.link(pivot)
    pivot.parent=root; pivot.location=(side*.58,0,1.65)
    arm=sphere('long soft arm',(side*.13,-.015,-.40),(.17,.20,.57),cream,pivot)
    arm.rotation_euler[1]=-side*.23
    arms.append(pivot)
eyes=[]; glints=[]
for x in [-.215,.215]:
    eyes.append(sphere('small eye',(x,-.462,2.215),(.045,.024,.050),dark))
    glints.append(sphere('eye glint',(x-.010,-.485,2.231),(.006,.003,.007),white))
    sphere('faint cheek',(x*1.22,-.439,2.10),(.063,.007,.028),pink)
# A tiny smile, with no nose, matching the reference expression.
curve=bpy.data.curves.new('tiny smile','CURVE'); curve.dimensions='3D'; curve.bevel_depth=.010; curve.bevel_resolution=3
spl=curve.splines.new('POLY'); spl.points.add(16)
for i,p in enumerate(spl.points):
    x=-.060+i*.12/16; p.co=(x,-.468,2.105+4.8*x*x,1)
mouth=bpy.data.objects.new('smile',curve); scene.collection.objects.link(mouth); mouth.parent=root; mouth.data.materials.append(dark)
openmouth=sphere('surprise mouth',(0,-.468,2.105),(.042,.013,.055),dark)

# Black floor catches a subtle contact shadow without an enclosing backdrop.
floor=material('black stage',(.0001,.0001,.0001),.85)
next(n for n in floor.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value=0
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.13))
bpy.context.object.data.materials.append(floor)
def aim(ob,at): ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,color,size in [('key',(-3,-4,6),450,(1,.94,.82),4),('fill',(3,-2,3),150,(.85,.90,1),3),('rim',(1,2,4),250,(1,.95,.82),2)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.color=color; data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob); ob.location=loc; aim(ob,(0,0,1.5))
camdata=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',camdata); scene.collection.objects.link(cam)
cam.location=(0,-8,2.7); aim(cam,(0,0,1.48)); camdata.type='ORTHO'; camdata.ortho_scale=3.25; scene.camera=cam

names=['tranquilo','curioso','pensando','animado','dormilon','feliz','saludo','sorpresa','sueno']
N=40
for mood in range(9):
    for f in range(N):
        phase=2*math.pi*f/N; s=math.sin(phase); c=math.cos(phase)
        frame=mood*N+f+1
        breath=.5-.5*c
        root.location=(.008*s,0,-.004*breath)
        root.rotation_euler=(.008*math.sin(phase+.5),.018*s,.012*s)
        root.scale=(1+.006*breath,1,1+.012*breath)
        left,right=arms
        left.rotation_euler=(.035*math.sin(phase-.4),.12+.035*s,0)
        right.rotation_euler=(-.025*math.sin(phase-.4),-.12-.035*s,0)
        # Six-frame eased closure/opening instead of two suddenly flat frames.
        blink=1-.94*(.5+.5*math.cos(math.pi*(f-29.5)/3.5)) if abs(f-29.5)<3.5 else 1
        for eye in eyes: eye.scale.z=.050*blink
        mouth.hide_render=False; openmouth.hide_render=True
        if mood==1: root.rotation_euler[1]=.12*s; root.rotation_euler[2]=.14
        if mood==2: right.rotation_euler[1]=-.8; root.rotation_euler[2]=-.10; root.rotation_euler[1]=.06*s
        if mood in [3,5]:
            root.location.z=.10*(1-c); left.rotation_euler[1]=.65+.15*s; right.rotation_euler[1]=-.65-.15*s
        if mood==5:
            root.rotation_euler[2]=.10*s
            for eye in eyes: eye.scale.z=.025
            left.rotation_euler[1]=.9+.15*s; right.rotation_euler[1]=-.9+.15*s
        if mood in [4,8]:
            for eye in eyes: eye.scale.z=.008
            root.rotation_euler[0]=.05; root.scale.z=1+.025*s
            if mood==8:
                mouth.hide_render=True; openmouth.hide_render=False; openmouth.scale.z=.035+.016*(1+s)
        if mood==6:
            right.rotation_euler[1]=-1.35+.22*math.sin(phase*2)
            right.rotation_euler[0]=.12*math.sin(phase*2-.5)
            root.rotation_euler[2]=-.04+.015*s
        if mood==7:
            mouth.hide_render=True; openmouth.hide_render=False; openmouth.scale.z=.065
            for eye in eyes: eye.scale.z=.065
            left.rotation_euler[1]=.8; right.rotation_euler[1]=-.8; root.location.z=.05*(1-c)
        for ob in [root,left,right,*eyes,openmouth]:
            for prop in ['location','rotation_euler','scale']: ob.keyframe_insert(data_path=prop,frame=frame)
        mouth.keyframe_insert(data_path='hide_render',frame=frame); openmouth.keyframe_insert(data_path='hide_render',frame=frame)
        for glint in glints:
            glint.hide_render=blink<1 or mood in [4,5,8]
            glint.keyframe_insert(data_path='hide_render',frame=frame)
scene.frame_start=1; scene.frame_end=9*N
scene.frame_set(1)
if '--scene-only' not in sys.argv:
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/musedial.blend'))
preview='--preview' in sys.argv
frames=[1,41,81,121,161,201,241,281,321] if preview else range(1,9*N+1)
if '--scene-only' in sys.argv: frames=[]
for frame in frames:
    path=OUT/f'{frame:04}.png'
    if path.exists() and '--force' not in sys.argv: continue
    scene.frame_set(frame); scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)
print('MUSEDIAL_RENDER_COMPLETE',flush=True)
