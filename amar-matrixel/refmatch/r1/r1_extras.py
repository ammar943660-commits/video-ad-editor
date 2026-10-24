# r1_extras.py — عناصر R1 الإضافية (تُنفَّذ داخل scene_seq.py عبر cfg['extras']): بِرك ذهب سائل، عمود/تاج سائل، قطرات ذهب على حدود القطعة، دخان الحدود.
# كل شيء دالة تحليلية للفريم fi، والإعدادات في r1_cfg.json ▸ r1.
R1C=cfg['r1']
def _ground_from_px(px,py):
    M=np.array(S.cam_matrix(CAM['frames'][int(os.environ.get('AMX_FIXCAM',0))])); w_,h_=CAM['width'],CAM['height']; fpx=(w_/2)/math.tan(math.radians(CAM['fov_deg'])/2)
    d=M[:3,:3]@np.array([(px-w_/2)/fpx,-(py-h_/2)/fpx,-1.0]); o=M[:3,3]; s=-o[2]/d[2]; return o+s*d
LOT=[_ground_from_px(x,y) for x,y in R1C['lot_px']]
def _rmp(a,b): return min(max((fi-a)/max(b-a,1e-6),0),1)
def _puddles():
    for pi_,P in enumerate(R1C['puddles']):
        a=_rmp(*P['grow'])
        if a<=0 or (P.get('end') and fi>=P['end']): continue
        c=_ground_from_px(*P['center_px']); r=P['radius_m']*(0.25+0.75*ease(a))
        bpy.ops.mesh.primitive_circle_add(vertices=48,radius=1.0,fill_type='TRIFAN',location=(c[0],c[1],0.03+0.05*pi_)); ob=bpy.context.object
        rr=random.Random(P.get('seed',1))
        for v in ob.data.vertices:
            ang=math.atan2(v.co.y,v.co.x); rad=1+0.14*math.sin(3*ang+rr.random()*6)+0.08*math.sin(7*ang+rr.random()*6)+0.03*rr.uniform(-1,1)
            v.co.x*=rad*r*P.get('aspect',1.6); v.co.y*=rad*r
        ob.rotation_euler=(0,0,P.get('yaw',0.66)); ob.data.materials.append(PUDDLE)
        import bmesh as _bm; _b=_bm.new(); _b.from_mesh(ob.data); _bm.ops.recalc_face_normals(_b,faces=_b.faces)
        for _f in _b.faces:
            if _f.normal.z<0: _f.normal_flip()
        _b.to_mesh(ob.data); _b.free()
        for pp in ob.data.polygons: pp.use_smooth=True
def _columns():
    for Cc in R1C['columns']:
        a=_rmp(Cc['f0'],Cc['f1'])
        if a<=0 or a>=1: continue
        c=_ground_from_px(*Cc['center_px']); hh=Cc['h']*math.sin(math.pi*min(a*1.25,1.0))   # يرتفع ثم يهبط
        if hh<0.3: continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=Cc['r'],depth=1.0,location=(c[0],c[1],hh/2)); ob=bpy.context.object; ob.scale=(1,1,hh)
        tx=bpy.data.textures.new('col','CLOUDS'); tx.noise_scale=0.6; md=ob.modifiers.new('ss','SUBSURF'); md.levels=2
        dm=ob.modifiers.new('d','DISPLACE'); dm.texture=tx; dm.strength=Cc['r']*0.5; ob.data.materials.append(CONC)
        for p in ob.data.polygons: p.use_smooth=True
        # تاج الرذاذ في القمة
        rr=random.Random(int(fi))
        for j in range(Cc.get('crown',8)):
            ang=j/Cc.get('crown',8)*6.283+rr.uniform(-.2,.2); rx=Cc['r']*1.5
            bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=Cc['r']*0.35,radius2=0.02,depth=Cc['r']*2.2,location=(c[0]+rx*math.cos(ang),c[1]+rx*math.sin(ang),hh+Cc['r']*0.8))
            o2=bpy.context.object; o2.rotation_euler=(0.5*math.sin(ang),-0.5*math.cos(ang),0); o2.data.materials.append(CONC)
