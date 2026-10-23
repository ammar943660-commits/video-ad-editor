"""bl_common.py — أدوات Blender المشتركة لمطابقة المراجع (تعمل بـ bpy داخل venv بايثون 3.11)."""
import bpy, bmesh, math, sys, os, json
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(__file__))
FONT='/home/user/video-ad-editor/video-ad-editor/motion/fonts/NotoKufiArabic-VF.ttf'
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.device='CPU'; return sc
def text_object(text, height=1.0, depth=0.35, bevel=0.035, wght=900, font=FONT, name='TXT', bevel_seg=4, line_gap=1.25, tracking=1.0, condense=1.0, embolden=0.0, bbox_anchor=False, size_to=None):
    """نص عربي مُشكَّل → Curve مبثوق (اتحاد الكنتورات بلا تداخل). height بالمتر لوحدة em؛ القاعدة y=0، المركز x=0."""
    from glyphs import polygons
    lines=text.split('\n'); infos=[polygons(l,font,wght,tracking=tracking,condense=condense,embolden=embolden) for l in lines]
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='2D'; cu.fill_mode='BOTH'; cu.extrude=depth/2; cu.bevel_depth=bevel; cu.bevel_resolution=bevel_seg; cu.resolution_u=2
    ybot=min(i[2][0] for i in infos)-line_gap*(len(infos)-1)
    off_y=0
    if size_to:  # (width_m,height_m): يضبط height وcondense لمطابقة صندوق النص بالمتر
        xr0=min(i[1][0] for i in infos); xr1=max(i[1][1] for i in infos); yr0=min(i[2][0] for i in infos)-line_gap*(len(infos)-1); yr1=max(i[2][1] for i in infos)
        height=size_to[1]/(yr1-yr0); condense_eff=size_to[0]/((xr1-xr0)*height*condense); 
    for li,(polys,xr,yr) in enumerate(infos):
        cx=(xr[0]+xr[1])/2
        for ext,holes in polys:
            for ring in [ext]+holes:
                sp=cu.splines.new('POLY'); sp.points.add(len(ring)-1); sp.use_cyclic_u=True
                for p,(px,py) in zip(sp.points,ring): p.co=((px-cx)*height*(condense_eff if size_to else 1.0),(py+off_y-(ybot if bbox_anchor else 0))*height,0,1)
        off_y-=line_gap
    ob=bpy.data.objects.new(name,cu); bpy.context.scene.collection.objects.link(ob); return ob
def concrete(name='CONCRETE', base=(0.56,0.55,0.53), rough=0.9, bump=0.5, scale=12.0):
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); bs=nt.nodes.new('ShaderNodeBsdfPrincipled'); bs.inputs['Roughness'].default_value=rough
    tc=nt.nodes.new('ShaderNodeTexCoord'); mp=nt.nodes.new('ShaderNodeMapping')
    n1=nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value=scale; n1.inputs['Detail'].default_value=10; n1.inputs['Roughness'].default_value=0.65
    n2=nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value=scale*9; n2.inputs['Detail'].default_value=6
    vo=nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value=scale*5; vo.feature='DISTANCE_TO_EDGE'
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(base[0]*.62,base[1]*.62,base[2]*.6,1); ramp.color_ramp.elements[1].color=(base[0]*1.12,base[1]*1.12,base[2]*1.1,1)
    mix=nt.nodes.new('ShaderNodeMath'); mix.operation='ADD'; mix.inputs[1].default_value=0.0
    mul=nt.nodes.new('ShaderNodeMix'); mul.data_type='FLOAT'; mul.inputs[0].default_value=0.35
    bp=nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value=bump; bp.inputs['Distance'].default_value=0.02
    L=nt.links; L.new(tc.outputs['Object'],mp.inputs['Vector']); 
    for n in (n1,n2,vo): L.new(mp.outputs['Vector'],n.inputs['Vector'])
    L.new(n1.outputs['Fac'],ramp.inputs['Fac']); L.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    h=nt.nodes.new('ShaderNodeMath'); h.operation='MULTIPLY_ADD'; L.new(n1.outputs['Fac'],h.inputs[0]); h.inputs[1].default_value=0.6; L.new(n2.outputs['Fac'],h.inputs[2])
    L.new(h.outputs['Value'],bp.inputs['Height']); L.new(bp.outputs['Normal'],bs.inputs['Normal']); L.new(bs.outputs['BSDF'],out.inputs['Surface']); return m

