#!/usr/bin/env python3
"""r3_quad2.py — رباعي الأرض لكل فريم بمطابقة Chamfer مقابل خريطة المسافة لبكسلات النيون السماوي (متينة ضد الحجب بالغبار).
   يبدأ من الفريم المرجعي 65 ويتقدم/يتراجع زمنياً، ثم تنعيم غاوسي."""
import cv2,numpy as np,glob,json,sys
from scipy.optimize import minimize
from scipy.ndimage import gaussian_filter1d
W=sys.argv[1]; fs=sorted(glob.glob(f'{W}/frames/*.png')); n=int(sys.argv[2]); ref=65
Q65=np.float64([[536,259],[1003,331],[800,580],[135,350]])
def cyan(im):
    h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV);m=((h[:,:,0]>82)&(h[:,:,0]<100)&(h[:,:,1]>110)&(h[:,:,2]>170)).astype(np.uint8);m[600:,900:]=0;return m
def samples(Q,k=70):
    pts=[]
    for a in range(4):
        p,q=Q[a],Q[(a+1)%4]
        for t in np.linspace(0,1,k,endpoint=False): pts.append(p+(q-p)*t)
    return np.array(pts)
def solve(m,Qinit,lam):
    dt=cv2.distanceTransform(1-cv2.dilate(m,np.ones((3,3),np.uint8)),cv2.DIST_L2,3)
    h,w=dt.shape
    def cost(x):
        Q=x.reshape(4,2);P=samples(Q);xi=np.clip(P[:,0],0,w-1).astype(int);yi=np.clip(P[:,1],0,h-1).astype(int);d=dt[yi,xi]
        vis=np.minimum(d,14.0)**2
        return vis.mean()+lam*np.sum((Q-Qinit)**2)/100.0
    r=minimize(cost,Qinit.flatten(),method='Powell',options={'xtol':0.05,'ftol':1e-4,'maxiter':12})
    return r.x.reshape(4,2),r.fun
Hs=np.load(f'{W}/cam_H.npy'); Q=[None]*n; Q[ref]=Q65.copy(); conf=[0]*n
def warp(Qp,Ha,Hb):  # Qp في إطار a → إطار b بالتحويل البنائي (SIFT المباني) كتخمين أولي
    M=Hb@np.linalg.inv(Ha); return cv2.perspectiveTransform(Qp[None].astype(np.float64),M)[0]
def run(rng,prev):
    last=ref
    for i in rng:
        init=warp(prev,Hs[last],Hs[i]); m=cyan(cv2.imread(fs[i]))
        if m.sum()<400: Q[i]=init.copy();conf[i]=0;prev=init;last=i;continue
        q,f=solve(m,init,lam=0.004);Q[i]=q;conf[i]=f;prev=q;last=i
run(range(ref+1,n),Q65); run(range(ref-1,-1,-1),Q65)
A=np.array(Q).reshape(n,8);sm=gaussian_filter1d(A,2.0,axis=0,mode='nearest').reshape(n,4,2)
json.dump({'quads':sm.tolist(),'cost':[float(c) for c in conf]},open(f'{W}/quads.json','w'))
print('done',[round(float(c),1) for c in conf[::25]])
