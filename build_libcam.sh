#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"


# config, build, and install libcamera
echo "Inside libcamera dir, configure the build with meson"
# The meson build options are from raspberry pi doc on libcamera
# ref https://www.raspberrypi.com/documentation/accessories/camera.html
# Optional: use --libdir="lib" to change install dir from the default "lib/aarch64-linux-gnu" 
(cd $PWD/libcamera && meson build --buildtype=release -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled)
echo "Inside libcamera dir, build and install with ninja"
(cd $PWD/libcamera && ninja -C build -j 2 )
(cd $PWD/libcamera && sudo ninja -C build install )
echo "Post-installation update"
sudo ldconfig
echo "Create symbolic link /usr/local/lib/python3.9/dist-packages/libcamera"
sudo ln -sf /usr/local/lib/aarch64-linux-gnu/python3.9/site-packages/libcamera /usr/local/lib/python3.9/dist-packages/libcamera
