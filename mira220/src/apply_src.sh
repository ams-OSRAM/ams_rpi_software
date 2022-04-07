LIBCAMERA_PATH=../../libcamera
SRC_PATH=.
cp $SRC_PATH/camera_sensor_properties.cpp $LIBCAMERA_PATH/src/libcamera/
cp $SRC_PATH/cam_helper_mira220.cpp $LIBCAMERA_PATH/src/ipa/raspberrypi/
cp $SRC_PATH/mira220.json $LIBCAMERA_PATH/src/ipa/raspberrypi/data/
