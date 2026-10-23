#!/usr/bin/env python3
"""export.py — يصدّر مشروع وصفة إلى ملفات قابلة للتعديل في Premiere / After Effects / Blender.
  python3 export.py <project_dir> [--target all|premiere|ae|blender]
المخرجات في <project_dir>/export/ :
  premiere.xml      FCP7 xmeml: V1=اللقطة، V2=طبقة المؤثر RGBA، A1=الصوت (File ▸ Import في Premiere)
  ae_build.jsx      سكربت After Effects: كومب + اللقطة + الطبقة + Nulls تتبع الزوايا + Corner Pin + نص عربي قابل للتعديل
  blender_build.py  سكربت Blender (stone_text): كاميرا من التتبع + نص ثلاثي الأبعاد + مادة حجر + ظل + Shadow Catcher
⚠ حالة الاختبار الصادقة: هذه الملفات وُلِّدت وفُحص تركيبها (XML صالح، JS/Python بلا أخطاء نحوية) لكنها لم تُشغَّل داخل Premiere/AE/Blender
  لأنها غير متوفرة في بيئة التطوير. صنِّفها «منفذ — غير مختبر» حتى تُجرَّب على جهاز فيه البرامج."""
import sys, os, json, argparse
from xml.sax.saxutils import escape
import numpy as np

def info(pd):
    pj = json.load(open(os.path.join(pd, 'project.json'))); ri = json.load(open(os.path.join(pd, 'renders', 'render-info.json'))); tr = json.load(open(os.path.join(pd, 'track.json'))) if os.path.exists(os.path.join(pd, 'track.json')) else None
    return pj, ri, tr

def premiere(pd, pj, ri, tr):
    W, H, fps = ri['W'], ri['H'], ri['fps']; n = ri['last'] - ri['first'] + 1; ab = os.path.abspath; plate = ab(os.path.join(pd, pj['plate'])); ov = ab(os.path.join(pd, 'renders', 'overlay.mov')); sfx = ab(os.path.join(pd, 'sfx.wav')); has_sfx = os.path.exists(sfx)
    def fileel(fid, path, name, video=True, audio=False, dur=n):
        return f'<file id="{fid}"><name>{escape(name)}</name><pathurl>file://localhost{escape(path)}</pathurl><rate><timebase>{int(fps)}</timebase><ntsc>FALSE</ntsc></rate><duration>{dur}</duration><media>' + (f'<video><samplecharacteristics><rate><timebase>{int(fps)}</timebase></rate><width>{W}</width><height>{H}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></video>' if video else '') + ('<audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio>' if audio else '') + '</media></file>'
    def clip(cid, name, fid, f, end, file_xml):
        return f'<clipitem id="{cid}"><name>{escape(name)}</name><duration>{n}</duration><rate><timebase>{int(fps)}</timebase></rate><start>0</start><end>{end}</end><in>0</in><out>{end}</out>{file_xml}</clipitem>'
    v1 = clip('c1', 'plate', 'f1', 0, n, fileel('f1', plate, 'plate.mp4')); v2 = clip('c2', f'AMX {pj["recipe"]} (RGBA)', 'f2', 0, n, fileel('f2', ov, 'overlay.mov'))
    a1 = (f'<audio><track>' + clip('c3', 'sfx', 'f3', 0, n, fileel('f3', sfx, 'sfx.wav', video=False, audio=True)) + '</track></audio>') if has_sfx else '<audio></audio>'
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4"><sequence id="seq1"><name>AMX_{escape(pj["recipe"])}</name><duration>{n}</duration><rate><timebase>{int(fps)}</timebase><ntsc>FALSE</ntsc></rate>
<media><video><format><samplecharacteristics><rate><timebase>{int(fps)}</timebase></rate><width>{W}</width><height>{H}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>
<track>{v1}</track><track>{v2}</track></video>{a1}</media></sequence></xmeml>'''
    os.makedirs(os.path.join(pd, 'export'), exist_ok=True); open(os.path.join(pd, 'export', 'premiere.xml'), 'w', encoding='utf-8').write(xml); return 'premiere.xml'

def ae(pd, pj, ri, tr):
    W, H, fps = ri['W'], ri['H'], ri['fps']; dur = (ri['last'] - ri['first'] + 1) / fps; ab = os.path.abspath(pd).replace('\\', '/'); P = pj.get('params', {})
    txt = ''.join((b.get('lines') or [''])[0] for b in P.get('beats', [])[:1]) if pj['recipe'] == 'stone_text' else ''
    corners = ''
    if tr:
        names = ['TL', 'TR', 'BR', 'BL']; frames = tr['frames']
        corners = 'var T=' + json.dumps([[f['corners'][k] for f in frames] for k in range(4)]) + ';\n' + f'''
