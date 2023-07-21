# Version v0.1.12

New features:
- Add support for Mira016.
- Update script to convert 8/10/12-bit raw file to pgm file.
- Update Python V4L2 interface for new commands, and I2C slave access.
- Experimental: remote access via Python and web interface.

# Version v0.1.11

No change from v0.1.11. Bump the tag version to sync with `ams_rpi_kernel` tag.

# Version v0.1.10

New features:
- Enable picamera2 full GUI app, add Desktop shortup, wallpaper.
- Update Mira050 color correction matrix json.

Bug fixes:
- Use newer commit id in Raspberry Pi downstream libcamera repo. Old one invalid.

# Version v0.1.9

New features:
- Use libcamera v0.0.2, libcamera-apps v1.0.2, picamera2 v0.3.7

Limitations:
- `ams_rpi_software` v0.1.9 is not backward compatible with libcamera v0.0.1.

Bug fixes:
- Change cam helpers according to recent API changes in libcamera.
- Make build script more robust.

# Version v0.1.8

Bug fixes:
- Install libepoxy manually to fix preview window problem.

# Version v0.1.7

New features:
- Support 8/10/12 bit modes and analog gain control for Mira050.
- Add demo Python scripts of Mira050 event detection.

# Version v0.1.6

Bug fixes:
- Fix over exposure bug of Mira220, and strange exposure behavior of Mira050.

# Version v0.1.5

New features:
- Build with libcamera-apps, picamera2.
- Support mira220color and mira050color.

# Version v0.1.4

New features:
- Add Mira050 support. Update readme for it.

# Version v0.1.3

New features:
- Use scripts, rather than the standard patch command, to apply patches.

# Version v0.1.2

New features:
- Add example and script for 12-bit per pixel mode.

# Version v0.1.1

New features:
- Update documents for 64bit OS. No code change needed.

# Version v0.1.0

New features:
- Basic mode: 1600x1400 with 8 bits per pixel.

Known issues:
- Each time a new image or video is captured, the mira220pmic module requires reloading.

