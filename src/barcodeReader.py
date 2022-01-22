#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
sys.path.append("..")
import os
import cv2
import time
import asyncio
import subprocess
import numpy as np
import urllib.request 
from time import sleep
import RPi.GPIO as GPIO
from pyzbar import pyzbar
from pyroute2 import IPRoute
from libs.mic_hat.interfaces import pixels
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from device_provisioning_service import Device
class BarcodeReader():
    def __init__(self):

        self.pixels = pixels.Pixels()
        self.pixels.off()
        self.lights()
        self.unsend_barcode_info = None
        self.button_last_timer= None
        self.barcode_image = None
        self.barcode_info = None
        self.last_read_barcode_info = None
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 540)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        # print(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # print(self.cap.get(cv2.CAP_PROP_FPS ))
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
                        self.pixels.off()
                        if (self.barcode_info != self.last_read_barcode_info):
                            self.last_read_barcode_info = self.barcode_info
                            self.pixels.think()
                            self.beepsound()
                            self.pixels.off()
                            is_online = self.get_connection_status()
                            if (is_online):
                                if self.unsend_barcode_info:
                                    for local_barcode_infos in self.unsend_barcode_info:
                                        self.getproductinfo(local_barcode_infos)
                                        local_barcode_details = self.getproductinfo(self.barcode_info)
                                        asyncio.run(self.iotsendmsg(local_barcode_details))
                                                    
                                self.getproductinfo(self.barcode_info)
                                barcode_details = self.getproductinfo(self.barcode_info)
                                asyncio.run(self.iotsendmsg(barcode_details))
                            else:
                                # print('local save method will be added')
                                self.unsend_barcode_info.append(self.barcode_info)
                                
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(self.barcode_image, self.barcode_info, (x + 6, y - 6), font, 1.0, (255, 0, 0), 1)
                    if self.barcode_info:
                        print("Barcode detected. Barcode: ", self.barcode_info)
                        #cv2.imshow("barcode_image" ,self.barcode_image)  
                        
                          
                    self.barcode_info = None
                    # cv2.imshow("Frame" ,self.frame)
                    if cv2.waitKey(1) == ord('q'):
                        break
                
        self.cap.release()
        cv2.destroyAllWindows()

              
    def get_connection_status(self):
        try:
            IPRoute().route('get', dst='8.8.8.8')
            return True
        except:
            return False
        
    def lights(self):
        self.pixels.wakeup()
        self.pixels.think()
        time.sleep(3)
        self.pixels.speak()
        time.sleep(3)
        self.pixels.off()
        
    def beepsound(self):
        subprocess.call(['aplay scn_bp.wav'], shell = True)

    def pleasebeep(self):
        GPIO.setmode(GPIO.BCM)
        buzzTime = 0.1
        buzzDelay = 2
        buzzerPin = 4
        GPIO.setup(buzzerPin, GPIO.OUT)
        GPIO.output(buzzerPin, True)
        sleep(buzzTime)
        GPIO.output(buzzerPin, False)  
        
        
    async def iotsendmsg(self, msgtoaz):
        connection_string = "HostName=ScaniieProd.azure-devices.net;DeviceId=scndev;SharedAccessKey=ZhVQ0tDUhgICNPL2SKwGMR9MMtIr1GdXxpkIEZjyIuA="
        device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
        await device_client.connect()
        # print (msgtoaz)
        # Send the message.
        await device_client.send_message(msgtoaz)
        # finally, disconnect
        await device_client.disconnect()

    def getproductinfo(self, barcode):
            request = urllib.request.urlopen('https://api.ean-search.org/api?token=5d0bcaaad5b03b9a3f06a3d170bf0998572765f1c0822075ff&op=barcode-lookup&format=json&ean=%s'% (barcode))    
            response_body = request.read()
            return(response_body.decode('utf-8'))


                      
    def filter_frame(self):
        gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        ret3, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        return thresh
    
    def find_bigggest_contour(self):
        contours, _ = cv2.findContours(self.binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        biggest_cnt = max(contours, key = cv2.contourArea)
        self.get_barcode_area(biggest_cnt)
        
        
    def get_barcode_area(self, c):
        
        x,y,w,h = cv2.boundingRect(c)
        # print(x,y,w,h)
        pts1 = np.float32([[x, y], [x+w, y], [x, y+h], [x+w, y+h]])
        pts2 = np.float32([[0, 0], [0+w, 0], [0, h], [w,h]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        self.barcode_image = cv2.warpPerspective(self.frame, matrix, (w,h))
        # cv2.imshow("img", self.barcode_image)
            


def main():
    
    barcode_reader = BarcodeReader()
    
if __name__ == '__main__':
    main()
    