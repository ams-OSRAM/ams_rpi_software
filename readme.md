Prerequiresites:
- Raspberry Pi 4 (RPI4). It is tested on RPI4, but shoudl also support Raspberry Pi Compute Module 4 or Raspberry Pi 3.
- Raspberry Pi OS Bullseye 32bit.
- Mira220 sensor board V3.0
- Mira220 driver (provided in a separate repo) installed on RPI.

Compilation:
- Log on to the RPI, checkout the repo `ams_rpi_software`.
- At the root directory of `ams_rpi_software`, run `build_all.sh`.

Tests:
- Capture a JPG image file `test01.jpg` and a RAW image file `test01.dng` with the command `mira220/script/pmic_reset.sh && libcamera-still --immediate -r -o test01.jpg`. The JPG file can be viewed directly, while the DNG file can be covnerted into a PPM file by `dcraw test01.dng`, which generates a `test01.ppm` that can be viewed by software like GIMP.
- Capture a video and open a window to display it with a provided script at `mira220/script/gst_test.sh`.

