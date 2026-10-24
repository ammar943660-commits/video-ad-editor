#!/bin/bash
# tune.sh <work> <frame> <tag> : يرسم ويقص ويقيس إضاءة وجه الحرف
W=$1; F=$2; T=$3
AMX_CAM=camera_true.json /tmp/bpyenv/bin/python scene_r3.py $W $F $W/rend/$(printf %04d $((F+1))).png 32 2>&1 | tail -0
python3 - <<P
import cv2,numpy as np
i=$F+1
a=cv2.imread("$W/frames/%04d.png"%i); b=cv2.imread("$W/rend/%04d.png"%i,-1); p=cv2.imread("$W/plate_p/%04d.png"%i)
al=b[:,:,3:4]/255.; o=(p*(1-al)+b[:,:,:3]*al).astype(np.uint8)
x0,x1,y0,y1=330,830,230,420
cv2.imwrite("$W/tx_$T.jpg",cv2.resize(np.vstack([a[y0:y1,x0:x1],o[y0:y1,x0:x1]]),None,fx=2.2,fy=2.2,interpolation=cv2.INTER_CUBIC))
print('face ours',b[270,590][:3],'ref',a[270,590])
P
