#!/usr/bin/env python3
"""export_ae.py — يصدّر R5 كمشروع After Effects قابل للتعديل (ExtendScript .jsx):
   كومب 1146×644 @30 · plate نهار + plate ليل (Opacity مفاتيح) · كل مسار نيون كطبقة Shape مع Trim Paths متحرك + Glow · كل بطاقة: Shape لوح + نص عربي حي (Text layer) + ذيل.
   python3 export_ae.py <work> <out_dir>  → r5_ae_build.jsx + plates/*.png (تُنسخ بجانبه)"""
import json,sys,os,shutil,random
W,O=sys.argv[1:3]; D=os.path.dirname(os.path.abspath(__file__)); C=json.load(open(f'{D}/r5_cfg.json')); P=json.load(open(f'{W}/neon_paths.json'))['paths']
P=[p for p in P if not (max(q[1] for q in p)<130 and max(q[0] for q in p)<260)]
os.makedirs(f'{O}/plates',exist_ok=True); shutil.copy(f'{W}/frames/0001.png',f'{O}/plates/day.png'); shutil.copy(f'{W}/night_plate.png',f'{O}/plates/night.png')
fps=30.0; rng=random.Random(4); a0,a1=C['neon_draw']
js=['// R5 — AMAR Matrixel: مخطط نيون للواجهة + بطاقات (مولَّد آلياً؛ كل القيم قابلة للتعديل)','(function(){',
 'app.beginUndoGroup("AMX R5");','var dir=File($.fileName).parent;','var comp=app.project.items.addComp("AMX_R5",1146,644,1,%.3f,%.1f);'%((C['end_cut']+6)/fps,fps),
 'function imp(n){return app.project.importFile(new ImportOptions(File(dir.fsName+"/plates/"+n)));}',
 'var day=comp.layers.add(imp("day.png")); var night=comp.layers.add(imp("night.png"));',
 'var op=night.property("Opacity"); op.setValueAtTime(%.3f,0); op.setValueAtTime(%.3f,100); op.setValueAtTime(%.3f,100); op.setValueAtTime(%.3f,0);'%(C['day_to_night'][0]/fps,C['day_to_night'][1]/fps,(C['end_cut']-1)/fps,C['end_cut']/fps),
 'function shapeLayer(name,pts,closed,col,w){var L=comp.layers.addShape();L.name=name;var g=L.property("Contents").addProperty("ADBE Vector Group");var s=g.property("Contents").addProperty("ADBE Vector Shape - Group");var sh=new Shape();sh.vertices=pts;sh.closed=closed;s.property("Path").setValue(sh);var st=g.property("Contents").addProperty("ADBE Vector Graphic - Stroke");st.property("Color").setValue(col);st.property("Stroke Width").setValue(w);return [L,g];}',
 'function trim(g,t0,t1){var tr=g.property("Contents").addProperty("ADBE Vector Filter - Trim");tr.property("End").setValueAtTime(t0,0);tr.property("End").setValueAtTime(t1,100);}',
 'function glow(L){var e=L.property("Effects").addProperty("ADBE Glo2");e.property("Glow Radius").setValue(18);e.property("Glow Intensity").setValue(1.5);}',
 'var CY=[%.3f,%.3f,%.3f];'%tuple(c/255 for c in C['neon']['glow'][::-1])]
for i,p in enumerate(P):
    st=rng.uniform(a0,a1-8); du=rng.uniform(5,10)
    js.append('var r=shapeLayer("NEON_%02d",%s,false,CY,%.1f); trim(r[1],%.3f,%.3f); glow(r[0]);'%(i,json.dumps([[float(x),float(y)] for x,y in p]),C['neon']['width']*1.5,st/fps,(st+du)/fps))
for k,cd in enumerate(C['cards']):
    x0,y0,x1,y1=cd['box']; t0,t1=cd['appear']
    js.append('var b=shapeLayer("CARD_%d_PANEL",%s,true,CY,2); var f=b[1].property("Contents").addProperty("ADBE Vector Graphic - Fill"); f.property("Color").setValue([%.3f,%.3f,%.3f]); f.property("Opacity").setValue(%d); b[0].property("Opacity").setValueAtTime(%.3f,0); b[0].property("Opacity").setValueAtTime(%.3f,100); glow(b[0]);'
              %(k,json.dumps([[x0,y0],[x1,y0],[x1,y1],[x0,y1]]),*[c/255 for c in C['panel']['fill'][::-1]],int(C['panel']['alpha']*100),t0/fps,t1/fps))
    js.append('var l=shapeLayer("CARD_%d_LEADER",%s,false,CY,1.5); trim(l[1],%.3f,%.3f); glow(l[0]);'%(k,json.dumps(cd['leader']),(t0+4)/fps,(t1+4)/fps))
    txt=cd['text'].replace('\n','\\r')
    js.append('var T=comp.layers.addText("%s"); T.name="CARD_%d_TEXT"; var td=T.property("Source Text").value; td.fontSize=%d; td.fillColor=[1,1,1]; td.justification=ParagraphJustification.CENTER_JUSTIFY; try{td.font="Tajawal-ExtraBold";}catch(e){} T.property("Source Text").setValue(td); T.property("Position").setValue([%d,%d]); T.property("Opacity").setValueAtTime(%.3f,0); T.property("Opacity").setValueAtTime(%.3f,100);'
              %(txt,k,int(cd['text_h']*1.25),(x0+x1)//2,(y0+y1)//2+cd['text_h']//3,(t0+5)/fps,t1/fps))
js+=['app.endUndoGroup();','})();']
open(f'{O}/r5_ae_build.jsx','w',encoding='utf-8').write('\n'.join(js)); print('jsx layers: neon',len(P),'cards',len(C['cards']))
