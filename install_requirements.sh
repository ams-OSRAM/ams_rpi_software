#!/usr/bin/env bash
################################
# Uninstall apt and pip packages
# Use self-built ones instead
################################
sudo apt remove -y rpicam-apps libcamera-dev libcamera-tools libcamera0 python3-libcamera python3-picamera2 || true
sudo apt remove -y libepoxy-dev || true
sudo apt install -y python3-opencv
################################
# Nginx forwards port 80 to 8000
################################
sudo apt install -y nginx


#################################
# libcamera prerequisites
# [ref](https://www.raspberrypi.com/documentation/computers/camera_software.html)
#################################
sudo apt install -y python3-pip git python3-jinja2
sudo apt install -y libboost-dev
sudo apt install -y libgnutls28-dev openssl libtiff5-dev pybind11-dev
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
sudo apt install -y meson cmake
sudo apt install -y python3-yaml python3-ply
sudo apt install -y libglib2.0-dev libgstreamer-plugins-base1.0-dev

#################################
# rpicam-apps / rpicam-apps prerequisites
# [ref](https://www.raspberrypi.com/documentation/computers/camera_software.html)
#################################
sudo apt install -y cmake libboost-program-options-dev libdrm-dev libexif-dev
sudo apt install -y meson ninja-build
sudo apt install -y libavcodec-dev libavdevice-dev libavformat-dev libswresample-dev
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
# sudo apt-get install -y libx264-dev libjpeg-dev
# # install the remaining plugins
# sudo apt-get install -y libgstreamer1.0-dev \
#      libgstreamer-plugins-base1.0-dev \
#      libgstreamer-plugins-bad1.0-dev \
#      gstreamer1.0-plugins-ugly \
#      gstreamer1.0-tools \
#      gstreamer1.0-gl \
#      gstreamer1.0-gtk3
# # if you have Qt5 install this plugin
# sudo apt-get install -y gstreamer1.0-qt5
# # install if you want to work with audio
# sudo apt-get install -y gstreamer1.0-pulseaudio



#################################
# picamera2 prerequisites
# [ref](https://github.com/raspberrypi/picamera2)
# Note: skip python3-libcamera, use self-built one
#################################
# sudo apt install -y python3-kms++ libcap-dev
# sudo apt install -y python3-pyqt5 python3-prctl libatlas-base-dev ffmpeg python3-pip python3-opengl
# sudo apt install -y python3-picamera2
#################################
# libcamera optional components
# [ref](https://libcamera.org/getting-started.html)
#################################
# install dependencies for if Dcam=enabled
# sudo apt install -y libevent-dev
# install dependencies for Dqcam=enabled
# sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5 qttools5-dev-tools libtiff-dev

