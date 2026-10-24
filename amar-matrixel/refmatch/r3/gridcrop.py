import cv2,sys
W,f,x0,x1,y0,y1,s,out=sys.argv[1],int(sys.argv[2]),*[int(v) for v in sys.argv[3:7]],float(sys.argv[7]),sys.argv[8]
im=cv2.imread(f"{W}/frames/{f+1:04d}.png")[y0:y1,x0:x1]; im=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
for x in range((x0//20+1)*20,x1,20):
    X=int((x-x0)*s); cv2.line(im,(X,0),(X,im.shape[0]),(0,255,255) if x%100==0 else (0,120,120),1)
    if x%100==0 or True: cv2.putText(im,str(x),(X+2,12),0,0.4,(0,255,255),1)
for y in range((y0//20+1)*20,y1,20):
    Y=int((y-y0)*s); cv2.line(im,(0,Y),(im.shape[1],Y),(0,255,255) if y%100==0 else (0,120,120),1); cv2.putText(im,str(y),(2,Y-2),0,0.4,(0,255,255),1)
cv2.imwrite(out,im)
