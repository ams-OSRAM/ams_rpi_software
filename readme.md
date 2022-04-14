Prerequisites:
- Raspberry Pi 4 (RPI4). It is tested on RPI4, but should also support Raspberry Pi Compute Module 4 or Raspberry Pi 3.
- Raspberry Pi OS Bullseye 32bit or 64bit.
- Mira220 sensor board V3.0
- Mira220 driver (provided in a separate repo) installed on RPI.

Compilation (performed on RPI):
- Log on to the RPI, clone or unpack the repo `ams_rpi_software`.
- At the root directory of `ams_rpi_software`, run `build_all.sh`.

Tests (performed on RPI, assuming Mira220 driver is installed):
- Capture a JPG image file `test01.jpg` and a RAW image file `test01.dng` with the command `mira220/script/pmic_reset.sh && libcamera-still --immediate -r -o test01.jpg`. The JPG file can be viewed directly, while the DNG file can be converted into a PPM file by `dcraw test01.dng`, which generates a `test01.ppm` that can be viewed by software like GIMP.
- Capture a video and open a window to display it with a provided script at `mira220/script/gst_test.sh`.
- [Optional] Integration test with OpenCV video capture in C++. Performing this test requires a one-time compilation of OpenCV, which takes 2 hours. This test case can be obtained from an external github repo, for [32bit OS](https://github.com/Qengineering/Libcamera-OpenCV-RPi-Bullseye-32OS) and [64bit OS](https://github.com/Qengineering/Libcamera-OpenCV-RPi-Bullseye-64OS) respectively. Please refer to the github repo for instructions. Note: each time this test is executed, first reset the Mira220 sensor using `mira220/script/pmic_reset.sh`.

Known issues:
- Each time a new image or video capture starts, the MIRA220 sensor needs to be reset by reloading the MIRA220PMIC module. This can be done by running the `mira220/script/pmic_reset.sh` script.
