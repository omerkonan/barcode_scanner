sudo apt-get install libcblas-dev
sudo apt-get install libhdf5-dev
sudo apt-get install libhdf5-serial-dev
sudo apt-get install libatlas-base-dev
sudo apt-get install libjasper-dev
sudo apt-get install libqtgui4
sudo apt-get install libqt4-test

pip3 install -r requirements.txt
cd /libs/RaspiWiFi/
chmod +x initial_setup.py
chmod +x setup_lib.py
sudo python3 initial_setup.py