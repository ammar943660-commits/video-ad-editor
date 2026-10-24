#!/usr/bin/env python3
"""glyph_overlay.py — يرسم هياكل الحروف (strokes) فوق صورة المرجع المعدَّلة لمراجعة الانطباق. python3 glyph_overlay.py <work> glyphs/x.json out.jpg [x0 x1]"""
import sys,json,cv2,numpy as np
W,gj,out=sys.argv[1:4]; G=json.load(open(gj)); im=cv2.imread(f"{W}/{G['image']}")
x0,x1=(int(sys.argv[4]),int(sys.argv[5])) if len(sys.argv)>5 else (0,im.shape[1])
ov=np.zeros(im.shape[:2],np.uint8)
def draw(img,color,t):
    for s in G['strokes']:
        if s['type']=='circle': cv2.circle(img,tuple(map(int,s['c'])),int(s['r']),color,t)
        else:
            pts=np.array(s['pts'],np.int32)
            if t<0: cv2.polylines(img,[pts],False,color,int(s['w']),cv2.LINE_AA)
            for p in pts: 
                if t<0: cv2.circle(img,tuple(p),int(s['w']/2),color,-1) if s.get('cap')=='round' or True else None
            cv2.polylines(img,[pts],False,color,2,cv2.LINE_AA) if t>=0 else None
vis=im.copy(); layer=im.copy(); draw(layer,(0,255,255),-1); vis=cv2.addWeighted(im,0.55,layer,0.45,0)
for s in G['strokes']:
    c=s['c'] if s['type']=='circle' else s['pts'][0]; cv2.putText(vis,s['id'],(int(c[0])-20,int(c[1])),0,0.45,(0,0,255),1)
cv2.imwrite(out,np.hstack([im[:,x0:x1],vis[:,x0:x1]]) if (x1-x0)<900 else np.vstack([im[:,x0:x1],vis[:,x0:x1]]))
