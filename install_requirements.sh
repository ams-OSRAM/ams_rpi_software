#!/usr/bin/env bash
#################################
# libcamera prerequisites
# [ref](https://www.raspberrypi.com/documentation/computers/camera_software.html)
#################################
sudo apt install -y python3-pip git python3-jinja2
# sudo pip3 install jinja2
# sudo apt install -y libboost-dev
# sudo apt install -y libgnutls28-dev openssl libtiff5-dev
# sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
# sudo apt install -y meson
# sudo pip3 install pyyaml ply
# sudo pip3 install --upgrade meson
# sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev
# python3-dev needed for python binding of pycamera
sudo apt install -y python3-dev
# opencv is needed for some mira sensor scripts
sudo apt install -y python3-opencv
sudo apt install -y libboost-dev
sudo apt install -y libgnutls28-dev openssl libtiff5-dev pybind11-dev
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
sudo apt install -y meson cmake
sudo apt install -y python3-yaml python3-ply
sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev
###############################
# Linux kernel prerequisites
# [ref](https://www.raspberrypi.com/documentation/computers/linux_kernel.html)
###############################
sudo apt install -y git bc bison flex libssl-dev make

##############################
# gstreamer (for preview window) prerequisites
# [ref](https://qengineering.eu/install-gstreamer-1.18-on-raspberry-pi-4.html)
##############################
# install a missing dependency
sudo apt-get install -y libx264-dev libjpeg-dev
# install the remaining plugins
sudo apt-get install -y libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev \
     libgstreamer-plugins-bad1.0-dev \
     gstreamer1.0-plugins-ugly \
     gstreamer1.0-tools \
     gstreamer1.0-gl \
     gstreamer1.0-gtk3
# if you have Qt5 install this plugin
sudo apt-get install -y gstreamer1.0-qt5
# install if you want to work with audio
sudo apt-get install -y gstreamer1.0-pulseaudio

#################################
# libcamera-apps prerequisites
# [ref](https://www.raspberrypi.com/documentation/computers/camera_software.html)
#################################
sudo apt install -y cmake libboost-program-options-dev libdrm-dev libexif-dev
# requirements for libepoxy
sudo apt install -y libegl1-mesa-dev
# Add libav support in libcamera-vid
sudo apt install -y libavcodec-dev libavdevice-dev libavformat-dev libswresample-dev


#################################
# picamera prerequisites
# [ref](https://github.com/raspberrypi/picamera2)
# Note: skip python3-libcamera, use self-built one
#################################
sudo apt install -y python3-kms++
sudo apt install -y python3-pyqt5 python3-prctl libatlas-base-dev ffmpeg python3-pip
pip3 install "numpy<2.0.0"
sudo apt uninstall python3-v4l2
pip3 install v4l2-python3
#################################
# libcamera optional components
# [ref](https://libcamera.org/getting-started.html)
#################################
# install dependencies for if Dcam=enabled
sudo apt install -y libevent-dev
# install dependencies for Dqcam=enabled
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5 qttools5-dev-tools libtiff-dev
###############################
# Picamera2 ams app components
##############################
sudo pip3 install rawpy
sudo pip3 install imageio
pip3 install "scipy<1.12.5"
################################
# Uninstall apt and pip packages
# Use self-built ones instead
################################
sudo apt remove -y libcamera-apps libcamera-dev libcamera-tools libcamera0 python3-libcamera
sudo pip uninstall -y picamera2
sudo apt remove -y libepoxy-dev
################################
# USB and WEB functionality
#
################################
#sudo pip3 install pyro5
################################
# Nginx forwards port 80 to 8000
################################
sudo apt install -y nginx
pip3 install pillow==9.4.0
