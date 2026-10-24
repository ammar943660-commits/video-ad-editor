#!/usr/bin/env python3
"""comp1.py — تركيب R1: plate + طبقة Blender (كاميرا ثابتة = فريم 0) مُزاحة بـhomography حركة الكاميرا لكل فريم + وميض حلقة ذهبية 2D (الختام).
   python3 comp1.py <work> <layer_dir> <out_dir> [cmp.jpg] f..."""
import cv2,numpy as np,sys,os,json,math
W,LD,O=sys.argv[1:4]; rest=sys.argv[4:]; cmp_=rest[0] if rest and rest[0].endswith('.jpg') else None; fs=[int(x) for x in (rest[1:] if cmp_ else rest)]
os.makedirs(O,exist_ok=True); H=np.load(f'{W}/H_r1.npy'); D=os.path.dirname(os.path.abspath(__file__)); RG=json.load(open(f'{D}/r1_cfg.json')).get('ring',{"f":[266,292],"center":[555,300],"rx":[60,700],"ry":[20,230]})
rows=[]
for i in fs:
    p=cv2.imread(f'{W}/plate/{i+1:04d}.png').astype(np.float32)
    rf=cv2.imread(f'{W}/frames/{i+1:04d}.png').astype(np.float32); reg=(slice(100,250),slice(0,300))   # تصحيح لوني متبقٍّ من المرجع (مبانٍ بلا مؤثرات)
    g=np.median(rf[reg].reshape(-1,3),0)/np.maximum(np.median(p[reg].reshape(-1,3),0),1); p=p*np.clip(g,0.8,1.4)
    b=cv2.imread(f'{LD}/{i+1:04d}.png',-1)
    if b is not None:
        if b.shape[:2]!=p.shape[:2]: b=cv2.resize(b,(p.shape[1],p.shape[0]),interpolation=cv2.INTER_CUBIC)
        b=cv2.warpPerspective(b,H[i],(p.shape[1],p.shape[0]),flags=cv2.INTER_LINEAR); al=b[:,:,3:4].astype(np.float32)/255; p=p*(1-al)+b[:,:,:3].astype(np.float32)*al
    u=(i-RG['f'][0])/(RG['f'][1]-RG['f'][0])
    if 0<u<1:
        L=np.zeros(p.shape[:2],np.float32); cx,cy=RG['center']; rx=RG['rx'][0]+(RG['rx'][1]-RG['rx'][0])*u; ry=RG['ry'][0]+(RG['ry'][1]-RG['ry'][0])*u
        rnd=np.random.RandomState(7)
        for k in range(60):
            a0=rnd.uniform(0,360); sweep=rnd.uniform(20,70); jit=rnd.uniform(0.85,1.15)
            cv2.ellipse(L,(int(cx),int(cy)),(int(rx*jit),int(ry*jit)),0,a0,a0+sweep,float(rnd.uniform(0.3,1)),2,cv2.LINE_AA)
        L*=math.sin(math.pi*u)**0.7; g=cv2.GaussianBlur(L,(0,0),3)*1.5+cv2.GaussianBlur(L,(0,0),12)*1.2
        p=p+np.stack([g*60,g*170,g*255],2)
    o=np.clip(p,0,255).astype(np.uint8); cv2.imwrite(f'{O}/{i+1:04d}.png',o)
    if cmp_:
        a=cv2.imread(f'{W}/frames/{i+1:04d}.png'); 
        for im,t in ((a,'REF'),(o,'OURS')): cv2.putText(im,f'{t} t={i/30:.2f}s',(8,22),0,0.65,(255,255,255),2)
        rows.append(np.hstack([cv2.resize(a,(760,427)),cv2.resize(o,(760,427))]))
if cmp_: cv2.imwrite(cmp_,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,88])
