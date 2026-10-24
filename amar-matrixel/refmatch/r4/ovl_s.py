import cv2,numpy as np,json,sys
W=sys.argv[1]; out=sys.argv[2]; fs=[int(x) for x in sys.argv[3:]]; T=json.load(open(f'{W}/lot_track.json'))['snapped']
ims=[]
for f in fs:
    a=cv2.imread(f'{W}/frames/{f+1:04d}.png'); q=np.array(T[f])
    cv2.polylines(a,[np.round(q).astype(np.int32)],True,(0,0,255),2); cv2.putText(a,str(f),(10,30),0,1,(0,0,255),2); ims.append(cv2.resize(a,(573,322)))
while len(ims)%3: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out,np.vstack([np.hstack(ims[i:i+3]) for i in range(0,len(ims),3)]))
