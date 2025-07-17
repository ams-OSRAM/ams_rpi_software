#!/usr/bin/env bash
sudo apt-get -y install python3-venv
python -m venv venv --system-site-packages
sudo apt -y remove python3-pidng
source venv/bin/activate
pip3 install -r requirements.txt
#cp setup_picamera2.py ./picamera2/setup.py
pip3 install ./picamera2
#pip3 install "numpy>2.0.0"
#pip3 install v4l2-python3
#################################
# libcamera optional components
# [ref](https://libcamera.org/getting-started.html)
#################################
#pip3 install rawpy
#pip3 install imageio
#pip3 install "scipy<1.12.5"
################################
# Uninstall apt and pip packages
# Use self-built ones instead
################################
#pip3 install pillow==9.4.0
