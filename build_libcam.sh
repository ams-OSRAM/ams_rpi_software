#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"

LIBCAMERA_COMMIT=main


if [[ ! -d $PWD/libcamera ]]
then
	echo "Clone libcamera source and checkout commit id ${LIBCAMERA_COMMIT}"
	git clone https://github.com/raspberrypi/libcamera.git
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
echo "Applying patches to libcamera source"
(cd $PWD/mira016/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/mira016/src && ./apply_src.sh)
echo "Applying patches to libcamera source"
(cd $PWD/mira130/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/mira130/src && ./apply_src.sh)
echo "Applying patches to libcamera source"
(cd $PWD/poncha110/patch && ./apply_patch.sh)
echo "Copying source files to libcamera source"
(cd $PWD/poncha110/src && ./apply_src.sh)

# config, build, and install libcamera
echo "Inside libcamera dir, configure the build with meson"
# The meson build options are from raspberry pi doc on libcam.\era
# ref https://www.raspberrypi.com/documentation/accessories/camera.html
# Optional: use --libdir="lib" to change install dir from the default "lib/aarch64-linux-gnu" 
(cd $PWD/libcamera && meson build --buildtype=release -Dpipelines=rpi/vc4 -Dipas=rpi/vc4 -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled)
#
echo "Inside libcamera dir, build and install with ninja"
(cd $PWD/libcamera && ninja -C build -j 2 )
(cd $PWD/libcamera && sudo ninja -C build install )
echo "Post-installation update"
sudo ldconfig
echo "Create symbolic link /usr/local/lib/python3.9/dist-packages/libcamera"
sudo ln -sf /usr/local/lib/aarch64-linux-gnu/python3.9/site-packages/libcamera /usr/local/lib/python3.9/dist-packages/libcamera

