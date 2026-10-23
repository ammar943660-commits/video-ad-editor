#!/usr/bin/env python3
"""scene_seq.py — مشهد R3 الكامل لفريم واحد: توالي أربع جمل (تجمّع الشظايا ← نص كامل ← انفجار ← ركام باقٍ) + غبار حدثي + أرضية Shadow Catcher.
   AMX_CAM=camera_true.json /tmp/bpyenv/bin/python scene_seq.py <work> <frame> <out.png> [samples]
   كل الحالات دالة تحليلية للفريم (بلا كاش/محاكاة)، فيُرسم أي فريم مستقلاً. ملاحظة: إحداثيات الشظايا من fracture.py (pieces JSON)."""
import sys,os,json,math,random
import numpy as np
import scene_r3 as S
from bl_common import *
from mathutils import Euler,Quaternion,Matrix,Vector
W=S.W; fi=S.fi; out=S.out; samples=S.samples; cfg=S.cfg; CAM=S.CAM; seq=cfg['seq']; FPS=30.0
sc=S.setup_scene(fi)
if os.environ.get('AMX_NOGROUND'): bpy.data.objects['GROUND'].hide_render=True
CONC=concrete(base=tuple(cfg['concrete']),bump=cfg['bump'],scale=cfg['noise_scale']/9*4)
CONCD=concrete(base=tuple(c*0.42 for c in cfg['concrete']),bump=cfg['bump']*1.4,scale=cfg['noise_scale']/9*4)
ease=lambda v:1-(1-min(max(v,0),1))**3
def plane_xf(b):
    pl=b['plane']; C=S.cam_matrix(CAM['frames'][b['ref_frame']])[:3,3]; zc=b.get('zc',0.0); k=C[2]/(C[2]-zc)
    BL=np.array(pl['BL'],float); loc=C+k*(BL-C); yaw=pl['baseline_yaw']
    return loc,k,Matrix(Euler((math.pi/2,0,yaw)).to_matrix())
def piece_depth(b,rn): return b['depth_m']*(0.9+0.5*rn)
objs=[]
def add_piece(P,b,loc,k,Rp,i,f,rnd):
    cx,cy=P['cx'],P['cy']; rest=Vector(loc)+Rp@Vector((k*cx,k*cy,0)); rq=Rp.to_quaternion()
    tf0,tf1=b['form']; ex=b.get('explode'); dly=rnd.random()*0.5; q_sc=Quaternion((rnd.gauss(0,1),rnd.gauss(0,1),rnd.gauss(0,1),rnd.gauss(0,1))).normalized()
    off=Vector((rnd.uniform(-1,1)*b['scatter'][0],rnd.uniform(-1,1)*b['scatter'][1],rnd.uniform(0.2,1)*b['scatter'][2])); rn=rnd.random(); th=piece_depth(b,rn)*k
    ang=rnd.uniform(0,2*math.pi); sp=rnd.uniform(*b['speed']); vup=rnd.uniform(*b['up']); spin=Vector((rnd.gauss(0,1),rnd.gauss(0,1),rnd.gauss(0,1)))*rnd.uniform(0.5,3.0)
    cen=Vector(loc)+Rp@Vector((k*b['centre'][0],k*b['centre'][1],0)); away=(rest-cen); away.z=0; away=away.normalized() if away.length>1e-6 else Vector((1,0,0))
    hv=(away*0.7+Vector((math.cos(ang),math.sin(ang),0))*0.5).normalized()*sp
    pos=None; rot=rq; scl=1.0
    tf2=b.get('settle',tf1)
    jit=Vector((rnd.gauss(0,0.5),rnd.gauss(0,0.5),rnd.gauss(0,0.4))); q_j=Quaternion(Vector((rnd.gauss(0,1),rnd.gauss(0,1),rnd.gauss(0,1))).normalized(),rnd.uniform(0.05,0.25))
    cmp_=0.78+0.22*ease((f-tf0)/max(tf2-tf0,1)) if f<tf2 else 1.0
    if f<tf2: rest=cen+(rest-cen)*Vector((cmp_,cmp_,1.0))
    if f<tf0: return None
    if f<tf1:
        u=(f-tf0)/(tf1-tf0); v=min(max((u-dly)/(1-0.5),0),1); e=ease(v)
        pos=(rest+off)*(1-e)+(rest+jit)*e; rot=q_sc.slerp(q_j@rq,e); scl=0.5+0.5*e
        if v<=0: pos=rest+off; scl=0.5
    elif f<tf2:
        e=ease((f-tf1)/max(tf2-tf1,1)); pos=rest+jit*(1-e); rot=(q_j@rq).slerp(rq,e); scl=1.0
    elif ex is None or f<ex[0]: return None   # النص الكامل يظهر (كائن آخر)
    else:
        t=(f-ex[0])/FPS-dly*0.3*0
        t=max(t-dly*0.35,0.0); g=9.8*b.get('gscale',1.0)
        # محاكاة تحليلية بخطوات: ارتداد واحد ثم استقرار
        vel=Vector((hv.x,hv.y,vup)); p=rest.copy(); tt=0.0; dt=1/FPS; landed=False; zl=th*0.45
        n=int(t*FPS)
        for s_ in range(n):
            vel.z-=g*dt; p=p+vel*dt
            if p.z<=zl:
                if abs(vel.z)>3.0 and not landed: p.z=zl; vel.z*=-0.28; vel.x*=0.6; vel.y*=0.6; landed=True
                else: p.z=zl; vel=Vector((0,0,0)); landed=True; break
        pos=p; ts=min(t,3.0)
        if vel.length<1e-3 and p.z<=zl+1e-3:
            tilt=Quaternion(Vector((rnd.gauss(0,1),rnd.gauss(0,1),0)).normalized() if True else Vector((1,0,0)),rnd.uniform(0,0.35)); yawq=Quaternion((0,0,1),rnd.uniform(0,6.28))
            rot=yawq@tilt   # مسطّح على الأرض (محور البثق عمودي)
            # أعد ربط مدارات الاستقرار بالحالة المقذوفة: استقرار تدريجي عبر slerp قصير
        else:
            sq=Quaternion(spin.normalized(),spin.length*ts); rot=sq@rq
    return pos,rot,scl,th
