#!/usr/bin/env python3
"""scene_r3.py — مشهد Blender لمرجع R3 (النص الحجري). يُشغَّل بـ bpy:  /tmp/bpyenv/bin/python scene_r3.py <work> <frame> [out.png] [samples]
   الكاميرا من camera.json (إحداثيات المستوى)، أرضية Shadow Catcher، نص خرساني 3D مُشكَّل بـHarfBuzz، شمس+سماء."""
import sys,os,json,math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from bl_common import *
import numpy as np
W=sys.argv[1]; fi=int(sys.argv[2]); out=sys.argv[3] if len(sys.argv)>3 else f'{W}/render_{fi}.png'; samples=int(sys.argv[4]) if len(sys.argv)>4 else 48
CAM=json.load(open(f"{W}/{os.environ.get('AMX_CAM','camera.json')}")); cfg=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'scene_cfg.json')))
def cam_matrix(fr):
    R=np.array(fr['R']).reshape(3,3); t=np.array(fr['t']); D=np.diag([1,-1,-1.]); F=np.diag([1,-1,-1.])
    V=np.eye(4); V[:3,:3]=F@R@D; V[:3,3]=F@t; return np.linalg.inv(V)
def setup_scene(fi, text_cfg=None):
    sc=reset(); sc.render.resolution_x=CAM['width']; sc.render.resolution_y=CAM['height']; sc.render.resolution_percentage=100
    sc.view_settings.view_transform='Standard'; sc.view_settings.look='None'; sc.cycles.samples=samples; sc.cycles.use_denoising=True; sc.render.film_transparent=True; sc.cycles.film_exposure=1.0
    cam=bpy.data.cameras.new('cam'); cam.sensor_fit='HORIZONTAL'; cam.sensor_width=36; cam.lens=18/math.tan(math.radians(CAM['fov_deg'])/2); cam.clip_start=0.5; cam.clip_end=2000
    co=bpy.data.objects.new('cam',cam); sc.collection.objects.link(co); sc.camera=co; co.matrix_world=Matrix(cam_matrix(CAM['frames'][fi]).tolist())
    # أرضية Shadow Catcher
    bpy.ops.mesh.primitive_plane_add(size=1000); g=bpy.context.object; g.name='GROUND'; g.is_shadow_catcher=True
    # إضاءة: شمس + سماء
    sun=bpy.data.lights.new('sun','SUN'); sun.energy=cfg['sun_energy']; sun.angle=math.radians(cfg['sun_angle']); sun.color=cfg['sun_color']
    so=bpy.data.objects.new('sun',sun); so.rotation_euler=tuple(math.radians(a) for a in cfg['sun_rot']); sc.collection.objects.link(so)
    w=bpy.data.worlds.new('w'); w.use_nodes=True; sc.world=w; bg=w.node_tree.nodes['Background']; bg.inputs['Color'].default_value=cfg['sky_color']+[1]; bg.inputs['Strength'].default_value=cfg['sky_strength']
    return sc
def add_text(text, base_xy, height_m, width_scale=1.0, depth=0.5, face_deg=None, wght=900, name='TXT', font=None, lean_deg=0, tracking=1.0, condense=1.0, embolden=0.0):
    ob=text_object(text,height=height_m,depth=depth,bevel=cfg['bevel']*height_m,wght=wght,name=name,font=font or cfg['font'],tracking=tracking,condense=condense,embolden=embolden)
    ob.data.materials.append(concrete(base=tuple(cfg['concrete']),bump=cfg['bump'],scale=cfg['noise_scale']/height_m*4))
    ob.scale=(width_scale,1,1)
    # يقف عمودياً: المنحنى في مستوى XY ← ندوّره حول X ليقف على Z
    cam_pos=cam_matrix(CAM['frames'][fi_global])[:3,3]
    dx,dy=cam_pos[0]-base_xy[0],cam_pos[1]-base_xy[1]; yaw=math.atan2(dy,dx) if face_deg is None else math.radians(face_deg)
    ob.rotation_mode='XYZ'; ob.rotation_euler=(math.radians(90-lean_deg),0,yaw+math.pi/2); ob.location=(base_xy[0],base_xy[1],0)
    return ob
def add_text_plane(text, plane, depth_m, font=None, name='TXT', lean_deg=0, tracking=1.0):
    """يضع النص على مستوى عمودي معرَّف بنقاط الصورة (plane_from_image.py): العرض/الارتفاع بالمتر من المرجع مباشرة."""
    ob=text_object(text,height=1.0,depth=depth_m,bevel=cfg['bevel']*plane['height_m'],font=font or cfg['font'],name=name,tracking=tracking,bbox_anchor=True,size_to=(plane['width_m'],plane['height_m']),condense=plane.get('condense',1.0))
    ob.data.materials.append(concrete(base=tuple(cfg['concrete']),bump=cfg['bump'],scale=cfg['noise_scale']/plane['height_m']*4))
    yaw=plane['baseline_yaw']; ob.rotation_mode='XYZ'; ob.rotation_euler=(math.radians(90-lean_deg),0,yaw); ob.location=(plane['base_center'][0],plane['base_center'][1],0)
    return ob
def add_traced(beat, plane):
    ob=shapes_object(beat['shapes'],depth=beat.get('depth_m',1.6),bevel=beat.get('bevel_m',0.06),name='TXT_TRACED')
    ob.data.materials.append(concrete(base=tuple(cfg['concrete']),bump=cfg['bump'],scale=cfg['noise_scale']/plane['height_m']*4))
    BLw=plane['BL']; ob.rotation_mode='XYZ'; ob.rotation_euler=(math.radians(90),0,plane['baseline_yaw']); ob.location=(BLw[0],BLw[1],0)
    # x0/z0 في الصورة المعدَّلة: الأصل في المستوى = BL ؛ لا إزاحة إضافية
    return ob
fi_global=fi
if __name__=='__main__':
    sc=setup_scene(fi)
    for b in cfg['beats'][:1]:
        (add_traced(b,b['plane']) if b.get('shapes') else add_text_plane(b['text'],b['plane'],b.get('depth_m',1.8),lean_deg=b.get('lean',0)))
    import random; rnd=random.Random(3); dm=dust_material(density=cfg.get('dust_density',2.2),noise_scale=cfg.get('dust_noise',1.4))
    for k in range(cfg.get('n_puffs',26)):
        x=rnd.uniform(-16,18); y=rnd.uniform(-9,3)+ (x*0.0); z=rnd.uniform(1.0,5.5); r=rnd.uniform(3.5,7.5); add_puff((x,y,z),r,dm,squash=rnd.uniform(0.7,1.0),rot=rnd.random()*6)
    sc.render.filepath=out; bpy.ops.render.render(write_still=True); print('rendered',out)
