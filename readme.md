
# Prerequisites:
- Raspberry Pi 4 (RPI4). It is tested on RPI4, but should also support Raspberry Pi Compute Module 4 or Raspberry Pi 3.
- Raspberry Pi OS Bullseye 64bit (recommended) or 32bit.
- Mira220 CSP sensor board V3.0 or Mira050 CSP sensor board V1.0
- Mira220 or Mira050 driver (provided in a separate repo) installed on RPI.
- Raspberry Pi has the required tools to compile libcamera. Refer to [Raspberry Pi doc](https://www.raspberrypi.com/documentation/accessories/camera.html#building-libcamera-and-libcamera-apps) on the required tools. It is recommended to test that all required tools are installed by compiling the standard libcamera as mentioned in the Raspberry Pi doc.

## Configure RPI:
- In the RPI, add a new line to `/boot/config.txt`, either specifying `dtoverlay=mira220` for Mira220 mono, or `dtoverlay=mira220color` for Mira220 color, or `dtoverlay=mira050` for Mira050 mono (pick one and only one!), depending on whether Mira220 mono or Mira220 color or Mira050 mono is conencted. If a standard RPI camera (such as SONY IMX219 or OVT OV5647) is connected instead, comment out or remove `dtoverlay=mira...` to avoid conflicts.

## Installing prerequisite tools on RPI:
```
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

###############################
# Linux kernel prerequisites
# [ref](https://www.raspberrypi.com/documentation/computers/linux_kernel.html)
###############################
sudo apt install git bc bison flex libssl-dev make

##############################
# gstreamer (for preview window) prerequisites
# [ref](https://qengineering.eu/install-gstreamer-1.18-on-raspberry-pi-4.html)
##############################
# install a missing dependency
sudo apt-get install libx264-dev libjpeg-dev
# install the remaining plugins
sudo apt-get install libgstreamer1.0-dev \
     libgstreamer-plugins-base1.0-dev \
     libgstreamer-plugins-bad1.0-dev \
     gstreamer1.0-plugins-ugly \
     gstreamer1.0-tools \
     gstreamer1.0-gl \
     gstreamer1.0-gtk3
# if you have Qt5 install this plugin
sudo apt-get install gstreamer1.0-qt5
# install if you want to work with audio
sudo apt-get install gstreamer1.0-pulseaudio
```

# Compilation (performed on RPI):
- Log on to the RPI, clone or unpack the repo `ams_rpi_software`.
- At the root directory of `ams_rpi_software`, run `build_all.sh`.

# Tests (performed on RPI, assuming Mira220 or Mira050 driver is installed):
- Capture a JPG image file `test01.jpg` with the command `libcamera-still --immediate -o test01.jpg`. The JPG file can be viewed directly.
- Capture a video and open a window to display it with a provided script, for Mira220 at `mira220/script/gst_test.sh`, and for Mira050 at `mira050/script/gst_test.sh`.
- [Optional] Integration test with OpenCV video capture in C++. Performing this test requires a one-time compilation of OpenCV, which takes 2 hours. This test case can be obtained from an external github repo, for [32bit OS](https://github.com/Qengineering/Libcamera-OpenCV-RPi-Bullseye-32OS) and [64bit OS](https://github.com/Qengineering/Libcamera-OpenCV-RPi-Bullseye-64OS) respectively. Please refer to the github repo for instructions.

### Use cases:
- Obtaining 12-bit-per-pixel raw images. Issue the command `libcamera-still --immediate -r -o test01.jpg` in which the `-r` option generates a RAW image file `test01.dng`. The DNG file can be converted into a PGM file by the command `dcraw -D -4 test01.dng` in which the `-D` option disables any Bayer and color processing, the `-4` option uses 16-bit container for each 12-bit pixel. The result is a `test01.pgm` that can be viewed by software like GIMP.
- Obtaining 12-bit-per-pixel raw image sequence. For Mira220, issue the command `libcamera-raw -t 2000 --mode 1600:1400:12:P --segment 1 -o video%05d.raw`; For Mira050, issue the command `libcamera-raw -t 2000 --mode 576:768:12:P --segment 1 -o video%05d.raw`. The `--mode` option specifies the width, height, bits-per-pixel, and Packed/Unpacked format for the frame. The raw image frames are in 12-bit packed format, which requires a conversion for viewing or post-processing. An example script is provided to convert this 12-bit packed format into 16-bit unpacked format. The script can be executed, for example, for Mira220 as `python common/convt_12P_16U.py -input video00000.raw -width 1600 -height 1400`; for Mira050 as `python common/convt_12P_16U.py -input video00000.raw -width 576 -height 768`. The script converts a `test00000.raw` into a `test00000.raw.pgm`, the latter storing each 12-bit pixel into a 16-bit container.

### Use cases supported on Mira220, but not yet on Mira050:
- Obtaining compressed 8-bit-per-pixel video. Issue the command `libcamera-vid -t 2000 --framerate 5 --codec h264 -o video01.h264 --save-pts video01_timestamp.txt` to capture 2000 milliseconds of video. The command generates a `video01.h264` video file and a time stamp record file `video01_timestamp.txt`. Since the h264 file does not contain timing information, it is recommended to convert it into a video format that has timing info, such as the mkv file format. As an example, first install the mkv video tools by the command `sudo apt install mkvtoolnix-gui`, followed by the command `mkvmerge -o video01.mkv --timecodes 0:video01_timestamp.txt video01.h264` that merges the h264 video file and the time stamp file to generate a mkv video file that contains timing information.
- Obtaining compressed 8-bit-per-pixel image sequence. Issue the command `libcamera-vid -t 2000 --framerate 5 --segment 1 --codec mjpeg -o test%04d.jpeg` to capture 2 seconds of video, and dump each frame into a JPEG file.

