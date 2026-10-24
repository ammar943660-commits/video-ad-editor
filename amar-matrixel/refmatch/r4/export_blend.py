#!/usr/bin/env python3
"""export_blend.py — مشروع Blender قابل للتعديل لـR4: كاميرا بمفاتيح لكل فريم (من تتبع القطعة) + إطار القطعة + مبانٍ Wireframe متوهجة (مكعبات بمعدِّل Wireframe، الارتفاع يتحرك بمفاتيح) + نص المساحة.
   /tmp/bpyenv/bin/python export_blend.py <work> out.blend [verify_frame]"""
import sys,os,json,math,numpy as np
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(D,'..'))
import bpy
from mathutils import Matrix
from bl_common import reset
W,OUT=sys.argv[1:3]; VF=int(sys.argv[3]) if len(sys.argv)>3 else None
sys.argv=['holo.py',W,'/tmp/_x','0','0']; src=open(f'{D}/holo.py').read().split("if __name__")[0]; G={'__file__':f'{D}/holo.py'}; exec(src,G)
C=G['C']; cam=G['cam']; TR=G['TR']; LW,LH=C['lot_m']; n=len(TR)
sc=reset(); sc.render.resolution_x=1146; sc.render.resolution_y=644; sc.render.fps=30; sc.frame_start=0; sc.frame_end=331; sc.render.film_transparent=True
cd=bpy.data.cameras.new('CAM'); cd.sensor_fit='HORIZONTAL'; cd.sensor_width=36; cd.lens=18/math.tan(math.radians(C['fov_deg'])/2); cd.clip_start=0.5; cd.clip_end=5000
co=bpy.data.objects.new('CAM',cd); sc.collection.objects.link(co); sc.camera=co
F=np.diag([1,-1,-1.]); MIR=None
for fr in range(sc.frame_end+1):
    s_=fr-C['loop']['from'] if fr>=C['loop']['from'] else fr
    H,R,t=cam(min(s_,n-1))
    if MIR is None: MIR=np.linalg.det(R)<0
    M=np.diag([1,-1,1.]) if MIR else np.eye(3)      # عالم يميني: نعكس Y إن لزم
    V=np.eye(4); V[:3,:3]=F@R@M; V[:3,3]=F@t; co.matrix_world=Matrix(np.linalg.inv(V).tolist()); co.keyframe_insert('location',frame=fr); co.keyframe_insert('rotation_euler',frame=fr)
sgn=-1 if MIR else 1
def em(name,col,s):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear(); o=nt.nodes.new('ShaderNodeOutputMaterial'); e=nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value=(col[2]/255,col[1]/255,col[0]/255,1); e.inputs['Strength'].default_value=s; nt.links.new(e.outputs[0],o.inputs['Surface']); return m
NEON=em('NEON',C['color']['glow1'],6.0)
def box(name,x0,x1,y0,y1,h,grow=None,thick=0.25):
    """صندوق Wireframe بارتفاع h (بالمتر)؛ النمو عبر Shape Key «HEIGHT» (0→1) كي لا تتشوه سماكة الخطوط."""
    import bmesh
    me=bpy.data.meshes.new(name); bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1.0); bm.to_mesh(me); bm.free()
    for v in me.vertices: v.co=( (x0+x1)/2+v.co.x*(x1-x0), sgn*((y0+y1)/2+v.co.y*(y1-y0)), 0.0 if v.co.z<0 else 0.01 )
    ob=bpy.data.objects.new(name,me); sc.collection.objects.link(ob); ob.shape_key_add(name='Basis'); k=ob.shape_key_add(name='HEIGHT')
    for i,v in enumerate(me.vertices):
        if v.co.z>0.005: k.data[i].co.z=h
    if grow: k.value=0; k.keyframe_insert('value',frame=grow[0]); k.value=1; k.keyframe_insert('value',frame=grow[1])
    else: k.value=1
    wf=ob.modifiers.new('wire','WIREFRAME'); wf.thickness=thick; ob.data.materials.append(NEON); ob['height_m']=h; return ob
box('LOT_OUTLINE',0,LW,0,LH,C['outline']['wall_h'],grow=C['outline']['wall_rise'])
hs=C.get('height_scale',1.0)
for i,B in enumerate(C['buildings']):
    u0,u1,v0,v1=B['uv']; ob=box(f'BUILDING_{i}',u0*LW,u1*LW,v0*LH,v1*LH,B['h']*hs,grow=B['grow']); ob['floors']=B['floors']
if VF is not None:
    sc.frame_set(VF); sc.cycles.samples=4; sc.render.filepath=f'{W}/blend_verify_{VF}.png'; bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT)); print('saved',OUT,'mirror',MIR)
