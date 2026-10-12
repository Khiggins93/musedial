"""Procedural reconstruction of the approved pumpkin concept; Blender 5.2.
Run: blender -b -t 8 -P assets/render_halloween.py [-- --preview --force]
"""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/rendered-halloween'; OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=32
scene.cycles.use_denoising=True; scene.render.threads_mode='FIXED'; scene.render.threads=8
scene.render.resolution_x=scene.render.resolution_y=192; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True; scene.render.fps=20
scene.world.color=(.018,.012,.025); scene.view_settings.view_transform='AgX'; scene.view_settings.exposure=.25

def material(name,color,rough=.65,emission=0):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.node_tree.nodes.clear()
    bs=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled'); out=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*color,1); bs.inputs['Roughness'].default_value=rough
    bs.inputs['Emission Color'].default_value=(*color,1); bs.inputs['Emission Strength'].default_value=emission
    return m,bs
orange,_=material('burnt orange velvet',(.8,.19,.018),.8)
rim_mat,_=material('pumpkin rolled edge',(.67,.12,.008),.8)
cream,_=material('warm cream face',(1,.78,.47),.8)
purple,_=material('violet bat cape',(.16,.03,.23),.64)
green,_=material('curved olive stem',(.16,.115,.016),.85)
dark,_=material('glossy black eyes',(.006,.003,.002),.22)
pink,_=material('peach cheeks',(.95,.26,.075),.88)
white,_=material('eye highlights',(1,.94,.77),.4)
gold,glow=material('amber pumpkin glow',(1,.40,.015),.4,3)
bronze,_=material('cape clasp',(.35,.17,.035),.4)
root=bpy.data.objects.new('Halloween Muse',None); scene.collection.objects.link(root)

def mesh(name,verts,faces,mat,parent=root):
    data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
    ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob); ob.parent=parent
    ob.data.materials.append(mat)
    for p in data.polygons:p.use_smooth=True
    return ob

def sphere(name,loc,scale,mat,parent=root,pumpkin=False):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=loc)
    ob=bpy.context.object; ob.name=name; ob.parent=parent; ob.scale=scale; ob.data.materials.append(mat)
    if pumpkin:
        for v in ob.data.vertices:
            a=math.atan2(v.co.y,v.co.x); fac=1+.055*math.cos(10*a)
            v.co.x*=fac; v.co.y*=fac
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def curve(name,points,radius,mat,parent=root):
    data=bpy.data.curves.new(name,'CURVE'); data.dimensions='3D'; data.bevel_depth=radius; data.bevel_resolution=3
    spl=data.splines.new('POLY'); spl.points.add(len(points)-1)
    for p,co in zip(spl.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob); ob.parent=parent; ob.data.materials.append(mat)
    return ob

body=sphere('segmented pumpkin suit',(0,0,1.0),(.66,.43,.70),orange,pumpkin=True)
head=sphere('large pumpkin hood',(0,0,2.22),(.85,.57,.78),orange,pumpkin=True)
face=sphere('cream face window',(0,-.535,2.20),(.63,.075,.445),cream)
for v in face.data.vertices:
    v.co.x=math.copysign(abs(v.co.x)**.76,v.co.x); v.co.z=math.copysign(abs(v.co.z)**.76,v.co.z)
    v.co.y+=(.07*v.co.x*v.co.x+.035*v.co.z*v.co.z)/.075
points=[]
for i in range(129):
    a=i*2*math.pi/128; u=math.copysign(abs(math.cos(a))**.76,math.cos(a)); v=math.copysign(abs(math.sin(a))**.76,math.sin(a))
    points.append((.65*u,-.555+.07*u*u+.035*v*v,2.20+.465*v))
