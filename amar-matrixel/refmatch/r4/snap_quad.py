#!/usr/bin/env python3
"""snap_quad.py — يلصق رباعي القطعة بخط النيون السماوي في كل فريم (الهولوغرام في المرجع لا يطابق حافة الرمل تماماً بعد صعود الكاميرا).
   هدف: متوسط المسافة من نقاط على الأضلاع الأربعة إلى أقرب بكسل سماوي (Distance Transform)؛ Nelder-Mead من التتبع/الفريم السابق.
   python3 snap_quad.py <work> <f_from> <f_to> [use_prev_after]"""
import cv2,numpy as np,json,sys
from scipy.optimize import minimize
W=sys.argv[1]; a,b=int(sys.argv[2]),int(sys.argv[3]); prev_after=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
T=json.load(open(f'{W}/lot_track.json')); Q=[np.array(q,float) for q in T['quads']]; S=T.get('snapped',[None]*len(Q))
if len(S)<len(Q): S+= [None]*(len(Q)-len(S))
def cyan(i):
    h=cv2.cvtColor(cv2.imread(f'{W}/frames/{i+1:04d}.png'),cv2.COLOR_BGR2HSV)
    return ((h[...,0]>85)&(h[...,0]<112)&(h[...,1]>70)&(h[...,2]>140)).astype(np.uint8)
def edge_pts(q,n=60):
    P=[]
    for k in range(4):
        p0,p1=q[k],q[(k+1)%4]; t=np.linspace(0.05,0.95,n)[:,None]; P.append(p0+(p1-p0)*t)
    return np.concatenate(P)
for i in range(a,b+1):
    m=cyan(i)
    if m.sum()<500: S[i]=Q[i].tolist(); continue
    dt=cv2.distanceTransform(1-m,cv2.DIST_L2,5); dt=np.minimum(dt,25)
    init=np.array(S[i-1]) if (i>prev_after and S[i-1] is not None) else Q[i]
    def cost(x):
        q=x.reshape(4,2); P=edge_pts(q); xi=np.clip(P[:,0],0,1145).astype(int); yi=np.clip(P[:,1],0,643).astype(int)
        inside=((P[:,0]>=0)&(P[:,0]<1146)&(P[:,1]>=0)&(P[:,1]<644))
        d=np.where(inside,dt[yi,xi],8.0); return float(np.mean(np.minimum(d,25)**0.7))+0.002*np.sum((x-init.flatten())**2)**0.5
    r=minimize(cost,init.flatten(),method='Nelder-Mead',options={'maxiter':3000,'xatol':0.3,'fatol':1e-4})
    S[i]=r.x.reshape(4,2).tolist()
    if i%10==0: print(i,round(r.fun,3),np.round(r.x).astype(int).tolist(),flush=True)
T['snapped']=S; json.dump(T,open(f'{W}/lot_track.json','w'))
