#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"
TOPDIR=${PWD}

version=$( cat /etc/os-release | grep -oP "[0-9]+" | head -1 )

cd $TOPDIR/rpicam-apps
meson setup build -Denable_libav=enabled -Denable_drm=enabled -Denable_egl=enabled -Denable_qt=enabled -Denable_opencv=disabled -Denable_tflite=disabled -Denable_hailo=disabled



#meson setup build -Denable_libav=true -Denable_drm=true -Denable_egl=true -Denable_qt=true -Denable_opencv=false -Denable_tflite=false
echo "Inside rpicam-apps dir, build and install with ninja"
meson compile -C build -j 2
sudo meson install -C build
#sudo ninja -C build install
cd $TOPDIR
echo "Post-installation update"
sudo ldconfig
