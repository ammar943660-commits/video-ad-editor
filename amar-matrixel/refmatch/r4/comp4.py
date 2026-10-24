#!/usr/bin/env python3
"""comp4.py — تركيب R4: plate + هولوغرام إضافي (screen) + مقارنة مع المرجع. python3 comp4.py <work> <holo_dir> <out_dir> [cmp.jpg] f1 f2 ..."""
import cv2,numpy as np,sys,os
W,HD,O=sys.argv[1:4]; rest=sys.argv[4:]; cmp_=rest[0] if rest and rest[0].endswith('.jpg') else None; fs=[int(x) for x in (rest[1:] if cmp_ else rest)]
os.makedirs(O,exist_ok=True); rows=[]
for i in fs:
    p=cv2.imread(f'{W}/plate/{i+1:04d}.png').astype(np.float32)/255; L=cv2.imread(f'{HD}/{i+1:04d}.png').astype(np.float32)/255
    o=1-(1-p)*(1-np.clip(L,0,1)); o=(o*255).astype(np.uint8); cv2.imwrite(f'{O}/{i+1:04d}.png',o)
    if cmp_:
        a=cv2.imread(f'{W}/frames/{i+1:04d}.png'); 
        for im,t in ((a,'REF'),(o,'OURS')): cv2.putText(im,f'{t} t={i/30:.2f}s',(8,22),0,0.65,(255,255,255),2)
        rows.append(np.hstack([cv2.resize(a,(760,427)),cv2.resize(o,(760,427))]))
if cmp_: cv2.imwrite(cmp_,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,88])
