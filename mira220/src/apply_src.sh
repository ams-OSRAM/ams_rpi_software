LIBCAMERA_PATH=../../libcamera
SRC_PATH=.
cp $SRC_PATH/cam_helper_mira220.cpp $LIBCAMERA_PATH/src/ipa/rpi/cam_helper/
cp $SRC_PATH/mira220.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/
cp $SRC_PATH/mira220color.json $LIBCAMERA_PATH/src/ipa/rpi/vc4/data/