curve('thick pumpkin hood rim',points,.055,rim_mat)
# Curved stem with a spiral tendril, both part of the silhouette.
curve('pumpkin stem',[(.03+.16*math.sin(t*1.6),.01,2.89+.40*t) for t in [i/24 for i in range(25)]],.075,green)
curve('curled tendril',[(.19+.12*math.cos(t)*(.4+.6*i/48),-.005,3.04+.12*math.sin(t)) for i,t in enumerate([i*2*math.pi/48 for i in range(49)])],.018,green)
for x in [-.27,.27]: sphere('short orange foot',(x,-.02,.27),(.23,.25,.18),orange)
arms=[]
for side in [-1,1]:
    pivot=bpy.data.objects.new('arm pivot',None); scene.collection.objects.link(pivot); pivot.parent=root; pivot.location=(side*.57,0,1.50)
    sphere('soft orange arm',(side*.12,-.015,-.27),(.18,.20,.43),orange,pivot)
    arms.append(pivot)
# Scalloped cape fans out behind the body, with a dimensional collar and clasp.
cape=[]
for side in [-1,1]:
    outline=[(.16,1.69),(.54,1.60),(.90,1.38),(1.15,.82),(.97,.98),(.84,.64),(.72,.88),(.52,.61),(.35,.96),(.18,1.08)]
    verts=[(side*x,.18+.05*x,z) for x,z in outline]
    ob=mesh('scalloped bat cape',verts,[tuple(range(len(verts)))],purple)
    solid=ob.modifiers.new('fabric thickness','SOLIDIFY'); solid.thickness=.025
    bevel=ob.modifiers.new('soft cloth edges','BEVEL'); bevel.width=.035; bevel.segments=3
    cape.append(ob)
    mesh('folded collar',[(0,-.45,1.63),(side*.51,-.33,1.62),(side*.36,-.40,1.40)],[(0,1,2)],purple)
sphere('bronze clasp',(0,-.485,1.57),(.073,.03,.08),bronze)
eyes=[]; glints=[]
for x in [-.245,.245]:
    eyes.append(sphere('black eye',(x,-.61,2.25),(.067,.035,.08),dark))
    glints.append(sphere('catchlight',(x-.016,-.645,2.28),(.018,.009,.018),white))
    sphere('rosy cheek',(x*1.32,-.581,2.10),(.087,.012,.047),pink)
mouth=curve('tiny smile',[(x,-.620,2.075+3.5*x*x) for x in [-.085+i*.17/20 for i in range(21)]],.014,dark)
openmouth=sphere('open expressive mouth',(0,-.62,2.08),(.067,.025,.085),dark)
# Luminous jack-o-lantern emblem: broad readable shapes, no tiny details.
for side in [-1,1]:
    mesh('glowing triangular pumpkin eye',[(side*.13,-.453,1.08),(side*.28,-.453,1.08),(side*.22,-.446,1.26)],[(0,1,2)],gold)
smile=[(-.29,.97),(-.18,.91),(-.065,.88),(.065,.88),(.18,.91),(.29,.97),(.22,.79),(.08,.735),(.08,.79),(-.02,.79),(-.02,.73),(-.18,.79)]
mesh('glowing pumpkin grin',[(x,-.456,z) for x,z in smile],[tuple(range(len(smile)))],gold)
ld=bpy.data.lights.new('amber reflected glow','POINT'); ld.energy=4; ld.color=(1,.25,.01); ld.shadow_soft_size=.25
lamp=bpy.data.objects.new('amber reflected glow',ld); scene.collection.objects.link(lamp); lamp.parent=root; lamp.location=(0,-.66,.94)

