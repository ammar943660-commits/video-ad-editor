#!/usr/bin/env python3
"""trace_neon.py — يتتبّع خطوط النيون من فريم مرجعي ليلي (قبل البطاقات) → هيكل عظمي → مسارات (polylines) قابلة للتعديل في neon_paths.json.
   ثم يبني plate ليلية بإزالة النيون (Inpaint). python3 trace_neon.py <work> <frame>"""
import cv2,numpy as np,json,sys
from skimage.morphology import skeletonize
W=sys.argv[1]; f=int(sys.argv[2]); im=cv2.imread(f'{W}/frames/{f+1:04d}.png'); h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=((h[...,0]>78)&(h[...,0]<108)&(h[...,1]>60)&(h[...,2]>120)).astype(np.uint8)
m[575:625,985:1140]=0; m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
sk=skeletonize(m>0).astype(np.uint8)
# تفكيك الهيكل إلى مسارات: أزل نقاط التفرّع ثم مكوّنات متصلة → ترتيب النقاط بتتبّع الجيران
nb=cv2.filter2D(sk,-1,np.ones((3,3)))*sk; br=(nb>3); sk2=sk.copy(); sk2[cv2.dilate(br.astype(np.uint8),np.ones((3,3)))>0]=0
n,lab=cv2.connectedComponents(sk2,connectivity=8); paths=[]
for k in range(1,n):
    ys,xs=np.where(lab==k)
    if len(xs)<8: continue
    pts=set(zip(xs.tolist(),ys.tolist())); deg={p:sum((p[0]+dx,p[1]+dy) in pts for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy) for p in pts}
    start=min(pts,key=lambda p:(deg[p],p[1])); path=[start]; seen={start}
    while True:
        c=path[-1]; nxt=[(c[0]+dx,c[1]+dy) for dx in (-1,0,1) for dy in (-1,0,1) if (dx or dy) and (c[0]+dx,c[1]+dy) in pts and (c[0]+dx,c[1]+dy) not in seen]
        if not nxt: break
        nxt.sort(key=lambda q:abs(q[0]-c[0])+abs(q[1]-c[1])); path.append(nxt[0]); seen.add(nxt[0])
    ap=cv2.approxPolyDP(np.array(path,np.int32).reshape(-1,1,2),1.0,False)[:,0,:].tolist()
    if len(path)>=8: paths.append(ap)
json.dump({'_doc':'مسارات نيون R5 (بكسل 1146×644) متتبَّعة من فريم المرجع %d — قابلة للتعديل/الحذف/الإضافة'%f,'paths':paths},open(f'{W}/neon_paths.json','w'))
# plate ليلية: إزالة النيون + توهجه
mm=cv2.dilate(m,np.ones((11,11),np.uint8))*255; glow=cv2.GaussianBlur(m.astype(np.float32),(0,0),6)
night=cv2.inpaint(im,mm,7,cv2.INPAINT_TELEA)
cv2.imwrite(f'{W}/night_plate.png',night); cv2.imwrite(f'{W}/neon_mask.png',m*255); print('paths',len(paths))
