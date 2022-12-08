#!/usr/bin/env bash
#################################
# libcamera prerequisites
# [ref](https://www.raspberrypi.com/documentation/accessories/camera.html)
#################################
sudo apt install -y python3-pip git
sudo pip3 install jinja2
sudo apt install -y libboost-dev
sudo apt install -y libgnutls28-dev openssl libtiff5-dev
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
sudo apt install -y meson
sudo pip3 install pyyaml ply
sudo pip3 install --upgrade meson
sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev
# python3-dev needed for python binding of pycamera
sudo apt install -y python3-dev

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
# [ref](https://www.raspberrypi.com/documentation/accessories/camera.html)
#################################
sudo apt install -y cmake libboost-program-options-dev libdrm-dev libexif-dev
#requirements for libepoxy
sudo apt install -y libegl1-mesa-dev

#################################
# picamera prerequisites
# [ref](https://github.com/raspberrypi/picamera2)
# Note: skip python3-libcamera, use self-built one
#################################
sudo apt install -y python3-kms++
sudo apt install -y python3-pyqt5 python3-prctl libatlas-base-dev ffmpeg python3-pip
pip3 install numpy --upgrade

#################################
# libcamera optional components
# [ref](https://libcamera.org/getting-started.html)
#################################
# install dependencies for if Dcam=enabled
sudo apt install -y libevent-dev
# install dependencies for Dqcam=enabled
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5 qttools5-dev-tools libtiff-dev

################################
# Uninstall apt and pip packages
# Use self-built ones instead
################################
sudo apt remove -y libcamera-apps libcamera-dev libcamera-tools libcamera0 python3-libcamera
sudo pip uninstall picamera2