mats_dust={}
def dust_mat(d,seed):
    key=(round(d*4)/4,int(seed)%3)
    if key not in mats_dust: mats_dust[key]=dust_material(color=tuple(seq['dust']['color']),density=max(key[0],0.15),noise_scale=seq['dust'].get('noise',1.5),seed=key[1]*3.7)
    return mats_dust[key]
def build():
    rr=random.Random(seq.get('seed',7)); depth_total=0
    for bi,b in enumerate(cfg['beats'][:4]):
        loc,k,Rp=plane_xf(b); PJ=json.load(open(b['pieces'])); tf0,tf1=b['form']; ex=b.get('explode')
        if b.get('settle',tf1)<=fi and (ex is None or fi<ex[0]):   # نص كامل
            ob=parts_object(PJ['whole'],depth=b['depth_m'],bevel=b.get('bevel_m',0.08),name=f'WHOLE{bi}'); ob.data.materials.append(CONC)
            ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=Rp.to_quaternion(); ob.location=Vector(loc); ob.scale=(k,k,k); continue
        if fi<tf0: continue
        for i,P in enumerate(PJ['pieces']):
            rnd=random.Random(bi*100003+i*7919+seq.get('seed',7))
            r=add_piece(P,b,loc,k,Rp,i,fi,rnd)
            if r is None: continue
            pos,rot,scl,th=r
            ob=parts_object([{'outer':P['outer'],'holes':P['holes']}],depth=th/k,bevel=b.get('bevel_m',0.08)*0.8,name=f'P{bi}_{i}'); ob.data.materials.append(CONCD)
            ob.rotation_mode='QUATERNION'; ob.rotation_quaternion=rot; ob.location=pos; ob.scale=(k*scl,)*3
def dust():
    D=seq['dust']
    for ei,e in enumerate(seq['events']):
        a=(fi-e['f'])/FPS
        if a<0: continue
        b=cfg['beats'][e['beat']]; loc,k,Rp=plane_xf(b); rr=random.Random(e.get('seed',1)*977+ei)
        Wm=b['plane']['width_m']*k
        for j in range(e['n']):
            u=rr.uniform(*e.get('u',(0,1)))*Wm; v=rr.uniform(*e['v']); z0=rr.uniform(*e['z']); r0=rr.uniform(*e['r']); sp=rr.uniform(0.3,1.0)*e.get('spread',3.0); vz=rr.uniform(0.2,1.0)*e.get('rise',2.0); ph=rr.uniform(0,6.28)
            base=Vector(loc)+Rp@Vector((u,0,0))+Vector((0,0,0)); nx=-(Rp@Vector((0,0,1))).normalized()   # عمودي المستوى
            c=base+nx*v; c.z=0
            pos=c+Vector((math.cos(ph),math.sin(ph),0))*sp*a**0.8+Vector((0,0,z0+vz*a**0.6)); r=r0*(1+e.get('grow',0.7)*math.sqrt(a))
            dens=e['density']*math.exp(-a/e['tau'])*min(1.0,a/0.12+0.15)
            if dens<0.12: continue
            add_puff((pos.x,pos.y,pos.z),r,dust_mat(dens,j),squash=rr.uniform(0.7,1.0),rot=rr.random()*6)
def rocks():
    R=seq.get('rocks',{})
    for bi,b in enumerate(cfg['beats'][:4]):
        t0=b['form'][0]
        if fi<t0: continue
        loc,k,Rp=plane_xf(b); Wm=b['plane']['width_m']*k; nx=-(Rp@Vector((0,0,1))).normalized(); ux=Rp@Vector((1,0,0))
        rr=random.Random(bi*7777+3)
        for j in range(R.get('n',70)):
            u=rr.uniform(0,1)*Wm; v=rr.uniform(*R.get('v',(-5,2))); sz=rr.uniform(*R.get('size',(0.4,1.4)))*(1+0.8*rr.random()**3); dly=rr.uniform(0,0.4)
            e=ease(((fi-t0)/FPS-dly)/0.35); 
            if e<=0: continue
            base=Vector(loc)+ux*u+nx*v; z=sz*0.4+(1-e)*9
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1.0,location=(base.x,base.y,z)); ob=bpy.context.object
            ob.scale=(sz*rr.uniform(0.7,1.3),sz*rr.uniform(0.7,1.3),sz*rr.uniform(0.45,0.9)); ob.rotation_euler=(rr.uniform(-.4,.4),rr.uniform(-.4,.4),rr.uniform(0,6.28)); ob.data.materials.append(CONCD)
            for p in ob.data.polygons: p.use_smooth=False
build(); rocks(); dust()
sc.cycles.volume_bounces=3; sc.cycles.volume_step_rate=2.0; sc.cycles.volume_preview_step_rate=2.0; sc.cycles.volume_max_steps=64
sc.render.filepath=out; bpy.ops.render.render(write_still=True); print('rendered',out,'frame',fi)
