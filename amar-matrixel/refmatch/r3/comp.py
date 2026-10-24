#!/usr/bin/env python3
"""comp.py — تركيب نهائي: plate_p + نيون (إضافي) + طبقة Blender RGBA. python3 comp.py <work> <rend_dir> <out_dir> i1 i2 ..."""
import cv2,numpy as np,sys,os
W,R,O=sys.argv[1:4]; os.makedirs(O,exist_ok=True)
for i in [int(x) for x in sys.argv[4:]]:
    p=cv2.imread(f'{W}/plate_p2/{i+1:04d}.png').astype(np.float32); nn=cv2.imread(f'{W}/neon/{i+1:04d}.png').astype(np.float32)
    o=p+nn*0.9; o=255*(1-np.exp(-o/255*1.0)) if False else np.clip(o,0,255)
    b=cv2.imread(f'{R}/{i+1:04d}.png',-1)
    if b is not None:
        if b.shape[:2]!=p.shape[:2]: b=cv2.resize(b,(p.shape[1],p.shape[0]),interpolation=cv2.INTER_CUBIC)
        al=b[:,:,3:4].astype(np.float32)/255; o=o*(1-al)+b[:,:,:3].astype(np.float32)*al
    nd=os.environ.get('ND_DIR')
    if nd and os.path.exists(f'{nd}/{i+1:04d}.png'):   # طبقة بلا غبار فوق الغبار: النص يبقى مقروءاً (كالمرجع)
        t=cv2.imread(f'{nd}/{i+1:04d}.png',-1)
        if t.shape[:2]!=o.shape[:2]: t=cv2.resize(t,(o.shape[1],o.shape[0]),interpolation=cv2.INTER_CUBIC)
        k=float(os.environ.get('ND_MIX','0.75')); a=t[:,:,3:4].astype(np.float32)/255*k; o=o*(1-a)+t[:,:,:3].astype(np.float32)*a
    cv2.imwrite(f'{O}/{i+1:04d}.png',np.clip(o,0,255).astype(np.uint8))
