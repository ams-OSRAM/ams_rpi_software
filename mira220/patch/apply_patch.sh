LIBCAMERA_PATH=../../libcamera
PATCH_PATH=.
patch $LIBCAMERA_PATH/src/libcamera/camera_sensor_properties.cpp < $PATCH_PATH/camera_sensor_properties.cpp.patch
patch $LIBCAMERA_PATH/src/ipa/raspberrypi/data/meson.build < $PATCH_PATH/rpi_data_meson.build.patch
patch $LIBCAMERA_PATH/src/ipa/raspberrypi/meson.build < $PATCH_PATH/rpi_meson.build.patch

