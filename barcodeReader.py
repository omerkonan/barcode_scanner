#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import numpy as np
from pyzbar import pyzbar

    
class BarcodeReader():
    def __init__(self):
        self.barcode_image = None
        self.barcode_info = None
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1080)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
        self.cap.set(cv2.CAP_PROP_FPS, 10)
        print(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        print(self.cap.get(cv2.CAP_PROP_FPS ))
        while (self.cap.isOpened()):
            success, self.frame = self.cap.read()
            if (success):
                self.binary_img = self.filter_frame()
                self.find_bigggest_contour()
                if not (self.barcode_image.size == 0):
                    for barcode in pyzbar.decode(self.barcode_image):
                        x, y , w, h = barcode.rect
                        cv2.rectangle(self.barcode_image, (x, y),(x+w, y+h), (0, 0, 255), 2)
                        self.barcode_info = barcode.data.decode('utf-8')
                        if not self.barcode_info:
                            break
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(self.barcode_image, self.barcode_info, (x + 6, y - 6), font, 1.0, (255, 0, 0), 1)
                    if self.barcode_info:
                        print("Barcode detected. Barcode: ", self.barcode_info)
                        cv2.imshow("barcode_image" ,self.barcode_image)  
                        
                          
                self.barcode_info = None
                cv2.imshow("Frame" ,self.frame)
                if cv2.waitKey(1) == ord('q'):
                    break
                
        self.cap.release()
        cv2.destroyAllWindows()
                    
    def filter_frame(self):
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        ret3, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        return thresh
    
    def find_bigggest_contour(self):
        contours, _ = cv2.findContours(self.binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        biggest_cnt = max(contours, key = cv2.contourArea)
        # hull = cv2.convexHull(c)
        # cv2.drawContours(self.frame, [biggest_cnt], -1, (0, 255, 0), 3)   
        self.get_barcode_area(biggest_cnt)
        
        
    def get_barcode_area(self, c):
        
        x,y,w,h = cv2.boundingRect(c)
        # print(x,y,w,h)
        pts1 = np.float32([[x, y], [x+w, y], [x, y+h], [x+w, y+h]])
        pts2 = np.float32([[0, 0], [0+w, 0], [0, h], [w,h]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        self.barcode_image = cv2.warpPerspective(self.frame, matrix, (w,h))
        cv2.imshow("img", self.barcode_image)
            


def main():
    barcode_reader = BarcodeReader()
if __name__ == '__main__':
    main()
    