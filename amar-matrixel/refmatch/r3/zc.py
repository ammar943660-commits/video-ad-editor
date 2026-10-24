import cv2,sys
img,x0,x1,y0,y1,s,out=sys.argv[1],*[int(v) for v in sys.argv[2:6]],float(sys.argv[6]),sys.argv[7]
im=cv2.imread(img)[y0:y1,x0:x1]; im=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
for x in range((x0//25+1)*25,x1,25):
    X=int((x-x0)*s); c=(0,255,255) if x%100==0 else (0,130,130); cv2.line(im,(X,0),(X,im.shape[0]),c,1)
    if x%50==0: cv2.putText(im,str(x),(X+2,12),0,0.45,(0,255,255),1)
for y in range((y0//25+1)*25,y1,25):
    Y=int((y-y0)*s); c=(0,255,255) if y%100==0 else (0,130,130); cv2.line(im,(0,Y),(im.shape[1],Y),c,1)
    if y%50==0: cv2.putText(im,str(y),(2,Y-2),0,0.45,(0,255,255),1)
cv2.imwrite(out,im)
