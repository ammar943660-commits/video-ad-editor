#!/usr/bin/env python3
"""trace_text.py — يستخلص شكل حروف النص من فريم المرجع المعدَّل المنظور (rect) باستعمال عتبة الإضاءة + غلاف الخط التقريبي، ثم يحوّله إلى مضلعات (متر) لبثق Blender.
   python3 trace_text.py <work> <outprefix> <font.ttf> <text> [lo hi]  → <outprefix>_shapes.json"""
import sys,json,numpy as np,cv2
from shapely.geometry import Polygon
from shapely.ops import unary_union
sys.path.insert(0,'..')
W,outp,font,text=sys.argv[1:5]; lo=float(sys.argv[5]) if len(sys.argv)>5 else 88; hi=float(sys.argv[6]) if len(sys.argv)>6 else 122
im=cv2.imread(outp+'_rect.png'); J=json.load(open(outp+'_rect.json')); wpx,hpx=J['wpx'],J['hpx']; half_w,top,bot=J['half_w'],J['top'],J['bot']
g=cv2.GaussianBlur(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32),(0,0),2)
m=((g>lo)&(g<hi)).astype(np.uint8)*255; m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
# غلاف تقريبي: خط Baloo محاذى إلى صندوق النص التقريبي
from glyphs import polygons
polys,xr,yr=polygons(text,font,None,condense=1.0)
y0,y1=float(sys.argv[7]) if len(sys.argv)>7 else 190,float(sys.argv[8]) if len(sys.argv)>8 else 590; x0,x1=float(sys.argv[9]) if len(sys.argv)>9 else 40,float(sys.argv[10]) if len(sys.argv)>10 else 1350
sx=(x1-x0)/(xr[1]-xr[0]); sy=(y1-y0)/(yr[1]-yr[0]); env=np.zeros((hpx,wpx),np.uint8)
for ext,holes in polys:
    for ring,val in [(ext,255)]+[(h,0) for h in holes]:
        pts=np.array([[x0+(x-xr[0])*sx,y1-(y-yr[0])*sy] for x,y in ring],np.int32); cv2.fillPoly(env,[pts],val)
env=cv2.dilate(env,np.ones((61,61),np.uint8))
mm=cv2.bitwise_and(m,env); mm=cv2.morphologyEx(mm,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8)); mm=cv2.GaussianBlur(mm,(0,0),3); mm=(mm>127).astype(np.uint8)*255
n,lab,st,_=cv2.connectedComponentsWithStats(mm); keep=np.zeros_like(mm)
for i in range(1,n):
    if st[i,4]>1800: keep[lab==i]=255
cv2.imwrite(outp+'_mask.png',keep)
cs,hier=cv2.findContours(keep,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
polysout=[]
def tom(p): return [(( p[0]/wpx-0.5)*2*half_w, top-(p[1]/hpx)*(top-bot)) for p in p]
# تجميع الخارجي/الثقوب
polysh=[]
for i,c in enumerate(cs):
    if cv2.contourArea(c)<400: continue
    ap=cv2.approxPolyDP(c,1.6,True)[:,0,:].astype(float); polysh.append((i,hier[0][i][3],ap))
shapes=[]
for i,par,ap in polysh:
    if par==-1:
        holes=[tom(a) for j,p2,a in polysh if p2==i]; shapes.append({'outer':tom(ap),'holes':holes})
json.dump({'shapes':shapes,'height_ref':top-bot},open(outp+'_shapes.json','w'))
vis=im.copy(); cv2.drawContours(vis,cs,-1,(0,255,255),2); cv2.imwrite(outp+'_trace.jpg',vis)
print('shapes',len(shapes))
