"""glyphs.py — نص عربي مُشكَّل (HarfBuzz) → كنتورات مسطّحة للخط (fontTools) لبناء مجسم Blender حقيقي بأي خط.
   outlines(text, font_path, wght=900) -> (contours, width, height)  ؛ contours: قائمة مضلعات [(x,y),...] بوحدة em (y لأعلى) مع اتجاه TrueType."""
import uharfbuzz as hb, io, os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.recordingPen import DecomposingRecordingPen
_cache={}
def _font(path,wght):
    k=(path,wght)
    if k in _cache: return _cache[k]
    tt=TTFont(path)
    if 'fvar' in tt and wght is not None:
        axes={a.axisTag:(min(max(wght,a.minValue),a.maxValue)) for a in tt['fvar'].axes if a.axisTag=='wght'}
        tt=instancer.instantiateVariableFont(tt,axes,inplace=False)
    buf=io.BytesIO(); tt.save(buf); data=buf.getvalue(); tt=TTFont(io.BytesIO(data))
    face=hb.Face(hb.Blob(data)); f=hb.Font(face); _cache[k]=(tt,f,face.upem); return _cache[k]
def _flat_quad(p0,p1,p2,n=6): return [((1-t)**2*p0[0]+2*(1-t)*t*p1[0]+t*t*p2[0],(1-t)**2*p0[1]+2*(1-t)*t*p1[1]+t*t*p2[1]) for t in [i/n for i in range(1,n+1)]]
def outlines(text,font_path,wght=900,rtl=None,lang='ar',script='Arab',n_curve=6,tracking=1.0):
    tt,font,upem=_font(font_path,wght); gs=tt.getGlyphSet(); order=tt.getGlyphOrder()
    if rtl is None: rtl=any('؀'<=c<='ۿ' for c in text)
    buf=hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    if rtl: buf.direction='rtl'; buf.script=script; buf.language=lang
    hb.shape(font,buf,{'kern':True,'liga':True,'calt':True,'rlig':True,'init':True,'medi':True,'fina':True,'isol':True})
    x=0; contours=[]
    for info,pos in zip(buf.glyph_infos,buf.glyph_positions):
        name=order[info.codepoint]; pen=DecomposingRecordingPen(gs); gs[name].draw(pen); cur=[]; start=None
        ox=x+pos.x_offset; oy=pos.y_offset
        def P(p): return ((p[0]+ox)/upem,(p[1]+oy)/upem)
        for op,args in pen.value:
            if op=='moveTo': cur=[P(args[0])]; last=args[0]
            elif op=='lineTo': cur.append(P(args[0])); last=args[0]
            elif op=='qCurveTo':
                pts=list(args); 
                if pts[-1] is None: pts=pts[:-1]
                # تفكيك مقاطع TrueType الضمنية
                offs=pts[:-1]; end=pts[-1]; segs=[]
                for i,c in enumerate(offs):
                    nxt=end if i==len(offs)-1 else ((c[0]+offs[i+1][0])/2,(c[1]+offs[i+1][1])/2); segs.append((c,nxt))
                for c,e in segs:
                    for q in _flat_quad(last,c,e,n_curve): cur.append(P(q))
                    last=e
            elif op=='curveTo':
                c1,c2,e=args
                for i in range(1,n_curve+1):
                    t=i/n_curve; q=((1-t)**3*last[0]+3*(1-t)**2*t*c1[0]+3*(1-t)*t*t*c2[0]+t**3*e[0],(1-t)**3*last[1]+3*(1-t)**2*t*c1[1]+3*(1-t)*t*t*c2[1]+t**3*e[1]); cur.append(P(q))
                last=e
            elif op in ('closePath','endPath'):
                if len(cur)>2: contours.append(cur)
                cur=[]
        x+=pos.x_advance*tracking
    xs=[p[0] for c in contours for p in c]; ys=[p[1] for c in contours for p in c]
    return contours,(min(xs),max(xs)),(min(ys),max(ys))
def polygons(text,font_path,wght=900,tracking=1.0,condense=1.0,embolden=0.0,**kw):
    """اتحاد كنتورات الحروف (shapely) → قائمة (خارجي، [ثقوب]) بلا تداخل — لازم عند tracking<1 (تراكب الحروف)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    cs,xr,yr=outlines(text,font_path,wght,tracking=tracking,**kw)
    def area(c): return sum(c[i][0]*c[(i+1)%len(c)][1]-c[(i+1)%len(c)][0]*c[i][1] for i in range(len(c)))/2
    outers=[Polygon(c).buffer(0) for c in cs if area(c)<0]  # TrueType: الخارجي باتجاه عقارب الساعة (مساحة سالبة)
    holes=[Polygon(c).buffer(0) for c in cs if area(c)>=0]
    u=unary_union(outers)
    if holes: u=u.difference(unary_union(holes))
    from shapely import affinity
    if condense!=1.0: u=affinity.scale(u,xfact=condense,yfact=1.0,origin=(0,0))
    if embolden: u=u.buffer(embolden,join_style=1,resolution=8).buffer(-embolden*0.35,join_style=1,resolution=8)
    geoms=list(u.geoms) if hasattr(u,'geoms') else [u]
    res=[(list(g.exterior.coords)[:-1],[list(i.coords)[:-1] for i in g.interiors]) for g in geoms if g.area>1e-4]
    xs=[p[0] for e,_ in res for p in e]; ys=[p[1] for e,_ in res for p in e]
    return res,(min(xs),max(xs)),(min(ys),max(ys))
if __name__=='__main__':
    import sys
    F='/home/user/video-ad-editor/video-ad-editor/motion/fonts/NotoKufiArabic-VF.ttf'
    c,xr,yr=outlines('ارض للبيع',F); print(len(c),xr,yr)