def dust_material(name='DUST', color=(0.60,0.56,0.50), density=1.6, noise_scale=1.6, detail=8.0, seed=0.0):
    """سحابة غبار حجمية: كثافة = ضوضاء 3D × سقوط شعاعي (بلا حواف حادة). تُوضع على كرات متعددة التقسيم."""
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear(); L=nt.links
    out=nt.nodes.new('ShaderNodeOutputMaterial'); vs=nt.nodes.new('ShaderNodeVolumeScatter'); ab=nt.nodes.new('ShaderNodeVolumeAbsorption'); ad=nt.nodes.new('ShaderNodeAddShader')
    tc=nt.nodes.new('ShaderNodeTexCoord'); mp=nt.nodes.new('ShaderNodeMapping'); mp.inputs['Location'].default_value=(seed,seed*0.7,seed*0.3)
    n1=nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value=noise_scale; n1.inputs['Detail'].default_value=detail; n1.inputs['Roughness'].default_value=0.62; n1.noise_dimensions='3D'
    sep=nt.nodes.new('ShaderNodeVectorMath'); sep.operation='LENGTH'; 
    gen=nt.nodes.new('ShaderNodeTexCoord')
    # سقوط شعاعي: 1 - |object coord| (كرة وحدة)
    rad=nt.nodes.new('ShaderNodeMath'); rad.operation='SUBTRACT'; rad.inputs[0].default_value=1.0
    rmap=nt.nodes.new('ShaderNodeMapRange'); rmap.inputs[1].default_value=0.0; rmap.inputs[2].default_value=0.75; rmap.inputs[3].default_value=0.0; rmap.inputs[4].default_value=1.0; rmap.clamp=True
    nmap=nt.nodes.new('ShaderNodeMapRange'); nmap.inputs[1].default_value=0.38; nmap.inputs[2].default_value=0.78; nmap.inputs[3].default_value=0.0; nmap.inputs[4].default_value=1.0; nmap.clamp=True
    mul=nt.nodes.new('ShaderNodeMath'); mul.operation='MULTIPLY'; dens=nt.nodes.new('ShaderNodeMath'); dens.operation='MULTIPLY'; dens.inputs[1].default_value=density
    L.new(tc.outputs['Object'],mp.inputs['Vector']); L.new(mp.outputs['Vector'],n1.inputs['Vector']); L.new(gen.outputs['Object'],sep.inputs[0]); L.new(sep.outputs['Value'],rad.inputs[1]); L.new(rad.outputs['Value'],rmap.inputs['Value'])
    L.new(n1.outputs['Fac'],nmap.inputs['Value']); L.new(nmap.outputs['Result'],mul.inputs[0]); L.new(rmap.outputs['Result'],mul.inputs[1]); L.new(mul.outputs['Value'],dens.inputs[0])
    for n in (vs,ab): L.new(dens.outputs['Value'],n.inputs['Density'])
    vs.inputs['Color'].default_value=color+(1,); ab.inputs['Color'].default_value=(color[0]*0.8,color[1]*0.78,color[2]*0.74,1); vs.inputs['Anisotropy'].default_value=0.2
    L.new(vs.outputs['Volume'],ad.inputs[0]); L.new(ab.outputs['Volume'],ad.inputs[1]); L.new(ad.outputs['Shader'],out.inputs['Volume']); return m
def add_puff(center, radius, mat, squash=0.8, rot=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=1.0,location=center); ob=bpy.context.object; ob.scale=(radius,radius,radius*squash); ob.rotation_euler=(0,0,rot)
    ob.data.materials.append(mat); ob.visible_shadow=True; return ob

