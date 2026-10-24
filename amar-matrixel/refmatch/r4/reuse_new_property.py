#!/usr/bin/env python3
"""reuse_new_property.py — يجهّز مجلد عمل R4 لعقار جديد من: فيديو اللقطة + رباعي القطعة في أول فريم (TL,TR,BR,BL بالبكسل).
   التتبع: track_lot.py (SIFT داخل القطعة) أو track.json جاهز (كاميرا معروفة). بعدها holo.py بإعداد العقار.
   python3 reuse_new_property.py <plate.mp4> <work> '<quad json>' [track.json]"""
import sys,os,json,subprocess,cv2,numpy as np
src,W,quad=sys.argv[1:4]; tj=sys.argv[4] if len(sys.argv)>4 else None
os.makedirs(f'{W}/frames',exist_ok=True); os.makedirs(f'{W}/plate',exist_ok=True)
subprocess.run(['ffmpeg','-loglevel','error','-y','-i',src,'-vf','fps=30',f'{W}/frames/%04d.png'],check=True)
for f in sorted(os.listdir(f'{W}/frames')): os.link(f'{W}/frames/{f}',f'{W}/plate/{f}') if not os.path.exists(f'{W}/plate/{f}') else None
n=len(os.listdir(f'{W}/frames')); h,w=cv2.imread(f'{W}/frames/0001.png').shape[:2]
if tj:
    T=json.load(open(tj)); Q=[fr['corners'] for fr in T['frames']][:n]
else:
    D=os.path.dirname(os.path.abspath(__file__)); subprocess.run(['python3',f'{D}/track_lot.py',W,str(n),quad],check=True)
    Q=json.load(open(f'{W}/lot_track.json'))['quads']
json.dump({'quads':Q,'snapped':Q},open(f'{W}/lot_track.json','w')); print('frames',n,'size',w,h)
