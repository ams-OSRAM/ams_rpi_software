#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"

version=$( cat /etc/os-release | grep -oP "[0-9]+" | head -1 )


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
# The meson build options are from raspberry pi doc on libcamera
# ref https://www.raspberrypi.com/documentation/accessories/camera.html
# Optional: use --libdir="lib" to change install dir from the default "lib/aarch64-linux-gnu" 


if [ $version -eq 11 ]; then
	echo "success, v11"
	(cd $PWD/libcamera && meson setup build --buildtype=release -Dpipelines=rpi/vc4 -Dipas=rpi/vc4 -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled)

	echo "Inside libcamera dir, build and install with ninja"
	(cd $PWD/libcamera && ninja -C build -j 2 )
	(cd $PWD/libcamera && sudo ninja -C build install )
	sudo ln -sf /usr/local/lib/aarch64-linux-gnu/python3.9/site-packages/libcamera	/usr/local/lib/python3.9/dist-packages/libcamera
elif [ $version -eq 12 ]; then
	(cd $PWD/libcamera && meson setup build --buildtype=release -Dpipelines=rpi/vc4,rpi/pisp -Dipas=rpi/vc4,rpi/pisp -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled)

	echo "Inside libcamera dir, build and install with ninja"
	(cd $PWD/libcamera && ninja -C build -j 2 )
	(cd $PWD/libcamera && sudo ninja -C build install )
	sudo ln -sf /usr/local/lib/aarch64-linux-gnu/python3.11/site-packages/libcamera	 /usr/local/lib/python3.11/dist-packages/libcamera
	echo "success, v12"
else
	echo "Unknown OS version, use default build options"
	exit 0
fi


#ninja -C build -j 2
#sudo ninja -C build install
echo "Post-installation update"
cd $TOPDIR
sudo ldconfig
