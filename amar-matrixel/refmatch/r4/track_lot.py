#!/usr/bin/env python3
"""track_lot.py — تتبع مستوى أرض القطعة في R4: رباعي الفريم 0 (من R3 لأن اللقطة الافتتاحية نفسها) ← homography متسلسلة بـSIFT+RANSAC
   داخل الرباعي فقط (رمل القطعة) مع تصحيح انجراف بالمطابقة مع فريم مرجعي كل K فريمات. python3 track_lot.py <work> <n> [q0json]"""
import cv2,numpy as np,json,sys
W=sys.argv[1]; n=int(sys.argv[2])
Q0=np.float32(json.loads(sys.argv[3]) if len(sys.argv)>3 else [[530,262],[1013,336],[790,582],[147,350]])
sift=cv2.SIFT_create(4000); bf=cv2.BFMatcher()
def load(i):
    g=cv2.cvtColor(cv2.imread(f'{W}/frames/{i+1:04d}.png'),cv2.COLOR_BGR2GRAY); return cv2.createCLAHE(3.0,(8,8)).apply(g)
def feats(i,q):
    g=load(i); m=np.zeros_like(g); cv2.fillPoly(m,[np.round(q).astype(np.int32)],255); m=cv2.erode(m,np.ones((15,15),np.uint8))
    k,d=sift.detectAndCompute(g,m); return k,d
def H_between(a,qa,b,qb_guess):
    ka,da=feats(a,qa); kb,db=feats(b,cv2.perspectiveTransform(qb_guess[None],np.eye(3))[0] if qb_guess is not None else qa)
    if da is None or db is None or len(ka)<10 or len(kb)<10: return None,0
    mm=[m for m,n_ in bf.knnMatch(da,db,k=2) if m.distance<0.75*n_.distance]
    if len(mm)<12: return None,len(mm)
    pa=np.float32([ka[m.queryIdx].pt for m in mm]); pb=np.float32([kb[m.trainIdx].pt for m in mm])
    H,inl=cv2.findHomography(pa,pb,cv2.RANSAC,3.0); return H,int(inl.sum()) if inl is not None else 0
Q=[Q0]; log=[]
for i in range(1,n):
    q=Q[-1]; H,ni=H_between(i-1,q,i,q)
    if H is None: H=np.eye(3); 
    qn=cv2.perspectiveTransform(q[None],H)[0]
    if i>=8 and i%8==0:  # تصحيح من فريم أبعد
        H2,n2=H_between(i-8,Q[i-8],i,qn)
        if H2 is not None and n2>40: qn=0.5*qn+0.5*cv2.perspectiveTransform(Q[i-8][None],H2)[0]
    Q.append(qn.astype(np.float32)); log.append(ni)
    if i%20==0: print(i,ni,np.round(qn).astype(int).tolist(),flush=True)
json.dump({'quads':[q.tolist() for q in Q],'inliers':log},open(f'{W}/lot_track.json','w'))
