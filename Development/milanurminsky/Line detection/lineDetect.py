import cv2

#load images
img = cv2.imread("image.jpg",0)
output_img = cv2.imread("white.jpg",0)
#threshold image into binary colored
ret,thresh1 = cv2.threshold(img,180,255,cv2.THRESH_BINARY)
#detect edges in image using canny algorithm
edges = cv2.Canny(thresh1,50,150,apertureSize = 3)
#write into new image
cv2.imwrite('canny.jpg',edges)

#detect lines and extend them / hough transformation
lines = cv2.HoughLines(edges,1,np.pi/100,130)
for rho,theta in lines[0]:
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a*rho
    y0 = b*rho
    x1 = int(x0 + 1000*(-b))
    y1 = int(y0 + 1000*(a))
    x2 = int(x0 - 1000*(-b))
    y2 = int(y0 - 1000*(a))

    cv2.line(output_img,(x1,y1),(x2,y2),(0,0,255),2)

#output created lines into new image
cv2.imwrite('white_new.jpg',output_img)
