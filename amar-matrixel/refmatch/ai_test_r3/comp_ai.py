#!/usr/bin/env python3
"""comp_ai.py — تركيب محلي سريع فوق لقطة AI لـR3 (بلا 3D): تعتيم المشهد + نيون سماوي يرسم حدود القطعة + توهج. ثوانٍ للمقطع.
   رباعي القطعة يُحوَّل من إحداثيات المرجع (فريم 0، 1146×644) عبر نفس القص العمودي المستخدم لصور البداية/النهاية.
   python3 comp_ai.py <in.mp4> <out.mp4> [cfg.json]"""
import cv2,numpy as np,sys,json,subprocess,os,tempfile
src,out=sys.argv[1:3]
C={"quad_ref":[[530,262],[1013,336],[790,582],[147,350]],"crop":{"sx":1920/1146,"x0":696,"cut":10,"ext":388,"cw":820},
   "neon":{"draw":[0.2,1.0],"color_bgr":[255,215,40],"width":3.0},"dark":{"t":[0.3,1.2],"k":0.70,"lot_keep":0.85},"fade_out":None}
if len(sys.argv)>3: C.update(json.load(open(sys.argv[3])))
cap=cv2.VideoCapture(src); fps=cap.get(5); W=int(cap.get(3)); H=int(cap.get(4))
c=C['crop']; k=W/c['cw']
Q=np.array([[(x*c['sx']-c['x0'])*k,(y*c['sx']-c['cut']+c['ext'])*k] for x,y in C['quad_ref']],np.float32)
lot=np.zeros((H,W),np.float32); cv2.fillPoly(lot,[np.round(Q).astype(np.int32)],1); lot=cv2.GaussianBlur(lot,(0,0),8)[...,None]
tmp=tempfile.mkdtemp(); i=0
ease=lambda x:1-(1-min(max(x,0),1))**3
while True:
    ok,f=cap.read()
    if not ok: break
    t=i/fps; o=f.astype(np.float32)
    d=ease((t-C['dark']['t'][0])/(C['dark']['t'][1]-C['dark']['t'][0])); kk=1-(1-C['dark']['k'])*d; kl=1-(1-C['dark']['lot_keep'])*d
    o=o*(lot*kl+(1-lot)*kk)*np.array([1.04,1.0,0.96])**d
    p=ease((t-C['neon']['draw'][0])/(C['neon']['draw'][1]-C['neon']['draw'][0]))
    if p>0:
        SS=4; core=np.zeros((H*SS,W*SS),np.float32); L=4*p; pts=[Q[0]]
        for e in range(4):
            if L<=e: break
            a,b=Q[e],Q[(e+1)%4]; pts.append(a+(b-a)*min(L-e,1))
        cv2.polylines(core,[np.round(np.array(pts)*SS*16).astype(np.int32)],False,1.0,int(C['neon']['width']*SS),cv2.LINE_AA,4)
        core=cv2.resize(core,(W,H),interpolation=cv2.INTER_AREA); col=np.array(C['neon']['color_bgr'],np.float32)/255
        g=core[...,None]*np.array([1,0.97,0.75])*0.5+cv2.GaussianBlur(core,(0,0),3)[...,None]*col*1.9+cv2.GaussianBlur(core,(0,0),10)[...,None]*col*0.9+cv2.GaussianBlur(core,(0,0),28)[...,None]*col*0.4
        o=255-(255-o)*(1-np.clip(g,0,1))
    cv2.imwrite(f'{tmp}/{i:04d}.png',np.clip(o,0,255).astype(np.uint8)); i+=1
subprocess.run(['ffmpeg','-loglevel','error','-y','-framerate',str(fps),'-i',f'{tmp}/%04d.png','-vf','scale=1080:1920:flags=lanczos','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',out],check=True)
print('frames',i,'fps',fps,'→',out)