def shapes_object(shapes_json, depth=1.6, bevel=0.05, smooth=0.03, name='TXT_TRACED', bevel_seg=3):
    """مجسم من صور ظلّية مرسومة/متتبَّعة (glyph_ws.py): إحداثيات بالمتر على مستوى النص (x على امتداد القاعدة، y للأعلى). تنعيم بـshapely."""
    import json
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    d=json.load(open(shapes_json)); polys=[]
    for sh in d['shapes']:
        p=Polygon(sh['outer'],[h for h in sh['holes'] if len(h)>=3]).buffer(0)
        if not p.is_empty: polys.append(p)
    u=unary_union(polys)
    if smooth>0: u=u.buffer(smooth,join_style=1).buffer(-smooth,join_style=1)  # إغلاق صغير فقط (يحفظ الثقوب والأجزاء الدقيقة)
    u=u.simplify(0.02)
    geoms=list(u.geoms) if hasattr(u,'geoms') else [u]
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='2D'; cu.fill_mode='BOTH'; cu.extrude=depth/2; cu.bevel_depth=bevel; cu.bevel_resolution=bevel_seg; cu.resolution_u=2
    for g in geoms:
        for ring in [list(g.exterior.coords)[:-1]]+[list(i.coords)[:-1] for i in g.interiors]:
            sp=cu.splines.new('POLY'); sp.points.add(len(ring)-1); sp.use_cyclic_u=True
            for pt,(x,y) in zip(sp.points,ring): pt.co=(x,y,0,1)
    ob=bpy.data.objects.new(name,cu); bpy.context.scene.collection.objects.link(ob); return ob

def billow_material(name='BILLOW', color=(0.80,0.72,0.62), edge=0.55, noise_scale=3.0):
    """غبار سطحي «قرنبيط» (بدل الحجم): ديفيوز فاتح مع شفافية ناعمة عند الحواف (Layer Weight) وتدرّج ضوضاء. أسرع بكثير من الحجم."""
    m=bpy.data.materials.new(name); m.use_nodes=True; nt=m.node_tree; nt.nodes.clear(); L=nt.links
    out=nt.nodes.new('ShaderNodeOutputMaterial'); mixs=nt.nodes.new('ShaderNodeMixShader'); tr=nt.nodes.new('ShaderNodeBsdfTransparent'); df=nt.nodes.new('ShaderNodeBsdfDiffuse')
    lw=nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value=edge
    tc=nt.nodes.new('ShaderNodeTexCoord'); n1=nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value=noise_scale; n1.inputs['Detail'].default_value=8
    ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(color[0]*.55,color[1]*.52,color[2]*.48,1); ramp.color_ramp.elements[1].color=color+(1,)
    mr=nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value=0.25; mr.inputs[2].default_value=0.9; mr.inputs[3].default_value=0.0; mr.inputs[4].default_value=1.0; mr.clamp=True
    L.new(tc.outputs['Object'],n1.inputs['Vector']); L.new(n1.outputs['Fac'],ramp.inputs['Fac']); L.new(ramp.outputs['Color'],df.inputs['Color'])
    L.new(lw.outputs['Facing'],mr.inputs['Value']); L.new(mr.outputs['Result'],mixs.inputs['Fac'])   # facing=1 في المنتصف → 0 شفافية؛ الحواف → 1
    L.new(df.outputs['BSDF'],mixs.inputs[1]); L.new(tr.outputs['BSDF'],mixs.inputs[2]); L.new(mixs.outputs['Shader'],out.inputs['Surface']); return m

def add_billow(center, radius, mat, seed=0, subdiv=4, disp=0.55, tex_scale=2.4, squash=0.85):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv,radius=1.0,location=center); ob=bpy.context.object; ob.scale=(radius,radius,radius*squash)
    tx=bpy.data.textures.new('bt%d'%seed,'CLOUDS'); tx.noise_scale=1.0/tex_scale; tx.noise_depth=4; 
    md=ob.modifiers.new('d','DISPLACE'); md.texture=tx; md.strength=disp; md.mid_level=0.4
    ob.rotation_euler=(seed*0.7,seed*1.3,seed*2.1); ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth=True
    return ob
