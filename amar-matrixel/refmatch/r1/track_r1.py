#!/usr/bin/env python3
"""track_r1.py — حركة كاميرا R1 (قريبة من الثبات: انزياح/تكبير بسيط): homography من الفريم 0 لكل فريم (SIFT على المباني والطريق فقط، مع RANSAC)، تُنعَّم زمنياً.
   python3 track_r1.py <work> <n> → H_r1.npy"""
import cv2,numpy as np,sys
from scipy.ndimage import gaussian_filter1d
W=sys.argv[1]; n=int(sys.argv[2]); s=cv2.SIFT_create(4000); bf=cv2.BFMatcher()
def g(i): return cv2.cvtColor(cv2.imread(f'{W}/frames/{i+1:04d}.png'),cv2.COLOR_BGR2GRAY)
m=np.zeros((644,1146),np.uint8); m[:150]=255; m[470:,:]=255; m[:,:120]=255; m[:,1030:]=255; m[580:625,990:1130]=0
k0,d0=s.detectAndCompute(g(0),m); Hs=[np.eye(3)]
for i in range(1,n):
    k,d=s.detectAndCompute(g(i),m); mm=[a for a,b in bf.knnMatch(d0,d,k=2) if a.distance<0.7*b.distance]
    H,_=cv2.findHomography(np.float32([k0[a.queryIdx].pt for a in mm]),np.float32([k[a.trainIdx].pt for a in mm]),cv2.RANSAC,2.0)
    # تقييد إلى تشابه (تكبير+إزاحة+دوران صغير): الحركات الأخرى ضوضاء من السيارات/المؤثرات
    A,_=cv2.estimateAffinePartial2D(np.float32([k0[a.queryIdx].pt for a in mm]),np.float32([k[a.trainIdx].pt for a in mm]),method=cv2.RANSAC,ransacReprojThreshold=2.0)
    Hs.append(np.vstack([A,[0,0,1]]))
H=np.array(Hs); P=H[:,:2,:].reshape(n,6); P=gaussian_filter1d(P,2.5,axis=0,mode='nearest'); H[:,:2,:]=P.reshape(n,2,3)
np.save(f'{W}/H_r1.npy',H); print('scale range',np.round([np.sqrt(abs(np.linalg.det(h[:2,:2]))) for h in H[::40]],3))
