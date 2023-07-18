#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

echo "${PWD}"
echo "Install requirements using install_requirements.sh"
sh $PWD/install_requirements.sh



# clone libcamera source, and checkout a proved commit

#########################################
# New way: RPI down-stream libcamera
# https://github.com/raspberrypi/libcamera.git
#########################################
# Latest commit, Raspberry Pi ONLY, fixed app_full.py
LIBCAMERA_COMMIT=923f5d707bb760bd3e724b3373568fa88c68454f

#########################################
# Old way: official up-stream libcamera
# https://git.libcamera.org/libcamera/libcamera.git
#########################################
# Previous tested commit is on 2022 Nov 18th
# LIBCAMERA_COMMIT=v0.0.2
# Previous tested commit is on 2022 August 30th
# LIBCAMERA_COMMIT=fc9783acc6083a59fae8bca1ce49635e59afa355
# Previous tested commit is on 2022 August 21st.
# LIBCAMERA_COMMIT=6c6289ee184d79
# Previous tested commit is on 2022 April 4th.
# LIBCAMERA_COMMIT=302731cd


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


# config, build, and install libcamera
echo "Inside libcamera dir, configure the build with meson"
# The meson build options are from raspberry pi doc on libcamera
# ref https://www.raspberrypi.com/documentation/accessories/camera.html
# Optional: use --libdir="lib" to change install dir from the default "lib/aarch64-linux-gnu" 
(cd $PWD/libcamera && meson build --buildtype=release -Dpipelines=raspberrypi -Dipas=raspberrypi -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled)
echo "Inside libcamera dir, build and install with ninja"
(cd $PWD/libcamera && ninja -C build -j 2 )
(cd $PWD/libcamera && sudo ninja -C build install )
echo "Post-installation update"
sudo ldconfig
echo "Create symbolic link /usr/local/lib/python3.9/dist-packages/libcamera"
sudo ln -sf /usr/local/lib/aarch64-linux-gnu/python3.9/site-packages/libcamera /usr/local/lib/python3.9/dist-packages/libcamera

################################
# Build libepoxy from source
# Apt install gives problems
################################
LIBEPOXY_COMMIT=1.5.10
if [[ ! -d $PWD/libepoxy ]]
then
	echo "Clone libepoxy source and checkout commit id ${LIBEPOXY_COMMIT}"
	git clone https://github.com/anholt/libepoxy.git
	(cd $PWD/libepoxy && git checkout $LIBEPOXY_COMMIT)
fi
echo "Inside libepoxy dir, create a _build dir"
(cd $PWD/libepoxy && mkdir -p _build)
echo "Inside libepoxy/_build dir, build and install"
(cd $PWD/libepoxy/_build && meson)  # use -j1 on Raspberry Pi 3 or earlier devices
(cd $PWD/libepoxy/_build && ninja -j 2)
(cd $PWD/libepoxy/_build && sudo ninja install) # this is only necessary on the first build

# clone libcamera-apps source, and checkout a proved commit
# Latest tested commit is on 2022 Dec 1st.
LIBCAMERA_APPS_COMMIT=v1.0.2
# Previous tested commit is on 2022 August 30th.
# LIBCAMERA_APPS_COMMIT=1bf0cca
# Previous tested commit is on 2022 August 10th.
# LIBCAMERA_APPS_COMMIT=e1beb45
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
(cd $PWD/libcamera-apps/build && make -j2)  # use -j1 on Raspberry Pi 3 or earlier devices
(cd $PWD/libcamera-apps/build && sudo make install)
(cd $PWD/libcamera-apps/build && sudo ldconfig) # this is only necessary on the first build

# clone picamera2 source, and checkout a proved commit
# Latest tested commit is on 2022 Dec 1st
PICAMERA2_COMMIT=v0.3.7
# Previous tested commit is on 2022 August 31st, tag v0.3.3
# PICAMERA2_COMMIT=017cbd7
# Previous tested commit is on 2022 August 22th.
# PICAMERA2_COMMIT=18cda82
if [[ ! -d $PWD/picamera2 ]]
then
        echo "Clone picamera2 source and checkout commit id ${PICAMERA2_COMMIT}"
        git clone https://github.com/raspberrypi/picamera2.git
	(cd $PWD/picamera2 && git checkout $PICAMERA2_COMMIT)
fi

# Use pip to install instead, install for all user
(cd $PWD/picamera2 && sudo pip3 install .)

# Create Desktop shorcut for default user
# The OS image creation script sets $FIRST_USER_NAME to pi
# If this script is run without $FIRST_USER_NAME, default is pi
FIRST_USER_NAME=${FIRST_USER_NAME:=pi}

# If shortcut file already exists, remove it.
if [ -f "/home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop" ]
then
	sudo rm -f /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
fi

# If Desktop folder does not exist, create it.
if [ ! -d "/home/${FIRST_USER_NAME}/Desktop" ]
then
	mkdir -p /home/${FIRST_USER_NAME}/Desktop
fi

echo "Create GUI Desktop Icon"
echo "[Desktop Entry]" > /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Version=1.0" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Type=Application" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Terminal=true" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Exec=/usr/bin/python $PWD/common/app_full_ams.py" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Name=ams_osram_jetcis" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Comment=ams_osram_jetcis" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Icon=$PWD/desktop/aperture.png" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Set the script rights accordingly"
# TODO: gio command may fail at OS image creation (pi user not logged in)
# QUICKFIX: skip gio setting for now.
# gio set /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop "metadata::trusted" yes
sudo chmod a+rwx /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
sudo chown ${FIRST_USER_NAME}:${FIRST_USER_NAME} /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop

# Explicitly set environemtn variable if not exist
grep -q '^export GST_PLUGIN_PATH' /home/${FIRST_USER_NAME}/.bashrc || echo "export GST_PLUGIN_PATH=/home/${FIRST_USER_NAME}/ams_rpi_software/libcamera/build/src/gstreamer" >> /home/${FIRST_USER_NAME}/.bashrc

(cd $PWD && sudo install_extra.sh )
exit 0

