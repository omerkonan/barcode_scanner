from time import sleep
import RPi.GPIO as GPIO
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import time
import asyncio
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from device_provisioning_service import Device
import urllib.request
from pixels import Pixels

pixels = Pixels()
pixels.off()

async def iotsendmsg(msgtoaz):

    connection_string = "HostName=ScaniieProd.azure-devices.net;DeviceId=scndev;SharedAccessKey=ZhVQ0tDUhgICNPL2SKwGMR9MMtIr1GdXxpkIEZjyIuA="
    device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)
    await device_client.connect()
    print (msgtoaz)
    # Send the message.
    await device_client.send_message(msgtoaz)
    # finally, disconnect
    await device_client.disconnect()

def getproductinfo(barcode):
        request = urllib.request.urlopen('https://api.ean-search.org/api?token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&op=barcode-lookup&format=json&ean=%s'% (barcode))    
        response_body = request.read()
        return(response_body.decode('utf-8'))



def pleasebeep():
        GPIO.setmode(GPIO.BCM)
        buzzTime = 0.1
        buzzDelay = 2
        buzzerPin = 4
        GPIO.setup(buzzerPin, GPIO.OUT)
        GPIO.output(buzzerPin, True)
        sleep(buzzTime)
        GPIO.output(buzzerPin, False)

def beepsound():
    pygame.mixer.init()
    pygame.mixer.music.load('/scaniie/final/beep.wav')
    pygame.mixer.music.play()

def lights():
    pixels.wakeup()
    pixels.think()
    time.sleep(3)
    pixels.speak()
    time.sleep(3)
    pixels.off()


#last_code = None

def getbarcode():
    #global last_code
    lights()
    cap = cv2.VideoCapture(0)
    cap.set(3,320)
    cap.set(4,240)
    last_code = None
    while True:
        success, img = cap.read()
        for barcode in decode(img):
            myData = barcode.data.decode('utf-8')
            #print(myData)
            pixels.off()
            if myData != last_code:
                last_code = myData
                #pleasebeep()
                pixels.think()
                beepsound()
                getproductinfo(myData)
                barcodeinfo = getproductinfo(myData)
                asyncio.run(iotsendmsg(barcodeinfo))
            #print(last_code)
        #cv2.imshow('Scaniie',img)
        #cv2.waitKey(1)

getbarcode()