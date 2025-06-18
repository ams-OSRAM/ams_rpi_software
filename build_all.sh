#!/usr/bin/env bash
set -e

cd "$( dirname "${BASH_SOURCE[0]}" )"

TOPDIR=${PWD}
echo "$TOPDIR"
echo "Install requirements using install_requirements.sh"
#os version
version=$( cat /etc/os-release | grep -oP "[0-9]+" | head -1 )

# !!!!!!!!!!!!!! UNCOMMENT THIS LINE IF YOU WANT TO INSTALL REQUIREMENTS !!!!!!!!!!!!!!
. $TOPDIR/install_requirements.sh

# clone libcamera source, and checkout a proved commit

#########################################
# New way: RPI down-stream libcamera
# https://github.com/raspberrypi/libcamera.git
#########################################

if [[ ! -d $TOPDIR/libcamera ]]
then
	echo "Clone libcamera source and checkout commit id ${LIBCAMERA_COMMIT}"
	git clone https://github.com/raspberrypi/libcamera.git
	cd $TOPDIR/libcamera
	git checkout $LIBCAMERA_COMMIT
	cd $TOPDIR

#echo "Create symbolic link /usr/local/lib/python3.11/dist-packages/libcamera"
fi
$TOPDIR/build_libcam.sh

################################
# Build libepoxy from source
# Apt install gives problems
################################
LIBEPOXY_COMMIT=1.5.10
if [[ ! -d $TOPDIR/libepoxy ]]
then
	echo "Clone libepoxy source and checkout commit id ${LIBEPOXY_COMMIT}"
	git clone https://github.com/anholt/libepoxy.git
	cd $TOPDIR/libepoxy
	git checkout $LIBEPOXY_COMMIT
	cd $TOPDIR
	cd $TOPDIR/libepoxy
	git checkout $LIBEPOXY_COMMIT
	cd $TOPDIR
fi
echo "Inside libepoxy dir, create a _build dir"
(cd $TOPDIR/libepoxy && mkdir -p _build)
echo "Inside libepoxy/_build dir, build and install"
(cd $TOPDIR/libepoxy && meson setup _build) # use -j1 on Raspberry Pi 3 or earlier devices
(cd $TOPDIR/libepoxy && ninja -C _build -j 1 )
(cd $TOPDIR/libepoxy && sudo ninja -C _build install )
cd $TOPDIR

echo "rpicam_apps"
# clone rpicam-apps source, and checkout a proved commit

# Bookworm release
RPICAM_APPS_COMMIT="1a64a19"
if [[ ! -d $TOPDIR/rpicam-apps ]]
then
        echo "Clone rpicam-apps source and checkout commit id ${RPICAM_APPS_COMMIT}"
        git clone https://github.com/raspberrypi/rpicam-apps.git
	cd $TOPDIR/rpicam-apps
	git checkout $RPICAM_APPS_COMMIT
	cd $TOPDIR
fi

echo "Inside rpicam-apps dir, configure the build with meson"
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

# clone picamera2 source, not for installation, but for apps etc.
PICAMERA2_COMMIT=16d52aec
# Preivous tested commit is on 2022 Dec 1st
# PICAMERA2_COMMIT=v0.3.7

if [[ ! -d $TOPDIR/picamera2 ]]
then
        echo "Clone picamera2 source and checkout commit id ${PICAMERA2_COMMIT}"
        git clone https://github.com/raspberrypi/picamera2.git
	cd $TOPDIR/picamera2
	git checkout $PICAMERA2_COMMIT
	cd $TOPDIR
else
	echo "picam2 already installer"
fi

# Option 1: Install picamera2 system-wide via apt install
# sudo apt install -y python3-picamera2=0.3.16-1
# Option 2: Install in virtual environment. Not stable. Ignore error.
# cd $TOPDIR/picamera2
# sudo pip3 install . --break-system-packages
# cd $TOPDIR

. $TOPDIR/install_python.sh
echo "Finished installing picamera2."

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

# Make sure the Desktop folder is own by Pi, not root.
sudo chown ${FIRST_USER_NAME}:${FIRST_USER_NAME} /home/${FIRST_USER_NAME}/Desktop

echo "Create GUI Desktop Icon"
echo "[Desktop Entry]" > /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Version=1.0" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Type=Application" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Terminal=true" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Exec=$PWD/venv/bin/python $PWD/common/app_full_ams.py" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Name=ams_cam" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Comment=ams_osram sensor viewer" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Icon=$PWD/desktop/aperture.png" >> /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
echo "Set the script rights accordingly"
# TODO: gio command may fail at OS image creation (pi user not logged in)
# QUICKFIX: skip gio setting for now.
# gio set /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop "metadata::trusted" yes
sudo chmod a+rwx /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop
sudo chown ${FIRST_USER_NAME}:${FIRST_USER_NAME} /home/${FIRST_USER_NAME}/Desktop/ams_rpi_gui.desktop

# Explicitly set environemtn variable if not exist
# grep -q '^export GST_PLUGIN_PATH' /home/${FIRST_USER_NAME}/.bashrc || echo "export GST_PLUGIN_PATH=/home/${FIRST_USER_NAME}/ams_rpi_software/libcamera/build/src/gstreamer" >> /home/${FIRST_USER_NAME}/.bashrc

. $TOPDIR/install_extra.sh
