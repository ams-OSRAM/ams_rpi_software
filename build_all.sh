#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"

UNAME_MACHINE=`uname -m`

# clone libcamera source, and checkout a proved commit
# Latest tested commit is on 2022 August 21st.
LIBCAMERA_COMMIT=6c6289ee184d79
# Previous tested commit is on 2022 April 4th.
# LIBCAMERA_COMMIT=302731cd
if [[ ! -d $PWD/libcamera ]]
then
	echo "Clone libcamera source and checkout commit id ${LIBCAMERA_COMMIT}"
	git clone https://git.libcamera.org/libcamera/libcamera.git
    (cd $PWD/libcamera && git checkout $LIBCAMERA_COMMIT)
fi

# apply patches and sources
echo "Applying patches to libcamera source"
(cd $PWD/mira220/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/mira220/src && ./apply_src.sh)
echo "Applying patches to libcamera source"
(cd $PWD/mira050/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/mira050/src && ./apply_src.sh)


# config, build, and install libcamera
echo "Inside libcamera dir, configure the build with meson"
# The meson build options are from raspberry pi doc on libcamera
# ref https://www.raspberrypi.com/documentation/accessories/camera.html
# Meson build options are only configured if this scripts runs on RPI
if [[ "$UNAME_MACHINE" == "armv7l" || "$UNAME_MACHINE" == "armv8" || "$UNAME_MACHINE" == "aarch64" ]]
then
	(cd $PWD/libcamera && meson build --buildtype=release -Dpipelines=raspberrypi -Dipas=raspberrypi -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled)
else
	(cd $PWD/libcamera && meson build)
fi
echo "Inside libcamera dir, build and install with ninja"
(cd $PWD/libcamera && ninja -C build -j 2 )
(cd $PWD/libcamera && sudo ninja -C build install )
echo "Post-installation update"
sudo ldconfig

# Only continue to build libcamera-apps and picamera2 if this scripts runs on RPI
# When this script runs on onther hosts, for example, x86_64 that runs Jenkins, skip libcamera-apps and picamera2.
if [[ "$UNAME_MACHINE" == "armv7l" || "$UNAME_MACHINE" == "armv8" || "$UNAME_MACHINE" == "aarch64" ]]
then
        echo "This script runs on ${UNAME_MACHINE} machine, assuming a Raspberry Pi. Continue with libcamerae-apps and picamera2."
else
        echo "This script runs on ${UNAME_MACHINE} machine, assuming not a Raspberry Pi. Skip libcamerae-apps and picamera2."
        exit 0
fi

# clone libcamera-apps source, and checkout a proved commit
# Latest tested commit is on 2022 August 10th.
LIBCAMERA_APPS_COMMIT=e1beb45
if [[ ! -d $PWD/libcamera-apps ]]
then
        echo "Clone libcamera-apps source and checkout commit id ${LIBCAMERA_APPS_COMMIT}"
        git clone https://github.com/raspberrypi/libcamera-apps.git
	(cd $PWD/libcamera-apps && git checkout $LIBCAMERA_APPS_COMMIT)
fi

echo "Inside libcamera-apps dir, create a build dir"
(cd $PWD/libcamera-apps && mkdir -p build)
echo "Inside libcamera-apps/build dir, use cmake to configure the build"
(cd $PWD/libcamera-apps/build && cmake .. -DENABLE_DRM=1 -DENABLE_X11=1 -DENABLE_QT=1 -DENABLE_OPENCV=0 -DENABLE_TFLITE=0)
echo "Inside libcamera-apps/build dir, build and install"
(cd $PWD/libcamera-apps/build && make -j4)  # use -j1 on Raspberry Pi 3 or earlier devices
(cd $PWD/libcamera-apps/build && sudo make install)
(cd $PWD/libcamera-apps/build && sudo ldconfig) # this is only necessary on the first build

# clone picamera2 source, and checkout a proved commit
# Latest tested commit is on 2022 August 22th.
PICAMERA2_COMMIT=18cda82
if [[ ! -d $PWD/picamera2 ]]
then
        echo "Clone picamera2 source and checkout commit id ${PICAMERA2_COMMIT}"
        git clone https://github.com/raspberrypi/picamera2.git
	(cd $PWD/picamera2 && git checkout $PICAMERA2_COMMIT)
fi

# Installation commands are from the readme of picamera2 repo
# Picamera2 source code is not needed for installation, but the picamera2/examples codes are useful for testing
sudo apt install -y python3-libcamera python3-kms++
sudo apt install -y python3-pyqt5 python3-prctl libatlas-base-dev ffmpeg python3-pip
pip3 install numpy --upgrade
pip3 install picamera2

