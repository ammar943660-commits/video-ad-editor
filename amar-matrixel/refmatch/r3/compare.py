#!/usr/bin/env python3
"""compare.py — مقارنة جنباً إلى جنب (مرجع | تنفيذ) عند اللحظات المتناظرة. python3 compare.py <work> <render_dir_or_plate> out.jpg i1 i2 ..."""
import cv2,numpy as np,sys
W,src,out=sys.argv[1:4]; idx=[int(x) for x in sys.argv[4:]]; rows=[]
for i in idx:
    a=cv2.imread(f'{W}/frames/{i+1:04d}.png'); b=cv2.imread(f'{src}/{i+1:04d}.png')
    if b is None: b=np.zeros_like(a)
    if b.shape[2]==4:
        al=b[:,:,3:4]/255.; p=cv2.imread(f'{W}/plate/{i+1:04d}.png'); b=(p*(1-al)+b[:,:,:3]*al).astype(np.uint8)
    for im,t in ((a,'REF'),(b,'OURS')): cv2.putText(im,f'{t} t={i/30:.2f}s',(8,22),0,0.65,(255,255,255),2); cv2.putText(im,f'{t} t={i/30:.2f}s',(8,22),0,0.65,(0,0,0),1)
    rows.append(np.hstack([cv2.resize(a,(760,427)),cv2.resize(b,(760,427))]))
cv2.imwrite(out,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,92])