var nulls=[];for(var k=0;k<4;k++){{var nl=comp.layers.addNull(dur);nl.name=["TL","TR","BR","BL"][k];var pos=nl.property("Position");
 var times=[],vals=[];for(var i=0;i<T[k].length;i++){{times.push(i/{fps});vals.push([T[k][i][0],T[k][i][1]]);}}pos.setValuesAtTimes(times,vals);nulls.push(nl);}}
// Corner Pin على Solid: اربط Upper/Lower بالـNulls (Expression) ليلتصق أي عنصر 2D بالمستوى المتتبَّع
var cp=comp.layers.addSolid([0.1,0.8,1],"CornerPin_Target",{W},{H},1,dur);cp.guideLayer=false;var fx=cp.property("Effects").addProperty("ADBE Corner Pin");
fx.property("Upper Left").expression='thisComp.layer("TL").transform.position';fx.property("Upper Right").expression='thisComp.layer("TR").transform.position';fx.property("Lower Right").expression='thisComp.layer("BR").transform.position';fx.property("Lower Left").expression='thisComp.layer("BL").transform.position';
cp.enabled=false; // أظهرها عند الحاجة، أو انقل محتواك داخل Pre-comp مطبَّق عليه نفس Corner Pin
'''
    js = f'''// AMAR Matrixel → After Effects. File ▸ Scripts ▸ Run Script File… (يتطلب تفعيل "Allow Scripts to Write Files and Access Network")
