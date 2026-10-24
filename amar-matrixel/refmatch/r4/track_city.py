#!/usr/bin/env python3
"""track_city.py — امتداد تتبع مستوى الأرض لما بعد تغطية المباني الهولوغرامية للقطعة: SIFT على المدينة المحيطة (خارج البكسلات السماوية المتمددة)
   مع RANSAC homography بين فريمات متتالية، يبدأ من الرباعي الملصوق عند f_from. python3 track_city.py <work> <f_from> <f_to>"""
import cv2,numpy as np,json,sys
W=sys.argv[1]; a,b=int(sys.argv[2]),int(sys.argv[3]); T=json.load(open(f'{W}/lot_track.json')); S=T['snapped']
sift=cv2.SIFT_create(5000); bf=cv2.BFMatcher()
def kd(i):
    im=cv2.imread(f'{W}/frames/{i+1:04d}.png'); h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    cy=((h[...,0]>80)&(h[...,0]<115)&(h[...,1]>50)&(h[...,2]>90)).astype(np.uint8)*255; m=255-cv2.dilate(cy,np.ones((31,31),np.uint8)); m[560:,850:]=0
    g=cv2.createCLAHE(3.0,(8,8)).apply(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)); return sift.detectAndCompute(g,m)
prev=kd(a); q=np.float32(S[a])
for i in range(a+1,b+1):
    cur=kd(i); mm=[m for m,n_ in bf.knnMatch(prev[1],cur[1],k=2) if m.distance<0.75*n_.distance]
    pa=np.float32([prev[0][m.queryIdx].pt for m in mm]); pb=np.float32([cur[0][m.trainIdx].pt for m in mm])
    H,inl=cv2.findHomography(pa,pb,cv2.RANSAC,2.5)
    q=cv2.perspectiveTransform(q[None],H)[0]; S[i]=q.tolist(); prev=cur
    if i%10==0: print(i,int(inl.sum()),np.round(q).astype(int).tolist(),flush=True)
T['snapped']=S; json.dump(T,open(f'{W}/lot_track.json','w'))
