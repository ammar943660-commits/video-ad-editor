#!/usr/bin/env python3
"""glyph_poly.py — يحوّل مضلعات الحروف المرسومة يدوياً (بكسل الصورة المعدَّلة) إلى shapes.json بالمتر + معاينة فوق المرجع.
   python3 glyph_poly.py <work> glyphs/x_poly.json out_prefix"""
import sys,json,cv2,numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
from shapely import affinity
W,gj,outp=sys.argv[1:4]; G=json.load(open(gj)); R=json.load(open(f"{W}/{G['rect']}_rect.json")); im=cv2.imread(f"{W}/{G['image']}")
def chaik(p,n):
    p=[tuple(q) for q in p]
    for _ in range(n):
        o=[]
        for i in range(len(p)):
            a,b=p[i],p[(i+1)%len(p)]
            o+= [(.75*a[0]+.25*b[0],.75*a[1]+.25*b[1]),(.25*a[0]+.75*b[0],.25*a[1]+.75*b[1])]
        p=o
    return p
def mk(s):
    if 'ellipse' in s: cx,cy,rx,ry=s['ellipse']; return affinity.scale(Point(cx,cy).buffer(1,resolution=24),rx,ry)
    n=s.get('smooth',0)
    return Polygon(chaik(s['pts'],n),[chaik(h,n) for h in s.get('holes',[])]).buffer(0)
U=unary_union([mk(s) for s in G['add']])
if G.get('erase'): U=U.difference(unary_union([mk(s) for s in G['erase']]))
def tom(c): return [(R['x0']+x/R['wpx']*(R['x1']-R['x0']), R['z1']-y/R['hpx']*(R['z1']-R['z0'])) for x,y in c]
geoms=list(U.geoms) if hasattr(U,'geoms') else [U]
shapes=[{'outer':tom(list(g.exterior.coords)[:-1]),'holes':[tom(list(i.coords)[:-1]) for i in g.interiors]} for g in geoms]
json.dump({'shapes':shapes,'width_m':R['width_m'],'height_m':R['height_m']},open(outp+'_shapes.json','w'))
vis=im.copy()
for g in geoms:
    cv2.polylines(vis,[np.array(g.exterior.coords,np.int32)],True,(0,255,255),2,cv2.LINE_AA)
    for i in g.interiors: cv2.polylines(vis,[np.array(i.coords,np.int32)],True,(0,0,255),2,cv2.LINE_AA)
cv2.imwrite(outp+'_vis.jpg',vis); print('shapes',len(shapes),'area',round(U.area))
