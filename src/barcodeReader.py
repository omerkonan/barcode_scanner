#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import cv2
import time
import pygame
import asyncio
import numpy as np
import urllib.request 
from time import sleep
from pyzbar import pyzbar
import RPi.GPIO as GPIO
from pixels import Pixels
from azure.iot.device import Message
from azure.iot.device.aio import IoTHubDeviceClient
from device_provisioning_service import Device
import RaspiWiFi.setup_lib as setup_lib

class BarcodeReader():
    def __init__(self, btn_input, entered_ssid, wpa_enabled_choice, wpa_entered_key, auto_config_choice, auto_config_delay, server_port_choice, ssl_enabled_choice):
        self.timeout = 6
        self.entered_ssid = entered_ssid
        self.wpa_enabled_choice = wpa_enabled_choice
        self.wpa_entered_key = wpa_entered_key
        self.auto_config_choice = auto_config_choice
        self.auto_config_delay = auto_config_delay
        self.server_port_choice = server_port_choice
        self.ssl_enabled_choice = ssl_enabled_choice
        self.btn_input = btn_input
        GPIO.setwarnings(False) 
        GPIO.setmode(GPIO.BOARD) 
        GPIO.setup(self.btn_input, GPIO.IN) 
        GPIO.add_event_detect(self.btn_input, GPIO.RISING, callback=self.buttonEventHandler_rising) 
        GPIO.add_event_detect(self.btn_input, GPIO.FALLING, callback=self.buttonEventHandler_falling)
        self.pixels = Pixels()
        self.pixels.off()
        self.lights()
        self.button_last_timer= None
        self.barcode_image = None
        self.barcode_info = None
        self.last_read_barcode_info = None
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
                        self.pixels.off()
                        if (self.barcode_info != self.last_read_barcode_info):
                            self.last_read_barcode_info = self.barcode_info
                            self.pixels.think()
                            self.beepsound()
                            self.getproductinfo(self.barcode_info)
                            barcode_details = self.getproductinfo(self.barcode_info)
                            asyncio.run(self.iotsendmsg(barcode_details))
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
        
    def buttonEventHandler_falling(self):
        self.button_last_timer = time.time()
        
    def buttonEventHandler_rising(self):
        now = time.time()
        if(now-self.button_last_timer >= self.timeout):
            self.open_hotspot()
            
    def open_hotspot(self):
        setup_lib.install_prereqs()
        setup_lib.copy_configs(self.wpa_enabled_choice)
        setup_lib.update_main_config_file(self.entered_ssid, self.auto_config_choice, self.auto_config_delay, self.ssl_enabled_choice, self.server_port_choice, self.wpa_enabled_choice, self.wpa_entered_key)
        os.system('sudo reboot')
        
    def lights(self):
        self.pixels.wakeup()
        self.pixels.think()
        time.sleep(3)
        self.pixels.speak()
        time.sleep(3)
        self.pixels.off()
        
    def beepsound(self):
        pygame.mixer.init()
        pygame.mixer.music.load('/scaniie/final/beep.wav')
        pygame.mixer.music.play()

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
        print (msgtoaz)
        # Send the message.
        await device_client.send_message(msgtoaz)
        # finally, disconnect
        await device_client.disconnect()

    def getproductinfo(self, barcode):
            request = urllib.request.urlopen('https://api.ean-search.org/api?token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&op=barcode-lookup&format=json&ean=%s'% (barcode))    
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
    button = 17
    entered_ssid = "SCANIIE"
    wpa_enabled_choice = True
    wpa_entered_key = "123456789"
    auto_config_choice = False
    auto_config_delay = ""
    server_port_choice = 80
    ssl_enabled_choice = False
    barcode_reader = BarcodeReader(button, entered_ssid, wpa_enabled_choice, wpa_entered_key, auto_config_choice, auto_config_delay, server_port_choice, ssl_enabled_choice)
    
if __name__ == '__main__':
    main()
    