def aim(ob,at):ob.rotation_euler=(Vector(at)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,color,size in [('soft key',(-3,-4,6),450,(1,.83,.62),4),('fill',(3,-3,3),190,(1,.90,.75),3),('violet rim',(-2,2,4),380,(.48,.16,1),2)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.color=color; data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob); ob.location=loc; aim(ob,(0,0,1.6))
camdata=bpy.data.cameras.new('Camera'); cam=bpy.data.objects.new('Camera',camdata); scene.collection.objects.link(cam)
cam.location=(0,-9,3.0); aim(cam,(0,0,1.7)); camdata.type='ORTHO'; camdata.ortho_scale=3.85; scene.camera=cam
N=40
for mood in range(12):
    for f in range(N):
        t=2*math.pi*f/N; s=math.sin(t); c=math.cos(t); frame=mood*N+f+1
        root.location=(0,0,.012*(1-c)); root.rotation_euler=(0,.02*s,.018*s); root.scale=(1+.006*s,1,1+.008*s)
        left,right=arms; left.rotation_euler=(0,.08+.025*s,0); right.rotation_euler=(0,-.08-.025*s,0)
        blink=1-.94*(.5+.5*math.cos(math.pi*(f-29.5)/3.5)) if abs(f-29.5)<3.5 else 1
        for eye in eyes:eye.scale.z=.08*blink
        mouth.hide_render=False; openmouth.hide_render=True; openmouth.scale=(.067,.025,.085)
        if mood==1:root.rotation_euler[2]=.13; root.rotation_euler[1]=.10*s
        if mood==2:root.rotation_euler[2]=-.09; eyes[1].scale.z=.025+.015*(1+c); right.rotation_euler[1]=-.35
        if mood==3:right.rotation_euler[1]=-1.25+.25*math.sin(2*t); right.rotation_euler[0]=.12*s
        if mood==4:
            for eye in eyes:eye.scale.z=.022
            root.location.z=.02*(1-math.cos(2*t)); right.rotation_euler[1]=-.6
        if mood in [5,6]:
            mouth.hide_render=True; openmouth.hide_render=False
            for eye in eyes:eye.scale.z=.105
            left.rotation_euler[1]=.65; right.rotation_euler[1]=-.65
            if mood==6:root.location.z=.13*(1-c); root.rotation_euler[0]=-.04*(1-c)
        if mood==7:
            mouth.hide_render=True; openmouth.hide_render=False; openmouth.scale=(.10,.025,.065+.025*(1+c))
            for eye in eyes:eye.scale.z=.018
            root.rotation_euler[2]=.07*s; root.location.z=.045*(1-math.cos(2*t))
        if mood==8:
            root.rotation_euler[2]=.11*s; root.location.z=.055*(1-math.cos(2*t))
            left.rotation_euler[1]=.65+.22*s; right.rotation_euler[1]=-.65+.22*s
        if mood==9:
            left.rotation_euler[1]=1.05+.13*s; right.rotation_euler[1]=-1.05-.13*s; root.rotation_euler[1]=.07*s
        if mood in [10,11]:
            for eye in eyes:eye.scale.z=.012
            root.rotation_euler[0]=.04; root.scale.z=1+.02*s
            if mood==11:mouth.hide_render=True; openmouth.hide_render=False; openmouth.scale.z=.035+.045*(1+s)
        for i,ob in enumerate(cape):
            ob.rotation_euler[2]=(-1 if i else 1)*(.015+.025*math.sin(t-.45))
            ob.keyframe_insert(data_path='rotation_euler',frame=frame)
        glow.inputs['Emission Strength'].default_value=(3 if mood!=9 else 5)+1.4*s
        glow.inputs['Emission Strength'].keyframe_insert(data_path='default_value',frame=frame)
        ld.energy=4+1.5*s; ld.keyframe_insert(data_path='energy',frame=frame)
        for ob in [root,left,right,*eyes,openmouth]:
            for prop in ['location','rotation_euler','scale']:ob.keyframe_insert(data_path=prop,frame=frame)
        for ob in [mouth,openmouth]:ob.keyframe_insert(data_path='hide_render',frame=frame)
        for ob in glints:
            ob.hide_render=blink<.5 or mood in [4,7,10,11]; ob.keyframe_insert(data_path='hide_render',frame=frame)
scene.frame_start=1; scene.frame_end=480; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/halloween.blend'))
frames=[m*N+1 for m in range(12)] if '--preview' in sys.argv else range(1,481)
for frame in frames:
    path=OUT/f'{frame:04}.png'
    if path.exists() and '--force' not in sys.argv:continue
    scene.frame_set(frame); scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
print('HALLOWEEN_RENDER_COMPLETE',flush=True)
