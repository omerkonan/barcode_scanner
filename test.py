# import qrtools
import cv2
from pyzbar.pyzbar import decode
# qr = qrtools.QR()
cap = cv2.VideoCapture(0)
success, frame = cap.read()
while(True):
    success, img = cap.read()
    detector = cv2.barcode_BarcodeDetector()
    # detect and decode
    ok, decoded_info, decoded_type, corners = detector.detectAndDecode(img)
    print("test",decoded_info)
    for barcode in decode(img):
        myData = barcode.data.decode('utf-8')
        print("pyzbar", myData)   
    cv2.imshow('Scaniie',img)
    cv2.waitKey(1)

# qr.decode("barcode_from_client.png")

