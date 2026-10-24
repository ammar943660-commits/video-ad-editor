#!/usr/bin/env python3
"""refine_gc.py — يصقل مضلعات الحروف التقريبية بـGrabCut داخل حزام ضيق حول الحدود (يلتقط حافة الصورة الحقيقية).
   python3 refine_gc.py <work> glyphs/x_poly.json out_prefix [band=8]  → out_prefix_shapes.json + out_prefix_vis.jpg"""
import sys,json,cv2,numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
sys.argv=[sys.argv[0]]+sys.argv[1:]
W,gj,outp=sys.argv[1:4]; band=int(sys.argv[4]) if len(sys.argv)>4 else 8
import importlib.util,os
# أعد استخدام mk/chaik من glyph_poly عبر تنفيذ الجزء التعريفي
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'glyph_poly.py')).read().split("U=unary_union")[0]
sys.argv=['x',W,gj,outp]; exec(src)
def tom(c): return [(R['x0']+x/R['wpx']*(R['x1']-R['x0']), R['z1']-y/R['hpx']*(R['z1']-R['z0'])) for x,y in c]
U=unary_union([mk(s) for s in G['add']]); 
if G.get('erase'): U=U.difference(unary_union([mk(s) for s in G['erase']]))
H,Wd=im.shape[:2]; m=np.zeros((H,Wd),np.uint8)
geoms=list(U.geoms) if hasattr(U,'geoms') else [U]
for g in geoms:
    cv2.fillPoly(m,[np.array(g.exterior.coords,np.int32)],255)
    for i in g.interiors: cv2.fillPoly(m,[np.array(i.coords,np.int32)],0)
k=lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
gc=np.full((H,Wd),cv2.GC_BGD,np.uint8); gc[cv2.dilate(m,k(band))>0]=cv2.GC_PR_BGD; gc[m>0]=cv2.GC_PR_FGD; gc[cv2.erode(m,k(band))>0]=cv2.GC_FGD
bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
cv2.grabCut(im,gc,None,bg,fg,6,cv2.GC_INIT_WITH_MASK)
r=((gc==cv2.GC_FGD)|(gc==cv2.GC_PR_FGD)).astype(np.uint8)*255
r=cv2.morphologyEx(r,cv2.MORPH_OPEN,k(2)); r=cv2.morphologyEx(r,cv2.MORPH_CLOSE,k(2)); r=cv2.GaussianBlur(r,(0,0),1.6); r=(r>127).astype(np.uint8)*255
cs,hi=cv2.findContours(r,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
shapes=[]; vis=im.copy()
for i,c in enumerate(cs):
    if hi[0][i][3]!=-1 or cv2.contourArea(c)<80: continue
    outer=cv2.approxPolyDP(c,1.2,True)[:,0,:]; holes=[]; j=hi[0][i][2]
    while j!=-1:
        if cv2.contourArea(cs[j])>40: holes.append(cv2.approxPolyDP(cs[j],1.2,True)[:,0,:])
        j=hi[0][j][0]
    cv2.polylines(vis,[outer.astype(np.int32)],True,(0,255,255),2,cv2.LINE_AA)
    for h in holes: cv2.polylines(vis,[h.astype(np.int32)],True,(0,0,255),2,cv2.LINE_AA)
    shapes.append({'outer':tom(outer.tolist()),'holes':[tom(h.tolist()) for h in holes]})
json.dump({'shapes':shapes,'width_m':R['width_m'],'height_m':R['height_m']},open(outp+'_shapes.json','w')); cv2.imwrite(outp+'_vis.jpg',vis); print('shapes',len(shapes))
