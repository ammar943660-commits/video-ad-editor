#!/usr/bin/env python3
"""trace_neon2.py — تتبّع نيون R5 (نسخة 2): اتحاد أقنعة الفريمات 20–27 (النيون مكتمل قبل البطاقات) مع حذف منطقة بطاقة 1 وذيلها،
   هيكل عظمي → مسارات، لصق النهايات المتقاربة (زوايا متصلة)، حذف الخطوط المتوازية المكررة، ثم قياس بداية ومدة رسم كل مسار من المرجع.
   ملاحظة صدق: الأشكال مرسومة فوق المرجع، والتوقيت بيانات مقيسة من المرجع (ليست بكسلات). python3 trace_neon2.py <work>"""
import cv2,numpy as np,json,sys
from skimage.morphology import skeletonize
W=sys.argv[1]; C=json.load(open('r5_cfg.json'))
def cy(f):
    h=cv2.cvtColor(cv2.imread(f'{W}/frames/{f+1:04d}.png'),cv2.COLOR_BGR2HSV); return ((h[...,0]>78)&(h[...,0]<108)&(h[...,1]>60)&(h[...,2]>120)).astype(np.uint8)
m=np.zeros((644,1146),np.uint8)
for f in range(20,28): m|=cy(f)
c1=C['cards'][0]; x0,y0,x1,y1=c1['box']; m[max(y0-25,0):y1+20,max(x0-35,0):x1+25]=0
cv2.polylines(m,[np.array(c1['leader'],np.int32)],False,0,14)
m[575:625,985:1140]=0; m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
n_,lab,st,_=cv2.connectedComponentsWithStats(m)
for k in range(1,n_):
    if st[k,4]<25: m[lab==k]=0
sk=skeletonize(m>0).astype(np.uint8)
nb=cv2.filter2D(sk,-1,np.ones((3,3)))*sk; br=(nb>3).astype(np.uint8); sk2=sk.copy(); sk2[cv2.dilate(br,np.ones((3,3)))>0]=0
n,lab=cv2.connectedComponents(sk2,connectivity=8); paths=[]
for k in range(1,n):
    ys,xs=np.where(lab==k)
    if len(xs)<6: continue
    pts=set(zip(xs.tolist(),ys.tolist())); deg={p:sum((p[0]+dx,p[1]+dy) in pts for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy) for p in pts}
    start=min(pts,key=lambda p:(deg[p],p[1])); path=[start]; seen={start}
    while True:
        c=path[-1]; nxt=[(c[0]+dx,c[1]+dy) for dx in (-1,0,1) for dy in (-1,0,1) if (dx or dy) and (c[0]+dx,c[1]+dy) in pts and (c[0]+dx,c[1]+dy) not in seen]
        if not nxt: break
        nxt.sort(key=lambda q:abs(q[0]-c[0])+abs(q[1]-c[1])); path.append(nxt[0]); seen.add(nxt[0])
    paths.append(cv2.approxPolyDP(np.array(path,np.int32).reshape(-1,1,2),1.0,False)[:,0,:].astype(float).tolist())
# لصق النهايات: كل نهايتين ضمن 7px تُنقلان لمركزهما (يعيد وصل الزوايا والتفرعات)
ends=[(i,j) for i in range(len(paths)) for j in (0,-1)]
for a in range(len(ends)):
    i,j=ends[a]; p=np.array(paths[i][j]); grp=[(i,j)]
    for b in range(len(ends)):
        if b==a: continue
        k,l=ends[b]
        if np.linalg.norm(np.array(paths[k][l])-p)<7: grp.append((k,l))
    if len(grp)>1:
        c=np.mean([paths[k][l] for k,l in grp],0).tolist()
        for k,l in grp: paths[k][l]=c
# نهاية حرة قريبة من وسط مسار آخر (تفرّع T): تُمدّ إليه
def dense(p):
    o=[];p=np.array(p)
    for a,b in zip(p[:-1],p[1:]):
        for t in np.linspace(0,1,max(2,int(np.linalg.norm(b-a)))): o.append(a+(b-a)*t)
    return np.array(o)
D=[dense(p) for p in paths]
for i in range(len(paths)):
    for j in (0,-1):
        p=np.array(paths[i][j]); best=None
        for k in range(len(paths)):
            if k==i: continue
            d=np.linalg.norm(D[k]-p,axis=1); q=d.argmin()
            if 1.5<d[q]<8 and (best is None or d[q]<best[0]): best=(d[q],D[k][q])
        if best is not None:
            if j==0: paths[i].insert(0,best[1].tolist())
            else: paths[i].append(best[1].tolist())
# حذف المكرر: مسار كل نقاطه ضمن 4px من مسار أطول
D=[dense(p) for p in paths]; L=[len(d) for d in D]; keep=[True]*len(paths)
for i in sorted(range(len(paths)),key=lambda i:L[i]):
    for k in range(len(paths)):
        if k!=i and keep[k] and L[k]>=L[i]:
            d=np.min(np.linalg.norm(D[i][:,None,:]-D[k][None,::2,:],axis=2),axis=1)
            if np.mean(d<4)>0.85: keep[i]=False; break
paths=[p for p,k in zip(paths,keep) if k]
# توقيت كل مسار من المرجع (الفريمات 0–40)
M=[cy(f) for f in range(41)]; out=[]
for p in paths:
    d=np.round(dense(p)).astype(int); d[:,0]=d[:,0].clip(0,1145); d[:,1]=d[:,1].clip(0,643)
    cov=[M[f][d[:,1],d[:,0]].mean() for f in range(41)]
    s=next((f for f,c in enumerate(cov) if c>0.1),None); e=next((f for f,c in enumerate(cov) if c>0.8),None)
    if s is None: s=12
    if e is None or e<=s: e=s+4
    out.append({'pts':[[round(x,1),round(y,1)] for x,y in p],'start':int(s),'dur':int(min(e-s,10))})
json.dump({'_doc':'نيون R5 v2: أشكال مرسومة فوق المرجع + توقيت (start/dur بالفريم @30fps) مقيس من المرجع. قابل للتعديل.','paths':out},open(f'{W}/neon_paths_v2.json','w'))
print('paths',len(out),'dropped dup',keep.count(False))
