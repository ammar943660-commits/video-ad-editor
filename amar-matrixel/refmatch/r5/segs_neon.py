#!/usr/bin/env python3
"""segs_neon.py — يحوّل مسارات النيون المتتبَّعة (neon_paths_v2.json) إلى قطع مستقيمة نظيفة: تبسيط، دمج القطع المتسامتة عبر الفجوات،
   حذف المكرر المتوازي، وإغلاق الزوايا بمدّ القطع حتى تقاطعها. يعيد قياس توقيت كل قطعة من المرجع. → neon_paths_v3.json"""
import cv2,numpy as np,json,sys,math
W=sys.argv[1]; P=json.load(open(f'{W}/neon_paths_v2.json'))['paths']
S=[]
for p in P:
    a=cv2.approxPolyDP(np.array(p['pts'],np.float32).reshape(-1,1,2),2.2,False)[:,0,:]
    for u,v in zip(a[:-1],a[1:]):
        if np.linalg.norm(v-u)>=5: S.append([u.astype(float),v.astype(float)])
def ang(s): d=s[1]-s[0]; return math.atan2(d[1],d[0])%math.pi
def adiff(a,b): d=abs(a-b)%math.pi; return min(d,math.pi-d)
def merge_pass(S,gap=34,off=3.0,ad=math.radians(4)):
    used=[False]*len(S); out=[]
    for i in range(len(S)):
        if used[i]: continue
        a,b=S[i]; used[i]=True; changed=True
        while changed:
            changed=False; d=(b-a)/np.linalg.norm(b-a); nrm=np.array([-d[1],d[0]])
            for j in range(len(S)):
                if used[j]: continue
                c,e=S[j]
                if adiff(ang([a,b]),ang([c,e]))>ad: continue
                if abs((c-a)@nrm)>off or abs((e-a)@nrm)>off: continue
                t=sorted([0,(b-a)@d]); tc=sorted([(c-a)@d,(e-a)@d])
                if tc[0]>t[1]+gap or tc[1]<t[0]-gap: continue
                lo=min(t[0],tc[0]); hi=max(t[1],tc[1]); mid=np.mean([a,b,c,e],0); base=a+((mid-a)@nrm)*nrm
                a,b=base+d*lo,base+d*hi; used[j]=True; changed=True
        out.append([a,b])
    return out
for _ in range(3): S=merge_pass(S)
S=[s for s in S if np.linalg.norm(s[1]-s[0])>=8]
def inter(s,t):
    p,r=s[0],s[1]-s[0]; q,u=t[0],t[1]-t[0]; den=r[0]*u[1]-r[1]*u[0]
    if abs(den)<1e-6: return None
    w=q-p; tt=(w[0]*u[1]-w[1]*u[0])/den; return p+tt*r
for i in range(len(S)):
    for k in (0,1):
        e=S[i][k]; best=None
        for j in range(len(S)):
            if j==i or adiff(ang(S[i]),ang(S[j]))<math.radians(30): continue
            X=inter(S[i],S[j])
            if X is None: continue
            de=np.linalg.norm(X-e)
            a,b=S[j]; L=np.linalg.norm(b-a); tt=(X-a)@(b-a)/L
            if de<10 and -10<tt<L+10 and (best is None or de<best[0]): best=(de,X,j,tt,L)
        if best is not None:
            S[i][k]=best[1]; j=best[2]
            if best[3]<0: S[j][0]=best[1]
            elif best[3]>best[4]: S[j][1]=best[1]
def cy(f):
    h=cv2.cvtColor(cv2.imread(f'{W}/frames/{f+1:04d}.png'),cv2.COLOR_BGR2HSV); return ((h[...,0]>78)&(h[...,0]<108)&(h[...,1]>60)&(h[...,2]>120))
M=[cy(f) for f in range(41)]; out=[]
for a,b in S:
    n=int(np.linalg.norm(b-a))+2; d=np.round(np.linspace(a,b,n)).astype(int); d[:,0]=d[:,0].clip(0,1145); d[:,1]=d[:,1].clip(0,643)
    cov=[M[f][d[:,1],d[:,0]].mean() for f in range(41)]
    s=next((f for f,c in enumerate(cov) if c>0.05),12); e=next((f for f,c in enumerate(cov) if c>0.8),s+4)
    # اتجاه الرسم: من الطرف الذي يضيء أولاً
    f1=next((f for f in range(41) if M[f][d[:len(d)//4,1],d[:len(d)//4,0]].mean()>0.5),40); f2=next((f for f in range(41) if M[f][d[-len(d)//4:,1],d[-len(d)//4:,0]].mean()>0.5),40)
    if f2<f1: a,b=b,a
    out.append({'pts':[[round(float(a[0]),1),round(float(a[1]),1)],[round(float(b[0]),1),round(float(b[1]),1)]],'start':int(s),'dur':int(max(2,min(e-s,10)))})
json.dump({'_doc':'نيون R5 v3: قطع مستقيمة منظّفة (أشكال مرسومة فوق المرجع) + توقيت مقيس من المرجع. قابل للتعديل/الحذف.','paths':out},open(f'{W}/neon_paths_v3.json','w'))
print('segments',len(out))