def _droplets():
    D=R1C['droplets']; a0,a1=D['draw']; end=D['end']
    if fi<a0 or fi>=end: return
    rr=random.Random(11); n=D['n']
    for j in range(n):
        s=j/n*4; k_=int(s)%4; u=s-int(s); p=LOT[k_]+(LOT[(k_+1)%4]-LOT[k_])*u
        tb=a0+(a1-a0)*j/n+rr.uniform(0,3)   # يظهر حين يمرّ الخط
        t=(fi-tb)/30.0
        if t<0: continue
        life=D['life']*rr.uniform(0.7,1.3); fade=1-max(0,(fi-(end-15))/15)
        hgt=D['h']*rr.uniform(0.5,1.3)*min(1,t/0.3)*(0.6+0.4*abs(math.sin(t*rr.uniform(4,8)+rr.random()*6)))*fade
        if hgt<0.1: continue
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=1.0,location=(p[0],p[1],hgt*0.5)); ob=bpy.context.object
        rad=D['r']*rr.uniform(0.7,1.2); ob.scale=(rad,rad,hgt*0.5+rad*0.3); ob.data.materials.append(CONC)
    # خط ذهبي متوهج (حبل منصهر) على الحدود
    L=4*min(1,(fi-a0)/max(a1-a0,1)); pts=[LOT[0]]
    for k_ in range(4):
        if L<=k_: break
        pts.append(LOT[k_]+(LOT[(k_+1)%4]-LOT[k_])*min(L-k_,1))
    cu=bpy.data.curves.new('rope','CURVE'); cu.dimensions='3D'; cu.bevel_depth=D['rope_r']; cu.bevel_resolution=3
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for q,p in zip(sp.points,pts): q.co=(p[0],p[1],D['rope_r'],1)
    ob=bpy.data.objects.new('rope',cu); bpy.context.scene.collection.objects.link(ob); ob.data.materials.append(GLOW)
def _smoke():
    Sm=R1C['smoke']; a=(fi-Sm['f'])/30.0
    if a<0 or fi>=Sm['end']: return
    rr=random.Random(5); P=[]
    for j in range(Sm['n']):
        s=rr.uniform(0,4); k_=int(s)%4; u=s-int(s); p=LOT[k_]+(LOT[(k_+1)%4]-LOT[k_])*u
        dens=Sm['density']*min(1,a/0.6)*max(0,1-(fi-(Sm['end']-20))/20)
        if dens<0.05: continue
        P.append((p[0],p[1],rr.uniform(*Sm['z'])+a*Sm['rise'],rr.uniform(*Sm['r'])*(1+0.5*a),dens))
    if P:
        xs=[q[0] for q in P]; ys=[q[1] for q in P]; zs=[q[2] for q in P]; rm=max(q[3] for q in P)*1.2
        dust_field(P,color=tuple(Sm['color']),noise_scale=0.7,detail=6,lo=0.48,hi=0.7,domain=((min(xs)-rm,min(ys)-rm,0),(max(xs)+rm,max(ys)+rm,max(zs)+rm)),gain=Sm.get('gain',2.5),name='SMOKE')
GLOW=bpy.data.materials.new('GLOW'); GLOW.use_nodes=True; _nt=GLOW.node_tree; _e=_nt.nodes.new('ShaderNodeEmission'); _e.inputs['Color'].default_value=(1.0,0.62,0.18,1); _e.inputs['Strength'].default_value=R1C['droplets'].get('glow',12)
_nt.links.new(_e.outputs[0],_nt.nodes['Material Output'].inputs['Surface']); _nt.nodes.remove(_nt.nodes['Principled BSDF'])
PUDDLE=gold_material(name='PUDDLE',base=(1.0,0.68,0.26),rough=0.55,bump=0.3,scale=2.0)
bpy.data.objects['GROUND'].visible_glossy=False
PRE_HOOKS=[_puddles,_columns,_droplets,_smoke]
