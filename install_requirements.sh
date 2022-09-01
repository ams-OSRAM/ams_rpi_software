#!/usr/bin/env bash
#requirements for libcamera
sudo apt install -y python3-pip git
sudo pip3 install jinja2
sudo apt install -y libboost-dev
sudo apt install -y libgnutls28-dev openssl libtiff5-dev
sudo apt install -y qtbase5-dev libqt5core5a libqt5gui5 libqt5widgets5
sudo apt install -y meson
sudo pip3 install pyyaml ply
sudo pip3 install --upgrade meson

#requirements for libcamera-apps
sudo apt install -y cmake libboost-program-options-dev libdrm-dev libexif-dev

#requirements for libepoxy
sudo apt install -y libegl1-mesa-dev


