Prerequisites:
- Raspberry Pi 4 (RPI4). It is tested on RPI4, but should also support Raspberry Pi Compute Module 4 or Raspberry Pi 3.
- Raspberry Pi OS Bullseye 32bit or 64bit.
- Mira220 sensor board V3.0
- Mira220 driver (provided in a separate repo) installed on RPI.
- Raspberry Pi has the required tools to compile libcamera. Refer to [Raspberry Pi doc](https://www.raspberrypi.com/documentation/accessories/camera.html#building-libcamera-and-libcamera-apps) on the required tools. It is recommended to test that all required tools are installed by compiling the standard libcamera as mentioned in the Raspberry Pi doc.

Compilation (performed on RPI):
- Log on to the RPI, clone or unpack the repo `ams_rpi_software`.
- At the root directory of `ams_rpi_software`, run `build_all.sh`.

Tests (performed on RPI, assuming Mira220 driver is installed):
- Capture a JPG image file `test01.jpg` with the command `mira220/script/pmic_reset.sh && libcamera-still --immediate -o test01.jpg`. The JPG file can be viewed directly, while 
- Capture a video and open a window to display it with a provided script at `mira220/script/gst_test.sh`.
- [Optional] Integration test with OpenCV video capture in C++. Performing this test requires a one-time compilation of OpenCV, which takes 2 hours. This test case can be obtained from an external github repo, for [32bit OS](https://github.com/Qengineering/Libcamera-OpenCV-RPi-Bullseye-32OS) and [64bit OS](https://github.com/Qengineering/Libcamera-OpenCV-RPi-Bullseye-64OS) respectively. Please refer to the github repo for instructions. Note: each time this test is executed, first reset the Mira220 sensor using `mira220/script/pmic_reset.sh`.

Use cases:
- Obtaining 12-bit-per-pixel raw images. Issue the command `mira220/script/pmic_reset.sh && libcamera-still --immediate -r -o test01.jpg` in which the `-r` option generates a RAW image file `test01.dng`. The DNG file can be converted into a PGM file by the command `dcraw -D -4 test01.dng` in which the `-D` option disables any Bayer and color processing, the `-4` option uses 16-bit container for each 12-bit pixel. The result is a `test01.pgm` that can be viewed by software like GIMP.
- Obtaining compressed 8-bit-per-pixel video. Issue the command `mira220/script/pmic_reset.sh && libcamera-vid -t 2000 --framerate 5 --codec h264 -o video01.h264 --save-pts video01_timestamp.txt` to capture 2000 milliseconds of video. The command generates a `video01.h264` video file and a time stamp record file `video01_timestamp.txt`. Since the h264 file does not contain timing information, it is recommended to convert it into a video format that has timing info, such as the mkv file format. As an example, first install the mkv video tools by the command `sudo apt install mkvtoolnix-gui`, followed by the command `mkvmerge -o video01.mkv --timecodes 0:video01_timestamp.txt video01.h264` that merges the h264 video file and the time stamp file to generate a mkv video file that contains timing information.
- Obtaining compressed 8-bit-per-pixel image sequence. Issue the command `mira220/script/pmic_reset.sh && libcamera-vid -t 2000 --framerate 5 --segment 1 --codec mjpeg -o test%04d.jpeg` to capture 2 seconds of video, and dump each frame into a JPEG file.
- Obtaining 12-bit-per-pixel raw image sequence. Issue the command `mira220/script/pmic_reset.sh && libcamera-raw -t 2000 --mode 1600:1400:12:P --segment 1 -o video%05d.raw`. The `-mode 1600:1400:12:P` option specifies the width, height, bits-per-pixel, and Packed/Unpacked format for the frame. The raw image frames are in 12-bit packed format, which requires a conversion for viewing or post-processing. An example script is provided to convert this 12-bit packed format into 16-bit unpacked format. The script can be executed, for example, as `python common/convt_12P_16U.py -input test00000.raw` for converting a `test00000.raw` into a `test00000.raw.pgm`, the latter storing each 12-bit pixel into a 16-bit container.

Known issues:
- Each time a new image or video capture starts, the MIRA220 sensor needs to be reset by reloading the MIRA220PMIC module. This can be done by running the `mira220/script/pmic_reset.sh` script.