// غير مُختبر داخل AE (غير متوفر في بيئة التطوير).
app.beginUndoGroup("AMX {pj["recipe"]}");
var proj=app.project,dur={dur:.4f};var comp=proj.items.addComp("AMX_{pj["recipe"]}",{W},{H},1,dur,{fps});
function imp(p){{var f=new File(p);return proj.importFile(new ImportOptions(f));}}
var plate=imp("{ab}/{pj["plate"]}");var pl=comp.layers.add(plate);pl.name="PLATE";
var ovf=new File("{ab}/renders/overlay.mov");if(ovf.exists){{var ov=comp.layers.add(imp(ovf.fsName));ov.name="AMX_OVERLAY (baked RGBA)";}}
{corners}
{"var t=comp.layers.addText('" + txt.replace("'", "\\'") + "');t.name='EDITABLE_TEXT (Arabic)';var td=t.property('Source Text').value;td.font='Tajawal-Black';td.fontSize=" + str(int(H * .09)) + ";td.fillColor=[0.65,0.64,0.6];td.justification=ParagraphJustification.CENTER_JUSTIFY;t.property('Source Text').setValue(td);t.property('Position').setValue([" + str(W // 2) + "," + str(int(H * .55)) + "]);t.enabled=false; // نص عربي قابل للتعديل: فعّله واربطه بـCorner Pin أو استبدل به الطبقة المخبوزة" if txt else ""}
comp.openInViewer();app.endUndoGroup();
'''
    os.makedirs(os.path.join(pd, 'export'), exist_ok=True); open(os.path.join(pd, 'export', 'ae_build.jsx'), 'w', encoding='utf-8').write(js); return 'ae_build.jsx'

def blender(pd, pj, ri, tr):
    if pj['recipe'] != 'stone_text' or not tr: return None
    W, H, fps = ri['W'], ri['H'], ri['fps']; P = pj['params']; ab = os.path.abspath(pd).replace('\\', '/'); beats = P['beats']
    try:
        import arabic_reshaper; from bidi.algorithm import get_display
        shaped = [[get_display(arabic_reshaper.reshape(l)) for l in b['lines']] for b in beats]; sh_note = 'مُشكَّل مسبقاً (arabic_reshaper+bidi) لأن مجسمات Blender لا تشكّل العربية'
    except Exception: shaped = [b['lines'] for b in beats]; sh_note = 'تحذير: arabic_reshaper غير مثبّت — النص قد يظهر بحروف منفصلة'
    cams = []
    for f in tr['frames']:
        R = np.array(f['R']).reshape(3, 3); t = np.array(f['t']); R3 = R @ np.diag([1, -1, -1]); v = np.eye(4); v[:3, :3] = R3; v[:3, 3] = t
        M = np.diag([1, -1, -1, 1]) @ v; cams.append(np.linalg.inv(M).flatten().tolist())   # camera→world بقاعدة three/Blender (تنظر −Z)
    pl = tr['plane']
    py = f'''# AMAR Matrixel → Blender {pj["recipe"]} — Scripting ▸ Run Script. غير مُختبر داخل Blender (غير متوفر في بيئة التطوير).
# {sh_note}
import bpy, math, mathutils
sc=bpy.context.scene; sc.render.resolution_x={W}; sc.render.resolution_y={H}; sc.render.fps={int(fps)}; sc.frame_start=0; sc.frame_end={len(cams) - 1}
sc.render.engine='CYCLES'; sc.render.film_transparent=True; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGBA'
cam_data=bpy.data.cameras.new('AMX_cam'); cam_data.sensor_fit='VERTICAL'; cam_data.angle_y=math.radians({tr["fov_deg"]}); cam=bpy.data.objects.new('AMX_cam',cam_data); sc.collection.objects.link(cam); sc.camera=cam
M={json.dumps(cams)}
for i,m in enumerate(M):
    cam.matrix_world=mathutils.Matrix([m[0:4],m[4:8],m[8:12],m[12:16]]); cam.keyframe_insert('location',frame=i); cam.keyframe_insert('rotation_euler',frame=i)
# أرضية Shadow Catcher (مستوى القطعة)
bpy.ops.mesh.primitive_plane_add(size=400); gr=bpy.context.object; gr.name='GROUND_catcher'; gr.is_shadow_catcher=True
sun=bpy.data.lights.new('sun','SUN'); sun.energy=4; so=bpy.data.objects.new('sun',sun); so.rotation_euler=(math.radians(55),0,math.radians(-35)); sc.collection.objects.link(so)
mat=bpy.data.materials.new('STONE'); mat.use_nodes=True; nt=mat.node_tree; bsdf=nt.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value=0.93
n1=nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value=6; n1.inputs['Detail'].default_value=12; ramp=nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(0.30,0.30,0.29,1); ramp.color_ramp.elements[1].color=(0.65,0.64,0.60,1)
bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=0.6; nt.links.new(n1.outputs['Fac'],ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'],bsdf.inputs['Base Color']); nt.links.new(n1.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
BEATS={json.dumps([{'lines': s, 't0': b.get('t0', .3), 'rise': b.get('rise', 1.5), 'hold': b.get('hold', 1.6), 'sink': b.get('sink', .9), 'size': b.get('size', .78), 'anchor': b.get('anchor', [0, -.12])} for s, b in zip(shaped, beats)], ensure_ascii=False)}
PW,PL={pl["w"]},{pl["l"]}
for b in BEATS:
    bpy.ops.object.text_add(); t=bpy.context.object; t.data.body='\\n'.join(b['lines']); t.data.align_x='CENTER'; t.data.extrude=0.35; t.data.bevel_depth=0.03; t.data.bevel_resolution=2
    # ⚠ اختر خطاً عربياً من Properties ▸ Font (مثل Tajawal-Black.ttf) وإلا تظهر مربعات
    t.data.size=PL*0.12; t.data.materials.append(mat); t.rotation_euler=(math.radians(90),0,0); t.location=(b['anchor'][0]*PW,b['anchor'][1]*PL,0)
    z0=-PL*0.14; t.location.z=z0; t.keyframe_insert('location',frame=int(b['t0']*{fps})); t.location.z=0; t.keyframe_insert('location',frame=int((b['t0']+b['rise'])*{fps}))
    t.location.z=0; t.keyframe_insert('location',frame=int((b['t0']+b['rise']+b['hold'])*{fps})); t.location.z=z0; t.keyframe_insert('location',frame=int((b['t0']+b['rise']+b['hold']+b['sink'])*{fps}))
# الغبار: أضف Volume/Particles يدوياً عند نقطة base (انظر stone_text.js للمعاملات: عدد≈150، حجم≈0.9–1.9×ارتفاع النص)
print('AMX scene built. Render ▸ Render Animation (PNG RGBA).')
'''
    os.makedirs(os.path.join(pd, 'export'), exist_ok=True); open(os.path.join(pd, 'export', 'blender_build.py'), 'w', encoding='utf-8').write(py); return 'blender_build.py'

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('proj'); ap.add_argument('--target', default='all'); a = ap.parse_args(); pj, ri, tr = info(a.proj); out = []
    if a.target in ('all', 'premiere'): out.append(premiere(a.proj, pj, ri, tr))
    if a.target in ('all', 'ae'): out.append(ae(a.proj, pj, ri, tr))
    if a.target in ('all', 'blender'): out.append(blender(a.proj, pj, ri, tr))
    print('✓ export:', [o for o in out if o])
if __name__ == '__main__': main()
