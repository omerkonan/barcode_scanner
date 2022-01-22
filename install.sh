sudo apt-get install -y libcblas-dev
sudo apt-get install -y libhdf5-dev
sudo apt-get install -y libhdf5-serial-dev
sudo apt-get install -y libatlas-base-dev
sudo apt-get install -y libjasper-dev
sudo apt-get install -y libqtgui4
sudo apt-get install -y libqt4-test


pip3 install --upgrade pip setuptools wheel
pip3 install --upgrade pip
pip3 install opencv-python==4.5.4.60
pip3 install -U numpy
pip3 install pyzbar
pip3 install pyroute2
pip3 install azure-iot-device
pip3 install -r $PWD/libs/mic_hat/requirements.txt
 
cd $PWD/libs/RaspiWiFi;
chmod +x initial_setup.py
chmod +x setup_lib.py
sudo python3 initial_setup.py
